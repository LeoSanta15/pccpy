"""Cartas de control para atributos: P, NP, C, U y Laney P' / U'."""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from .._constants import d2
from .._data import as_1d
from ..results import ControlChart
from ._engine import StagePanel, build_chart, full


def _prep(counts, n, need_n: bool):
    c = as_1d(counts, "conteos")
    if np.any(c < 0):
        raise ValueError("Los conteos no pueden ser negativos.")
    if not need_n:
        return c, np.ones_like(c)
    if n is None:
        raise ValueError("Falta el tamaño de la muestra 'n'.")
    n_arr = np.asarray(n, dtype=float)
    if n_arr.ndim == 0:
        n_arr = np.full(c.shape, float(n_arr))
    elif n_arr.shape != c.shape:
        raise ValueError("'n' debe ser un escalar o tener la misma longitud que los conteos.")
    if np.any(n_arr <= 0) or not np.all(np.isfinite(n_arr)):
        raise ValueError("Los tamaños de muestra deben ser positivos.")
    return c, n_arr


def _attribute_chart(code, kind, ylabel, counts, n, stages, tests, test_params,
                     historical, laney) -> ControlChart:
    c, n_arr = _prep(counts, n, need_n=code != "c")
    if code in ("p", "np") and np.any(c > n_arr):
        raise ValueError("Hay conteos de defectuosos mayores que el tamaño de la muestra.")
    if code == "np" and not np.all(n_arr == n_arr[0]):
        raise ValueError("La carta NP requiere tamaño de muestra constante; use la carta P.")

    def stage_fn(idx):
        d, ni = c[idx], n_arr[idx]
        k = len(idx)
        if code == "p":
            ctr = historical if historical is not None else d.sum() / ni.sum()
            y, sig = d / ni, np.sqrt(ctr * (1 - ctr) / ni)
            lo, hi = 0.0, 1.0
        elif code == "np":
            p = historical if historical is not None else d.sum() / ni.sum()
            ctr = ni[0] * p
            y, sig = d, np.full(k, np.sqrt(ni[0] * p * (1 - p)))
            lo, hi = 0.0, float(ni[0])
        elif code == "c":
            ctr = historical if historical is not None else d.mean()
            y, sig = d, np.full(k, np.sqrt(ctr))
            lo, hi = 0.0, np.inf
        else:  # "u"
            ctr = historical if historical is not None else d.sum() / ni.sum()
            y, sig = d / ni, np.sqrt(ctr / ni)
            lo, hi = 0.0, np.inf

        params = {"centro": float(ctr), "n_puntos": k}
        if laney:
            if k < 2:
                raise ValueError("Laney requiere al menos 2 puntos por etapa.")
            with np.errstate(divide="ignore", invalid="ignore"):
                z = (y - ctr) / sig
            sigma_z = float(np.mean(np.abs(np.diff(z))) / d2(2))
            sig = sig * sigma_z
            params["sigma_z"] = sigma_z

        panel = StagePanel(
            code.upper(), y, full(ctr, k),
            np.minimum(hi, ctr + 3 * sig), np.maximum(lo, ctr - 3 * sig), sig,
            ylabel, "basic", symmetric=False,
        )
        return [panel], params

    return build_chart(kind, c.size, stages, stage_fn, tests, test_params)


def p_chart(defectives, n, *, p: Optional[float] = None, stages=None, tests=(1,),
            test_params: Optional[Dict[int, float]] = None) -> ControlChart:
    """Carta P: proporción de unidades defectuosas (n constante o variable)."""
    return _attribute_chart("p", "P", "Proporción", defectives, n, stages, tests,
                            test_params, p, laney=False)


def np_chart(defectives, n, *, p: Optional[float] = None, stages=None, tests=(1,),
             test_params: Optional[Dict[int, float]] = None) -> ControlChart:
    """Carta NP: número de defectuosos (n constante)."""
    return _attribute_chart("np", "NP", "Conteo", defectives, n, stages, tests,
                            test_params, p, laney=False)


def c_chart(defects, *, c: Optional[float] = None, stages=None, tests=(1,),
            test_params: Optional[Dict[int, float]] = None) -> ControlChart:
    """Carta C: número de defectos por unidad de inspección (tamaño constante)."""
    return _attribute_chart("c", "C", "Conteo", defects, None, stages, tests,
                            test_params, c, laney=False)


def u_chart(defects, n, *, u: Optional[float] = None, stages=None, tests=(1,),
            test_params: Optional[Dict[int, float]] = None) -> ControlChart:
    """Carta U: defectos por unidad (tamaño de muestra constante o variable)."""
    return _attribute_chart("u", "U", "Conteo por unidad", defects, n, stages, tests,
                            test_params, u, laney=False)


def laney_p_chart(defectives, n, *, stages=None, tests=(1,),
                  test_params: Optional[Dict[int, float]] = None) -> ControlChart:
    """Carta P' de Laney: corrige la sobredispersión/subdispersión de la carta P.

    Los límites se multiplican por sigma_z, estimada con el rango móvil promedio de
    los puntajes z estandarizados.
    """
    return _attribute_chart("p", "Laney P'", "Proporción", defectives, n, stages, tests,
                            test_params, None, laney=True)


def laney_u_chart(defects, n, *, stages=None, tests=(1,),
                  test_params: Optional[Dict[int, float]] = None) -> ControlChart:
    """Carta U' de Laney: corrige la sobredispersión/subdispersión de la carta U."""
    return _attribute_chart("u", "Laney U'", "Conteo por unidad", defects, n, stages, tests,
                            test_params, None, laney=True)
