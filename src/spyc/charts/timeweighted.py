"""Cartas de control de peso temporal: EWMA y CUSUM (tabular)."""
from __future__ import annotations

from typing import Optional

import numpy as np

from .._data import as_1d, to_subgroups
from .._sigma import sigma_individuals, sigma_subgroups
from ..results import ControlChart
from ._engine import StagePanel, build_chart, full


def _series(data, subgroup_size, subgroup):
    """Devuelve (medias por punto, n por subgrupo, sigma estimada, media global)."""
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 1 and subgroup_size is None and subgroup is None:
        x = as_1d(arr)
        return x, 1, sigma_individuals(x, "mr", 2), float(x.mean())
    g = to_subgroups(data, subgroup_size, subgroup)
    if np.isnan(g).any():
        raise ValueError("EWMA/CUSUM requieren subgrupos de igual tamaño (sin valores faltantes).")
    n = g.shape[1]
    sigma = sigma_subgroups(g, "rbar") if n > 1 else sigma_individuals(g[:, 0], "mr", 2)
    return g.mean(axis=1), n, sigma, float(g.mean())


def ewma_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    subgroup=None,
    weight: float = 0.2,
    k: float = 3.0,
    target: Optional[float] = None,
    sigma: Optional[float] = None,
) -> ControlChart:
    """Carta de media móvil exponencialmente ponderada (EWMA).

    ``weight`` (lambda, por defecto 0.2) y ``k`` (ancho de los límites en sigmas,
    por defecto 3) coinciden con los valores por defecto de Minitab. Los límites
    son los exactos, que se ensanchan al inicio de la serie. ``target`` y
    ``sigma`` se estiman de los datos si no se dan.
    """
    if not 0 < weight <= 1:
        raise ValueError("'weight' debe estar en (0, 1].")
    means, n, sigma_est, grand = _series(data, subgroup_size, subgroup)
    s = float(sigma) if sigma is not None else sigma_est
    t0 = float(target) if target is not None else grand
    s_x = s / np.sqrt(n)

    def stage_fn(idx):
        N = len(means)
        z = np.empty(N)
        prev = t0
        for i, xb in enumerate(means):
            prev = weight * xb + (1 - weight) * prev
            z[i] = prev
        i_arr = np.arange(1, N + 1)
        sig_t = s_x * np.sqrt(weight / (2 - weight) * (1 - (1 - weight) ** (2 * i_arr)))
        ucl, lcl = t0 + k * sig_t, t0 - k * sig_t
        flagged = np.flatnonzero((z > ucl) | (z < lcl))
        panel = StagePanel("EWMA", z, full(t0, N), ucl, lcl, sig_t, "EWMA", "only1",
                           violations={1: flagged})
        return [panel], {"objetivo": t0, "sigma": s, "peso": weight, "k": k, "n_subgrupo": n}

    return build_chart("EWMA", len(means), None, stage_fn, (1,), None)


def cusum_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    subgroup=None,
    target: Optional[float] = None,
    sigma: Optional[float] = None,
    h: float = 4.0,
    k: float = 0.5,
) -> ControlChart:
    """Carta CUSUM tabular (Minitab: Stat > Control Charts > Time-Weighted > CUSUM).

    ``h`` (límite de decisión) y ``k`` (holgura) están en unidades de sigma del
    estadístico graficado; por defecto h=4 y k=0.5. Se grafica la suma superior
    (positiva) y la inferior (negativa) en las unidades originales de los datos.
    """
    if h <= 0 or k < 0:
        raise ValueError("'h' debe ser > 0 y 'k' >= 0.")
    means, n, sigma_est, grand = _series(data, subgroup_size, subgroup)
    s = float(sigma) if sigma is not None else sigma_est
    t0 = float(target) if target is not None else grand
    s_x = s / np.sqrt(n)

    def stage_fn(idx):
        N = len(means)
        up, lo = np.zeros(N), np.zeros(N)
        cp = cm = 0.0
        for i, xb in enumerate(means):
            zi = (xb - t0) / s_x
            cp = max(0.0, zi - k + cp)
            cm = max(0.0, -zi - k + cm)
            up[i], lo[i] = cp * s_x, -cm * s_x
        ucl, lcl = h * s_x, -h * s_x
        flagged = np.flatnonzero((up > ucl) | (lo < lcl))
        panel = StagePanel(
            "CUSUM", up, full(0.0, N), full(ucl, N), full(lcl, N), full(s_x, N),
            "Suma acumulada", "only1", secondary=lo, violations={1: flagged},
        )
        return [panel], {"objetivo": t0, "sigma": s, "h": h, "k": k, "n_subgrupo": n}

    return build_chart("CUSUM", len(means), None, stage_fn, (1,), None)
