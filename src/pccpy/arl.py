"""ARL (longitud media de racha) de las cartas Shewhart, CUSUM y EWMA.

El ARL es el número esperado de puntos graficados hasta la primera señal; la señal cuenta como un punto, así que el mínimo es 1.
Con ``shift = 0`` es el ARL en control (ARL₀); con ``shift != 0``, el ARL fuera de control.

Supuestos comunes a todas las funciones:

* el estadístico graficado es normal, independiente en el tiempo y de varianza 1 una vez estandarizado;
* ``shift`` es el desplazamiento de su media **en unidades de σ del estadístico graficado** (con subgrupos de tamaño ``n`` la
  σ del estadístico es σ/√n: multiplica por √n el desplazamiento expresado en σ de la variable individual);
* los parámetros del proceso (μ y σ) son conocidos, no estimados;
* solo cuenta la regla «un punto fuera de los límites»: no se aplican las pruebas suplementarias de rachas;
* la carta es bilateral y simétrica.

Cada función admite tres métodos (``method``): ``"numeric"`` (por defecto; fórmula cerrada o ecuación integral con cuadratura de
Gauss-Legendre), ``"markov"`` (cadena de Markov con celdas) y ``"simulation"`` (Monte Carlo).
"""
from __future__ import annotations

import warnings

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from scipy.special import ndtr

from ._i18n import tr
from .charts._engine import check_method

_METODOS = ("numeric", "markov", "simulation")
_MAX_PASOS = 200_000  # tope de la simulación: evita bucles sin fin con ARL astronómicos
_LOG_RESTO = np.log(1e-13)  # (1 − λ)^{2t} por debajo de esto: los límites exactos de la EWMA ya son los asintóticos


