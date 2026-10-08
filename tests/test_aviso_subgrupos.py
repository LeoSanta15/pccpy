"""Aviso con subgrupos pequeños y datos asimétricos (cartas Xbar-R/S y capacidad)."""
from __future__ import annotations

import warnings

import numpy as np
import pytest

import pccpy as pp

RNG = np.random.default_rng(0)
ASIMETRICOS = RNG.exponential(2.0, (30, 4))
NORMALES = np.random.default_rng(1).normal(10, 1, (30, 4))
GRANDES = np.random.default_rng(2).exponential(2.0, (30, 8))


@pytest.mark.parametrize("carta", [pp.xbar_r_chart, pp.xbar_s_chart])
def test_cartas_avisan_con_subgrupos_pequenos_y_asimetria(carta):
    with pytest.warns(UserWarning, match="subgrupos pequeños") as w:
        carta(ASIMETRICOS)
    assert "falsas alarmas" in str(w[0].message) and "diagnose()" in str(w[0].message)
    assert w[0].filename.endswith("test_aviso_subgrupos.py")  # apunta al código del usuario


def test_capacidad_avisa_y_menciona_las_alternativas():
    with pytest.warns(UserWarning, match="capability_nonnormal"):
        pp.capability_analysis(ASIMETRICOS, 0.0, 20.0)
    with pytest.warns(UserWarning, match="bootstrap"):
        pp.capability_analysis(ASIMETRICOS, 0.0, 20.0)


def test_subgrupos_1d_con_subgroup_size_tambien_avisan():
    with pytest.warns(UserWarning, match="subgrupos pequeños"):
        pp.xbar_r_chart(ASIMETRICOS.ravel(), subgroup_size=4)


@pytest.mark.parametrize("llamada", [
    lambda: pp.xbar_r_chart(NORMALES),                      # datos normales
    lambda: pp.xbar_r_chart(GRANDES),                       # subgrupos de 8: el TCL ya ayuda
    lambda: pp.xbar_s_chart(GRANDES),
    lambda: pp.capability_analysis(NORMALES, 5.0, 15.0),
    lambda: pp.capability_analysis(GRANDES, 0.0, 20.0),
    lambda: pp.imr_chart(ASIMETRICOS.ravel()),              # individuales: no es el caso de este aviso
    lambda: pp.capability_analysis(ASIMETRICOS.ravel(), 0.0, 20.0),
])
def test_sin_aviso_en_los_demas_casos(llamada):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        llamada()


def test_pocos_datos_o_asimetria_leve_no_avisan():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pp.xbar_r_chart(ASIMETRICOS[:4])  # 16 observaciones: muy pocas para juzgar la forma
        leve = np.random.default_rng(3).gamma(30, 1, (30, 4))  # asimetría ≈ 0,37
        pp.xbar_r_chart(leve)


def test_el_aviso_no_cambia_el_resultado():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = pp.xbar_r_chart(ASIMETRICOS)
    assert a["Xbar"].ucl[0] > a["Xbar"].center[0] > a["Xbar"].lcl[0]


def test_aviso_en_ingles():
    with pp.language("en"), pytest.warns(UserWarning, match="small subgroups"):
        pp.xbar_r_chart(ASIMETRICOS)
