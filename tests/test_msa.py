"""Tests para gage_rr, gage_rr_nested, gage_type1, gage_type1_summary,
gage_linearity, attribute_agreement y capability_analysis_summary."""
import math

import numpy as np
import pandas as pd
import pytest

import pccpy

RNG = np.random.default_rng(0)

# Datos sintéticos: 10 partes × 3 operadores × 2 réplicas
PARTS, OPS, REPS = 10, 3, 2
_part_eff = RNG.normal(0, 2.0, PARTS)
_op_eff   = RNG.normal(0, 0.3, OPS)
DATA = np.array([
    _part_eff[p] + _op_eff[o] + RNG.normal(0, 0.5, REPS)
    for p in range(PARTS) for o in range(OPS)
]).ravel()
TOLERANCE = 20.0


# ── Crossed Gage R&R — ANOVA ──────────────────────────────────────────────────
def test_gage_rr_anova_pct_finite():
    g = pccpy.gage_rr(DATA, parts=PARTS, operators=OPS, replicates=REPS,
                      tolerance=TOLERANCE)
    assert math.isfinite(g.pct_gage)
    assert 0 <= g.pct_gage <= 100


def test_gage_rr_anova_variance_components_sum_to_total():
    g = pccpy.gage_rr(DATA, parts=PARTS, operators=OPS, replicates=REPS)
    summed = g.var_repeatability + g.var_reproducibility + g.var_part
    assert g.var_total == pytest.approx(summed, rel=1e-6)


def test_gage_rr_anova_table_columns():
    g = pccpy.gage_rr(DATA, parts=PARTS, operators=OPS, replicates=REPS)
    assert g.anova_table is not None
    for col in ("GL", "SC", "CM", "F"):
        assert col in g.anova_table.columns


def test_gage_rr_ndc_positive():
    g = pccpy.gage_rr(DATA, parts=PARTS, operators=OPS, replicates=REPS,
                      tolerance=TOLERANCE)
    assert g.ndc >= 1


def test_gage_rr_to_frame_and_summary():
    g = pccpy.gage_rr(DATA, parts=PARTS, operators=OPS, replicates=REPS,
                      tolerance=TOLERANCE)
    df = g.to_frame()
    assert len(df) > 0
    s = g.summary()
    assert "Repetibilidad" in s or "repeatability" in s.lower() or "%" in s


# ── Crossed Gage R&R — Xbar-R ────────────────────────────────────────────────
def test_gage_rr_xbarr_method():
    g = pccpy.gage_rr(DATA, parts=PARTS, operators=OPS, replicates=REPS,
                      method="xbar_r", tolerance=TOLERANCE)
    assert math.isfinite(g.pct_gage)
    assert g.anova_table is None


# ── Nested Gage R&R ───────────────────────────────────────────────────────────
def test_gage_rr_nested_returns_result():
    data_nested = RNG.normal(0, 1, PARTS * OPS * REPS)
    g = pccpy.gage_rr_nested(data_nested, parts=PARTS, operators=OPS, replicates=REPS)
    assert math.isfinite(g.pct_gage)


# ── Type 1 ────────────────────────────────────────────────────────────────────
def test_gage_type1_bias_calculation():
    ref = 10.0
    meas = RNG.normal(ref + 0.05, 0.08, 25)
    t1 = pccpy.gage_type1(meas, reference=ref, tolerance=0.5)
    assert t1.bias == pytest.approx(meas.mean() - ref)


def test_gage_type1_t_stat():
    ref = 10.0
    meas = RNG.normal(ref + 0.05, 0.08, 25)
    t1 = pccpy.gage_type1(meas, reference=ref)
    expected_t = t1.bias * math.sqrt(25) / meas.std(ddof=1)
    assert t1.t_stat == pytest.approx(expected_t)


def test_gage_type1_cg_cgk_with_tolerance():
    meas = RNG.normal(10.0, 0.05, 25)
    t1 = pccpy.gage_type1(meas, reference=10.0, tolerance=0.5)
    assert math.isfinite(t1.cg) and math.isfinite(t1.cgk)
    assert t1.cg > 0


def test_gage_type1_cg_nan_without_tolerance():
    meas = RNG.normal(10.0, 0.05, 25)
    t1 = pccpy.gage_type1(meas, reference=10.0)
    assert math.isnan(t1.cg) and math.isnan(t1.cgk)


def test_gage_type1_to_frame_and_summary():
    meas = RNG.normal(10.0, 0.05, 25)
    t1 = pccpy.gage_type1(meas, reference=10.0, tolerance=0.5)
    assert len(t1.to_frame()) > 0
    s = t1.summary()
    assert len(s) > 0


