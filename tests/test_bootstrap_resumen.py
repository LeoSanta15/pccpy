"""bootstrap_summary: media, mediana y desviación estándar con intervalos bootstrap y clásicos de referencia."""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

import pccpy as pp

X = np.random.default_rng(1).gamma(2, 1, 60)


def test_estimaciones_y_bootstrap_coinciden_con_el_calculo_manual_con_los_mismos_remuestreos():
    r = pp.bootstrap_summary(X, n_boot=500, seed=3)
    assert r.estimate == pytest.approx([X.mean(), np.median(X), X.std(ddof=1)])

    def manual(m):
        return np.array([np.mean(m), np.median(m), np.std(m, ddof=1)])

    ref = pp.bootstrap_ci(X, manual, n_boot=500, seed=3)  # sin vectorizar: bucle sobre cada remuestreo
    assert r.lower == pytest.approx(ref.ci[0]) and r.upper == pytest.approx(ref.ci[1])
    assert r.ci("median") == pytest.approx((ref.ci[0][1], ref.ci[1][1]))


def test_intervalos_clasicos_de_media_y_sigma():
    r = pp.bootstrap_summary(X, n_boot=300, seed=1)
    n, m, s = X.size, X.mean(), X.std(ddof=1)
    lo, hi = stats.t.interval(0.95, n - 1, loc=m, scale=s / np.sqrt(n))
    assert (r.classic_lower[0], r.classic_upper[0]) == pytest.approx((lo, hi))
    assert r.classic_lower[2] == pytest.approx(np.sqrt((n - 1) * s**2 / stats.chi2.ppf(0.975, n - 1)))
    assert r.classic_upper[2] == pytest.approx(np.sqrt((n - 1) * s**2 / stats.chi2.ppf(0.025, n - 1)))


@pytest.mark.parametrize("n, confianza", [(12, 0.9), (30, 0.95), (60, 0.95), (101, 0.99)])
def test_intervalo_de_la_mediana_por_estadisticos_de_orden(n, confianza):
    x = np.random.default_rng(n).normal(0, 1, n)
    xs = np.sort(x)
    r = pp.bootstrap_summary(x, n_boot=200, confidence=confianza, seed=1)
    lo, hi = r.classic_lower[1], r.classic_upper[1]
    k = int(np.where(xs == lo)[0][0]) + 1  # posición del límite inferior (base 1)
    assert hi == xs[n - k]  # simétrico: x_(k) y x_(n+1−k)
    cobertura = lambda j: 1 - 2 * stats.binom.cdf(j - 1, n, 0.5)  # noqa: E731 - cobertura exacta del par (x_(j), x_(n+1-j))
    assert cobertura(k) >= confianza  # cubre al menos lo pedido…
    assert cobertura(k + 1) < confianza  # …y es el más estrecho que lo consigue


def test_tabla_resumen_y_traduccion():
    r = pp.bootstrap_summary(X, n_boot=200, seed=2)
    estable = r.to_frame(stable=True)
    assert list(estable.index) == ["mean", "median", "std"]
    assert list(estable.columns) == ["estimate", "lower", "upper", "classic_lower", "classic_upper"]
    assert list(r.to_frame().index) == ["Media", "Mediana", "Desv.Est."]
    assert "bootstrap bca" in r.summary() and "clásico" in r.summary()
    with pp.language("en"):
        assert list(r.to_frame().index) == ["Mean", "Median", "Std.Dev."]
        assert "classic" in r.summary()


def test_reproducible_y_errores_heredados():
    assert pp.bootstrap_summary(X, n_boot=200, seed=4).lower.tolist() == pp.bootstrap_summary(X, n_boot=200, seed=4).lower.tolist()
    with pytest.raises(ValueError, match="method"):
        pp.bootstrap_summary(X, method="x")
    with pytest.raises(ValueError, match="confidence"):
        pp.bootstrap_summary(X, confidence=1.0)
    with pytest.warns(UserWarning, match="cautela"):
        pp.bootstrap_summary(X[:10], n_boot=200, seed=1)


def test_cobertura_de_la_desviacion_estandar_con_datos_asimetricos():
    """gamma(2), n = 60: el intervalo clásico de sigma subcubre; el bootstrap se acerca más al 95 %."""
    rng = np.random.default_rng(11)
    boot = clas = 0
    rep = 250
    for _ in range(rep):
        r = pp.bootstrap_summary(rng.gamma(2, 1, 60), n_boot=400, seed=int(rng.integers(1 << 30)))
        boot += r.lower[2] <= np.sqrt(2) <= r.upper[2]
        clas += r.classic_lower[2] <= np.sqrt(2) <= r.classic_upper[2]
    assert boot / rep >= 0.88 and boot / rep > clas / rep + 0.04
