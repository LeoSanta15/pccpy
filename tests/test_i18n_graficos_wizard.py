"""Fase 3 de i18n: textos de los gráficos y del asistente (``wizard``).

Las referencias en español (``tests/golden/i18n_plots_es.json`` y ``i18n_wizard_es.json``) se generaron con el código
**anterior** a la migración y no se regeneran: son el control independiente de que traducir no cambió el español.
"""
from __future__ import annotations

import json
from pathlib import Path

import _corpus_i18n as corpus
import pytest

import pccpy

GOLDEN_DIR = Path(__file__).parent / "golden"
PLOTS_ES = json.loads((GOLDEN_DIR / "i18n_plots_es.json").read_text(encoding="utf-8"))
WIZARD_ES = json.loads((GOLDEN_DIR / "i18n_wizard_es.json").read_text(encoding="utf-8"))
_CACHE: dict = {}


def _figuras(lang: str) -> dict:
    if ("plots", lang) not in _CACHE:
        with pccpy.language(lang):
            _CACHE[("plots", lang)] = corpus.construir_graficos()
    return _CACHE[("plots", lang)]


def _wizard(lang: str) -> dict:
    if ("wizard", lang) not in _CACHE:
        with pccpy.language(lang):
            _CACHE[("wizard", lang)] = corpus.textos_wizard()
    return _CACHE[("wizard", lang)]


# ── español: sin cambios ─────────────────────────────────────────────────────

def test_las_figuras_del_corpus_son_las_de_la_referencia():
    figs, errores = _figuras("es")
    assert not errores and sorted(figs) == sorted(PLOTS_ES)


@pytest.mark.parametrize("nombre", sorted(PLOTS_ES))
def test_el_espanol_de_los_graficos_no_cambia(nombre):
    assert _figuras("es")[0][nombre] == PLOTS_ES[nombre]


@pytest.mark.parametrize("parte", sorted(WIZARD_ES))
def test_el_espanol_del_asistente_no_cambia(parte):
    assert _wizard("es")[parte] == WIZARD_ES[parte]


# ── inglés ───────────────────────────────────────────────────────────────────

ESPANOL_GRAFICOS = frozenset(
    "valor observación observaciones media mediana carta curva dentro objetivo muestra subgrupo subgrupos gráfico "
    "histograma densidad parte operador sesgo rango conteo proporción atípicos frecuencia porcentaje intervalo "
    "tolerancia muestreo aceptación diagnóstico rápido proceso capacidad probabilidad secuencia normalidad "
    "cobertura confianza método lados señales verde amarillo rojo regresión linealidad referencia últimas últimos "
    "reproducibilidad repetibilidad contribución fuente fracción defectiva defectuosa acumulado acumulada "
    "análisis volver análisis recomendado alternativas pendiente selecciona opción ingresa número entre "
    "tiempo eventos defectos unidad suma móvil sistema medición concordancia atributos".split()
)


def _palabras_es(texto: str) -> set[str]:
    import re

    return {p.lower() for p in re.findall(r"[A-Za-zÁ-ú]+", texto)} & ESPANOL_GRAFICOS


def test_los_graficos_en_ingles_no_tienen_palabras_en_espanol():
    figs, errores = _figuras("en")
    assert not errores
    malos = {n: sorted({p for t in textos for p in _palabras_es(t)}) for n, textos in figs.items()}
    assert {n: p for n, p in malos.items() if p} == {}


@pytest.mark.parametrize("nombre", sorted(PLOTS_ES))
def test_los_graficos_en_ingles_tienen_la_misma_estructura(nombre):
    es, en = _figuras("es")[0][nombre], _figuras("en")[0][nombre]
    assert len(es) == len(en)
    assert sum(t.count("#") for t in es) == sum(t.count("#") for t in en)


def test_los_graficos_en_ingles_traducen_los_textos_de_ejemplo():
    figs, _ = _figuras("en")
    textos = {t for ts in figs.values() for t in ts}
    assert {"Observation", "Value", "Histogram", "Normal probability plot", "UCL=#", "LCL=#"} <= textos


def test_un_idioma_no_contamina_al_otro_en_los_graficos():
    assert _figuras("es")[0]["plot_diagnose_tendencia"] != _figuras("en")[0]["plot_diagnose_tendencia"]
    assert "Observación" in _figuras("es")[0]["plot_diagnose_tendencia"]
    assert "Observation" in _figuras("en")[0]["plot_diagnose_tendencia"]


def _textos_del_arbol() -> list[str]:
    from pccpy import _wizard

    textos = []
    for pregunta, opciones in _wizard._TREE.values():
        textos.append(pregunta)
        textos.extend(etiqueta for etiqueta, _destino in opciones)
    for r in _wizard._RESULTS.values():
        textos.extend([r.rationale, r._snippet])
    return textos


def test_todo_texto_del_arbol_del_asistente_esta_traducido_al_ingles():
    from pccpy._i18n import tr

    with pccpy.language("en"):
        sin_traducir = [t for t in _textos_del_arbol() if tr(t) == t]
    assert sin_traducir == []


def test_el_arbol_del_asistente_en_ingles_no_tiene_palabras_en_espanol():
    from pccpy._i18n import tr

    with pccpy.language("en"):
        malos = {t: _palabras_es(tr(t)) for t in _textos_del_arbol()}
    assert {t: p for t, p in malos.items() if p} == {}


def test_los_fragmentos_de_codigo_en_ingles_son_python_valido():
    import ast

    from pccpy import _wizard

    with pccpy.language("en"):
        for clave, r in _wizard._RESULTS.items():
            codigo = r.snippet()
            ast.parse(codigo)
            assert f"pp.{r.function}(" in codigo, clave


def test_el_asistente_cli_en_ingles_tiene_la_misma_forma_que_en_espanol():
    es, en = _wizard("es")["cli"].splitlines(), _wizard("en")["cli"].splitlines()
    assert len(es) == len(en)
    assert [len(linea) for linea in en[1:4]] == [len(linea) for linea in es[1:4]]  # el marco mantiene su ancho


def test_el_asistente_widget_en_ingles_tiene_los_mismos_elementos():
    es, en = _wizard("es")["widget"], _wizard("en")["widget"]
    assert [len(p) for p in es] == [len(p) for p in en]


def test_el_estado_inicial_de_la_sesion_se_traduce():
    assert _wizard("es")["widget_repr_inicial"] == "WidgetSession(pendiente)"
    assert _wizard("en")["widget_repr_inicial"] == "WidgetSession(pending)"


def test_el_prompt_y_el_error_de_opcion_se_traducen():
    en = _wizard("en")["cli"]
    assert "Select an option:" in en and "Enter a number between 1 and 7." in en
    assert "Selecciona" not in en


def test_el_asistente_en_ingles_no_tiene_palabras_en_espanol_ni_en_el_cli_ni_en_el_widget():
    en = _wizard("en")
    widget = [t for pantalla in en["widget"] for t in pantalla]
    texto = en["cli"] + "\n".join(widget) + "\n".join(v["summary"] for v in en["resultados"].values())
    assert _palabras_es(texto) == set()
    assert "← Back" in widget and "← Volver" not in widget
