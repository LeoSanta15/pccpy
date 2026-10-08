"""Cartas I-MR, Xbar-R y Xbar-S con ``transform=`` y ``scale=``."""
from __future__ import annotations

import warnings

import matplotlib
import numpy as np
import pytest
from scipy import stats

import pccpy as pp
from pccpy.transforms import Transformation, fit_transformation

matplotlib.use("Agg")

X = stats.lognorm.rvs(0.6, size=100, random_state=1) * 5
G = stats.lognorm.rvs(0.6, size=(30, 4), random_state=2) * 5


@pytest.fixture(autouse=True)
def _cerrar():
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


def test_la_carta_transformada_equivale_a_la_carta_normal_de_los_datos_transformados():
    t = fit_transformation(X, "boxcox")
    manual = pp.imr_chart(t.forward(X), tests=(1, 2))
    c = pp.imr_chart(X, transform="boxcox", scale="transformed", tests=(1, 2))
    for nombre in ("I", "MR"):
        for campo in ("values", "center", "ucl", "lcl"):
            assert getattr(c[nombre], campo) == pytest.approx(getattr(manual[nombre], campo), nan_ok=True)
        assert c[nombre].violations.keys() == manual[nombre].violations.keys()
    assert c.transformation.method == "boxcox" and c.chart_scale == "transformed"


def test_escala_original_es_la_inversa_de_los_limites_transformados():
    t = fit_transformation(X, "boxcox")
    lam = t.params["lambda"]
    inv = lambda z: (lam * z + 1) ** (1 / lam)  # noqa: E731 - inversa de Box-Cox escrita aparte
    ct = pp.imr_chart(X, transform=t, scale="transformed")
    co = pp.imr_chart(X, transform=t)  # por defecto: escala original
    assert co["I"].values == pytest.approx(X)  # los datos originales, sin redondeo
    for campo in ("center", "ucl", "lcl"):
        assert getattr(co["I"], campo) == pytest.approx(inv(getattr(ct["I"], campo)))
    sigma, centro = ct["I"].sigma, ct["I"].center
    for k in (1, 2):
        assert co["I"].zones_upper[k] == pytest.approx(inv(centro + k * sigma))
        assert co["I"].zones_lower[k] == pytest.approx(inv(centro - k * sigma))
    # los límites son asimétricos respecto a la línea central
    assert co["I"].ucl[0] - co["I"].center[0] > co["I"].center[0] - co["I"].lcl[0]
    # la dispersión se queda en la escala transformada
    assert co["MR"].values == pytest.approx(ct["MR"].values, nan_ok=True) and co["MR"].ucl == pytest.approx(ct["MR"].ucl)


def test_las_senales_no_dependen_de_la_escala():
    a = pp.imr_chart(X, transform="yeo-johnson", tests=(1, 2, 3))
    b = pp.imr_chart(X, transform="yeo-johnson", scale="transformed", tests=(1, 2, 3))
    for nombre in ("I", "MR"):
        assert {t: v.tolist() for t, v in a[nombre].violations.items()} == \
               {t: v.tolist() for t, v in b[nombre].violations.items()}


@pytest.mark.parametrize("carta, disp", [(pp.xbar_r_chart, "R"), (pp.xbar_s_chart, "S")])
def test_xbar_con_transformacion(carta, disp):
    t = fit_transformation(G.ravel(), "yeo-johnson")
    manual = carta(t.forward(G))
    ct = carta(G, transform="yeo-johnson", scale="transformed")
    co = carta(G, transform="yeo-johnson")
    assert ct["Xbar"].ucl == pytest.approx(manual["Xbar"].ucl) and ct[disp].ucl == pytest.approx(manual[disp].ucl)
    assert co["Xbar"].ucl == pytest.approx(t.inverse(manual["Xbar"].ucl))
    assert co["Xbar"].values == pytest.approx(t.inverse(manual["Xbar"].values))
    assert co[disp].values == pytest.approx(manual[disp].values)  # R o S: escala transformada


def test_subgrupos_1d_y_etapas():
    c = pp.xbar_r_chart(G.ravel(), subgroup_size=4, transform="boxcox", stages=np.repeat([1, 2], 15))
    assert len(c.params) == 2 and c.transformation.method == "boxcox"


def test_reutilizar_la_transformacion_con_datos_nuevos():
    c = pp.imr_chart(X, transform="boxcox")
    nuevos = stats.lognorm.rvs(0.6, size=40, random_state=9) * 5
    prm = c.params[0]
    c2 = pp.imr_chart(nuevos, transform=c.transformation, mu=prm["media"], sigma=prm["sigma"])
    assert c2["I"].ucl == pytest.approx(c["I"].ucl[0])  # mismos límites congelados, en unidades originales
    assert c2["I"].values == pytest.approx(nuevos)


def test_con_datos_asimetricos_la_carta_normal_da_mas_falsas_alarmas_que_la_transformada():
    """Lognormal bajo control (σ = 0,8): la carta I normal se sale por arriba mucho más que el 0,27 % esperado."""
    rng = np.random.default_rng(5)
    normal = transf = total = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(60):
            x = rng.lognormal(1, 0.8, 100)
            normal += len(pp.imr_chart(x)["I"].violations.get(1, []))
            transf += len(pp.imr_chart(x, transform="boxcox")["I"].violations.get(1, []))
            total += 100
    assert normal / total > 0.01 and transf / total < 0.006  # medido: ≈ 1,9 % frente a ≈ 0,3 %
    assert normal > 3 * transf


@pytest.mark.parametrize("llamada, texto", [
    (lambda: pp.imr_chart(X, transform="x"), "transform"),
    (lambda: pp.imr_chart(X, transform="boxcox", scale="x"), "scale"),
    (lambda: pp.imr_chart(X - X.max() - 1, transform="boxcox"), "positivos"),
    (lambda: pp.xbar_r_chart(G, scale="x"), "scale"),
])
def test_errores(llamada, texto):
    with pytest.raises(ValueError, match=texto):
        llamada()


def test_fase_i_todavia_no_admite_transform():
    with pytest.raises(ValueError, match="transform"):
        pp.phase_one(pp.imr_chart, X, transform="boxcox")


def test_sin_transform_no_cambia_nada():
    c = pp.imr_chart(X)
    assert c.transformation is None and c["I"].zones_upper is None and "Transformación" not in c.summary()


@pytest.mark.parametrize("escala", ["original", "transformed"])
def test_resumen_grafico_y_tabla(escala):
    c = pp.imr_chart(X, transform="johnson", scale=escala)
    assert "Transformación Johnson" in c.summary()
    assert c.plot() is not None and "I_ucl" in c.to_frame(stable=True).columns
    with pp.language("en"):
        assert "Transformation Johnson" in c.summary()


def test_ylabel_de_dispersion_avisa_de_la_escala():
    c = pp.imr_chart(X, transform="boxcox")
    assert "escala transformada" in c["MR"].ylabel and "escala transformada" not in c["I"].ylabel


@pytest.mark.parametrize("metodo, z", [("boxcox", -10.0), ("yeo-johnson", 50.0)])
def test_inversa_fuera_de_rango_va_al_extremo_del_soporte(metodo, z):
    lam = 0.5 if metodo == "boxcox" else -0.5
    t = Transformation(metodo, {"lambda": lam})
    out = t.inverse(z)
    assert out == (0.0 if metodo == "boxcox" else np.inf)
    t2 = Transformation("boxcox", {"lambda": -0.5})
    assert t2.inverse(10.0) == np.inf
