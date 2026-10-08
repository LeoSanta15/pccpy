"""Diagnóstico rápido de un proceso: estadísticos, normalidad, tendencias y recomendación."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

from ._data import _excel_writer
from ._frames import tabla_estadisticos
from ._i18n import N_, tr

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    import pandas as pd

__all__ = ["DiagnoseResult", "diagnose"]


def _tendencia(direccion: str) -> str:
    """Texto de la dirección de la tendencia; el valor guardado en el resultado ('creciente'/'decreciente') no se traduce."""
    return {"creciente": tr("creciente"), "decreciente": tr("decreciente")}.get(direccion, direccion)


@dataclass
class DiagnoseResult:
    """Resultado del diagnóstico rápido devuelto por :func:`diagnose`."""

    # ── Estadísticos básicos ────────────────────────────────────────────────
    n: int
    mean: float
    std: float
    cv: float
    min_val: float
    max_val: float
    median: float
    skewness: float
    kurtosis: float

    # ── Normalidad (Anderson-Darling vía scipy) ─────────────────────────────
    normality_stat: float
    normality_p: float
    is_normal: bool

    # ── Tendencia ──────────────────────────────────────────────────────────
    has_trend: bool
    trend_direction: str        # 'creciente', 'decreciente', ''

    # ── Valores atípicos (método IQR) ───────────────────────────────────────
    outlier_count: int
    outlier_indices: list[int]

    # ── Recomendación ──────────────────────────────────────────────────────
    recommended_function: str
    recommended_snippet: str
    issues: list[str] = field(default_factory=list)

    # ── Especificaciones (opcionales) ───────────────────────────────────────
    lsl: float | None = None
    usl: float | None = None
    target: float | None = None
    cp: float | None = None
    cpk: float | None = None

    # ── Asimetría y forma (solo si no es normal) ────────────────────────────
    non_normal_reason: str = ""            # 'outliers', 'skewed', 'shape' o ''
    transform_normalizes: bool | None = None  # ¿Box-Cox deja los datos normales? (None si no aplica)
    best_distribution: str | None = None    # distribución con menor AIC si gana a la normal

    # ══════════════════════════════════════════════════════════════════════
    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico).

        Con ``stable=True`` las filas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        o = self
        rows = [
            ("n", N_("N"), o.n), ("mean", N_("Media"), o.mean), ("std", N_("Desv.Est."), o.std),
            ("cv_pct", N_("CV (%)"), o.cv),
            ("min", N_("Mínimo"), o.min_val), ("max", N_("Máximo"), o.max_val), ("median", N_("Mediana"), o.median),
            ("skewness", N_("Asimetría"), o.skewness), ("kurtosis", N_("Curtosis"), o.kurtosis),
            ("normality_stat", N_("Estadístico normalidad"), o.normality_stat),
            ("normality_p", N_("p-valor normalidad"), o.normality_p),
            ("is_normal", N_("Distribución normal"), o.is_normal),
            ("has_trend", N_("Tiene tendencia"), o.has_trend),
            ("trend_direction", N_("Dirección tendencia"), o.trend_direction),
            ("outlier_count", N_("Valores atípicos (IQR)"), o.outlier_count),
            ("lsl", N_("LEI"), o.lsl), ("usl", N_("LES"), o.usl), ("target", N_("Objetivo"), o.target),
            ("cp_estimated", N_("Cp estimado"), o.cp), ("cpk_estimated", N_("Cpk estimado"), o.cpk),
            ("recommended_function", N_("Función recomendada"), o.recommended_function),
        ]
        if o.non_normal_reason:
            rows += [("non_normal_reason", N_("Motivo de la no normalidad"), o.non_normal_reason),
                     ("best_distribution", N_("Mejor distribución (AIC)"), o.best_distribution)]
        return tabla_estadisticos(rows, stable)

    def to_excel(self, path) -> None:
        """Exporta el diagnóstico a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Diagnóstico"))

    def summary(self) -> str:
        """Resumen en texto al estilo sesión de Minitab."""
        sep = "═" * 60
        distribucion = tr("Normal (p > 0.05)") if self.is_normal else tr("No normal (p ≤ 0.05)")
        lines = [
            sep,
            tr("  DIAGNÓSTICO RÁPIDO DEL PROCESO"),
            sep,
            tr("  N               : {n}").format(n=self.n),
            tr("  Media           : {mean:.4f}").format(mean=self.mean),
            tr("  Desv. estándar  : {std:.4f}").format(std=self.std),
            tr("  CV              : {cv:.2f} %").format(cv=self.cv),
            tr("  Mínimo / Máximo : {low:.4f}  /  {high:.4f}").format(low=self.min_val, high=self.max_val),
            tr("  Mediana         : {median:.4f}").format(median=self.median),
            tr("  Asimetría       : {skewness:.4f}").format(skewness=self.skewness),
            tr("  Curtosis        : {kurtosis:.4f}").format(kurtosis=self.kurtosis),
            "",
            tr("  ── Normalidad (prueba de normalidad) ──"),
            tr("  Estadístico     : {stat:.4f}").format(stat=self.normality_stat),
            tr("  Valor p         : {p:.4f}").format(p=self.normality_p),
            tr("  Distribución    : {distribution}").format(distribution=distribucion),
        ]
        if self.non_normal_reason:
            motivos = {"outliers": tr("valores atípicos (sin ellos los datos son normales)"),
                       "skewed": tr("asimetría"), "shape": tr("forma de la distribución (colas, varias modas)")}
            lines += ["", tr("  ── Por qué no es normal ──"),
                      tr("  Motivo          : {reason}").format(reason=motivos.get(self.non_normal_reason, ""))]
            if self.transform_normalizes is not None:
                lines.append(tr("  Box-Cox normaliza: {answer}").format(
                    answer=tr("sí") if self.transform_normalizes else tr("no")))
            if self.best_distribution:
                lines.append(tr("  Mejor distribución (AIC): {distribution}").format(distribution=self.best_distribution))
        if self.has_trend:
            lines += [
                "",
                tr("  ── Tendencia ──"),
                tr("  Se detectó tendencia {direction}.").format(direction=_tendencia(self.trend_direction)),
            ]
        if self.outlier_count:
            lines += [
                "",
                tr("  ── Valores atípicos (IQR) ──"),
                tr("  Cantidad : {count}").format(count=self.outlier_count),
                tr("  Índices  : {indices}").format(indices=self.outlier_indices[:10])
                + (" …" if len(self.outlier_indices) > 10 else ""),
            ]
        if self.cp is not None:
            lines += [
                "",
                tr("  ── Capacidad (estimada) ──"),
                tr("  Cp  : {cp:.3f}").format(cp=self.cp),
                tr("  Cpk : {cpk:.3f}").format(cpk=self.cpk),
            ]
        if self.issues:
            lines += ["", tr("  ── Alertas ──")]
            for issue in self.issues:
                lines.append(f"  ⚠  {issue}")
        lines += [
            "",
            tr("  ── Análisis recomendado ──"),
            tr("  Función : {function}").format(function=self.recommended_function),
            "",
            textwrap.indent(self.recommended_snippet, "  "),
            sep,
        ]
        return "\n".join(lines)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)

    def plot(self, *, figsize: tuple[float, float] = (10, 4)) -> plt.Figure:
        """Histograma con curva normal + gráfico de secuencia.

        Returns
        -------
        matplotlib.figure.Figure
        """
        import matplotlib.pyplot as plt
        from matplotlib import gridspec

        with plt.rc_context({}):
            fig = plt.figure(figsize=figsize, constrained_layout=True)
        gs = gridspec.GridSpec(1, 2, figure=fig)

        # ── Histograma ─────────────────────────────────────────────────────
        ax1 = fig.add_subplot(gs[0])
        ax1.hist(self._x, bins="auto", density=True, color="#5B9BD5", alpha=0.7,
                 edgecolor="white", linewidth=0.5)
        xgrid = np.linspace(self._x.min(), self._x.max(), 200)
        ax1.plot(xgrid, stats.norm.pdf(xgrid, self.mean, self.std),
                 color="#E74C3C", linewidth=1.8, label=tr("Normal ajustada"))
        if self.lsl is not None:
            ax1.axvline(self.lsl, color="#E67E22", ls="--", lw=1.2, label=tr("LIE={v}").format(v=self.lsl))
        if self.usl is not None:
            ax1.axvline(self.usl, color="#E67E22", ls="--", lw=1.2, label=tr("LSE={v}").format(v=self.usl))
        if self.target is not None:
            ax1.axvline(self.target, color="#27AE60", ls=":", lw=1.2, label=tr("Objetivo={v}").format(v=self.target))
        ax1.set_title(tr("Histograma"), fontsize=10)
        ax1.set_xlabel(tr("Valor"))
        ax1.set_ylabel(tr("Densidad"))
        ax1.legend(fontsize=8)
        norm_str = tr("Normal") if self.is_normal else tr("No normal")
        ax1.text(0.98, 0.97, f"p = {self.normality_p:.3f}  ({norm_str})",
                 transform=ax1.transAxes, ha="right", va="top", fontsize=8,
                 color="#555")

        # ── Secuencia ─────────────────────────────────────────────────────
        ax2 = fig.add_subplot(gs[1])
        ax2.plot(self._x, color="#5B9BD5", linewidth=1, marker="o",
                 markersize=3, markerfacecolor="white", markeredgewidth=0.8)
        ax2.axhline(self.mean, color="#E74C3C", linewidth=1.2, label=tr("Media={v:.3f}").format(v=self.mean))
        if self.outlier_indices:
            ax2.scatter(self.outlier_indices, self._x[self.outlier_indices],
                        color="#E74C3C", zorder=5, s=40, label=tr("Atípicos"))
        ax2.set_title(tr("Gráfico de secuencia"), fontsize=10)
        ax2.set_xlabel(tr("Observación"))
        ax2.set_ylabel(tr("Valor"))
        ax2.legend(fontsize=8)
        fig.suptitle(tr("Diagnóstico rápido del proceso"), fontsize=11, fontweight="bold")
        return fig

    # interno: guardamos x para plot() — se asigna tras la construcción
    _x: np.ndarray = field(default=None, repr=False, compare=False)  # type: ignore[assignment, arg-type]