# ------------------------------------------------------------------------------------------ validación
def _numero(valor) -> float:
    """``float(valor)``, o ``nan`` si no es convertible (el llamador rechaza lo no finito con su propio mensaje)."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return float("nan")


def _shift(shift) -> np.ndarray:
    try:
        arr = np.asarray(shift, dtype=float)
    except (TypeError, ValueError):
        raise ValueError(tr("'shift' debe contener solo valores finitos.")) from None
    if not np.all(np.isfinite(arr)):
        raise ValueError(tr("'shift' debe contener solo valores finitos."))
    return arr


def _n_runs(n_runs) -> int:
    try:
        ok = float(n_runs) == int(n_runs) and int(n_runs) >= 1
    except (TypeError, ValueError, OverflowError):
        ok = False
    if not ok:
        raise ValueError(tr("'n_runs' debe ser un entero >= 1."))
    return int(n_runs)


def _aplicar(shift, una_vez):
    """Aplica ``una_vez(shift_escalar)``: devuelve un float con un escalar y un arreglo con un arreglo."""
    arr = _shift(shift)
    if arr.ndim == 0:
        return float(max(1.0, una_vez(float(arr))))
    salida = np.array([max(1.0, una_vez(float(v))) for v in arr.ravel()], dtype=float)
    return salida.reshape(arr.shape)


# ---------------------------------------------------------------------------------------- simulación
def _simular(kind, mu, n_runs, rng, *, k=0.0, h=0.0, headstart=0.0, lam=0.0, L=0.0, exact=False) -> float:
    """ARL por Monte Carlo: ``n_runs`` cartas en paralelo con el estadístico ~ N(mu, 1)."""
    largo = np.zeros(n_runs)
    vivo = np.arange(n_runs)
    c_mas = np.full(n_runs, float(headstart))
    c_menos = np.full(n_runs, float(headstart))
    z = np.zeros(n_runs)
    t = 0
    while vivo.size and t < _MAX_PASOS:
        t += 1
        x = rng.normal(mu, 1.0, vivo.size)
        if kind == "shewhart":
            senal = np.abs(x) > k
        elif kind == "cusum":
            c_mas = np.maximum(0.0, x - k + c_mas)
            c_menos = np.maximum(0.0, -x - k + c_menos)
            senal = (c_mas > h) | (c_menos > h)
        else:  # ewma
            z = (1.0 - lam) * z + lam * x
            varianza = lam / (2.0 - lam) * ((1.0 - (1.0 - lam) ** (2 * t)) if exact else 1.0)
            senal = np.abs(z) > L * np.sqrt(varianza)
        largo[vivo[senal]] = t
        mantener = ~senal
        vivo, c_mas, c_menos, z = vivo[mantener], c_mas[mantener], c_menos[mantener], z[mantener]
    if vivo.size:
        warnings.warn(tr(
            "{n} de {total} corridas no dieron señal en {pasos} puntos: el ARL simulado queda sesgado a la baja."
        ).format(n=vivo.size, total=n_runs, pasos=t), UserWarning, stacklevel=4)
        largo[vivo] = t
    return float(largo.mean())


# ------------------------------------------------------------------------------------------- Shewhart
def arl_shewhart(k: float = 3.0, shift=0.0, method: str = "numeric", n_runs: int = 10_000, seed=None):
    """ARL de una carta Shewhart con límites a ±``k`` sigmas (regla «un punto fuera de los límites»).

    Con el estadístico ``Z ~ N(shift, 1)`` el ARL es ``1 / P(|Z| > k)``. Con ``k = 3`` y ``shift = 0`` da 370.398.

    Parameters
    ----------
    k : float
        Ancho de los límites en sigmas del estadístico graficado (> 0).
    shift : float o array-like
        Desplazamiento de la media en sigmas del estadístico graficado (``0`` = en control). Un arreglo devuelve un arreglo.
    method : {"numeric", "simulation"}
        ``"numeric"`` (por defecto) es la fórmula cerrada. ``"simulation"`` es Monte Carlo; ``"markov"`` no se admite porque la
        fórmula ya es exacta.
    n_runs : int
        Corridas de la simulación (solo con ``method="simulation"``).
    seed : int, Generator o None
        Semilla de la simulación (misma semilla, mismo resultado).

    Returns
    -------
    float o ndarray
        ARL, siempre >= 1.
    """
    k = _numero(k)
    if not (np.isfinite(k) and k > 0):
        raise ValueError(tr("'k' debe ser un número finito > 0."))
    check_method(method, ("numeric", "simulation"), "'method'")
    n_runs = _n_runs(n_runs)
    if method == "numeric":
        return _aplicar(shift, lambda s: 1.0 / (ndtr(-k - s) + ndtr(s - k)))
    rng = np.random.default_rng(seed)
    return _aplicar(shift, lambda s: _simular("shewhart", s, n_runs, rng, k=k))


# ---------------------------------------------------------------------------------------------- CUSUM
def _cusum_lado_numeric(h: float, k: float, mu: float, headstart: float, n: int = 80) -> float:
    """ARL de la CUSUM unilateral ``C_t = max(0, C_{t-1} + X_t − k)`` por ecuación integral (Gauss-Legendre).

    ``L(u) = 1 + L(0)·P(u + X − k ≤ 0) + ∫₀ʰ L(y) f(y − u + k) dy`` con ``X ~ N(mu, 1)``, resuelta por el método de Nyström.
    """
    x, w = np.polynomial.legendre.leggauss(n)
    y = 0.5 * h * (x + 1.0)
    w = 0.5 * h * w
    u = np.concatenate(([0.0], y))  # incógnitas: L(0) y L en los nodos
    nucleo = np.exp(-0.5 * (y[None, :] - u[:, None] + k - mu) ** 2) / np.sqrt(2.0 * np.pi) * w[None, :]
    p_cero = ndtr(k - u - mu)  # P(u + X − k ≤ 0): el estadístico se queda en 0
    a = np.zeros((n + 1, n + 1))
    a[:, 0] = -p_cero
    a[:, 1:] = -nucleo
    a += np.eye(n + 1)
    a[0, 0] = ndtr(mu - k)  # 1 − P(0 + X − k ≤ 0) sin cancelación
    sol = np.linalg.solve(a, np.ones(n + 1))
    s = headstart
    densidad = np.exp(-0.5 * (y - s + k - mu) ** 2) / np.sqrt(2.0 * np.pi)
    return float(1.0 + sol[0] * ndtr(k - s - mu) + np.sum(w * sol[1:] * densidad))


def _cusum_lado_markov(h: float, k: float, mu: float, headstart: float, m: int = 300) -> float:
    """ARL de la CUSUM unilateral por cadena de Markov con celdas (Brook y Evans, 1972)."""
    paso = 2.0 * h / (2 * m + 1)
    valores = paso * np.arange(m + 1)
    i = valores[:, None]
    j = valores[None, :]
    q = ndtr(j * 0 + (j + 0.5 * paso) - i + k - mu) - ndtr((j - 0.5 * paso) - i + k - mu)
    q[:, 0] = ndtr(0.5 * paso - valores + k - mu)  # el estado 0 absorbe todo lo que cae por debajo de la primera celda
    sol = np.linalg.solve(np.eye(m + 1) - q, np.ones(m + 1))
    return float(np.interp(headstart, valores, sol))


def _cusum_bilateral_2d(h: float, k: float, mu: float, headstart: float, m: int = 60) -> float:
    """ARL de la CUSUM bilateral por cadena de Markov bidimensional ``(C⁺, C⁻)``, con arranque rápido.

    Los dos lados no son independientes (``C⁺`` y ``C⁻`` pueden ser positivas a la vez), así que con ``headstart > 0`` la
    combinación ``1/ARL⁺ + 1/ARL⁻`` falla (≈ 6 % con ``h = 4``, ``k = 0.5`` y ``headstart = 2``). Cada celda es un par de celdas
    de Brook y Evans; como ``C⁺`` y ``C⁻`` dependen de la misma observación ``x``, las probabilidades de transición se obtienen
    integrando ``x`` entre los puntos donde alguna de las dos sumas cambia de celda. El resultado se interpola bilinealmente en
    ``(headstart, headstart)``. Con ``m = 60`` el error es de ≈ 0.1 %.
    """
    paso = 2.0 * h / (2 * m + 1)
    n = m + 1
    bordes = (np.arange(n) + 0.5) * paso  # borde superior de las celdas 0..m (el de la m es h)
    filas, columnas, valores = [], [], []
    for i in range(n):
        for j in range(n):
            br = np.sort(np.concatenate((bordes - i * paso + k, j * paso - k - bordes)))
            bajo, alto = np.concatenate(([-np.inf], br)), np.concatenate((br, [np.inf]))
            medio = np.where(np.isinf(bajo), alto - 1.0, np.where(np.isinf(alto), bajo + 1.0, 0.5 * (bajo + alto)))
            masa = ndtr(alto - mu) - ndtr(bajo - mu)
            p = np.searchsorted(bordes, np.maximum(0.0, i * paso + medio - k), side="right")
            q = np.searchsorted(bordes, np.maximum(0.0, j * paso - medio - k), side="right")
            ok = (p <= m) & (q <= m) & (masa > 0)
            filas.append(np.full(int(ok.sum()), i * n + j))
            columnas.append(p[ok] * n + q[ok])
            valores.append(masa[ok])
    q_mat = sp.csr_matrix((np.concatenate(valores), (np.concatenate(filas), np.concatenate(columnas))), shape=(n * n, n * n))
    r = spsolve((sp.eye(n * n, format="csr") - q_mat).tocsc(), np.ones(n * n)).reshape(n, n)
    pos = headstart / paso
    i0 = int(min(np.floor(pos), m - 1))
    f = pos - i0
    return float((1 - f) ** 2 * r[i0, i0] + f * (1 - f) * (r[i0 + 1, i0] + r[i0, i0 + 1]) + f * f * r[i0 + 1, i0 + 1])


def _cusum_bilateral(h: float, k: float, mu: float, headstart: float, lado) -> float:
    """Combina los dos lados: ``1/ARL = 1/ARL⁺ + 1/ARL⁻`` (aproximación estándar; un lado con deriva fuerte en contra es ∞)."""
    if headstart > 0:
        return _cusum_bilateral_2d(h, k, mu, headstart)
    inversa = 0.0
    for deriva in (mu, -mu):
        if deriva - k < -6.0:  # el lado se aleja del límite: su ARL es > 1e10 y no cambia el resultado
            continue
        inversa += 1.0 / lado(h, k, deriva, headstart)
    return 1.0 / inversa


def arl_cusum(h: float = 4.0, k: float = 0.5, shift=0.0, headstart: float = 0.0, method: str = "numeric",
              n_runs: int = 10_000, seed=None):
    """ARL de la CUSUM tabular bilateral de :func:`pccpy.cusum_chart`.

    Con ``C⁺ᵢ = max(0, zᵢ − k + C⁺ᵢ₋₁)`` y ``C⁻ᵢ = max(0, −zᵢ − k + C⁻ᵢ₋₁)`` hay señal cuando alguna suma supera ``h``. ``h`` y
    ``k`` están en sigmas del estadístico graficado. Con ``h = 4`` y ``k = 0.5`` el ARL en control es ≈ 168 y con 1σ de
    desplazamiento ≈ 8.4.

    Con ``headstart = 0`` los métodos ``"numeric"`` y ``"markov"`` calculan cada lado y los combinan con
    ``1/ARL = 1/ARL⁺ + 1/ARL⁻`` (aproximación estándar: con ``h = 4`` y ``k = 0.5`` difiere menos de 0.3 % de la simulación).
    Con ``headstart > 0`` esa combinación falla (≈ 6 % con ``headstart = h/2`` y ``shift = 0``) y ambos métodos resuelven la
    cadena de Markov bidimensional ``(C⁺, C⁻)`` (error ≈ 0.1 %, más lenta: del orden de un segundo). ``"simulation"`` simula las
    dos sumas a la vez.

    Parameters
    ----------
    h : float
        Límite de decisión (> 0).
    k : float
        Holgura o valor de referencia (>= 0).
    shift : float o array-like
        Desplazamiento de la media en sigmas del estadístico graficado. Un arreglo devuelve un arreglo.
    headstart : float
        Arranque rápido (Lucas y Crosier, 1982): ambas sumas empiezan en este valor (``0 <= headstart < h``).
    method : {"numeric", "markov", "simulation"}
        ``"numeric"`` (por defecto): ecuación integral con cuadratura de Gauss-Legendre.
    n_runs, seed
        Corridas y semilla de la simulación.

    Returns
    -------
    float o ndarray
        ARL, siempre >= 1.
    """
    h = _numero(h)
    if not (np.isfinite(h) and h > 0):
        raise ValueError(tr("'h' debe ser un número finito > 0."))
    k = _numero(k)
    if not (np.isfinite(k) and k >= 0):
        raise ValueError(tr("'k' debe ser un número finito >= 0."))
    headstart = _numero(headstart)
    if not 0 <= headstart < h:
        raise ValueError(tr("'headstart' debe cumplir 0 <= headstart < h."))
    check_method(method, _METODOS, "'method'")
    n_runs = _n_runs(n_runs)
    if method == "simulation":
        rng = np.random.default_rng(seed)
        return _aplicar(shift, lambda s: _simular("cusum", s, n_runs, rng, h=h, k=k, headstart=headstart))
    lado = _cusum_lado_numeric if method == "numeric" else _cusum_lado_markov
    return _aplicar(shift, lambda s: _cusum_bilateral(h, k, s, headstart, lado))


# ------------------------------------------------------------------------------------------------ EWMA
def _discretizar(metodo: str, c: float, n: int):
    """Nodos y pesos de Gauss-Legendre (``numeric``) o celdas con sus bordes (``markov``) sobre ``[-c, c]``."""
    if metodo == "numeric":
        x, w = np.polynomial.legendre.leggauss(n)
        return c * x, c * w, None, None
    bordes = np.linspace(-c, c, n + 1)
    return 0.5 * (bordes[:-1] + bordes[1:]), None, bordes[:-1], bordes[1:]


def _matriz_ewma(metodo: str, origen: np.ndarray, destino, lam: float, mu: float) -> np.ndarray:
    """Probabilidad (o núcleo por peso) de pasar de cada punto de ``origen`` a cada nodo o celda de ``destino``."""
    nodos, pesos, bajo, alto = destino
    media = (1.0 - lam) * origen[:, None]
    if metodo == "numeric":
        z = (nodos[None, :] - media) / lam - mu
        return np.exp(-0.5 * z * z) / (lam * np.sqrt(2.0 * np.pi)) * pesos[None, :]
    return ndtr((alto[None, :] - media) / lam - mu) - ndtr((bajo[None, :] - media) / lam - mu)


def _arl_ewma(metodo: str, lam: float, L: float, mu: float, exact: bool) -> float:
    c_inf = L * np.sqrt(lam / (2.0 - lam))
    if metodo == "numeric":
        n = int(np.clip(np.ceil(24.0 * c_inf / lam), 48, 320))
    else:
        n = int(np.clip(np.ceil(60.0 * c_inf / lam), 101, 601)) | 1  # impar: la celda central contiene 0
    asint = _discretizar(metodo, c_inf, n)
    m = _matriz_ewma(metodo, asint[0], asint, lam, mu)
    v = np.linalg.solve(np.eye(n) - m, np.ones(n))
    if not exact:
        return float(1.0 + _matriz_ewma(metodo, np.zeros(1), asint, lam, mu)[0] @ v)
    # límites exactos (varianza λ/(2−λ)·(1−(1−λ)^{2t})): recursión hacia atrás desde el instante T0, a partir del cual los límites
    # ya son los asintóticos y el ARL restante es la solución de la ecuación integral
    t0 = 1 if lam >= 1.0 else max(1, int(np.ceil(_LOG_RESTO / (2.0 * np.log1p(-lam)))))
    destino = asint
    for t in range(t0 - 1, 0, -1):
        actual = _discretizar(metodo, c_inf * np.sqrt(1.0 - (1.0 - lam) ** (2 * t)), n)
        v = 1.0 + _matriz_ewma(metodo, actual[0], destino, lam, mu) @ v
        destino = actual
    return float(1.0 + _matriz_ewma(metodo, np.zeros(1), destino, lam, mu)[0] @ v)


def arl_ewma(weight: float = 0.2, L: float = 3.0, shift=0.0, exact_limits: bool = False, method: str = "numeric",
             n_runs: int = 10_000, seed=None):
    """ARL de la EWMA bilateral de :func:`pccpy.ewma_chart`.

    El estadístico es ``Zᵢ = (1 − λ)·Zᵢ₋₁ + λ·xᵢ`` con ``Z₀ = 0`` y hay señal cuando ``|Zᵢ|`` supera ``L·σ_Z``. Con límites
    asintóticos ``σ_Z = √(λ/(2 − λ))``; con ``exact_limits=True``, ``σ_Z = √(λ/(2 − λ)·(1 − (1 − λ)^{2i}))`` (límites más
    estrechos al principio). Con ``λ = 1`` es la carta Shewhart de :func:`arl_shewhart`.

    Parameters
    ----------
    weight : float
        Peso λ de la EWMA, en ``(0, 1]``.
    L : float
        Ancho de los límites en sigmas de la EWMA (> 0).
    shift : float o array-like
        Desplazamiento de la media en sigmas del estadístico graficado. Un arreglo devuelve un arreglo.
    exact_limits : bool
        Usa los límites exactos en lugar de los asintóticos.
    method : {"numeric", "markov", "simulation"}
        ``"numeric"`` (por defecto): ecuación integral con cuadratura de Gauss-Legendre (Crowder, 1987).
        ``"markov"``: cadena de Markov con celdas (Lucas y Saccucci, 1990).
    n_runs, seed
        Corridas y semilla de la simulación.

    Returns
    -------
    float o ndarray
        ARL, siempre >= 1.
    """
    lam = _numero(weight)
    if not (np.isfinite(lam) and 0 < lam <= 1):
        raise ValueError(tr("'weight' debe estar en (0, 1]."))
    L = _numero(L)
    if not (np.isfinite(L) and L > 0):
        raise ValueError(tr("'L' debe ser un número finito > 0."))
    check_method(method, _METODOS, "'method'")
    n_runs = _n_runs(n_runs)
    if method == "simulation":
        rng = np.random.default_rng(seed)
        return _aplicar(shift, lambda s: _simular("ewma", s, n_runs, rng, lam=lam, L=L, exact=bool(exact_limits)))
    return _aplicar(shift, lambda s: _arl_ewma(method, lam, L, s, bool(exact_limits)))
