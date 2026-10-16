# Trazabilidad: S007-RF-01, S007-RF-02, S007-RF-03 (spec 007).
"""Especificación 007: prueba de Benneyan (rachas de ceros) en la carta G.

Referencia independiente de ``c``: el menor entero con ``p**c <= alpha``, ``alpha = 1 - Phi(k)``, calculado aquí con
logaritmos y comprobado con la potencia exacta. Es una definición propia de pccpy (ver la spec, «No verificable sin la
fuente»), no una equivalencia con Minitab.
"""
import math

import numpy as np
import pytest
from scipy import stats

import pccpy as pp
from pccpy.rules import describe


def _c_manual(p, k=3.0):
    alpha = float(stats.norm.sf(k))
    c = max(1, math.ceil(math.log(alpha) / math.log(p)))
    while p ** c > alpha:  # guarda contra el redondeo del logaritmo
        c += 1
    while c > 1 and p ** (c - 1) <= alpha:
        c -= 1
    return c


def _marcados(chart, panel="G"):
    """Índices (base 0) marcados por la prueba de Benneyan."""
    return chart[panel].violations.get("B", np.array([], dtype=int)).tolist()


# -------------------------------------------------------------------------- RF-01
@pytest.mark.parametrize("p, k", [(0.05, 3.0), (0.3, 3.0), (0.5, 3.0), (0.9, 3.0), (0.05, 2.0), (0.3, 2.0)])
def test_s007_rf_01_umbral_es_el_menor_c_con_p_c_menor_que_alfa(p, k):
    """S007-RF-01: c-1 ceros seguidos no avisan; c ceros seguidos sí, en el c-ésimo."""
    c = _c_manual(p, k)
    assert p ** c <= stats.norm.sf(k) < p ** (c - 1) or c == 1
    x_corto = [5] + [0] * (c - 1) + [7]
    x_largo = [5] + [0] * c + [7]
    assert _marcados(pp.g_chart(x_corto, p=p, k=k, benneyan=True)) == []
    assert _marcados(pp.g_chart(x_largo, p=p, k=k, benneyan=True)) == [c]


def test_s007_rf_01_valor_conocido_p_005_k_3_da_c_3():
    """S007-RF-01: p=0,05, k=3 -> c=3 (0,05**3 = 1,25e-4 <= 0,00135 < 0,05**2)."""
    assert _marcados(pp.g_chart([9, 0, 0, 8], p=0.05, benneyan=True)) == []
    assert _marcados(pp.g_chart([9, 0, 0, 0, 8], p=0.05, benneyan=True)) == [3]


def test_s007_rf_01_p_extremos_dan_c_finito_y_al_menos_1():
    """S007-RF-01 (caso borde): p muy pequeño -> c=1; p cercano a 1 -> c grande pero finito, sin desbordes."""
    assert _marcados(pp.g_chart([4, 0, 6], p=1e-9, benneyan=True)) == [1]
    p = 0.999
    c = _c_manual(p)
    ch = pp.g_chart([3] + [0] * (c + 4), p=p, benneyan=True)
    assert _marcados(ch) == list(range(c, c + 5))


def test_s007_rf_01_falsas_alarmas_por_punto_son_p_c_y_no_superan_alfa():
    """S007-RF-01: Monte Carlo (20 semillas) de la geométrica con p conocido; tasa = p**c <= alfa.

    Con p=0,3 -> c=6, p**c = 7,29e-4. Con 20 x 50 000 puntos se esperan ~729 marcas; el error de Monte Carlo (racha
    de marcas contiguas, sd ~ 37) justifica la tolerancia relativa del 15 %.
    """
    p, n, seeds = 0.3, 50_000, 20
    c = _c_manual(p)
    marcas = 0
    for seed in range(seeds):
        x = np.random.default_rng(seed).geometric(p, n) - 1  # casos antes del evento: P(0) = p
        marcas += len(_marcados(pp.g_chart(x, p=p, benneyan=True)))
    tasa = marcas / (seeds * n)
    assert tasa == pytest.approx(p ** c, rel=0.15)
    assert tasa <= stats.norm.sf(3.0)


# -------------------------------------------------------------------------- RF-02
def test_s007_rf_02_por_defecto_no_se_aplica():
    """S007-RF-02: benneyan=False es el valor por defecto y no cambia nada (guarda frente a 0.15.1)."""
    x = [9, 0, 0, 0, 0, 0, 8]
    a = pp.g_chart(x, p=0.05)
    b = pp.g_chart(x, p=0.05, benneyan=False)
    assert "B" not in a["G"].violations
    assert a.to_frame().equals(b.to_frame())
    assert a.violations().equals(b.violations())


