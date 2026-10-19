"""Constantes de control estadístico de procesos (d2, d3, c4, c5, A2, D3, D4, ...).

Se calculan numéricamente para *cualquier* tamaño de subgrupo n >= 2, en lugar
de depender de una tabla finita. Los valores coinciden con las tablas
publicadas (p. ej. Montgomery, Apéndice VI) a los decimales publicados.
"""
from __future__ import annotations

import math
from functools import cache

import numpy as np
from scipy import integrate
from scipy.special import gammaln

from ._i18n import tr

_SQRT2PI = math.sqrt(2.0 * math.pi)


def _phi(t: float) -> float:
    return math.exp(-0.5 * t * t) / _SQRT2PI


def _Phi(t: float) -> float:
    return 0.5 * math.erfc(-t / math.sqrt(2.0))


def _check_n(n: int) -> int:
    n = int(n)
    if n < 2:
        raise ValueError(tr("El tamaño de subgrupo debe ser >= 2 (recibido: {n}).").format(n=n))
    return n


@cache
def d2(n: int) -> float:
    """Media del rango relativo W = R/sigma para n observaciones normales."""
    n = _check_n(n)

    def f(x: float) -> float:
        p = _Phi(x)
        return 1.0 - p**n - (1.0 - p) ** n

    val, _ = integrate.quad(f, -np.inf, np.inf, epsabs=1e-13, epsrel=1e-13, limit=200)
    return float(val)


def d2_star(m: int, g: float) -> float:
    """``d2*(m, g)`` de AIAG: media del rango relativo cuando se promedian ``g`` rangos de ``m`` valores.

    Aproximación ``sqrt(d2(m)² + d3(m)²/g)``: con ``g = 1`` es exacta (raíz de ``E[W²]``, p. ej. ``√2`` para ``m = 2``) y
    con ``g`` grande tiende a ``d2(m)``. Reproduce las constantes K2 y K3 del manual MSA de AIAG a ~1e-3
    (``1/d2*(3, 1) = 0,5231`` y ``1/d2*(10, 1) = 0,3146``).
    """
    if g <= 0:
        raise ValueError(tr("'g' debe ser positivo (recibido: {g}).").format(g=g))
    return math.sqrt(d2(m) ** 2 + d3(m) ** 2 / g)


@cache
def d3(n: int) -> float:
    """Desviación estándar del rango relativo W = R/sigma."""
    n = _check_n(n)
    lim = 9.0 + math.log(n)

    def joint(y: float, x: float) -> float:
        # densidad conjunta (mínimo x, máximo y) por (y - x)^2
        return (
            (y - x) ** 2
            * n
            * (n - 1)
            * _phi(x)
            * _phi(y)
            * (_Phi(y) - _Phi(x)) ** (n - 2)
        )

    ex2, _ = integrate.dblquad(
        joint, -lim, lim, lambda x: x, lambda x: lim, epsabs=1e-11, epsrel=1e-11
    )
    return math.sqrt(max(ex2 - d2(n) ** 2, 0.0))


@cache
def c4(n: int) -> float:
    """Factor de corrección de sesgo de la desviación estándar muestral."""
    n = _check_n(n)
    return math.sqrt(2.0 / (n - 1)) * math.exp(gammaln(n / 2.0) - gammaln((n - 1) / 2.0))


@cache
def c5(n: int) -> float:
    """Desviación estándar de s / sigma: sqrt(1 - c4^2)."""
    return math.sqrt(1.0 - c4(n) ** 2)


def control_chart_constants(n: int) -> dict[str, float]:
    """Devuelve todas las constantes para un tamaño de subgrupo ``n``.

    Claves: d2, d3, c4, c5, A2, A3, D3, D4, B3, B4.
    """
    n = _check_n(n)
    _d2, _d3, _c4, _c5 = d2(n), d3(n), c4(n), c5(n)
    return {
        "d2": _d2,
        "d3": _d3,
        "c4": _c4,
        "c5": _c5,
        "A2": 3.0 / (_d2 * math.sqrt(n)),
        "A3": 3.0 / (_c4 * math.sqrt(n)),
        "D3": max(0.0, 1.0 - 3.0 * _d3 / _d2),
        "D4": 1.0 + 3.0 * _d3 / _d2,
        "B3": max(0.0, 1.0 - 3.0 * _c5 / _c4),
        "B4": 1.0 + 3.0 * _c5 / _c4,
    }


