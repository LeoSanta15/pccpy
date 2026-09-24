"""Análisis de capacidad del proceso (equivalente a Stat > Quality Tools > Capability Analysis).

Definiciones (como en Minitab):

* **Within (potencial)**: Cp, CPL, CPU, Cpk con sigma *dentro* de los subgrupos
  (rango móvil para individuales; pooled / Rbar / Sbar para subgrupos).
* **Overall (desempeño)**: Pp, PPL, PPU, Ppk con la desviación estándar muestral
  de *todos* los datos (n-1).
* Cpm = (LES - LEI) / (6 * sqrt(s_overall^2 + (media - objetivo)^2)).
* Z.Bench = Phi^-1(1 - P(defecto total)).
* Los intervalos de confianza de Pp y Ppk usan las aproximaciones estándar
  (chi-cuadrado y Bissell), bilaterales.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import boxcox as _boxcox

from ._data import as_1d, to_subgroups
from ._sigma import sigma_individuals, sigma_subgroups

NAN = float("nan")


def _fmt(v, nd: int = 2) -> str:
    return "*" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{nd}f}"


def _check_specs(lsl, usl):
    if lsl is None and usl is None:
        raise ValueError("Indique al menos un límite de especificación (lsl o usl).")
    if lsl is not None and usl is not None and lsl >= usl:
        raise ValueError("El límite inferior (lsl) debe ser menor que el superior (usl).")


def _indices(mean: float, sigma: float, lsl, usl) -> tuple[float, float, float, float]:
    if not sigma > 0:
        raise ValueError("La variación del proceso es cero; no se pueden calcular índices.")
    cpl = (mean - lsl) / (3 * sigma) if lsl is not None else NAN
    cpu = (usl - mean) / (3 * sigma) if usl is not None else NAN
    cp = (usl - lsl) / (6 * sigma) if lsl is not None and usl is not None else NAN
    cpk = float(np.nanmin([cpl, cpu]))
    return cp, cpl, cpu, cpk


def _expected_ppm(mean: float, sigma: float, lsl, usl) -> tuple[float, float, float]:
    lo = 1e6 * stats.norm.cdf((lsl - mean) / sigma) if lsl is not None else NAN
    hi = 1e6 * stats.norm.sf((usl - mean) / sigma) if usl is not None else NAN
    return lo, hi, float(np.nansum([lo, hi]))


def _z_bench(total_ppm: float) -> float:
    p = total_ppm / 1e6
    return float(stats.norm.isf(p)) if p > 0 else math.inf


def _observed_ppm(x: np.ndarray, lsl, usl) -> tuple[float, float, float]:
    lo = 1e6 * float(np.mean(x < lsl)) if lsl is not None else NAN
    hi = 1e6 * float(np.mean(x > usl)) if usl is not None else NAN
    return lo, hi, float(np.nansum([lo, hi]))


@dataclass
class CapabilityResult:
    """Resultado de un análisis de capacidad para datos normales."""

    n: int
    mean: float
    sigma_within: float
    sigma_overall: float
    within_method: str
    lsl: float | None
    usl: float | None
    target: float | None
    cp: float
    cpl: float
    cpu: float
    cpk: float
    pp: float
    ppl: float
    ppu: float
    ppk: float
    cpm: float
    z_bench_within: float
    z_bench_overall: float
    z_lsl_overall: float
    z_usl_overall: float
    ppm_obs: tuple[float, float, float]  # (< LEI, > LES, total)
    ppm_within: tuple[float, float, float]
    ppm_overall: tuple[float, float, float]
    pp_ci: tuple[float, float]
    ppk_ci: tuple[float, float]
    ci_level: float
    transform: dict[str, float] | None = None
    data: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    def to_frame(self) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico)."""
        rows = [
            ("N", self.n), ("Media", self.mean),
            ("Desv.Est. (dentro)", self.sigma_within), ("Desv.Est. (general)", self.sigma_overall),
            ("Cp", self.cp), ("CPL", self.cpl), ("CPU", self.cpu), ("Cpk", self.cpk),
            ("Pp", self.pp), ("PPL", self.ppl), ("PPU", self.ppu), ("Ppk", self.ppk),
            ("Cpm", self.cpm),
            ("Z.Bench (dentro)", self.z_bench_within), ("Z.Bench (general)", self.z_bench_overall),
            ("PPM obs < LEI", self.ppm_obs[0]), ("PPM obs > LES", self.ppm_obs[1]),
            ("PPM obs total", self.ppm_obs[2]),
            ("PPM esp. dentro total", self.ppm_within[2]),
            ("PPM esp. general total", self.ppm_overall[2]),
        ]
        return pd.DataFrame(rows, columns=["estadístico", "valor"]).set_index("estadístico")

    def summary(self) -> str:
        o = self
        ci = round(o.ci_level * 100)
        L = [
            "Análisis de capacidad del proceso (distribución normal)",
            f"  LEI={_fmt(o.lsl, 4)}  Objetivo={_fmt(o.target, 4)}  LES={_fmt(o.usl, 4)}",
            (f"  N={o.n}  Media={o.mean:.5f}  "
            f"Desv.Est.(dentro)={o.sigma_within:.5f} [{o.within_method}]  "
            f"Desv.Est.(general)={o.sigma_overall:.5f}"),
        ]
        if o.transform:
            L.append(
                f"  Transformación Box-Cox con lambda = {o.transform['lambda']:.4f} "
                "(Media, Desv.Est. y Z.* están en la escala transformada; "
                "LEI/LES/objetivo y PPM observado, en unidades originales)"
            )
        L += [
            "  Capacidad potencial (dentro):",
            f"    Cp={_fmt(o.cp)}  CPL={_fmt(o.cpl)}  CPU={_fmt(o.cpu)}  Cpk={_fmt(o.cpk)}",
            f"    Z.Bench={_fmt(o.z_bench_within)}",
            "  Desempeño general:",
            f"    Pp={_fmt(o.pp)}  PPL={_fmt(o.ppl)}  PPU={_fmt(o.ppu)}  Ppk={_fmt(o.ppk)}  Cpm={_fmt(o.cpm)}",
            (f"    IC {ci}% Pp: ({_fmt(o.pp_ci[0])}, {_fmt(o.pp_ci[1])})   "
            f"IC {ci}% Ppk: ({_fmt(o.ppk_ci[0])}, {_fmt(o.ppk_ci[1])})"),
            f"    Z.Bench={_fmt(o.z_bench_overall)}  Z.LEI={_fmt(o.z_lsl_overall)}  Z.LES={_fmt(o.z_usl_overall)}",
            "  Desempeño (PPM):            < LEI       > LES      Total",
        ]
        for label, t in (("Observado", o.ppm_obs), ("Esperado dentro", o.ppm_within),
                         ("Esperado general", o.ppm_overall)):
            L.append(f"    {label:<18}{_fmt(t[0]):>10}{_fmt(t[1]):>12}{_fmt(t[2]):>11}")
        return "\n".join(L)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()

    def plot(self, **kwargs):
        """Histograma de capacidad. Ver :func:`spyc.plotting.plot_capability`."""
        from .plotting import plot_capability

        return plot_capability(self, **kwargs)


