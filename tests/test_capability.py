import math

import numpy as np
import pytest
from scipy import stats

import pccpy

RNG = np.random.default_rng(7)
X = RNG.normal(100.4, 1.5, 150)
LSL, USL, T = 95.0, 105.0, 100.0


def test_individuals_match_hand_calculation():
    r = pccpy.capability_analysis(X, LSL, USL, T)
    mrbar = np.mean(np.abs(np.diff(X)))
    sw, so, m = mrbar / 1.128379167, X.std(ddof=1), X.mean()
    assert r.sigma_within == pytest.approx(sw) and r.sigma_overall == pytest.approx(so)
    assert r.cp == pytest.approx((USL - LSL) / (6 * sw))
    assert r.cpk == pytest.approx(min(m - LSL, USL - m) / (3 * sw))
    assert r.pp == pytest.approx((USL - LSL) / (6 * so))
    assert r.ppk == pytest.approx(min(m - LSL, USL - m) / (3 * so))
    assert r.cpl == pytest.approx((m - LSL) / (3 * sw)) and r.cpu == pytest.approx((USL - m) / (3 * sw))
    assert r.cpm == pytest.approx((USL - LSL) / (6 * math.sqrt(so**2 + (m - T) ** 2)))
    assert r.within_method == "mr"


def test_within_and_overall_are_different_estimates(rng):
    """Regresión: el proyecto previo usaba la misma sigma para Cp/Cpk y Pp/Ppk."""
    drifting = np.arange(60) * 0.05 + rng.normal(0, 0.2, 60)  # deriva: overall >> within
    r = pccpy.capability_analysis(drifting, -3, 6)
    assert r.sigma_overall > 1.5 * r.sigma_within
    assert r.cpk > r.ppk and r.cp > r.pp


def test_expected_ppm_and_zbench_consistency():
    r = pccpy.capability_analysis(X, LSL, USL)
    m, so = X.mean(), X.std(ddof=1)
    lo = 1e6 * stats.norm.cdf((LSL - m) / so)
    hi = 1e6 * stats.norm.sf((USL - m) / so)
    assert r.ppm_overall == pytest.approx((lo, hi, lo + hi))
    assert r.z_bench_overall == pytest.approx(stats.norm.isf((lo + hi) / 1e6))
    assert r.z_lsl_overall == pytest.approx((m - LSL) / so)
    assert r.ppm_obs == (0.0, 0.0, 0.0)


def test_observed_ppm_counts_out_of_spec(rng):
    x = np.r_[np.full(97, 100.0) + rng.normal(0, 0.1, 97), 90.0, 110.0, 111.0]
    r = pccpy.capability_analysis(x, LSL, USL)
    assert r.ppm_obs == pytest.approx((1e4, 2e4, 3e4))


def test_confidence_intervals_bracket_estimates():
    r = pccpy.capability_analysis(X, LSL, USL, ci_level=0.95)
    assert r.pp_ci[0] < r.pp < r.pp_ci[1]
    assert r.ppk_ci[0] < r.ppk < r.ppk_ci[1]
    wide = pccpy.capability_analysis(X, LSL, USL, ci_level=0.99)
    assert wide.ppk_ci[1] - wide.ppk_ci[0] > r.ppk_ci[1] - r.ppk_ci[0]
    n = len(X)
    half = 1.959964 * math.sqrt(1 / (9 * n) + r.ppk**2 / (2 * (n - 1)))
    assert r.ppk_ci[1] - r.ppk == pytest.approx(half, rel=1e-5)


def test_one_sided_specs():
    up = pccpy.capability_analysis(X, usl=USL)
    assert math.isnan(up.cp) and math.isnan(up.cpl) and up.cpk == pytest.approx(up.cpu)
    assert math.isnan(up.ppm_obs[0]) and not math.isnan(up.ppm_obs[2])
    lo = pccpy.capability_analysis(X, lsl=LSL)
    assert lo.cpk == pytest.approx(lo.cpl)
    assert "*" in up.summary()


def test_subgroup_data_uses_pooled_by_default_and_rbar_option(rng):
    g = rng.normal(100, 1.5, (30, 5))
    r = pccpy.capability_analysis(g, LSL, USL)
    sp = math.sqrt(np.mean(g.var(axis=1, ddof=1)))
    assert r.within_method == "pooled"
    assert r.sigma_within == pytest.approx(sp / pccpy.c4(121))  # c4(sum(n_i - 1) + 1)
    rb = pccpy.capability_analysis(g, LSL, USL, within_method="rbar")
    assert rb.sigma_within == pytest.approx(np.mean(g.max(1) - g.min(1)) / pccpy.d2(5))
    same = pccpy.capability_analysis(g.ravel(), LSL, USL, subgroup_size=5)
    assert same.sigma_within == pytest.approx(r.sigma_within)
    assert r.n == 150


