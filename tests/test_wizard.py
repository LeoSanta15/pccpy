"""Tests para pp.wizard — WizardResult y modos auto/cli."""
import math
import textwrap

import numpy as np
import pytest

import pccpy

RNG = np.random.default_rng(42)


# ── WizardResult ──────────────────────────────────────────────────────────────

def test_wizard_result_snippet_default():
    from pccpy._wizard import WizardResult
    r = WizardResult(function="imr_chart", params={"tests": (1,)})
    s = r.snippet()
    assert "imr_chart" in s
    assert "tests" in s


def test_wizard_result_snippet_custom():
    from pccpy._wizard import WizardResult
    r = WizardResult(function="imr_chart", _snippet="pp.imr_chart(x)")
    assert r.snippet() == "pp.imr_chart(x)"


def test_wizard_result_summary_contains_function():
    from pccpy._wizard import WizardResult
    r = WizardResult(function="ewma_chart", rationale="Alta sensibilidad")
    s = r.summary()
    assert "ewma_chart" in s
    assert "Alta sensibilidad" in s


def test_wizard_result_summary_contains_alternatives():
    from pccpy._wizard import WizardResult
    r = WizardResult(function="imr_chart", alternatives=["ewma_chart"])
    assert "ewma_chart" in r.summary()


def test_wizard_result_run_imr():
    from pccpy._wizard import WizardResult
    x = RNG.normal(100, 2, 30)
    r = WizardResult(function="imr_chart", params={"tests": (1,)})
    carta = r.run(x)
    assert hasattr(carta, "summary")


# ── Modo auto — datos 1-D ─────────────────────────────────────────────────────

def test_wizard_auto_1d_normal_large_returns_capability():
    x = RNG.normal(50, 2, 200)
    res = pccpy.wizard(x, mode="auto")
    assert res.function in ("capability_analysis", "capability_boxcox")


def test_wizard_auto_1d_small_returns_imr():
    x = RNG.normal(50, 2, 15)
    res = pccpy.wizard(x, mode="auto")
    assert res.function == "imr_chart"


def test_wizard_auto_1d_trend_returns_run_chart():
    x = np.linspace(1, 100, 50)
    res = pccpy.wizard(x, mode="auto")
    assert res.function == "run_chart"


def test_wizard_auto_2d_small_cols_returns_xbar_r():
    x = RNG.normal(0, 1, (30, 5))
    res = pccpy.wizard(x, mode="auto")
    assert res.function == "xbar_r_chart"


def test_wizard_auto_2d_many_cols_returns_t2():
    x = RNG.normal(0, 1, (30, 12))
    res = pccpy.wizard(x, mode="auto")
    assert res.function == "t2_chart"


def test_wizard_auto_requires_x():
    with pytest.raises(ValueError, match="obligatorio"):
        pccpy.wizard(mode="auto")


def test_wizard_auto_result_has_snippet():
    x = RNG.normal(0, 1, 50)
    res = pccpy.wizard(x, mode="auto")
    assert len(res.snippet()) > 0


# ── Modo CLI — simulado con monkeypatch ───────────────────────────────────────

def _simulate_cli(inputs: list[str], monkeypatch: pytest.MonkeyPatch) -> pccpy.WizardResult:
    """Simula entradas de teclado para el modo CLI."""
    responses = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    return pccpy.wizard(mode="cli")


def test_wizard_cli_imr(monkeypatch):
    # raíz→cartas→cartas_ind→r:imr
    res = _simulate_cli(["1", "1", "1"], monkeypatch)
    assert res.function == "imr_chart"


def test_wizard_cli_capability(monkeypatch):
    # raíz→capacidad→cap_normal→r:capability
    res = _simulate_cli(["2", "1", "1"], monkeypatch)
    assert res.function == "capability_analysis"


def test_wizard_cli_sixpack(monkeypatch):
    # raíz→capacidad→cap_normal→r:sixpack
    res = _simulate_cli(["2", "1", "2"], monkeypatch)
    assert res.function == "capability_sixpack"


