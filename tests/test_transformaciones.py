"""Transformaciones de normalización (Box-Cox, Yeo-Johnson, Johnson) y ``capability_analysis(transform=...)``."""
from __future__ import annotations

import matplotlib
import numpy as np
import pytest
from scipy import stats
from scipy.special import boxcox

import pccpy as pp
from pccpy.normality import anderson_darling_pvalue, anderson_darling_statistic
from pccpy.transforms import Transformation, fit_transformation

matplotlib.use("Agg")

RNG = np.random.default_rng(0)
SU = stats.johnsonsu.rvs(0.5, 1.5, loc=10, scale=2, size=300, random_state=RNG)
SB = stats.johnsonsb.rvs(0.3, 1.2, loc=0, scale=10, size=300, random_state=RNG)
NEGATIVA = -stats.gamma.rvs(2, size=200, random_state=RNG) * 2 + 30  # asimétrica a la izquierda
MIXTA = np.concatenate([-stats.gamma.rvs(2, size=60, random_state=RNG), stats.gamma.rvs(2, size=140, random_state=RNG)])


def _p_ad(z):
    return anderson_darling_pvalue(anderson_darling_statistic(z), len(z))


@pytest.fixture(autouse=True)
def _cerrar():
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


# ───────────────────────────────────────── fórmulas contra scipy ─────────────
@pytest.mark.parametrize("familia, dist, args", [
    ("SU", stats.johnsonsu, (0.5, 1.5, 10.0, 2.0)),
    ("SB", stats.johnsonsb, (0.3, 1.2, 0.0, 10.0)),
])
def test_johnson_forward_es_la_normal_inversa_de_la_cdf(familia, dist, args):
    a, b, loc, scale = args
    t = Transformation("johnson", {"family": familia, "a": a, "b": b, "loc": loc, "scale": scale})
    x = dist.rvs(*args, size=50, random_state=1)
    assert t.forward(x) == pytest.approx(stats.norm.ppf(dist.cdf(x, *args)), abs=1e-8)


def test_johnson_sl_es_la_lognormal_de_tres_parametros():
    s, loc, scale = 0.5, 2.0, 3.0
    t = Transformation("johnson", {"family": "SL", "a": 0.0, "b": 1 / s, "loc": loc, "scale": scale})
    x = stats.lognorm.rvs(s, loc, scale, size=50, random_state=2)
    assert t.forward(x) == pytest.approx(stats.norm.ppf(stats.lognorm.cdf(x, s, loc, scale)), abs=1e-8)


@pytest.mark.parametrize("lam", [-1.0, 0.0, 0.5, 2.0, 2.5])
def test_yeo_johnson_coincide_con_scipy(lam):
    t = Transformation("yeo-johnson", {"lambda": lam})
    assert t.forward(MIXTA) == pytest.approx(stats.yeojohnson(MIXTA, lmbda=lam), rel=1e-9, abs=1e-9)


def test_los_ajustes_de_lambda_coinciden_con_scipy():
    x = np.abs(MIXTA) + 0.5
    assert fit_transformation(x, "boxcox").params["lambda"] == pytest.approx(stats.boxcox(x)[1])
    assert fit_transformation(MIXTA, "yeo-johnson").params["lambda"] == pytest.approx(stats.yeojohnson(MIXTA)[1])
    t = fit_transformation(x, "boxcox")
    assert t.forward(x) == pytest.approx(boxcox(x, t.params["lambda"]))


@pytest.mark.parametrize("metodo, datos", [("boxcox", np.abs(MIXTA) + 0.5), ("yeo-johnson", MIXTA),
                                           ("johnson", SU), ("johnson", SB), ("johnson", NEGATIVA)])
def test_ida_y_vuelta(metodo, datos):
    t = fit_transformation(datos, metodo)
    assert t.inverse(t.forward(datos)) == pytest.approx(datos, rel=1e-7, abs=1e-7)
    assert Transformation.from_info(t.info()).forward(datos[:5]) == pytest.approx(t.forward(datos[:5]))


def test_escalares_y_nan():
    t = fit_transformation(MIXTA, "yeo-johnson")
    assert isinstance(t.forward(1.5), float) and isinstance(t.inverse(0.3), float)
    r = t.forward(np.array([1.0, np.nan, -1.0]))
    assert np.isnan(r[1]) and np.isfinite(r[[0, 2]]).all()


# ───────────────────────────────────────── ajuste de Johnson ─────────────────
def test_johnson_elige_la_familia_correcta_y_normaliza():
    tu, tb = fit_transformation(SU, "johnson"), fit_transformation(SB, "johnson")
    assert tu.params["family"] == "SU" and tb.params["family"] == "SB"
    for t, x in ((tu, SU), (tb, SB), (fit_transformation(NEGATIVA, "johnson"), NEGATIVA)):
        assert _p_ad(t.forward(x)) > 0.05  # los datos transformados son compatibles con una normal
        assert t.params["p_value"] == pytest.approx(_p_ad(t.forward(x)))


