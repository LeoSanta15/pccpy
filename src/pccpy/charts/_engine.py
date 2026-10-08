"""Motor común: calcula cada etapa por separado y ensambla el resultado."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

import numpy as np

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
    violations: dict[int, np.ndarray] | None = None  # si viene dado, se omiten las pruebas


def full(value, n: int) -> np.ndarray:
    return np.full(n, value, dtype=float)


def build_chart(
    kind: str,
    n_points: int,
    stages,
    stage_fn: Callable[[np.ndarray], tuple[list[StagePanel], dict]],
    tests,
    test_params: dict[int, float] | None = None,
) -> ControlChart:
    """Ejecuta ``stage_fn`` en cada etapa, aplica las pruebas y concatena."""
    tests = rules.normalize_tests(tests)
    test_params = dict(test_params or {})
    acc: dict[str, dict] = {}
    params_list: list[dict] = []

    for label, idx in stage_slices(n_points, stages):
        panels, params = stage_fn(idx)
        params_list.append({"stage": label, **params})
        for sp in panels:
            a = acc.setdefault(
                sp.name,
                {"sp": sp, "values": [], "center": [], "ucl": [], "lcl": [], "sigma": [],
                 "stage": [], "secondary": [], "viol": {}},
            )
            for key in ("values", "center", "ucl", "lcl", "sigma"):
                a[key].append(getattr(sp, key))
            a["stage"].append(np.full(len(idx), label, dtype=object))
            if sp.secondary is not None:
                a["secondary"].append(sp.secondary)

            if sp.violations is not None:
                found = sp.violations
            else:
                allowed = rules.FAMILIES[sp.family]
                wanted = [t for t in tests if t in allowed]
                found = rules.apply_tests(sp.values, sp.center, sp.sigma, wanted, test_params)
            for t, ii in found.items():
                a["viol"].setdefault(t, []).append(np.asarray(ii, dtype=int) + int(idx[0]))

    panels_out: list[Panel] = []
    for name, a in acc.items():
        sp = a["sp"]
        viol = {
            t: (np.concatenate(v) if v else np.array([], dtype=int))
            for t, v in sorted(a["viol"].items())
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
