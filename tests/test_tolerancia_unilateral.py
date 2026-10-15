# Trazabilidad: S001-RF-01, S001-RF-02, S001-RF-03 (spec 001).
"""Especificación 001: tolerancia no paramétrica unilateral con la cota más ajustada que cumple la confianza."""
import numpy as np
import pytest
from scipy import stats

import pccpy as pp


def _cola(n, r, p):
    """P(Bin(n, 1 − p) ≥ r): confianza de que X_(r) deje al menos la cobertura p por encima (referencia independiente)."""
    return float(stats.binom.sf(r - 1, n, 1 - p))


def test_s001_rf_01_la_cota_inferior_usa_el_mayor_r_que_cumple():
    x = np.random.default_rng(1).normal(size=300)
    r = pp.tolerance_interval(x, coverage=0.95, confidence=0.95, method="nonparametric", sides="lower")
    assert r.lower == np.sort(x)[8] and r.upper is None  # r = 9
    assert r.achieved_confidence == pytest.approx(_cola(300, 9, 0.95), abs=1e-12)
    assert r.achieved_confidence == pytest.approx(0.96593, abs=1e-5)


def test_s001_rf_01_la_cota_superior_usa_el_mismo_indice():
    x = np.random.default_rng(1).normal(size=300)
    r = pp.tolerance_interval(x, coverage=0.95, confidence=0.95, method="nonparametric", sides="upper")
    assert r.upper == np.sort(x)[300 - 9] and r.lower is None
    assert r.achieved_confidence == pytest.approx(0.96593, abs=1e-5)


@pytest.mark.parametrize("n", [100, 300, 1000])
def test_s001_rf_01_ningun_r_mayor_cumple_la_confianza(n):
    x = np.random.default_rng(2).normal(size=n)
    res = pp.tolerance_interval(x, coverage=0.9, confidence=0.9, method="nonparametric", sides="lower")
    r = int(np.searchsorted(np.sort(x), res.lower) + 1)
    assert _cola(n, r, 0.9) >= 0.9 > _cola(n, r + 1, 0.9)


def test_s001_rf_02_la_confianza_declarada_se_cumple_en_simulacion():
    rng = np.random.default_rng(3)
    n, p, conf = 100, 0.9, 0.9
    muestras = rng.normal(size=(20_000, n))
    declarada = pp.tolerance_interval(muestras[0], coverage=p, confidence=conf, method="nonparametric",
                                      sides="lower").achieved_confidence
    xs = np.sort(muestras, axis=1)
    r = int(np.searchsorted(xs[0], pp.tolerance_interval(muestras[0], coverage=p, confidence=conf,
                                                          method="nonparametric", sides="lower").lower) + 1)
    cobertura = 1 - stats.norm.cdf(xs[:, r - 1])  # población por encima de la cota X_(r) de cada réplica
    assert (cobertura >= p).mean() == pytest.approx(declarada, abs=0.01)


def test_s001_rf_03_el_tamano_minimo_no_cambia():
    rng = np.random.default_rng(4)
    for lado in ("lower", "upper"):
        with pytest.raises(ValueError):
            pp.tolerance_interval(rng.normal(size=58), coverage=0.95, confidence=0.95, method="nonparametric", sides=lado)
        r = pp.tolerance_interval(rng.normal(size=59), coverage=0.95, confidence=0.95, method="nonparametric", sides=lado)
        assert r.achieved_confidence == pytest.approx(_cola(59, 1, 0.95), abs=1e-12)