def test_valores_fuera_del_soporte_de_sb_o_sl_dan_infinito():
    t = Transformation("johnson", {"family": "SB", "a": 0.0, "b": 1.0, "loc": 0.0, "scale": 10.0})
    r = t.forward(np.array([-1.0, 0.0, 5.0, 10.0, 12.0]))
    assert r[0] == r[1] == -np.inf and r[3] == r[4] == np.inf and r[2] == pytest.approx(0.0)
    sl = Transformation("johnson", {"family": "SL", "a": 0.0, "b": 1.0, "loc": 2.0, "scale": 1.0})
    assert sl.forward(1.0) == -np.inf


# ───────────────────────────────────────── capability_analysis(transform=) ───
@pytest.mark.parametrize("metodo, datos, lsl, usl", [
    ("yeo-johnson", NEGATIVA, 15.0, 32.0), ("johnson", NEGATIVA, 15.0, 32.0), ("boxcox", np.abs(MIXTA) + 0.5, 0.1, 9.0)])
def test_capacidad_con_transformacion_equivale_a_transformar_a_mano(metodo, datos, lsl, usl):
    r = pp.capability_analysis(datos, lsl, usl, transform=metodo)
    t = fit_transformation(datos, metodo)
    ref = pp.capability_analysis(t.forward(datos), t.forward(lsl), t.forward(usl))
    for campo in ("n", "mean", "sigma_within", "sigma_overall", "cp", "cpk", "pp", "ppk"):
        assert getattr(r, campo) == pytest.approx(getattr(ref, campo)), campo
    # se informa en unidades originales
    assert (r.lsl, r.usl) == (lsl, usl) and np.array_equal(r.data, datos)
    assert r.ppm_obs[2] == pytest.approx(1e6 * np.mean((datos < lsl) | (datos > usl)))
    assert r.transform["method"] == metodo


def test_con_subgrupos_la_sigma_dentro_se_calcula_en_la_escala_transformada():
    g = np.exp(np.random.default_rng(4).normal(1, 0.4, (30, 4)))
    r = pp.capability_analysis(g, 0.5, 20.0, transform="yeo-johnson")
    t = fit_transformation(g.ravel(), "yeo-johnson")
    ref = pp.capability_analysis(t.forward(g), t.forward(0.5), t.forward(20.0))
    assert r.sigma_within == pytest.approx(ref.sigma_within) and r.within_method == "pooled"


def test_un_limite_fuera_del_soporte_da_indices_infinitos_sin_fallar():
    y = stats.beta.rvs(2, 5, size=200, random_state=1) * 10
    r = pp.capability_analysis(y, -1.0, 12.0, transform="johnson")
    assert r.transform["family"] == "SB" and np.isinf(r.pp) and np.isinf(r.ppk)


def test_con_bootstrap_y_con_transformacion():
    r = pp.capability_analysis(NEGATIVA, 15.0, 32.0, transform="yeo-johnson", ci_method="bootstrap", n_boot=300, seed=1)
    assert r.pp_ci[0] < r.pp < r.pp_ci[1] and r.ci_method == "bootstrap:bca:300"


def test_sin_transform_no_cambia():
    r = pp.capability_analysis(NEGATIVA, 15.0, 32.0)
    assert r.transform is None and "Transformación" not in r.summary()


def test_resumen_y_grafico():
    r = pp.capability_analysis(NEGATIVA, 15.0, 32.0, transform="johnson")
    assert "Transformación Johnson" in r.summary() and "escala transformada" in r.summary()
    assert r.plot() is not None
    with pp.language("en"):
        assert "Johnson" in r.summary() and "transformed scale" in r.summary()


@pytest.mark.parametrize("llamada, texto", [
    (lambda: pp.capability_analysis(NEGATIVA, 15, 32, transform="x"), "transform"),
    (lambda: pp.capability_analysis(MIXTA, -3, 8, transform="boxcox"), "positivos"),
    (lambda: pp.capability_analysis(np.abs(MIXTA) + 1, -3, 8, transform="boxcox"), "lsl"),
    (lambda: pp.capability_analysis(NEGATIVA, 15, 32, transform="yeo-johnson", sigma_within=1.0), "sigma_within"),
    (lambda: pp.capability_analysis(np.full(20, 3.0) + np.arange(20) * 0, 1, 5, transform="yeo-johnson"), "constantes"),
    (lambda: fit_transformation(NEGATIVA[:5], "yeo-johnson"), "al menos 8"),
])
def test_errores(llamada, texto):
    with pytest.raises(ValueError, match=texto):
        llamada()