def test_wizard_cli_cap_summary(monkeypatch):
    # raíz→capacidad→cap_normal→r:cap_summary
    res = _simulate_cli(["2", "1", "3"], monkeypatch)
    assert res.function == "capability_analysis_summary"


def test_wizard_cli_ewma(monkeypatch):
    # raíz→cartas→cartas_ind→r:ewma
    res = _simulate_cli(["1", "1", "2"], monkeypatch)
    assert res.function == "ewma_chart"


def test_wizard_cli_cusum(monkeypatch):
    # raíz→cartas→cartas_ind→r:cusum
    res = _simulate_cli(["1", "1", "3"], monkeypatch)
    assert res.function == "cusum_chart"


def test_wizard_cli_xbar_r(monkeypatch):
    # raíz→cartas→cartas_sub→cartas_sub_r→r:xbar_r
    res = _simulate_cli(["1", "2", "1", "1"], monkeypatch)
    assert res.function == "xbar_r_chart"


def test_wizard_cli_xbar_s(monkeypatch):
    # raíz→cartas→cartas_sub→r:xbar_s
    res = _simulate_cli(["1", "2", "2"], monkeypatch)
    assert res.function == "xbar_s_chart"


def test_wizard_cli_laney_p(monkeypatch):
    # raíz→cartas→cartas_p→cartas_p_var→r:laney_p
    res = _simulate_cli(["1", "3", "2", "2"], monkeypatch)
    assert res.function == "laney_p_chart"


def test_wizard_cli_z14(monkeypatch):
    # raíz→muestreo→r:z14
    res = _simulate_cli(["4", "1"], monkeypatch)
    assert res.function == "acceptance_sampling_attributes"


def test_wizard_cli_z19(monkeypatch):
    # raíz→muestreo→r:z19
    res = _simulate_cli(["4", "2"], monkeypatch)
    assert res.function == "acceptance_sampling_variables"


def test_wizard_cli_dodge_romig_ltpd(monkeypatch):
    # raíz→muestreo→muestreo_dr→r:dr_ltpd
    res = _simulate_cli(["4", "3", "1"], monkeypatch)
    assert res.function == "dodge_romig"


def test_wizard_cli_gage_rr(monkeypatch):
    # raíz→msa→r:gage_rr
    res = _simulate_cli(["3", "1"], monkeypatch)
    assert res.function == "gage_rr"


def test_wizard_cli_tolerance_bilateral(monkeypatch):
    # raíz→tolerancia→tol_datos→tol_lados→r:tol_two
    res = _simulate_cli(["6", "1", "1", "1"], monkeypatch)
    assert res.function == "tolerance_interval"
    assert res.params.get("sides") == "two"


def test_wizard_cli_run_chart(monkeypatch):
    # raíz→corridas→r:run
    res = _simulate_cli(["7", "1"], monkeypatch)
    assert res.function == "run_chart"


def test_wizard_cli_precontrol(monkeypatch):
    # raíz→corridas→r:precontrol
    res = _simulate_cli(["7", "2"], monkeypatch)
    assert res.function == "precontrol"


def test_wizard_cli_invalid_input_retries(monkeypatch):
    # Entrada inválida primero, luego válida
    inputs = iter(["0", "abc", "1", "1", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    res = pccpy.wizard(mode="cli")
    assert res.function == "imr_chart"


# ── Modo no válido ─────────────────────────────────────────────────────────────

def test_wizard_invalid_mode():
    with pytest.raises(ValueError, match="mode"):
        pccpy.wizard(mode="unknown")


# ── Default mode detection ────────────────────────────────────────────────────

def test_wizard_default_mode_with_x():
    """Sin mode= pero con x → auto."""
    x = RNG.normal(0, 1, 200)
    res = pccpy.wizard(x)
    assert isinstance(res, pccpy.WizardResult)


def test_wizard_default_mode_no_x(monkeypatch):
    """Sin mode= ni x → cli."""
    inputs = iter(["1", "1", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    res = pccpy.wizard()
    assert res.function == "imr_chart"
