"""Genera las figuras y las salidas de los ejemplos que muestran los README (``docs/imagenes/<idioma>/``).

Ejecuta ``examples/basic_example.py`` y ``examples/advanced_example.py`` en una carpeta temporal, una vez en español y otra
en inglés (``PCCPY_LANG``), copia las figuras (PNG con paleta de 256 colores, para que pesen poco) y guarda lo que imprimen
(``output_<ejemplo>.txt``). Los README embeben esos textos y enlazan las figuras con URL absolutas, porque en la página de PyPI
los enlaces relativos dan 404.

Uso:  python scripts/generar_figuras_readme.py
Tras regenerar, revisa el diff y actualiza a mano los bloques de salida de las secciones «Ejemplos con resultados» de
``README.md`` y ``README_en.md``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "docs" / "imagenes"
EJEMPLOS = ("basic_example", "advanced_example")


def _optimizar(origen: Path, destino: Path) -> None:
    with Image.open(origen) as im:
        im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(destino, optimize=True)


def generar(idioma: str) -> None:
    carpeta = DESTINO / idioma
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "PCCPY_LANG": idioma, "MPLBACKEND": "Agg", "PYTHONHASHSEED": "0"}
        for nombre in EJEMPLOS:
            res = subprocess.run([sys.executable, str(RAIZ / "examples" / f"{nombre}.py")], cwd=tmp, env=env,
                                 capture_output=True, text=True, check=True)
            texto = res.stdout.replace(str(Path(tmp).resolve() / "output"), "output").replace(f"{tmp}/output", "output")
            (carpeta / f"output_{nombre}.txt").write_text(texto, encoding="utf-8")
        for png in sorted((Path(tmp) / "output").glob("*.png")):
            _optimizar(png, carpeta / png.name)


if __name__ == "__main__":
    for idioma in ("es", "en"):
        generar(idioma)
        peso = sum(p.stat().st_size for p in (DESTINO / idioma).glob("*.png")) / 1024
        print(f"{idioma}: {len(list((DESTINO / idioma).glob('*.png')))} figuras, {peso:.0f} KB")
