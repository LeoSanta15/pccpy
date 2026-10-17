"""Pruebas de la especificación 014 (parte A): ``DiagnoseResult.trend_direction`` en inglés.

La referencia independiente es el signo de la pendiente de una recta de mínimos cuadrados (``scipy.stats.linregress``).
"""
import re
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

import pccpy

RAIZ = Path(__file__).resolve().parents[1]


def _con_tendencia(signo, n=60, seed=0):
    rng = np.random.default_rng(seed)
    return signo * np.linspace(0, 40, n) + rng.normal(0, 0.2, n)


@pytest.mark.parametrize("idioma", ["es", "en"])
@pytest.mark.parametrize("signo, esperado", [(+1, "increasing"), (-1, "decreasing")])
def test_s014_rf_01_trend_direction_en_ingles_en_cualquier_idioma(idioma, signo, esperado):
    """S014-RF-01: los valores guardados son ``'increasing'``/``'decreasing'`` y no dependen del idioma."""
    x = _con_tendencia(signo)
    assert np.sign(stats.linregress(np.arange(x.size), x).slope) == signo
    with pccpy.language(idioma):
        d = pccpy.diagnose(x)
    assert d.has_trend is True
    assert d.trend_direction == esperado


def test_s014_rf_01_sin_tendencia_es_cadena_vacia():
    d = pccpy.diagnose(np.random.default_rng(3).normal(0, 1, 60))
    assert d.has_trend is False
    assert d.trend_direction == ""


def test_s014_rf_01_sin_alias_en_espanol():
    d = pccpy.diagnose(_con_tendencia(+1))
    assert d.trend_direction not in ("creciente", "decreciente")


def test_s014_rf_02_summary_muestra_la_tendencia_traducida():
    """S014-RF-02: lo que se muestra sigue traducido, aunque el valor guardado sea el canónico.

    ``issues`` se escribe al llamar a ``diagnose()``, así que el idioma que cuenta es el de esa llamada.
    """
    for signo, es, en in ((+1, "creciente", "increasing"), (-1, "decreciente", "decreasing")):
        x = _con_tendencia(signo)
        with pccpy.language("es"):
            texto = pccpy.diagnose(x).summary()
        assert f"Se detectó tendencia {es}." in texto
        assert en not in texto
        with pccpy.language("en"):
            texto = pccpy.diagnose(x).summary()
        assert en in texto
        assert es not in texto


def test_s014_rf_02_to_frame_da_el_valor_canonico_en_cualquier_idioma():
    """Los valores de ``to_frame()`` no cambian con el idioma (solo las etiquetas): el valor canónico se ve igual."""
    d = pccpy.diagnose(_con_tendencia(+1))
    assert "increasing" in d.to_frame(stable=True).astype(str).to_numpy()
    for idioma in ("es", "en"):
        with pccpy.language(idioma):
            assert "increasing" in d.to_frame().astype(str).to_numpy()


def _lineas_con_literal(carpeta, sufijos, excluir=()):
    """Líneas con ``'creciente'``/``'decreciente'`` entre comillas fuera de ``excluir``."""
    patron = re.compile(r"""["'](de)?creciente["']""")
    hallazgos = []
    for ruta in sorted((RAIZ / carpeta).rglob("*")):
        if not ruta.is_file() or ruta.suffix not in sufijos or any(e in ruta.parts or e == ruta.name for e in excluir):
            continue
        for n, linea in enumerate(ruta.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if patron.search(linea):
                hallazgos.append((str(ruta.relative_to(RAIZ)), n, linea.strip()))
    return hallazgos


def test_s014_rf_03_src_solo_conserva_el_literal_en_la_traduccion():
    """S014-RF-03: en ``src/`` el literal solo aparece dentro de ``tr(...)`` (la tabla de traducción)."""
    fuera = [h for h in _lineas_con_literal("src", {".py"}) if "tr(" not in h[2]]
    assert fuera == []


def test_s014_rf_03_tests_y_documentacion_usan_los_valores_nuevos():
    excluir = ("golden", "test_tendencia_ingles.py")
    hallazgos = _lineas_con_literal("tests", {".py"}, excluir)
    hallazgos += _lineas_con_literal("docs/source", {".md", ".rst", ".py"})
    for nombre in ("README.md", "README_en.md"):
        for n, linea in enumerate((RAIZ / nombre).read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"""["'](de)?creciente["']""", linea):
                hallazgos.append((nombre, n, linea.strip()))
    assert hallazgos == []
