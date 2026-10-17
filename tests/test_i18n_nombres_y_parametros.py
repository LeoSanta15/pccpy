"""Regresión: ningún texto de las salidas queda en español al cambiar de idioma.

Las claves de ``params`` y los nombres de paneles (``chart["Zone"]``) son código en inglés y no cambian con el idioma; lo que se muestra
(``summary()``, título del gráfico, etiqueta de ``contributions()``) sí se traduce.
"""
import numpy as np

import pccpy


def test_el_resumen_de_zmr_traduce_los_parametros_y_el_valor_historica():
    x = np.random.default_rng(1).normal(50, 1, 20)
    partes = ["A"] * 10 + ["B"] * 10
    carta = pccpy.zmr_chart(x, partes, mu={"A": 50.0, "B": 50.0}, sigma=1.0)
    with pccpy.language("en"):
        linea = carta.summary().splitlines()[1]
    assert "method=historical" in linea
    assert "histórica" not in linea
    with pccpy.language("es"):
        assert "método=histórica" in carta.summary().splitlines()[1]


def test_el_resumen_de_zmr_traduce_sigma_min_y_max():
    x = np.random.default_rng(1).normal(50, 1, 40)
    carta = pccpy.zmr_chart(x, ["A"] * 20 + ["B"] * 20, mu={"A": 50.0, "B": 50.0}, sigma={"A": 1.0, "B": 2.0})
    assert "sigma_min" in carta.params[0]            # la clave del código está en inglés
    with pccpy.language("en"):
        assert "sigma_min=" in carta.summary() and "sigma_max=" in carta.summary()


def test_la_carta_de_zona_se_muestra_como_zona_en_español_y_zone_en_ingles():
    carta = pccpy.zone_chart(np.random.default_rng(2).normal(0, 1, 50), mu=0.0, sigma=1.0)
    assert carta["Zone"] is not None and carta.kind == "Zone"   # identificadores en inglés, iguales en todos los idiomas
    with pccpy.language("es"):
        assert carta.summary().splitlines()[0] == "Carta de control Zona"
    with pccpy.language("en"):
        assert carta.summary().splitlines()[0] == "Control chart Zone"
        titulo = carta.plot().axes[0].figure._suptitle.get_text()
    assert "Zone" in titulo


def test_la_etiqueta_de_contribuciones_se_traduce():
    rng = np.random.default_rng(3)
    carta = pccpy.t2_chart(rng.multivariate_normal([0, 0], [[1, .3], [.3, 1]], 40))
    with pccpy.language("en"):
        assert carta.contributions(5).name == "contribution (point 5)"
    with pccpy.language("es"):
        assert carta.contributions(5).name == "contribución (punto 5)"
