"""Fase 3b de i18n: pareto, curvas OC/AOQ, tablas ANOVA, kappa y hojas de Excel.

La referencia en español (``tests/golden/i18n_tablas_es.json``) se generó con el código **anterior** a la fase 3b.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import _corpus_i18n as corpus
import matplotlib.pyplot as plt
import numpy as np
import pytest

import pccpy

TABLAS_ES = json.loads((Path(__file__).parent / "golden" / "i18n_tablas_es.json").read_text(encoding="utf-8"))
_CACHE: dict = {}


def _tablas(lang: str) -> dict:
    if lang not in _CACHE:
        with pccpy.language(lang):
            _CACHE[lang] = corpus.tablas_sueltas()
    return _CACHE[lang]


@pytest.mark.parametrize("nombre", sorted(TABLAS_ES))
def test_el_espanol_de_las_tablas_no_cambia(nombre):
    assert _tablas("es")[nombre] == TABLAS_ES[nombre]


def test_las_tablas_del_corpus_son_las_de_la_referencia():
    assert sorted(_tablas("es")) == sorted(TABLAS_ES)


ESPANOL = frozenset(
    "categoría conteo porcentaje acumulado fuente partes operadores operador repetibilidad otros acuerdo defectivo "
    "aceptar resumen plan linealidad estadístico valor".split()
)


def _palabras(texto) -> set[str]:
    return {p.lower() for p in re.findall(r"[A-Za-zÁ-ú]+", str(texto))} & ESPANOL


@pytest.mark.parametrize("nombre", sorted(TABLAS_ES))
def test_las_cabeceras_en_ingles_no_tienen_palabras_en_espanol(nombre):
    t = _tablas("en")[nombre]
    etiquetas = [t["index_name"], *t["columns"]] + ([str(i) for i in t["index"]] if nombre.startswith("anova") else [])
    assert all(not _palabras(e) for e in etiquetas), etiquetas


@pytest.mark.parametrize("nombre", sorted(TABLAS_ES))
def test_es_y_en_tienen_la_misma_forma_y_los_mismos_numeros(nombre):
    es, en = _tablas("es")[nombre], _tablas("en")[nombre]
    assert len(es["columns"]) == len(en["columns"]) and len(es["index"]) == len(en["index"])
    if nombre in ("pareto_con_otros",) or nombre.startswith("excel_"):
        return  # contienen etiquetas de datos o de hojas traducidas
    assert es["data"] == en["data"]


def _hojas(lang: str, que: str) -> list[str]:
    import tempfile

    import pandas as pd

    datos = corpus._msa_datos()[0]
    with pccpy.language(lang), tempfile.TemporaryDirectory() as tmp:
        if que == "gage_rr":
            res = pccpy.gage_rr(datos, parts=10, operators=3, replicates=2)
        else:
            res = pccpy.attribute_agreement(corpus._desde_df_atributos()[0], reference=corpus._desde_df_atributos()[1], replicates=2)
        res.to_excel(f"{tmp}/x.xlsx")
        return list(pd.read_excel(f"{tmp}/x.xlsx", sheet_name=None))


def test_las_hojas_de_excel_se_traducen():
    assert _hojas("en", "gage_rr") == ["Summary", "ANOVA"]
    assert _hojas("es", "gage_rr") == ["Resumen", "ANOVA"]
    assert _hojas("en", "acuerdo") == ["Summary", "KappaVsReference"]
    assert _hojas("es", "acuerdo") == ["Resumen", "KappaVsReferencia"]


def test_pareto_agrupa_otros_con_el_nombre_del_idioma_activo():
    with pccpy.language("en"):
        assert "Other" in pccpy.pareto(["x", "y", "z", "w"], [50, 30, 3, 2], other_below=5).iloc[:, 0].tolist()
    assert "Otros" in pccpy.pareto(["x", "y", "z", "w"], [50, 30, 3, 2], other_below=5).iloc[:, 0].tolist()


# ── claves estables ──────────────────────────────────────────────────────────

def _objetos():
    atr = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    var = pccpy.acceptance_sampling_variables(N=1000, aql=1.0)
    dr = pccpy.dodge_romig(N=1000, ltpd=0.05, process_avg=0.01)
    datos = corpus._msa_datos()[0]
    cruzado = pccpy.gage_rr(datos, parts=10, operators=3, replicates=2)
    anidado = pccpy.gage_rr_nested(datos, parts=10, operators=3, replicates=2)
    acuerdo = pccpy.attribute_agreement(corpus._desde_df_atributos()[0], reference=corpus._desde_df_atributos()[1], replicates=2)
    return {
        "oc_atr": lambda: atr.oc_curve(stable=True), "aoq_atr": lambda: atr.aoq_curve(stable=True),
        "oc_var": lambda: var.oc_curve(stable=True), "oc_dr": lambda: dr.oc_curve(stable=True),
        "aoq_dr": lambda: dr.aoq_curve(stable=True),
        "pareto": lambda: pccpy.pareto(["a", "b", "a"], stable=True),
        "anova_cruzado": lambda: cruzado.anova_frame(stable=True), "anova_anidado": lambda: anidado.anova_frame(stable=True),
        "kappa_dentro": lambda: acuerdo.kappa_within_frame(stable=True),
        "kappa_ref": lambda: acuerdo.kappa_vs_reference_frame(stable=True),
    }


CLAVES = {
    "oc_atr": ["defective_fraction", "p_accept"], "oc_var": ["defective_fraction", "p_accept"],
    "oc_dr": ["defective_fraction", "p_accept"], "aoq_atr": ["defective_fraction", "aoq"],
    "aoq_dr": ["defective_fraction", "aoq"], "pareto": ["category", "count", "percent", "cumulative_percent"],
    "anova_cruzado": ["df", "ss", "ms", "f", "p_value"], "anova_anidado": ["df", "ss", "ms", "f", "p_value"],
    "kappa_dentro": ["kappa", "p_value", "pct_agreement"], "kappa_ref": ["kappa", "p_value", "pct_agreement"],
}


@pytest.mark.parametrize("nombre", sorted(CLAVES))
def test_las_claves_estables_no_cambian_con_el_idioma(nombre):
    f = _objetos()[nombre]
    with pccpy.language("es"):
        es = f()
    with pccpy.language("en"):
        en = f()
    assert list(es.columns) == CLAVES[nombre] == list(en.columns)
    assert es.index.name == en.index.name and list(es.index) == list(en.index)
    assert es.equals(en)


def test_las_filas_y_el_indice_estables_de_anova():
    f = _objetos()
    assert list(f["anova_cruzado"]().index) == ["parts", "operators", "parts_x_operators", "error_repeatability"]
    assert list(f["anova_anidado"]().index) == ["operators", "parts_nested", "error"]
    assert f["anova_cruzado"]().index.name == "source" and f["kappa_ref"]().index.name == "operator"


def test_anova_frame_es_none_sin_anova_y_los_atributos_siguen_en_espanol():
    datos = corpus._msa_datos()[0]
    assert pccpy.gage_rr(datos, parts=10, operators=3, replicates=2, method="xbar_r").anova_frame() is None
    g = pccpy.gage_rr(datos, parts=10, operators=3, replicates=2)
    with pccpy.language("en"):
        assert list(g.anova_table.columns) == ["GL", "SC", "CM", "F", "p-valor"]  # dato público: no cambia
        assert list(g.anova_frame().columns) == ["DF", "SS", "MS", "F", "p-value"]


def test_curvas_en_ingles_por_defecto_y_stable_ignora_el_idioma():
    plan = pccpy.acceptance_sampling_attributes(N=1000, aql=1.0)
    with pccpy.language("en"):
        assert list(plan.oc_curve().columns) == ["p_defective", "P(accept)"]
    assert list(plan.oc_curve().columns) == ["p_defectivo", "P(aceptar)"]


def test_los_graficos_funcionan_con_tablas_de_cualquier_idioma():
    plt.close("all")
    for lang in ("es", "en"):
        with pccpy.language(lang):
            assert isinstance(pccpy.plot_pareto(pccpy.pareto(["a", "b", "a"])), plt.Figure)
            assert isinstance(pccpy.plot_pareto(pccpy.pareto(["a", "b", "a"], stable=True)), plt.Figure)
            assert isinstance(pccpy.acceptance_sampling_attributes(N=1000, aql=1.0).plot(), plt.Figure)
    plt.close("all")
