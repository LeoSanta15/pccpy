"""Gráficos con matplotlib: cartas de control, capacidad, probabilidad normal y sixpack."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
from scipy import stats
from scipy.special import boxcox as _boxcox

from ._data import as_1d, to_subgroups
from .normality import anderson_darling_pvalue, anderson_darling_statistic
from .results import ControlChart, Panel

#: Cartas cuyo eje x son observaciones individuales (no subgrupos).
_POINT_KINDS = ("I-MR", "EWMA", "CUSUM", "MA", "Z-MR", "G", "T")
BLUE, RED, GREEN, GRAY, ORANGE = "#1f4e9c", "#d62728", "#2e8b57", "#8c8c8c", "#e08a00"


# ------------------------------------------------------------------ cartas de control
def _draw_panel(ax, panel: Panel, zones: bool = False) -> None:
    x = np.arange(1, len(panel.values) + 1)
    labels = list(dict.fromkeys(panel.stage.tolist()))
    for lab in labels:
        m = panel.stage == lab
        xs = x[m]
        kw = dict(drawstyle="steps-mid")
        ax.plot(xs, panel.center[m], color=GREEN, lw=1.3, **kw)
        ax.plot(xs, panel.ucl[m], color=RED, lw=1.3, **kw)
        ax.plot(xs, panel.lcl[m], color=RED, lw=1.3, **kw)
        if zones and panel.symmetric:
            for k in (1, 2):
                for sgn in (1, -1):
                    ax.plot(xs, panel.center[m] + sgn * k * panel.sigma[m],
                            color=GRAY, lw=0.7, ls="--", **kw)
    ax.plot(x, panel.values, marker="o", ms=4, lw=1, color=BLUE, zorder=3)
    if panel.secondary is not None:
        ax.plot(x, panel.secondary, marker="o", ms=4, lw=1, color=ORANGE, zorder=3)

    tests_at = {}
    for t, idx in panel.violations.items():
        for i in idx:
            tests_at.setdefault(int(i), []).append(t)
    for i, ts in tests_at.items():
        y = panel.values[i]
        if panel.secondary is not None and panel.secondary[i] < panel.lcl[i]:
            y = panel.secondary[i]
        ax.plot(x[i], y, "s", color=RED, ms=7, zorder=4)
        ax.annotate(",".join(map(str, sorted(ts))), (x[i], y), textcoords="offset points",
                    xytext=(0, 7), ha="center", fontsize=8, color=RED)

    if len(labels) > 1:
        for lab in labels[1:]:
            first = x[panel.stage == lab][0]
            ax.axvline(first - 0.5, color=GRAY, ls=":", lw=1)

    for val, txt, col in ((panel.ucl[-1], "LCS", RED), (panel.center[-1], "LC", GREEN),
                          (panel.lcl[-1], "LCI", RED)):
        if np.isfinite(val):
            ax.annotate(f"{txt}={val:.4g}", xy=(1.0, val), xycoords=("axes fraction", "data"),
                        xytext=(4, 0), textcoords="offset points", va="center",
                        fontsize=8, color=col, annotation_clip=False)
    ax.set_ylabel(panel.ylabel)
    ax.grid(alpha=0.25)


def plot_control_chart(chart: ControlChart, *, zones: bool = False, figsize=None,
                       title: Optional[str] = None):
    """Dibuja todos los paneles de la carta, apilados. Devuelve la figura.

    ``zones=True`` agrega las líneas de 1 y 2 sigma (solo en gráficos simétricos).
    Los puntos que fallan una prueba se marcan en rojo con el número de la prueba.
    """
    k = len(chart.panels)
    fig, axes = plt.subplots(k, 1, sharex=True, figsize=figsize or (11, 3.6 * k), squeeze=False)
    for ax, panel in zip(axes[:, 0], chart.panels):
        _draw_panel(ax, panel, zones)
    axes[-1, 0].xaxis.set_major_locator(MaxNLocator(integer=True))
    axes[-1, 0].set_xlabel("Observación" if chart.kind in _POINT_KINDS else "Muestra")
    fig.suptitle(title or f"Carta de control {chart.kind}", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 0.9, 0.97))
    return fig


# ------------------------------------------------------------------------ capacidad
def plot_capability(res, *, bins=None, ax=None):
    """Histograma de capacidad con curvas normales (dentro / general) y especificaciones."""
    from .capability import CapabilityResult

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    x = res.data
    ax.hist(x, bins=bins or "auto", density=True, color="#cfe0f5", edgecolor="white")
    pts = [x.min(), x.max()] + [v for v in (res.lsl, res.usl) if v is not None]
    pad = 0.05 * (max(pts) - min(pts))
    grid = np.linspace(min(pts) - pad, max(pts) + pad, 400)

    if isinstance(res, CapabilityResult):
        if res.transform:
            lam = res.transform["lambda"]
            y = _boxcox(x, lam)
            g = grid[grid > 0]
            ax.plot(g, stats.norm.pdf(_boxcox(g, lam), y.mean(), y.std(ddof=1)) * g ** (lam - 1),
                    color=BLUE, lw=1.6, label="General (Box-Cox)")
        else:
            ax.plot(grid, stats.norm.pdf(grid, res.mean, res.sigma_within), color=BLUE,
                    lw=1.4, ls="--", label="Dentro")
            ax.plot(grid, stats.norm.pdf(grid, res.mean, res.sigma_overall), color=ORANGE,
                    lw=1.6, label="General")
    else:
        ax.plot(grid, res.frozen.pdf(grid), color=BLUE, lw=1.6, label=res.distribution)

    if res.lsl is not None:
        ax.axvline(res.lsl, color=RED, lw=1.5, label="LEI")
    if res.usl is not None:
        ax.axvline(res.usl, color=RED, lw=1.5, ls="-.", label="LES")
    if res.target is not None:
        ax.axvline(res.target, color=GREEN, lw=1.3, ls=":", label="Objetivo")
    ax.set_xlabel("Valor")
    ax.set_ylabel("Densidad")
    ax.set_title("Histograma de capacidad")
    ax.legend(fontsize=8)
    if fig is not None:
        fig.tight_layout()
    return ax.figure


def probability_plot(data, *, ax=None):
    """Gráfico de probabilidad normal (rangos medianos de Benard) con prueba de Anderson-Darling."""
    x = np.sort(as_1d(data, "data"))
    n = x.size
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4.5))
    p = (np.arange(1, n + 1) - 0.3) / (n + 0.4)
    ax.plot(x, stats.norm.ppf(p), "o", ms=4, color=BLUE)
    mu, s = x.mean(), x.std(ddof=1)
    ax.plot(x, (x - mu) / s, color=RED, lw=1.3)
    ticks = np.array([0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9])
    ax.set_yticks(stats.norm.ppf(ticks / 100))
    ax.set_yticklabels([f"{t:g}" for t in ticks])
    a2 = anderson_darling_statistic(x)
    pv = anderson_darling_pvalue(a2, n)
    ptxt = "< 0.005" if pv < 0.005 else f"= {pv:.3f}"
    ax.text(0.03, 0.97, f"AD = {a2:.3f}\nValor p {ptxt}\nN = {n}", transform=ax.transAxes,
            va="top", fontsize=8, bbox=dict(fc="white", ec=GRAY, alpha=0.9))
    ax.set_xlabel("Valor")
    ax.set_ylabel("Porcentaje")
    ax.set_title("Gráfico de probabilidad normal")
    ax.grid(alpha=0.25)
    if fig is not None:
        fig.tight_layout()
    return ax.figure


def _capability_plot(ax, res) -> None:
    """Barras 'Especificación / Dentro / General' del sixpack."""
    m = res.mean
    lo = res.lsl if res.lsl is not None else m - 4 * res.sigma_overall
    hi = res.usl if res.usl is not None else m + 4 * res.sigma_overall
    rows = [
        (2, "Espec.", lo, hi, RED, res.lsl is not None, res.usl is not None),
        (1, "Dentro", m - 3 * res.sigma_within, m + 3 * res.sigma_within, BLUE, True, True),
        (0, "General", m - 3 * res.sigma_overall, m + 3 * res.sigma_overall, ORANGE, True, True),
    ]
    for y, _, a, b, col, _, _ in rows:
        ax.hlines(y, a, b, color=col, lw=3)
        ax.plot([m], [y], "o", color=col)
    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels(["Espec.", "Dentro", "General"])
    ax.set_ylim(-0.7, 2.7)
    txt = (f"Dentro\nCp = {res.cp:.2f}\nCpk = {res.cpk:.2f}\n\n"
           f"General\nPp = {res.pp:.2f}\nPpk = {res.ppk:.2f}")
    ax.text(1.02, 0.5, txt.replace("nan", "*"), transform=ax.transAxes, va="center", fontsize=8)
    ax.set_title("Gráfico de capacidad")
    ax.grid(alpha=0.25, axis="x")


def capability_sixpack(data, lsl=None, usl=None, target=None, *, subgroup_size=None,
                       subgroup=None, tests=(1,), figsize=(13, 11)):
    """Capability Sixpack de Minitab: carta de control, últimos 25, histograma,
    probabilidad normal y gráfico de capacidad.

    Devuelve ``(figura, resultado_de_capacidad, carta_de_control)``.
    """
    from .capability import capability_analysis
    from .charts import imr_chart, xbar_r_chart, xbar_s_chart

    arr = np.asarray(data, dtype=float)
    grouped = arr.ndim == 2 or subgroup is not None or (subgroup_size is not None and subgroup_size > 1)
    res = capability_analysis(arr, lsl, usl, target, subgroup_size=subgroup_size, subgroup=subgroup)
    if grouped:
        g = to_subgroups(arr, subgroup_size, subgroup)
        fn = xbar_r_chart if g.shape[1] <= 8 else xbar_s_chart
        chart = fn(g, tests=tests)
    else:
        g = None
        chart = imr_chart(arr, tests=tests)

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.42)
    ax_a, ax_b, ax_c = (fig.add_subplot(gs[i, 0]) for i in range(3))
    _draw_panel(ax_a, chart.panels[0])
    _draw_panel(ax_b, chart.panels[1])
    ax_a.set_title(chart.panels[0].name + " (dentro)", fontsize=10)
    ax_b.set_title(chart.panels[1].name, fontsize=10)

    if grouped:
        last = g[-25:]
        base = len(g) - len(last)
        for i, row in enumerate(last):
            ax_c.plot(np.full(row.size, base + i + 1), row, "o", ms=4, color=BLUE, alpha=0.7)
        ax_c.set_title("Últimos 25 subgrupos", fontsize=10)
        ax_c.set_xlabel("Subgrupo")
    else:
        lastv = arr[-25:]
        ax_c.plot(np.arange(len(arr) - len(lastv) + 1, len(arr) + 1), lastv, "o-", ms=4, color=BLUE)
        ax_c.set_title("Últimas 25 observaciones", fontsize=10)
        ax_c.set_xlabel("Observación")
    ax_c.axhline(res.mean, color=GREEN, lw=1)
    ax_c.grid(alpha=0.25)

    plot_capability(res, ax=fig.add_subplot(gs[0, 1]))
    probability_plot(res.data, ax=fig.add_subplot(gs[1, 1]))
    _capability_plot(fig.add_subplot(gs[2, 1]), res)
    fig.suptitle("Sixpack de capacidad", fontweight="bold")
    return fig, res, chart
