"""Cartas de control multivariadas: T² de Hotelling, varianza generalizada, MEWMA y MCUSUM.

Formulas según la documentación de métodos de Minitab y Montgomery (Introduction to
Statistical Quality Control, cap. 11). Los datos pueden ser observaciones
individuales (matriz N x p) o subgrupos (matriz 3-D m x n x p, o matriz N x p con
``subgroup_size``).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd
from scipy import optimize, stats

from .charts._engine import StagePanel, build_chart, full
from .results import ControlChart, MultivariateChart

#: Probabilidad de cola superior que usa Minitab en los límites de T²: 1 - Phi(3).
ALPHA = 0.00134989803156746

_OUT_OF_LIMIT = "1 punto fuera de los límites de control"


# ------------------------------------------------------------------------- datos
def _prepare(data, subgroup_size):
    """Devuelve (puntos m x p, n, S promedio, media global, nombres, m)."""
    names = None
    if isinstance(data, pd.DataFrame):
        names = [str(c) for c in data.columns]
        data = data.to_numpy(dtype=float)
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 3:
        if subgroup_size is not None:
            raise ValueError("Con datos 3-D no se debe indicar 'subgroup_size'.")
        grp = arr
    elif arr.ndim == 2:
        if subgroup_size is None or subgroup_size == 1:
            grp = None
        else:
            n = int(subgroup_size)
            if n < 2 or arr.shape[0] % n != 0:
                raise ValueError(
                    f"{arr.shape[0]} filas no se pueden dividir en subgrupos de {subgroup_size}."
                )
            grp = arr.reshape(-1, n, arr.shape[1])
    else:
        raise ValueError("Los datos deben ser una matriz N x p (o 3-D: subgrupos x n x p).")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Los datos contienen valores faltantes o infinitos.")
    p = arr.shape[-1]
    if p < 2:
        raise ValueError("Una carta multivariada necesita al menos 2 variables.")
    names = names or [f"X{j + 1}" for j in range(p)]

    if grp is None:
        pts, n = arr, 1
        cov = np.cov(arr, rowvar=False)
        grand = arr.mean(axis=0)
    else:
        n = grp.shape[1]
        pts = grp.mean(axis=1)
        cov = np.mean([np.cov(g, rowvar=False) for g in grp], axis=0)
        grand = pts.mean(axis=0)
    return pts, n, cov, grand, names, pts.shape[0]


def _check_cov(cov: np.ndarray) -> None:
    if cov.shape[0] != cov.shape[1] or not np.allclose(cov, cov.T):
        raise ValueError("La matriz de covarianzas debe ser cuadrada y simétrica.")
    if np.linalg.cond(cov) > 1e12:
        raise ValueError(
            "La matriz de covarianzas es singular o casi singular: hay variables "
            "(casi) linealmente dependientes o muy pocas observaciones."
        )


def _resolve_params(mu, cov, est_mu, est_cov, p, n_hist):
    """(media, cov, fase) donde fase es 'phase1', 'phase2' o 'known'."""
    if (mu is None) != (cov is None):
        raise ValueError("Indique 'mu' y 'cov' juntos (parámetros históricos) o ninguno.")
    if mu is None:
        if n_hist is not None:
            raise ValueError("'n_hist' solo aplica con parámetros históricos.")
        return est_mu, est_cov, "phase1"
    mu, cov = np.asarray(mu, dtype=float).ravel(), np.asarray(cov, dtype=float)
    if mu.size != p or cov.shape != (p, p):
        raise ValueError(f"'mu' debe tener {p} elementos y 'cov' ser {p} x {p}.")
    return mu, cov, ("known" if n_hist is None else "phase2")


# --------------------------------------------------------------------- T² Hotelling
def _t2_reference(p, m, n, alpha, phase):
    """(línea central, LCS) de T²: media y percentil 1-alpha de su distribución."""
    q = 1.0 - alpha
    if phase == "known":
        return float(p), float(stats.chi2.ppf(q, p))
    if n == 1:
        if phase == "phase1":
            if m - p - 1 <= 0:
                raise ValueError(f"Se necesitan más de {p + 1} observaciones (hay {m}).")
            ucl = (m - 1) ** 2 / m * stats.beta.ppf(q, p / 2, (m - p - 1) / 2)
            return p * (m - 1) / m, float(ucl)
        v2 = m - p
        if v2 <= 0:
            raise ValueError("'n_hist' debe ser mayor que el número de variables.")
        kk = p * (m + 1) * (m - 1) / (m * (m - p))
    else:
        v2 = m * n - m - p + 1
        if v2 <= 0:
            raise ValueError("Muy pocos datos para el número de variables (grados de libertad <= 0).")
        kk = (p * (m - 1) if phase == "phase1" else p * (m + 1)) * (n - 1) / v2
    center = kk * v2 / (v2 - 2) if v2 > 2 else float("nan")
    return float(center), float(kk * stats.f.ppf(q, p, v2))


def t2_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    mu=None,
    cov=None,
    n_hist: Optional[int] = None,
    alpha: float = ALPHA,
) -> MultivariateChart:
    """Carta T² de Hotelling (Stat > Control Charts > Multivariate > T-Squared).

    Parameters
    ----------
    data : DataFrame o array
        Matriz N x p de observaciones individuales; con ``subgroup_size`` las filas
        consecutivas se agrupan en subgrupos; también acepta un array 3-D
        (subgrupos x n x p). Los subgrupos deben tener igual tamaño.
    mu, cov : opcional
        Vector de medias y matriz de covarianzas históricos (deben darse juntos).
        Sin ellos se estiman de los datos y se usan límites de **Fase I**.
    n_hist : int, opcional
        Con parámetros históricos, número de subgrupos (u observaciones) con que se
        estimaron; usa los límites de **Fase II** basados en F. Sin ``n_hist`` los
        parámetros se toman como conocidos (límite chi-cuadrado).
    alpha : float
        Probabilidad de cola superior del límite (por defecto 0.00135, como Minitab).

    El resultado tiene un panel ``"T2"`` con LC = valor esperado de T² y LCS; no hay
    LCI. Use ``chart.contributions(punto)`` para ver qué variables explican una señal.
    """
    pts, n, s_est, grand, names, m = _prepare(data, subgroup_size)
    p = pts.shape[1]
    mean, S, phase = _resolve_params(mu, cov, grand, s_est, p, n_hist)
    _check_cov(S)
    m_ref = m if phase == "phase1" else (n_hist or m)
    center, ucl = _t2_reference(p, m_ref, n, alpha, phase)

    d = pts - mean
    t2 = n * np.einsum("ij,ij->i", d @ np.linalg.inv(S), d)
    flagged = np.flatnonzero(t2 > ucl)

    def stage_fn(idx):
        panel = StagePanel(
            "T2", t2, full(center, m), full(ucl, m), full(np.nan, m), full(np.nan, m),
            "T² de Hotelling", "only1", symmetric=False, violations={1: flagged},
        )
        return [panel], {"fase": {"phase1": "I", "phase2": "II", "known": "parámetros conocidos"}[phase],
                         "variables": p, "puntos": m, "tamaño": n, "alfa": alpha}

    base = build_chart("T²", m, None, stage_fn, (1,), None)
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=pts, mean=mean,
                             cov=S, scale=float(n))


# -------------------------------------------------------------- varianza generalizada
def _gv_constants(p: int, n: int):
    """b1 y b2 con E|S| = b1 |Sigma| y Var|S| = b2 |Sigma|² (S con divisor n-1)."""
    i = np.arange(1, p + 1)
    prod1 = np.prod(n - i, dtype=float)
    prod2 = np.prod(n - i + 2, dtype=float)
    b1 = prod1 / (n - 1) ** p
    b2 = prod1 * (prod2 - prod1) / (n - 1) ** (2 * p)
    return float(b1), float(b2)


def generalized_variance_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    cov=None,
    k: float = 3.0,
) -> MultivariateChart:
    """Carta de varianza generalizada |S| (dispersión multivariada).

    Grafica el determinante de la matriz de covarianzas de cada subgrupo, con
    LC = b1|S̄|, límites |S̄|(b1 ± k·√b2) (LCI no menor que 0) y S̄ el promedio de las
    matrices de covarianza de los subgrupos. Con ``cov`` (Sigma conocida) se usa
    |Sigma| en lugar de |S̄|. Requiere subgrupos de tamaño n > p.
    """
    if subgroup_size is None and np.asarray(data).ndim != 3:
        raise ValueError("La varianza generalizada requiere subgrupos: indique 'subgroup_size' o pase datos 3-D.")
    pts, n, s_est, _, names, m = _prepare(data, subgroup_size)
    p = pts.shape[1]
    if n <= p:
        raise ValueError(f"El tamaño de subgrupo ({n}) debe ser mayor que el número de variables ({p}).")
    arr = np.asarray(data.to_numpy() if isinstance(data, pd.DataFrame) else data, dtype=float)
    grp = arr if arr.ndim == 3 else arr.reshape(-1, n, p)
    dets = np.array([np.linalg.det(np.cov(g, rowvar=False)) for g in grp])
    if cov is None:
        sig = s_est
        known = False
    else:
        sig = np.asarray(cov, dtype=float)
        if sig.shape != (p, p):
            raise ValueError(f"'cov' debe ser {p} x {p}.")
        known = True
    _check_cov(sig)
    b1, b2 = _gv_constants(p, n)
    det_s = float(np.linalg.det(sig))
    center = b1 * det_s
    ucl = det_s * (b1 + k * np.sqrt(b2))
    lcl = max(0.0, det_s * (b1 - k * np.sqrt(b2)))
    flagged = np.flatnonzero((dets > ucl) | (dets < lcl))

    def stage_fn(idx):
        panel = StagePanel("|S|", dets, full(center, m), full(ucl, m), full(lcl, m),
                           full(np.nan, m), "Varianza generalizada", "only1",
                           symmetric=False, violations={1: flagged})
        return [panel], {"|S|": det_s, "variables": p, "subgrupos": m, "tamaño": n,
                         "sigma_conocida": known}

    base = build_chart("Varianza generalizada", m, None, stage_fn, (1,), None)
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=None, mean=None,
                             cov=sig, scale=float(n))


# ------------------------------------------------------------------------- MEWMA
def _mewma_arl(h: float, p: int, lam: float, cells: int = 300) -> float:
    """ARL en control de la MEWMA con límite h (cadena de Markov de Runger y Prabhu).

    Con datos N(0, I), s = |Z|² es una cadena de Markov exacta: |Z'|²/lam² sigue una
    chi-cuadrado no central con parámetro (1-lam)² s / lam². Se discretiza s en
    ``cells`` celdas hasta el umbral h·lam/(2-lam) (la señal es T² > h con la
    covarianza asintótica de Z).
    """
    c = h * lam / (2.0 - lam)
    edges = np.linspace(0.0, c, cells + 1)
    mid = 0.5 * (edges[:-1] + edges[1:])
    nc = (1.0 - lam) ** 2 * mid / lam**2
    cdf = stats.ncx2.cdf(edges[None, :] / lam**2, p, nc[:, None])
    trans = np.diff(cdf, axis=1)
    start = np.diff(stats.chi2.cdf(edges / lam**2, p))
    arl_from = np.linalg.solve(np.eye(cells) - trans, np.ones(cells))
    return float(1.0 + start @ arl_from)


@lru_cache(maxsize=64)
def mewma_limit(p: int, weight: float = 0.1, arl: float = 200.0) -> float:
    """Límite de control H de la MEWMA para un ARL en control dado.

    Resuelve ARL(H) = ``arl`` con la cadena de Markov de Runger y Prabhu (1996), la
    misma idea del programa de Bodden y Rigdon (1999) que cita Minitab. Con
    p=2, weight=0.1 y arl=200 da H ≈ 8.64 (Prabhu y Runger, 1997).
    """
    if arl <= 1:
        raise ValueError("'arl' debe ser > 1.")
    f = lambda h: np.log(_mewma_arl(h, p, weight)) - np.log(arl)
    lo, hi = 1e-3, 2.0 * p
    while f(hi) < 0:
        hi *= 2.0
    return float(optimize.brentq(f, lo, hi, xtol=1e-6))


def mewma_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    weight: float = 0.1,
    arl: float = 200.0,
    ucl: Optional[float] = None,
    mu=None,
    cov=None,
) -> MultivariateChart:
    """Carta MEWMA (EWMA multivariada, Stat > Control Charts > Multivariate > MEWMA).

    ``Z_i = weight·(x_i - mu) + (1 - weight)·Z_(i-1)`` con ``Z_0 = 0``; se grafica
    ``T²_i = Z_i' Sigma_Z^-1 Z_i`` con la covarianza asintótica de Z,
    ``weight/(2 - weight)·Sigma``. El límite ``H`` se calcula para que el ARL en
    control (desde ``Z_0 = 0``) sea ``arl`` (por defecto 200, como Minitab), o se
    fija con ``ucl``. Sirve para detectar cambios pequeños y
    sostenidos en el vector de medias. ``mu`` y ``cov`` se estiman si no se dan
    (deben darse juntos).
    """
    if not 0 < weight <= 1:
        raise ValueError("'weight' debe estar en (0, 1].")
    pts, n, s_est, grand, names, m = _prepare(data, subgroup_size)
    p = pts.shape[1]
    mean, S, _ = _resolve_params(mu, cov, grand, s_est, p, None)
    _check_cov(S)
    h = float(ucl) if ucl is not None else mewma_limit(p, float(weight), float(arl))

    sig_inv = np.linalg.inv(weight / (2.0 - weight) * S / n)  # covarianza asintótica de Z
    z = np.zeros(p)
    t2 = np.empty(m)
    for i in range(m):
        z = weight * (pts[i] - mean) + (1.0 - weight) * z
        t2[i] = z @ sig_inv @ z
    flagged = np.flatnonzero(t2 > h)

    def stage_fn(idx):
        panel = StagePanel("MEWMA", t2, full(np.nan, m), full(h, m), full(np.nan, m),
                           full(np.nan, m), "MEWMA (T²)", "only1", symmetric=False,
                           violations={1: flagged})
        return [panel], {"peso": weight, "LCS": h, "ARL": None if ucl is not None else arl,
                         "variables": p, "puntos": m, "tamaño": n}

    base = build_chart("MEWMA", m, None, stage_fn, (1,), None)
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=None, mean=mean,
                             cov=S, scale=float(n))


# ------------------------------------------------------------------------- MCUSUM
def _mcusum_arl(h: float, p: int, k: float, cells: int = 300) -> float:
    """ARL en control de la MCUSUM de Crosier con límite h.

    Con datos N(0, I), r = ||S|| es una cadena de Markov exacta: r' = máx(0, C - k) con
    C² chi-cuadrado no central (p gl, parámetro r²). Se discretiza (0, h] en ``cells``
    celdas más el estado r = 0, que tiene masa propia.
    """
    edges = np.linspace(0.0, h, cells + 1)
    states = np.r_[0.0, 0.5 * (edges[:-1] + edges[1:])]
    cdf = np.empty((cells + 1, cells + 1))
    cdf[0] = stats.chi2.cdf((edges + k) ** 2, p)  # desde r = 0 (centralidad 0)
    cdf[1:] = stats.ncx2.cdf((edges[None, :] + k) ** 2, p, states[1:, None] ** 2)
    trans = np.empty((cells + 1, cells + 1))
    trans[:, 0] = cdf[:, 0]  # P(C <= k): S vuelve a 0
    trans[:, 1:] = np.diff(cdf, axis=1)
    return float(np.linalg.solve(np.eye(cells + 1) - trans, np.ones(cells + 1))[0])


@lru_cache(maxsize=64)
def mcusum_limit(p: int, k: float = 0.5, arl: float = 200.0) -> float:
    """Límite de control h de la MCUSUM de Crosier para un ARL en control dado."""
    if arl <= 1:
        raise ValueError("'arl' debe ser > 1.")
    if k < 0:
        raise ValueError("'k' debe ser >= 0.")
    f = lambda h: np.log(_mcusum_arl(h, p, k)) - np.log(arl)
    lo, hi = 1e-3, 2.0 * p
    while f(hi) < 0:
        hi *= 2.0
    return float(optimize.brentq(f, lo, hi, xtol=1e-6))


def mcusum_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    k: float = 0.5,
    h: Optional[float] = None,
    arl: float = 200.0,
    mu=None,
    cov=None,
) -> MultivariateChart:
    """Carta CUSUM multivariada de Crosier (1988).

    Con ``d_t = x_t - mu`` y ``C_t = sqrt((S_(t-1) + d_t)' Sigma^-1 (S_(t-1) + d_t))``:
    ``S_t = 0`` si ``C_t <= k`` y ``S_t = (S_(t-1) + d_t)(1 - k/C_t)`` en otro caso. Se
    grafica ``Y_t = sqrt(S_t' Sigma^-1 S_t)`` y hay señal si ``Y_t > h``. ``k`` es la
    holgura (0.5 por defecto) y ``h`` se calcula para el ``arl`` en control pedido
    (200 por defecto) o se fija con ``h``. ``mu`` y ``cov`` se estiman si no se dan
    (deben darse juntos). Con subgrupos se usan las medias y Sigma/n.
    """
    if k < 0:
        raise ValueError("'k' debe ser >= 0.")
    pts, n, s_est, grand, names, m = _prepare(data, subgroup_size)
    p = pts.shape[1]
    mean, S, _ = _resolve_params(mu, cov, grand, s_est, p, None)
    _check_cov(S)
    if h is not None and h <= 0:
        raise ValueError("'h' debe ser > 0.")
    lim = float(h) if h is not None else mcusum_limit(p, float(k), float(arl))

    sig_inv = np.linalg.inv(S / n)
    s_vec = np.zeros(p)
    y = np.empty(m)
    for i in range(m):
        v = s_vec + (pts[i] - mean)
        c = float(np.sqrt(v @ sig_inv @ v))
        s_vec = v * (1.0 - k / c) if c > k else np.zeros(p)
        y[i] = np.sqrt(s_vec @ sig_inv @ s_vec)
    flagged = np.flatnonzero(y > lim)

    def stage_fn(idx):
        panel = StagePanel("MCUSUM", y, full(0.0, m), full(lim, m), full(np.nan, m),
                           full(np.nan, m), "MCUSUM (Y)", "only1", symmetric=False,
                           violations={1: flagged})
        return [panel], {"k": k, "LCS": lim, "ARL": None if h is not None else arl,
                         "variables": p, "puntos": m, "tamaño": n}

    base = build_chart("MCUSUM", m, None, stage_fn, (1,), None)
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=None, mean=mean,
                             cov=S, scale=float(n))
