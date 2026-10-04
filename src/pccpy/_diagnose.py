"""Diagnóstico rápido de un proceso: estadísticos, normalidad, tendencias y recomendación."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

from ._data import _excel_writer
from ._i18n import tr

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    import pandas as pd

__all__ = ["DiagnoseResult", "diagnose"]


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

    # ══════════════════════════════════════════════════════════════════════
    def to_frame(self) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico)."""
        import pandas as pd

        o = self
        rows = [
            ("N", o.n), ("Media", o.mean), ("Desv.Est.", o.std), ("CV (%)", o.cv),
            ("Mínimo", o.min_val), ("Máximo", o.max_val), ("Mediana", o.median),
            ("Asimetría", o.skewness), ("Curtosis", o.kurtosis),
            ("Estadístico normalidad", o.normality_stat),
            ("p-valor normalidad", o.normality_p),
            ("Distribución normal", o.is_normal),
            ("Tiene tendencia", o.has_trend),
            ("Dirección tendencia", o.trend_direction),
            ("Valores atípicos (IQR)", o.outlier_count),
            ("LEI", o.lsl), ("LES", o.usl), ("Objetivo", o.target),
            ("Cp estimado", o.cp), ("Cpk estimado", o.cpk),
            ("Función recomendada", o.recommended_function),
        ]
        return pd.DataFrame(rows, columns=["estadístico", "valor"]).set_index("estadístico")

    def to_excel(self, path) -> None:
        """Exporta el diagnóstico a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name="Diagnóstico")

    def summary(self) -> str:
        """Resumen en texto al estilo sesión de Minitab."""
        sep = "═" * 60
        lines = [
            sep,
            "  DIAGNÓSTICO RÁPIDO DEL PROCESO",
            sep,
            f"  N               : {self.n}",
            f"  Media           : {self.mean:.4f}",
            f"  Desv. estándar  : {self.std:.4f}",
            f"  CV              : {self.cv:.2f} %",
            f"  Mínimo / Máximo : {self.min_val:.4f}  /  {self.max_val:.4f}",
            f"  Mediana         : {self.median:.4f}",
            f"  Asimetría       : {self.skewness:.4f}",
            f"  Curtosis        : {self.kurtosis:.4f}",
            "",
            "  ── Normalidad (prueba de normalidad) ──",
            f"  Estadístico     : {self.normality_stat:.4f}",
            f"  Valor p         : {self.normality_p:.4f}",
            f"  Distribución    : {'Normal (p > 0.05)' if self.is_normal else 'No normal (p ≤ 0.05)'}",
        ]
        if self.has_trend:
            lines += [
                "",
                "  ── Tendencia ──",
                f"  Se detectó tendencia {self.trend_direction}.",
            ]
        if self.outlier_count:
            lines += [
                "",
                "  ── Valores atípicos (IQR) ──",
                f"  Cantidad : {self.outlier_count}",
                f"  Índices  : {self.outlier_indices[:10]}"
                + (" …" if len(self.outlier_indices) > 10 else ""),
            ]
        if self.cp is not None:
            lines += [
                "",
                "  ── Capacidad (estimada) ──",
                f"  Cp  : {self.cp:.3f}",
                f"  Cpk : {self.cpk:.3f}",
            ]
        if self.issues:
            lines += ["", "  ── Alertas ──"]
            for issue in self.issues:
                lines.append(f"  ⚠  {issue}")
        lines += [
            "",
            "  ── Análisis recomendado ──",
            f"  Función : {self.recommended_function}",
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
                 color="#E74C3C", linewidth=1.8, label="Normal ajustada")
        if self.lsl is not None:
            ax1.axvline(self.lsl, color="#E67E22", ls="--", lw=1.2, label=f"LIE={self.lsl}")
        if self.usl is not None:
            ax1.axvline(self.usl, color="#E67E22", ls="--", lw=1.2, label=f"LSE={self.usl}")
        if self.target is not None:
            ax1.axvline(self.target, color="#27AE60", ls=":", lw=1.2, label=f"Objetivo={self.target}")
        ax1.set_title("Histograma", fontsize=10)
        ax1.set_xlabel("Valor")
        ax1.set_ylabel("Densidad")
        ax1.legend(fontsize=8)
        norm_str = "Normal" if self.is_normal else "No normal"
        ax1.text(0.98, 0.97, f"p = {self.normality_p:.3f}  ({norm_str})",
                 transform=ax1.transAxes, ha="right", va="top", fontsize=8,
                 color="#555")

        # ── Secuencia ─────────────────────────────────────────────────────
        ax2 = fig.add_subplot(gs[1])
        ax2.plot(self._x, color="#5B9BD5", linewidth=1, marker="o",
                 markersize=3, markerfacecolor="white", markeredgewidth=0.8)
        ax2.axhline(self.mean, color="#E74C3C", linewidth=1.2, label=f"Media={self.mean:.3f}")
        if self.outlier_indices:
            ax2.scatter(self.outlier_indices, self._x[self.outlier_indices],
                        color="#E74C3C", zorder=5, s=40, label="Atípicos")
        ax2.set_title("Gráfico de secuencia", fontsize=10)
        ax2.set_xlabel("Observación")
        ax2.set_ylabel("Valor")
        ax2.legend(fontsize=8)
        fig.suptitle("Diagnóstico rápido del proceso", fontsize=11, fontweight="bold")
        return fig

    # interno: guardamos x para plot() — se asigna tras la construcción
    _x: np.ndarray = field(default=None, repr=False, compare=False)  # type: ignore[assignment, arg-type]


# ══════════════════════════════════════════════════════════════════════════════
# Función pública
# ══════════════════════════════════════════════════════════════════════════════

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

    # ── Recomendación ──────────────────────────────────────────────────────
    if has_trend:
        rec_fn = "run_chart"
        rec_snippet = "import pccpy as pp\nresultado = pp.run_chart(datos)"
    elif lsl is not None or usl is not None:
        if is_normal:
            rec_fn = "capability_analysis"
            args = ", ".join(
                f"{k}={v!r}"
                for k, v in [("lsl", lsl), ("usl", usl), ("target", target)]
                if v is not None
            )
            rec_snippet = f"import pccpy as pp\nresultado = pp.capability_analysis(datos, {args})"
        else:
            rec_fn = "capability_boxcox"
            args = ", ".join(
                f"{k}={v!r}"
                for k, v in [("lsl", lsl), ("usl", usl)]
                if v is not None
            )
            rec_snippet = f"import pccpy as pp\nresultado = pp.capability_boxcox(datos, {args})"
    elif n >= 30 and is_normal or n >= 30:
        rec_fn = "imr_chart"
        rec_snippet = "import pccpy as pp\nresultado = pp.imr_chart(datos)"
    else:
        rec_fn = "imr_chart"
        rec_snippet = "import pccpy as pp\nresultado = pp.imr_chart(datos)"

    # ── Capacidad estimada ─────────────────────────────────────────────────
    cp = cpk = None
    if lsl is not None and usl is not None and std > 0:
        cp = float((usl - lsl) / (6 * std))
        cpk = float(min(usl - mean, mean - lsl) / (3 * std))

    # ── Alertas ────────────────────────────────────────────────────────────
    issues: list[str] = []
    if not is_normal:
        issues.append("La distribución no es normal (p ≤ 0.05). Considera transformación o análisis no paramétrico.")
    if has_trend:
        issues.append(f"Se detectó tendencia {trend_dir}. Verifica causas asignables antes de calcular capacidad.")
    if outlier_idx:
        issues.append(f"{len(outlier_idx)} valor(es) atípico(s) detectado(s). Investiga su origen.")
    if cp is not None and cp < 1.0:
        issues.append(f"Cp = {cp:.2f} < 1.0: el proceso no es capaz con las especificaciones dadas.")
    if cpk is not None and cpk < 1.0:
        issues.append(f"Cpk = {cpk:.2f} < 1.0: el proceso no está centrado o no es capaz.")

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
    )
    result._x = x
    return result
