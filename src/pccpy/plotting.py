"""Gráficos con matplotlib: cartas de control, capacidad, probabilidad normal y sixpack."""
from __future__ import annotations

import math

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
def _draw_panel(ax, panel: Panel, zones: bool = True) -> None:
    x = np.arange(1, len(panel.values) + 1)
    labels = list(dict.fromkeys(panel.stage.tolist()))
    for lab in labels:
        m = panel.stage == lab
        xs = x[m]
        kw = {"drawstyle": "steps-mid"}
        ax.plot(xs, panel.center[m], color=GREEN, lw=1.3, **kw)
        ax.plot(xs, panel.ucl[m], color=RED, lw=1.3, **kw)
        ax.plot(xs, panel.lcl[m], color=RED, lw=1.3, **kw)
        if zones:
            for k in (1, 2):
                for sgn in (1, -1):
                    ax.plot(xs, panel.center[m] + sgn * k * panel.sigma[m],
                            color=GRAY, lw=0.7, ls="--", **kw)
    ax.plot(x, panel.values, marker="o", ms=4, lw=1, color=BLUE, zorder=3)
    if panel.secondary is not None:
        ax.plot(x, panel.secondary, marker="o", ms=4, lw=1, color=ORANGE, zorder=3)

    tests_at: dict[int, list] = {}
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


def plot_control_chart(chart: ControlChart, *, zones: bool = True, figsize=None,
                       title: str | None = None):
    """Dibuja todos los paneles de la carta, apilados. Devuelve la figura.

    ``zones=True`` (por defecto) agrega las líneas de 1 y 2 sigma en todos los
    paneles, igual que Minitab. Pasa ``zones=False`` para mostrar solo LCS, LC y LCI.
    Los puntos que fallan una prueba se marcan en rojo con el número de la prueba.
    """
    with plt.rc_context({}):
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
        with plt.rc_context({}):
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
        with plt.rc_context({}):
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
            va="top", fontsize=8, bbox={"fc": "white", "ec": GRAY, "alpha": 0.9})
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
                       subgroup=None, value=None, tests=(1,), figsize=(13, 11)):
    """Capability Sixpack de Minitab: carta de control, últimos 25, histograma,
    probabilidad normal y gráfico de capacidad.

    Devuelve ``(figura, resultado_de_capacidad, carta_de_control)``.
    Acepta los mismos formatos de entrada que :func:`xbar_r_chart`.
    """
    from .capability import capability_analysis
    from .charts import imr_chart, xbar_r_chart, xbar_s_chart

    arr = np.asarray(data, dtype=float)
    grouped = arr.ndim == 2 or subgroup is not None or (subgroup_size is not None and subgroup_size > 1)
    res = capability_analysis(arr, lsl, usl, target, subgroup_size=subgroup_size,
                              subgroup=subgroup, value=value)
    if grouped:
        g, _ = to_subgroups(arr, subgroup_size, subgroup, value=value)
        fn = xbar_r_chart if g.shape[1] <= 8 else xbar_s_chart
        chart = fn(g, tests=tests)
    else:
        g = None
        chart = imr_chart(arr, tests=tests)

    with plt.rc_context({}):
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


