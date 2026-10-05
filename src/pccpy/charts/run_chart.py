"""Carta de corridas (Run Chart) con las 4 pruebas de aleatoriedad de Minitab."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from .._data import as_1d
from .._frames import tabla_estadisticos
from .._i18n import N_, tr

NAN = float("nan")


def _runs_about_median(x: np.ndarray):
    med = float(np.median(x))
    mask = x != med
    side = x[mask] > med  # True = above, False = below
    n1, n2 = int(side.sum()), int((~side).sum())
    n = n1 + n2
    if n < 2 or n1 == 0 or n2 == 0:
        return 0, n1, n2, NAN, NAN, NAN, NAN, 0
    s = side.astype(int)
    runs = 1 + int(np.sum(s[1:] != s[:-1]))
    er = 2.0 * n1 * n2 / n + 1
    vr = max(2.0 * n1 * n2 * (2.0 * n1 * n2 - n) / (n**2 * (n - 1)), 1e-12)
    z = (runs - er) / math.sqrt(vr)
    p_clust = float(stats.norm.cdf(z))
    p_mix = float(stats.norm.sf(z))
    # Longest run
    longest, cur = 1, 1
    for i in range(1, len(s)):
        cur = cur + 1 if s[i] == s[i - 1] else 1
        longest = max(longest, cur)
    return runs, n1, n2, er, vr, p_clust, p_mix, longest


def _runs_updown(x: np.ndarray):
    n = len(x)
    diff = np.sign(np.diff(x.astype(float)))
    diff = diff[diff != 0]
    m = len(diff)
    if m < 2:
        return 0, NAN, NAN, NAN, NAN, 0
    runs = 1 + int(np.sum(diff[1:] != diff[:-1]))
    er = (2.0 * n - 1) / 3.0
    vr = max((16.0 * n - 29.0) / 90.0, 1e-12)
    z = (runs - er) / math.sqrt(vr)
    p_trends = float(stats.norm.cdf(z))
    p_osc = float(stats.norm.sf(z))
    # Longest run up or down (in points, = longest run in diff + 1)
    longest, cur = 1, 1
    for i in range(1, len(diff)):
        cur = cur + 1 if diff[i] == diff[i - 1] else 1
        longest = max(longest, cur)
    return runs, er, vr, p_trends, p_osc, longest + 1


@dataclass
class RunChartResult:
    """Resultado de :func:`run_chart` con las 4 pruebas de aleatoriedad."""

    values: np.ndarray = field(repr=False)
    median: float
    n_above: int
    n_below: int
    n_runs_about_median: int
    expected_runs_about_median: float
    p_clustering: float
    p_mixtures: float
    longest_run_about_median: int
    n_runs_updown: int
    expected_runs_updown: float
    p_trends: float
    p_oscillation: float
    longest_run_updown: int
    alpha: float = 0.05

    def _flag(self, p: float) -> str:
        return " *" if not math.isnan(p) and p < self.alpha else ""

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla con los estadísticos de las 4 pruebas.

        Con ``stable=True`` las filas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        rows = [
            ("median", N_("Mediana"), self.median),
            ("n_above", N_("N sobre mediana"), self.n_above),
            ("n_below", N_("N bajo mediana"), self.n_below),
            ("runs_about_median", N_("Rachas sobre/bajo mediana"), self.n_runs_about_median),
            ("expected_runs_about_median", N_("Rachas esperadas (mediana)"), round(self.expected_runs_about_median, 3)),
            ("p_clustering", N_("p Agrupamiento (clustering)"), round(self.p_clustering, 4)),
            ("p_mixtures", N_("p Mezclas (mixtures)"), round(self.p_mixtures, 4)),
            ("longest_run_about_median", N_("Racha más larga (mediana)"), self.longest_run_about_median),
            ("runs_updown", N_("Rachas arriba/abajo"), self.n_runs_updown),
            ("expected_runs_updown", N_("Rachas esperadas (arriba/abajo)"), round(self.expected_runs_updown, 3)),
            ("p_trends", N_("p Tendencias (trends)"), round(self.p_trends, 4)),
            ("p_oscillation", N_("p Oscilación (oscillation)"), round(self.p_oscillation, 4)),
            ("longest_run_updown", N_("Racha más larga (arriba/abajo)"), self.longest_run_updown),
        ]
        return tabla_estadisticos(rows, stable)

    def summary(self) -> str:
        o = self
        a = round(o.alpha * 100)
        L = [
            tr("Carta de corridas  N={n}  Mediana={median:.5g}").format(n=len(o.values), median=o.median),
            tr("  Pruebas de aleatoriedad (α={alpha}%); * = señal").format(alpha=a),
            tr("  Sobre/bajo la mediana:"),
            tr("    Rachas={runs}  Esperadas={expected:.2f}  Racha más larga={longest}").format(
                runs=o.n_runs_about_median, expected=o.expected_runs_about_median, longest=o.longest_run_about_median),
            tr("    p Agrupamiento={p_clustering:.4f}{flag_clustering}  p Mezclas={p_mixtures:.4f}{flag_mixtures}").format(
                p_clustering=o.p_clustering, flag_clustering=o._flag(o.p_clustering),
                p_mixtures=o.p_mixtures, flag_mixtures=o._flag(o.p_mixtures)),
            tr("  Arriba/abajo:"),
            tr("    Rachas={runs}  Esperadas={expected:.2f}  Racha más larga={longest}").format(
                runs=o.n_runs_updown, expected=o.expected_runs_updown, longest=o.longest_run_updown),
            tr("    p Tendencias={p_trends:.4f}{flag_trends}  p Oscilación={p_oscillation:.4f}{flag_oscillation}").format(
                p_trends=o.p_trends, flag_trends=o._flag(o.p_trends),
                p_oscillation=o.p_oscillation, flag_oscillation=o._flag(o.p_oscillation)),
        ]
        return "\n".join(L)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        """Gráfico de la carta de corridas. Ver :func:`pccpy.plotting.plot_run_chart`."""
        from ..plotting import plot_run_chart

        return plot_run_chart(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def run_chart(data, *, alpha: float = 0.05) -> RunChartResult:
    """Carta de corridas con las 4 pruebas de aleatoriedad de Minitab.

    Parameters
    ----------
    data : array-like
        Vector 1-D de observaciones individuales en orden de producción.
    alpha : float
        Nivel de significancia para señalar las pruebas (por defecto 0.05).

    Returns
    -------
    RunChartResult
        Resultado con estadísticos, p-valores y método ``.plot()``.

    Pruebas
    -------
    1. **Agrupamiento** (clustering): pocas rachas sobre/bajo la mediana → datos agrupados.
    2. **Mezclas** (mixtures): muchas rachas sobre/bajo la mediana → mezcla de procesos.
    3. **Tendencias** (trends): pocas rachas arriba/abajo → tendencia sostenida.
    4. **Oscilación** (oscillation): muchas rachas arriba/abajo → zigzag sistemático.
    """
    x = as_1d(data, "data")
    if len(x) < 3:
        raise ValueError(tr("run_chart requiere al menos 3 observaciones."))
    med = float(np.median(x))
    r_med, n1, n2, er_med, _, p_clust, p_mix, lr_med = _runs_about_median(x)
    r_ud, er_ud, _, p_trends, p_osc, lr_ud = _runs_updown(x)
    return RunChartResult(
        values=x, median=med,
        n_above=n1, n_below=n2,
        n_runs_about_median=r_med,
        expected_runs_about_median=round(er_med, 3) if not math.isnan(er_med) else NAN,
        p_clustering=p_clust, p_mixtures=p_mix,
        longest_run_about_median=lr_med,
        n_runs_updown=r_ud,
        expected_runs_updown=round(er_ud, 3) if not math.isnan(er_ud) else NAN,
        p_trends=p_trends, p_oscillation=p_osc,
        longest_run_updown=lr_ud,
        alpha=alpha,
    )