# ══════════════════════════════════════════════════════════════════════════════
# Función pública
# ══════════════════════════════════════════════════════════════════════════════

def _p_normalidad(x: np.ndarray) -> float:
    return float(stats.normaltest(x)[1]) if len(x) >= 8 else float("nan")


def _estudiar_no_normalidad(x: np.ndarray, skewness: float, outlier_mask: np.ndarray) -> tuple:
    """Motivo de la no normalidad, si Box-Cox normaliza y la distribución de menor AIC (si gana a la normal)."""
    # Atípicos como causa: hay algún punto muy lejano (a más de 3·RIC de los cuartiles, "far out" de Tukey), sin ellos
    # los datos son normales y simétricos. Una cola larga normal (p. ej. lognormal) no cumple esto: es asimetría.
    sin_atipicos = x[~outlier_mask]
    if outlier_mask.any() and len(sin_atipicos) >= 8:
        q1, q3 = np.percentile(x, [25, 75])
        lejanos = (x < q1 - 3 * (q3 - q1)) | (x > q3 + 3 * (q3 - q1))
        if lejanos.any() and _p_normalidad(sin_atipicos) > 0.05 and abs(stats.skew(sin_atipicos)) < 0.5:
            return "outliers", None, None
    razon = "skewed" if abs(skewness) >= 0.5 else "shape"

    from scipy.special import boxcox

    from .capability import _DISTS

    normaliza = None
    positivo = bool(x.min() > 0)
    if positivo:
        try:
            _, lam = stats.boxcox(x)
            normaliza = bool(_p_normalidad(boxcox(x, lam)) > 0.05)
        except Exception:  # noqa: BLE001 - un ajuste que falla no impide el diagnóstico
            normaliza = None

    candidatas = (["lognormal", "weibull", "gamma", "loglogistic"] if positivo
                  else ["logistic", "largest_extreme", "smallest_extreme"])
    aic = {}
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for nombre in ["normal", *candidatas]:
            dist, fit_kw, _ = _DISTS[nombre]
            try:
                p = dist.fit(x, **fit_kw)
                aic[nombre] = 2 * (len(p) - len(fit_kw)) - 2 * float(np.sum(dist(*p).logpdf(x)))
            except Exception:  # noqa: BLE001 - un ajuste que falla simplemente no compite
                aic.pop(nombre, None)
    mejor = None
    otras = {k: v for k, v in aic.items() if k != "normal"}
    if otras and "normal" in aic:
        k = min(otras, key=lambda nombre: otras[nombre])
        if otras[k] < aic["normal"] - 2:  # diferencia de AIC > 2: mejora apreciable sobre la normal
            mejor = k
    return razon, normaliza, mejor


