"""Pruebas formales de valores atípicos: Grubbs (uno) y ESD generalizada de Rosner (varios).

Ambas suponen que los datos *sin* los atípicos vienen de una distribución normal. No son una regla para eliminar datos:
señalan puntos que no encajan con esa normal. En datos de proceso ordenados en el tiempo, las cartas de control y sus
pruebas de causas especiales son la herramienta adecuada.

* **Grubbs** (1969): ``G = max |xᵢ − x̄| / s`` frente a
  ``(n − 1)/√n · √(t² / (n − 2 + t²))`` con ``t`` = cuantil ``1 − α/(2n)`` de la t de Student con ``n − 2`` grados
  (``α/n`` si es unilateral). Contrasta un solo atípico; con dos atípicos del mismo lado puede enmascararse.
* **Dixon** (1951): razones entre huecos de los datos ordenados, ``r10 = (x₂ − x₁)/(xₙ − x₁)`` y sus variantes ``r11``,
  ``r21`` y ``r22`` (a partir de ``n`` = 3, 4, 5 y 6; ``'auto'`` elige la de Dixon según ``n``: 3–7 r10, 8–10 r11, 11–13
  r21, 14–30 r22). Pensada para muestras pequeñas. Los valores críticos **se calculan**, no se tabulan: bajo normalidad
  ``P(Q > c)`` es una integral doble sobre el mínimo y el ``(n−m)``-ésimo estadístico de orden con una cola binomial, que
  se resuelve por cuadratura de Gauss-Legendre y se invierte con ``brentq``. Reproduce las tablas publicadas de r10
  (Dixon, 1951; Rorabacher, 1991) a ≤ 0,005. En la prueba bilateral se usa ``α/2`` en cada cola (conservador).
* **ESD generalizada** (Rosner, 1983): quita de uno en uno el punto más alejado hasta ``max_outliers`` veces, calcula
  ``Rᵢ`` y el valor crítico ``λᵢ`` y declara atípicos los ``k`` primeros, donde ``k`` es el mayor ``i`` con ``Rᵢ > λᵢ``.
  Evita el enmascaramiento; conviene con ``n ≥ 25``.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import optimize, special, stats

from ._frames import etiquetas
from ._i18n import N_, tr

METODOS = ("grubbs", "esd", "dixon")
DIXON_RAZONES = {"r10": (1, 0), "r11": (1, 1), "r21": (2, 1), "r22": (2, 2)}  # (k, m): (x_{k+1} − x₁)/(x_{n−m} − x₁)
DIXON_N_MAXIMO = 100
DIXON_N_RECOMENDADO = 30
_NODOS_DIXON = 300
LADOS = ("two", "upper", "lower")
MAX_ATIPICOS_POR_DEFECTO = 10

_COLUMNAS = {"step": N_("paso"), "index": N_("índice"), "value": N_("valor"), "statistic": N_("estadístico"),
             "critical": N_("valor crítico"), "outlier": N_("atípico")}


def _critico(n: int, alpha: float, lados: str, metodo: str, paso: int = 1) -> float:
    """Valor crítico con ``n`` datos en la muestra actual (``paso`` = 1 en Grubbs; i-ésimo paso en ESD)."""
    k = n - 2  # grados de libertad de la t
    p = 1 - (alpha / (2 * n) if lados == "two" else alpha / n)
    t = float(stats.t.ppf(p, k))
    if metodo == "grubbs":
        return (n - 1) / np.sqrt(n) * np.sqrt(t * t / (k + t * t))
    return (n - 1) * t / np.sqrt((k + t * t) * n)  # λᵢ de Rosner con n = tamaño de la muestra restante


def _estadistico(x: np.ndarray, lados: str) -> tuple[int, float]:
    """Posición del punto más extremo y su estadístico, con la media y s de ``x``."""
    m, s = float(x.mean()), float(x.std(ddof=1))
    if lados == "two":
        d = np.abs(x - m)
    elif lados == "upper":
        d = x - m
    else:
        d = m - x
    j = int(np.argmax(d))
    return j, float(d[j] / s)


def _dixon_razon_automatica(n: int) -> str:
    """Razón que recomienda Dixon (1951) según el tamaño de la muestra."""
    return "r10" if n <= 7 else "r11" if n <= 10 else "r21" if n <= 13 else "r22"


def _dixon_p_cola(c: float, n: int, k: int, m: int) -> float:
    """``P(Q > c)`` bajo normalidad, con ``Q = (x_{k+1} − x₁)/(x_{n−m} − x₁)`` (sospechoso el mínimo).

    Condicionando en ``x₁ = a`` y ``x_{n−m} = b`` (densidad conjunta de dos estadísticos de orden), los ``n − m − 2``
    valores intermedios son iid en ``(a, b)``; ``Q > c`` equivale a que como mucho ``k − 1`` de ellos caigan por debajo
    de ``t = a + c(b − a)``. Se integra en la escala uniforme ``u = Φ(a)``, ``v = Φ(b)`` con cuadratura de Gauss-Legendre.
    """
    g, w = np.polynomial.legendre.leggauss(_NODOS_DIXON)
    g, w = (g + 1) / 2, w / 2
    u, s = g[:, None], g[None, :]
    v = u + (1 - u) * s
    jac = (1 - u) * w[:, None] * w[None, :]
    a, b = stats.norm.ppf(u), stats.norm.ppf(v)
    p = np.clip((stats.norm.cdf(a + c * (b - a)) - u) / (v - u), 0.0, 1.0)
    cola = stats.binom.cdf(k - 1, n - m - 2, p)
    log_coef = special.gammaln(n + 1) - special.gammaln(n - m - 1) - special.gammaln(m + 1)
    densidad = np.exp(log_coef + (n - m - 2) * np.log(v - u) + m * np.log1p(-v))
    return float(np.sum(jac * densidad * cola))


@lru_cache(maxsize=512)
def _dixon_critico(n: int, razon: str, alfa_unilateral: float) -> float:
    """Valor crítico unilateral de la razón de Dixon: el ``c`` con ``P(Q > c) = α`` bajo normalidad."""
    k, m = DIXON_RAZONES[razon]
    return float(optimize.brentq(lambda c: _dixon_p_cola(c, n, k, m) - alfa_unilateral, 1e-9, 1 - 1e-9, xtol=1e-8))


def _dixon_estadistico(x_ordenado: np.ndarray, razon: str) -> float:
    """Razón de Dixon con sospechoso el mínimo de ``x_ordenado``."""
    k, m = DIXON_RAZONES[razon]
    return float((x_ordenado[k] - x_ordenado[0]) / (x_ordenado[len(x_ordenado) - 1 - m] - x_ordenado[0]))


@dataclass
class OutlierTestResult:
    """Resultado de ``outlier_test``: pasos de la prueba y puntos declarados atípicos."""

    method: str
    alpha: float
    sides: str
    n: int
    steps: pd.DataFrame
    outlier_indices: np.ndarray
    outlier_values: np.ndarray
    ratio: str = ""  # razón de Dixon usada ('r10', 'r11', 'r21' o 'r22'); vacío en los demás métodos
    normality_p: float = float("nan")  # Shapiro-Wilk de los datos sin los atípicos (nan si quedan menos de 3)
    dropped: int = 0  # valores no finitos ignorados
    data: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def has_outliers(self) -> bool:
        """``True`` si se declaró al menos un atípico."""
        return self.outlier_indices.size > 0

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Un paso por fila: índice (base 0 en los datos originales), valor, estadístico, crítico y si es atípico."""
        col = etiquetas(_COLUMNAS, stable)
        s = self.steps
        return pd.DataFrame({col["step"]: s["step"], col["index"]: s["index"], col["value"]: s["value"],
                             col["statistic"]: s["statistic"], col["critical"]: s["critical"],
                             col["outlier"]: s["outlier"]})

    def summary(self) -> str:
        nombre = {"grubbs": tr("Grubbs"), "esd": tr("ESD generalizada (Rosner)"),
                  "dixon": tr("Dixon ({ratio})").format(ratio=self.ratio)}[self.method]
        lados = {"two": tr("bilateral"), "upper": tr("unilateral superior"), "lower": tr("unilateral inferior")}[self.sides]
        lines = [tr("Prueba de atípicos: {metodo}, {lados}, α = {alpha:g}  (n = {n})").format(
            metodo=nombre, lados=lados, alpha=self.alpha, n=self.n)]
        for _, f in self.steps.iterrows():
            lines.append(tr("  Paso {paso}: valor {valor:.6g} (índice {indice}), estadístico {est:.4f} {cmp} crítico {crit:.4f}"
                            ).format(paso=int(f["step"]), valor=f["value"], indice=int(f["index"]), est=f["statistic"],
                                     cmp=">" if f["statistic"] > f["critical"] else "≤", crit=f["critical"]))
        if self.has_outliers:
            lines.append(tr("  Atípicos declarados: {valores} (índices {indices})").format(
                valores=", ".join(f"{v:.6g}" for v in self.outlier_values),
                indices=", ".join(str(int(i)) for i in self.outlier_indices)))
        else:
            lines.append(tr("  Ningún atípico declarado."))
        lines.append(tr("  La prueba supone datos normales. No es una regla para eliminar datos: investiga el origen."))
        if self.normality_p < 0.05:
            lines.append(tr("  Aviso: los datos restantes no parecen normales (Shapiro-Wilk p = {p:.4f}); la prueba puede "
                            "marcar puntos que no son atípicos.").format(p=self.normality_p))
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()


