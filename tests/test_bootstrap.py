"""Bootstrap (percentil y BCa): contra scipy.stats.bootstrap, fórmulas manuales y cobertura simulada."""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

import pccpy as pp
from pccpy.bootstrap import _bca_alfas

X = np.random.default_rng(1).lognormal(0, 1, 60)


@pytest.mark.parametrize("metodo, scipy_metodo", [("bca", "BCa"), ("percentile", "percentile")])
def test_coincide_con_scipy(metodo, scipy_metodo):
    r = pp.bootstrap_ci(X, np.mean, method=metodo, seed=3, n_boot=20000, vectorized=True)
    ref = stats.bootstrap((X,), np.mean, confidence_level=0.95, n_resamples=20000, method=scipy_metodo,
                          random_state=3).confidence_interval
    ancho = ref.high - ref.low
    assert r.ci[0] == pytest.approx(ref.low, abs=0.03 * ancho)  # error de Monte Carlo
    assert r.ci[1] == pytest.approx(ref.high, abs=0.03 * ancho)
    assert r.estimate == pytest.approx(X.mean())


def test_bca_formula_manual_con_los_mismos_remuestreos():
    """Las fórmulas de z0, aceleración y cuantiles ajustados se recalculan aparte con los mismos datos."""
    rng = np.random.default_rng(5)
    reps = rng.normal(2.0, 0.5, (4000, 1)) ** 2
    x = X[:15]
    theta = np.array([x.mean()])
    jack = np.array([[np.delete(x, i).mean()] for i in range(len(x))])
    bajo, alto = _bca_alfas(theta, reps, jack, 0.05)
    # cálculo manual
    prop = np.mean(reps[:, 0] < theta[0]) + 0.5 * np.mean(reps[:, 0] == theta[0])
    z0 = stats.norm.ppf(prop)
    d = jack[:, 0].mean() - jack[:, 0]
    a = (d ** 3).sum() / (6 * ((d ** 2).sum()) ** 1.5)
    esperado = [stats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z))) for z in stats.norm.ppf([0.025, 0.975])]
    assert (bajo[0], alto[0]) == pytest.approx(esperado)


def test_reproducible_y_semillas_distintas():
    a = pp.bootstrap_ci(X, np.mean, seed=7).ci
    assert a == pp.bootstrap_ci(X, np.mean, seed=7).ci
    assert a != pp.bootstrap_ci(X, np.mean, seed=8).ci


def test_estadistica_vectorial_comparte_remuestreos():
    r = pp.bootstrap_ci(X, lambda v: np.array([v.mean(), v.std(ddof=1)]), seed=2)
    lo, hi = r.ci
    assert lo.shape == hi.shape == (2,) and np.all(lo < r.estimate) and np.all(r.estimate < hi)
    solo = pp.bootstrap_ci(X, lambda v: v.mean(), seed=2)
    assert solo.ci[0] == pytest.approx(lo[0]) and solo.ci[1] == pytest.approx(hi[0])
    assert list(r.to_frame(stable=True).columns) == ["estimate", "lower", "upper"]


def test_vectorizada_igual_que_no_vectorizada():
    a = pp.bootstrap_ci(X, np.mean, seed=4, vectorized=True).ci
    b = pp.bootstrap_ci(X, np.mean, seed=4).ci
    assert a == pytest.approx(b)


def _sd(v, axis=-1):
    return np.std(v, axis=axis, ddof=1)


def test_cobertura_de_sigma_con_datos_asimetricos_mejora_la_de_chi_cuadrado():
    """Desviación estándar de una gamma(2) con n = 60: el intervalo chi-cuadrado pierde cobertura, BCa mucho menos."""
    rng = np.random.default_rng(11)
    n, rep, verdadera = 60, 300, np.sqrt(2.0)
    cubre_bca = cubre_chi2 = 0
    for _ in range(rep):
        m = rng.gamma(2.0, 1.0, n)
        lo, hi = pp.bootstrap_ci(m, _sd, vectorized=True, n_boot=600, seed=int(rng.integers(1 << 30))).ci
        cubre_bca += lo <= verdadera <= hi
        s = m.std(ddof=1)
        inf = s * np.sqrt((n - 1) / stats.chi2.ppf(0.975, n - 1))
        sup = s * np.sqrt((n - 1) / stats.chi2.ppf(0.025, n - 1))
        cubre_chi2 += inf <= verdadera <= sup
    assert cubre_bca / rep >= 0.88
    assert cubre_bca / rep > cubre_chi2 / rep + 0.05  # medido: ≈ 0,92 frente a ≈ 0,83


def test_cobertura_de_la_media_es_razonable_con_datos_asimetricos():
    """Para la media el intervalo t ya aguanta bastante (TCL): BCa queda en una cobertura comparable, no mejor."""
    rng = np.random.default_rng(12)
    n, rep, verdadera = 60, 300, 2.0
    cubre = 0
    for _ in range(rep):
        m = rng.gamma(2.0, 1.0, n)
        lo, hi = pp.bootstrap_ci(m, np.mean, vectorized=True, n_boot=600, seed=int(rng.integers(1 << 30))).ci
        cubre += lo <= verdadera <= hi
    assert cubre / rep >= 0.88


def test_avisos():
    with pytest.warns(UserWarning, match="cautela"):
        pp.bootstrap_ci(X[:10], np.mean, seed=1)
    with pytest.warns(UserWarning, match="degenerada"):
        r = pp.bootstrap_ci(np.full(30, 2.0), np.mean, seed=1)
    assert r.ci == (2.0, 2.0)
    with pytest.warns(UserWarning, match="no fue finita"):
        pp.bootstrap_ci(X, lambda v: np.nan if v[0] > 2 else v.mean(), seed=1)


def test_bca_degrada_a_percentil_con_aviso():
    # un estimador que cae siempre por encima de todos los remuestreos: z0 infinito
    base = X.copy()
    with pytest.warns(UserWarning, match="BCa no se puede"):
        r = pp.bootstrap_ci(base, lambda v: float(v.max()) if v is not base else 1e9, seed=1, n_boot=200)
    assert r.method == "bca/percentile"


@pytest.mark.parametrize("kw, error", [
    (dict(method="x"), "method"), (dict(confidence=1), "confidence"), (dict(confidence=0), "confidence"),
    (dict(n_boot=10), "n_boot"), (dict(n_boot=500.5), "n_boot"),
])
def test_errores_de_parametros(kw, error):
    with pytest.raises(ValueError, match=error):
        pp.bootstrap_ci(X, np.mean, **kw)


def test_errores_de_entrada():
    with pytest.raises(TypeError, match="statistic"):
        pp.bootstrap_ci(X, 3)
    with pytest.raises(ValueError, match="al menos 2"):
        pp.bootstrap_ci([1.0], np.mean)
    with pytest.raises(ValueError, match="mismo número"):
        calls = {"n": 0}

        def mal(v):
            calls["n"] += 1
            return np.array([1.0]) if calls["n"] == 1 else np.array([1.0, 2.0])

        pp.bootstrap_ci(X, mal, seed=1)
    with pytest.raises(ValueError, match="válidos"):
        pp.bootstrap_ci(X, lambda v: np.nan if v is not X else 1.0, seed=1)


def test_resumen_es_en():
    r = pp.bootstrap_ci(X, np.mean, seed=1, vectorized=True)
    assert "Intervalo bootstrap" in r.summary()
    with pp.language("en"):
        assert "Bootstrap interval" in r.summary()
        assert r.to_frame().columns[0] == "estimate"
    assert r.to_frame().columns[0] == "estimación"
