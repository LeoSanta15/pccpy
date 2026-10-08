"""``PhaseOneResult.to_dict`` / ``from_dict``: la Fase II tras guardar y cargar es idéntica a la original."""
import json

import numpy as np
import pytest

import pccpy as pp

pytestmark = pytest.mark.filterwarnings("ignore:Con subgrupos pequeños")


def _ida_y_vuelta(r):
    return pp.PhaseOneResult.from_dict(json.loads(json.dumps(r.to_dict())))


def _igual(a, b):
    assert len(a.panels) == len(b.panels)
    for pa, pb in zip(a.panels, b.panels):
        for campo in ("values", "center", "ucl", "lcl"):
            np.testing.assert_array_equal(getattr(pa, campo), getattr(pb, campo))
        assert {k: list(v) for k, v in pa.violations.items()} == {k: list(v) for k, v in pb.violations.items()}


def _casos():
    rng = np.random.default_rng(6)
    x = rng.normal(50, 2, 60)
    x[[10, 33]] += 14
    g = rng.normal(50, 2, 120)
    g[8] += 15
    b = rng.binomial(200, 0.05, 40)
    b[9] = 70
    c = rng.poisson(6, 40)
    c[9] = 40
    return [
        ("imr", pp.imr_chart, x, {"tests": (1, 2)}, {}),
        ("xbar_r", pp.xbar_r_chart, g, {"subgroup_size": 4, "tests": (1,)}, {"subgroup_size": 4}),
        ("xbar_s", pp.xbar_s_chart, g, {"subgroup_size": 4, "tests": (1,)}, {"subgroup_size": 4}),
        ("p", pp.p_chart, b, {"n": np.full(40, 200)}, {"n": np.full(10, 200)}),
        ("np", pp.np_chart, b, {"n": 200}, {"n": 200}),
        ("c", pp.c_chart, c, {}, {}),
        ("u", pp.u_chart, c, {"n": 2.0}, {"n": 2.0}),
    ]


@pytest.mark.parametrize("caso", _casos(), ids=lambda c: c[0])
def test_la_fase2_tras_guardar_y_cargar_es_identica(caso):
    _, funcion, datos, kw1, kw2 = caso
    r = pp.phase_one(funcion, datos, **kw1)
    cargado = _ida_y_vuelta(r)
    nuevos = datos[:10] if np.ndim(kw2.get("n", 0)) > 0 else datos[:40]
    _igual(r.phase2(nuevos, **kw2), cargado.phase2(nuevos, **kw2))
    assert cargado.limits == r.limits and cargado.converged == r.converged and cargado.reason == r.reason
    np.testing.assert_array_equal(cargado.excluded, r.excluded)
    np.testing.assert_array_equal(cargado.kept, r.kept)
    assert [h.n_points for h in cargado.history] == [h.n_points for h in r.history]


@pytest.mark.parametrize("metodo", ["boxcox", "yeo-johnson", "johnson"])
def test_con_transformacion_se_restaura_con_sus_parametros(metodo):
    x = np.random.default_rng(7).gamma(4.0, 2.0, 90) + 1.0
    r = pp.phase_one(pp.imr_chart, x, transform=metodo, tests=(1,))
    cargado = _ida_y_vuelta(r)
    assert cargado.transformation.params == r.transformation.params
    nuevos = np.random.default_rng(2).gamma(4.0, 2.0, 20) + 1.0
    _igual(r.phase2(nuevos), cargado.phase2(nuevos))
    assert cargado.to_frame(stable=True).equals(r.to_frame(stable=True))


def test_el_resultado_cargado_no_tiene_carta_pero_resume_y_avisa_al_dibujar():
    x = np.random.default_rng(1).normal(0, 1, 40)
    cargado = _ida_y_vuelta(pp.phase_one(pp.imr_chart, x, tests=(1,)))
    assert cargado.chart is None and "Fase I" in cargado.summary()
    with pytest.raises(ValueError, match="from_dict"):
        cargado.plot()


def test_el_diccionario_es_json_con_nan_como_null():
    x = np.random.default_rng(1).poisson(5, 40)
    d = pp.phase_one(pp.c_chart, x).to_dict()
    texto = json.dumps(d, allow_nan=False)  # falla si quedara algún NaN o inf
    assert json.loads(texto)["chart"] == "c_chart"
    cargado = pp.PhaseOneResult.from_dict(json.loads(texto))
    assert all(np.isnan(h.sigma) for h in cargado.history)


def test_argumentos_que_no_se_pueden_guardar_dan_un_error_que_dice_cual():
    x = np.random.default_rng(1).normal(0, 1, 40)
    r = pp.phase_one(pp.imr_chart, x, tests=(1,))
    r._argumentos["raro"] = lambda: 1
    with pytest.raises(ValueError, match="raro"):
        r.to_dict()


def test_from_dict_valida_esquema_carta_y_limites():
    x = np.random.default_rng(1).normal(0, 1, 40)
    d = pp.phase_one(pp.imr_chart, x, tests=(1,)).to_dict()
    with pytest.raises(ValueError, match="to_dict"):
        pp.PhaseOneResult.from_dict({"otra": 1})
    with pytest.raises(ValueError, match="versión más nueva"):
        pp.PhaseOneResult.from_dict({**d, "schema": 99})
    with pytest.raises(ValueError, match="no está soportada"):
        pp.PhaseOneResult.from_dict({**d, "chart": "ewma_chart"})
    with pytest.raises(ValueError, match="no corresponden"):
        pp.PhaseOneResult.from_dict({**d, "limits": {"p": 0.1}})
    with pytest.raises(ValueError, match="no corresponden"):
        pp.PhaseOneResult.from_dict({**d, "limits": {"mu": float("nan"), "sigma": 1.0}})
    with pytest.raises(ValueError, match="transform"):
        pp.PhaseOneResult.from_dict({**d, "chart": "c_chart", "limits": {"c": 5.0},
                                     "transformation": {"method": "boxcox", "lambda": 0.5}})