def k_from_confidence(confidence: float) -> float:
    """Multiplicador ``k`` (en sigmas) de unos límites bilaterales con la confianza dada, para un estadístico normal.

    ``k = Φ⁻¹(1 − (1 − confianza)/2)``: ``0.9973`` da ``k ≈ 3``, ``0.95`` da 1.960 y ``0.99`` da 2.576. Solo es exacto en los
    paneles normales (individuales y medias); en R, S, MR y atributos la probabilidad real la da ``chart.probability()``.

    Parameters
    ----------
    confidence : float
        Confianza bilateral, ``0 < confidence < 1``.
    """
    if isinstance(confidence, (bool, np.bool_)) or not isinstance(confidence, (int, float, np.integer, np.floating)) \
            or not 0.0 < float(confidence) < 1.0:
        raise ValueError(tr("'confidence' debe ser un número entre 0 y 1 (exclusivos); recibido: {valor!r}.").format(
            valor=confidence))
    from scipy import stats

    return float(stats.norm.isf((1.0 - float(confidence)) / 2.0))


@cache
def cmed(n: int) -> float:
    """Desviación estándar de la mediana de ``n`` normales estándar (``cmed(n) = sd(mediana)/σ``).

    Con ``n`` impar es la integral de ``x²`` por la densidad del estadístico de orden central; con ``n`` par, la mediana es el
    promedio de los dos valores centrales y se integra su densidad conjunta. El coeficiente de Montgomery para la carta de
    medianas es ``Ã2 = 3·cmed(n)/d2(n)`` (``n`` = 3, 5, 7, 9: 1.187, 0.691, 0.509, 0.412).
    """
    n = _check_n(n)
    if n == 1:
        return 1.0
    log_c = gammaln(n + 1)
    if n % 2 == 1:
        m = (n - 1) // 2
        c = math.exp(log_c - 2.0 * gammaln(m + 1))

        def f(x: float) -> float:
            p = _Phi(x)
            return x * x * c * p**m * (1.0 - p) ** m * _phi(x)

        return math.sqrt(integrate.quad(f, -12.0, 12.0, epsabs=1e-13, epsrel=1e-13)[0])
    m = n // 2
    c = math.exp(log_c - 2.0 * gammaln(m))  # n!/((m − 1)!)²: m − 1 por debajo de x, ninguna entre x e y y m − 1 por encima de y

    def g(y: float, x: float) -> float:  # densidad conjunta de X(m), X(m+1) con x < y, por ((x + y)/2)²
        px, qy = _Phi(x), 1.0 - _Phi(y)
        return 0.25 * (x + y) ** 2 * c * px ** (m - 1) * qy ** (m - 1) * _phi(x) * _phi(y)

    valor = integrate.dblquad(g, -12.0, 12.0, lambda x: x, lambda x: 12.0, epsabs=1e-12, epsrel=1e-12)[0]
    return math.sqrt(valor)


@cache
def c_mssd(n: int) -> float:
    """Constante de insesgamiento del estimador ``σ̂ = √(MSSD/2)`` con ``n`` observaciones consecutivas (``n − 1`` diferencias).

    ``MSSD/2 = Q/(n − 1)`` con ``Q = Σᵢ λᵢ·zᵢ²`` (zᵢ normales estándar independientes y ``λⱼ = 1 − cos(πj/n)``, j = 1…n−1, los
    valores propios de ``DᵀD/2``). Como ``√q = (1/(2√π))·∫₀^∞ (1 − e^{−sq})·s^{−3/2} ds`` y ``E[e^{−sQ}] = Πⱼ(1 + 2sλⱼ)^{−1/2}``,
    ``c_mssd(n) = E[√(Q/(n−1))]`` se calcula por integración numérica (sin simulación). Con n = 10 vale ≈ 0.962.
    """
    n = int(n)
    if n < 2:
        raise ValueError(tr("El tamaño de subgrupo debe ser >= 2 (recibido: {n}).").format(n=n))
    lam = 1.0 - np.cos(np.pi * np.arange(1, n) / n)

    def f(t: float) -> float:  # con s = t²: (1 − Π(1 + 2t²λ)^{−1/2}) · t^{−2}
        if t < 1e-6:
            return float(lam.sum())
        return float(-np.expm1(-0.5 * np.sum(np.log1p(2.0 * t * t * lam))) / (t * t))

    valor = integrate.quad(f, 0.0, np.inf, epsabs=1e-13, epsrel=1e-12, limit=400)[0]
    return float(valor / math.sqrt(math.pi * (n - 1)))