def outlier_test(data, *, method: str = "grubbs", alpha: float = 0.05, sides: str = "two",
                 max_outliers: int | None = None, dixon_ratio: str = "auto") -> OutlierTestResult:
    """Prueba formal de valores atípicos (Grubbs, ESD generalizada de Rosner o Dixon).

    Parameters
    ----------
    data : array-like
        Muestra 1-D (los valores no finitos se ignoran con un aviso; los índices son los de la entrada original).
    method : {'grubbs', 'esd', 'dixon'}
        ``'grubbs'`` contrasta un solo atípico (el más extremo); ``'esd'`` busca hasta ``max_outliers`` atípicos
        sin que se enmascaren entre sí; ``'dixon'`` contrasta un solo atípico con la razón de Dixon (muestras pequeñas,
        3 ≤ n ≤ 100; se recomienda n ≤ 30).
    alpha : float
        Nivel de significación (por defecto 0,05).
    sides : {'two', 'upper', 'lower'}
        Bilateral, o solo valores demasiado altos o demasiado bajos.
    max_outliers : int, opcional
        Solo ESD: máximo de atípicos a buscar (por defecto ``min(10, (n − 1) // 2)``).
    dixon_ratio : {'auto', 'r10', 'r11', 'r21', 'r22'}
        Solo Dixon: la razón. ``'auto'`` usa la de Dixon (1951) según ``n``. ``r21`` y ``r22`` saltan al vecino del
        sospechoso (``x₃`` en vez de ``x₂``), de modo que un segundo atípico del mismo lado no enmascara el contraste;
        ``r11`` y ``r22`` quitan del denominador el extremo opuesto, de modo que un atípico en el otro extremo no lo
        infla.

    Returns
    -------
    OutlierTestResult
        ``outlier_indices`` y ``outlier_values`` de los atípicos declarados, y un paso por fila en ``to_frame()``.

    Notes
    -----
    Ambas pruebas suponen que los datos sin los atípicos son normales; el resultado incluye el valor p de Shapiro-Wilk
    de los datos restantes. Declarar un punto atípico no justifica eliminarlo.
    """
    if method not in METODOS:
        raise ValueError(tr("'method' debe ser uno de {opciones}.").format(opciones=", ".join(METODOS)))
    if sides not in LADOS:
        raise ValueError(tr("'sides' debe ser uno de {opciones}.").format(opciones=", ".join(LADOS)))
    if not 0 < alpha < 1:
        raise ValueError(tr("'alpha' debe estar en (0, 1)."))
    if dixon_ratio != "auto" and dixon_ratio not in DIXON_RAZONES:
        raise ValueError(tr("'dixon_ratio' debe ser 'auto' o uno de {opciones}.").format(opciones=", ".join(DIXON_RAZONES)))
    original = np.asarray(data, dtype=float).ravel()
    ok = np.isfinite(original)
    descartados = int((~ok).sum())
    if descartados:
        warnings.warn(tr("Se ignoraron {n} valor(es) no finito(s); los índices son los de la entrada original.").format(
            n=descartados), UserWarning, stacklevel=2)
    posiciones = np.flatnonzero(ok)
    x = original[ok]
    n = x.size
    razon = ""
    if method == "dixon":
        razon = _dixon_razon_automatica(n) if dixon_ratio == "auto" else dixon_ratio
        minimo = sum(DIXON_RAZONES[razon]) + 2
    else:
        minimo = 3 if method == "grubbs" else 4
    if n < minimo:
        raise ValueError(tr("Se necesitan al menos {n} observaciones para esta prueba.").format(n=minimo))
    if np.ptp(x) == 0:
        raise ValueError(tr("Los datos son constantes: no se puede calcular la prueba de atípicos."))

    if method == "dixon":
        return _prueba_dixon(original, x, posiciones, razon, alpha, sides, descartados)

    if method == "grubbs":
        r = 1
    else:
        r = (min(MAX_ATIPICOS_POR_DEFECTO, (n - 1) // 2) if max_outliers is None else int(max_outliers))
        if r < 1 or r > n - 3:
            raise ValueError(tr("'max_outliers' debe estar entre 1 y n − 3 ({tope}).").format(tope=n - 3))

    restantes = np.arange(n)  # posiciones (en x) de los datos que quedan
    filas = []
    for paso in range(1, r + 1):
        y = x[restantes]
        if np.ptp(y) == 0:
            break
        j, est = _estadistico(y, sides)
        crit = _critico(y.size, alpha, sides, method)
        filas.append({"step": paso, "index": int(posiciones[restantes[j]]), "value": float(y[j]),
                      "statistic": est, "critical": float(crit), "outlier": False})
        restantes = np.delete(restantes, j)
    # Grubbs: solo el primer paso decide; ESD: atípicos = los primeros k pasos, con k el mayor i en que R_i > λ_i
    k = 0
    for i, f in enumerate(filas, start=1):
        if f["statistic"] > f["critical"]:
            k = i
    for f in filas[:k]:
        f["outlier"] = True
    pasos = pd.DataFrame(filas)
    indices = pasos.loc[pasos["outlier"], "index"].to_numpy(dtype=int)
    sin = np.delete(original, indices)
    sin = sin[np.isfinite(sin)]
    p_norm = float(stats.shapiro(sin)[1]) if sin.size >= 3 and np.ptp(sin) > 0 else float("nan")
    return OutlierTestResult(
        method=method, alpha=float(alpha), sides=sides, n=n, steps=pasos, outlier_indices=indices,
        outlier_values=original[indices], normality_p=p_norm, dropped=descartados, data=original)


def _prueba_dixon(original: np.ndarray, x: np.ndarray, posiciones: np.ndarray, razon: str, alpha: float, sides: str,
                  descartados: int) -> OutlierTestResult:
    n = x.size
    if n > DIXON_N_MAXIMO:
        raise ValueError(tr("La prueba de Dixon admite como máximo {n} observaciones; usa Grubbs o la ESD generalizada.").format(
            n=DIXON_N_MAXIMO))
    if n > DIXON_N_RECOMENDADO:
        warnings.warn(tr("La prueba de Dixon está pensada para muestras pequeñas (n ≤ {n}); con más datos es preferible "
                         "Grubbs o la ESD generalizada.").format(n=DIXON_N_RECOMENDADO), UserWarning, stacklevel=3)
    m = DIXON_RAZONES[razon][1]
    orden = np.argsort(x, kind="stable")
    xs = x[orden]
    if xs[n - 1 - m] == xs[0] or xs[n - 1] == xs[m]:
        raise ValueError(tr("Hay demasiados valores repetidos en los extremos: la razón de Dixon {razon} no está definida.").format(
            razon=razon))
    candidatos = []  # (estadístico, posición en x, valor)
    if sides in ("two", "lower"):
        candidatos.append((_dixon_estadistico(xs, razon), orden[0]))
    if sides in ("two", "upper"):
        candidatos.append((_dixon_estadistico(-xs[::-1], razon), orden[-1]))
    est, j = max(candidatos, key=lambda c: c[0])
    crit = _dixon_critico(n, razon, alpha / 2 if sides == "two" else alpha)
    atipico = bool(est > crit)
    pasos = pd.DataFrame([{"step": 1, "index": int(posiciones[j]), "value": float(x[j]), "statistic": est,
                           "critical": crit, "outlier": atipico}])
    indices = pasos.loc[pasos["outlier"], "index"].to_numpy(dtype=int)
    sin = np.delete(original, indices)
    sin = sin[np.isfinite(sin)]
    p_norm = float(stats.shapiro(sin)[1]) if sin.size >= 3 and np.ptp(sin) > 0 else float("nan")
    return OutlierTestResult(
        method="dixon", alpha=float(alpha), sides=sides, n=n, steps=pasos, outlier_indices=indices,
        outlier_values=original[indices], ratio=razon, normality_p=p_norm, dropped=descartados, data=original)