def test_s007_rf_02_marca_desde_el_c_esimo_cero_y_los_siguientes():
    """S007-RF-02: por defecto (benneyan_marks="from_c") se marcan el c-ésimo cero y los siguientes."""
    ch = pp.g_chart([9, 0, 0, 0, 0, 0, 8, 0, 0, 4], p=0.05, benneyan=True)  # c = 3
    assert _marcados(ch) == [3, 4, 5]


def test_s007_rf_02_run_marca_toda_la_racha_que_alcanza_c():
    """S007-RF-02: benneyan_marks="run" marca todos los ceros de la racha que alcanza c, no las rachas más cortas."""
    ch = pp.g_chart([9, 0, 0, 0, 0, 0, 8, 0, 0, 4], p=0.05, benneyan=True, benneyan_marks="run")
    assert _marcados(ch) == [1, 2, 3, 4, 5]


def test_s007_rf_02_violations_lista_la_clave_B_con_descripcion_propia():
    """S007-RF-02: violations() lista la prueba "B" con una descripción propia (no vacía, distinta de las pruebas 1-4)
    y traducida: cambia con el idioma, como el resto de textos visibles (R-17)."""
    ch = pp.g_chart([9, 0, 0, 0, 8], p=0.05, benneyan=True)
    v = ch.violations(stable=True)
    fila = v[v["test"].astype(str) == "B"]
    assert fila["point"].tolist() == [4]
    desc_es = fila["description"].iloc[0]
    assert desc_es.strip()
    assert desc_es not in {describe(t) for t in (1, 2, 3, 4)}
    with pp.language("en"):
        v_en = ch.violations(stable=True)
    desc_en = v_en[v_en["test"].astype(str) == "B"]["description"].iloc[0]
    assert desc_en.strip() and desc_en != desc_es


def test_s007_rf_02_benneyan_marks_invalido_lanza_value_error():
    """S007-RF-02: un valor distinto de "from_c" y "run" lanza ValueError."""
    with pytest.raises(ValueError):
        pp.g_chart([9, 0, 0, 0, 8], p=0.05, benneyan=True, benneyan_marks="todo")


def test_s007_rf_02_se_aplica_aunque_tests_este_vacio():
    """S007-RF-02 (caso borde): benneyan es una opción propia, independiente de ``tests``."""
    ch = pp.g_chart([9, 0, 0, 0, 8], p=0.05, benneyan=True, tests=())
    assert _marcados(ch) == [3]


@pytest.mark.parametrize("x", [[9, 4, 7, 2, 8], [0, 0], [3, 0, 0, 5]])
def test_s007_rf_02_sin_ceros_o_serie_corta_no_hay_senal(x):
    """S007-RF-02 (casos borde): sin ceros, o con menos de c ceros seguidos, no hay señal y no es un error."""
    assert _marcados(pp.g_chart(x, p=0.05, benneyan=True)) == []


def test_s007_rf_02_todo_ceros_con_p_dado_marca_desde_el_c_esimo():
    """S007-RF-02 (caso borde): todos los conteos 0 con p dado -> señal desde el c-ésimo punto."""
    assert _marcados(pp.g_chart([0] * 6, p=0.05, benneyan=True)) == [2, 3, 4, 5]


def test_s007_rf_02_todo_ceros_sin_p_sigue_lanzando_el_error_actual():
    """S007-RF-02 (guarda): sin p y con todos 0, el error es el de siempre, con o sin benneyan."""
    with pytest.raises(ValueError, match="0"):
        pp.g_chart([0, 0, 0], benneyan=True)


# -------------------------------------------------------------------------- RF-03
def test_s007_rf_03_una_racha_que_cruza_la_frontera_de_etapas_no_se_une():
    """S007-RF-03: 2 ceros al final de la etapa 1 y 2 al inicio de la 2 (c=3) no hacen una racha de 4."""
    x = [7, 9, 8, 0, 0, 0, 0, 8, 9, 7]
    ch = pp.g_chart(x, p=0.05, stages=[1] * 5 + [2] * 5, benneyan=True)
    assert _marcados(ch) == []
    # Guarda: sin etapas, los mismos datos sí son una racha de 4.
    assert _marcados(pp.g_chart(x, p=0.05, benneyan=True)) == [5, 6]


def test_s007_rf_03_cada_etapa_usa_su_propio_p():
    """S007-RF-03: sin p, cada etapa estima el suyo y por tanto su propio c.

    Etapa 1 (media 20, p = 1/21) -> c = 3; etapa 2 (media 2,9, p = 1/3,9) -> c = 5.
    Tres ceros seguidos señalan en la etapa 1 y no en la 2.
    """
    e1 = [30, 40, 50, 0, 0, 0]
    e2 = [0, 0, 0, 4, 3, 5, 2, 6, 1, 5]
    ch = pp.g_chart(e1 + e2, stages=[1] * len(e1) + [2] * len(e2), benneyan=True)
    assert _marcados(ch) == [5]
