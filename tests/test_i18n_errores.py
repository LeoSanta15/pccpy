"""Fase 1 de i18n: todo mensaje de error o aviso pasa por ``tr()`` y su traducción es coherente.

Comprobaciones estáticas (AST) sobre ``src/``: una ruta de error rara vez tiene test propio, así que un marcador
``{…}`` sin su argumento en ``.format`` solo fallaría en producción. Los detectores llevan su control negativo.
"""
from __future__ import annotations

import ast
import re
import string
import warnings
from pathlib import Path

import numpy as np
import pytest

import pccpy
from pccpy._data import as_1d

SRC = Path(pccpy.__file__).resolve().parent
ARCHIVOS = sorted(SRC.rglob("*.py"))
NOMBRES_RESERVADOS = {"tr", "N_"}


def _nombre(func: ast.AST) -> str:
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")


def _mensajes(arbol: ast.AST):
    """(línea, nodo del mensaje) de cada ``raise X(msg)`` y ``warnings.warn(msg, …)``."""
    for n in ast.walk(arbol):
        if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) and n.exc.args:
            yield n.lineno, n.exc.args[0]
        elif isinstance(n, ast.Call) and _nombre(n.func) == "warn" and n.args:
            yield n.lineno, n.args[0]


def _es_llamada_a_tr(n: ast.AST) -> bool:
    return isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "tr"


def problemas_de_mensajes(codigo: str) -> list[str]:
    """Problemas de un fragmento de código: texto sin ``tr()``, f-strings dentro de ``tr()`` y marcadores mal enlazados."""
    problemas = []
    for linea, msg in _mensajes(ast.parse(codigo)):
        llamada_format = None
        base = msg
        if isinstance(msg, ast.Call) and isinstance(msg.func, ast.Attribute) and msg.func.attr == "format":
            llamada_format, base = msg, msg.func.value
        if not _es_llamada_a_tr(base):
            problemas.append(f"línea {linea}: el mensaje no pasa por tr()")
            continue
        if not base.args or not (isinstance(base.args[0], ast.Constant) and isinstance(base.args[0].value, str)):
            problemas.append(f"línea {linea}: tr() debe recibir un texto literal (no un f-string ni una variable)")
            continue
        plantilla = base.args[0].value
        campos = [c for _l, c, _f, _c in string.Formatter().parse(plantilla) if c is not None]
        if "" in campos or any(c.isdigit() for c in campos):
            problemas.append(f"línea {linea}: usa marcadores con nombre ({{nombre}}), no posicionales")
            continue
        nombres = {re.split(r"[.\[]", c)[0] for c in campos}
        if llamada_format is None:
            if nombres:
                problemas.append(f"línea {linea}: la plantilla tiene marcadores {sorted(nombres)} pero no se llama a .format()")
            continue
        if llamada_format.args or any(k.arg is None for k in llamada_format.keywords):
            problemas.append(f"línea {linea}: .format() debe recibir solo argumentos con nombre")
            continue
        dados = {k.arg for k in llamada_format.keywords}
        if dados != nombres:
            problemas.append(f"línea {linea}: marcadores {sorted(nombres)} ≠ argumentos de .format() {sorted(dados)}")
    return problemas


def nombres_reservados_ocupados(codigo: str) -> list[str]:
    """Usos de ``tr``/``N_`` como variable, argumento o definición (romperían las llamadas a ``tr()`` de esa función)."""
    ocupados = []
    for n in ast.walk(ast.parse(codigo)):
        if isinstance(n, ast.Name) and n.id in NOMBRES_RESERVADOS and isinstance(n.ctx, ast.Store):
            ocupados.append(f"línea {n.lineno}: asigna {n.id}")
        elif isinstance(n, ast.arg) and n.arg in NOMBRES_RESERVADOS:
            ocupados.append(f"línea {n.lineno}: argumento {n.arg}")
        elif isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in NOMBRES_RESERVADOS:
            ocupados.append(f"línea {n.lineno}: define {n.name}")
    return ocupados


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda p: str(p.relative_to(SRC)))
def test_todo_mensaje_de_error_o_aviso_pasa_por_tr(ruta):
    problemas = problemas_de_mensajes(ruta.read_text(encoding="utf-8"))
    assert not problemas, f"{ruta.relative_to(SRC)}:\n" + "\n".join(problemas)


@pytest.mark.parametrize("ruta", [r for r in ARCHIVOS if r.name != "_i18n.py"], ids=lambda p: str(p.relative_to(SRC)))
def test_nadie_ocupa_los_nombres_tr_y_N_(ruta):
    ocupados = nombres_reservados_ocupados(ruta.read_text(encoding="utf-8"))
    assert not ocupados, f"{ruta.relative_to(SRC)}: {ocupados}"


# ── controles negativos de los detectores ────────────────────────────────────

def test_el_detector_senala_un_mensaje_sin_tr():
    assert problemas_de_mensajes('raise ValueError("falta tr")')


def test_el_detector_senala_un_fstring_dentro_de_tr():
    assert problemas_de_mensajes('raise ValueError(tr(f"valor {x}"))')


def test_el_detector_senala_un_marcador_sin_argumento():
    assert problemas_de_mensajes('raise ValueError(tr("{a} y {b}").format(a=1))')


def test_el_detector_senala_un_argumento_sobrante():
    assert problemas_de_mensajes('raise ValueError(tr("{a}").format(a=1, b=2))')


def test_el_detector_senala_marcadores_sin_format():
    assert problemas_de_mensajes('raise ValueError(tr("hay {a}"))')


