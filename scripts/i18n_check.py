"""Comprueba que los catálogos de traducción están al día.

Uso::

    python scripts/i18n_check.py

Falla (código 1) si:

1. los textos marcados con ``tr()`` / ``N_()`` en ``src/`` no coinciden con ``src/pccpy/locale/pccpy.pot``
   (ejecuta ``make i18n-update``);
2. algún idioma tiene un texto sin traducir, ``fuzzy`` o con marcadores ``{…}`` distintos de los del original
   (un marcador distinto provoca un ``KeyError`` al mostrar el mensaje);
3. el ``.mo`` compilado no corresponde a su ``.po`` (ejecuta ``make i18n-compile``).
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

from babel.messages.extract import extract_from_dir
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "src"
LOCALES = SRC / "pccpy" / "locale"
POT = LOCALES / "pccpy.pot"
MARCADOR = re.compile(r"\{[^{}]*\}")


def textos_del_codigo() -> set[str]:
    """Textos literales pasados a ``tr()`` o ``N_()`` en ``src/``."""
    encontrados: set[str] = set()
    for _archivo, _linea, mensaje, _comentarios, _contexto in extract_from_dir(
        str(SRC), method_map=[("**.py", "python")], keywords={"tr": None, "N_": None}
    ):
        if isinstance(mensaje, str) and mensaje:
            encontrados.add(mensaje)
    return encontrados


def textos_del_pot() -> set[str]:
    with POT.open("rb") as f:
        return {m.id for m in read_po(f) if m.id and isinstance(m.id, str)}


def marcadores(texto: str) -> list[str]:
    return sorted(MARCADOR.findall(texto))


def revisar_idioma(carpeta: Path, esperados: set[str]) -> list[str]:
    idioma = carpeta.name
    po = carpeta / "LC_MESSAGES" / "pccpy.po"
    mo = carpeta / "LC_MESSAGES" / "pccpy.mo"
    problemas: list[str] = []
    if not po.is_file():
        return [f"[{idioma}] falta {po.relative_to(RAIZ)}"]
    with po.open("rb") as f:
        catalogo = read_po(f, locale=idioma)
    traducidos = {m.id: m for m in catalogo if m.id and isinstance(m.id, str)}
    for texto in sorted(esperados):
        m = traducidos.get(texto)
        if m is None or not m.string:
            problemas.append(f"[{idioma}] sin traducir: {texto[:70]!r}")
        elif m.fuzzy:
            problemas.append(f"[{idioma}] marcado fuzzy (revisar): {texto[:70]!r}")
        elif isinstance(m.string, str) and marcadores(m.string) != marcadores(texto):
            problemas.append(f"[{idioma}] marcadores distintos {marcadores(texto)} vs {marcadores(m.string)}: {texto[:60]!r}")
    for texto in sorted(set(traducidos) - esperados):
        problemas.append(f"[{idioma}] texto que ya no existe en el código: {texto[:70]!r}")
    if not mo.is_file():
        problemas.append(f"[{idioma}] falta {mo.relative_to(RAIZ)} (make i18n-compile)")
    else:
        compilado = io.BytesIO()
        write_mo(compilado, catalogo)
        if compilado.getvalue() != mo.read_bytes():
            problemas.append(f"[{idioma}] el .mo no corresponde al .po (make i18n-compile)")
    return problemas


def main() -> int:
    if not POT.is_file():
        print(f"ERROR: falta {POT.relative_to(RAIZ)} (make i18n-extract)")
        return 1
    codigo, pot = textos_del_codigo(), textos_del_pot()
    problemas: list[str] = []
    for texto in sorted(codigo - pot):
        problemas.append(f"[pot] texto nuevo sin extraer: {texto[:70]!r}")
    for texto in sorted(pot - codigo):
        problemas.append(f"[pot] texto que ya no existe en el código: {texto[:70]!r}")
    idiomas = sorted(d for d in LOCALES.glob("*") if d.is_dir())
    for carpeta in idiomas:
        problemas += revisar_idioma(carpeta, codigo)
    for p in problemas:
        print(p)
    if problemas:
        print(f"\nERROR: {len(problemas)} problema(s) en los catálogos de traducción (make i18n-update / make i18n-compile).")
        return 1
    print(f"OK: {len(codigo)} textos; idiomas con catálogo: {', '.join(d.name for d in idiomas) or 'ninguno'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