# ----------------------------------------------------------------------- run chart
def plot_run_chart(result, *, figsize=None, title: str | None = None):
    """Gráfico de la carta de corridas con la mediana y anotaciones de p-valores.

    Devuelve la figura de matplotlib.
    """

    x = result.values
    n = len(x)
    obs = np.arange(1, n + 1)
    with plt.rc_context({}):
        fig, ax = plt.subplots(figsize=figsize or (max(8, n * 0.35), 4.5))
    ax.plot(obs, x, "o-", ms=4, lw=1, color=BLUE, zorder=3)
    ax.axhline(result.median, color=GREEN, lw=1.3, ls="--", label=f"Mediana={result.median:.4g}")

    # Color above/below
    above = x > result.median
    below = x < result.median
    ax.fill_between(obs, x, result.median, where=above, alpha=0.12, color=BLUE, step=None)
    ax.fill_between(obs, x, result.median, where=below, alpha=0.12, color=ORANGE, step=None)

    ax.annotate(f"Mediana={result.median:.4g}", xy=(1.0, result.median),
                xycoords=("axes fraction", "data"), xytext=(4, 0),
                textcoords="offset points", va="center", fontsize=8, color=GREEN,
                annotation_clip=False)

    alpha = result.alpha
    tests = [
        ("Agrupamiento", result.p_clustering),
        ("Mezclas", result.p_mixtures),
        ("Tendencias", result.p_trends),
        ("Oscilación", result.p_oscillation),
    ]
    lines = [f"p {name}={p:.4f}{'*' if p < alpha else ''}" for name, p in tests]
    ax.text(0.02, 0.97, "\n".join(lines), transform=ax.transAxes, va="top",
            fontsize=7.5, bbox={"fc": "white", "ec": GRAY, "alpha": 0.85})

    ax.set_xlabel("Observación")
    ax.set_ylabel("Valor")
    ax.set_title(title or "Carta de corridas")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------- pre-control
def plot_precontrol(result, *, figsize=None, title: str | None = None):
    """Gráfico de pre-control con zonas verde/amarillo/rojo.

    Devuelve la figura de matplotlib.
    """
    x = result.values
    n = len(x)
    obs = np.arange(1, n + 1)

    ZONE_COLORS = {"G": "#2e8b57", "Y-": "#e08a00", "Y+": "#e08a00", "R-": "#d62728", "R+": "#d62728"}
    with plt.rc_context({}):
        fig, ax = plt.subplots(figsize=figsize or (max(8, n * 0.35), 5))

    # Zones background
    ax.axhspan(result.lsl, result.usl, alpha=0.06, color=GREEN, zorder=0)
    ax.axhspan(result.green_lo, result.green_hi, alpha=0.12, color=GREEN, zorder=0)

    # Spec and zone lines
    for val, col, ls, lbl in (
        (result.usl, RED, "-", f"LES={result.usl:.4g}"),
        (result.lsl, RED, "-", f"LEI={result.lsl:.4g}"),
        (result.green_hi, GREEN, "--", f"Verde hi={result.green_hi:.4g}"),
        (result.green_lo, GREEN, "--", f"Verde lo={result.green_lo:.4g}"),
        (result.center, GREEN, ":", f"Centro={result.center:.4g}"),
    ):
        ax.axhline(val, color=col, lw=1.2, ls=ls)
        ax.annotate(lbl, xy=(1.0, val), xycoords=("axes fraction", "data"),
                    xytext=(4, 0), textcoords="offset points", va="center",
                    fontsize=7.5, color=col, annotation_clip=False)

    # Points colored by zone
    sig_idx = {i for i, _ in result.signals}
    for i, (v, z) in enumerate(zip(x, result.zones)):
        col = ZONE_COLORS.get(z, BLUE)
        marker = "s" if i in sig_idx else "o"
        ax.plot(obs[i], v, marker, ms=6 if i in sig_idx else 4, color=col, zorder=4)
    ax.plot(obs, x, "-", lw=0.8, color=GRAY, zorder=2)

    # Signal annotations
    for i, code in result.signals:
        short = {"red": "R", "two_yellow_same": "YY", "two_yellow_opp": "YY↕"}.get(code, code)
        ax.annotate(short, (obs[i], x[i]), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8, color=RED)

    stats_txt = (f"N={n}  Verde={result.n_green}  "
                 f"Amarillo={result.n_yellow}  Rojo={result.n_red}  "
                 f"Señales={len(result.signals)}")
    ax.text(0.02, 0.97, stats_txt, transform=ax.transAxes, va="top",
            fontsize=8, bbox={"fc": "white", "ec": GRAY, "alpha": 0.85})
    ax.set_xlabel("Observación")
    ax.set_ylabel("Valor")
    ax.set_title(title or "Carta de pre-control")
    ax.grid(alpha=0.2)
    fig.tight_layout(rect=(0, 0, 0.88, 1))
    return fig


