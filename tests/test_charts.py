import numpy as np
import pytest

import pccpy
from pccpy import control_chart_constants as cc

RNG = np.random.default_rng(2024)
X = RNG.normal(50, 2, 60)
G = RNG.normal(10, 0.5, (25, 5))


# ---------------------------------------------------------------- I-MR
def test_imr_matches_hand_formulas():
    ch = pccpy.imr_chart(X)
    mrbar = np.mean(np.abs(np.diff(X)))
    sigma = mrbar / 1.128379167  # d2(2) exacto
    I, MR = ch["I"], ch["MR"]
    assert I.center[0] == pytest.approx(X.mean())
    assert I.ucl[0] == pytest.approx(X.mean() + 3 * sigma)
    assert I.lcl[0] == pytest.approx(X.mean() - 3 * sigma)
    assert MR.center[1] == pytest.approx(mrbar)
    assert MR.ucl[1] == pytest.approx(3.26653 * mrbar, rel=1e-4)  # D4(2)
    assert MR.lcl[1] == 0.0
    assert np.isnan(MR.values[0]) and MR.values[1] == pytest.approx(abs(X[1] - X[0]))


def test_imr_alternative_sigma_methods():
    mr = np.abs(np.diff(X))
    med = pccpy.imr_chart(X, sigma_method="median_mr").params[0]["sigma"]
    assert med == pytest.approx(np.median(mr) / 0.954)
    mssd = pccpy.imr_chart(X, sigma_method="mssd").params[0]["sigma"]
    assert mssd == pytest.approx(np.sqrt(np.sum(np.diff(X) ** 2) / (2 * (len(X) - 1))))
    with pytest.raises(ValueError):
        pccpy.imr_chart(X, sigma_method="nope")
    with pytest.raises(ValueError):
        pccpy.imr_chart(X, sigma_method="median_mr", span=3)


def test_imr_span_3():
    ch = pccpy.imr_chart(X, span=3)
    w = np.lib.stride_tricks.sliding_window_view(X, 3)
    rng3 = w.max(1) - w.min(1)
    assert ch.params[0]["sigma"] == pytest.approx(rng3.mean() / cc(3)["d2"])
    assert np.isnan(ch["MR"].values[:2]).all()


def test_imr_historical_parameters():
    ch = pccpy.imr_chart(X, mu=50, sigma=2)
    assert ch["I"].ucl[0] == 56 and ch["I"].lcl[0] == 44
    assert ch["MR"].center[0] == pytest.approx(2 * 1.128379, rel=1e-5)


def test_imr_detects_point_beyond_limits():
    y = X.copy()
    y[30] += 15
    ch = pccpy.imr_chart(y, tests=[1])
    assert 30 in ch["I"].violations[1]
    assert not ch.in_control
    v = ch.violations()
    assert {"panel", "punto", "prueba", "valor", "descripcion"} <= set(v.columns)
    assert ((v["panel"] == "I") & (v["punto"] == 31)).any()  # punto en base 1


def test_default_is_test1_only_like_minitab(rng):
    ch = pccpy.imr_chart(np.full(30, 5.0) + np.arange(30) * 0.0 + rng.normal(0, 1e-9, 30))
    assert ch.tests == (1,)


def test_stages_use_separate_limits_and_offset_indices(rng):
    a = rng.normal(10, 1, 30)
    b = rng.normal(20, 1, 30)
    b[10] += 12  # atípico en la etapa 2
    x = np.r_[a, b]
    ch = pccpy.imr_chart(x, stages=np.r_[np.ones(30), 2 * np.ones(30)], tests=[1])
    I = ch["I"]
    assert I.center[0] == pytest.approx(a.mean()) and I.center[-1] == pytest.approx(b.mean())
    assert len(ch.params) == 2
    assert 40 in I.violations[1]  # 30 + 10, índice global
    # sin etapas, el salto entre medias infla sigma; con etapas no
    assert ch.params[0]["sigma"] < pccpy.imr_chart(x).params[0]["sigma"]


def test_non_contiguous_stages_rejected():
    with pytest.raises(ValueError, match="contigua"):
        pccpy.imr_chart(np.arange(6.0), stages=[1, 1, 2, 2, 1, 1])
    with pytest.raises(ValueError):
        pccpy.imr_chart(np.arange(6.0), stages=[1, 2])


def test_missing_values_rejected():
    with pytest.raises(ValueError):
        pccpy.imr_chart([1.0, np.nan, 3.0])


