"""Motor común: calcula cada etapa por separado y ensambla el resultado."""
from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy import stats

from .. import rules
from .._data import stage_slices
from .._i18n import N_, tr
from ..results import ControlChart, Panel
from ..transforms import Transformation, fit_transformation


@dataclass
class StagePanel:
    """Panel calculado para *una* etapa (arrays de la longitud de la etapa)."""

    name: str
    values: np.ndarray
    center: np.ndarray
    ucl: np.ndarray
    lcl: np.ndarray
    sigma: np.ndarray
    ylabel: str
    family: str = "full"  # 'full' | 'basic' | 'only1' (ver rules.FAMILIES)
    secondary: np.ndarray | None = None
    symmetric: bool = True
    violations: dict[int | str, np.ndarray] | None = None  # si viene dado, se omiten las pruebas
    dist: dict | None = None  # distribución en control del estadístico: {"family": ..., parámetros por punto}


def _unir_dist(por_etapa: list) -> dict | None:
    """Concatena la distribución de cada etapa (``None`` si la carta no tiene una distribución conocida)."""
    if not por_etapa or por_etapa[0] is None:
        return None
    return {"family": por_etapa[0]["family"],
            **{k: np.concatenate([np.atleast_1d(d[k]) for d in por_etapa]) for k in por_etapa[0] if k != "family"}}


def full(value, n: int) -> np.ndarray:
    return np.full(n, value, dtype=float)


@dataclass(frozen=True)
class Limits:
    """Ancho de los límites de control en sigmas (``upper`` arriba, ``lower`` abajo) y si las zonas se reescalan con ellos."""

    upper: float = 3.0
    lower: float = 3.0
    rescale_zones: bool = False

    @property
    def default(self) -> bool:
        return self.upper == 3.0 and self.lower == 3.0


def _real(valor) -> bool:
    return isinstance(valor, (int, float, np.integer, np.floating)) and not isinstance(valor, (bool, np.bool_))


def _par(valor, nombre: str) -> tuple:
    """Un valor o una pareja (superior, inferior) -> ``(superior, inferior, es_pareja)``."""
    if isinstance(valor, (list, tuple, np.ndarray)):
        if len(valor) != 2:
            raise ValueError(tr("'{nombre}' debe ser un número o una pareja (superior, inferior); recibido: {valor!r}.").format(
                nombre=nombre, valor=valor))
        return valor[0], valor[1], True
    return valor, valor, False


def resolve_limits(k=None, alpha=None, rescale_zones: bool = False) -> Limits:
    """Valida ``k``/``alpha`` y devuelve los anchos de los límites (S014-RF-08 y RF-11).

    ``k`` es un número (los dos lados) o una pareja ``(k_superior, k_inferior)``. ``alpha`` es la probabilidad **bilateral** de
    falsa alarma de un panel normal si es un número (``k = Φ⁻¹(1 − α/2)``) y la **unilateral** de cada lado si es una pareja
    (``k = Φ⁻¹(1 − α)``). Sin ninguno de los dos, ``k = 3``.
    """
    if not isinstance(rescale_zones, (bool, np.bool_)):
        raise ValueError(tr("'rescale_zones' debe ser True o False; recibido: {valor!r}.").format(valor=rescale_zones))  # noqa: TRY004
    if k is not None and alpha is not None:
        raise ValueError(tr("Indica 'k' o 'alpha', no los dos."))
    if alpha is not None:
        a_sup, a_inf, es_par = _par(alpha, "alpha")
        for a in (a_sup, a_inf):
            if not _real(a) or not 0.0 < float(a) < 1.0:
                raise ValueError(tr("'alpha' debe ser un número entre 0 y 1 (exclusivos); recibido: {valor!r}.").format(valor=alpha))
        f = (lambda a: stats.norm.isf(float(a))) if es_par else (lambda a: stats.norm.isf(float(a) / 2.0))
        return Limits(float(f(a_sup)), float(f(a_inf)), bool(rescale_zones))
    if k is None:
        return Limits(3.0, 3.0, bool(rescale_zones))
    k_sup, k_inf, _ = _par(k, "k")
    for v in (k_sup, k_inf):
        if not _real(v) or not np.isfinite(v) or v <= 0:
            raise ValueError(tr("'k' debe ser un número finito mayor que 0 (o una pareja de ellos); recibido: {valor!r}.").format(
                valor=k))
    return Limits(float(k_sup), float(k_inf), bool(rescale_zones))


