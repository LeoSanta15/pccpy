import matplotlib.pyplot as plt
import numpy as np
import pytest

import spyc

RNG = np.random.default_rng(5)
X = RNG.normal(100, 2, 80)
G = RNG.normal(100, 2, (25, 4))
D = RNG.binomial(100, 0.05, 30)


@pytest.mark.parametrize("make", [
    lambda: spyc.imr_chart(X, tests="all"),
    lambda: spyc.imr_chart(X, stages=np.r_[np.ones(40), np.full(40, 2)], tests="all"),
    lambda: spyc.xbar_r_chart(G, tests="all"),
    lambda: spyc.xbar_s_chart(G, tests="all"),
    lambda: spyc.p_chart(D, RNG.integers(80, 120, 30), tests=[1, 2, 3, 4]),
    lambda: spyc.np_chart(D, 100),
    lambda: spyc.c_chart(D),
    lambda: spyc.u_chart(D, 100),
    lambda: spyc.laney_p_chart(D, 100),
    lambda: spyc.ewma_chart(X),
    lambda: spyc.cusum_chart(np.r_[X[:40], X[40:] + 4]),
])
def test_every_chart_plots(make):
    fig = make().plot(zones=True)
    assert isinstance(fig, plt.Figure) and len(fig.axes) >= 1


def test_capability_and_normality_plots():
    r = spyc.capability_analysis(X, 94, 106, 100)
    assert isinstance(r.plot(), plt.Figure)
    assert isinstance(spyc.capability_nonnormal(np.exp(X / 50), 2, 9).plot(), plt.Figure)
    assert isinstance(spyc.capability_boxcox(X, 94, 106).plot(), plt.Figure)
    assert isinstance(spyc.probability_plot(X), plt.Figure)
    assert isinstance(spyc.plot_pareto(spyc.pareto(["a", "b", "a"])), plt.Figure)


def test_sixpack_individuals_and_subgroups():
    fig, res, chart = spyc.capability_sixpack(X, 94, 106, 100)
    assert chart.kind == "I-MR" and len(fig.axes) >= 6
    fig2, res2, chart2 = spyc.capability_sixpack(G, 94, 106, 100)
    assert chart2.kind == "Xbar-R"
    _, _, chart3 = spyc.capability_sixpack(RNG.normal(100, 2, (20, 10)), 94, 106)
    assert chart3.kind == "Xbar-S"  # subgrupos de 9 o más usan S
