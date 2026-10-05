"""Genera una tabla español | inglés (agrupada por módulo) para que una persona revise las traducciones.

Uso: python scripts/i18n_revision.py [idioma] > revision.md      (por defecto: en)
"""
from __future__ import annotations

import sys
from pathlib import Path

from babel.messages.pofile import read_po

LOCALES = Path(__file__).resolve().parent.parent / "src" / "pccpy" / "locale"


def _celda(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", "⏎ ").strip()


def main(idioma: str = "en") -> None:
    with (LOCALES / idioma / "LC_MESSAGES" / "pccpy.po").open("rb") as f:
        mensajes = [m for m in read_po(f, locale=idioma) if m.id]
    print(f"# Revisión de la traducción `{idioma}` ({len(mensajes)} textos)\n")
    print("Marca cada fila: ✔ correcta · ✎ cambiar (escribe la propuesta) · ? duda.\n")
    print("| # | Español | Inglés | ✔/✎/? |\n|---|---|---|---|")
    for i, m in enumerate(sorted(mensajes, key=lambda m: m.id.strip().lower()), 1):
        print(f"| {i} | {_celda(m.id)} | {_celda(m.string)} | |")


if __name__ == "__main__":
    main(*sys.argv[1:2])