# ---------------------------------------------------------------------- tolerance
def plot_tolerance(result, *, figsize=None, title: str | None = None, bins: int = 20):
    """Histograma con el intervalo de tolerancia superpuesto.

    Devuelve la figura de matplotlib.
    """
    x = result.data
    with plt.rc_context({}):
        fig, ax = plt.subplots(figsize=figsize or (8, 4))
    ax.hist(x, bins=bins, color=BLUE, alpha=0.55, edgecolor="white", linewidth=0.5, label="Datos")

    ymax = ax.get_ylim()[1]
    line_kw = {"lw": 1.8, "zorder": 5}
    if result.lower is not None:
        ax.axvline(result.lower, color=RED, ls="--", label=f"LI = {result.lower:.4g}", **line_kw)
        ax.annotate(f"LI={result.lower:.4g}", xy=(result.lower, ymax * 0.92),
                    xytext=(-4, 0), textcoords="offset points",
                    ha="right", fontsize=8, color=RED, annotation_clip=False)
    if result.upper is not None:
        ax.axvline(result.upper, color=RED, ls="--", label=f"LS = {result.upper:.4g}", **line_kw)
        ax.annotate(f"LS={result.upper:.4g}", xy=(result.upper, ymax * 0.92),
                    xytext=(4, 0), textcoords="offset points",
                    ha="left", fontsize=8, color=RED, annotation_clip=False)
    ax.axvline(result.mean, color=GREEN, ls=":", lw=1.2, label=f"Media = {result.mean:.4g}", zorder=4)

    p100 = round(result.coverage * 100, 1)
    g100 = round(result.confidence * 100, 1)
    info = f"N={result.n}  Cobertura≥{p100}%  Confianza={g100}%\nMétodo={result.method}  Lados={result.sides}"
    if result.k_factor is not None:
        info += f"  k={result.k_factor:.4f}"
    if result.achieved_confidence is not None:
        info += f"\nConf. alcanzada={result.achieved_confidence*100:.2f}%"
    ax.text(0.02, 0.97, info, transform=ax.transAxes, va="top",
            fontsize=8, bbox={"fc": "white", "ec": GRAY, "alpha": 0.85})

    ax.set_xlabel("Valor")
    ax.set_ylabel("Frecuencia")
    ax.set_title(title or "Intervalo de tolerancia")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------- acceptance sampling
def plot_sampling_attributes(result, *, figsize=None, title: str | None = None):
    """Curva OC y curva AOQ para un plan de muestreo por atributos.

    Devuelve la figura de matplotlib.
    """
    with plt.rc_context({}):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize or (11, 4.5))

    oc = result.oc_curve()
    p = oc["p_defectivo"].to_numpy()
    pa = oc["P(aceptar)"].to_numpy()

    ax1.plot(p * 100, pa * 100, color=BLUE, lw=2)
    ax1.axhline(95, color=GRAY, ls=":", lw=0.8)
    ax1.axhline(10, color=GRAY, ls=":", lw=0.8)
    ax1.set_xlabel("Fracción defectiva p (%)")
    ax1.set_ylabel("P(aceptar) (%)")
    ax1.set_title("Curva OC")
    ax1.grid(alpha=0.25)

    if hasattr(result, "aql"):
        aql_frac = result.aql if result.aql <= 1.0 else result.aql / 100.0
        ax1.axvline(aql_frac * 100, color=GREEN, ls="--", lw=1.2,
                    label=f"AQL={result.aql:.3g}%")
    if hasattr(result, "ltpd") and not math.isnan(result.ltpd):
        ax1.axvline(result.ltpd * 100, color=RED, ls="--", lw=1.2,
                    label=f"LTPD={result.ltpd*100:.3g}%")
    ax1.legend(fontsize=8)

    aoq_df = result.aoq_curve()
    aoq = aoq_df["AOQ"].to_numpy()
    ax2.plot(p * 100, aoq * 100, color=ORANGE, lw=2)
    if hasattr(result, "aoql") and not math.isnan(result.aoql):
        ax2.axhline(result.aoql * 100, color=RED, ls="--", lw=1.2,
                    label=f"AOQL={result.aoql*100:.3g}%")
        ax2.legend(fontsize=8)
    ax2.set_xlabel("Fracción defectiva p (%)")
    ax2.set_ylabel("AOQ (%)")
    ax2.set_title("Calidad media de salida (AOQ)")
    ax2.grid(alpha=0.25)

    n_txt = result.n
    c_txt = result.c
    info = f"N={result.N}  n={n_txt}  Ac={c_txt}  Re={c_txt + 1}"
    fig.suptitle(title or f"Muestreo de aceptación — {info}", fontsize=10)
    fig.tight_layout()
    return fig


