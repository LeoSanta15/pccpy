"""Estimadores de la desviación estándar del proceso (sigma *within*).

Fórmulas según la documentación de métodos de Minitab:

* Individuales: rango móvil promedio / d2(span), mediana del rango móvil / 0.954
  (span = 2) o raíz cuadrada de la media de las diferencias cuadradas sucesivas (MSSD).
* Subgrupos: Rbar, Sbar o desviación estándar combinada (pooled) con factor c4.
"""
from __future__ import annotations

import warnings
from typing import Callable

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ._constants import c4, d2

MEDIAN_MR_CONSTANT = 0.954  # constante que usa Minitab para span = 2


def vec(func: Callable[[int], float], n_i: np.ndarray) -> np.ndarray:
    """Aplica una constante f(n) a un vector de tamaños; NaN donde n < 2."""
    out = np.full(n_i.shape, np.nan)
    for n in np.unique(n_i):
        if n >= 2:
            out[n_i == n] = func(int(n))
    return out


def moving_range(x: np.ndarray, span: int = 2) -> np.ndarray:
    """Rangos móviles de ventana ``span``; los primeros span-1 valores son NaN."""
    if span < 2:
        raise ValueError("'span' debe ser >= 2.")
    out = np.full(x.shape, np.nan)
    if x.size >= span:
        w = sliding_window_view(x, span)
        out[span - 1 :] = w.max(axis=1) - w.min(axis=1)
    return out


def sigma_individuals(x: np.ndarray, method: str = "mr", span: int = 2) -> float:
    """Sigma a partir de observaciones individuales."""
    if x.size < 2:
        raise ValueError("Se necesitan al menos 2 observaciones para estimar sigma.")
    if method == "mr":
        if x.size < span:
            raise ValueError(f"Se necesitan al menos {span} observaciones (span={span}).")
        return float(np.nanmean(moving_range(x, span)) / d2(span))
    if method == "median_mr":
        if span != 2:
            raise ValueError("'median_mr' solo está disponible con span = 2.")
        return float(np.nanmedian(moving_range(x, 2)) / MEDIAN_MR_CONSTANT)
    if method == "mssd":
        return float(np.sqrt(np.sum(np.diff(x) ** 2) / (2.0 * (x.size - 1))))
    raise ValueError("sigma_method debe ser 'mr', 'median_mr' o 'mssd'.")


def subgroup_stats(g: np.ndarray):
    """(n_i, medias, rangos, desv. est.) por subgrupo; rango/desv NaN si n_i = 1."""
    n_i = np.sum(~np.isnan(g), axis=1)
    means = np.nanmean(g, axis=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        rng = np.nanmax(g, axis=1) - np.nanmin(g, axis=1)
        s = np.nanstd(g, axis=1, ddof=1)
    rng = np.where(n_i >= 2, rng, np.nan)
    s = np.where(n_i >= 2, s, np.nan)
    return n_i, means, rng, s


def sigma_subgroups(g: np.ndarray, method: str = "pooled") -> float:
    """Sigma a partir de subgrupos (matriz k x m con NaN de relleno)."""
    n_i, _, rng, s = subgroup_stats(g)
    valid = n_i >= 2
    if not valid.any():
        raise ValueError(
            "Ningún subgrupo tiene 2 o más observaciones; no se puede estimar sigma."
        )
    if method == "rbar":
        return float(np.mean(rng[valid] / vec(d2, n_i)[valid]))
    if method == "sbar":
        return float(np.mean(s[valid] / vec(c4, n_i)[valid]))
    if method == "pooled":
        dof = float(np.sum(n_i[valid] - 1))
        sp = np.sqrt(np.sum((n_i[valid] - 1) * s[valid] ** 2) / dof)
        return float(sp / c4(int(dof) + 1))
    raise ValueError("sigma_method debe ser 'rbar', 'sbar' o 'pooled'.")
