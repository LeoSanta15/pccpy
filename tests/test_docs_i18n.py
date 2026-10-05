"""Fase 4 de i18n: la documentación (Sphinx) y el README tienen versión en inglés coherente con la española."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from docs_i18n_check import problemas_de_mensaje  # noqa: E402

# ── detector de problemas de traducción de la documentación (con controles negativos) ─────────────────────


def test_el_detector_acepta_una_traduccion_correcta():
    assert problemas_de_mensaje("Ver {doc}`inicio_rapido` para más datos.", "See {doc}`inicio_rapido` for more data.") == []
    assert problemas_de_mensaje("Devuelve ``x`` y `y`.", "Returns ``x`` and `y`.") == []


def test_el_detector_senala_una_traduccion_vacia():
    assert problemas_de_mensaje("Texto", "")


def test_el_detector_senala_un_rol_de_sphinx_que_cambia():
    assert problemas_de_mensaje("Ver :func:`diagnose`.", "See :func:`diagnoses`.")
    assert problemas_de_mensaje("Ver {doc}`faq`.", "See the FAQ.")


def test_el_detector_trata_igual_los_roles_rst_y_myst():
    assert problemas_de_mensaje("Ver :func:`diagnose`.", "See {func}`diagnose`.") == []


def test_el_detector_senala_un_rol_rst_en_una_pagina_markdown():
    assert problemas_de_mensaje("Ver :func:`x`.", "See :func:`x`.", markdown=True)
    assert problemas_de_mensaje("Ver :func:`x`.", "See {func}`x`.", markdown=True) == []
    assert problemas_de_mensaje("Ver :func:`x`.", "See :func:`x`.", markdown=False) == []


def test_el_detector_senala_una_url_o_un_codigo_que_cambian():
    assert problemas_de_mensaje("Ver https://a.org/x.", "See https://b.org/x.")
    assert problemas_de_mensaje("Usa `a` y `b`.", "Use `a`.")
    assert problemas_de_mensaje("Es **importante**.", "It is important.")


def test_el_detector_senala_texto_en_espanol_sin_traducir():
    assert problemas_de_mensaje("Calcula el índice para los datos.", "Calcula el índice para los datos.")
    assert problemas_de_mensaje("Calcula el índice.", "Computes the índice de los datos.")


def test_el_detector_acepta_etiquetas_cortas_identicas_e_identificadores():
    assert problemas_de_mensaje("carta de control", "carta de control") == []
    assert problemas_de_mensaje("Ver sigma_entre.", "See sigma_entre.") == []


# ── los catálogos del repositorio ───────────────────────────────────────────────────────────────────────────


def test_los_catalogos_de_la_documentacion_estan_al_dia():
    pytest.importorskip("sphinx")
    import docs_i18n_check

    assert docs_i18n_check.main() == 0


def test_hay_un_catalogo_en_inglés_por_pagina_salvo_el_historial():
    paginas = {p.relative_to(RAIZ / "docs" / "source").with_suffix("").as_posix()
               for p in (RAIZ / "docs" / "source").rglob("*") if p.suffix in (".md", ".rst")}
    catalogos = {p.relative_to(RAIZ / "docs" / "locales" / "en" / "LC_MESSAGES").with_suffix("").as_posix()
                 for p in (RAIZ / "docs" / "locales" / "en" / "LC_MESSAGES").rglob("*.po")}
    assert paginas - catalogos == set()


# ── README en inglés ────────────────────────────────────────────────────────────────────────────────────────


def _bloques(texto: str, lenguaje: str) -> list[str]:
    return re.findall(rf"```{lenguaje}\n([\s\S]*?)\n```", texto)


def test_el_readme_en_ingles_tiene_la_misma_estructura_que_el_espanol():
    es = (RAIZ / "README.md").read_text(encoding="utf-8")
    en = (RAIZ / "README_en.md").read_text(encoding="utf-8")
    assert len(_bloques(es, "python")) == len(_bloques(en, "python"))
    assert len(re.findall(r"^#{1,4} ", es, re.M)) == len(re.findall(r"^#{1,4} ", en, re.M))
    assert len(re.findall(r"^\|", es, re.M)) == len(re.findall(r"^\|", en, re.M))   # filas de tablas


def test_los_dos_readme_se_enlazan_entre_si():
    assert "(README_en.md)" in (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "(README.md)" in (RAIZ / "README_en.md").read_text(encoding="utf-8")


def test_los_enlaces_internos_del_readme_en_ingles_apuntan_a_titulos_existentes():
    texto = (RAIZ / "README_en.md").read_text(encoding="utf-8")

    def ancla(titulo: str) -> str:
        t = re.sub(r"[^\w\s\-²]", "", titulo.lower().strip())
        return t.replace(" ", "-")

    titulos = {ancla(t) for t in re.findall(r"^#{1,4} (.+)$", texto, re.M)}
    rotos = [a for a in re.findall(r"\]\(#([^)]+)\)", texto) if a not in titulos]
    assert rotos == []


def test_los_bloques_de_codigo_del_readme_en_ingles_son_python_valido():
    import ast

    for b in _bloques((RAIZ / "README_en.md").read_text(encoding="utf-8"), "python"):
        ast.parse(b)


def test_el_readme_en_ingles_no_tiene_identificadores_en_espanol_en_el_codigo():
    en = (RAIZ / "README_en.md").read_text(encoding="utf-8")
    codigo = "\n".join(_bloques(en, "python"))
    sin_comentarios = re.sub(r"#.*", "", codigo)
    assert not re.search(r"\b(carta|datos|defectos|defectuosos|etapas|tiempos|tabla)\b", sin_comentarios)


@pytest.mark.skipif(importlib.util.find_spec("sphinx") is None, reason="sphinx no instalado")
def test_el_idioma_de_sphinx_se_puede_elegir_por_variable_de_entorno():
    texto = (RAIZ / "docs" / "source" / "conf.py").read_text(encoding="utf-8")
    assert "READTHEDOCS_LANGUAGE" in texto and 'locale_dirs = ["../locales"]' in texto
