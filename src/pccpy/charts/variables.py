"""Cartas de control para datos continuos: I-MR, X-barra-R y X-barra-S."""
from __future__ import annotations

import warnings

import numpy as np

from .._constants import c4, c5, cmed, d2, d3
from .._data import as_1d_con_huecos, avisar_asimetria_subgrupos, to_subgroups
from .._i18n import N_, tr
from .._labels import con_etiquetas
from .._sigma import moving_range, sigma_individuals, sigma_subgroups, subgroup_stats, vec
from ..results import ControlChart
from ._engine import (
    StagePanel,
    aplicar_escala,
    build_chart,
    check_method,
    full,
    resolve_center,
    resolve_limits,
    resolver_transformacion,
)


@con_etiquetas
def imr_chart(
    x,
    *,
    span: int = 2,
    sigma_method: str = "mr",
    mu: float | None = None,
    sigma: float | None = None,
    stages=None,
    tests=(1,),
    test_params: dict[int, float] | None = None,
    transform=None,
    scale: str = "original",
    k=None,
    alpha=None,
    rescale_zones: bool = False,
    center: str = "mean",
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
    transform : {None, 'boxcox', 'yeo-johnson', 'johnson'} o Transformation
        Normaliza los datos antes de calcular la carta (útil con datos asimétricos): los límites y las pruebas se
        calculan en la escala transformada. Se puede pasar una ``Transformation`` ya ajustada (p. ej.
        ``carta.transformation``) para aplicar la misma a datos nuevos. ``mu`` y ``sigma`` históricos, si se dan,
        están en la escala transformada (son los de ``carta.params``).
    scale : {'original', 'transformed'}
        Con ``transform``: escala en que se guarda y dibuja el panel I. ``'original'`` (por defecto) devuelve los
        valores, los límites y las líneas de 1 y 2 sigma en unidades originales (los límites quedan asimétricos);
        el panel MR se queda en la escala transformada. ``'transformed'`` deja todo en la escala transformada.
    k : float | (float, float), opcional
        Ancho de los límites en sigmas (por defecto 3). Un número da límites simétricos; una pareja ``(k_superior, k_inferior)``,
        límites distintos arriba y abajo. La prueba 1 marca lo que sale de los límites dibujados (salvo que ``test_params``
        traiga su propio umbral para la 1). No se combina con ``alpha``.
    alpha : float | (float, float), opcional
        Probabilidad de falsa alarma en lugar de ``k``: un número es **bilateral** (``k = Φ⁻¹(1 − α/2)``); una pareja
        ``(alpha_superior, alpha_inferior)`` es **unilateral** por lado (``k = Φ⁻¹(1 − α)``). Es exacta en el panel I (normal)
        y aproximada en el panel MR; ``carta.probability()`` da la probabilidad real.
    rescale_zones : bool
        Por defecto las zonas de las pruebas 2 a 8 siguen en 1σ y 2σ aunque cambie ``k``. Con ``True`` pasan a ``k/3`` y
        ``2k/3`` sigmas de cada lado.
    center : {'mean', 'median'}
        Línea central del panel I: la media (por defecto) o la mediana de las observaciones de la etapa. σ y los límites se
        calculan igual (``centro ± kσ``). La mediana no corrige las falsas alarmas de la prueba 1 con datos asimétricos (los límites
        siguen siendo simétricos; para eso está ``transform=``), pero hace que la prueba 2 no dependa de la distribución. No se combina
        con ``mu``.
    """
    limits = resolve_limits(k, alpha, rescale_zones)
    ku, kl = limits.upper, limits.lower
    center = resolve_center(center, mu)
    x = as_1d_con_huecos(x)
    t = resolver_transformacion(transform, x[np.isfinite(x)], scale)
    x_original = x
    if t is not None:
        x = t.forward(x)
    if span < 2:
        raise ValueError(tr("'span' debe ser >= 2."))
    check_method(sigma_method, ("mr", "median_mr", "mssd"))
    dd2, dd3 = d2(span), d3(span)

    def stage_fn(idx):
        xs = x[idx]
        n = int(np.count_nonzero(~np.isnan(xs)))  # observaciones válidas (los huecos no cuentan)
        m = (float(np.nanmedian(xs)) if center == "median" else float(np.nanmean(xs))) if mu is None else float(mu)
        s = float(sigma) if sigma is not None else sigma_individuals(xs, sigma_method, span)
        if s == 0:
            warnings.warn(tr("Sigma estimada = 0 (los datos no varían): los límites de control coinciden con la línea "
                             "central y ningún punto es informativo."), UserWarning, stacklevel=5)
        i_panel = StagePanel(
            "I", xs, full(m, xs.size), full(m + ku * s, xs.size), full(m - kl * s, xs.size), full(s, xs.size),
            N_("Valor individual"), "full",
            dist={"family": "normal", "loc": full(m, xs.size), "scale": full(s, xs.size)},
        )
        c = dd2 * s
        mr_panel = StagePanel(
            "MR", moving_range(xs, span), full(c, xs.size), full(c + ku * dd3 * s, xs.size),
            full(max(0.0, c - kl * dd3 * s), xs.size), full(dd3 * s, xs.size),
            N_("Rango móvil"), "only1", symmetric=False,
            dist={"family": "range", "n": full(span, xs.size), "scale": full(s, xs.size)},
        )
        return [i_panel, mr_panel], {"mean": m, "sigma": s, "mr_mean": c, "n": n, "center": center}

    chart = build_chart("I-MR", x.size, stages, stage_fn, tests, test_params, limits)
    return chart if t is None else aplicar_escala(chart, t, scale, originales=x_original)


def _xbar_chart(kind, disp, data, subgroup_size, subgroup, sigma_method, mu, sigma,
                stages, tests, test_params, value=None, transform=None, scale="original", limits=None,
                center="mean") -> ControlChart:
    ku, kl = limits.upper, limits.lower
    g, n_complete = to_subgroups(data, subgroup_size, subgroup, value=value)
    mediana = kind == "Median-R"
    if mediana:
        tamanos = np.sum(~np.isnan(g), axis=1)
        if tamanos.min() != tamanos.max():
            raise ValueError(tr("La carta de medianas requiere subgrupos del mismo tamaño (hay de {minimo} a {maximo} observaciones)."
                                ).format(minimo=int(tamanos.min()), maximo=int(tamanos.max())))
        if tamanos[0] < 2:
            raise ValueError(tr("La carta de medianas requiere subgrupos de al menos 2 observaciones."))
    t = resolver_transformacion(transform, g[~np.isnan(g)], scale)
    if t is None:
        avisar_asimetria_subgrupos(g[:n_complete], destino="carta", stacklevel=5)
    else:
        g = t.forward(g)
    total = g.shape[0]

    def stage_fn(idx):
        gs_all = g[idx]
        n_i, means, rng, s_i = subgroup_stats(gs_all)
        k = len(idx)

        # Subgrupos completos dentro de esta etapa (excluye el último si es incompleto)
        idx_complete = idx[idx < n_complete] if n_complete < total else idx
        gs_lim = g[idx_complete] if idx_complete.size > 0 else gs_all

        n_i_lim = subgroup_stats(gs_lim)[0]
        if mu is not None:
            m = float(mu)
        elif mediana:
            m = float(np.nanmean(np.nanmedian(gs_lim, axis=1)))  # promedio de las medianas de subgrupo
        elif center == "median":
            m = float(np.nanmedian(subgroup_stats(gs_lim)[1]))  # mediana de las medias de subgrupo
        else:
            m = float(np.nansum(gs_lim) / n_i_lim.sum())
        sg = float(sigma) if sigma is not None else sigma_subgroups(gs_lim, sigma_method)

        if mediana:
            sig_x = sg * vec(cmed, n_i)  # desviación estándar de la mediana de n observaciones
            x_panel = StagePanel(
                "Median", np.nanmedian(gs_all, axis=1), full(m, k), m + ku * sig_x, m - kl * sig_x, sig_x,
                N_("Mediana de la muestra"), "full",
                dist={"family": "median", "n": n_i, "loc": full(m, k), "scale": full(sg, k)},
            )
        else:
            sig_x = sg / np.sqrt(n_i)
            x_panel = StagePanel(
                "Xbar", means, full(m, k), m + ku * sig_x, m - kl * sig_x, sig_x,
                N_("Media de la muestra"), "full",
                dist={"family": "normal", "loc": full(m, k), "scale": sig_x},
            )
        if disp == "r":
            c, sd = sg * vec(d2, n_i), sg * vec(d3, n_i)
            d_panel = StagePanel(
                "R", rng, c, c + ku * sd, np.maximum(0.0, c - kl * sd), sd,
                N_("Rango de la muestra"), "basic", symmetric=False,
                dist={"family": "range", "n": n_i, "scale": full(sg, k)},
            )
        else:
            c, sd = sg * vec(c4, n_i), sg * vec(c5, n_i)
            d_panel = StagePanel(
                "S", s_i, c, c + ku * sd, np.maximum(0.0, c - kl * sd), sd,
                N_("Desv. est. de la muestra"), "basic", symmetric=False,
                dist={"family": "sd", "n": n_i, "scale": full(sg, k)},
            )
        size = int(n_i[0]) if n_i.min() == n_i.max() else "variable"
        return [x_panel, d_panel], {"mean": m, "sigma": sg, "subgroups": k, "size": size, "center": center}

    chart = build_chart(kind, total, stages, stage_fn, tests, test_params, limits)
    return chart if t is None else aplicar_escala(chart, t, scale)


@con_etiquetas
def xbar_r_chart(
    data,
    *,
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
    sigma_method: str = "rbar",
    mu: float | None = None,
    sigma: float | None = None,
    stages=None,
    tests=(1,),
    test_params: dict[int, float] | None = None,
    transform=None,
    scale: str = "original",
    k=None,
    alpha=None,
    rescale_zones: bool = False,
    center: str = "mean",
) -> ControlChart:
    """Carta X-barra y R (Stat > Control Charts > Xbar-R).

    Acepta tres formatos de entrada:

    * ``data`` 2-D (array o DataFrame ancho): cada fila es un subgrupo.
    * ``data`` 1-D (array o Series) + ``subgroup_size``: se parte en subgrupos de
      tamaño fijo. Si el total no es divisible, el último subgrupo incompleto se
      grafica con sus propios límites pero no entra en el cálculo de sigma ni media.
    * ``data`` DataFrame largo + ``subgroup`` (nombre de la columna de grupos) +
      ``value`` (nombre de la columna de valores; opcional si hay solo una columna
      numérica): convierte automáticamente al formato matricial.

    ``sigma_method``: ``'rbar'`` (por defecto) o ``'pooled'``.
    Con tamaños desiguales, sigma es el promedio de R_i/d2(n_i) ponderado por d2(n_i)²/d3(n_i)² (varianza inversa,
    como Minitab); con tamaño constante es el promedio simple.

    ``transform`` y ``scale`` funcionan como en :func:`imr_chart`: se normalizan todas las observaciones, los límites y
    las pruebas se calculan en la escala transformada y, con ``scale='original'`` (por defecto), el panel X̄ se
    devuelve en unidades originales; el panel R queda en la escala transformada.

    ``k``, ``alpha`` y ``rescale_zones`` ajustan el ancho de los límites y las zonas como en :func:`imr_chart`: ``k`` en sigmas del
    estadístico (un número o una pareja ``(superior, inferior)``) o ``alpha`` como probabilidad de falsa alarma. Los paneles de
    dispersión usan el mismo ``k``; allí ``alpha`` es una aproximación (la probabilidad real la da ``carta.probability()``).

    ``center``: ``'mean'`` (por defecto, la media de todas las observaciones) o ``'median'`` (la mediana de las medias de subgrupo de
    los subgrupos completos de la etapa); σ y los límites no cambian. No se combina con ``mu``.
    """
    limits = resolve_limits(k, alpha, rescale_zones)
    center = resolve_center(center, mu)
    check_method(sigma_method, ("rbar", "pooled"))
    return _xbar_chart("Xbar-R", "r", data, subgroup_size, subgroup, sigma_method,
                       mu, sigma, stages, tests, test_params, value=value, transform=transform, scale=scale, limits=limits, center=center)


@con_etiquetas
def xbar_s_chart(
    data,
    *,
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
    sigma_method: str = "sbar",
    mu: float | None = None,
    sigma: float | None = None,
    stages=None,
    tests=(1,),
    test_params: dict[int, float] | None = None,
    transform=None,
    scale: str = "original",
    k=None,
    alpha=None,
    rescale_zones: bool = False,
    center: str = "mean",
) -> ControlChart:
    """Carta X-barra y S (Stat > Control Charts > Xbar-S).

    Acepta los mismos formatos de entrada que :func:`xbar_r_chart`, incluidos ``transform`` y ``scale``.
    ``sigma_method``: ``'sbar'`` (por defecto) o ``'pooled'``. Con tamaños desiguales, sigma es el promedio de s_i/c4(n_i)
    ponderado por c4(n_i)²/(1 − c4(n_i)²) (varianza inversa).

    ``k``, ``alpha`` y ``rescale_zones`` ajustan el ancho de los límites y las zonas como en :func:`imr_chart`: ``k`` en sigmas del
    estadístico (un número o una pareja ``(superior, inferior)``) o ``alpha`` como probabilidad de falsa alarma. Los paneles de
    dispersión usan el mismo ``k``; allí ``alpha`` es una aproximación (la probabilidad real la da ``carta.probability()``).

    ``center``: ``'mean'`` (por defecto, la media de todas las observaciones) o ``'median'`` (la mediana de las medias de subgrupo de
    los subgrupos completos de la etapa); σ y los límites no cambian. No se combina con ``mu``.
    """
    limits = resolve_limits(k, alpha, rescale_zones)
    center = resolve_center(center, mu)
    check_method(sigma_method, ("sbar", "pooled"))
    return _xbar_chart("Xbar-S", "s", data, subgroup_size, subgroup, sigma_method,
                       mu, sigma, stages, tests, test_params, value=value, transform=transform, scale=scale, limits=limits, center=center)


@con_etiquetas
def median_r_chart(
    data,
    *,
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
    mu: float | None = None,
    sigma: float | None = None,
    stages=None,
    tests=(1,),
    test_params: dict[int, float] | None = None,
    k=None,
    alpha=None,
    rescale_zones: bool = False,
) -> ControlChart:
    """Carta de medianas de subgrupo y R (X̃-R).

    Grafica la mediana de cada subgrupo con la línea central en el promedio de las medianas (o ``mu``) y los límites
    ``centro ± 3·cmed(n)·σ``, con ``σ = R̄/d2(n)`` y ``cmed(n)`` la desviación estándar de la mediana de ``n`` normales estándar
    (el coeficiente ``Ã2 = 3·cmed(n)/d2(n)`` de Montgomery; ``n`` = 3, 5, 7, 9: 1.187, 0.691, 0.509, 0.412). El panel R es el de
    :func:`xbar_r_chart`. Acepta los mismos formatos de entrada, ``stages``, ``mu`` y ``sigma``, y ``k``/``alpha``/``rescale_zones``
    como :func:`imr_chart`.

    Los subgrupos deben tener el mismo tamaño ``n >= 2``. Solo los tamaños impares (3, 5, 7, 9) se contrastaron con la tabla
    publicada; ``cmed(n)`` se calcula por integración para cualquier ``n``. Con datos normales la mediana varía de 1.3 a 1.5 veces
    más que la media (``n`` = 3 a 9), así que esta carta es menos sensible que Xbar-R; ``carta.probability()`` usa la distribución exacta
    de la mediana (beta con ``n`` impar, integración con ``n`` par).
    """
    limits = resolve_limits(k, alpha, rescale_zones)
    return _xbar_chart("Median-R", "r", data, subgroup_size, subgroup, "rbar", mu, sigma, stages, tests, test_params,
                       value=value, limits=limits, center="mean_of_medians")
