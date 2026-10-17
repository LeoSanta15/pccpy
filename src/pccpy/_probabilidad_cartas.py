"""Probabilidad de un valor en las cartas de control (``ControlChart.probability``).

Cada panel guarda la distribución en control de su estadístico por punto (``Panel.dist``): ``{"family": …, parámetros}``.
Aquí se traduce esa descripción a las funciones ``P(X < v)``, ``P(X > v)``, ``P(X ≤ v)`` y ``P(X ≥ v)`` y se reutiliza el núcleo
de ``_probabilidad.py`` (validación de los valores, arreglos, ``between``, resultado).
"""
from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.special import ndtr

from ._i18n import tr
from ._probabilidad import ProbabilityResult, calcular_probabilidad

_POSICION = ("I", "Xbar")  # paneles cuyos valores se pueden pedir en unidades originales cuando hay transformación


def _sin_ruido(k):
    """Redondea al entero más cercano los valores que solo difieren de él por error de coma flotante (0,07·100 ≠ 7)."""
    k = np.asarray(k, dtype=float)
    r = np.rint(k)
    return np.where(np.abs(k - r) <= 1e-9 * np.maximum(1.0, np.abs(k)), r, k)


def _incompatibles():
    return ValueError(tr("Los valores indicados y 'point' tienen formas incompatibles."))


def _normal(loc, scale):
    def lt(v):
        z = (np.asarray(v, dtype=float) - loc) / np.where(scale > 0, scale, 1.0)
        return np.where(scale > 0, ndtr(z), np.where(v < loc, 0.0, np.where(v > loc, 1.0, 0.5)))

    def gt(v):
        z = (np.asarray(v, dtype=float) - loc) / np.where(scale > 0, scale, 1.0)
        return np.where(scale > 0, ndtr(-z), np.where(v < loc, 1.0, np.where(v > loc, 0.0, 0.5)))

    return lt, gt


def _por_n(v, n, scale, f):
    """Evalúa ``f(z, n)`` agrupando por ``n`` (el rango de n normales necesita una distribución por cada n)."""
    v, n, scale = np.broadcast_arrays(np.asarray(v, dtype=float), np.asarray(n, dtype=float), np.asarray(scale, dtype=float))
    # con escala 0 el estadístico vale 0 con certeza: z = +inf si v > 0 y 0 si v <= 0
    z = np.where(scale > 0, v / np.where(scale > 0, scale, 1.0), np.where(v > 0, np.inf, 0.0))
    out = np.empty(z.shape)
    for ni in np.unique(n):
        m = n == ni
        out[m] = f(z[m], int(ni))
    return out


def _rango(n, scale):
    def lt(v):
        def f(z, ni):
            d = stats.studentized_range(ni, np.inf)
            fin = np.isfinite(z) & (z > 0)
            r = np.where(z > 0, 1.0, 0.0)
            if fin.any():
                r[fin] = d.cdf(z[fin])
            return r
        return _por_n(v, n, scale, f)

    def gt(v):
        def f(z, ni):
            d = stats.studentized_range(ni, np.inf)
            fin = np.isfinite(z) & (z > 0)
            r = np.where(z > 0, 0.0, 1.0)
            if fin.any():
                r[fin] = d.sf(z[fin])
            return r
        return _por_n(v, n, scale, f)

    return lt, gt


def _desviacion(n, scale):
    def lt(v):
        def f(z, ni):
            fin = np.isfinite(z) & (z > 0)
            r = np.where(z > 0, 1.0, 0.0)
            r[fin] = stats.chi2.cdf((ni - 1) * z[fin] ** 2, ni - 1)
            return r
        return _por_n(v, n, scale, f)

    def gt(v):
        def f(z, ni):
            fin = np.isfinite(z) & (z > 0)
            r = np.where(z > 0, 0.0, 1.0)
            r[fin] = stats.chi2.sf((ni - 1) * z[fin] ** 2, ni - 1)
            return r
        return _por_n(v, n, scale, f)

    return lt, gt


def _discreta(cdf_le, sf_gt, divisor):
    """P(Y < v), P(Y > v), P(Y ≤ v) y P(Y ≥ v) con ``Y = conteo/divisor`` y ``conteo`` discreto de soporte 0, 1, 2…"""
    def umbral(v):
        return _sin_ruido(np.asarray(v, dtype=float) * divisor)

    return (lambda v: cdf_le(np.ceil(umbral(v)) - 1), lambda v: sf_gt(np.floor(umbral(v))),
            lambda v: cdf_le(np.floor(umbral(v))), lambda v: sf_gt(np.ceil(umbral(v)) - 1))