def capability_analysis(
    data,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
    *,
    subgroup_size: int | None = None,
    subgroup=None,
    within_method: str | None = None,
    sigma_within: float | None = None,
    ci_level: float = 0.95,
) -> CapabilityResult:
    """Capacidad del proceso para datos con distribución normal.

    Parameters
    ----------
    data : array-like
        Vector 1-D de individuales, o matriz 2-D (fila = subgrupo), o vector 1-D
        con ``subgroup_size`` / ``subgroup``.
    lsl, usl, target : float, opcional
        Límites de especificación inferior y superior, y valor objetivo.
    within_method : str, opcional
        Individuales: ``'mr'`` (por defecto), ``'median_mr'`` o ``'mssd'``.
        Subgrupos: ``'pooled'`` (por defecto), ``'rbar'`` o ``'sbar'``.
    sigma_within : float, opcional
        Sigma dentro de subgrupos ya conocida (anula la estimación).
    ci_level : float
        Nivel de confianza de los intervalos de Pp y Ppk (por defecto 0.95).
    """
    _check_specs(lsl, usl)
    if not 0 < ci_level < 1:
        raise ValueError("'ci_level' debe estar entre 0 y 1.")

    arr = np.asarray(data, dtype=float)
    grouped = arr.ndim == 2 or subgroup is not None or (subgroup_size is not None and subgroup_size > 1)
    if grouped:
        g = to_subgroups(arr, subgroup_size, subgroup)
        x = g[~np.isnan(g)]
        method = within_method or "pooled"
        if method not in ("pooled", "rbar", "sbar"):
            raise ValueError("Con subgrupos, within_method debe ser 'pooled', 'rbar' o 'sbar'.")
        sw = float(sigma_within) if sigma_within is not None else sigma_subgroups(g, method)
    else:
        x = as_1d(arr)
        method = within_method or "mr"
        if method not in ("mr", "median_mr", "mssd"):
            raise ValueError("Con individuales, within_method debe ser 'mr', 'median_mr' o 'mssd'.")
        sw = float(sigma_within) if sigma_within is not None else sigma_individuals(x, method)
    if sigma_within is not None:
        method = "especificada"
    if x.size < 2:
        raise ValueError("Se necesitan al menos 2 observaciones.")

    n, mean = x.size, float(x.mean())
    so = float(x.std(ddof=1))
    cp, cpl, cpu, cpk = _indices(mean, sw, lsl, usl)
    pp, ppl, ppu, ppk = _indices(mean, so, lsl, usl)

    cpm = NAN
    if target is not None and lsl is not None and usl is not None:
        cpm = (usl - lsl) / (6 * math.sqrt(so**2 + (mean - target) ** 2))

    alpha = 1 - ci_level
    pp_ci = (NAN, NAN)
    if not math.isnan(pp):
        pp_ci = (
            pp * math.sqrt(stats.chi2.ppf(alpha / 2, n - 1) / (n - 1)),
            pp * math.sqrt(stats.chi2.ppf(1 - alpha / 2, n - 1) / (n - 1)),
        )
    zc = stats.norm.ppf(1 - alpha / 2)
    half = zc * math.sqrt(1.0 / (9 * n) + ppk**2 / (2 * (n - 1)))
    ppk_ci = (ppk - half, ppk + half)

    ppm_w = _expected_ppm(mean, sw, lsl, usl)
    ppm_o = _expected_ppm(mean, so, lsl, usl)
    return CapabilityResult(
        n=n, mean=mean, sigma_within=sw, sigma_overall=so, within_method=method,
        lsl=lsl, usl=usl, target=target,
        cp=cp, cpl=cpl, cpu=cpu, cpk=cpk, pp=pp, ppl=ppl, ppu=ppu, ppk=ppk, cpm=cpm,
        z_bench_within=_z_bench(ppm_w[2]), z_bench_overall=_z_bench(ppm_o[2]),
        z_lsl_overall=(mean - lsl) / so if lsl is not None else NAN,
        z_usl_overall=(usl - mean) / so if usl is not None else NAN,
        ppm_obs=_observed_ppm(x, lsl, usl), ppm_within=ppm_w, ppm_overall=ppm_o,
        pp_ci=pp_ci, ppk_ci=ppk_ci, ci_level=ci_level, data=x,
    )


