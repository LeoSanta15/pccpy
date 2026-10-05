"""Muestreo de aceptación: validaciones, planes personalizados, evaluación de muestras y Dodge-Romig."""
from __future__ import annotations

import math

import matplotlib
import numpy as np
import pytest
from scipy import stats

import pccpy as pp

matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def _cerrar():
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


def test_atributos_validaciones():
    with pytest.raises(ValueError, match="N debe"):
        pp.acceptance_sampling_attributes(N=1, aql=1.0)
    for aql in (0, -1, 11):
        with pytest.raises(ValueError, match="aql"):
            pp.acceptance_sampling_attributes(N=100, aql=aql)


def test_atributos_plan_personalizado_y_probabilidad_binomial():
    plan = pp.acceptance_sampling_attributes(N=500, aql=1.0, n=50, c=1)
    assert plan.method == "custom" and (plan.n, plan.c) == (50, 1)
    for p in (0.005, 0.02, 0.1):
        assert plan.pa(p) == pytest.approx(stats.binom.cdf(1, 50, p))
    assert plan.alpha == pytest.approx(1 - stats.binom.cdf(1, 50, 0.01), abs=5e-3)
    assert plan.pa(plan.ltpd) == pytest.approx(0.10, abs=0.01)


@pytest.mark.parametrize("nivel", [1, 2, 3])
def test_niveles_de_inspeccion_dan_muestras_crecientes(nivel):
    n = {i: pp.acceptance_sampling_attributes(N=1000, aql=1.0, inspection_level=i).n for i in (1, 2, 3)}
    assert n[1] <= n[2] <= n[3] and n[nivel] > 0


def test_guardar_graficos(tmp_path):
    pp.acceptance_sampling_attributes(N=1000, aql=1.0).save_plot(str(tmp_path / "a.png"))
    pp.acceptance_sampling_variables(N=1000, aql=1.0).save_plot(str(tmp_path / "v.png"))
    pp.dodge_romig(N=1000, ltpd=0.05).save_plot(str(tmp_path / "d.png"))
    assert len(list(tmp_path.glob("*.png"))) == 3


def test_variables_validaciones_y_plan_personalizado():
    with pytest.raises(ValueError, match="N debe"):
        pp.acceptance_sampling_variables(N=1, aql=1.0)
    with pytest.raises(ValueError, match="aql"):
        pp.acceptance_sampling_variables(N=100, aql=0)
    with pytest.raises(ValueError, match="spec_type"):
        pp.acceptance_sampling_variables(N=100, aql=1.0, spec_type="tres")
    plan = pp.acceptance_sampling_variables(N=500, aql=1.0, n=20, k=1.8)
    assert plan.method == "custom" and (plan.n, plan.k) == (20, 1.8)
    assert 0 < plan.alpha < 1 and 0.01 < plan.ltpd < 1


def test_variables_evalua_la_muestra_con_formulas_manuales():
    plan = pp.acceptance_sampling_variables(N=500, aql=1.0, n=10, k=1.5)
    x = np.array([10.1, 10.0, 9.9, 10.2, 10.05, 9.95, 10.0, 10.1, 9.9, 10.0])
    xbar, s = x.mean(), x.std(ddof=1)
    r = plan.evaluate(x, usl=10.6)
    assert r["Q_usl"] == pytest.approx((10.6 - xbar) / s) and bool(r["accept"])
    assert plan.evaluate(x, usl=10.1)["accept"] == ((10.1 - xbar) / s >= 1.5)
    assert plan.evaluate(x, lsl=9.4)["Q_lsl"] == pytest.approx((xbar - 9.4) / s)
    bilateral = pp.acceptance_sampling_variables(N=500, aql=1.0, spec_type="two", n=10, k=1.5)
    rb = bilateral.evaluate(x, usl=10.6, lsl=9.4)
    assert rb["accept"] == ((10.6 - xbar) / s >= 1.5 and (xbar - 9.4) / s >= 1.5) and "vs k" in rb["criterion"]
    constante = plan.evaluate(np.full(5, 10.0), usl=11.0)  # s = 0
    assert math.isinf(constante["Q_usl"]) and constante["accept"]


def test_variables_bilateral_es_el_producto_de_dos_unilaterales():
    uni = pp.acceptance_sampling_variables(N=500, aql=1.0, n=20, k=1.7)
    bi = pp.acceptance_sampling_variables(N=500, aql=1.0, spec_type="two", n=20, k=1.7)
    assert bi.pa(0.02) == pytest.approx(uni.pa(0.01) ** 2)
    assert uni.pa(0) == 1.0 and uni.pa(1) == 0.0


def test_variables_niveles_de_inspeccion():
    assert pp.acceptance_sampling_variables(N=1000, aql=1.0, inspection_level=1).method == "z1.9"
    # la tabla Z1.9 incluida es simplificada: una combinación que no trae se rechaza con un mensaje claro
    with pytest.raises(ValueError, match="no disponible"):
        pp.acceptance_sampling_variables(N=1000, aql=1.0, inspection_level=3)


def test_dodge_romig_validaciones():
    with pytest.raises(ValueError, match="exactamente"):
        pp.dodge_romig(N=500)
    with pytest.raises(ValueError, match="exactamente"):
        pp.dodge_romig(N=500, ltpd=0.05, aoql=0.01)
    with pytest.raises(ValueError, match="N debe"):
        pp.dodge_romig(N=1, ltpd=0.05)
    with pytest.raises(ValueError, match="process_avg"):
        pp.dodge_romig(N=500, ltpd=0.05, process_avg=0)
    with pytest.raises(ValueError, match="ltpd"):
        pp.dodge_romig(N=500, ltpd=1.5)
    with pytest.raises(ValueError, match="aoql"):
        pp.dodge_romig(N=500, aoql=0)


def test_dodge_romig_cumple_su_objetivo():
    ltpd = pp.dodge_romig(N=1000, ltpd=0.05, process_avg=0.01)
    assert ltpd.plan_type == "LTPD" and stats.binom.cdf(ltpd.c, ltpd.n, 0.05) <= 0.10 + 1e-9
    aoql = pp.dodge_romig(N=1000, aoql=0.02, process_avg=0.01)
    assert aoql.plan_type == "AOQL" and aoql.aoql <= 0.02 * 1.05 + 1e-6
    assert ltpd.pa(0.01) == pytest.approx(stats.binom.cdf(ltpd.c, ltpd.n, 0.01))
    assert not ltpd.oc_curve().empty and str(ltpd.n) in ltpd.summary()
