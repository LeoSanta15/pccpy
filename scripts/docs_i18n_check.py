"""Comprueba los catálogos de traducción de la documentación (docs/locales/<idioma>/LC_MESSAGES).

Falla si: un catálogo no está al día con el código fuente de la documentación; hay textos vacíos o *fuzzy*; la traducción
cambia las referencias (roles de Sphinx, URL, número de fragmentos de código o de negritas); o queda texto en español sin
traducir. ``changelog`` queda fuera: el historial de versiones se conserva en el idioma fuente.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from babel.messages.pofile import read_po

RAIZ = Path(__file__).resolve().parent.parent
LOCALES = RAIZ / "docs" / "locales"
EXCLUIDOS = {"changelog"}
PALABRAS_ES = frozenset("de la el en con para por que los las una del al se es un como si sin sobre entre más muy este esta cuando donde".split())
ROL = re.compile(r"((?<![`\w])\{[a-z]+\}`[^`]+`|:[a-z]+:`[^`]+`)")
URL = re.compile(r"https?://[^\s)>\]`]+")


def _mensajes(ruta: Path, idioma: str):
    with ruta.open("rb") as f:
        return [m for m in read_po(f, locale=idioma) if m.id]


def _sin_codigo(texto: str) -> str:
    return re.sub(r"``[^`]*``|`[^`]*`|\{[a-z]+\}`[^`]*`", " ", texto)


def _roles(texto: str) -> Counter:
    """Roles de Sphinx normalizados: ``:func:`x``` (RST) y ``{func}`x``` (MyST) cuentan igual."""
    return Counter(re.sub(r"^:([a-z]+):`", r"{\1}`", r) for r in ROL.findall(texto))


def problemas_de_mensaje(msgid: str, msgstr: str) -> list[str]:
    """Problemas de una traducción concreta (vacía, referencias o texto español)."""
    if not msgstr:
        return ["sin traducir"]
    malos = []
    if _roles(msgid) != _roles(msgstr):
        malos.append("los roles/referencias de Sphinx cambian")
    if Counter(URL.findall(msgid)) != Counter(URL.findall(msgstr)):
        malos.append("las URL cambian")
    for marca in ("`", "**"):
        if msgid.count(marca) != msgstr.count(marca):
            malos.append(f"cambia el número de {marca!r}")
    palabras = [p for p in re.findall(r"[a-záéíóúñ_]+", _sin_codigo(msgstr).lower()) if "_" not in p]  # sin identificadores
    if msgid == msgstr and len(palabras) <= 4:
        return malos  # etiquetas cortas idénticas (nombres, términos del glosario): se aceptan tal cual
    if len(palabras) >= 3 and PALABRAS_ES & set(palabras):
        malos.append("parece quedar texto en español: " + ", ".join(sorted(PALABRAS_ES & set(palabras))))
    return malos


def main() -> int:
    errores = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "sphinx", "-b", "gettext", "-q", str(RAIZ / "docs" / "source"), tmp], check=True)
        pot = {p.relative_to(tmp).with_suffix("").as_posix(): {m.id for m in _mensajes(p, "en")} for p in Path(tmp).rglob("*.pot")}
    for idioma_dir in sorted(LOCALES.iterdir()):
        if not idioma_dir.is_dir():
            continue
        idioma = idioma_dir.name
        catalogos = {p.relative_to(idioma_dir / "LC_MESSAGES").with_suffix("").as_posix(): p for p in (idioma_dir / "LC_MESSAGES").rglob("*.po")}
        for dominio, ids in sorted(pot.items()):
            if dominio in EXCLUIDOS:
                continue
            if dominio not in catalogos:
                errores.append(f"[{idioma}] falta el catálogo de {dominio} (make docs-update)")
                continue
            mensajes = _mensajes(catalogos[dominio], idioma)
            if {m.id for m in mensajes} != ids:
                errores.append(f"[{idioma}] {dominio}: catálogo desactualizado (make docs-update)")
            for m in mensajes:
                if m.fuzzy:
                    errores.append(f"[{idioma}] {dominio}: texto fuzzy: {m.id[:50]!r}")
                for p in problemas_de_mensaje(m.id, m.string):
                    errores.append(f"[{idioma}] {dominio}: {p}: {m.id[:60]!r} ⇒ {m.string[:60]!r}")
    for e in errores:
        print(e)
    if errores:
        print(f"\nERROR: {len(errores)} problema(s) en los catálogos de la documentación")
        return 1
    print(f"OK: catálogos de la documentación al día ({', '.join(sorted(p.name for p in LOCALES.iterdir() if p.is_dir()))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