def test_el_detector_senala_marcadores_posicionales():
    assert problemas_de_mensajes('raise ValueError(tr("{}").format(1))')


def test_el_detector_senala_un_aviso_sin_tr():
    assert problemas_de_mensajes('warnings.warn("aviso", UserWarning)')


def test_el_detector_acepta_el_patron_correcto():
    codigo = (
        'raise ValueError(tr("fijo"))\n'
        'raise ValueError(tr("{a.b} y {c}").format(a=x, c=y))\n'
        'warnings.warn(tr("aviso {n}").format(n=3), UserWarning, stacklevel=2)\n'
    )
    assert problemas_de_mensajes(codigo) == []


def test_el_detector_de_nombres_reservados():
    assert nombres_reservados_ocupados("def f():\n    tr = 1\n")
    assert nombres_reservados_ocupados("def f(N_):\n    pass\n")
    assert nombres_reservados_ocupados("def f():\n    return 1\n") == []


def llamadas_a_tr_dentro_de_fstrings(codigo: str) -> list[str]:
    """``tr()``/``N_()`` dentro de un f-string: Babel solo los extrae en Python >= 3.12, así que el catálogo dependería de la versión."""
    return [
        f"línea {c.lineno}"
        for f in ast.walk(ast.parse(codigo)) if isinstance(f, ast.JoinedStr)
        for c in ast.walk(f) if isinstance(c, ast.Call) and _nombre(c.func) in NOMBRES_RESERVADOS
    ]


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda p: str(p.relative_to(SRC)))
def test_ningun_tr_dentro_de_un_fstring(ruta):
    assert not llamadas_a_tr_dentro_de_fstrings(ruta.read_text(encoding="utf-8")), (
        f"{ruta.relative_to(SRC)}: asigna tr(...) a una variable antes del f-string"
    )


def test_el_detector_de_tr_en_fstrings_funciona():
    assert llamadas_a_tr_dentro_de_fstrings("x = f\"{tr('a'):<5}\"")
    assert llamadas_a_tr_dentro_de_fstrings("y = f'{N_(\"a\")}'")
    assert llamadas_a_tr_dentro_de_fstrings("a = tr('a')\nx = f\"{a:<5}\"") == []


# ── el catálogo en inglés ────────────────────────────────────────────────────

ESPANOL = frozenset(
    "debe deben requiere requieren datos observaciones observación necesita necesitan tamaño valores longitud matriz "
    "carta subgrupos etapa columna columnas ignoraron falta cada pocos todos todas entre puntos mayor menor para los las "
    "una del".split()
)


def palabras_en_espanol(texto: str) -> set[str]:
    sin_codigo = re.sub(r"\{[^{}]*\}|'[^']*'", " ", texto)       # marcadores y nombres entre comillas
    return {p.lower() for p in re.findall(r"[A-Za-zÁ-ú]+", sin_codigo)} & ESPANOL


def _catalogo_en():
    from babel.messages.pofile import read_po

    with (SRC / "locale" / "en" / "LC_MESSAGES" / "pccpy.po").open("rb") as f:
        return [m for m in read_po(f, locale="en") if m.id]


def test_el_detector_de_espanol_en_las_traducciones_funciona():
    assert palabras_en_espanol("The data must be 1-D, los datos deben ser") == {"los", "datos", "deben"}
    assert palabras_en_espanol("'datos' is empty. {datos}") == set()
    assert palabras_en_espanol("Sample sizes must be positive.") == set()


@pytest.mark.parametrize("mensaje", _catalogo_en(), ids=lambda m: m.id[:50])
def test_la_traduccion_al_ingles_no_tiene_palabras_en_espanol(mensaje):
    assert palabras_en_espanol(mensaje.string) == set(), mensaje.string


# ── errores reales de la API pública, de punta a punta ───────────────────────

CASOS = [
    (lambda: as_1d([], "x"), ValueError, "'x' is empty."),
    (lambda: pccpy.diagnose([1.0, 2.0, 3.0]), ValueError, "diagnose requires at least 4 observations."),
    (lambda: pccpy.run_chart([1.0, 2.0]), ValueError, "run_chart requires at least 3 observations."),
    (lambda: pccpy.wizard(mode="otro"), ValueError, "mode must be 'auto', 'cli' or 'widget'; received 'otro'."),
    (lambda: pccpy.capability_analysis(np.arange(30.0), lsl=12, usl=8), ValueError,
     "The lower limit (lsl) must be less than the upper limit (usl)."),
    (lambda: pccpy.tolerance_interval(np.arange(30.0), coverage=2.0), ValueError, "'coverage' must be in (0, 1)."),
]


@pytest.mark.parametrize(("llamar", "excepcion", "esperado"), CASOS, ids=[c[2][:40] for c in CASOS])
def test_los_errores_reales_salen_en_ingles_y_con_el_mismo_tipo(llamar, excepcion, esperado):
    with pccpy.language("en"), pytest.raises(excepcion) as ei:
        llamar()
    assert str(ei.value) == esperado


def test_los_mismos_errores_siguen_en_espanol_por_defecto():
    with pytest.raises(ValueError, match="está vacío"):
        as_1d([], "x")
    with pytest.raises(ValueError, match="requiere al menos 4 observaciones"):
        pccpy.diagnose([1.0, 2.0, 3.0])


def test_el_aviso_de_valores_no_finitos_sale_en_ingles():
    with pccpy.language("en"), warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        as_1d([1.0, float("nan"), 3.0], "x")
    assert [str(x.message) for x in w] == [
        "'x' contains 1 non-finite value(s) (NaN/inf) at positions [1]. They are excluded from the analysis."
    ]
