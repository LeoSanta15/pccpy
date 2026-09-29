"""Tests para acceptance_sampling_attributes, acceptance_sampling_variables y dodge_romig."""
import math

import numpy as np
import pytest

import pccpy

RNG = np.random.default_rng(7)


# ── Z1.4 atributos ────────────────────────────────────────────────────────────
def test_z14_returns_plan():
    plan = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    assert plan.n > 0 and plan.c >= 0


def test_z14_pa_at_zero_defect_rate_is_one():
    plan = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    assert plan.pa(0.0) == pytest.approx(1.0)


def test_z14_pa_at_high_defect_rate_near_zero():
    plan = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    assert plan.pa(0.5) < 0.01


def test_z14_ltpd_at_10pct_acceptance():
    plan = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    # P(aceptar | ltpd) ≈ 0.10 por definición
    assert plan.pa(plan.ltpd) == pytest.approx(0.10, abs=0.05)


def test_z14_oc_curve_shape():
    plan = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    oc = plan.oc_curve()
    # columnas en español
    assert "P(aceptar)" in oc.columns
    # Pa decrece monótonamente
    assert (oc["P(aceptar)"].diff().dropna() <= 0).all()


def test_z14_aoq_curve():
    plan = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    aoq = plan.aoq_curve()
    assert "AOQ" in aoq.columns
    # El máximo de la curva AOQ debe ser cercano a aoq_max
    assert aoq["AOQ"].max() == pytest.approx(plan.aoq_max, rel=0.10)


def test_z14_to_frame_and_summary():
    plan = pccpy.acceptance_sampling_attributes(N=500, aql=2.5)
    df = plan.to_frame()
    assert len(df) > 0
    s = plan.summary()
    assert len(s) > 0


def test_z14_larger_lot_same_aql_same_or_larger_n():
    p1 = pccpy.acceptance_sampling_attributes(N=500, aql=1.0)
    p2 = pccpy.acceptance_sampling_attributes(N=10000, aql=1.0)
    assert p2.n >= p1.n


# ── Z1.9 variables ────────────────────────────────────────────────────────────
def test_z19_plan_has_positive_n_and_k():
    plan = pccpy.acceptance_sampling_variables(N=1000, aql=1.0)
    assert plan.n > 0 and plan.k > 0


def test_z19_evaluate_accept_good_lot():
    plan = pccpy.acceptance_sampling_variables(N=1000, aql=1.0, spec_type="one")
    sample = RNG.normal(10.5, 0.05, plan.n)
    dec = plan.evaluate(sample, usl=11.0)
    assert dec["accept"] is True


def test_z19_evaluate_reject_bad_lot():
    plan = pccpy.acceptance_sampling_variables(N=1000, aql=1.0, spec_type="one")
    # Q = (usl - xbar) / s < k → rechazar
    sample = np.full(plan.n, 10.999)
    sample[0] = 10.99   # desviación pequeña; Q ≈ 0.72 < k=0.851
    dec = plan.evaluate(sample, usl=11.0)
    assert dec["accept"] is False


def test_z19_evaluate_returns_expected_keys():
    plan = pccpy.acceptance_sampling_variables(N=1000, aql=1.0)
    sample = RNG.normal(10.5, 0.1, plan.n)
    dec = plan.evaluate(sample, usl=11.0)
    for key in ("xbar", "s", "accept"):
        assert key in dec


def test_z19_oc_curve():
    plan = pccpy.acceptance_sampling_variables(N=1000, aql=1.0)
    oc = plan.oc_curve()
    assert "P(aceptar)" in oc.columns
    assert (oc["P(aceptar)"].diff().dropna() <= 0).all()


# ── Dodge-Romig ───────────────────────────────────────────────────────────────
def test_dodge_romig_ltpd_plan():
    plan = pccpy.dodge_romig(N=1000, ltpd=0.05, process_avg=0.01)
    assert plan.n > 0 and plan.c >= 0
    assert math.isfinite(plan.aoql)


def test_dodge_romig_aoql_plan():
    plan = pccpy.dodge_romig(N=1000, aoql=0.01, process_avg=0.005)
    assert plan.n > 0 and plan.c >= 0
    assert math.isfinite(plan.ltpd)


def test_dodge_romig_summary_and_frame():
    plan = pccpy.dodge_romig(N=500, ltpd=0.05, process_avg=0.01)
    s = plan.summary()
    assert len(s) > 0
    df = plan.to_frame()
    assert len(df) > 0
