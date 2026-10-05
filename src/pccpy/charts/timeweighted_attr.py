"""EWMA y CUSUM para cartas de atributos: P, C y U.

Los límites siguen las fórmulas de Montgomery (Introduction to Statistical
Quality Control, 8ª ed.) y Lucas & Saccucci (1990):

* **EWMA-P/U/C**: Z_i = λ·Y_i + (1−λ)·Z_{i-1}; límites *exactos* que se
  ensanchan al inicio de la serie usando el factor √(1−(1−λ)^{2i}).
* **CUSUM-P/U/C**: esquema estandarizado (z-scores); h y k en unidades de σ.
  Con tamaño de muestra variable (P y U), se estandariza cada punto con su
  propia desviación estándar antes de acumular.
"""
from __future__ import annotations

import numpy as np

from .._i18n import N_, tr
from ..results import ControlChart
from ._engine import StagePanel, build_chart, full
from .attributes import _prep


# ─────────────────────────────────────────────── helpers compartidos ──────────
def _baseline(code: str, c: np.ndarray, n_arr: np.ndarray, hist) -> float:
    if hist is not None:
        return float(hist)
    if code in ("p", "u"):
        return float(c.sum() / n_arr.sum())
    return float(c.mean())  # c


def _sigma_attr(code: str, ctr: float, n_arr: np.ndarray) -> np.ndarray:
    if code == "p":
        return np.sqrt(ctr * (1 - ctr) / n_arr)
    if code == "u":
        return np.sqrt(ctr / n_arr)
    return np.full(len(n_arr), np.sqrt(ctr))  # c


# ─────────────────────────────────────────────────────────────── EWMA ─────────
def _ewma_attr(code: str, kind: str, ylabel: str,
               counts, n, historical, weight: float, k: float) -> ControlChart:
    c, n_arr = _prep(counts, n, need_n=code != "c")
    if code in ("p", "np") and np.any(c > n_arr):
        raise ValueError(tr("Hay conteos mayores que el tamaño de muestra."))
    if not 0 < weight <= 1:
        raise ValueError(tr("'weight' debe estar en (0, 1]."))

    ctr = _baseline(code, c, n_arr, historical)
    y = c / n_arr if code in ("p", "u") else c.astype(float)
    N = len(y)

    def stage_fn(idx):
        z = np.empty(N)
        prev = ctr
        for i, yi in enumerate(y):
            prev = weight * yi + (1 - weight) * prev
            z[i] = prev
        i_arr = np.arange(1, N + 1)
        factor = np.sqrt(weight / (2 - weight) * (1 - (1 - weight) ** (2 * i_arr)))
        sig_base = _sigma_attr(code, ctr, n_arr)
        sig_t = sig_base * factor
        ucl = ctr + k * sig_t
        lcl = np.maximum(0.0, ctr - k * sig_t)
        flagged = np.flatnonzero((z > ucl) | (z < lcl))
        panel = StagePanel(
            f"EWMA-{code.upper()}", z, full(ctr, N), ucl, lcl, sig_t,
            ylabel, "only1", symmetric=False, violations={1: flagged},
        )
        return [panel], {"centro": ctr, "peso": weight, "k": k}

    return build_chart(kind, N, None, stage_fn, (1,), {1: k})


def ewma_p_chart(
    defectives,
    n,
    *,
    p: float | None = None,
    weight: float = 0.2,
    k: float = 3.0,
) -> ControlChart:
    """EWMA para la proporción de defectuosos (equivalente a carta P suavizada).

    Parameters
    ----------
    defectives : array-like
        Conteo de unidades defectuosas por muestra.
    n : int o array-like
        Tamaño de muestra (constante o variable).
    p : float, opcional
        Proporción de referencia. Si no se da, se estima de los datos.
    weight : float
        Factor de suavizado λ ∈ (0, 1]. Por defecto 0.2 (igual que Minitab).
    k : float
        Ancho de los límites en sigmas. Por defecto 3.0.
    """
    return _ewma_attr("p", "EWMA-P", N_("Proporción EWMA"), defectives, n, p, weight, k)


def ewma_c_chart(
    defects,
    *,
    c: float | None = None,
    weight: float = 0.2,
    k: float = 3.0,
) -> ControlChart:
    """EWMA para el número de defectos por unidad de inspección (carta C suavizada).

    Parameters
    ----------
    defects : array-like
        Número de defectos por unidad.
    c : float, opcional
        Tasa media de defectos. Si no se da, se estima de los datos.
    weight : float
        Factor de suavizado λ. Por defecto 0.2.
    k : float
        Ancho de los límites en sigmas. Por defecto 3.0.
    """
    return _ewma_attr("c", "EWMA-C", N_("Conteo EWMA"), defects, None, c, weight, k)