def test_user_supplied_sigma_within():
    r = pccpy.capability_analysis(X, LSL, USL, sigma_within=2.0)
    assert r.cp == pytest.approx(10 / 12) and r.within_method == "especificada"


def test_input_validation():
    with pytest.raises(ValueError):
        pccpy.capability_analysis(X)
    with pytest.raises(ValueError):
        pccpy.capability_analysis(X, 105, 95)
    with pytest.raises(ValueError):
        pccpy.capability_analysis(np.full(10, 3.0), 0, 6)
    with pytest.raises(ValueError):
        pccpy.capability_analysis(X, LSL, USL, within_method="rbar")  # inválido para individuales
    with pytest.raises(ValueError):
        pccpy.capability_analysis(X, LSL, USL, ci_level=1.5)


def test_summary_and_frame():
    r = pccpy.capability_analysis(X, LSL, USL, T)
    s = r.summary()
    assert "Cpk=" in s and "Ppk=" in s and "PPM" in s
    df = r.to_frame()
    assert df.loc["Cpk", "valor"] == pytest.approx(r.cpk)


# ---------------------------------------------------------------- no normal / Box-Cox
def test_nonnormal_percentile_method_on_weibull():
    shape, scale = 1.8, 3.0
    w = stats.weibull_min.rvs(shape, scale=scale, size=4000, random_state=11)
    r = pccpy.capability_nonnormal(w, lsl=0.05, usl=12, distribution="weibull")
    true = stats.weibull_min(shape, scale=scale)
    assert r.x_median == pytest.approx(true.ppf(0.5), rel=0.03)
    assert r.x_high == pytest.approx(true.ppf(stats.norm.cdf(3)), rel=0.05)
    assert r.pp == pytest.approx((12 - 0.05) / (r.x_high - r.x_low))
    assert r.ppu == pytest.approx((12 - r.x_median) / (r.x_high - r.x_median))
    assert r.ppk == pytest.approx(min(r.ppl, r.ppu))
    assert r.ppm_expected[1] == pytest.approx(1e6 * true.sf(12), abs=200)
    assert "weibull" in r.summary()


def test_nonnormal_normal_dist_agrees_with_normal_pp(rng):
    x = rng.normal(50, 2, 3000)
    nn = pccpy.capability_nonnormal(x, 42, 58, distribution="normal")
    nm = pccpy.capability_analysis(x, 42, 58)
    assert nn.pp == pytest.approx(nm.pp, rel=1e-3)
    assert nn.ppk == pytest.approx(nm.ppk, rel=1e-3)


def test_nonnormal_validation():
    with pytest.raises(ValueError):
        pccpy.capability_nonnormal([1, 2, -3, 4], 0, 5, distribution="weibull")
    with pytest.raises(ValueError):
        pccpy.capability_nonnormal(X, LSL, USL, distribution="cauchy")


@pytest.mark.parametrize("dist", ["lognormal", "gamma", "exponential", "loglogistic",
                                  "logistic", "largest_extreme", "smallest_extreme"])
def test_all_distributions_fit(dist, rng):
    r = pccpy.capability_nonnormal(rng.gamma(4, 2, 300) + 0.5, 0.2, 40, distribution=dist)
    assert math.isfinite(r.ppk) and math.isfinite(r.aic)


def test_boxcox_recovers_lognormal(rng):
    x = np.exp(rng.normal(1.0, 0.4, 2000))  # lambda óptimo ~ 0
    r = pccpy.capability_boxcox(x, lsl=0.5, usl=9)
    assert abs(r.transform["lambda"]) < 0.15
    assert r.lsl == 0.5 and r.usl == 9  # se reportan en unidades originales
    assert r.ppm_obs[2] == pytest.approx(1e6 * np.mean((x < 0.5) | (x > 9)))
    fixed = pccpy.capability_boxcox(x, 0.5, 9, lam=0.0)
    assert fixed.transform["lambda"] == 0.0
    # lambda = 0 equivale a analizar log(x) con log(specs)
    ref = pccpy.capability_analysis(np.log(x), math.log(0.5), math.log(9))
    assert fixed.ppk == pytest.approx(ref.ppk)
    assert "Box-Cox" in r.summary()


def test_boxcox_rejects_nonpositive():
    with pytest.raises(ValueError):
        pccpy.capability_boxcox([1, 2, 0, 3], 0.5, 5)
    with pytest.raises(ValueError):
        pccpy.capability_boxcox(X, lsl=-1, usl=200)
