"""Análisis de capacidad del proceso (equivalente a Stat > Quality Tools > Capability Analysis).

Definiciones (como en Minitab):

* **Within (potencial)**: Cp, CPL, CPU, Cpk con sigma *dentro* de los subgrupos
  (rango móvil para individuales; pooled / Rbar / Sbar para subgrupos).
* **Overall (desempeño)**: Pp, PPL, PPU, Ppk con la desviación estándar muestral
  de *todos* los datos (n-1).
* Cpm = min(T - LEI, LES - T) / (3 * s_T), con s_T^2 = sum((x_i - T)^2) / (n - 1) = s^2 + n/(n-1) * (media - T)^2.
  Con T en el punto medio de la especificación es (LES - LEI) / (6 * s_T).
* Z.Bench = Phi^-1(1 - P(defecto total)).
* Los intervalos de confianza de Pp y Ppk usan las aproximaciones estándar
  (chi-cuadrado y Bissell), bilaterales.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import boxcox as _boxcox

from ._data import _excel_writer, as_1d, avisar_asimetria_subgrupos, to_subgroups
from ._frames import tabla_estadisticos
from ._i18n import N_, tr
from ._sigma import sigma_individuals, sigma_subgroups
from .bootstrap import bootstrap_ci
from .transforms import Transformation, fit_transformation

NAN = float("nan")


def _fmt(v, nd: int = 2) -> str:
    return "*" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{nd}f}"


def _check_specs(lsl, usl):
    if lsl is not None and usl is not None and lsl >= usl:
        raise ValueError(tr("El límite inferior (lsl) debe ser menor que el superior (usl)."))


def _ci_ppk(ppk: float, n: int, alpha: float) -> tuple[float, float]:
    """IC aproximado de Ppk (Bissell): ``Ppk ± z·sqrt(1/(9n) + Ppk²/(2(n − 1)))``; con Ppk infinito es (inf, inf)."""
    if math.isinf(ppk):
        return (ppk, ppk)
    zc = stats.norm.ppf(1 - alpha / 2)
    half = zc * math.sqrt(1.0 / (9 * n) + ppk**2 / (2 * (n - 1)))
    return (ppk - half, ppk + half)


def _cpm(lsl: float, usl: float, target: float, s_target: float) -> float:
    """Cpm = min(T − LEI, LES − T) / (3·s_T); con T en el punto medio es (LES − LEI) / (6·s_T).

    ``s_target`` es la desviación respecto al objetivo, ``s_T² = Σ(xᵢ − T)²/(n − 1)``.
    """
    if s_target <= 0:
        return NAN
    if math.isclose(target, (lsl + usl) / 2):
        return (usl - lsl) / (6 * s_target)
    return min(target - lsl, usl - target) / (3 * s_target)


def _indices(mean: float, sigma: float, lsl, usl) -> tuple[float, float, float, float]:
    if lsl is None and usl is None:
        return NAN, NAN, NAN, NAN
    if not sigma > 0:
        import warnings
        warnings.warn(
            tr("La variación del proceso es cero (desviación estándar = 0). "
            "Los índices de capacidad no están definidos y se devuelven como NaN."),
            UserWarning,
            stacklevel=4,
        )
        return NAN, NAN, NAN, NAN
    cpl = (mean - lsl) / (3 * sigma) if lsl is not None else NAN
    cpu = (usl - mean) / (3 * sigma) if usl is not None else NAN
    cp = (usl - lsl) / (6 * sigma) if lsl is not None and usl is not None else NAN
    cpk = float(np.nanmin([cpl, cpu]))
    return cp, cpl, cpu, cpk


def _expected_ppm(mean: float, sigma: float, lsl, usl) -> tuple[float, float, float]:
    if not sigma > 0:
        return NAN, NAN, NAN
    lo = 1e6 * stats.norm.cdf((lsl - mean) / sigma) if lsl is not None else NAN
    hi = 1e6 * stats.norm.sf((usl - mean) / sigma) if usl is not None else NAN
    return lo, hi, float(np.nansum([lo, hi]))


def _z_bench(total_ppm: float) -> float:
    if math.isnan(total_ppm):
        return NAN
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
    ci_method: str = "normal"
    data: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def dpmo(self) -> float:
        """Defectos por millón de oportunidades (PPM esperado general)."""
        return self.ppm_overall[2]

    @property
    def sigma_level(self) -> float:
        """Nivel sigma del proceso: Z.bench general = Φ⁻¹(1 − P(defecto total))."""
        return self.z_bench_overall

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico).

        Con ``stable=True`` las filas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        rows = [
            ("n", N_("N"), self.n), ("mean", N_("Media"), self.mean),
            ("sigma_within", N_("Desv.Est. (dentro)"), self.sigma_within),
            ("sigma_overall", N_("Desv.Est. (general)"), self.sigma_overall),
            ("cp", N_("Cp"), self.cp), ("cpl", N_("CPL"), self.cpl), ("cpu", N_("CPU"), self.cpu),
            ("cpk", N_("Cpk"), self.cpk),
            ("pp", N_("Pp"), self.pp), ("ppl", N_("PPL"), self.ppl), ("ppu", N_("PPU"), self.ppu),
            ("ppk", N_("Ppk"), self.ppk),
            ("cpm", N_("Cpm"), self.cpm),
            ("z_bench_within", N_("Z.Bench (dentro)"), self.z_bench_within),
            ("z_bench_overall", N_("Z.Bench (general)"), self.z_bench_overall),
            ("sigma_level", N_("Nivel Sigma"), self.sigma_level), ("dpmo", N_("DPMO"), self.dpmo),
            ("ppm_obs_below_lsl", N_("PPM obs < LEI"), self.ppm_obs[0]),
            ("ppm_obs_above_usl", N_("PPM obs > LES"), self.ppm_obs[1]),
            ("ppm_obs_total", N_("PPM obs total"), self.ppm_obs[2]),
            ("ppm_within_total", N_("PPM esp. dentro total"), self.ppm_within[2]),
            ("ppm_overall_total", N_("PPM esp. general total"), self.ppm_overall[2]),
        ]
        return tabla_estadisticos(rows, stable)

    def summary(self) -> str:
        o = self
        ci = round(o.ci_level * 100)
        L = [
            tr("Análisis de capacidad del proceso (distribución normal)"),
            tr("  LEI={lsl}  Objetivo={target}  LES={usl}").format(
                lsl=_fmt(o.lsl, 4), target=_fmt(o.target, 4), usl=_fmt(o.usl, 4)),
            tr("  N={n}  Media={mean:.5f}  Desv.Est.(dentro)={within:.5f} [{method}]  Desv.Est.(general)={overall:.5f}").format(
                n=o.n, mean=o.mean, within=o.sigma_within, method=o.within_method, overall=o.sigma_overall),
        ]
        if o.transform and o.transform.get("method", "boxcox") != "boxcox":
            L.append(
                tr("  Transformación {detalle} (Media, Desv.Est. y Z.* están en la escala transformada; "
                   "LEI/LES/objetivo y PPM observado, en unidades originales)").format(
                    detalle=Transformation.from_info(o.transform).describe())
            )
        elif o.transform:
            L.append(
                tr("  Transformación Box-Cox con lambda = {lam:.4f} (Media, Desv.Est. y Z.* están en la escala transformada; "
                   "LEI/LES/objetivo y PPM observado, en unidades originales)").format(lam=o.transform["lambda"])
            )
        L += [
            tr("  Capacidad potencial (dentro):"),
            tr("    Cp={cp}  CPL={cpl}  CPU={cpu}  Cpk={cpk}").format(
                cp=_fmt(o.cp), cpl=_fmt(o.cpl), cpu=_fmt(o.cpu), cpk=_fmt(o.cpk)),
            tr("    Z.Bench={z}").format(z=_fmt(o.z_bench_within)),
            tr("  Desempeño general:"),
            tr("    Pp={pp}  PPL={ppl}  PPU={ppu}  Ppk={ppk}  Cpm={cpm}").format(
                pp=_fmt(o.pp), ppl=_fmt(o.ppl), ppu=_fmt(o.ppu), ppk=_fmt(o.ppk), cpm=_fmt(o.cpm)),
            tr("    IC {ci}% Pp: ({pp_lo}, {pp_hi})   IC {ci}% Ppk: ({ppk_lo}, {ppk_hi})").format(
                ci=ci, pp_lo=_fmt(o.pp_ci[0]), pp_hi=_fmt(o.pp_ci[1]), ppk_lo=_fmt(o.ppk_ci[0]), ppk_hi=_fmt(o.ppk_ci[1])),
            *([tr("    (intervalos por bootstrap {metodo}, {n_boot} remuestreos)").format(
                metodo=o.ci_method.split(":")[1], n_boot=o.ci_method.split(":")[2])] if o.ci_method.startswith("bootstrap:") else []),
            tr("    Z.Bench={z_bench}  Z.LEI={z_lsl}  Z.LES={z_usl}  Nivel Sigma={sigma_level}  DPMO={dpmo:,.0f}").format(
                z_bench=_fmt(o.z_bench_overall), z_lsl=_fmt(o.z_lsl_overall), z_usl=_fmt(o.z_usl_overall),
                sigma_level=_fmt(o.sigma_level), dpmo=o.dpmo),
            tr("  Desempeño (PPM):            < LEI       > LES      Total"),
        ]
        for label, t in ((tr("Observado"), o.ppm_obs), (tr("Esperado dentro"), o.ppm_within),
                         (tr("Esperado general"), o.ppm_overall)):
            L.append(f"    {label:<18}{_fmt(t[0]):>10}{_fmt(t[1]):>12}{_fmt(t[2]):>11}")
        return "\n".join(L)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()

    def to_excel(self, path) -> None:
        """Exporta el análisis de capacidad a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Capacidad"))

    def plot(self, **kwargs):
        """Histograma de capacidad. Ver :func:`pccpy.plotting.plot_capability`."""
        from .plotting import plot_capability

        return plot_capability(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def _ci_bootstrap_pp_ppk(x, lsl, usl, ci_level, n_boot, bootstrap_method, seed) -> tuple:
    """Intervalos bootstrap de Pp y Ppk (sigma general) remuestreando las observaciones; ``nan`` si no aplican."""
    con_pp = lsl is not None and usl is not None

    def indices(m, axis=-1):
        mu = m.mean(axis=axis)
        sd = m.std(axis=axis, ddof=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            cols = []
            if con_pp:
                cols.append((usl - lsl) / (6 * sd))
            ppl = (mu - lsl) / (3 * sd) if lsl is not None else np.full_like(mu, np.inf)
            ppu = (usl - mu) / (3 * sd) if usl is not None else np.full_like(mu, np.inf)
            cols.append(np.minimum(ppl, ppu))
        return np.stack(cols, axis=-1)

    r = bootstrap_ci(x, indices, method=bootstrap_method, n_boot=n_boot, confidence=ci_level, seed=seed,
                     vectorized=True)
    lo, hi = r.ci
    if con_pp:
        return (float(lo[0]), float(hi[0])), (float(lo[1]), float(hi[1]))
    return (NAN, NAN), (float(lo[0]), float(hi[0]))


def capability_analysis(
    data,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
    *,
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
    within_method: str | None = None,
    sigma_within: float | None = None,
    ci_level: float = 0.95,
    ci_method: str = "normal",
    n_boot: int = 2000,
    bootstrap_method: str = "bca",
    seed: int | None = None,
    transform: str | None = None,
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
    ci_method : str
        ``'normal'`` (por defecto: chi-cuadrado para Pp y Bissell para Ppk, que suponen normalidad) o
        ``'bootstrap'``: intervalos de Pp y Ppk por remuestreo de las observaciones, sin suponer normalidad
        (recomendado con datos asimétricos; ver :func:`pccpy.bootstrap_ci`).
    n_boot, bootstrap_method, seed :
        Con ``ci_method='bootstrap'``: número de remuestreos (2000), ``'bca'`` o ``'percentile'`` y semilla.
    transform : {None, 'boxcox', 'yeo-johnson', 'johnson'}
        Transforma los datos (y los límites de especificación y el objetivo) antes de calcular: Box-Cox (solo datos y
        límites positivos), Yeo-Johnson (admite ceros y negativos) o Johnson (SU, SB o SL, la que deje los datos más
        normales). Los índices se calculan en la escala transformada; los límites, el objetivo y el PPM observado se
        informan en unidades originales. ``sigma_within`` no se puede combinar con ``transform`` (está en la escala
        original). Ver :mod:`pccpy.transforms`.
    """
    _check_specs(lsl, usl)
    if not 0 < ci_level < 1:
        raise ValueError(tr("'ci_level' debe estar entre 0 y 1."))
    if ci_method not in ("normal", "bootstrap"):
        raise ValueError(tr("'ci_method' debe ser 'normal' o 'bootstrap'."))

    arr = np.asarray(data, dtype=float)
    grouped = arr.ndim == 2 or subgroup is not None or (subgroup_size is not None and subgroup_size > 1)
    if grouped:
        g, n_complete = to_subgroups(arr, subgroup_size, subgroup, value=value)
        x = g[~np.isnan(g)]
        method = within_method or "pooled"
        if method not in ("pooled", "rbar", "sbar"):
            raise ValueError(tr("Con subgrupos, within_method debe ser 'pooled', 'rbar' o 'sbar'."))
        g_lim = g[:n_complete]
        avisar_asimetria_subgrupos(g_lim, destino="capacidad", stacklevel=3)
        sw = float(sigma_within) if sigma_within is not None else sigma_subgroups(g_lim, method)
    else:
        x = as_1d(arr)
        method = within_method or "mr"
        if method not in ("mr", "median_mr", "mssd"):
            raise ValueError(tr("Con individuales, within_method debe ser 'mr', 'median_mr' o 'mssd'."))
        sw = float(sigma_within) if sigma_within is not None else sigma_individuals(x, method)
    if sigma_within is not None:
        method = "especificada"
    if x.size < 2:
        raise ValueError(tr("Se necesitan al menos 2 observaciones."))

    transformacion = None
    if transform is not None:
        if sigma_within is not None:
            raise ValueError(tr("'sigma_within' no se puede combinar con 'transform' (está en la escala original)."))
        transformacion = fit_transformation(x, transform)
        lsl_o, usl_o, target_o, x_o = lsl, usl, target, x
        if transform == "boxcox":
            for nombre, v in (("lsl", lsl), ("usl", usl), ("target", target)):
                if v is not None and v <= 0:
                    raise ValueError(tr("Box-Cox requiere que {name} sea positivo.").format(name=nombre))
        x = transformacion.forward(x)
        lsl, usl, target = (None if v is None else transformacion.forward(v) for v in (lsl, usl, target))
        if grouped:
            g_lim = transformacion.forward(g_lim)
            sw = sigma_subgroups(g_lim, method)
        else:
            sw = sigma_individuals(x, method)

    n, mean = x.size, float(x.mean())
    so = float(x.std(ddof=1))
    cp, cpl, cpu, cpk = _indices(mean, sw, lsl, usl)
    pp, ppl, ppu, ppk = _indices(mean, so, lsl, usl)

    cpm = NAN
    if target is not None and lsl is not None and usl is not None:
        cpm = _cpm(lsl, usl, target, math.sqrt(float(np.sum((x - target) ** 2)) / (n - 1)))

    alpha = 1 - ci_level
    pp_ci = (NAN, NAN)
    ppk_ci = (NAN, NAN)
    if ci_method == "bootstrap":
        pp_ci, ppk_ci = _ci_bootstrap_pp_ppk(x, lsl, usl, ci_level, n_boot, bootstrap_method, seed)
    else:
        if not math.isnan(pp):
            pp_ci = (
                pp * math.sqrt(stats.chi2.ppf(alpha / 2, n - 1) / (n - 1)),
                pp * math.sqrt(stats.chi2.ppf(1 - alpha / 2, n - 1) / (n - 1)),
            )
        if not math.isnan(ppk):
            ppk_ci = _ci_ppk(ppk, n, alpha)

    ppm_w = _expected_ppm(mean, sw, lsl, usl)
    ppm_o = _expected_ppm(mean, so, lsl, usl)
    so_safe = so if so > 0 else NAN
    res = CapabilityResult(
        n=n, mean=mean, sigma_within=sw, sigma_overall=so, within_method=method,
        lsl=lsl, usl=usl, target=target,
        cp=cp, cpl=cpl, cpu=cpu, cpk=cpk, pp=pp, ppl=ppl, ppu=ppu, ppk=ppk, cpm=cpm,
        z_bench_within=_z_bench(ppm_w[2]), z_bench_overall=_z_bench(ppm_o[2]),
        z_lsl_overall=(mean - lsl) / so_safe if lsl is not None else NAN,
        z_usl_overall=(usl - mean) / so_safe if usl is not None else NAN,
        ppm_obs=_observed_ppm(x, lsl, usl), ppm_within=ppm_w, ppm_overall=ppm_o,
        pp_ci=pp_ci, ppk_ci=ppk_ci, ci_level=ci_level, data=x,
        ci_method=f"bootstrap:{bootstrap_method}:{n_boot}" if ci_method == "bootstrap" else "normal",
    )
    if transformacion is not None:  # se informa en unidades originales (como capability_boxcox)
        res.lsl, res.usl, res.target = lsl_o, usl_o, target_o
        res.data = x_o
        res.ppm_obs = _observed_ppm(x_o, lsl_o, usl_o)
        res.transform = transformacion.info()
    return res


def capability_analysis_summary(
    mean: float,
    std_overall: float,
    n: int,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
    *,
    std_within: float | None = None,
    ci_level: float = 0.95,
) -> CapabilityResult:
    """Capacidad del proceso a partir de estadísticos resumen (sin datos crudos).

    Útil cuando solo se dispone de la media, desviación estándar y tamaño de
    muestra (por ejemplo, desde un informe o un sistema externo).

    Parameters
    ----------
    mean : float
        Media del proceso.
    std_overall : float
        Desviación estándar global (muestral, ddof=1). Se usa para Pp/Ppk.
    n : int
        Número de observaciones (necesario para los intervalos de confianza).
    lsl, usl, target : float, opcional
        Límites de especificación inferior/superior y valor objetivo.
    std_within : float, opcional
        Sigma dentro de subgrupos. Si no se proporciona se asume igual a
        ``std_overall`` (lo que equivale a tratar los datos como individuales
        sin estructura de subgrupo).
    ci_level : float
        Nivel de confianza de los IC de Pp y Ppk. Por defecto 0.95.

    Returns
    -------
    CapabilityResult

    Examples
    --------
    >>> import pccpy as pp
    >>> res = pp.capability_analysis_summary(mean=10.0, std_overall=0.5, n=100,
    ...                                      lsl=8.5, usl=11.5)
    >>> print(res.summary())
    """
    _check_specs(lsl, usl)
    if std_overall <= 0:
        raise ValueError(tr("'std_overall' debe ser positivo."))
    if n < 2:
        raise ValueError(tr("'n' debe ser ≥ 2."))
    if not 0 < ci_level < 1:
        raise ValueError(tr("'ci_level' debe estar entre 0 y 1."))

    sw = float(std_within) if std_within is not None else float(std_overall)
    so = float(std_overall)
    mean = float(mean)

    cp, cpl, cpu, cpk = _indices(mean, sw, lsl, usl)
    pp, ppl, ppu, ppk = _indices(mean, so, lsl, usl)

    cpm = NAN
    if target is not None and lsl is not None and usl is not None:
        cpm = _cpm(lsl, usl, target, math.sqrt(so**2 + n / (n - 1) * (mean - target) ** 2))

    alpha = 1 - ci_level
    pp_ci = (NAN, NAN)
    ppk_ci = (NAN, NAN)
    if not math.isnan(pp):
        pp_ci = (
            pp * math.sqrt(stats.chi2.ppf(alpha / 2, n - 1) / (n - 1)),
            pp * math.sqrt(stats.chi2.ppf(1 - alpha / 2, n - 1) / (n - 1)),
        )
    if not math.isnan(ppk):
        ppk_ci = _ci_ppk(ppk, n, alpha)

    ppm_w = _expected_ppm(mean, sw, lsl, usl)
    ppm_o = _expected_ppm(mean, so, lsl, usl)
    so_safe = so if so > 0 else NAN

    return CapabilityResult(
        n=n, mean=mean, sigma_within=sw, sigma_overall=so,
        within_method="especificada" if std_within is not None else "overall",
        lsl=lsl, usl=usl, target=target,
        cp=cp, cpl=cpl, cpu=cpu, cpk=cpk, pp=pp, ppl=ppl, ppu=ppu, ppk=ppk, cpm=cpm,
        z_bench_within=_z_bench(ppm_w[2]), z_bench_overall=_z_bench(ppm_o[2]),
        z_lsl_overall=(mean - lsl) / so_safe if lsl is not None else NAN,
        z_usl_overall=(usl - mean) / so_safe if usl is not None else NAN,
        ppm_obs=(NAN, NAN, NAN),  # sin datos crudos no se puede calcular
        ppm_within=ppm_w, ppm_overall=ppm_o,
        pp_ci=pp_ci, ppk_ci=ppk_ci, ci_level=ci_level, data=np.array([]),
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
    """Capacidad tras una transformación Box-Cox (datos estrictamente positivos).

    ``data`` puede ser un vector 1-D (con ``subgroup_size=`` para subgrupos de tamaño fijo, en ``kwargs``) o una matriz
    2-D / DataFrame ancho con un subgrupo por fila. Para un DataFrame en formato largo (``subgroup=`` + ``value=``) usa
    ``capability_analysis(..., transform='boxcox')``, que admite todos los formatos de entrada.

    ``lam`` fija lambda; si no se da, se estima por **máxima verosimilitud** con ``scipy.stats.boxcox`` sobre todas las
    observaciones. Ese lambda puede diferir ligeramente del que calcula Minitab (otro optimizador y otro criterio de
    redondeo), así que usa ``lam=`` o ``round_lambda=True`` si necesitas el mismo valor. Con ``round_lambda=True`` se
    redondea al múltiplo de 0.5 más cercano. Los límites de especificación y el objetivo se transforman con el mismo
    lambda. Acepta los mismos argumentos opcionales que :func:`capability_analysis`.
    """
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 2:
        x = arr[np.isfinite(arr)]
        if x.size == 0:
            raise ValueError(tr("'data' no tiene valores válidos tras eliminar NaN/inf."))
    else:
        arr = x = as_1d(data, "data")
    if x.min() <= 0:
        raise ValueError(tr("Box-Cox requiere datos estrictamente positivos."))
    for name, v in (("lsl", lsl), ("usl", usl), ("target", target)):
        if v is not None and v <= 0:
            raise ValueError(tr("Box-Cox requiere que {name} sea positivo.").format(name=name))
    if lam is None:
        _, lam = stats.boxcox(x)
        if round_lambda:
            lam = round(lam * 2) / 2
    y = _boxcox(np.where(np.isfinite(arr), arr, 1.0), lam) if arr.ndim == 2 else _boxcox(x, lam)
    if arr.ndim == 2:
        y = np.where(np.isfinite(arr), y, np.nan)
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
    pp_ci: tuple[float, float] = (NAN, NAN)
    ppk_ci: tuple[float, float] = (NAN, NAN)
    ci_level: float = 0.95
    ci_method: str = "none"

    @property
    def frozen(self):
        return _DISTS[self.distribution][0](*self.params)

    def summary(self) -> str:
        o = self
        observado, esperado = tr("Observado"), tr("Esperado")  # fuera del f-string: Babel solo extrae tr() de f-strings en Python >= 3.12
        return "\n".join([
            tr("Análisis de capacidad (no normal) - distribución {distribution}").format(distribution=o.distribution),
            tr("  LEI={lsl}  LES={usl}  N={n}  logL={loglik:.3f}  AIC={aic:.3f}").format(
                lsl=_fmt(o.lsl, 4), usl=_fmt(o.usl, 4), n=o.n, loglik=o.loglik, aic=o.aic),
            tr("  Percentiles: 0.135% = {low:.5f}   50% = {median:.5f}   99.865% = {high:.5f}").format(
                low=o.x_low, median=o.x_median, high=o.x_high),
            tr("  Pp={pp}  PPL={ppl}  PPU={ppu}  Ppk={ppk}").format(
                pp=_fmt(o.pp), ppl=_fmt(o.ppl), ppu=_fmt(o.ppu), ppk=_fmt(o.ppk)),
            *([tr("  IC {ci}% Pp: ({pp_lo}, {pp_hi})   IC {ci}% Ppk: ({ppk_lo}, {ppk_hi})  [bootstrap {metodo}, {n_boot} remuestreos]").format(
                ci=round(o.ci_level * 100), pp_lo=_fmt(o.pp_ci[0]), pp_hi=_fmt(o.pp_ci[1]), ppk_lo=_fmt(o.ppk_ci[0]),
                ppk_hi=_fmt(o.ppk_ci[1]), metodo=o.ci_method.split(":")[1], n_boot=o.ci_method.split(":")[2])]
              if o.ci_method.startswith("bootstrap:") else []),
            tr("  Desempeño (PPM):            < LEI       > LES      Total"),
            f"    {observado:<18}{_fmt(o.ppm_obs[0]):>10}{_fmt(o.ppm_obs[1]):>12}{_fmt(o.ppm_obs[2]):>11}",
            f"    {esperado:<18}{_fmt(o.ppm_expected[0]):>10}{_fmt(o.ppm_expected[1]):>12}{_fmt(o.ppm_expected[2]):>11}",
        ])

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico).

        Con ``stable=True`` las filas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        o = self
        rows = [
            ("n", N_("N"), o.n), ("distribution", N_("Distribución"), o.distribution),
            ("lsl", N_("LEI"), o.lsl), ("usl", N_("LES"), o.usl), ("target", N_("Objetivo"), o.target),
            ("percentile_low", N_("Percentil 0.135%"), o.x_low), ("median", N_("Mediana"), o.x_median),
            ("percentile_high", N_("Percentil 99.865%"), o.x_high),
            ("pp", N_("Pp"), o.pp), ("ppl", N_("PPL"), o.ppl), ("ppu", N_("PPU"), o.ppu), ("ppk", N_("Ppk"), o.ppk),
            ("ppm_obs_below_lsl", N_("PPM obs < LEI"), o.ppm_obs[0]),
            ("ppm_obs_above_usl", N_("PPM obs > LES"), o.ppm_obs[1]),
            ("ppm_obs_total", N_("PPM obs total"), o.ppm_obs[2]),
            ("ppm_exp_below_lsl", N_("PPM esp < LEI"), o.ppm_expected[0]),
            ("ppm_exp_above_usl", N_("PPM esp > LES"), o.ppm_expected[1]),
            ("ppm_exp_total", N_("PPM esp total"), o.ppm_expected[2]),
        ]
        if o.ci_method.startswith("bootstrap:"):
            rows += [("pp_lower", N_("Pp, límite inferior"), o.pp_ci[0]), ("pp_upper", N_("Pp, límite superior"), o.pp_ci[1]),
                     ("ppk_lower", N_("Ppk, límite inferior"), o.ppk_ci[0]),
                     ("ppk_upper", N_("Ppk, límite superior"), o.ppk_ci[1])]
        return tabla_estadisticos(rows, stable)

    def to_excel(self, path) -> None:
        """Exporta el análisis de capacidad no normal a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Capacidad"))

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_capability

        return plot_capability(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def _indices_percentiles(frozen, lsl, usl) -> tuple:
    """Percentiles 0,135 %, 50 %, 99,865 % de la distribución ajustada y los índices Pp, PPL, PPU y Ppk."""
    p_lo, p_hi = stats.norm.cdf(-3), stats.norm.cdf(3)
    x_lo, x_med, x_hi = (float(frozen.ppf(q)) for q in (p_lo, 0.5, p_hi))
    pp = (usl - lsl) / (x_hi - x_lo) if lsl is not None and usl is not None else NAN
    ppu = (usl - x_med) / (x_hi - x_med) if usl is not None else NAN
    ppl = (x_med - lsl) / (x_med - x_lo) if lsl is not None else NAN
    ppk = float(np.nanmin([ppl, ppu]))
    return x_lo, x_med, x_hi, pp, ppl, ppu, ppk


def _ci_bootstrap_nonnormal(x, dist, fit_kw, lsl, usl, ci_level, n_boot, bootstrap_method, seed) -> tuple:
    """Intervalos bootstrap de Pp y Ppk re-ajustando la distribución en cada remuestreo."""
    con_pp = lsl is not None and usl is not None

    def indices(m):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                frozen = dist(*dist.fit(m, **fit_kw))
                _, _, _, pp, _, _, ppk = _indices_percentiles(frozen, lsl, usl)
        except Exception:  # noqa: BLE001 - un ajuste que falla en un remuestreo se descarta (NaN)
            return np.array([NAN, NAN] if con_pp else [NAN])
        return np.array([pp, ppk] if con_pp else [ppk])

    r = bootstrap_ci(x, indices, method=bootstrap_method, n_boot=n_boot, confidence=ci_level, seed=seed)
    lo, hi = r.ci
    if con_pp:
        return (float(lo[0]), float(hi[0])), (float(lo[1]), float(hi[1]))
    return (NAN, NAN), (float(lo[0]), float(hi[0]))


def capability_nonnormal(
    data,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
    *,
    distribution: str = "weibull",
    ci_method: str = "none",
    ci_level: float = 0.95,
    n_boot: int = 1000,
    bootstrap_method: str = "percentile",
    seed: int | None = None,
) -> NonNormalCapabilityResult:
    """Capacidad para datos no normales por percentiles de la distribución ajustada.

    Ajusta por máxima verosimilitud una de: ``normal``, ``lognormal``, ``weibull``,
    ``gamma``, ``exponential``, ``loglogistic``, ``logistic``, ``largest_extreme``,
    ``smallest_extreme`` (las distribuciones de soporte positivo usan umbral 0).

    Pp = (LES - LEI) / (X99.865 - X0.135); PPU = (LES - X50) / (X99.865 - X50);
    PPL = (X50 - LEI) / (X50 - X0.135); Ppk = min(PPL, PPU).

    Con ``ci_method='bootstrap'`` se añaden intervalos de Pp y Ppk: en cada remuestreo de las observaciones se
    **vuelve a ajustar** la distribución y se recalculan los índices, de modo que el intervalo recoge también la
    incertidumbre del ajuste. Es más lento que con datos normales (un ajuste por remuestreo): por eso ``n_boot``
    es 1000 y el método ``'percentile'`` por defecto (``'bca'`` hace además un ajuste por observación). Con
    ``ci_method='none'`` (por defecto) no se calcula ningún intervalo.
    """
    _check_specs(lsl, usl)
    if ci_method not in ("none", "bootstrap"):
        raise ValueError(tr("'ci_method' debe ser 'none' o 'bootstrap'."))
    if not 0 < ci_level < 1:
        raise ValueError(tr("'ci_level' debe estar entre 0 y 1."))
    key = distribution.lower()
    if key not in _DISTS:
        raise ValueError(tr(
            "Distribución no soportada: {distribution!r}. Opciones: {options}"
        ).format(distribution=distribution, options=sorted(_DISTS)))
    dist, fit_kw, positive = _DISTS[key]
    x = as_1d(data, "data")
    if x.size < 3:
        raise ValueError(tr("Se necesitan al menos 3 observaciones."))
    if positive and x.min() <= 0:
        raise ValueError(tr("La distribución {key} requiere datos estrictamente positivos.").format(key=key))

    params = dist.fit(x, **fit_kw)
    frozen = dist(*params)
    loglik = float(np.sum(frozen.logpdf(x)))
    n_free = len(params) - len(fit_kw)
    aic = 2 * n_free - 2 * loglik

    x_lo, x_med, x_hi, pp, ppl, ppu, ppk = _indices_percentiles(frozen, lsl, usl)

    pp_ci = ppk_ci = (NAN, NAN)
    if ci_method == "bootstrap":
        pp_ci, ppk_ci = _ci_bootstrap_nonnormal(x, dist, fit_kw, lsl, usl, ci_level, n_boot, bootstrap_method, seed)

    e_lo = 1e6 * float(frozen.cdf(lsl)) if lsl is not None else NAN
    e_hi = 1e6 * float(frozen.sf(usl)) if usl is not None else NAN
    return NonNormalCapabilityResult(
        distribution=key, params=tuple(float(p) for p in params), loglik=loglik, aic=aic,
        n=x.size, lsl=lsl, usl=usl, target=target,
        x_low=x_lo, x_median=x_med, x_high=x_hi, pp=pp, ppl=ppl, ppu=ppu, ppk=ppk,
        ppm_obs=_observed_ppm(x, lsl, usl),
        ppm_expected=(e_lo, e_hi, float(np.nansum([e_lo, e_hi]))), data=x,
        pp_ci=pp_ci, ppk_ci=ppk_ci, ci_level=ci_level,
        ci_method=f"bootstrap:{bootstrap_method}:{n_boot}" if ci_method == "bootstrap" else "none",
    )
