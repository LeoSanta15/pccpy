import os
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import pccpy

RNG = np.random.default_rng(5)
X = RNG.normal(100, 2, 80)
G = RNG.normal(100, 2, (25, 4))
G_wide = RNG.normal(100, 2, (20, 10))
D = RNG.binomial(100, 0.05, 30)
MV = RNG.normal(0, 1, (40, 3))


# ── Control charts ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("make", [
    lambda: pccpy.imr_chart(X, tests="all"),
    lambda: pccpy.imr_chart(X, stages=np.r_[np.ones(40), np.full(40, 2)], tests="all"),
    lambda: pccpy.xbar_r_chart(G, tests="all"),
    lambda: pccpy.xbar_s_chart(G, tests="all"),
    lambda: pccpy.p_chart(D, RNG.integers(80, 120, 30), tests=[1, 2, 3, 4]),
    lambda: pccpy.np_chart(D, 100),
    lambda: pccpy.c_chart(D),
    lambda: pccpy.u_chart(D, 100),
    lambda: pccpy.laney_p_chart(D, 100),
    lambda: pccpy.ewma_chart(X),
    lambda: pccpy.cusum_chart(np.r_[X[:40], X[40:] + 4]),
])
def test_every_chart_plots(make):
    fig = make().plot(zones=True)
    assert isinstance(fig, plt.Figure) and len(fig.axes) >= 1


@pytest.mark.parametrize("make", [
    lambda: pccpy.imr_rs_chart(G),
    lambda: pccpy.zone_chart(X),
    lambda: pccpy.ma_chart(X),
])
def test_advanced_charts_plot(make):
    fig = make().plot()
    assert isinstance(fig, plt.Figure) and len(fig.axes) >= 1


@pytest.mark.parametrize("make", [
    lambda: pccpy.t2_chart(MV),
    lambda: pccpy.mewma_chart(MV),
])
def test_multivariate_charts_plot(make):
    fig = make().plot()
    assert isinstance(fig, plt.Figure) and len(fig.axes) >= 1


def test_run_chart_plot():
    fig = pccpy.run_chart(X).plot()
    assert isinstance(fig, plt.Figure)


# ── Capability ───────────────────────────────────────────────────────────────

def test_capability_and_normality_plots():
    r = pccpy.capability_analysis(X, 94, 106, 100)
    assert isinstance(r.plot(), plt.Figure)
    assert isinstance(pccpy.capability_nonnormal(np.exp(X / 50), 2, 9).plot(), plt.Figure)
    assert isinstance(pccpy.capability_boxcox(X, 94, 106).plot(), plt.Figure)
    assert isinstance(pccpy.probability_plot(X), plt.Figure)
    assert isinstance(pccpy.plot_pareto(pccpy.pareto(["a", "b", "a"])), plt.Figure)


def test_sixpack_individuals_and_subgroups():
    fig, res, chart = pccpy.capability_sixpack(X, 94, 106, 100)
    assert chart.kind == "I-MR" and len(fig.axes) >= 6
    fig2, res2, chart2 = pccpy.capability_sixpack(G, 94, 106, 100)
    assert chart2.kind == "Xbar-R"
    _, _, chart3 = pccpy.capability_sixpack(G_wide, 94, 106)
    assert chart3.kind == "Xbar-S"


# ── Tolerance ────────────────────────────────────────────────────────────────

def test_tolerance_plot():
    res = pccpy.tolerance_interval(X, coverage=0.95, confidence=0.95)
    fig = res.plot()
    assert isinstance(fig, plt.Figure)


# ── Acceptance sampling ──────────────────────────────────────────────────────

def test_acceptance_attributes_plot():
    plan = pccpy.acceptance_sampling_attributes(1000, 1.5)
    fig = plan.plot()
    assert isinstance(fig, plt.Figure)


def test_acceptance_variables_plot():
    plan = pccpy.acceptance_sampling_variables(1000, 1.5)
    fig = plan.plot()
    assert isinstance(fig, plt.Figure)


def test_dodge_romig_plot():
    plan = pccpy.dodge_romig(1000, ltpd=0.05)
    fig = plan.plot()
    assert isinstance(fig, plt.Figure)


# ── MSA ──────────────────────────────────────────────────────────────────────

def test_gage_rr_plot():
    data3d = RNG.normal(0, 1, (10, 3, 2))
    res = pccpy.gage_rr(data3d, parts=10, operators=3, replicates=2)
    fig = res.plot()
    assert isinstance(fig, plt.Figure)


def test_gage_type1_plot():
    res = pccpy.gage_type1(RNG.normal(10, 0.1, 25), reference=10.0)
    fig = res.plot()
    assert isinstance(fig, plt.Figure)


