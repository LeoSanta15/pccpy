"""Tests para tolerance_interval y tolerance_interval_summary."""
import math

import numpy as np
import pytest
from scipy import stats

import pccpy

RNG = np.random.default_rng(42)
X50 = RNG.normal(100, 2, 50)
X300 = RNG.normal(100, 2, 300)


# ── Normal bilateral ──────────────────────────────────────────────────────────
def test_normal_two_bounds_symmetric():
    res = pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.95)
    xbar, s = X50.mean(), X50.std(ddof=1)
    assert res.lower == pytest.approx(xbar - res.k_factor * s)
    assert res.upper == pytest.approx(xbar + res.k_factor * s)
    assert res.lower < res.upper
    assert res.method == "normal" and res.sides == "two"


def test_normal_two_k_factor_known_value():
    # Para n=50, p=0.95, 1-alpha=0.95: k ≈ 2.382 (Howe 1969)
    res = pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.95)
    assert res.k_factor == pytest.approx(2.382, rel=0.01)


def test_normal_two_wider_at_higher_confidence():
    r90 = pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.90)
    r99 = pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.99)
    width = lambda r: r.upper - r.lower
    assert width(r99) > width(r90)


# ── Normal unilateral ─────────────────────────────────────────────────────────
def test_normal_lower_has_no_upper():
    res = pccpy.tolerance_interval(X50, sides="lower")
    assert res.upper is None
    assert res.lower is not None and res.k_factor is not None


def test_normal_upper_has_no_lower():
    res = pccpy.tolerance_interval(X50, sides="upper")
    assert res.lower is None
    assert res.upper is not None


def test_normal_lower_upper_k_equal():
    rl = pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.95, sides="lower")
    ru = pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.95, sides="upper")
    assert rl.k_factor == pytest.approx(ru.k_factor)


# ── No paramétrico ────────────────────────────────────────────────────────────
def test_nonparam_two_uses_order_stats():
    res = pccpy.tolerance_interval(X300, coverage=0.95, confidence=0.95, method="nonparametric")
    xs = np.sort(X300)
    assert res.lower == pytest.approx(xs[0])
    assert res.upper is not None
    assert res.achieved_confidence is not None
    assert res.achieved_confidence >= 0.95
    assert res.k_factor is None


def test_nonparam_small_n_raises():
    with pytest.raises(ValueError, match="insuficiente"):
        pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.95, method="nonparametric")


# ── tolerance_interval_summary ────────────────────────────────────────────────
def test_summary_matches_raw():
    xbar, s, n = float(X50.mean()), float(X50.std(ddof=1)), len(X50)
    rs = pccpy.tolerance_interval_summary(xbar, s, n, coverage=0.95, confidence=0.95)
    rr = pccpy.tolerance_interval(X50, coverage=0.95, confidence=0.95)
    assert rs.lower == pytest.approx(rr.lower)
    assert rs.upper == pytest.approx(rr.upper)
    assert rs.k_factor == pytest.approx(rr.k_factor)
    assert rs.method == "normal"


def test_summary_one_sided():
    rs = pccpy.tolerance_interval_summary(100.0, 2.0, 50, sides="upper")
    assert rs.lower is None and rs.upper is not None


def test_summary_validation():
    with pytest.raises(ValueError):
        pccpy.tolerance_interval_summary(100.0, -1.0, 50)
    with pytest.raises(ValueError):
        pccpy.tolerance_interval_summary(100.0, 2.0, 1)
    with pytest.raises(ValueError):
        pccpy.tolerance_interval_summary(100.0, 2.0, 50, coverage=1.5)


# ── Validaciones generales ────────────────────────────────────────────────────
def test_input_validation():
    with pytest.raises(ValueError):
        pccpy.tolerance_interval([1.0])
    with pytest.raises(ValueError):
        pccpy.tolerance_interval(X50, coverage=0)
    with pytest.raises(ValueError):
        pccpy.tolerance_interval(X50, sides="both")
    with pytest.raises(ValueError):
        pccpy.tolerance_interval(X50, method="bootstrap")


# ── to_frame / summary ────────────────────────────────────────────────────────
def test_to_frame_and_summary():
    res = pccpy.tolerance_interval(X50)
    df = res.to_frame()
    assert "Límite inferior" in df.index and "Límite superior" in df.index
    s = res.summary()
    assert "normal" in s and "LI" in s and "LS" in s