def ewma_u_chart(
    defects,
    n,
    *,
    u: float | None = None,
    weight: float = 0.2,
    k: float = 3.0,
) -> ControlChart:
    """EWMA para los defectos por unidad con tamaño de muestra variable (carta U suavizada).

    Parameters
    ----------
    defects : array-like
        Conteo de defectos por muestra.
    n : int o array-like
        Área de oportunidad o tamaño de muestra.
    u : float, opcional
        Tasa media de defectos por unidad. Si no se da, se estima de los datos.
    weight : float
        Factor de suavizado λ. Por defecto 0.2.
    k : float
        Ancho de los límites en sigmas. Por defecto 3.0.
    """
    return _ewma_attr("u", "EWMA-U", N_("Defectos/unidad EWMA"), defects, n, u, weight, k)


# ─────────────────────────────────────────────────────────────── CUSUM ────────
def _cusum_attr(code: str, kind: str, ylabel: str,
                counts, n, historical, h: float, k: float) -> ControlChart:
    c, n_arr = _prep(counts, n, need_n=code != "c")
    if code in ("p", "np") and np.any(c > n_arr):
        raise ValueError(tr("Hay conteos mayores que el tamaño de muestra."))
    if h <= 0 or k < 0:
        raise ValueError(tr("'h' debe ser > 0 y 'k' >= 0."))

    ctr = _baseline(code, c, n_arr, historical)
    y = c / n_arr if code in ("p", "u") else c.astype(float)
    sig = _sigma_attr(code, ctr, n_arr)
    N = len(y)

    def stage_fn(idx):
        up = np.zeros(N)
        lo = np.zeros(N)
        cp = cm = 0.0
        for i, yi in enumerate(y):
            zi = (yi - ctr) / sig[i]
            cp = max(0.0, zi - k + cp)
            cm = max(0.0, -zi - k + cm)
            up[i], lo[i] = cp, -cm
        flagged = np.flatnonzero((up > h) | (lo < -h))
        # Sigma = 1 (estandarizado); límites en sigma units
        panel = StagePanel(
            f"CUSUM-{code.upper()}", up, full(0.0, N), full(h, N), full(-h, N),
            full(1.0, N), ylabel, "only1",
            secondary=lo, symmetric=True, violations={1: flagged},
        )
        return [panel], {"centro": ctr, "h": h, "k": k}

    return build_chart(kind, N, None, stage_fn, (1,), None)


def cusum_p_chart(
    defectives,
    n,
    *,
    p: float | None = None,
    h: float = 4.0,
    k: float = 0.5,
) -> ControlChart:
    """CUSUM tabular estandarizado para la proporción de defectuosos.

    Transforma cada observación a puntaje z = (p_i − p̄) / σ_i antes de acumular,
    lo que permite manejar tamaños de muestra variables. ``h`` y ``k`` están en
    unidades de σ (por defecto h=4, k=0.5).

    Parameters
    ----------
    defectives : array-like
        Conteo de unidades defectuosas por muestra.
    n : int o array-like
        Tamaño de muestra.
    p : float, opcional
        Proporción de referencia. Si no se da, se estima de los datos.
    h : float
        Límite de decisión en unidades de σ. Por defecto 4.0.
    k : float
        Holgura de referencia en unidades de σ. Por defecto 0.5.
    """
    return _cusum_attr("p", "CUSUM-P", N_("Suma acumulada P (σ)"), defectives, n, p, h, k)


def cusum_c_chart(
    defects,
    *,
    c: float | None = None,
    h: float = 4.0,
    k: float = 0.5,
) -> ControlChart:
    """CUSUM tabular estandarizado para el número de defectos (carta C).

    Parameters
    ----------
    defects : array-like
        Número de defectos por unidad de inspección.
    c : float, opcional
        Tasa media de defectos. Si no se da, se estima de los datos.
    h : float
        Límite de decisión en σ. Por defecto 4.0.
    k : float
        Holgura en σ. Por defecto 0.5.
    """
    return _cusum_attr("c", "CUSUM-C", N_("Suma acumulada C (σ)"), defects, None, c, h, k)


def cusum_u_chart(
    defects,
    n,
    *,
    u: float | None = None,
    h: float = 4.0,
    k: float = 0.5,
) -> ControlChart:
    """CUSUM tabular estandarizado para defectos por unidad (carta U).

    Parameters
    ----------
    defects : array-like
        Conteo de defectos por muestra.
    n : int o array-like
        Área de oportunidad o tamaño de muestra.
    u : float, opcional
        Tasa media de defectos por unidad. Si no se da, se estima de los datos.
    h : float
        Límite de decisión en σ. Por defecto 4.0.
    k : float
        Holgura en σ. Por defecto 0.5.
    """
    return _cusum_attr("u", "CUSUM-U", N_("Suma acumulada U (σ)"), defects, n, u, h, k)
