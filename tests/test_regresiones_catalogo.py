"""Tests de regresión de bugs del catálogo que no tenían (BUG-01, BUG-07, BUG-12) y guardas del flujo de publicación (BUG-13).

Cada test se probó por mutación: reintroduce el bug y falla (ver ``docs/retrospectiva/BUG_CATALOG.md``).
"""
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

import pccpy as pp
from pccpy._data import _excel_writer

RAIZ = Path(__file__).resolve().parents[1]


def _lineas_de_zona(ax):
    return [ln for ln in ax.get_lines() if ln.get_linestyle() == "--"]


@pytest.mark.parametrize("carta", ["xbar_r_chart", "xbar_s_chart"])
def test_bug01_los_paneles_de_dispersion_dibujan_las_zonas(carta):
    """BUG-01: las cartas R/S (paneles asimétricos) también muestran las bandas de 1σ y 2σ con ``zones=True``."""
    datos = np.random.default_rng(0).normal(10, 1, (20, 5))
    fig = getattr(pp, carta)(datos).plot(zones=True)
    try:
        assert len(_lineas_de_zona(fig.axes[0])) >= 4  # Xbar: ±1σ y ±2σ
        assert len(_lineas_de_zona(fig.axes[1])) >= 4  # R o S
        fig_sin = getattr(pp, carta)(datos).plot(zones=False)
        assert len(_lineas_de_zona(fig_sin.axes[1])) == 0
        plt.close(fig_sin)
    finally:
        plt.close(fig)


def test_bug01_la_carta_de_rango_movil_dibuja_las_zonas():
    fig = pp.imr_chart(np.random.default_rng(1).normal(10, 1, 40)).plot(zones=True)
    try:
        assert len(_lineas_de_zona(fig.axes[1])) >= 4  # panel MR
    finally:
        plt.close(fig)


def _sin_openpyxl(monkeypatch):
    """Simula que ``openpyxl`` no está instalado, también sus submódulos ya importados por otros tests (``from openpyxl.workbook …``)."""
    for nombre in [n for n in sys.modules if n == "openpyxl" or n.startswith("openpyxl.")]:
        monkeypatch.setitem(sys.modules, nombre, None)
    monkeypatch.setitem(sys.modules, "openpyxl", None)


def test_bug07_exportar_a_excel_sin_openpyxl_da_instrucciones(monkeypatch, tmp_path):
    """BUG-07: sin ``openpyxl`` el error dice cómo instalarlo (``pip install pccpy[excel]``), no un ``ImportError`` opaco."""
    _sin_openpyxl(monkeypatch)
    with pytest.raises(ImportError, match=r"pccpy\[excel\]"):
        _excel_writer(tmp_path / "a.xlsx")


def test_bug07_to_excel_de_un_resultado_sin_openpyxl(monkeypatch, tmp_path):
    _sin_openpyxl(monkeypatch)
    resultado = pp.capability_analysis(np.random.default_rng(2).normal(10, 1, 50), 6, 14)
    with pytest.raises(ImportError, match=r"pip install openpyxl"):
        resultado.to_excel(tmp_path / "salida.xlsx")


def test_bug12_los_graficos_no_modifican_rcparams():
    """BUG-12: ``.plot()`` no deja cambios en ``matplotlib.rcParams`` (se dibuja dentro de ``plt.rc_context``)."""
    rng = np.random.default_rng(3)
    figuras = {
        "carta": lambda: pp.xbar_r_chart(rng.normal(10, 1, (20, 5))).plot(),
        "capacidad": lambda: pp.capability_analysis(rng.normal(10, 1, 60), 6, 14).plot(),
        "pareto": lambda: pp.pareto({"a": 30, "b": 20, "c": 5}).plot(),
        "gage": lambda: pp.gage_rr(rng.normal(0, 1, 60), 10, 3, 2).plot(),
    }
    for nombre, hacer in figuras.items():
        antes = dict(matplotlib.rcParams)
        hacer()
        plt.close("all")  # algunas funciones devuelven la figura y otras los ejes
        despues = dict(matplotlib.rcParams)
        cambiados = {k for k in antes if antes[k] != despues[k]}
        assert not cambiados, f"{nombre}: .plot() cambió rcParams {sorted(cambiados)}"


def test_bug13_el_flujo_de_publicacion_verifica_la_version_y_los_metadatos():
    """BUG-13: ``publish.yml`` comprueba que el tag del release == versión del wheel y corre ``twine check`` antes de publicar."""
    flujo = (RAIZ / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    assert "twine check" in flujo
    assert "github.event.release.tag_name" in flujo
    assert flujo.index("twine check") < flujo.index("gh-action-pypi-publish")
    assert flujo.index("github.event.release.tag_name") < flujo.index("gh-action-pypi-publish")
