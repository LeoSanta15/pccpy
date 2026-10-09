"""Fase 2 de i18n: ``summary()`` y ``to_frame()`` en español (referencia fija) y en inglés (invariantes).

La referencia en español (``tests/golden/i18n_es.json``) se generó con el código **anterior** a la migración y no se
regenera: es el control independiente de que traducir no cambió ni una palabra del español. Los números se enmascaran
(``#``) para no depender de decimales entre versiones de numpy/scipy; las etiquetas de las tablas se comparan exactas.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import _corpus_i18n as corpus
import pytest

import pccpy

GOLDEN = json.loads((Path(__file__).parent / "golden" / "i18n_es.json").read_text(encoding="utf-8"))
RESULTADOS: dict[str, dict] = {}


def _obtener(nombre: str, lang: str) -> dict:
    clave = f"{nombre}|{lang}"
    if clave not in RESULTADOS:
        with pccpy.language(lang):
            RESULTADOS[clave] = corpus.textos(corpus.entradas()[nombre]())
    return RESULTADOS[clave]


def _iguales(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        # 1e-3: los ajustes por máxima verosimilitud (Weibull…) varían en la 5.ª cifra entre versiones de scipy; lo que
        # protege esta prueba es la estructura y el texto en español, y los números se validan con referencias aparte
        return math.isclose(a, b, rel_tol=1e-3, abs_tol=1e-9)
    return a == b


def test_el_corpus_y_la_referencia_coinciden_en_las_entradas():
    assert sorted(corpus.entradas()) == sorted(GOLDEN)


@pytest.mark.parametrize("nombre", sorted(GOLDEN))
def test_el_espanol_no_cambia_summary(nombre):
    esperado = GOLDEN[nombre]
    actual = _obtener(nombre, "es")
    for clave in ("summary", "str", "texto"):
        if clave in esperado:
            assert corpus.enmascarar(actual[clave]) == corpus.enmascarar(esperado[clave])
            assert len(actual[clave].splitlines()) == len(esperado[clave].splitlines())


@pytest.mark.parametrize("nombre", sorted(n for n, v in GOLDEN.items() if "frame" in v))
def test_el_espanol_no_cambia_to_frame(nombre):
    esperado, actual = GOLDEN[nombre]["frame"], _obtener(nombre, "es")["frame"]
    assert actual["columns"] == esperado["columns"]
    assert actual["index_name"] == esperado["index_name"]
    if esperado["index"] and isinstance(esperado["index"][0], str):
        assert actual["index"] == esperado["index"]
    assert len(actual["data"]) == len(esperado["data"])
    for fila_a, fila_e in zip(actual["data"], esperado["data"]):
        assert all(_iguales(a, e) for a, e in zip(fila_a, fila_e)), (fila_a, fila_e)


# ── el inglés: mismas líneas y mismos números que el español ─────────────────

from test_i18n_errores import palabras_en_espanol  # noqa: E402

ESTABLES = json.loads((Path(__file__).parent / "golden" / "i18n_stable.json").read_text(encoding="utf-8"))
# El texto de decisión del asistente (rationale) y sus alternativas se migran en la fase 3.
PENDIENTES_FASE_3 = {n for n in GOLDEN if n.startswith("wizard")}
ENTRADAS_CON_TEXTO = sorted(n for n, v in GOLDEN.items() if {"summary", "str", "texto"} & set(v))


def _texto(d: dict) -> str:
    return next(d[k] for k in ("summary", "str", "texto") if k in d)


@pytest.mark.parametrize("nombre", ENTRADAS_CON_TEXTO)
def test_el_ingles_tiene_las_mismas_lineas_y_numeros_que_el_espanol(nombre):
    es, en = _texto(_obtener(nombre, "es")), _texto(_obtener(nombre, "en"))
    assert len(en.splitlines()) == len(es.splitlines())
    assert corpus.NUMERO.findall(en) == corpus.NUMERO.findall(es)
    assert en != es


@pytest.mark.parametrize("nombre", [n for n in ENTRADAS_CON_TEXTO if n not in PENDIENTES_FASE_3])
def test_el_ingles_no_tiene_palabras_en_espanol(nombre):
    assert palabras_en_espanol(_texto(_obtener(nombre, "en"))) == set()


def test_el_ingles_mantiene_las_columnas_de_las_tablas_alineadas():
    """Las filas de la tabla de Gage R&R y el encabezado de PPM conservan la posición de sus columnas."""
    def cols(texto, patron):
        return [[m.end() for m in corpus.NUMERO.finditer(ln)] for ln in texto.splitlines() if re.search(patron, ln)]

    es, en = _texto(_obtener("gage_rr_anova", "es")), _texto(_obtener("gage_rr_anova", "en"))
    assert cols(en, r"\d+\.\d{5}") == cols(es, r"\d+\.\d{5}")
    for nombre in ("capability_con_especificaciones", "capability_nonnormal_weibull"):
        es_t, en_t = _texto(_obtener(nombre, "es")), _texto(_obtener(nombre, "en"))
        enc_es = next(ln for ln in es_t.splitlines() if "(PPM)" in ln)
        enc_en = next(ln for ln in en_t.splitlines() if "(PPM)" in ln)
        assert [enc_en.index(s) for s in ("<", ">", "Total")] == [enc_es.index(s) for s in ("<", ">", "Total")]


@pytest.mark.parametrize("nombre", sorted(n for n, v in GOLDEN.items() if "frame" in v))
def test_to_frame_en_ingles_tiene_la_misma_forma_y_valores_con_etiquetas_traducidas(nombre):
    es, en = _obtener(nombre, "es")["frame"], _obtener(nombre, "en")["frame"]
    assert len(en["data"]) == len(es["data"]) and len(en["columns"]) == len(es["columns"])
    for fila_es, fila_en in zip(es["data"], en["data"]):
        assert all(_iguales(a, b) for a, b in zip(fila_es, fila_en))
    etiquetas = [str(x) for x in en["columns"]] + ([str(x) for x in en["index"]] if isinstance(en["index"][0], str) else [])
    etiquetas.append(str(en["index_name"]))
    assert palabras_en_espanol(" ".join(etiquetas)) == set()
    if nombre not in PENDIENTES_FASE_3:
        assert (en["columns"], en["index_name"]) != (es["columns"], es["index_name"])


# ── to_frame(stable=True): claves que no cambian con el idioma ───────────────

@pytest.mark.parametrize("nombre", sorted(ESTABLES))
def test_las_claves_estables_son_las_de_la_referencia_y_no_dependen_del_idioma(nombre):
    for lang in ("es", "en"):
        with pccpy.language(lang):
            actual = corpus.tabla_estable(corpus.entradas()[nombre]())
        esperado = ESTABLES[nombre]
        assert actual["columns"] == esperado["columns"]
        assert actual["index_name"] == esperado["index_name"]
        if esperado["index"] and isinstance(esperado["index"][0], str):
            assert actual["index"] == esperado["index"]


@pytest.mark.parametrize("nombre", sorted(ESTABLES))
def test_las_claves_estables_son_snake_case_unicas_y_sin_separadores(nombre):
    t = ESTABLES[nombre]
    claves = [str(c) for c in t["columns"]] + ([i for i in t["index"] if isinstance(i, str)])
    # el nombre del panel (p. ej. ``|S|``) es un identificador existente y va de prefijo de la clave
    assert all(re.fullmatch(r"[A-Za-z|][A-Za-z0-9_|]*", k) for k in claves), claves
    indice = [i for i in t["index"] if isinstance(i, str)]
    assert len(indice) == len(set(indice))


def test_stable_devuelve_los_mismos_valores_que_la_tabla_traducida():
    for nombre in ("capability_con_especificaciones", "gage_rr_anova", "tolerancia_normal"):
        obj = corpus.entradas()[nombre]()
        normal, estable = obj.to_frame().to_numpy(dtype=object), obj.to_frame(stable=True).to_numpy(dtype=object)
        valores_normales = [v for fila in normal for v in fila if not (isinstance(v, str) and v == "")]
        valores_estables = [v for fila in estable for v in fila]
        assert valores_normales == valores_estables


@pytest.mark.parametrize("lang", ["es", "en"])
def test_violations_stable_tiene_claves_canonicas(lang):
    with pccpy.language(lang):
        v = corpus.entradas()["imr_con_atipicos"]().violations(stable=True)
        traducida = corpus.entradas()["imr_con_atipicos"]().violations()
    assert list(v.columns) == ["panel", "point", "test", "value", "description"]
    assert len(v) == len(traducida) > 0
    assert list(traducida.columns) == (["panel", "punto", "prueba", "valor", "descripcion"] if lang == "es"
                                       else ["panel", "point", "test", "value", "description"])