def _funciones(d: dict):
    """``(P(X<v), P(X>v), P(X≤v) o None, P(X≥v) o None)`` de la distribución ``d`` (parámetros ya elegidos por punto)."""
    fam = d["family"]
    if fam == "normal":
        return (*_normal(d["loc"], d["scale"]), None, None)
    if fam == "range":
        return (*_rango(d["n"], d["scale"]), None, None)
    if fam == "sd":
        return (*_desviacion(d["n"], d["scale"]), None, None)
    if fam == "weibull":
        forma, escala = d["shape"], d["scale"]

        def lt(v):
            v = np.asarray(v, dtype=float)
            return np.where(v > 0, -np.expm1(-(np.where(v > 0, v, 1.0) / escala) ** forma), 0.0)

        def gt(v):
            v = np.asarray(v, dtype=float)
            return np.where(v > 0, np.exp(-(np.where(v > 0, v, 1.0) / escala) ** forma), 1.0)

        return lt, gt, None, None
    if fam == "binomial":
        n, p = d["n"], d["p"]
        return _discreta(lambda k: stats.binom.cdf(k, n, p), lambda k: stats.binom.sf(k, n, p), d["divisor"])
    if fam == "poisson":
        mu = d["mu"]
        return _discreta(lambda k: stats.poisson.cdf(k, mu), lambda k: stats.poisson.sf(k, mu), d["divisor"])
    if fam == "geometric":  # X = cantidad entre eventos (0, 1, 2…) y X + 1 ~ geométrica(p)
        p = d["p"]
        return _discreta(lambda k: stats.geom.cdf(k + 1, p), lambda k: stats.geom.sf(k + 1, p), 1.0)
    raise ValueError(tr("La carta no tiene una distribución conocida del estadístico graficado."))  # pragma: no cover


def _puntos(point, n_puntos: int):
    """Índices base 0 de ``point`` (``None`` si no se indicó) y su valor normalizado para el resultado."""
    if point is None:
        return None, None
    aviso = ValueError(tr("'point' debe ser un entero (o un arreglo de enteros) entre 1 y {n}.").format(n=n_puntos))
    arr = np.asarray(point)
    if arr.ndim > 1 or arr.size == 0 or arr.dtype == bool or not np.issubdtype(arr.dtype, np.integer):
        raise aviso
    if np.any(arr < 1) or np.any(arr > n_puntos):
        raise aviso
    return arr - 1, (int(arr) if arr.ndim == 0 else arr)


def probabilidad_carta(chart, *, panel=None, below=None, above=None, between=None, point=None) -> ProbabilityResult:
    """Núcleo de ``ControlChart.probability``."""
    nombres = [p.name for p in chart.panels]
    if panel is None:
        panel_obj = chart.panels[0]
    elif isinstance(panel, str) and panel in nombres:
        panel_obj = chart[panel]
    else:
        raise ValueError(tr("'{panel}' no es un panel de la carta (paneles: {paneles}).").format(
            panel=panel, paneles=", ".join(nombres)))
    if panel_obj.dist is None:
        raise ValueError(tr("La carta {kind} no admite probability(): el estadístico que grafica no tiene una distribución "
                            "conocida en control.").format(kind=chart.kind))
    dist = panel_obj.dist
    n_puntos = len(panel_obj.values)
    indices, point_res = _puntos(point, n_puntos)
    if indices is None:
        parametros = [np.asarray(v) for k, v in dist.items() if k != "family"]
        if any(np.any(a != a[0]) for a in parametros):
            raise ValueError(tr("La distribución del estadístico cambia entre los puntos de la carta (tamaño de muestra, "
                                "etapas o ponderación): indica 'point=' con el punto (base 1) o los puntos que quieres."))
        indices = 0
    elegidos = {k: (v if k == "family" else np.asarray(v)[indices]) for k, v in dist.items()}
    lt, gt, le, ge = _funciones(elegidos)

    def seguro(f):
        def g(v):
            try:
                return f(v)
            except ValueError as e:  # numpy: formas que no se pueden combinar
                raise _incompatibles() from e
        return g

    lcl = np.asarray(panel_obj.lcl, dtype=float)[indices]
    ucl = np.asarray(panel_obj.ucl, dtype=float)[indices]
    escala = None
    if chart.transformation is not None and chart.chart_scale == "original" and panel_obj.name in _POSICION:
        escala = chart.transformation.forward
    return calcular_probabilidad(
        seguro(lt), seguro(gt), lsl=None if np.all(np.isnan(lcl)) else lcl, usl=None if np.all(np.isnan(ucl)) else ucl,
        below=below, above=above, between=between, sigma=None, opportunities=1, escala=escala,
        cdf_le=None if le is None else seguro(le), sf_ge=None if ge is None else seguro(ge),
        es_defecto=False, panel=panel_obj.name, point=point_res)