# ── Type 1 — summary ─────────────────────────────────────────────────────────
def test_gage_type1_summary_matches_raw():
    ref = 10.0
    meas = RNG.normal(ref + 0.02, 0.06, 30)
    xbar, s, n = float(meas.mean()), float(meas.std(ddof=1)), len(meas)
    ts = pccpy.gage_type1_summary(xbar, s, n, reference=ref, tolerance=0.5)
    tr = pccpy.gage_type1(meas, reference=ref, tolerance=0.5)
    assert ts.bias   == pytest.approx(tr.bias)
    assert ts.t_stat == pytest.approx(tr.t_stat)
    assert ts.cg     == pytest.approx(tr.cg)
    assert ts.cgk    == pytest.approx(tr.cgk)


def test_gage_type1_summary_validation():
    with pytest.raises(ValueError):
        pccpy.gage_type1_summary(10.0, -0.1, 25, reference=10.0)
    with pytest.raises(ValueError):
        pccpy.gage_type1_summary(10.0, 0.05, 1, reference=10.0)


# ── Linearity & Bias ──────────────────────────────────────────────────────────
def test_gage_linearity_detects_positive_slope():
    refs = np.repeat([2.0, 5.0, 8.0, 11.0, 14.0], 6)
    meas = refs + 0.02 * refs + RNG.normal(0, 0.05, len(refs))
    lin = pccpy.gage_linearity(meas, refs, tolerance=14.0)
    assert lin.slope > 0


def test_gage_linearity_zero_slope_constant_bias():
    refs = np.repeat([2.0, 4.0, 6.0, 8.0, 10.0], 5)
    meas = refs + 0.1 + RNG.normal(0, 0.02, len(refs))
    lin = pccpy.gage_linearity(meas, refs, tolerance=10.0)
    assert abs(lin.slope) < 0.05


def test_gage_linearity_summary_and_frame():
    refs = np.repeat([2.0, 4.0, 6.0, 8.0, 10.0], 5)
    meas = refs + RNG.normal(0.05, 0.03, len(refs))
    lin = pccpy.gage_linearity(meas, refs, tolerance=10.0)
    assert len(lin.summary()) > 0
    assert len(lin.to_frame()) > 0


# ── Attribute Agreement ───────────────────────────────────────────────────────
def _make_attr_data():
    ref = np.array(["G", "D", "G", "G", "D", "G", "D", "G", "D", "G"])
    rng2 = np.random.default_rng(11)
    ops = {}
    for op in ["Op1", "Op2", "Op3"]:
        r1, r2 = ref.copy(), ref.copy()
        for r in (r1, r2):
            flip = rng2.random(10) < 0.1
            r[flip] = np.where(r[flip] == "G", "D", "G")
        ops[op] = np.concatenate([r1, r2])
    return pd.DataFrame(ops), ref


def test_attribute_agreement_kappa_in_range():
    df, ref = _make_attr_data()
    res = pccpy.attribute_agreement(df, reference=ref, replicates=2)
    for kappa in res.kappa_vs_reference["kappa"]:
        assert -1 <= kappa <= 1


def test_attribute_agreement_fleiss_kappa():
    df, ref = _make_attr_data()
    res = pccpy.attribute_agreement(df, reference=ref, replicates=2)
    assert math.isfinite(res.fleiss_kappa)
    assert -1 <= res.fleiss_kappa <= 1


def test_attribute_agreement_perfect_gives_kappa_one():
    # 10 muestras × 2 réplicas; reference debe tener n×replicates entradas
    ref10 = np.array(["G", "D", "G", "D", "G", "G", "D", "G", "D", "G"])
    ref20 = np.tile(ref10, 2)   # réplica 1 luego réplica 2
    df = pd.DataFrame({"Op1": ref20, "Op2": ref20, "Op3": ref20})
    res = pccpy.attribute_agreement(df, reference=ref20, replicates=2)
    for kappa in res.kappa_vs_reference["kappa"]:
        assert kappa == pytest.approx(1.0)


def test_attribute_agreement_summary_and_frame():
    df, ref = _make_attr_data()
    res = pccpy.attribute_agreement(df, reference=ref, replicates=2)
    assert len(res.summary()) > 0
    assert len(res.to_frame()) > 0


# ── capability_analysis_summary ───────────────────────────────────────────────
def test_capability_summary_matches_raw():
    x = RNG.normal(50, 2, 200)
    rr = pccpy.capability_analysis(x, lsl=44, usl=56)
    rs = pccpy.capability_analysis_summary(
        mean=rr.mean, std_overall=rr.sigma_overall, n=rr.n, lsl=44, usl=56
    )
    assert rs.pp  == pytest.approx(rr.pp,  rel=1e-5)
    assert rs.ppk == pytest.approx(rr.ppk, rel=1e-5)
    assert math.isnan(rs.ppm_obs[0])


def test_capability_summary_with_std_within():
    rs = pccpy.capability_analysis_summary(
        mean=50.0, std_overall=2.0, n=100,
        lsl=44, usl=56, std_within=1.8
    )
    assert rs.cp == pytest.approx((56 - 44) / (6 * 1.8))
    assert rs.within_method == "especificada"
