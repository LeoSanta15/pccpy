"""Intervalos bootstrap de capacidad (``ci_method="bootstrap"``): normal, Box-Cox y no normal."""
from __future__ import annotations

import warnings

import numpy as np
import pytest
from scipy import stats

import pccpy as pp

X = np.random.default_rng(2).gamma(4, 1, 80) + 5
LSL, USL = 6.0, 22.0


def _pp_ppk_manual(m):
    """Pp y Ppk con la sigma general, escritos aparte para cada remuestreo."""
    mu, s = np.mean(m), np.std(m, ddof=1)
    return np.array([(USL - LSL) / (6 * s), min(mu - LSL, USL - mu) / (3 * s)])


def test_capacidad_normal_bootstrap_coincide_con_el_calculo_manual():
    r = pp.capability_analysis(X, LSL, USL, ci_method="bootstrap", n_boot=500, seed=5)
    manual = pp.bootstrap_ci(X, _pp_ppk_manual, n_boot=500, seed=5)
    lo, hi = manual.ci
    assert r.pp_ci == pytest.approx((lo[0], hi[0])) and r.ppk_ci == pytest.approx((lo[1], hi[1]))
    assert r.ci_method == "bootstrap:bca:500" and "bootstrap bca, 500" in r.summary()
    assert r.pp_ci[0] < r.pp < r.pp_ci[1]


def test_por_defecto_no_cambia_y_un_solo_limite_deja_pp_sin_intervalo():
    normal = pp.capability_analysis(X, LSL, USL)
    assert normal.ci_method == "normal" and "bootstrap" not in normal.summary()
    uno = pp.capability_analysis(X, usl=USL, ci_method="bootstrap", n_boot=300, seed=1)
    assert np.isnan(uno.pp_ci).all() and uno.ppk_ci[0] < uno.ppk < uno.ppk_ci[1]


def test_percentil_y_bca_difieren_pero_son_reproducibles():
    a = pp.capability_analysis(X, LSL, USL, ci_method="bootstrap", bootstrap_method="percentile", seed=2).ppk_ci
    b = pp.capability_analysis(X, LSL, USL, ci_method="bootstrap", bootstrap_method="percentile", seed=2).ppk_ci
    c = pp.capability_analysis(X, LSL, USL, ci_method="bootstrap", seed=2).ppk_ci
    assert a == b and a != c


def test_cobertura_de_pp_con_datos_asimetricos_mejora_la_del_intervalo_normal():
    """gamma(2), n = 150, límites −3 y 9: el intervalo chi-cuadrado de Pp subcubre; BCa se acerca al 95 %."""
    rng = np.random.default_rng(31)
    lsl, usl, mu, sd = -3.0, 9.0, 2.0, np.sqrt(2.0)
    pp_true, ppk_true = (usl - lsl) / (6 * sd), min(mu - lsl, usl - mu) / (3 * sd)
    n, rep = 150, 300
    pp_n = pp_b = ppk_b = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(rep):
            x = rng.gamma(2, 1, n)
            rn = pp.capability_analysis(x, lsl, usl)
            rb = pp.capability_analysis(x, lsl, usl, ci_method="bootstrap", n_boot=500, seed=int(rng.integers(1 << 30)))
            pp_n += rn.pp_ci[0] <= pp_true <= rn.pp_ci[1]
            pp_b += rb.pp_ci[0] <= pp_true <= rb.pp_ci[1]
            ppk_b += rb.ppk_ci[0] <= ppk_true <= rb.ppk_ci[1]
    assert pp_b / rep >= 0.88
    assert pp_b / rep > pp_n / rep + 0.05  # medido: ≈ 0,92 frente a ≈ 0,81
    assert ppk_b / rep >= 0.86  # para Ppk el intervalo normal ya es razonable: aquí solo se exige no empeorar mucho


def test_boxcox_con_bootstrap_equivale_a_capacidad_sobre_los_datos_transformados():
    r = pp.capability_boxcox(X, LSL, USL, lam=0.5, ci_method="bootstrap", n_boot=300, seed=3)
    y = (X ** 0.5 - 1) / 0.5
    t = lambda v: (v ** 0.5 - 1) / 0.5  # noqa: E731
    ref = pp.capability_analysis(y, t(LSL), t(USL), ci_method="bootstrap", n_boot=300, seed=3)
    assert r.pp_ci == pytest.approx(ref.pp_ci) and r.ppk_ci == pytest.approx(ref.ppk_ci)


def test_nonormal_bootstrap_reajusta_la_distribucion_en_cada_remuestreo():
    x = np.random.default_rng(8).weibull(1.5, 60) * 5
    lsl, usl = 0.2, 20.0
    r = pp.capability_nonnormal(x, lsl, usl, distribution="weibull", ci_method="bootstrap", n_boot=120, seed=4)

    def manual(m):  # ajuste de Weibull y percentiles escritos aparte con scipy
        c, loc, scale = stats.weibull_min.fit(m, floc=0)
        q = lambda p: stats.weibull_min.ppf(p, c, loc, scale)  # noqa: E731
        lo, med, hi = q(stats.norm.cdf(-3)), q(0.5), q(stats.norm.cdf(3))
        return np.array([(usl - lsl) / (hi - lo), min((med - lsl) / (med - lo), (usl - med) / (hi - med))])

    ref = pp.bootstrap_ci(x, manual, method="percentile", n_boot=120, seed=4)
    assert r.pp_ci == pytest.approx((ref.ci[0][0], ref.ci[1][0]), rel=1e-6)
    assert r.ppk_ci == pytest.approx((ref.ci[0][1], ref.ci[1][1]), rel=1e-6)
    assert r.ci_method == "bootstrap:percentile:120" and "bootstrap percentile" in r.summary()
    assert "pp_lower" in r.to_frame(stable=True).index


def test_nonormal_sin_bootstrap_no_cambia():
    r = pp.capability_nonnormal(X, LSL, USL, distribution="lognormal")
    assert r.ci_method == "none" and np.isnan(r.pp_ci).all()
    assert "pp_lower" not in r.to_frame(stable=True).index and "bootstrap" not in r.summary()


def test_nonormal_con_un_solo_limite():
    r = pp.capability_nonnormal(X, usl=USL, distribution="gamma", ci_method="bootstrap", n_boot=100, seed=1)
    assert np.isnan(r.pp_ci).all() and np.isfinite(r.ppk_ci).all()


@pytest.mark.parametrize("llamada, texto", [
    (lambda: pp.capability_analysis(X, LSL, USL, ci_method="x"), "ci_method"),
    (lambda: pp.capability_analysis(X, LSL, USL, ci_method="bootstrap", bootstrap_method="x"), "method"),
    (lambda: pp.capability_analysis(X, LSL, USL, ci_method="bootstrap", n_boot=5), "n_boot"),
    (lambda: pp.capability_nonnormal(X, LSL, USL, ci_method="normal"), "ci_method"),
    (lambda: pp.capability_nonnormal(X, LSL, USL, ci_level=1.5), "ci_level"),
])
def test_errores(llamada, texto):
    with pytest.raises(ValueError, match=texto):
        llamada()


def test_resumen_en_ingles():
    r = pp.capability_analysis(X, LSL, USL, ci_method="bootstrap", n_boot=200, seed=1)
    with pp.language("en"):
        assert "bootstrap" in r.summary() and "resamples" in r.summary()
