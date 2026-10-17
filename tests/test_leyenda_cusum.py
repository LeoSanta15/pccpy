# Trazabilidad: S008-RF-01, S008-RF-02, S008-RF-03 (spec 008).
"""Especificación 008: leyenda de las dos sumas en el gráfico de la CUSUM.

No hay resultado numérico que contrastar: los tests inspeccionan los objetos de matplotlib (leyenda y líneas).
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

import pccpy as pp
from pccpy.plotting import BLUE, ORANGE

RNG = np.random.default_rng(8)
X = np.r_[RNG.normal(100, 2, 40), RNG.normal(104, 2, 40)]
D = RNG.binomial(100, 0.05, 30)
N = RNG.integers(80, 120, 30)

SUPERIOR, INFERIOR = "C+ (suma superior)", "C- (suma inferior)"

CUSUM = [
    lambda: pp.cusum_chart(X),
    lambda: pp.cusum_p_chart(D, N),
    lambda: pp.cusum_c_chart(D),
    lambda: pp.cusum_u_chart(D, 100),
]
SIN_SEGUNDA_SERIE = [
    lambda: pp.imr_chart(X, tests="all"),
    lambda: pp.xbar_r_chart(RNG.normal(100, 2, (25, 4)), tests="all"),
    lambda: pp.ewma_chart(X),
    lambda: pp.g_chart(RNG.geometric(0.05, 40) - 1),
]


@pytest.fixture(autouse=True)
def _cerrar_figuras():
    yield
    plt.close("all")


def _textos(ax):
    leyenda = ax.get_legend()
    return None if leyenda is None else [t.get_text() for t in leyenda.get_texts()]


@pytest.mark.parametrize("make", CUSUM)
def test_s008_rf_01_el_panel_de_la_cusum_tiene_leyenda_con_las_dos_sumas(make):
    """S008-RF-01: dos entradas, «C+ (suma superior)» y «C- (suma inferior)», con los colores de las líneas."""
    ax = make().plot().axes[0]
    assert _textos(ax) == [SUPERIOR, INFERIOR]
    colores = [linea.get_color() for linea in ax.get_legend().get_lines()]
    assert colores == [BLUE, ORANGE]


def test_s008_rf_01_con_varias_etapas_hay_una_sola_leyenda_sin_entradas_repetidas():
    """S008-RF-01 (caso borde): una leyenda por panel, no una por etapa."""
    ax = pp.cusum_chart(X, stages=np.r_[np.ones(40), np.full(40, 2)]).plot().axes[0]
    assert _textos(ax) == [SUPERIOR, INFERIOR]


def test_s008_rf_01_sin_zonas_la_leyenda_es_la_misma():
    """S008-RF-01 (caso borde): zones=False no cambia la leyenda."""
    ax = pp.cusum_chart(X).plot(zones=False).axes[0]
    assert _textos(ax) == [SUPERIOR, INFERIOR]


def test_s008_rf_01_sin_senales_la_leyenda_es_la_misma():
    """S008-RF-01 (caso borde): una CUSUM de un proceso estable, sin señales, también lleva leyenda."""
    estable = pp.cusum_chart(RNG.normal(100, 2, 40), target=100.0, sigma=2.0)
    assert estable.in_control
    assert _textos(estable.plot().axes[0]) == [SUPERIOR, INFERIOR]


@pytest.mark.parametrize("make", SIN_SEGUNDA_SERIE)
def test_s008_rf_01_las_cartas_sin_segunda_serie_no_llevan_leyenda(make):
    """S008-RF-01 (guarda: pasa antes y después): ningún panel sin segunda serie tiene leyenda."""
    assert all(ax.get_legend() is None for ax in make().plot().axes)


@pytest.mark.parametrize("make", CUSUM)
def test_s008_rf_02_no_cambia_ni_los_datos_ni_el_estado_global(make):
    """S008-RF-02 (guarda: pasa antes y después): dibujar no altera los datos, las tablas ni matplotlib.rcParams."""
    carta = make()
    antes_tabla = carta.to_frame(stable=True).copy()
    antes_violaciones = carta.violations(stable=True).copy()
    antes_resumen = carta.summary()
    rc = dict(matplotlib.rcParams)

    ax = carta.plot().axes[0]

    assert dict(matplotlib.rcParams) == rc
    assert carta.to_frame(stable=True).equals(antes_tabla)
    assert carta.violations(stable=True).equals(antes_violaciones)
    assert carta.summary() == antes_resumen
    panel = carta.panels[0]
    azul = [lin for lin in ax.get_lines() if lin.get_color() == BLUE and lin.get_marker() == "o"]
    naranja = [lin for lin in ax.get_lines() if lin.get_color() == ORANGE and lin.get_marker() == "o"]
    assert len(azul) == 1 and len(naranja) == 1
    np.testing.assert_array_equal(azul[0].get_ydata(), panel.values)
    np.testing.assert_array_equal(naranja[0].get_ydata(), panel.secondary)


def test_s008_rf_03_la_leyenda_se_traduce_al_ingles():
    """S008-RF-03: con el idioma en inglés las dos entradas no están vacías y difieren de las españolas."""
    carta = pp.cusum_chart(X)
    es = _textos(carta.plot().axes[0])
    with pp.language("en"):
        en = _textos(carta.plot().axes[0])
    assert es == [SUPERIOR, INFERIOR]
    assert en is not None and len(en) == 2 and all(t.strip() for t in en)
    assert en[0] != es[0] and en[1] != es[1]