def build_chart(
    kind: str,
    n_points: int,
    stages,
    stage_fn: Callable[[np.ndarray], tuple[list[StagePanel], dict]],
    tests,
    test_params: dict[int, float] | None = None,
    limits: Limits | None = None,
) -> ControlChart:
    """Ejecuta ``stage_fn`` en cada etapa, aplica las pruebas y concatena.

    Con ``limits`` (cartas con ancho de límites ajustable) la prueba 1 usa como umbral el ancho de cada lado, ``params`` guarda
    ``k_upper`` y ``k_lower`` y las zonas se reescalan si ``limits.rescale_zones``.
    """
    tests = rules.normalize_tests(tests)
    test_params = dict(test_params or {})
    if limits is not None and not limits.default and 1 in test_params \
            and not test_params[1] == limits.upper == limits.lower:
        warnings.warn(tr("'test_params[1]' ({umbral}) difiere del ancho de los límites (k = {superior} arriba y {inferior} abajo): "
                         "la prueba 1 usa {umbral} sigmas y marca puntos que no coinciden con los límites dibujados.").format(
            umbral=test_params[1], superior=limits.upper, inferior=limits.lower), UserWarning, stacklevel=5)
    acc: dict[str, dict] = {}
    params_list: list[dict] = []

    for label, idx in stage_slices(n_points, stages):
        panels, params = stage_fn(idx)
        params_list.append({"stage": label, **params,
                            **({"k_upper": limits.upper, "k_lower": limits.lower} if limits is not None else {})})
        for sp in panels:
            a = acc.setdefault(
                sp.name,
                {"sp": sp, "values": [], "center": [], "ucl": [], "lcl": [], "sigma": [],
                 "stage": [], "secondary": [], "viol": {}, "dist": []},
            )
            for key in ("values", "center", "ucl", "lcl", "sigma"):
                a[key].append(getattr(sp, key))
            a["stage"].append(np.full(len(idx), label, dtype=object))
            a["dist"].append(sp.dist)
            if sp.secondary is not None:
                a["secondary"].append(sp.secondary)

            found: dict[int | str, np.ndarray]
            if sp.violations is not None:
                found = sp.violations
            else:
                allowed = rules.FAMILIES[sp.family]
                wanted = [t for t in tests if t in allowed]
                found = dict(rules.apply_tests(
                    sp.values, sp.center, sp.sigma, wanted, test_params,
                    limits=None if limits is None else (limits.upper, limits.lower),
                    rescale_zones=limits is not None and limits.rescale_zones).items())
            for t, ii in found.items():
                a["viol"].setdefault(t, []).append(np.asarray(ii, dtype=int) + int(idx[0]))

    panels_out: list[Panel] = []
    for name, a in acc.items():
        sp = a["sp"]
        viol = {
            t: (np.concatenate(v) if v else np.array([], dtype=int))
            for t, v in sorted(a["viol"].items(), key=lambda kv: str(kv[0]))
        }
        panels_out.append(
            Panel(
                name=name,
                values=np.concatenate(a["values"]),
                center=np.concatenate(a["center"]),
                ucl=np.concatenate(a["ucl"]),
                lcl=np.concatenate(a["lcl"]),
                sigma=np.concatenate(a["sigma"]),
                stage=np.concatenate(a["stage"]),
                ylabel=sp.ylabel,
                violations=viol,
                secondary=np.concatenate(a["secondary"]) if a["secondary"] else None,
                symmetric=sp.symmetric,
                dist=_unir_dist(a["dist"]),
            )
        )
    return ControlChart(kind=kind, panels=panels_out, params=params_list,
                        tests=tests, test_params=test_params)


def check_method(method: str, allowed: Sequence[str], what: str = "sigma_method") -> None:
    if method not in allowed:
        raise ValueError(tr(
            "{what} debe ser uno de {allowed} (recibido: {method!r})."
        ).format(what=what, allowed=tuple(allowed), method=method))


#: Etiquetas del eje y de los paneles de dispersión cuando la carta lleva una transformación.
_YLABEL_TRANSFORMADO = {
    "Rango móvil": N_("Rango móvil (escala transformada)"),
    "Rango de la muestra": N_("Rango de la muestra (escala transformada)"),
    "Desv. est. de la muestra": N_("Desv. est. de la muestra (escala transformada)"),
}
_PANELES_DE_POSICION = ("I", "Xbar")


def resolver_transformacion(transform, datos, scale: str) -> Transformation | None:
    """Valida ``transform``/``scale`` y devuelve la transformación (ajustada a ``datos`` si se pidió por nombre)."""
    if scale not in ("original", "transformed"):
        raise ValueError(tr("'scale' debe ser 'original' o 'transformed' (recibido: {scale!r}).").format(scale=scale))
    if transform is None:
        return None
    if isinstance(transform, Transformation):
        return transform
    return fit_transformation(datos, transform)


def aplicar_escala(chart: ControlChart, t: Transformation, scale: str, originales: np.ndarray | None = None) -> ControlChart:
    """Anota la transformación en la carta y, con ``scale='original'``, lleva los paneles de posición a unidades originales.

    Las pruebas de causas especiales ya se evaluaron en la escala transformada (donde los datos son ~normales); aquí
    solo se cambia lo que se guarda y se dibuja. Los paneles de dispersión (MR, R, S) quedan en la escala transformada,
    porque su valor no tiene equivalente en unidades originales. ``originales`` son las observaciones sin transformar
    (se usan tal cual en el panel I, sin error de redondeo).
    """
    chart.transformation, chart.chart_scale = t, scale
    for panel in chart.panels:
        if panel.name not in _PANELES_DE_POSICION:
            panel.ylabel = _YLABEL_TRANSFORMADO.get(panel.ylabel, panel.ylabel)
            continue
        if scale != "original":
            continue
        centro_t, sigma_t = panel.center.copy(), panel.sigma.copy()
        panel.values = originales.copy() if (panel.name == "I" and originales is not None) else t.inverse(panel.values)
        panel.center, panel.ucl, panel.lcl = t.inverse(panel.center), t.inverse(panel.ucl), t.inverse(panel.lcl)
        panel.zones_upper = {k: t.inverse(centro_t + k * sigma_t) for k in (1, 2)}
        panel.zones_lower = {k: t.inverse(centro_t - k * sigma_t) for k in (1, 2)}
    return chart
