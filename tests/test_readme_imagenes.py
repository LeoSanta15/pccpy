"""Las figuras de los README (es/en) existen, se enlazan con URL absoluta y no pesan de más.

PyPI no resuelve rutas relativas: las imágenes van en ``docs/imagenes/<idioma>/`` y se enlazan con ``raw.githubusercontent.com``.
Se regeneran con ``python scripts/generar_figuras_readme.py``.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
BASE = "https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes"
README = {"es": "README.md", "en": "README_en.md"}


def _imagenes(texto: str) -> list[str]:
    """Figuras del README (las insignias de shields.io no cuentan)."""
    return [u for u in re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", texto) if "img.shields.io" not in u]


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_las_imagenes_del_readme_son_absolutas_y_existen(idioma):
    urls = _imagenes((RAIZ / README[idioma]).read_text(encoding="utf-8"))
    assert urls, f"{README[idioma]} no tiene figuras"
    for url in urls:
        assert url.startswith(f"{BASE}/{idioma}/"), url
        assert (RAIZ / "docs" / "imagenes" / idioma / url.rsplit("/", 1)[1]).is_file(), url


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_todas_las_figuras_de_los_ejemplos_estan_en_el_readme(idioma):
    carpeta = RAIZ / "docs" / "imagenes" / idioma
    en_readme = {u.rsplit("/", 1)[1] for u in _imagenes((RAIZ / README[idioma]).read_text(encoding="utf-8"))}
    en_disco = {p.name for p in carpeta.glob("*.png")}
    assert len(en_disco) == 25
    assert en_disco == en_readme


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_las_figuras_pesan_poco(idioma):
    for png in (RAIZ / "docs" / "imagenes" / idioma).glob("*.png"):
        assert png.stat().st_size < 120_000, png.name


def test_los_dos_readme_tienen_las_mismas_figuras():
    es = [u.rsplit("/", 1)[1] for u in _imagenes((RAIZ / README["es"]).read_text(encoding="utf-8"))]
    en = [u.rsplit("/", 1)[1] for u in _imagenes((RAIZ / README["en"]).read_text(encoding="utf-8"))]
    assert es == en


def test_el_indice_de_los_readme_incluye_la_seccion_de_ejemplos():
    for nombre, ancla in (("README.md", "#ejemplos-con-resultados"), ("README_en.md", "#worked-examples-with-results")):
        texto = (RAIZ / nombre).read_text(encoding="utf-8")
        assert f"]({ancla})" in texto
        numeros = [int(n) for n in re.findall(r"^(\d+)\. \[", texto, re.MULTILINE)]
        assert numeros == list(range(1, len(numeros) + 1)), f"{nombre}: numeración del índice rota"


# ── los ejemplos: código de ``examples/`` en inglés; en los README los nombres de variable siguen el idioma del README ── ──────────────────────────────


def _codigo_de_ejemplos(nombre: str, inicio: str, fin: str) -> list[str]:
    texto = (RAIZ / nombre).read_text(encoding="utf-8")
    seccion = texto[texto.index(inicio):texto.index(fin)]
    bloques = re.findall(r"```python\n([\s\S]*?)\n```", seccion)
    return [re.sub(r"[ \t]*#.*", "", b) for b in bloques]  # sin comentarios: esos sí van en el idioma del README


def _seccion(nombre: str, inicio: str, fin: str) -> str:
    texto = (RAIZ / nombre).read_text(encoding="utf-8")
    return texto[texto.index(inicio):texto.index(fin)]


def _versiones_minimas() -> bool:
    import numpy as np

    return tuple(int(p) for p in np.__version__.split(".")[:2]) < (1, 26)


@pytest.mark.skipif(_versiones_minimas(), reason=(
    "Las salidas del README salen de numpy >= 1.26 y scipy >= 1.11: con las versiones mínimas declaradas (numpy 1.22, scipy 1.9) "
    "`multivariate_normal` y los ajustes de máxima verosimilitud difieren en las últimas cifras y las salidas no coinciden "
    "línea a línea; la reproducibilidad se comprueba en el resto de la matriz de Python."))
@pytest.mark.parametrize(("nombre", "inicio", "fin", "idioma"), [
    ("README.md", "## Ejemplos con resultados", "## Cartas de variables", "es"),
    ("README_en.md", "## Worked examples with results", "## Variables charts", "en"),
])
def test_los_fragmentos_del_readme_reproducen_las_salidas_que_muestran(nombre, inicio, fin, idioma):
    """Ejecutados en orden, los fragmentos imprimen cada línea de salida que el README enseña (salvo las abreviadas con «…»)."""
    import contextlib
    import io

    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np

    import pccpy

    matplotlib.use("Agg")
    seccion = _seccion(nombre, inicio, fin)
    bloques = re.findall(r"```python\n([\s\S]*?)\n```", seccion)
    salidas = re.findall(r"```text\n([\s\S]*?)\n```", seccion)
    assert bloques and salidas
    espacio = {"np": np, "pp": pccpy}
    impreso = io.StringIO()
    with pccpy.language(idioma), contextlib.redirect_stdout(impreso):
        for bloque in bloques:
            exec(bloque, espacio)  # noqa: S102
    plt.close("all")
    ausentes = [ln for o in salidas for ln in o.split("\n") if ln.strip() not in ("", "…") and ln.rstrip() not in impreso.getvalue()]
    assert ausentes == []


def test_el_readme_en_español_usa_nombres_de_variable_en_español_y_el_ingles_no():
    es = "\n".join(re.sub(r"[ \t]*#.*", "", b) for b in re.findall(
        r"```python\n([\s\S]*?)\n```", _seccion("README.md", "## Ejemplos con resultados", "## Cartas de variables")))
    en = "\n".join(re.sub(r"[ \t]*#.*", "", b) for b in re.findall(
        r"```python\n([\s\S]*?)\n```", _seccion("README_en.md", "## Worked examples with results", "## Variables charts")))
    assert re.search(r"\b(carta|subgrupos|defectuosos|datos|tiempos)\b", es)
    assert not re.search(r"\b(carta|subgrupos|defectuosos|datos|tiempos|tabla|etapas)\b", en)


def test_los_ejemplos_estan_en_ingles_y_sin_texto_propio():
    """Los scripts de ``examples/`` solo usan ASCII: ni identificadores ni mensajes propios en español (S/ C)."""
    for ejemplo in (RAIZ / "examples").glob("*.py"):
        assert ejemplo.read_text(encoding="utf-8").isascii(), ejemplo.name


def test_las_salidas_en_ingles_no_tienen_texto_en_espanol():
    for salida in (RAIZ / "docs" / "imagenes" / "en").glob("output_*.txt"):
        texto = salida.read_text(encoding="utf-8")
        assert not re.search(r"[áéíóúñÁÉÍÓÚ¿¡]", texto), salida.name
