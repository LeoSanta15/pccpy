"""Cartas de control para datos continuos: I-MR, X-barra-R y X-barra-S."""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from .._constants import c4, c5, d2, d3
from .._data import as_1d, to_subgroups
from .._sigma import moving_range, sigma_individuals, sigma_subgroups, subgroup_stats, vec
from ..results import ControlChart
from ._engine import StagePanel, build_chart, check_method, full


def imr_chart(
    x,
    *,
    span: int = 2,
    sigma_method: str = "mr",
    mu: Optional[float] = None,
    sigma: Optional[float] = None,
    stages=None,
    tests=(1,),
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Carta de valores individuales y rango móvil (Stat > Control Charts > I-MR).

    Parameters
    ----------
    x : array-like
        Observaciones individuales en orden temporal.
    span : int
        Longitud del rango móvil (por defecto 2, como Minitab).
    sigma_method : {'mr', 'median_mr', 'mssd'}
        Estimador de sigma: rango móvil promedio (por defecto), mediana del rango
        móvil (solo span=2) o raíz de la media de diferencias cuadradas sucesivas.
    mu, sigma : float, opcional
        Parámetros históricos; si se dan, no se estiman de los datos.
    stages : array-like, opcional
        Etiqueta de etapa por observación; los límites se calculan por etapa.
    tests : 'all' | int | iterable | None
        Pruebas de causas especiales (1-8). Por defecto solo la prueba 1, igual que Minitab.
    test_params : dict, opcional
        Valor K por prueba, p. ej. ``{2: 8}``.
    """
    x = as_1d(x)
    if span < 2:
        raise ValueError("'span' debe ser >= 2.")
    check_method(sigma_method, ("mr", "median_mr", "mssd"))
    dd2, dd3 = d2(span), d3(span)

    def stage_fn(idx):
        xs = x[idx]
        n = xs.size
        m = float(xs.mean()) if mu is None else float(mu)
        s = float(sigma) if sigma is not None else sigma_individuals(xs, sigma_method, span)
        i_panel = StagePanel(
            "I", xs, full(m, n), full(m + 3 * s, n), full(m - 3 * s, n), full(s, n),
            "Valor individual", "full",
        )
        c = dd2 * s
        mr_panel = StagePanel(
            "MR", moving_range(xs, span), full(c, n), full(c + 3 * dd3 * s, n),
            full(max(0.0, c - 3 * dd3 * s), n), full(dd3 * s, n),
            "Rango móvil", "basic", symmetric=False,
        )
        return [i_panel, mr_panel], {"media": m, "sigma": s, "MR_prom": c, "n": n}

    return build_chart("I-MR", x.size, stages, stage_fn, tests, test_params)


def _xbar_chart(kind, disp, data, subgroup_size, subgroup, sigma_method, mu, sigma,
                stages, tests, test_params) -> ControlChart:
    g = to_subgroups(data, subgroup_size, subgroup)

    def stage_fn(idx):
        gs = g[idx]
        n_i, means, rng, s_i = subgroup_stats(gs)
        k = len(idx)
        m = float(np.nansum(gs) / n_i.sum()) if mu is None else float(mu)
        sg = float(sigma) if sigma is not None else sigma_subgroups(gs, sigma_method)
        sig_x = sg / np.sqrt(n_i)
        x_panel = StagePanel(
            "Xbar", means, full(m, k), m + 3 * sig_x, m - 3 * sig_x, sig_x,
            "Media de la muestra", "full",
        )
        if disp == "r":
            c, sd = sg * vec(d2, n_i), sg * vec(d3, n_i)
            d_panel = StagePanel(
                "R", rng, c, c + 3 * sd, np.maximum(0.0, c - 3 * sd), sd,
                "Rango de la muestra", "basic", symmetric=False,
            )
        else:
            c, sd = sg * vec(c4, n_i), sg * vec(c5, n_i)
            d_panel = StagePanel(
                "S", s_i, c, c + 3 * sd, np.maximum(0.0, c - 3 * sd), sd,
                "Desv. est. de la muestra", "basic", symmetric=False,
            )
        size = int(n_i[0]) if n_i.min() == n_i.max() else "variable"
        return [x_panel, d_panel], {"media": m, "sigma": sg, "subgrupos": k, "tamaño": size}

    return build_chart(kind, g.shape[0], stages, stage_fn, tests, test_params)


def xbar_r_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    subgroup=None,
    sigma_method: str = "rbar",
    mu: Optional[float] = None,
    sigma: Optional[float] = None,
    stages=None,
    tests=(1,),
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Carta X-barra y R (Stat > Control Charts > Xbar-R).

    ``data``: matriz 2-D (una fila por subgrupo), o vector 1-D junto con
    ``subgroup_size`` (tamaño fijo) o ``subgroup`` (identificador de subgrupo por
    observación, admite tamaños desiguales).

    ``sigma_method``: ``'rbar'`` (por defecto) o ``'pooled'``.
    Con tamaños desiguales, sigma se estima promediando R_i/d2(n_i) (ver README).
    """
    check_method(sigma_method, ("rbar", "pooled"))
    return _xbar_chart("Xbar-R", "r", data, subgroup_size, subgroup, sigma_method,
                       mu, sigma, stages, tests, test_params)


def xbar_s_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    subgroup=None,
    sigma_method: str = "sbar",
    mu: Optional[float] = None,
    sigma: Optional[float] = None,
    stages=None,
    tests=(1,),
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Carta X-barra y S (Stat > Control Charts > Xbar-S).

    Igual que :func:`xbar_r_chart` pero la dispersión se mide con la desviación
    estándar. ``sigma_method``: ``'sbar'`` (por defecto) o ``'pooled'``.
    """
    check_method(sigma_method, ("sbar", "pooled"))
    return _xbar_chart("Xbar-S", "s", data, subgroup_size, subgroup, sigma_method,
                       mu, sigma, stages, tests, test_params)
