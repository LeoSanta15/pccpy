"""Configuración de Sphinx para la documentación de pccpy."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Si pccpy no está instalado (pip install -e ".[docs]"), autodoc no podrá importarlo;
# esto solo ayuda a encontrarlo si alguien corre sphinx-build sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pccpy  # noqa: E402

project = "pccpy"
author = "LeoSanta15"
copyright = "2026, LeoSanta15"
release = pccpy.__version__
version = pccpy.__version__

# Idioma fuente: español. Para el inglés: ``sphinx-build -D language=en`` (make docs-en) o, en Read the Docs,
# un segundo proyecto como traducción (READTHEDOCS_LANGUAGE).
language = os.environ.get("READTHEDOCS_LANGUAGE", "es")
locale_dirs = ["../locales"]   # docs/locales/<idioma>/LC_MESSAGES/*.po
gettext_compact = False        # un catálogo por página
gettext_location = False       # sin números de línea: diffs de catálogo más pequeños
gettext_uuid = False

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
html_title = f"pccpy {version}"

# pccpy importa numpy/scipy/pandas/matplotlib; si alguna no estuviera instalada
# al construir la documentación (p. ej. en un entorno mínimo), se simulan aquí
# para que autodoc no falle por completo. En un entorno con "pip install -e .[docs]"
# esto no hace nada porque los módulos reales ya están disponibles.
autodoc_mock_imports = []
