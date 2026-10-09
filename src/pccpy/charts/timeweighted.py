"""Cartas de control de peso temporal: EWMA y CUSUM (tabular)."""
from __future__ import annotations

import numpy as np

from .._data import as_1d, to_subgroups
from .._i18n import N_, tr
from .._labels import con_etiquetas
from .._sigma import sigma_individuals, sigma_subgroups
from ..results import ControlChart
from ._engine import StagePanel, build_chart, check_method, full


def _series_etapas(data, subgroup_size, subgroup, value=None, sigma_method=None):
    """Devuelve (medias por punto, n por subgrupo, estimador ``estimar(idx) -> (sigma, media global)`` por etapa).

    ``sigma_method``: con individuales ``'mr'`` (por defecto), ``'median_mr'`` o ``'mssd'``; con subgrupos ``'rbar'``
    (por defecto), ``'sbar'`` o ``'pooled'``.
    """
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 1 and subgroup_size is None and subgroup is None and value is None:
        x = as_1d(arr)
        metodo = sigma_method or "mr"
        check_method(metodo, ("mr", "median_mr", "mssd"))
        return x, 1, lambda idx: (sigma_individuals(x[idx], metodo, 2), float(x[idx].mean()))
    g, n_complete = to_subgroups(data, subgroup_size, subgroup, value=value)
    # Verificar subgrupos completos (el incompleto tiene NaN por diseño)
    if np.isnan(g[:n_complete]).any():
        raise ValueError(tr("EWMA/CUSUM/MA requieren subgrupos de igual tamaño (sin valores faltantes)."))
    n = g.shape[1]
    g_lim = g[:n_complete]
    metodo = sigma_method or "rbar"
    check_method(metodo, ("rbar", "sbar", "pooled") if n > 1 else ("mr", "median_mr", "mssd"))
    means = np.nanmean(g, axis=1)

    def estimar(idx):
        filas = idx[idx < n_complete]  # el subgrupo incompleto no entra en la estimación
        sub = g_lim[filas]
        sigma = sigma_subgroups(sub, metodo) if n > 1 else sigma_individuals(sub[:, 0], metodo, 2)
        return sigma, float(np.nanmean(sub))

    return means, n, estimar


def _series(data, subgroup_size, subgroup, value=None):
    """Devuelve (medias por punto, n por subgrupo, sigma estimada, media global) con el método por defecto."""
    means, n, estimar = _series_etapas(data, subgroup_size, subgroup, value=value)
    sigma, grand = estimar(np.arange(len(means)))
    return means, n, sigma, grand


@con_etiquetas
def ewma_chart(
    data,
    *,
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
    weight: float = 0.2,
    k: float = 3.0,
    target: float | None = None,
    sigma: float | None = None,
    sigma_method: str | None = None,
    stages=None,
) -> ControlChart:
    """Carta de media móvil exponencialmente ponderada (EWMA).

    ``weight`` (lambda, por defecto 0.2) y ``k`` (ancho de los límites en sigmas,
    por defecto 3) coinciden con los valores por defecto de Minitab. Los límites
    son los exactos, que se ensanchan al inicio de la serie. ``target`` y
    ``sigma`` se estiman de los datos si no se dan.

    ``sigma_method``: estimador de sigma. Con individuales ``'mr'`` (rango móvil promedio, por defecto), ``'median_mr'``
    o ``'mssd'``; con subgrupos ``'rbar'`` (por defecto), ``'sbar'`` o ``'pooled'``. ``stages``: etiqueta de etapa por
    punto; el objetivo y sigma se estiman por etapa (salvo que se den) y la EWMA **se reinicia** en el objetivo al
    empezar cada etapa.

    Acepta los mismos formatos de entrada que :func:`xbar_r_chart` (matriz 2-D,
    vector 1-D + ``subgroup_size``, o DataFrame largo con ``subgroup`` + ``value``).
    """
    if not 0 < weight <= 1:
        raise ValueError(tr("'weight' debe estar en (0, 1]."))
    means, n, estimar = _series_etapas(data, subgroup_size, subgroup, value=value, sigma_method=sigma_method)

    def stage_fn(idx):
        sigma_est, grand = estimar(idx)
        s = float(sigma) if sigma is not None else sigma_est
        t0 = float(target) if target is not None else grand
        s_x = s / np.sqrt(n)
        xs = means[idx]
        N = len(xs)
        z = np.empty(N)
        prev = t0
        for i, xb in enumerate(xs):
            prev = weight * xb + (1 - weight) * prev
            z[i] = prev
        i_arr = np.arange(1, N + 1)
        sig_t = s_x * np.sqrt(weight / (2 - weight) * (1 - (1 - weight) ** (2 * i_arr)))
        ucl, lcl = t0 + k * sig_t, t0 - k * sig_t
        flagged = np.flatnonzero((z > ucl) | (z < lcl))
        panel = StagePanel("EWMA", z, full(t0, N), ucl, lcl, sig_t, "EWMA", "only1",
                           violations={1: flagged})
        return [panel], {"objetivo": t0, "sigma": s, "peso": weight, "k": k, "n_subgrupo": n}

    return build_chart("EWMA", len(means), stages, stage_fn, (1,), {1: k})


