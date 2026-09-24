"""Configuración de Sphinx para la documentación de spyc."""
from __future__ import annotations

import sys
from pathlib import Path

# Si spyc no está instalado (pip install -e ".[docs]"), autodoc no podrá importarlo;
# esto solo ayuda a encontrarlo si alguien corre sphinx-build sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import spyc  # noqa: E402

project = "spyc"
author = "Autores de spyc"
copyright = "2026, Autores de spyc"
release = spyc.__version__
version = spyc.__version__

language = "es"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- autodoc / napoleon -----------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {"members": True, "undoc-members": False, "show-inheritance": False}
autosummary_generate = False  # las páginas de referencia se escriben a mano

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = False

# -- HTML ---------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = f"spyc {version}"

# spyc importa numpy/scipy/pandas/matplotlib; si alguna no estuviera instalada
# al construir la documentación (p. ej. en un entorno mínimo), se simulan aquí
# para que autodoc no falle por completo. En un entorno con "pip install -e .[docs]"
# esto no hace nada porque los módulos reales ya están disponibles.
autodoc_mock_imports = []