def plot_sampling_variables(result, *, figsize=None, title: str | None = None):
    """Curva OC para un plan de muestreo por variables.

    Devuelve la figura de matplotlib.
    """
    oc = result.oc_curve()
    p = oc["p_defectivo"].to_numpy()
    pa = oc["P(aceptar)"].to_numpy()

    with plt.rc_context({}):
        fig, ax = plt.subplots(figsize=figsize or (7, 4.5))
    ax.plot(p * 100, pa * 100, color=BLUE, lw=2)
    ax.axhline(95, color=GRAY, ls=":", lw=0.8)
    ax.axhline(10, color=GRAY, ls=":", lw=0.8)
    if not math.isnan(result.ltpd):
        ax.axvline(result.ltpd * 100, color=RED, ls="--", lw=1.2,
                   label=f"LTPD={result.ltpd*100:.3g}%")
    aql_frac = result.aql / 100.0
    ax.axvline(aql_frac * 100, color=GREEN, ls="--", lw=1.2,
               label=f"AQL={result.aql:.3g}%")
    ax.legend(fontsize=8)
    ax.set_xlabel("Fracción defectiva p (%)")
    ax.set_ylabel("P(aceptar) (%)")
    ax.set_title(title or f"Curva OC — Plan variables  n={result.n}  k={result.k:.4f}")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────── MSA / Gage R&R ──────────
