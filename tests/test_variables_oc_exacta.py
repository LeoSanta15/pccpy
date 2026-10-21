"""Pruebas de la especificación 018: curva OC exacta (t no central) de los planes por variables unilaterales.

La referencia es la integral numérica `∫ Φ(√n·(z_p − k·s)) f_s(s) ds` escrita aparte (con `f_s` la densidad de la
desviación estándar muestral con n − 1 grados de libertad) y simulaciones con 20 semillas: nunca la aproximación normal
de Montgomery ni la salida anterior de pccpy.
"""
import math
import warnings

import numpy as np
import pytest
from scipy import stats
from scipy.integrate import quad
from scipy.optimize import brentq

import pccpy as pp

_PLAN_N = 1000  # tamaño de lote cualquiera (los planes a medida no lo usan)


def _pa_integral(n: int, k: float, p: float) -> float:
    """P(aceptar) = P((U − x̄)/s ≥ k) con P(X > U) = p, calculada por integración numérica."""
    zp = stats.norm.isf(p)
    gl = n - 1

    def integrando(s: float) -> float:
        f_s = 2.0 * s * gl * stats.chi2.pdf(gl * s * s, gl)
        return stats.norm.cdf(math.sqrt(n) * (zp - k * s)) * f_s

    return float(quad(integrando, 0.0, np.inf, epsabs=1e-13, epsrel=1e-11, limit=200)[0])


def _plan(n: int, k: float, aql: float = 1.0, **kw):
    return pp.acceptance_sampling_variables(_PLAN_N, aql, n=n, k=k, **kw)


def _pa_simulada(n: int, k: float, p: float, semillas: int = 20, muestras: int = 100_000) -> tuple[float, float]:
    """Fracción de lotes aceptados (media sobre semillas) y su error estándar; U = 0, μ = −z_p, σ = 1."""
    zp = stats.norm.isf(p)
    tasas = []
    for semilla in range(semillas):
        x = np.random.default_rng(semilla).standard_normal((muestras, n)) - zp
        q = (0.0 - x.mean(axis=1)) / x.std(axis=1, ddof=1)
        tasas.append(float(np.mean(q >= k)))
    media = float(np.mean(tasas))
    return media, math.sqrt(media * (1 - media) / (semillas * muestras))


# ── S018-RF-01: probabilidad de aceptación exacta ─────────────────────────────────────────────────────────────────────
_MALLA = [(n, k, p) for n in (2, 3, 5, 10, 35, 75, 200) for k in (-0.5, 0.0, 0.5, 1.5, 2.5)
          for p in (1e-6, 1e-4, 0.0025, 0.01, 0.1, 0.3, 0.5, 0.9)]


@pytest.mark.parametrize("n, k, p", _MALLA)
def test_s018_rf01_pa_coincide_con_la_integral(n, k, p):
    """S018-RF-01: `pa(p)` unilateral coincide con la integral numérica independiente (error relativo < 1e-9)."""
    assert _plan(n, k).pa(p) == pytest.approx(_pa_integral(n, k, p), rel=1e-9, abs=1e-12)


@pytest.mark.parametrize("n, k, p", [(35, 1.89, 0.01), (35, 1.89, 0.05), (3, 1.12, 0.025), (10, 1.41, 0.025)])
def test_s018_rf01_pa_coincide_con_la_simulacion(n, k, p):
    """S018-RF-01: con 20 semillas × 100 000 lotes, la `Pa` simulada queda a menos de 3 errores estándar de `pa(p)`."""
    simulada, error = _pa_simulada(n, k, p)
    assert abs(_plan(n, k).pa(p) - simulada) < 3 * error


def test_s018_rf01_la_tabla_de_mil_std_414_usa_la_pa_exacta():
    """S018-RF-01: el plan de la tabla (n = 35, k = 1,89) da `Pa(1 %)` = 0,94167 (integral), no 0,93902 (aproximación)."""
    plan = pp.acceptance_sampling_variables(1000, 1.0)
    assert (plan.n, plan.k) == (35, 1.89)
    assert plan.pa(0.01) == pytest.approx(_pa_integral(35, 1.89, 0.01), rel=1e-9)
    assert plan.pa(0.01) == pytest.approx(0.94167, abs=1e-5)