# ---------------------------------------------------------------- Xbar-R / Xbar-S
def test_xbar_r_matches_a2_d4():
    ch = pccpy.xbar_r_chart(G)
    c = cc(5)
    rbar = np.mean(G.max(1) - G.min(1))
    grand = G.mean()
    xb, r = ch["Xbar"], ch["R"]
    assert xb.center[0] == pytest.approx(grand)
    assert xb.ucl[0] == pytest.approx(grand + c["A2"] * rbar)
    assert xb.lcl[0] == pytest.approx(grand - c["A2"] * rbar)
    assert r.center[0] == pytest.approx(rbar)
    assert r.ucl[0] == pytest.approx(c["D4"] * rbar)
    assert r.lcl[0] == pytest.approx(c["D3"] * rbar)
    assert ch.params[0]["tamaño"] == 5


def test_xbar_s_matches_a3_b3_b4():
    ch = pccpy.xbar_s_chart(G)
    c = cc(5)
    sbar = np.mean(G.std(axis=1, ddof=1))
    assert ch["Xbar"].ucl[0] == pytest.approx(G.mean() + c["A3"] * sbar)
    assert ch["S"].center[0] == pytest.approx(sbar)
    assert ch["S"].ucl[0] == pytest.approx(c["B4"] * sbar)
    assert ch["S"].lcl[0] == pytest.approx(c["B3"] * sbar)


def test_pooled_sigma():
    ch = pccpy.xbar_s_chart(G, sigma_method="pooled")
    sp = np.sqrt(np.mean(G.var(axis=1, ddof=1)))  # subgrupos iguales
    assert ch.params[0]["sigma"] == pytest.approx(sp / cc(101)["c4"])  # c4(sum(n_i-1)+1) = c4(25*4+1)


def test_subgroup_input_formats_are_equivalent():
    a = pccpy.xbar_r_chart(G)
    b = pccpy.xbar_r_chart(G.ravel(), subgroup_size=5)
    c = pccpy.xbar_r_chart(G.ravel(), subgroup=np.repeat(np.arange(25), 5))
    for other in (b, c):
        assert np.allclose(a["Xbar"].ucl, other["Xbar"].ucl)
        assert np.allclose(a["R"].values, other["R"].values)


def test_unequal_subgroup_sizes_scale_limits_by_sqrt_n(rng):
    vals = rng.normal(0, 1, 24)
    ids = np.repeat(np.arange(6), [2, 6, 4, 4, 4, 4])
    ch = pccpy.xbar_r_chart(vals, subgroup=ids)
    xb = ch["Xbar"]
    half = xb.ucl - xb.center
    sizes = np.array([2, 6, 4, 4, 4, 4])
    assert np.allclose(half * np.sqrt(sizes), half[0] * np.sqrt(2))
    assert ch.params[0]["tamaño"] == "variable"


def test_subgroup_of_one_gives_nan_dispersion_but_valid_xbar(rng):
    vals = rng.normal(0, 1, 9)
    ids = [0, 0, 1, 1, 2, 3, 3, 4, 4]  # el subgrupo 2 tiene una sola observación
    ch = pccpy.xbar_r_chart(vals, subgroup=ids)
    assert np.isnan(ch["R"].values[2]) and np.isfinite(ch["Xbar"].values[2])


def test_wrong_method_for_chart():
    with pytest.raises(ValueError):
        pccpy.xbar_r_chart(G, sigma_method="sbar")
    with pytest.raises(ValueError):
        pccpy.xbar_s_chart(G, sigma_method="rbar")


def test_tests_1_to_8_apply_to_xbar_but_only_1_to_4_to_range():
    ch = pccpy.xbar_r_chart(G, tests="all")
    assert set(ch["Xbar"].violations) == set(range(1, 9))
    assert set(ch["R"].violations) == {1, 2, 3, 4}


# ---------------------------------------------------------------- atributos
D = RNG.binomial(100, 0.05, 30)
NV = RNG.integers(80, 121, 30)


def test_p_chart_constant_and_variable_n(rng):
    ch = pccpy.p_chart(D, 100)
    pbar = D.sum() / 3000
    p = ch["P"]
    assert p.center[0] == pytest.approx(pbar)
    assert p.ucl[0] == pytest.approx(pbar + 3 * np.sqrt(pbar * (1 - pbar) / 100))
    dv = rng.binomial(NV, 0.05)
    pv = pccpy.p_chart(dv, NV)["P"]
    assert pv.center[0] == pytest.approx(dv.sum() / NV.sum())
    assert not np.allclose(pv.ucl, pv.ucl[0])  # límites variables
    assert np.all(pv.lcl >= 0)


def test_np_c_u_charts():
    n = pccpy.np_chart(D, 100)["NP"]
    pbar = D.sum() / 3000
    assert n.center[0] == pytest.approx(100 * pbar)
    assert n.ucl[0] == pytest.approx(100 * pbar + 3 * np.sqrt(100 * pbar * (1 - pbar)))
    c = pccpy.c_chart(D)["C"]
    assert c.center[0] == pytest.approx(D.mean())
    assert c.ucl[0] == pytest.approx(D.mean() + 3 * np.sqrt(D.mean()))
    u = pccpy.u_chart(D, NV)["U"]
    ubar = D.sum() / NV.sum()
    assert u.center[0] == pytest.approx(ubar)
    assert u.ucl[3] == pytest.approx(ubar + 3 * np.sqrt(ubar / NV[3]))
    assert np.allclose(u.values, D / NV)