def plot_gage_rr(result, *, figsize=None, title: str | None = None):
    """Gráficas de componentes de variación del Gage R&R.

    Devuelve la figura de matplotlib.
    """
    data = result._data  # (parts, operators, replicates)
    p, o, _r = data.shape
    part_labels = [f"P{i+1}" for i in range(p)]
    op_labels = [f"Op{j+1}" for j in range(o)]

    with plt.rc_context({}):
        fig, axes = plt.subplots(2, 3, figsize=figsize or (14, 7))
    ax = axes

    # 1. % Contribution bar chart
    srcs = ["Repetibilidad", "Reproducibilidad", "Parte a parte", "Gage R&R"]
    pcts = [result.pct_repeatability, result.pct_reproducibility,
            result.pct_part, result.pct_gage]
    colors = [BLUE, ORANGE, GREEN, RED]
    ax[0, 0].barh(srcs, pcts, color=colors)
    ax[0, 0].axvline(10, color=GRAY, ls=":", lw=1)
    ax[0, 0].axvline(30, color=GRAY, ls=":", lw=1)
    ax[0, 0].set_xlabel("%Contribución")
    ax[0, 0].set_title("%Contribución por fuente")
    for i, v in enumerate(pcts):
        ax[0, 0].text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=8)

    # 2. Medias por parte (R-chart of parts)
    part_means = data.mean(axis=(1, 2))
    ax[0, 1].plot(range(1, p + 1), part_means, "o-", color=BLUE)
    ax[0, 1].set_xticks(range(1, p + 1))
    ax[0, 1].set_xticklabels(part_labels, fontsize=7)
    ax[0, 1].set_xlabel("Parte")
    ax[0, 1].set_ylabel("Media")
    ax[0, 1].set_title("Media por parte")
    ax[0, 1].grid(alpha=0.25)

    # 3. Medias por operador
    op_means = data.mean(axis=(0, 2))
    ax[0, 2].plot(range(1, o + 1), op_means, "s-", color=ORANGE)
    ax[0, 2].set_xticks(range(1, o + 1))
    ax[0, 2].set_xticklabels(op_labels, fontsize=8)
    ax[0, 2].set_xlabel("Operador")
    ax[0, 2].set_ylabel("Media")
    ax[0, 2].set_title("Media por operador")
    ax[0, 2].grid(alpha=0.25)

    # 4. Interacción parte × operador
    for j in range(o):
        op_part_means = data[:, j, :].mean(axis=1)
        ax[1, 0].plot(range(1, p + 1), op_part_means, "o-", label=op_labels[j], lw=1.2)
    ax[1, 0].set_xticks(range(1, p + 1))
    ax[1, 0].set_xticklabels(part_labels, fontsize=7)
    ax[1, 0].set_xlabel("Parte")
    ax[1, 0].set_ylabel("Media")
    ax[1, 0].set_title("Interacción parte×operador")
    ax[1, 0].legend(fontsize=7)
    ax[1, 0].grid(alpha=0.25)

    # 5. Rangos por operador
    ranges = data.max(axis=2) - data.min(axis=2)  # (p, o)
    for j in range(o):
        ax[1, 1].plot(range(1, p + 1), ranges[:, j], "o", ms=4,
                      label=op_labels[j], alpha=0.7)
    Rbar = ranges.mean()
    ax[1, 1].axhline(Rbar, color=BLUE, ls="--", lw=1, label=f"R̄={Rbar:.3g}")
    ax[1, 1].set_xticks(range(1, p + 1))
    ax[1, 1].set_xticklabels(part_labels, fontsize=7)
    ax[1, 1].set_xlabel("Parte")
    ax[1, 1].set_ylabel("Rango")
    ax[1, 1].set_title("Rango por parte/operador")
    ax[1, 1].legend(fontsize=7)
    ax[1, 1].grid(alpha=0.25)

    # 6. Resumen numérico
    ax[1, 2].axis("off")
    summ = (f"Gage R&R ({result.method})\n"
            f"n={result.parts}P × {result.operators}O × {result.replicates}R\n\n"
            f"%GR&R = {result.pct_gage:.1f}%\n"
            f"  Repet. = {result.pct_repeatability:.1f}%\n"
            f"  Repro. = {result.pct_reproducibility:.1f}%\n"
            f"Parte a parte = {result.pct_part:.1f}%\n"
            f"NDC = {result.ndc}\n"
            f"%Var. estudio = {result.pct_study_var:.1f}%")
    ax[1, 2].text(0.1, 0.9, summ, transform=ax[1, 2].transAxes, va="top",
                  fontsize=9, family="monospace",
                  bbox={"fc": "white", "ec": GRAY, "alpha": 0.85})

    fig.suptitle(title or "Análisis Gage R&R", fontsize=11, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_type1(result, *, figsize=None, title: str | None = None):
    """Gráfico de corridas del Estudio Tipo 1 con líneas de referencia.

    Devuelve la figura de matplotlib.
    """
    # We need data — read from the result; since we stored nothing, just plot bias info
    with plt.rc_context({}):
        fig, ax = plt.subplots(figsize=figsize or (8, 4))
    # Plot bias as a horizontal bar / reference diagram
    ax.axhline(0, color=GREEN, lw=1.5, label="Referencia")
    ax.axhline(result.bias, color=RED, lw=2, ls="--",
               label=f"Sesgo = {result.bias:.4g} ({result.bias_pct:.2f}%)")
    sv_half = result.study_variation / 2
    ax.axhspan(-sv_half, sv_half, alpha=0.10, color=BLUE, label="±Var. estudio/2")
    ax.set_xlim(-0.5, 0.5)
    ax.set_xlabel("")
    ax.set_ylabel("Sesgo")
    cg_s = f"Cg={result.cg:.3f}  " if not math.isnan(result.cg) else ""
    cgk_s = f"Cgk={result.cgk:.3f}" if not math.isnan(result.cgk) else ""
    ax.set_title(title or (f"Estudio Tipo 1  N={result.n}  "
                            f"Ref={result.reference}  {cg_s}{cgk_s}"))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig


def plot_linearity(result, *, figsize=None, title: str | None = None):
    """Sesgo vs referencia con la línea de regresión.

    Devuelve la figura de matplotlib.
    """
    with plt.rc_context({}):
        fig, ax = plt.subplots(figsize=figsize or (8, 4.5))
    ax.scatter(result._all_refs, result._all_biases, color=BLUE, s=25, alpha=0.7, zorder=4)
    # Reference level means
    ax.plot(result.references, result.biases, "s", color=ORANGE, ms=7, zorder=5,
            label="Sesgo medio")
    # Regression line
    x_line = np.linspace(result._all_refs.min(), result._all_refs.max(), 100)
    y_line = result.intercept + result.slope * x_line
    ax.plot(x_line, y_line, color=RED, lw=2, label=(
        f"Regresión: sesgo={result.intercept:.4g}+{result.slope:.4g}·ref\n"
        f"  R²={result.r_squared:.4f}  p={result.p_slope:.4f}"))
    ax.axhline(0, color=GRAY, ls=":", lw=1)
    ax.axhline(result.avg_bias, color=GREEN, ls="--", lw=1.2,
               label=f"Sesgo prom.={result.avg_bias:.4g} ({result.avg_bias_pct:.2f}%)")
    ax.set_xlabel("Valor de referencia")
    ax.set_ylabel("Sesgo (medición − referencia)")
    ax.set_title(title or "Linealidad y sesgo del sistema de medición")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig


def plot_attribute_agreement(result, *, figsize=None, title: str | None = None):
    """Kappa por operador (vs referencia y dentro).

    Devuelve la figura de matplotlib.
    """
    ops = list(result.kappa_within.index)
    x = np.arange(len(ops))

    with plt.rc_context({}):
        fig, axes = plt.subplots(1, 2, figsize=figsize or (10, 4))

    # Kappa vs reference
    if not result.kappa_vs_reference.empty:
        kappas_ref = result.kappa_vs_reference["kappa"].to_numpy(dtype=float)
        axes[0].bar(x, kappas_ref, color=BLUE, alpha=0.7)
        axes[0].axhline(0.75, color=GREEN, ls="--", lw=1.2, label="κ=0.75 (bueno)")
        axes[0].axhline(0.40, color=RED, ls="--", lw=1.2, label="κ=0.40 (aceptable)")
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(ops, fontsize=8)
        axes[0].set_ylim(0, 1.05)
        axes[0].set_ylabel("Kappa")
        axes[0].set_title("Kappa vs referencia")
        axes[0].legend(fontsize=8)
        axes[0].grid(axis="y", alpha=0.25)

    # Kappa within
    kappas_in = result.kappa_within["kappa"].to_numpy(dtype=float)
    axes[1].bar(x, kappas_in, color=ORANGE, alpha=0.7)
    axes[1].axhline(0.75, color=GREEN, ls="--", lw=1.2, label="κ=0.75")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(ops, fontsize=8)
    axes[1].set_ylim(0, 1.05)
    axes[1].set_ylabel("Kappa")
    axes[1].set_title("Kappa dentro del operador")
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)

    fig.suptitle(title or (f"Concordancia por atributos — "
                            f"κ global={result.kappa_overall:.4f}  "
                            f"Fleiss κ={result.fleiss_kappa:.4f}"), fontsize=10)
    fig.tight_layout()
    return fig
