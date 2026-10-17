# Trazabilidad: S009-RF-09 (spec 009).
"""Especificación 009, RF-09: las funciones de ARL se exportan, se documentan y se validan."""
from pathlib import Path

import pytest

import pccpy as pp

RAIZ = Path(__file__).resolve().parent.parent
FUNCIONES = ["arl_shewhart", "arl_cusum", "arl_ewma", "arl_sd", "arl_range", "arl_binomial", "arl_poisson", "arl_g", "arl_t"]
IDS = ["arl-shewhart", "arl-cusum", "arl-ewma", "arl-sd", "arl-range", "arl-binomial", "arl-poisson", "arl-g", "arl-t"]


@pytest.mark.parametrize("nombre", FUNCIONES)
def test_s009_rf_09_cada_funcion_esta_exportada_y_documentada(nombre):
    """S009-RF-09: está en ``__all__``, tiene docstring con sus supuestos y aparece en la página de referencia."""
    assert nombre in pp.__all__
    doc = getattr(pp, nombre).__doc__ or ""
    assert "ARL" in doc and "Parameters" in doc
    referencia = (RAIZ / "docs/source/referencia/arl.rst").read_text(encoding="utf-8")
    assert f".. autofunction:: pccpy.{nombre}" in referencia


def test_s009_rf_09_la_guia_y_el_readme_mencionan_el_arl():
    """S009-RF-09: la guía existe, está enlazada desde el índice y los dos README la citan."""
    guia = (RAIZ / "docs/source/arl.md").read_text(encoding="utf-8")
    assert "pp.arl_cusum" in guia and "Supuestos" in guia
    assert "\narl\n" in (RAIZ / "docs/source/index.md").read_text(encoding="utf-8")
    for readme in ("README.md", "README_en.md"):
        assert "pp.arl_shewhart" in (RAIZ / readme).read_text(encoding="utf-8")


def test_s009_rf_09_hay_una_comprobacion_de_validacion_por_funcion_y_pasan():
    """S009-RF-09: ``run_validation`` incluye una comprobación por función de ARL, con referencia independiente, y todas pasan."""
    informe = pp.run_validation(IDS)
    assert [c.id for c in informe.checks] == IDS
    assert informe.passed, informe.summary()
    assert all(c.source and c.tolerance > 0 for c in informe.checks)
