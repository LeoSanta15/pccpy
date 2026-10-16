# Trazabilidad: S002-RF-01, S002-RF-02, S002-RF-03 (spec 002).
"""Especificación 002: carta T con duraciones iguales a 0."""
import warnings

import numpy as np
import pytest
from scipy import stats

import pccpy as pp

SERIE = [1.2, 3.4, 2.2, 5.1, 0.8, 2.9, 1.7, 4.4, 2.6, 3.1]


def test_s002_rf_01_un_cero_se_nombra_con_su_posicion():
    """S002-RF-01: el mensaje habla de ceros y cita la posición."""
    with pytest.raises(ValueError, match=r"cero.*\[0\]|\[0\].*cero"):
        pp.t_chart([0.0] + SERIE)


def test_s002_rf_01_un_negativo_no_se_presenta_como_cero():
    """S002-RF-01: un negativo da un mensaje de negativos, no de ceros."""
    with pytest.raises(ValueError) as e:
        pp.t_chart(SERIE[:3] + [-1.0] + SERIE[3:])
    assert "negativ" in str(e.value).lower()
    assert "iguales a 0" not in str(e.value)


def test_s002_rf_01_cero_y_negativo_juntos_mencionan_ambos():
    """S002-RF-01: caso borde con cero y negativo en la misma serie."""
    with pytest.raises(ValueError) as e:
        pp.t_chart([0.0, -1.0] + SERIE)
    assert "negativ" in str(e.value).lower() and "cero" in str(e.value).lower()


@pytest.mark.parametrize("dist", ["weibull", "exponential"])
def test_s002_rf_02_zeros_drop_equivale_a_la_serie_sin_ceros(dist):
    """S002-RF-02: ``zeros="drop"`` da el resultado de la serie sin ceros y avisa de cuántos."""
    con_ceros = SERIE[:4] + [0.0] + SERIE[4:] + [0.0]
    with pytest.warns(UserWarning, match="2"):
        a = pp.t_chart(con_ceros, distribution=dist, zeros="drop")
    b = pp.t_chart(SERIE, distribution=dist)
    assert a["T"].ucl[0] == pytest.approx(b["T"].ucl[0], rel=1e-12)
    assert a["T"].lcl[0] == pytest.approx(b["T"].lcl[0], rel=1e-12)
    assert len(a["T"].values) == len(SERIE)


def test_s002_rf_02_los_limites_coinciden_con_un_ajuste_aparte():
    """S002-RF-02: referencia independiente, ``scipy.stats.weibull_min.fit(floc=0)``."""
    with pytest.warns(UserWarning):
        ch = pp.t_chart([0.0] + SERIE, zeros="drop")
    c, _, sc = stats.weibull_min.fit(SERIE, floc=0)
    assert ch.params[0]["forma"] == pytest.approx(c, rel=1e-4)
    assert ch.params[0]["escala"] == pytest.approx(sc, rel=1e-4)


def test_s002_rf_02_por_defecto_sigue_siendo_error():
    """S002-RF-02: ``zeros="error"`` (y omitirlo) rechaza los ceros y sugiere la opción."""
    for kw in ({}, {"zeros": "error"}):
        with pytest.raises(ValueError, match="zeros"):
            pp.t_chart([0.0] + SERIE, **kw)


def test_s002_rf_02_todo_ceros_y_valor_invalido():
    """S002-RF-02: sin datos tras excluir, o ``zeros`` desconocido, es ``ValueError``."""
    with pytest.raises(ValueError), pytest.warns(UserWarning):
        pp.t_chart([0.0, 0.0, 0.0], zeros="drop")
    with pytest.raises(ValueError):
        pp.t_chart(SERIE, zeros="otro")


def test_s002_rf_02_los_negativos_se_rechazan_aunque_se_excluyan_ceros():
    """S002-RF-02: ``zeros="drop"`` no oculta los negativos."""
    with pytest.raises(ValueError, match="(?i)negativ"):
        pp.t_chart([0.0, -1.0] + SERIE, zeros="drop")


def test_s002_rf_03_con_datos_positivos_no_cambia_nada():
    """S002-RF-03: guarda; sin ceros ``zeros`` no altera el resultado ni emite avisos."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        a = pp.t_chart(SERIE)
        b = pp.t_chart(SERIE, zeros="drop")
    for clave in ("ucl", "lcl", "center"):
        assert np.allclose(getattr(a["T"], clave), getattr(b["T"], clave), rtol=0, atol=0)