def test_attribute_validation():
    with pytest.raises(ValueError):
        pccpy.np_chart(D, NV)  # n variable
    with pytest.raises(ValueError):
        pccpy.p_chart([5, 200], 100)  # defectuosos > n
    with pytest.raises(ValueError):
        pccpy.c_chart([1, -1, 2])


def test_p_chart_flags_outlier():
    d = D.copy()
    d[7] = 30
    assert 7 in pccpy.p_chart(d, 100, tests=[1])["P"].violations[1]


def test_laney_p_prime_widens_limits_when_overdispersed(rng):
    n = np.full(30, 1000)
    p = np.clip(rng.normal(0.1, 0.02, 30), 0.01, 0.5)  # variación extra-binomial
    d = np.round(p * n)
    lp = pccpy.laney_p_chart(d, n)
    sz = lp.params[0]["sigma_z"]
    pbar = d.sum() / n.sum()
    z = (d / n - pbar) / np.sqrt(pbar * (1 - pbar) / n)
    assert sz == pytest.approx(np.mean(np.abs(np.diff(z))) / 1.128379, rel=1e-5)
    assert sz > 1
    std = pccpy.p_chart(d, n)["P"]
    assert lp["P"].ucl[0] - lp["P"].center[0] == pytest.approx(sz * (std.ucl[0] - std.center[0]))
    assert pccpy.laney_u_chart(D, NV).params[0]["sigma_z"] > 0


# ---------------------------------------------------------------- EWMA / CUSUM
def test_ewma_recursion_and_exact_limits(rng):
    lam, s = 0.2, 2.0
    x = rng.normal(10, 2, 15)
    ch = pccpy.ewma_chart(x, weight=lam, target=10, sigma=s)
    z = ch["EWMA"]
    expect, prev = [], 10.0
    for v in x:
        prev = lam * v + (1 - lam) * prev
        expect.append(prev)
    assert np.allclose(z.values, expect)
    assert z.ucl[0] == pytest.approx(10 + 3 * s * lam)  # primer límite = target + K*sigma*lambda
    asym = 10 + 3 * s * np.sqrt(lam / (2 - lam))
    assert z.ucl[-1] == pytest.approx(asym, rel=1e-3)


def test_ewma_detects_small_shift():
    noise = np.tile([0.5, -0.5], 30)  # ruido determinista, sin falsas alarmas
    x = np.r_[noise[:30], noise[30:] + 1.5]  # desplazamiento de +1.5 sigma desde el punto 31
    ch = pccpy.ewma_chart(x, target=0, sigma=1)
    flagged = ch["EWMA"].violations[1]
    assert flagged.size > 0 and flagged.min() >= 30  # ninguna alarma antes del cambio


def test_cusum_hand_calculation():
    x = np.full(12, 11.0)  # desplazamiento sostenido de +1 sigma
    ch = pccpy.cusum_chart(x, target=10, sigma=1, h=4, k=0.5)
    c = ch["CUSUM"]
    assert np.allclose(c.values, 0.5 * np.arange(1, 13))  # sube 0.5 por punto
    assert np.allclose(c.secondary, 0)
    assert c.ucl[0] == 4 and c.lcl[0] == -4
    assert list(c.violations[1]) == list(range(8, 12))  # 4.5 > 4 desde el 9.º punto


def test_cusum_lower_side_and_subgroups():
    x = np.full(12, 9.0)
    c = pccpy.cusum_chart(x, target=10, sigma=1)["CUSUM"]
    assert np.allclose(c.secondary, -0.5 * np.arange(1, 13))
    sub = pccpy.cusum_chart(G, target=10, sigma=0.5)["CUSUM"]  # subgrupos de 5: sigma_x = 0.5/sqrt(5)
    assert sub.ucl[0] == pytest.approx(4 * 0.5 / np.sqrt(5))
    with pytest.raises(ValueError):
        pccpy.ewma_chart(X, weight=0)
    with pytest.raises(ValueError):
        pccpy.cusum_chart(X, h=-1)


# ---------------------------------------------------------------- resultado
def test_result_helpers():
    ch = pccpy.imr_chart(X, tests="all")
    df = ch.to_frame()
    assert len(df) == len(X) and "I_valor" in df.columns and "MR_LCS" in df.columns
    assert "I-MR" in ch.summary()
    with pytest.raises(KeyError):
        ch["nope"]
    pf = ch["I"].to_frame()
    assert list(pf["punto"])[:3] == [1, 2, 3]
