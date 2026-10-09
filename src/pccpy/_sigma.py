"""Estimadores de la desviación estándar del proceso (sigma *within*).

Fórmulas según la documentación de métodos de Minitab:

* Individuales: rango móvil promedio / d2(span), mediana del rango móvil / 0.954
  (span = 2) o raíz cuadrada de la media de las diferencias cuadradas sucesivas (MSSD).
* Subgrupos: Rbar, Sbar o desviación estándar combinada (pooled) con factor c4. Con tamaños de subgrupo desiguales,
  Rbar y Sbar promedian las estimaciones de cada subgrupo con pesos de varianza inversa (los de Minitab):
  ``w_i = d2(n_i)² / d3(n_i)²`` para ``R_i / d2(n_i)`` y ``w_i = c4(n_i)² / (1 − c4(n_i)²)`` para ``s_i / c4(n_i)``.
  Con tamaño constante los pesos son iguales y es el promedio simple.
"""
from __future__ import annotations

import warnings
from typing import Callable

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ._constants import c4, d2, d3
from ._i18n import tr

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
        raise ValueError(tr("'span' debe ser >= 2."))
    out = np.full(x.shape, np.nan)
    if x.size >= span:
        w = sliding_window_view(x, span)
        out[span - 1 :] = w.max(axis=1) - w.min(axis=1)
    return out


def sigma_individuals(x: np.ndarray, method: str = "mr", span: int = 2) -> float:
    """Sigma a partir de observaciones individuales."""
    if x.size < 2:
        raise ValueError(tr("Se necesitan al menos 2 observaciones para estimar sigma."))
    if method == "mr":
        if x.size < span:
            raise ValueError(tr(
                "Se necesitan al menos {span} observaciones (span={span})."
            ).format(span=span))
        return float(np.nanmean(moving_range(x, span)) / d2(span))
    if method == "median_mr":
        if span != 2:
            raise ValueError(tr("'median_mr' solo está disponible con span = 2."))
        return float(np.nanmedian(moving_range(x, 2)) / MEDIAN_MR_CONSTANT)
    if method == "mssd":
        return float(np.sqrt(np.sum(np.diff(x) ** 2) / (2.0 * (x.size - 1))))
    raise ValueError(tr("sigma_method debe ser 'mr', 'median_mr' o 'mssd'."))


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
            tr("Ningún subgrupo tiene 2 o más observaciones; no se puede estimar sigma.")
        )
    iguales = bool(np.all(n_i[valid] == n_i[valid][0]))  # con tamaño constante los pesos son iguales: promedio simple
    if method == "rbar":
        d2v, d3v = vec(d2, n_i)[valid], vec(d3, n_i)[valid]
        if iguales:
            return float(np.mean(rng[valid] / d2v))
        w = d2v**2 / d3v**2  # 1 / Var(R_i / d2) ∝ d2² / d3²
        return float(np.sum(w * rng[valid] / d2v) / np.sum(w))
    if method == "sbar":
        c4v = vec(c4, n_i)[valid]
        if iguales:
            return float(np.mean(s[valid] / c4v))
        w = c4v**2 / (1.0 - c4v**2)  # 1 / Var(s_i / c4) ∝ c4² / (1 − c4²)
        return float(np.sum(w * s[valid] / c4v) / np.sum(w))
    if method == "pooled":
        dof = float(np.sum(n_i[valid] - 1))
        sp = np.sqrt(np.sum((n_i[valid] - 1) * s[valid] ** 2) / dof)
        return float(sp / c4(int(dof) + 1))
    raise ValueError(tr("sigma_method debe ser 'rbar', 'sbar' o 'pooled'."))