def capability_boxcox(
    data,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
    *,
    lam: float | None = None,
    round_lambda: bool = False,
    **kwargs,
) -> CapabilityResult:
    """Capacidad tras una transformación Box-Cox (datos positivos, 1-D).

    ``lam`` fija lambda; si no se da, se estima por máxima verosimilitud. Con
    ``round_lambda=True`` se redondea al múltiplo de 0.5 más cercano. Los límites de
    especificación y el objetivo se transforman con el mismo lambda. Acepta los
    mismos argumentos opcionales que :func:`capability_analysis` (subgrupos, etc.).
    """
    x = as_1d(data, "data")
    if x.min() <= 0:
        raise ValueError("Box-Cox requiere datos estrictamente positivos.")
    for name, v in (("lsl", lsl), ("usl", usl), ("target", target)):
        if v is not None and v <= 0:
            raise ValueError(f"Box-Cox requiere que {name} sea positivo.")
    if lam is None:
        _, lam = stats.boxcox(x)
        if round_lambda:
            lam = round(lam * 2) / 2
    y = _boxcox(x, lam)
    t = lambda v: None if v is None else float(_boxcox(v, lam))
    res = capability_analysis(y, t(lsl), t(usl), t(target), **kwargs)
    res.transform = {"lambda": float(lam)}
    res.lsl, res.usl, res.target = lsl, usl, target  # se reportan en unidades originales
    res.data = x
    res.ppm_obs = _observed_ppm(x, lsl, usl)
    return res


# --------------------------------------------------------------------------- no normal
_DISTS = {
    "normal": (stats.norm, {}, False),
    "lognormal": (stats.lognorm, {"floc": 0}, True),
    "weibull": (stats.weibull_min, {"floc": 0}, True),
    "gamma": (stats.gamma, {"floc": 0}, True),
    "exponential": (stats.expon, {"floc": 0}, True),
    "loglogistic": (stats.fisk, {"floc": 0}, True),
    "logistic": (stats.logistic, {}, False),
    "largest_extreme": (stats.gumbel_r, {}, False),
    "smallest_extreme": (stats.gumbel_l, {}, False),
}


