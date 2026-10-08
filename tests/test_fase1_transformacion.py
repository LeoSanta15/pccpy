"""Fase I con ``transform=``: la transformación se reajusta en cada pasada y se congela para la Fase II."""
import numpy as np
import pytest

import pccpy as pp
from pccpy import phase1
from pccpy.transforms import Transformation

pytestmark = pytest.mark.filterwarnings("ignore:La transformación cambió mucho")


def _datos(seed=7, n=90, contaminados=(12, 47)):
    x = np.random.default_rng(seed).gamma(4.0, 2.0, n) + 1.0
    x[list(contaminados)] *= 8.0
    return x


def test_reajusta_en_cada_pasada_y_congela_la_ultima():
    r = pp.phase_one(pp.imr_chart, _datos(), transform="boxcox", tests=(1,))
    assert r.excluded.size >= 1 and len(r.history) >= 2
    ts = [h.transformation for h in r.history]
    assert all(isinstance(t, Transformation) for t in ts)
    # al quitar puntos con causa especial, lambda cambia de una pasada a otra
    assert ts[0].params["lambda"] != ts[-1].params["lambda"]
    assert r.transformation is ts[-1]
    assert r.chart.transformation is r.transformation


def test_equivale_a_transformar_antes_con_una_transformacion_fija():
    x = _datos()
    t = pp.fit_transformation(x, "yeo-johnson")
    a = pp.phase_one(pp.imr_chart, x, transform=t, scale="transformed", tests=(1,))
    b = pp.phase_one(pp.imr_chart, t.forward(x), tests=(1,))
    np.testing.assert_array_equal(a.excluded, b.excluded)
    assert a.limits["mu"] == pytest.approx(b.limits["mu"])
    assert a.limits["sigma"] == pytest.approx(b.limits["sigma"])
    assert all(h.transformation is t for h in a.history)  # una Transformation dada no se reajusta


def test_fase2_aplica_la_transformacion_congelada_sin_reajustar():
    rng = np.random.default_rng(1)
    r = pp.phase_one(pp.imr_chart, _datos(), transform="boxcox", tests=(1,))
    nuevos = rng.gamma(9.0, 5.0, 30) + 1.0  # otra distribución: un reajuste daría otro lambda
    c = r.phase2(nuevos)
    assert c.transformation.params == r.transformation.params
    mu, sigma = r.limits["mu"], r.limits["sigma"]
    esperado = r.transformation.inverse(mu + 3 * sigma)
    assert c.panels[0].ucl[0] == pytest.approx(esperado)  # límite en escala original, asimétrico


def test_subgrupos_y_yeo_johnson_con_negativos():
    rng = np.random.default_rng(2)
    x = rng.gamma(3.0, 1.0, 120) - 2.0  # con negativos: Box-Cox no aplica
    r = pp.phase_one(pp.xbar_r_chart, x, transform="yeo-johnson", subgroup_size=4, tests=(1,))
    assert r.transformation.method == "yeo-johnson"
    assert r.phase2(rng.gamma(3.0, 1.0, 20) - 2.0, subgroup_size=4).transformation.params == r.transformation.params


def test_boxcox_con_datos_no_positivos_falla_desde_la_primera_pasada():
    x = np.random.default_rng(3).normal(0, 1, 40)
    with pytest.raises(ValueError, match="Box-Cox"):
        pp.phase_one(pp.imr_chart, x, transform="boxcox", tests=(1,))


def test_transform_solo_en_cartas_de_variables():
    with pytest.raises(ValueError, match="transform"):
        pp.phase_one(pp.c_chart, np.arange(30) % 5 + 1, transform="boxcox")


def test_sin_transform_el_resultado_no_cambia():
    x = _datos()
    r = pp.phase_one(pp.imr_chart, x, tests=(1,))
    assert r.transformation is None and all(h.transformation is None for h in r.history)
    assert "Transformación" not in r.summary()


def _falla_en_la_segunda(monkeypatch):
    original = phase1.fit_transformation
    llamadas = []

    def falso(datos, metodo):
        llamadas.append(1)
        if len(llamadas) > 1:
            raise ValueError("no se pudo ajustar")
        return original(datos, metodo)

    monkeypatch.setattr(phase1, "fit_transformation", falso)


def test_si_no_se_puede_reajustar_se_detiene_con_la_carta_actual(monkeypatch):
    _falla_en_la_segunda(monkeypatch)
    with pytest.warns(UserWarning, match="no convergió"):
        r = pp.phase_one(pp.imr_chart, _datos(), transform="boxcox", tests=(1,))
    assert r.reason == "transform_failed" and not r.converged
    assert r.excluded.size == 0 and r.chart.transformation is r.transformation


@pytest.mark.filterwarnings("default")
def test_avisa_si_lambda_cambia_mucho(monkeypatch):
    lambdas = iter([0.0, 1.0, 1.0, 1.0, 1.0])

    def falso(datos, metodo):
        return Transformation("boxcox", {"lambda": next(lambdas)})

    monkeypatch.setattr(phase1, "fit_transformation", falso)
    with pytest.warns(UserWarning, match="Fase I no es estable"):
        pp.phase_one(pp.imr_chart, _datos(), transform="boxcox", tests=(1,))
