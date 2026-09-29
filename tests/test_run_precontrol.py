"""Tests para run_chart y precontrol."""
import math
import collections

import numpy as np
import pytest

import pccpy

RNG = np.random.default_rng(5)
X_RAND  = RNG.normal(100, 2, 50)
X_TREND = np.linspace(98, 106, 50) + RNG.normal(0, 0.3, 50)


# ── run_chart ──────────────────────────────────────────────────────────────────
def test_run_chart_returns_result():
    rc = pccpy.run_chart(X_RAND)
    assert math.isfinite(rc.median)
    assert rc.n_above + rc.n_below == len(X_RAND)


def test_run_chart_p_values_in_range():
    rc = pccpy.run_chart(X_RAND)
    for attr in ("p_clustering", "p_mixtures", "p_trends", "p_oscillation"):
        v = getattr(rc, attr)
        assert 0 <= v <= 1


def test_run_chart_trend_detected():
    rc = pccpy.run_chart(X_TREND)
    assert rc.p_trends < 0.05


def test_run_chart_to_frame():
    rc = pccpy.run_chart(X_RAND)
    df = rc.to_frame()
    assert len(df) > 0


def test_run_chart_summary():
    rc = pccpy.run_chart(X_RAND)
    s = rc.summary()
    assert len(s) > 0


def test_run_chart_min_length():
    with pytest.raises(ValueError):
        pccpy.run_chart([1.0, 2.0])


# ── precontrol ────────────────────────────────────────────────────────────────
def test_precontrol_returns_result():
    pc = pccpy.precontrol(X_RAND, lsl=94, usl=106)
    assert pc.lsl == 94 and pc.usl == 106
    assert len(pc.zones) == len(X_RAND)


def test_precontrol_zone_labels_valid():
    pc = pccpy.precontrol(X_RAND, lsl=94, usl=106)
    valid = {"G", "Y-", "Y+", "R-", "R+"}
    assert all(z in valid for z in pc.zones)


def test_precontrol_zone_counts():
    pc = pccpy.precontrol(X_RAND, lsl=94, usl=106)
    counts = collections.Counter(pc.zones)
    assert sum(counts.values()) == len(X_RAND)


def test_precontrol_all_green_no_red():
    x = np.full(30, 100.0) + RNG.normal(0, 0.01, 30)
    pc = pccpy.precontrol(x, lsl=94, usl=106)
    counts = collections.Counter(pc.zones)
    assert counts.get("R-", 0) + counts.get("R+", 0) == 0
    assert len(pc.signals) == 0


def test_precontrol_out_of_spec_detected():
    x = np.concatenate([np.full(28, 100.0), [80.0, 120.0]])
    pc = pccpy.precontrol(x, lsl=94, usl=106)
    counts = collections.Counter(pc.zones)
    assert counts.get("R-", 0) + counts.get("R+", 0) > 0


def test_precontrol_to_frame():
    pc = pccpy.precontrol(X_RAND, lsl=94, usl=106)
    df = pc.to_frame()
    assert len(df) > 0


def test_precontrol_summary():
    pc = pccpy.precontrol(X_RAND, lsl=94, usl=106)
    s = pc.summary()
    assert len(s) > 0


def test_precontrol_requires_both_specs():
    with pytest.raises((ValueError, TypeError)):
        pccpy.precontrol(X_RAND, lsl=94)