@con_etiquetas
def cusum_chart(
    data,
    *,
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
    target: float | None = None,
    sigma: float | None = None,
    h: float = 4.0,
    k: float = 0.5,
    headstart: float = 0.0,
    sigma_method: str | None = None,
    stages=None,
) -> ControlChart:
    """Carta CUSUM tabular (Minitab: Stat > Control Charts > Time-Weighted > CUSUM).

    ``h`` (límite de decisión) y ``k`` (holgura) están en unidades de sigma del
    estadístico graficado; por defecto h=4 y k=0.5. Se grafica la suma superior
    (positiva) y la inferior (negativa) en las unidades originales de los datos.

    ``headstart``: arranque rápido (FIR, Lucas y Crosier, 1982) en unidades de sigma del estadístico: ambas sumas
    empiezan en ``headstart`` en lugar de 0 (por defecto 0; un valor habitual es ``h/2``), de modo que un desajuste
    inicial se detecta antes. Debe cumplir ``0 ≤ headstart < h``. ``sigma_method`` y ``stages`` funcionan como en
    :func:`ewma_chart`; las sumas se reinician (en ``headstart``) al empezar cada etapa.

    Acepta los mismos formatos de entrada que :func:`xbar_r_chart`.
    """
    if h <= 0 or k < 0:
        raise ValueError(tr("'h' debe ser > 0 y 'k' >= 0."))
    if not 0 <= headstart < h:
        raise ValueError(tr("'headstart' debe cumplir 0 <= headstart < h."))
    means, n, estimar = _series_etapas(data, subgroup_size, subgroup, value=value, sigma_method=sigma_method)

    def stage_fn(idx):
        sigma_est, grand = estimar(idx)
        s = float(sigma) if sigma is not None else sigma_est
        t0 = float(target) if target is not None else grand
        s_x = s / np.sqrt(n)
        xs = means[idx]
        N = len(xs)
        up, lo = np.zeros(N), np.zeros(N)
        cp = cm = float(headstart)
        for i, xb in enumerate(xs):
            zi = (xb - t0) / s_x
            cp = max(0.0, zi - k + cp)
            cm = max(0.0, -zi - k + cm)
            up[i], lo[i] = cp * s_x, -cm * s_x
        ucl, lcl = h * s_x, -h * s_x
        flagged = np.flatnonzero((up > ucl) | (lo < lcl))
        panel = StagePanel(
            "CUSUM", up, full(0.0, N), full(ucl, N), full(lcl, N), full(s_x, N),
            N_("Suma acumulada"), "only1", secondary=lo, violations={1: flagged},
        )
        return [panel], {"objetivo": t0, "sigma": s, "h": h, "k": k, "headstart": headstart, "n_subgrupo": n}

    return build_chart("CUSUM", len(means), stages, stage_fn, (1,), None)
