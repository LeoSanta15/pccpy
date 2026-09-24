"""Cartas de control multivariadas: T² de Hotelling, varianza generalizada, MEWMA y MCUSUM.

Formulas según la documentación de métodos de Minitab y Montgomery (Introduction to
Statistical Quality Control, cap. 11). Los datos pueden ser observaciones
individuales (matriz N x p) o subgrupos (matriz 3-D m x n x p, o matriz N x p con
``subgroup_size``).

Todas las cartas aceptan ``stages`` (etiqueta de etapa por punto graficado): sin
parámetros históricos, la media y la covarianza (o Sigma de referencia) se vuelven a
estimar dentro de cada etapa, igual que en las cartas univariadas; con parámetros
históricos se usan los mismos en todas las etapas, pero MEWMA y MCUSUM reinician su
acumulador al principio de cada una. También aceptan ``boxcox=True`` para transformar
cada variable por separado antes de calcular la carta (no se puede combinar con
parámetros históricos).
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
    """Devuelve (puntos m x p, n, S promedio, media global, nombres, m, grupos)."""
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
    return pts, n, cov, grand, names, pts.shape[0], grp


def _stage_ref(pts: np.ndarray, grp, idx: np.ndarray):
    """Media y covarianza estimadas solo con los puntos de una etapa (``idx``)."""
    sub = pts[idx]
    if grp is None:
        return sub.mean(axis=0), np.cov(sub, rowvar=False)
    g = grp[idx]
    return sub.mean(axis=0), np.mean([np.cov(x, rowvar=False) for x in g], axis=0)


def _check_cov(cov: np.ndarray) -> None:
    if cov.shape[0] != cov.shape[1] or not np.allclose(cov, cov.T):
        raise ValueError("La matriz de covarianzas debe ser cuadrada y simétrica.")
    if np.linalg.cond(cov) > 1e12:
        raise ValueError(
            "La matriz de covarianzas es singular o casi singular: hay variables "
            "(casi) linealmente dependientes o muy pocas observaciones (revise, si usa "
            "'stages', que cada etapa tenga suficientes puntos)."
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


# --------------------------------------------------------------------------- Box-Cox
def _boxcox_transform(arr: np.ndarray):
    """Transforma cada variable (última dimensión) con su propio lambda de Box-Cox
    (máxima verosimilitud, ``scipy.stats.boxcox``), estimado con todas las
    observaciones individuales disponibles (sin promediar por subgrupo)."""
    if np.any(arr <= 0):
        raise ValueError("'boxcox' requiere datos positivos en todas las variables.")
    shape = arr.shape
    flat = arr.reshape(-1, shape[-1])
    out = np.empty_like(flat)
    lambdas = np.empty(shape[-1])
    for j in range(shape[-1]):
        out[:, j], lambdas[j] = stats.boxcox(flat[:, j])
    return out.reshape(shape), lambdas


def _maybe_boxcox(data, mu, cov, boxcox: bool):
    """Sin ``boxcox``, devuelve ``data`` tal cual. Con ``boxcox``, la transforma y
    devuelve también los nombres de columna (si los había) y los lambda estimados."""
    if not boxcox:
        return data, None, None
    if mu is not None or cov is not None:
        raise ValueError("'boxcox' no se puede combinar con parámetros históricos ('mu'/'cov').")
    names = [str(c) for c in data.columns] if isinstance(data, pd.DataFrame) else None
    arr, lambdas = _boxcox_transform(np.asarray(data, dtype=float))
    return arr, names, lambdas


def _lambda_param(names, lambdas) -> dict:
    return {} if lambdas is None else {"lambda_boxcox": {nm: round(float(lam), 4)
                                                          for nm, lam in zip(names, lambdas)}}


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
    stages=None,
    boxcox: bool = False,
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
    stages : array-like, opcional
        Etiqueta de etapa por punto graficado. Sin ``mu``/``cov``, la media y la
        covarianza (y por tanto los límites de Fase I) se vuelven a estimar dentro
        de cada etapa; con parámetros históricos, se usan los mismos en todas las
        etapas.
    boxcox : bool
        Transforma cada variable con su propio Box-Cox antes de calcular la carta
        (no se puede combinar con ``mu``/``cov``).

    El resultado tiene un panel ``"T2"`` con LC = valor esperado de T² y LCS; no hay
    LCI. Use ``chart.contributions(punto)`` para ver qué variables explican una señal
    (usa la media y covarianza de la etapa de ese punto).
    """
    data, names_bc, lambdas = _maybe_boxcox(data, mu, cov, boxcox)
    pts, n, s_est, grand, names, m, grp = _prepare(data, subgroup_size)
    if names_bc is not None:
        names = names_bc
    p = pts.shape[1]
    hist_mean, hist_S, phase0 = _resolve_params(mu, cov, grand, s_est, p, n_hist)
    if phase0 != "phase1":
        _check_cov(hist_S)

    stage_means, stage_covs, stage_scales = [], [], []

    def stage_fn(idx):
        npts = len(idx)
        if phase0 == "phase1":
            mean_i, S_i = _stage_ref(pts, grp, idx)
            _check_cov(S_i)
            phase, m_ref = "phase1", npts
        else:
            mean_i, S_i, phase = hist_mean, hist_S, phase0
            m_ref = n_hist if phase == "phase2" else 0
        center, ucl = _t2_reference(p, m_ref, n, alpha, phase)
        d = pts[idx] - mean_i
        t2 = n * np.einsum("ij,ij->i", d @ np.linalg.inv(S_i), d)
        flagged = np.flatnonzero(t2 > ucl)
        panel = StagePanel(
            "T2", t2, full(center, npts), full(ucl, npts), full(np.nan, npts), full(np.nan, npts),
            "T² de Hotelling", "only1", symmetric=False, violations={1: flagged},
        )
        stage_means.append(mean_i)
        stage_covs.append(S_i)
        stage_scales.append(float(n))
        prm = {"fase": {"phase1": "I", "phase2": "II", "known": "parámetros conocidos"}[phase],
              "variables": p, "puntos": npts, "tamaño": n, "alfa": alpha}
        prm.update(_lambda_param(names, lambdas))
        return [panel], prm

    base = build_chart("T²", m, stages, stage_fn, (1,), None)
    labels = [prm["stage"] for prm in base.params]
    stage_mean = dict(zip(labels, stage_means))
    stage_cov = dict(zip(labels, stage_covs))
    stage_scale = dict(zip(labels, stage_scales))
    first = labels[0]
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=pts,
                             mean=stage_mean[first], cov=stage_cov[first], scale=stage_scale[first],
                             stage_mean=stage_mean, stage_cov=stage_cov, stage_scale=stage_scale)


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
    stages=None,
    boxcox: bool = False,
) -> MultivariateChart:
    """Carta de varianza generalizada |S| (dispersión multivariada).

    Grafica el determinante de la matriz de covarianzas de cada subgrupo, con
    LC = b1|S̄|, límites |S̄|(b1 ± k·√b2) (LCI no menor que 0) y S̄ el promedio de las
    matrices de covarianza de los subgrupos. Con ``cov`` (Sigma conocida) se usa
    |Sigma| en lugar de |S̄|. Requiere subgrupos de tamaño n > p.

    ``stages``: sin ``cov``, S̄ (y por tanto el centro y los límites) se recalcula
    dentro de cada etapa; con ``cov`` se usa la misma Sigma en todas. ``boxcox``:
    transforma cada variable antes de calcular la carta.
    """
    if subgroup_size is None and np.asarray(data).ndim != 3:
        raise ValueError("La varianza generalizada requiere subgrupos: indique 'subgroup_size' o pase datos 3-D.")
    data, names_bc, lambdas = _maybe_boxcox(data, None, cov, boxcox)
    pts, n, s_est, _, names, m, grp = _prepare(data, subgroup_size)
    if names_bc is not None:
        names = names_bc
    p = pts.shape[1]
    if n <= p:
        raise ValueError(f"El tamaño de subgrupo ({n}) debe ser mayor que el número de variables ({p}).")
    dets = np.array([np.linalg.det(np.cov(g, rowvar=False)) for g in grp])
    if cov is not None:
        fixed_sig = np.asarray(cov, dtype=float)
        if fixed_sig.shape != (p, p):
            raise ValueError(f"'cov' debe ser {p} x {p}.")
        _check_cov(fixed_sig)
    b1, b2 = _gv_constants(p, n)

    def stage_fn(idx):
        npts = len(idx)
        if cov is None:
            _, sig = _stage_ref(pts, grp, idx)
            _check_cov(sig)
            known = False
        else:
            sig, known = fixed_sig, True
        det_s = float(np.linalg.det(sig))
        center = b1 * det_s
        ucl = det_s * (b1 + k * np.sqrt(b2))
        lcl = max(0.0, det_s * (b1 - k * np.sqrt(b2)))
        sub_dets = dets[idx]
        flagged = np.flatnonzero((sub_dets > ucl) | (sub_dets < lcl))
        panel = StagePanel("|S|", sub_dets, full(center, npts), full(ucl, npts), full(lcl, npts),
                           full(np.nan, npts), "Varianza generalizada", "only1",
                           symmetric=False, violations={1: flagged})
        prm = {"|S|": det_s, "variables": p, "subgrupos": npts, "tamaño": n, "sigma_conocida": known}
        prm.update(_lambda_param(names, lambdas))
        return [panel], prm

    base = build_chart("Varianza generalizada", m, stages, stage_fn, (1,), None)
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=None, mean=None,
                             cov=(fixed_sig if cov is not None else s_est), scale=float(n))


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
    stages=None,
    boxcox: bool = False,
) -> MultivariateChart:
    """Carta MEWMA (EWMA multivariada, Stat > Control Charts > Multivariate > MEWMA).

    ``Z_i = weight·(x_i - mu) + (1 - weight)·Z_(i-1)`` con ``Z_0 = 0``; se grafica
    ``T²_i = Z_i' Sigma_Z^-1 Z_i`` con la covarianza asintótica de Z,
    ``weight/(2 - weight)·Sigma``. El límite ``H`` se calcula para que el ARL en
    control (desde ``Z_0 = 0``) sea ``arl`` (por defecto 200, como Minitab), o se
    fija con ``ucl``. Sirve para detectar cambios pequeños y
    sostenidos en el vector de medias. ``mu`` y ``cov`` se estiman si no se dan
    (deben darse juntos).

    ``stages``: la recursión reinicia (``Z_0 = 0``) al principio de cada etapa; sin
    ``mu``/``cov`` también se vuelve a estimar la media y Sigma dentro de cada una.
    ``boxcox``: transforma cada variable antes de calcular la carta.
    """
    if not 0 < weight <= 1:
        raise ValueError("'weight' debe estar en (0, 1].")
    data, names_bc, lambdas = _maybe_boxcox(data, mu, cov, boxcox)
    pts, n, s_est, grand, names, m, grp = _prepare(data, subgroup_size)
    if names_bc is not None:
        names = names_bc
    p = pts.shape[1]
    hist_mean, hist_S, _ = _resolve_params(mu, cov, grand, s_est, p, None)
    use_hist = mu is not None
    if use_hist:
        _check_cov(hist_S)
    h = float(ucl) if ucl is not None else mewma_limit(p, float(weight), float(arl))

    def stage_fn(idx):
        npts = len(idx)
        if use_hist:
            mean_i, S_i = hist_mean, hist_S
        else:
            mean_i, S_i = _stage_ref(pts, grp, idx)
            _check_cov(S_i)
        sig_inv = np.linalg.inv(weight / (2.0 - weight) * S_i / n)  # covarianza asintótica de Z
        z = np.zeros(p)
        t2 = np.empty(npts)
        for i, x in enumerate(pts[idx]):
            z = weight * (x - mean_i) + (1.0 - weight) * z
            t2[i] = z @ sig_inv @ z
        flagged = np.flatnonzero(t2 > h)
        panel = StagePanel("MEWMA", t2, full(np.nan, npts), full(h, npts), full(np.nan, npts),
                           full(np.nan, npts), "MEWMA (T²)", "only1", symmetric=False,
                           violations={1: flagged})
        prm = {"peso": weight, "LCS": h, "ARL": None if ucl is not None else arl,
              "variables": p, "puntos": npts, "tamaño": n}
        prm.update(_lambda_param(names, lambdas))
        return [panel], prm

    base = build_chart("MEWMA", m, stages, stage_fn, (1,), None)
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=None,
                             mean=(hist_mean if use_hist else grand),
                             cov=(hist_S if use_hist else s_est), scale=float(n))


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
    stages=None,
    boxcox: bool = False,
) -> MultivariateChart:
    """Carta CUSUM multivariada de Crosier (1988).

    Con ``d_t = x_t - mu`` y ``C_t = sqrt((S_(t-1) + d_t)' Sigma^-1 (S_(t-1) + d_t))``:
    ``S_t = 0`` si ``C_t <= k`` y ``S_t = (S_(t-1) + d_t)(1 - k/C_t)`` en otro caso. Se
    grafica ``Y_t = sqrt(S_t' Sigma^-1 S_t)`` y hay señal si ``Y_t > h``. ``k`` es la
    holgura (0.5 por defecto) y ``h`` se calcula para el ``arl`` en control pedido
    (200 por defecto) o se fija con ``h``. ``mu`` y ``cov`` se estiman si no se dan
    (deben darse juntos). Con subgrupos se usan las medias y Sigma/n.

    ``stages``: el acumulador ``S`` reinicia en 0 al principio de cada etapa; sin
    ``mu``/``cov`` también se vuelve a estimar la media y Sigma dentro de cada una.
    ``boxcox``: transforma cada variable antes de calcular la carta.
    """
    if k < 0:
        raise ValueError("'k' debe ser >= 0.")
    data, names_bc, lambdas = _maybe_boxcox(data, mu, cov, boxcox)
    pts, n, s_est, grand, names, m, grp = _prepare(data, subgroup_size)
    if names_bc is not None:
        names = names_bc
    p = pts.shape[1]
    hist_mean, hist_S, _ = _resolve_params(mu, cov, grand, s_est, p, None)
    use_hist = mu is not None
    if use_hist:
        _check_cov(hist_S)
    if h is not None and h <= 0:
        raise ValueError("'h' debe ser > 0.")
    lim = float(h) if h is not None else mcusum_limit(p, float(k), float(arl))

    def stage_fn(idx):
        npts = len(idx)
        if use_hist:
            mean_i, S_i = hist_mean, hist_S
        else:
            mean_i, S_i = _stage_ref(pts, grp, idx)
            _check_cov(S_i)
        sig_inv = np.linalg.inv(S_i / n)
        s_vec = np.zeros(p)
        y = np.empty(npts)
        for i, x in enumerate(pts[idx]):
            v = s_vec + (x - mean_i)
            c = float(np.sqrt(v @ sig_inv @ v))
            s_vec = v * (1.0 - k / c) if c > k else np.zeros(p)
            y[i] = np.sqrt(s_vec @ sig_inv @ s_vec)
        flagged = np.flatnonzero(y > lim)
        panel = StagePanel("MCUSUM", y, full(0.0, npts), full(lim, npts), full(np.nan, npts),
                           full(np.nan, npts), "MCUSUM (Y)", "only1", symmetric=False,
                           violations={1: flagged})
        prm = {"k": k, "LCS": lim, "ARL": None if h is not None else arl,
              "variables": p, "puntos": npts, "tamaño": n}
        prm.update(_lambda_param(names, lambdas))
        return [panel], prm

    base = build_chart("MCUSUM", m, stages, stage_fn, (1,), None)
    return MultivariateChart(kind=base.kind, panels=base.panels, params=base.params,
                             tests=base.tests, test_params=base.test_params,
                             test1_text=_OUT_OF_LIMIT, variables=names, points=None,
                             mean=(hist_mean if use_hist else grand),
                             cov=(hist_S if use_hist else s_est), scale=float(n))
