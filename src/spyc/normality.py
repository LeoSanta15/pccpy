"""Pruebas de normalidad (Anderson-Darling, Shapiro-Wilk, D'Agostino-Pearson)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats
from scipy.special import log_ndtr

from ._data import as_1d


@dataclass
class NormalityResult:
    method: str
    statistic: float
    p_value: float
    n: int

    def reject(self, alpha: float = 0.05) -> bool:
        """True si se rechaza la normalidad al nivel ``alpha``."""
        return self.p_value < alpha

    def __str__(self) -> str:
        p = "< 0.005" if self.p_value < 0.005 else f"{self.p_value:.3f}"
        return f"{self.method}: estadístico = {self.statistic:.4f}, valor p {'' if p.startswith('<') else '= '}{p} (n = {self.n})"


def anderson_darling_statistic(x: np.ndarray) -> float:
    """Estadístico A^2 de Anderson-Darling para normalidad (media y sigma estimadas)."""
    n = x.size
    y = np.sort(x)
    s = y.std(ddof=1)
    if s == 0:
        raise ValueError("Todos los datos son iguales; no se puede probar normalidad.")
    z = (y - y.mean()) / s
    i = np.arange(1, n + 1)
    a2 = -n - np.sum((2 * i - 1) * (log_ndtr(z) + log_ndtr(-z[::-1]))) / n
    return float(a2)


def anderson_darling_pvalue(a2: float, n: int) -> float:
    """Valor p aproximado (D'Agostino y Stephens, 1986, caso 3), como en Minitab."""
    a = a2 * (1.0 + 0.75 / n + 2.25 / n**2)
    if a >= 0.6:
        p = np.exp(1.2937 - 5.709 * a + 0.0186 * a**2)
    elif a >= 0.34:
        p = np.exp(0.9177 - 4.279 * a - 1.38 * a**2)
    elif a > 0.2:
        p = 1.0 - np.exp(-8.318 + 42.796 * a - 59.938 * a**2)
    else:
        p = 1.0 - np.exp(-13.436 + 101.14 * a - 223.73 * a**2)
    return float(min(max(p, 0.0), 1.0))


def normality_test(data, method: str = "anderson") -> NormalityResult:
    """Prueba de normalidad.

    ``method``: ``'anderson'`` (por defecto, la de Minitab), ``'shapiro'`` o
    ``'dagostino'`` (requiere n >= 8).
    """
    x = as_1d(data, "data")
    n = x.size
    if n < 3:
        raise ValueError("Se necesitan al menos 3 observaciones.")
    m = method.lower()
    if m == "anderson":
        a2 = anderson_darling_statistic(x)
        return NormalityResult("Anderson-Darling", a2, anderson_darling_pvalue(a2, n), n)
    if m == "shapiro":
        st, p = stats.shapiro(x)
        return NormalityResult("Shapiro-Wilk", float(st), float(p), n)
    if m == "dagostino":
        if n < 8:
            raise ValueError("D'Agostino-Pearson requiere al menos 8 observaciones.")
        st, p = stats.normaltest(x)
        return NormalityResult("D'Agostino-Pearson", float(st), float(p), n)
    raise ValueError("method debe ser 'anderson', 'shapiro' o 'dagostino'.")
