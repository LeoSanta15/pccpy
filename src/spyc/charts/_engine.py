"""Motor común: calcula cada etapa por separado y ensambla el resultado."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .. import rules
from .._data import stage_slices
from ..results import ControlChart, Panel


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
    secondary: Optional[np.ndarray] = None
    symmetric: bool = True
    violations: Optional[Dict[int, np.ndarray]] = None  # si viene dado, se omiten las pruebas


def full(value, n: int) -> np.ndarray:
    return np.full(n, value, dtype=float)


def build_chart(
    kind: str,
    n_points: int,
    stages,
    stage_fn: Callable[[np.ndarray], Tuple[List[StagePanel], dict]],
    tests,
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Ejecuta ``stage_fn`` en cada etapa, aplica las pruebas y concatena."""
    tests = rules.normalize_tests(tests)
    test_params = dict(test_params or {})
    acc: Dict[str, dict] = {}
    params_list: List[dict] = []

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

    panels_out: List[Panel] = []
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
        raise ValueError(f"{what} debe ser uno de {tuple(allowed)} (recibido: {method!r}).")