@dataclass
class NonNormalCapabilityResult:
    """Capacidad por el método de percentiles (Minitab, distribuciones no normales)."""

    distribution: str
    params: tuple[float, ...]
    loglik: float
    aic: float
    n: int
    lsl: float | None
    usl: float | None
    target: float | None
    x_low: float  # percentil 0.135 %
    x_median: float
    x_high: float  # percentil 99.865 %
    pp: float
    ppl: float
    ppu: float
    ppk: float
    ppm_obs: tuple[float, float, float]
    ppm_expected: tuple[float, float, float]
    data: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def frozen(self):
        return _DISTS[self.distribution][0](*self.params)

    def summary(self) -> str:
        o = self
        return "\n".join([
            f"Análisis de capacidad (no normal) - distribución {o.distribution}",
            f"  LEI={_fmt(o.lsl, 4)}  LES={_fmt(o.usl, 4)}  N={o.n}  logL={o.loglik:.3f}  AIC={o.aic:.3f}",
            f"  Percentiles: 0.135% = {o.x_low:.5f}   50% = {o.x_median:.5f}   99.865% = {o.x_high:.5f}",
            f"  Pp={_fmt(o.pp)}  PPL={_fmt(o.ppl)}  PPU={_fmt(o.ppu)}  Ppk={_fmt(o.ppk)}",
            "  Desempeño (PPM):            < LEI       > LES      Total",
            f"    {'Observado':<18}{_fmt(o.ppm_obs[0]):>10}{_fmt(o.ppm_obs[1]):>12}{_fmt(o.ppm_obs[2]):>11}",
            f"    {'Esperado':<18}{_fmt(o.ppm_expected[0]):>10}{_fmt(o.ppm_expected[1]):>12}{_fmt(o.ppm_expected[2]):>11}",
        ])

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_capability

        return plot_capability(self, **kwargs)


def capability_nonnormal(
    data,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
    *,
    distribution: str = "weibull",
) -> NonNormalCapabilityResult:
    """Capacidad para datos no normales por percentiles de la distribución ajustada.

    Ajusta por máxima verosimilitud una de: ``normal``, ``lognormal``, ``weibull``,
    ``gamma``, ``exponential``, ``loglogistic``, ``logistic``, ``largest_extreme``,
    ``smallest_extreme`` (las distribuciones de soporte positivo usan umbral 0).

    Pp = (LES - LEI) / (X99.865 - X0.135); PPU = (LES - X50) / (X99.865 - X50);
    PPL = (X50 - LEI) / (X50 - X0.135); Ppk = min(PPL, PPU).
    """
    _check_specs(lsl, usl)
    key = distribution.lower()
    if key not in _DISTS:
        raise ValueError(f"Distribución no soportada: {distribution!r}. Opciones: {sorted(_DISTS)}")
    dist, fit_kw, positive = _DISTS[key]
    x = as_1d(data, "data")
    if x.size < 3:
        raise ValueError("Se necesitan al menos 3 observaciones.")
    if positive and x.min() <= 0:
        raise ValueError(f"La distribución {key} requiere datos estrictamente positivos.")

    params = dist.fit(x, **fit_kw)
    frozen = dist(*params)
    loglik = float(np.sum(frozen.logpdf(x)))
    n_free = len(params) - len(fit_kw)
    aic = 2 * n_free - 2 * loglik

    p_lo, p_hi = stats.norm.cdf(-3), stats.norm.cdf(3)
    x_lo, x_med, x_hi = (float(frozen.ppf(q)) for q in (p_lo, 0.5, p_hi))
    pp = (usl - lsl) / (x_hi - x_lo) if lsl is not None and usl is not None else NAN
    ppu = (usl - x_med) / (x_hi - x_med) if usl is not None else NAN
    ppl = (x_med - lsl) / (x_med - x_lo) if lsl is not None else NAN
    ppk = float(np.nanmin([ppl, ppu]))

    e_lo = 1e6 * float(frozen.cdf(lsl)) if lsl is not None else NAN
    e_hi = 1e6 * float(frozen.sf(usl)) if usl is not None else NAN
    return NonNormalCapabilityResult(
        distribution=key, params=tuple(float(p) for p in params), loglik=loglik, aic=aic,
        n=x.size, lsl=lsl, usl=usl, target=target,
        x_low=x_lo, x_median=x_med, x_high=x_hi, pp=pp, ppl=ppl, ppu=ppu, ppk=ppk,
        ppm_obs=_observed_ppm(x, lsl, usl),
        ppm_expected=(e_lo, e_hi, float(np.nansum([e_lo, e_hi]))), data=x,
    )
