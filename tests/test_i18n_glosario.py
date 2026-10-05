"""Fase 5 de i18n: el glosario español → inglés se aplica de forma consistente en todo el catálogo y la guía lo documenta."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PO = RAIZ / "src" / "pccpy" / "locale" / "en" / "LC_MESSAGES" / "pccpy.po"
GUIA = RAIZ / "docs" / "source" / "traducir.md"

# término español (inicio de palabra) → fragmento que debe aparecer en la traducción
GLOSARIO = {
    "carta de control": "control chart", "cartas de control": "control chart",
    "límites de control": "control limit", "línea central": "center line", "subgrupo": "subgroup",
    "observación": "observation", "observaciones": "observation", "capacidad": "capability",
    "desviación estándar": "standard deviation", "intervalo de tolerancia": "tolerance interval",
    "muestreo de aceptación": "acceptance sampling", "causas especiales": "special-cause", "repetibilidad": "repeatab", "reproducibilidad": "reproducib",
    "sesgo": "bias", "linealidad": "linearity", "concordancia": "agreement", "fracción defectuosa": "fraction defective",
    "p-valor": "p-value", "valor p": "p-value", "mediana": "median", "rango": "range", "especificación": "specification",
    "defectuosos": "defective", "tamaño de muestra": "sample size", "normalidad": "normality", "atípico": "outlier",
    "tendencia": "trend", "mezcla": "mixture", "agrupamiento": "clustering", "oscilación": "oscillation",
    "operador": "operator", "parte": "part",
}


def _catalogo():
    from babel.messages.pofile import read_po

    with PO.open("rb") as f:
        return [m for m in read_po(f, locale="en") if m.id]


def incoherencias(catalogo, glosario) -> list[str]:
    """Textos cuyo original usa un término del glosario y cuya traducción no usa el término inglés acordado."""
    malos = []
    for terminio, ingles in glosario.items():
        patron = re.compile(r"\b" + re.escape(terminio), re.IGNORECASE)
        malos += [f"[{terminio}→{ingles}] {m.id[:60]!r} ⇒ {m.string[:60]!r}"
                  for m in catalogo if patron.search(m.id) and ingles not in m.string.lower()]
    return malos


def test_todo_el_catalogo_respeta_el_glosario():
    assert incoherencias(_catalogo(), GLOSARIO) == []


def test_el_detector_de_glosario_senala_una_incoherencia():
    class M:
        id, string = "Límite de control superior", "Upper bound"

    assert incoherencias([M], {"límite de control": "control limit"})


def test_cada_termino_del_glosario_aparece_en_algun_texto():
    ids = " ".join(m.id.lower() for m in _catalogo())
    assert [t for t in GLOSARIO if t not in ids] == []


def test_la_guia_documenta_los_terminos_del_glosario():
    """Cada traducción acordada figura en la tabla de la guía «Cómo traducir»."""
    guia = GUIA.read_text(encoding="utf-8").lower()
    fila = re.compile(r"^\| (.+?) \| (.+?) \|$", re.MULTILINE)
    ingles_en_guia = {e.strip() for _es, e in fila.findall(guia)}
    ausentes = sorted({e for e in GLOSARIO.values() if not any(e in g for g in ingles_en_guia)})
    assert ausentes == []


@pytest.mark.parametrize("idioma", ["en"])
def test_el_catalogo_no_tiene_traducciones_vacias_ni_fuzzy(idioma):
    assert [m.id[:40] for m in _catalogo() if not m.string or m.fuzzy] == []
