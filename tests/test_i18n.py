"""Idioma de los textos visibles: global, contexto, hilos, respaldo y catálogo real."""
from __future__ import annotations

import threading
import warnings
from pathlib import Path

import pytest

import pccpy
from pccpy import _i18n
from pccpy._i18n import N_, _


@pytest.fixture(autouse=True)
def idioma_limpio():
    """Cada test parte del español y deja el estado global como lo encontró."""
    anterior = _i18n._global
    _i18n._global = "es"
    yield
    _i18n._global = anterior
    _i18n._cache.clear()


@pytest.fixture
def catalogo_de_prueba(tmp_path, monkeypatch):
    """Catálogo ``xx`` con un texto traducido; no depende de los catálogos reales."""
    from babel.messages.catalog import Catalog
    from babel.messages.mofile import write_mo

    cat = Catalog(locale="de", domain="pccpy")
    cat.add("Hola {nombre}.", "Hallo {nombre}.")
    destino = tmp_path / "de" / "LC_MESSAGES"
    destino.mkdir(parents=True)
    with (destino / "pccpy.mo").open("wb") as f:
        write_mo(f, cat)
    monkeypatch.setattr(_i18n, "_LOCALES", tmp_path)
    _i18n._cache.clear()
    return "de"


def test_el_idioma_por_defecto_es_espanol_y_no_traduce():
    assert _i18n.get_language() == "es"
    assert _("Hola {nombre}.") == "Hola {nombre}."


def test_set_language_traduce(catalogo_de_prueba):
    pccpy.set_language(catalogo_de_prueba)
    assert _("Hola {nombre}.").format(nombre="Ana") == "Hallo Ana."


def test_texto_sin_traduccion_devuelve_el_original(catalogo_de_prueba):
    pccpy.set_language(catalogo_de_prueba)
    assert _("Un texto que no está en el catálogo.") == "Un texto que no está en el catálogo."


def test_el_idioma_global_se_ve_desde_un_hilo_nuevo(catalogo_de_prueba):
    pccpy.set_language(catalogo_de_prueba)
    resultado = {}
    hilo = threading.Thread(target=lambda: resultado.update(t=_("Hola {nombre}.")))
    hilo.start()
    hilo.join()
    assert resultado["t"] == "Hallo {nombre}."


def test_language_cambia_solo_dentro_del_bloque(catalogo_de_prueba):
    with pccpy.language(catalogo_de_prueba):
        assert pccpy.get_language() == "de"
        assert _("Hola {nombre}.") == "Hallo {nombre}."
    assert pccpy.get_language() == "es"
    assert _("Hola {nombre}.") == "Hola {nombre}."


def test_language_se_restaura_aunque_el_bloque_falle(catalogo_de_prueba):
    with pytest.raises(RuntimeError), pccpy.language(catalogo_de_prueba):
        raise RuntimeError("fallo")
    assert pccpy.get_language() == "es"


def test_language_anidado(catalogo_de_prueba):
    with pccpy.language(catalogo_de_prueba):
        with pccpy.language("es"):
            assert pccpy.get_language() == "es"
        assert pccpy.get_language() == "de"


def test_un_hilo_creado_dentro_de_language_no_hereda_el_contexto(catalogo_de_prueba):
    resultado = {}
    with pccpy.language(catalogo_de_prueba):
        hilo = threading.Thread(target=lambda: resultado.update(t=pccpy.get_language()))
        hilo.start()
        hilo.join()
    assert resultado["t"] == "es"


@pytest.mark.parametrize("variante", ["en", "EN", "en_US", "en-US", "en.UTF-8", " en "])
def test_set_language_normaliza_variantes(variante):
    pccpy.set_language(variante)
    assert pccpy.get_language() == "en"


@pytest.mark.parametrize("malo", ["fr", "zz", "", "   ", "_"])
def test_set_language_rechaza_idiomas_no_disponibles_o_vacios(malo):
    with pytest.raises(ValueError):
        pccpy.set_language(malo)
    assert pccpy.get_language() == "es"


def test_language_rechaza_idiomas_no_disponibles():
    with pytest.raises(ValueError, match="no disponible"):
        with pccpy.language("fr"):
            pass


def test_los_mensajes_de_error_del_propio_modulo_se_traducen_con_el_catalogo_real():
    with pccpy.language("en"), pytest.raises(ValueError, match="Language not available"):
        pccpy.set_language("fr")


def test_available_languages_incluye_el_idioma_fuente_y_el_catalogo_real():
    assert pccpy.available_languages() == ["en", "es"]


def test_variable_de_entorno_valida(monkeypatch):
    monkeypatch.setenv("PCCPY_LANG", "en_US")
    assert _i18n._idioma_inicial() == "en"


def test_variable_de_entorno_invalida_avisa_y_usa_espanol(monkeypatch):
    monkeypatch.setenv("PCCPY_LANG", "zz")
    with pytest.warns(UserWarning, match="PCCPY_LANG"):
        assert _i18n._idioma_inicial() == "es"


def test_sin_variable_de_entorno_no_avisa(monkeypatch):
    monkeypatch.delenv("PCCPY_LANG", raising=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _i18n._idioma_inicial() == "es"


def test_N_marca_sin_traducir_y_se_traduce_al_mostrar(catalogo_de_prueba):
    constante = N_("Hola {nombre}.")           # constante de módulo: se define una vez, en español
    assert constante == "Hola {nombre}."
    with pccpy.language(catalogo_de_prueba):
        assert _(constante) == "Hallo {nombre}."
    assert _(constante) == "Hola {nombre}."    # y vuelve al español sin reimportar


def test_la_api_publica_exporta_las_funciones_de_idioma():
    for nombre in ("set_language", "get_language", "language", "available_languages"):
        assert nombre in pccpy.__all__
        assert callable(getattr(pccpy, nombre))


def test_el_wheel_incluye_los_catalogos_compilados():
    """Los .mo son datos del paquete: deben existir junto al módulo (y ``package-data`` los empaqueta)."""
    mo = Path(_i18n.__file__).parent / "locale" / "en" / "LC_MESSAGES" / "pccpy.mo"
    assert mo.is_file()
    assert 'locale/*/LC_MESSAGES/*.mo' in (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
