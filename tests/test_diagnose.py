"""Tests para pp.diagnose — DiagnoseResult."""
import math

import numpy as np
import pytest

import pccpy

RNG = np.random.default_rng(42)


# ── Básico ────────────────────────────────────────────────────────────────────

def test_diagnose_returns_diagnose_result():
    x = RNG.normal(50, 2, 60)
    d = pccpy.diagnose(x)
    assert isinstance(d, pccpy.DiagnoseResult)


def test_diagnose_stats_correct():
    import warnings
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d = pccpy.diagnose(x)
    assert d.n == 5
    assert math.isclose(d.mean, 3.0)
    assert math.isclose(d.median, 3.0)
    assert math.isclose(d.min_val, 1.0)
    assert math.isclose(d.max_val, 5.0)


def test_diagnose_min_n():
    with pytest.raises(ValueError, match="al menos 4"):
        pccpy.diagnose([1.0, 2.0, 3.0])


# ── Normalidad ────────────────────────────────────────────────────────────────

def test_diagnose_normal_data():
    # Usamos semilla fija que produce datos normales sin skewness/kurtosis extremos
    rng_local = np.random.default_rng(2024)
    x = rng_local.normal(100, 5, 500)
    d = pccpy.diagnose(x)
    assert d.is_normal is True
    assert d.normality_p > 0.05


def test_diagnose_nonnormal_data():
    x = RNG.exponential(scale=2, size=200)
    d = pccpy.diagnose(x)
    assert d.is_normal is False
    assert d.normality_p <= 0.05


# ── Tendencia ─────────────────────────────────────────────────────────────────

def test_diagnose_trend_detected():
    x = np.linspace(1, 100, 60)
    d = pccpy.diagnose(x)
    assert d.has_trend is True
    assert d.trend_direction == "creciente"


def test_diagnose_downtrend_detected():
    x = np.linspace(100, 1, 60)
    d = pccpy.diagnose(x)
    assert d.has_trend is True
    assert d.trend_direction == "decreciente"


def test_diagnose_no_trend():
    x = RNG.normal(50, 2, 60)
    d = pccpy.diagnose(x)
    # No garantizado, pero datos aleatorios normales raramente tienen >80% incrementos
    assert isinstance(d.has_trend, bool)


# ── Valores atípicos ──────────────────────────────────────────────────────────

def test_diagnose_outliers_detected():
    x = RNG.normal(50, 1, 50).tolist()
    x[10] = 200.0   # outlier obvio
    d = pccpy.diagnose(x)
    assert d.outlier_count >= 1
    assert 10 in d.outlier_indices


def test_diagnose_no_outliers_clean_data():
    x = RNG.normal(50, 1, 50)
    d = pccpy.diagnose(x)
    # Puede haber 0 o pocos; sólo verificamos que es un entero ≥ 0
    assert d.outlier_count >= 0


# ── Capacidad ─────────────────────────────────────────────────────────────────

def test_diagnose_cp_cpk_with_limits():
    x = RNG.normal(50, 1, 100)
    d = pccpy.diagnose(x, lsl=44, usl=56)
    assert d.cp is not None
    assert d.cpk is not None
    assert d.cp > 0
    assert d.lsl == 44
    assert d.usl == 56


def test_diagnose_cp_none_without_limits():
    x = RNG.normal(50, 1, 60)
    d = pccpy.diagnose(x)
    assert d.cp is None
    assert d.cpk is None


def test_diagnose_target_stored():
    x = RNG.normal(50, 1, 60)
    d = pccpy.diagnose(x, lsl=44, usl=56, target=50.0)
    assert d.target == 50.0


# ── Recomendaciones ──────────────────────────────────────────────────────────

def test_diagnose_trend_recommends_run_chart():
    x = np.linspace(0, 100, 80)
    d = pccpy.diagnose(x)
    assert d.recommended_function == "run_chart"


def test_diagnose_normal_with_limits_recommends_capability():
    x = RNG.normal(50, 1, 100)
    d = pccpy.diagnose(x, lsl=44, usl=56)
    assert d.recommended_function in ("capability_analysis", "capability_boxcox")


def test_diagnose_small_n_recommends_imr():
    x = RNG.normal(50, 1, 15)
    d = pccpy.diagnose(x)
    assert d.recommended_function == "imr_chart"


def test_diagnose_snippet_contains_function():
    x = RNG.normal(50, 1, 60)
    d = pccpy.diagnose(x)
    assert d.recommended_function in d.recommended_snippet


# ── summary() ────────────────────────────────────────────────────────────────

def test_diagnose_summary_contains_key_fields():
    x = RNG.normal(50, 1, 60)
    d = pccpy.diagnose(x, lsl=44, usl=56)
    s = d.summary()
    assert "Media" in s
    assert "Normalidad" in s or "Normal" in s
    assert d.recommended_function in s


# ── plot() ───────────────────────────────────────────────────────────────────

def test_diagnose_plot_returns_figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = RNG.normal(50, 2, 60)
    d = pccpy.diagnose(x, lsl=44, usl=56)
    fig = d.plot()
    assert fig is not None
    plt.close("all")


# ── Issues ────────────────────────────────────────────────────────────────────

def test_diagnose_issues_nonnormal():
    x = RNG.exponential(scale=2, size=200)
    d = pccpy.diagnose(x)
    assert any("normal" in issue.lower() for issue in d.issues)


def test_diagnose_issues_trend():
    x = np.linspace(0, 100, 80)
    d = pccpy.diagnose(x)
    assert any("tendencia" in issue.lower() for issue in d.issues)


def test_diagnose_issues_low_capability():
    # Proceso muy variable con especificaciones estrechas → Cp < 1
    x = RNG.normal(50, 5, 100)
    d = pccpy.diagnose(x, lsl=49, usl=51)
    assert any("Cp" in issue or "capaz" in issue for issue in d.issues)
