"""Constantes de control estadístico de procesos (d2, d3, c4, c5, A2, D3, D4, ...).

Se calculan numéricamente para *cualquier* tamaño de subgrupo n >= 2, en lugar
de depender de una tabla finita. Los valores coinciden con las tablas
publicadas (p. ej. Montgomery, Apéndice VI) a los decimales publicados.
"""
from __future__ import annotations

import math
from functools import lru_cache
from typing import Dict

import numpy as np
from scipy import integrate
from scipy.special import gammaln

_SQRT2PI = math.sqrt(2.0 * math.pi)


def _phi(t: float) -> float:
    return math.exp(-0.5 * t * t) / _SQRT2PI


def _Phi(t: float) -> float:
    return 0.5 * math.erfc(-t / math.sqrt(2.0))


def _check_n(n: int) -> int:
    n = int(n)
    if n < 2:
        raise ValueError(f"El tamaño de subgrupo debe ser >= 2 (recibido: {n}).")
    return n


@lru_cache(maxsize=None)
def d2(n: int) -> float:
    """Media del rango relativo W = R/sigma para n observaciones normales."""
    n = _check_n(n)

    def f(x: float) -> float:
        p = _Phi(x)
        return 1.0 - p**n - (1.0 - p) ** n

    val, _ = integrate.quad(f, -np.inf, np.inf, epsabs=1e-13, epsrel=1e-13, limit=200)
    return float(val)


@lru_cache(maxsize=None)
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


@lru_cache(maxsize=None)
def c4(n: int) -> float:
    """Factor de corrección de sesgo de la desviación estándar muestral."""
    n = _check_n(n)
    return math.sqrt(2.0 / (n - 1)) * math.exp(gammaln(n / 2.0) - gammaln((n - 1) / 2.0))


@lru_cache(maxsize=None)
def c5(n: int) -> float:
    """Desviación estándar de s / sigma: sqrt(1 - c4^2)."""
    return math.sqrt(1.0 - c4(n) ** 2)


def control_chart_constants(n: int) -> Dict[str, float]:
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