def diagnose(
    x,
    *,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
) -> DiagnoseResult:
    """Diagnóstico rápido de un proceso 1-D.

    Calcula estadísticos descriptivos, prueba de normalidad, detección de
    tendencia y valores atípicos, e indica qué función de ``pccpy`` usar a
    continuación.

    Parameters
    ----------
    x : array-like
        Datos del proceso (vector 1-D).
    lsl : float, optional
        Límite de especificación inferior.
    usl : float, optional
        Límite de especificación superior.
    target : float, optional
        Valor objetivo (nominal).

    Returns
    -------
    DiagnoseResult
        Objeto con todos los resultados; llama a ``.summary()`` para un texto
        al estilo Minitab o a ``.plot()`` para un gráfico rápido.

    Examples
    --------
    >>> import numpy as np, pccpy as pp
    >>> rng = np.random.default_rng(0)
    >>> x = rng.normal(50, 2, 60)
    >>> d = pp.diagnose(x, lsl=44, usl=56)
    >>> print(d.summary())
    """
    x = np.asarray(x, dtype=float).ravel()
    n = len(x)
    if n < 4:
        raise ValueError(tr("diagnose requiere al menos 4 observaciones."))

    # ── Estadísticos básicos ────────────────────────────────────────────────
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    cv = float(std / mean * 100) if mean != 0 else float("nan")
    min_val = float(np.min(x))
    max_val = float(np.max(x))
    median = float(np.median(x))
    skewness = float(stats.skew(x))
    kurt = float(stats.kurtosis(x))

    # ── Normalidad ─────────────────────────────────────────────────────────
    if n < 8:
        norm_stat, norm_p = float("nan"), float("nan")
        is_normal = True
    else:
        norm_stat, norm_p = stats.normaltest(x)
        is_normal = bool(norm_p > 0.05)

    # ── Tendencia (Mann-Kendall simplificado: % incrementos) ────────────────
    diffs = np.diff(x)
    pct_inc = float((diffs > 0).mean())
    has_trend = pct_inc > 0.80 or pct_inc < 0.20
    trend_dir = "creciente" if pct_inc > 0.80 else ("decreciente" if pct_inc < 0.20 else "")

    # ── Valores atípicos (IQR × 1.5) ───────────────────────────────────────
    q1, q3 = float(np.percentile(x, 25)), float(np.percentile(x, 75))
    iqr = q3 - q1
    outlier_mask = (x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)
    outlier_idx = [int(i) for i in np.where(outlier_mask)[0]]

    # ── Por qué no es normal (solo con prueba de normalidad válida) ─────────
    razon, normaliza, mejor = "", None, None
    if not is_normal:
        razon, normaliza, mejor = _estudiar_no_normalidad(x, skewness, outlier_mask)

    # ── Recomendación ──────────────────────────────────────────────────────
    con_specs = lsl is not None or usl is not None
    specs_positivas = all(v is None or v > 0 for v in (lsl, usl, target))  # Box-Cox transforma también los límites
    args_specs = ", ".join(f"{k}={v!r}" for k, v in [("lsl", lsl), ("usl", usl), ("target", target)] if v is not None)
    if has_trend:
        rec_fn = "run_chart"
        rec_snippet = tr("import pccpy as pp\nresultado = pp.run_chart(datos)")
    elif con_specs:
        if is_normal or razon == "outliers":
            rec_fn = "capability_analysis"
            rec_snippet = tr("import pccpy as pp\nresultado = pp.capability_analysis(datos, {args})").format(args=args_specs)
        elif normaliza and specs_positivas:
            rec_fn = "capability_boxcox"
            args = ", ".join(f"{k}={v!r}" for k, v in [("lsl", lsl), ("usl", usl)] if v is not None)
            rec_snippet = tr("import pccpy as pp\nresultado = pp.capability_boxcox(datos, {args})").format(args=args)
        elif mejor:
            rec_fn = "capability_nonnormal"
            args = ", ".join(f"{k}={v!r}" for k, v in [("lsl", lsl), ("usl", usl)] if v is not None)
            rec_snippet = tr("import pccpy as pp\nresultado = pp.capability_nonnormal(datos, {args}, distribution={distribution!r})"
                             ).format(args=args, distribution=mejor)
        else:
            rec_fn = "capability_analysis"
            rec_snippet = tr("import pccpy as pp\nresultado = pp.capability_analysis(datos, {args})").format(args=args_specs)
    else:
        rec_fn = "imr_chart"
        rec_snippet = tr("import pccpy as pp\nresultado = pp.imr_chart(datos)")

    # ── Capacidad estimada ─────────────────────────────────────────────────
    cp = cpk = None
    if lsl is not None and usl is not None and std > 0:
        cp = float((usl - lsl) / (6 * std))
        cpk = float(min(usl - mean, mean - lsl) / (3 * std))

    # ── Alertas ────────────────────────────────────────────────────────────
    issues: list[str] = []
    if not is_normal:
        issues.append(tr("La distribución no es normal (p ≤ 0.05). Considera transformación o análisis no paramétrico."))
    if razon == "outliers":
        issues.append(tr("La no normalidad se debe a valores atípicos (sin ellos los datos son normales): investiga su "
                         "origen antes de transformar los datos."))
    elif razon in ("skewed", "shape") and con_specs and rec_fn == "capability_analysis":
        issues.append(tr("Ninguna transformación ni distribución ajusta claramente mejor que la normal: interpreta con "
                         "cautela los índices de capacidad normales (usa ci_method='bootstrap' para los intervalos)."))
    if normaliza and con_specs and not specs_positivas:
        issues.append(tr("Box-Cox normalizaría los datos, pero requiere límites de especificación y objetivo positivos; "
                         "se recomienda ajustar una distribución no normal."))
    if razon == "skewed" and not con_specs:
        issues.append(tr("Los datos son asimétricos (asimetría = {skewness:.2f}): los límites de I-MR suponen "
                         "normalidad y pueden dar falsas alarmas del lado de la cola larga.").format(skewness=skewness))
    if has_trend:
        issues.append(tr(
            "Se detectó tendencia {direction}. Verifica causas asignables antes de calcular capacidad."
        ).format(direction=_tendencia(trend_dir)))
    if outlier_idx:
        issues.append(tr("{count} valor(es) atípico(s) detectado(s). Investiga su origen.").format(count=len(outlier_idx)))
    if cp is not None and cp < 1.0:
        issues.append(tr("Cp = {cp:.2f} < 1.0: el proceso no es capaz con las especificaciones dadas.").format(cp=cp))
    if cpk is not None and cpk < 1.0:
        issues.append(tr("Cpk = {cpk:.2f} < 1.0: el proceso no está centrado o no es capaz.").format(cpk=cpk))

    result = DiagnoseResult(
        n=n, mean=mean, std=std, cv=cv,
        min_val=min_val, max_val=max_val, median=median,
        skewness=skewness, kurtosis=kurt,
        normality_stat=float(norm_stat), normality_p=float(norm_p),
        is_normal=is_normal,
        has_trend=has_trend, trend_direction=trend_dir,
        outlier_count=len(outlier_idx), outlier_indices=outlier_idx,
        recommended_function=rec_fn, recommended_snippet=rec_snippet,
        issues=issues, lsl=lsl, usl=usl, target=target,
        cp=cp, cpk=cpk,
        non_normal_reason=razon, transform_normalizes=normaliza, best_distribution=mejor,
    )
    result._x = x
    return result