# ── S018-RF-02: alpha y ltpd con la OC exacta ─────────────────────────────────────────────────────────────────────────
def test_s018_rf02_alpha_y_ltpd_del_plan_de_la_tabla():
    """S018-RF-02: `alpha` y `ltpd` de N = 1000, AQL 1 % salen de la integral (0,05833 y 6,50 %)."""
    plan = pp.acceptance_sampling_variables(1000, 1.0)
    alpha_ref = 1.0 - _pa_integral(35, 1.89, 0.01)
    ltpd_ref = brentq(lambda p: _pa_integral(35, 1.89, p) - 0.10, 0.01, 0.9999, xtol=1e-12)
    assert plan.alpha == pytest.approx(alpha_ref, rel=1e-6)
    assert plan.ltpd == pytest.approx(ltpd_ref, rel=1e-6)
    assert plan.alpha == pytest.approx(0.05833, abs=1e-4)
    assert plan.ltpd * 100 == pytest.approx(6.50, abs=0.005)


def test_s018_rf02_alpha_y_ltpd_de_un_plan_a_medida():
    """S018-RF-02: un plan a medida (n = 3, k = 1,12, AQL 2,5 %) también usa la `Pa` exacta."""
    plan = _plan(3, 1.12, aql=2.5)
    assert plan.alpha == pytest.approx(1.0 - _pa_integral(3, 1.12, 0.025), rel=1e-6)
    assert plan.alpha == pytest.approx(0.1094, abs=1e-4)


def test_s018_rf02_ltpd_nan_si_pa_en_el_aql_es_menor_que_010():
    """S018-RF-02 (guarda: pasa antes del código): `ltpd` es nan, sin lanzar, si `Pa(AQL) < 0,10`."""
    plan = _plan(5, 5.0, aql=1.0)
    assert plan.pa(0.01) < 0.10
    assert math.isnan(plan.ltpd)


def test_s018_rf02_oc_curve_monotona_y_acotada():
    """S018-RF-02 (guarda): `oc_curve()` empieza en 1, no crece y está en [0, 1]."""
    oc = pp.acceptance_sampling_variables(1000, 1.0).oc_curve(stable=True)
    pa = oc["p_accept"].to_numpy()
    assert pa[0] == 1.0
    assert np.all(np.diff(pa) <= 1e-12) and pa.min() >= 0.0 and pa.max() <= 1.0


# ── S018-RF-03: extremos sin ruido numérico ───────────────────────────────────────────────────────────────────────────
def test_s018_rf03_p_cero_y_uno():
    """S018-RF-03 (guarda): `Pa(0) = 1` y `Pa(1) = 0` exactos."""
    plan = _plan(10, 1.5)
    assert plan.pa(0.0) == 1.0 and plan.pa(1.0) == 0.0


@pytest.mark.parametrize("n, k, p", [(2, 1.0, 0.01), (2000, 2.0, 1e-12), (2000, 2.0, 0.01), (10, 0.0, 0.3),
                                     (10, -1.0, 0.3), (35, 1.89, 1e-12)])
def test_s018_rf03_extremos_sin_avisos(n, k, p):
    """S018-RF-03: `n` = 2 y 2 000, `p` = 1e-12 y `k` ≤ 0 dan un valor finito en [0, 1] sin avisos."""
    plan = _plan(n, k)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        valor = plan.pa(p)
    assert math.isfinite(valor) and 0.0 <= valor <= 1.0


def test_s018_rf03_n_igual_a_2_coincide_con_la_integral():
    """S018-RF-03: con n = 2 (un grado de libertad) `pa` coincide con la integral independiente."""
    for p in (0.001, 0.05, 0.3):
        assert _plan(2, 1.0).pa(p) == pytest.approx(_pa_integral(2, 1.0, p), rel=1e-9)


def test_s018_rf03_k_cero_da_al_menos_un_medio():
    """S018-RF-03: con k = 0 y p ≤ 0,5, `Pa ≥ 0,5` (la media queda del lado bueno del límite)."""
    plan = _plan(10, 0.0)
    assert all(plan.pa(p) >= 0.5 for p in (1e-6, 0.01, 0.2, 0.5))


# ── S018-RF-04: la OC bilateral no cambia ─────────────────────────────────────────────────────────────────────────────
def test_s018_rf04_bilateral_coincide_con_la_simulacion():
    """S018-RF-04 (guarda: pasa antes del código): bilateral con el proceso centrado, 20 semillas × 100 000 lotes."""
    n, k, p = 10, 1.5, 0.02
    z = stats.norm.isf(p / 2.0)   # límites en ±z, μ = 0, σ = 1
    tasas = []
    for semilla in range(20):
        x = np.random.default_rng(semilla).standard_normal((100_000, n))
        xbar, s = x.mean(axis=1), x.std(axis=1, ddof=1)
        tasas.append(float(np.mean(((z - xbar) / s >= k) & ((xbar + z) / s >= k))))
    media = float(np.mean(tasas))
    error = math.sqrt(media * (1 - media) / (20 * 100_000))
    assert abs(_plan(n, k, spec_type="two").pa(p) - media) < 3 * error