def test_gage_linearity_plot():
    refs = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    meas = refs[:, None] + RNG.normal(0, 0.1, (5, 5))
    res = pccpy.gage_linearity(meas.ravel(), np.repeat(refs, 5))
    fig = res.plot()
    assert isinstance(fig, plt.Figure)


def test_attribute_agreement_plot():
    parts = ["p1"] * 4 + ["p2"] * 4 + ["p3"] * 4
    ops = ["A", "A", "B", "B"] * 3
    ratings = RNG.choice(["Good", "Bad"], 12)
    df = pd.DataFrame({"part": parts, "operator": ops, "rating": ratings})
    res = pccpy.attribute_agreement(df)
    fig = res.plot()
    assert isinstance(fig, plt.Figure)


# ── Pre-control & diagnose ───────────────────────────────────────────────────

def test_precontrol_plot():
    fig = pccpy.precontrol(X, 94, 106).plot()
    assert isinstance(fig, plt.Figure)


def test_diagnose_plot():
    fig = pccpy.diagnose(X, lsl=94, usl=106).plot()
    assert isinstance(fig, plt.Figure)


# ── to_excel smoke tests ─────────────────────────────────────────────────────

def _xl(obj):
    pytest.importorskip("openpyxl")
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        obj.to_excel(path)
        return os.path.getsize(path)
    finally:
        os.unlink(path)


def test_to_excel_control_chart():
    assert _xl(pccpy.imr_chart(X)) > 0


def test_to_excel_capability():
    assert _xl(pccpy.capability_analysis(X, 94, 106)) > 0


def test_to_excel_capability_nonnormal():
    assert _xl(pccpy.capability_nonnormal(np.exp(X / 50), 2, 9)) > 0


def test_to_excel_tolerance():
    assert _xl(pccpy.tolerance_interval(X)) > 0


def test_to_excel_diagnose():
    assert _xl(pccpy.diagnose(X, lsl=94, usl=106)) > 0


def test_to_excel_acceptance_attributes():
    assert _xl(pccpy.acceptance_sampling_attributes(1000, 1.5)) > 0


def test_to_excel_acceptance_variables():
    assert _xl(pccpy.acceptance_sampling_variables(1000, 1.5)) > 0


def test_to_excel_dodge_romig():
    assert _xl(pccpy.dodge_romig(1000, ltpd=0.05)) > 0


def test_to_excel_gage_rr():
    data3d = RNG.normal(0, 1, (10, 3, 2))
    assert _xl(pccpy.gage_rr(data3d, parts=10, operators=3, replicates=2)) > 0


def test_to_excel_gage_type1():
    assert _xl(pccpy.gage_type1(RNG.normal(10, 0.1, 25), reference=10.0)) > 0


def test_to_excel_gage_linearity():
    refs = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    meas = refs[:, None] + RNG.normal(0, 0.1, (5, 5))
    assert _xl(pccpy.gage_linearity(meas.ravel(), np.repeat(refs, 5))) > 0


def test_to_excel_attribute_agreement():
    parts = ["p1"] * 4 + ["p2"] * 4 + ["p3"] * 4
    ops = ["A", "A", "B", "B"] * 3
    ratings = RNG.choice(["Good", "Bad"], 12)
    df = pd.DataFrame({"part": parts, "operator": ops, "rating": ratings})
    assert _xl(pccpy.attribute_agreement(df)) > 0


# ── save_plot smoke tests ─────────────────────────────────────────────────────

def _sp(obj, fmt="png", **kwargs):
    with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as f:
        path = f.name
    try:
        obj.save_plot(path, **kwargs)
        return os.path.getsize(path)
    finally:
        os.unlink(path)


def test_save_plot_control_chart_png():
    assert _sp(pccpy.imr_chart(X)) > 0


def test_save_plot_control_chart_pdf():
    assert _sp(pccpy.imr_chart(X), fmt="pdf") > 0


def test_save_plot_capability():
    assert _sp(pccpy.capability_analysis(X, 94, 106)) > 0


def test_save_plot_tolerance():
    assert _sp(pccpy.tolerance_interval(X)) > 0


def test_save_plot_diagnose():
    assert _sp(pccpy.diagnose(X, lsl=94, usl=106)) > 0


def test_save_plot_precontrol():
    assert _sp(pccpy.precontrol(X, 94, 106)) > 0


def test_save_plot_run_chart():
    assert _sp(pccpy.run_chart(X)) > 0


def test_save_plot_acceptance():
    assert _sp(pccpy.acceptance_sampling_attributes(1000, 1.5)) > 0


def test_save_plot_gage_rr():
    data3d = RNG.normal(0, 1, (10, 3, 2))
    assert _sp(pccpy.gage_rr(data3d, parts=10, operators=3, replicates=2)) > 0


def test_save_plot_multivariate():
    assert _sp(pccpy.t2_chart(MV)) > 0
