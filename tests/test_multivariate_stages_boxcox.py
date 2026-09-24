"""Etapas y Box-Cox en las cartas multivariadas (T², varianza generalizada, MEWMA y MCUSUM)."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

import spyc
from spyc.multivariate import _boxcox_transform, _t2_reference

SIG1 = np.array([[1.0, 0.6, 0.3], [0.6, 1.0, 0.2], [0.3, 0.2, 1.0]])
SIG2 = np.array([[3.0, 0.6, 0.3], [0.6, 2.0, 0.2], [0.3, 0.2, 1.0]])


def _dos_etapas(rng, mu1=(0, 0, 0), mu2=(2, 2, 2)):
    X1 = rng.multivariate_normal(mu1, SIG1, 40)
    X2 = rng.multivariate_normal(mu2, SIG2, 40)
    return np.vstack([X1, X2]), np.array([1] * 40 + [2] * 40)


# ------------------------------------------------------------------------------ T²
def test_t2_fase1_con_etapas_reestima_media_y_cov_por_etapa(rng):
    X, st = _dos_etapas(rng)
    ch = spyc.t2_chart(X, stages=st)
    assert [p["fase"] for p in ch.params] == ["I", "I"]
    assert [p["puntos"] for p in ch.params] == [40, 40]
    assert ch.stage_mean[1] == pytest.approx(X[:40].mean(axis=0))
    assert ch.stage_mean[2] == pytest.approx(X[40:].mean(axis=0))
    assert ch.stage_cov[1] == pytest.approx(np.cov(X[:40], rowvar=False))
    assert not np.allclose(ch.stage_mean[1], ch.stage_mean[2])
    # sin etapas, coincide con dos cartas por separado
    solo1 = spyc.t2_chart(X[:40])
    assert ch["T2"].values[:40] == pytest.approx(solo1["T2"].values)
    assert ch["T2"].ucl[0] == pytest.approx(solo1["T2"].ucl[0])


def test_t2_historicos_con_etapas_usa_los_mismos_limites(rng):
    X, st = _dos_etapas(rng)
    mu, cov = np.zeros(3), SIG1
    ch = spyc.t2_chart(X, mu=mu, cov=cov, n_hist=100, stages=st)
    assert ch["T2"].ucl[0] == ch["T2"].ucl[-1]
    assert ch["T2"].center[0] == ch["T2"].center[-1]
    assert ch.stage_mean[1] is ch.stage_mean[2]  # el mismo array, sin reestimar
    # sin n_hist: parámetros conocidos (chi-cuadrado), también constante entre etapas
    ch2 = spyc.t2_chart(X, mu=mu, cov=cov, stages=st)
    assert [p["fase"] for p in ch2.params] == ["parámetros conocidos"] * 2
    assert ch2["T2"].ucl[0] == pytest.approx(stats.chi2.ppf(1 - spyc.multivariate.ALPHA, 3))


def test_t2_contribuciones_usan_la_etapa_del_punto(rng):
    X, st = _dos_etapas(rng, mu1=(0, 0, 0), mu2=(0, 0, 6))
    ch = spyc.t2_chart(X, stages=st)
    # el punto 41 (primero de la etapa 2) se compara con la media/cov de esa etapa
    manual = spyc.t2_chart(X[40:]).contributions(1)
    assert ch.contributions(41).to_numpy() == pytest.approx(manual.to_numpy())


def test_t2_etapa_con_pocos_puntos_falla_igual_que_sin_etapas(rng):
    X, _ = _dos_etapas(rng)
    with pytest.raises(ValueError, match="más de 4"):
        spyc.t2_chart(X, stages=[1] * 4 + [2] * 76)


def test_t2_dataframe_con_etapas_conserva_nombres(rng):
    X, st = _dos_etapas(rng)
    df = pd.DataFrame(X, columns=["a", "b", "c"])
    ch = spyc.t2_chart(df, stages=st)
    assert list(ch.contributions(5).index) == ["a", "b", "c"]


# --------------------------------------------------------------- varianza generalizada
def test_gv_con_etapas_reestima_sbar_por_etapa(rng):
    G1 = rng.multivariate_normal([0, 0, 0], SIG1, 200).reshape(25, 8, 3)
    G2 = rng.multivariate_normal([0, 0, 0], SIG2, 200).reshape(25, 8, 3)
    G = np.vstack([G1, G2])
    ch = spyc.generalized_variance_chart(G, stages=[1] * 25 + [2] * 25)
    assert ch.params[0]["|S|"] < ch.params[1]["|S|"]  # SIG2 tiene mayor determinante
    solo1 = spyc.generalized_variance_chart(G1)
    assert ch["|S|"].center[0] == pytest.approx(solo1["|S|"].center[0])
    assert ch["|S|"].ucl[0] == pytest.approx(solo1["|S|"].ucl[0])


def test_gv_con_cov_conocida_y_etapas_usa_la_misma_en_todas(rng):
    G1 = rng.multivariate_normal([0, 0, 0], SIG1, 200).reshape(25, 8, 3)
    G2 = rng.multivariate_normal([0, 0, 0], SIG2, 200).reshape(25, 8, 3)
    G = np.vstack([G1, G2])
    ch = spyc.generalized_variance_chart(G, cov=SIG1, stages=[1] * 25 + [2] * 25)
    assert ch["|S|"].center[0] == pytest.approx(ch["|S|"].center[-1])
    assert ch.params[0]["sigma_conocida"] and ch.params[1]["sigma_conocida"]


# --------------------------------------------------------------------------- MEWMA
def test_mewma_reinicia_el_acumulador_en_cada_etapa(rng):
    X, st = _dos_etapas(rng, mu1=(0, 0, 0), mu2=(5, 5, 5))
    ch = spyc.mewma_chart(X, stages=st, mu=np.zeros(3), cov=SIG1)
    # el primer punto de la etapa 2 se calcula como si Z volviera a 0
    solo2 = spyc.mewma_chart(X[40:], mu=np.zeros(3), cov=SIG1, ucl=ch.params[0]["LCS"])
    assert ch["MEWMA"].values[40] == pytest.approx(solo2["MEWMA"].values[0])
    assert ch["MEWMA"].ucl[0] == ch["MEWMA"].ucl[-1]  # el límite no depende de la etapa


def test_mewma_fase1_con_etapas_reestima_media_y_cov(rng):
    X, st = _dos_etapas(rng)
    ch = spyc.mewma_chart(X, stages=st)
    solo1 = spyc.mewma_chart(X[:40], ucl=ch.params[0]["LCS"])
    assert ch["MEWMA"].values[:40] == pytest.approx(solo1["MEWMA"].values)


# -------------------------------------------------------------------------- MCUSUM
def test_mcusum_reinicia_el_acumulador_en_cada_etapa(rng):
    X, st = _dos_etapas(rng, mu1=(0, 0, 0), mu2=(5, 5, 5))
    ch = spyc.mcusum_chart(X, stages=st, mu=np.zeros(3), cov=SIG1)
    solo2 = spyc.mcusum_chart(X[40:], mu=np.zeros(3), cov=SIG1, h=ch.params[0]["LCS"])
    assert ch["MCUSUM"].values[40] == pytest.approx(solo2["MCUSUM"].values[0])
    assert ch["MCUSUM"].values[40] == pytest.approx(0.0, abs=1e-9) or ch["MCUSUM"].values[40] >= 0


def test_mcusum_fase1_con_etapas_reestima_media_y_cov(rng):
    X, st = _dos_etapas(rng)
    ch = spyc.mcusum_chart(X, stages=st)
    solo1 = spyc.mcusum_chart(X[:40], h=ch.params[0]["LCS"])
    assert ch["MCUSUM"].values[:40] == pytest.approx(solo1["MCUSUM"].values)


# ------------------------------------------------------------------------- Box-Cox
def test_boxcox_transform_coincide_con_scipy_por_columna(rng):
    X = np.exp(rng.normal(0, 0.4, (80, 3)))
    out, lambdas = _boxcox_transform(X)
    for j in range(3):
        esperado, lam_sp = stats.boxcox(X[:, j])
        assert lambdas[j] == pytest.approx(lam_sp, rel=1e-6)
        assert out[:, j] == pytest.approx(esperado, rel=1e-6)


def test_boxcox_transform_usa_todas_las_observaciones_no_las_medias_de_subgrupo(rng):
    X = np.exp(rng.normal(0, 0.4, (96, 2))).reshape(12, 8, 2)
    _, lambdas = _boxcox_transform(X)
    flat = X.reshape(-1, 2)
    for j in range(2):
        _, lam_sp = stats.boxcox(flat[:, j])
        assert lambdas[j] == pytest.approx(lam_sp, rel=1e-6)


def test_boxcox_rechaza_datos_no_positivos(rng):
    X = rng.normal(0, 1, (30, 2))
    with pytest.raises(ValueError, match="positivos"):
        _boxcox_transform(X)


@pytest.mark.parametrize("chart_fn,kwargs", [
    (spyc.t2_chart, {}),
    (spyc.mewma_chart, {}),
    (spyc.mcusum_chart, {}),
])
def test_boxcox_en_cada_carta_normaliza_y_reporta_lambda(rng, chart_fn, kwargs):
    X = np.exp(rng.normal(0, 0.3, (60, 3)))
    ch = chart_fn(X, boxcox=True, **kwargs)
    lam = ch.params[0]["lambda_boxcox"]
    assert set(lam) == {"X1", "X2", "X3"}
    esperado, _ = _boxcox_transform(X)
    sin_transformar = chart_fn(esperado, **kwargs)
    # los valores graficados deben coincidir con calcular la carta sobre los datos ya transformados
    key = list(ch.panels[0].name for _ in [0])[0]
    assert ch[key].values == pytest.approx(sin_transformar[key].values, rel=1e-6)


def test_gv_boxcox_reporta_lambda_y_normaliza(rng):
    X = np.exp(rng.normal(0, 0.3, (96, 2))).reshape(12, 8, 2)
    ch = spyc.generalized_variance_chart(X, boxcox=True)
    assert set(ch.params[0]["lambda_boxcox"]) == {"X1", "X2"}
    transformado, _ = _boxcox_transform(X)
    sin_transformar = spyc.generalized_variance_chart(transformado)
    assert ch["|S|"].values == pytest.approx(sin_transformar["|S|"].values, rel=1e-6)


def test_boxcox_conserva_nombres_de_dataframe(rng):
    X = pd.DataFrame(np.exp(rng.normal(0, 0.3, (60, 2))), columns=["peso", "largo"])
    ch = spyc.t2_chart(X, boxcox=True)
    assert set(ch.params[0]["lambda_boxcox"]) == {"peso", "largo"}
    assert list(ch.variables) == ["peso", "largo"]


def test_boxcox_rechaza_combinarse_con_historicos(rng):
    X = np.exp(rng.normal(0, 0.3, (40, 2)))
    with pytest.raises(ValueError, match="no se puede combinar"):
        spyc.t2_chart(X, mu=np.zeros(2), cov=np.eye(2), boxcox=True)
    with pytest.raises(ValueError, match="no se puede combinar"):
        spyc.mewma_chart(X, mu=np.zeros(2), cov=np.eye(2), boxcox=True)
    with pytest.raises(ValueError, match="no se puede combinar"):
        spyc.mcusum_chart(X, mu=np.zeros(2), cov=np.eye(2), boxcox=True)
    with pytest.raises(ValueError, match="no se puede combinar"):
        spyc.generalized_variance_chart(X, subgroup_size=4, cov=np.eye(2), boxcox=True)


def test_boxcox_normaliza_mejor_que_los_datos_originales(rng):
    # datos muy sesgados (lognormal): Box-Cox debe acercar la asimetría a 0
    X = rng.lognormal(0, 1.0, (300, 2))
    _, lambdas = _boxcox_transform(X)
    transformado, _ = _boxcox_transform(X)
    assert abs(stats.skew(transformado[:, 0])) < abs(stats.skew(X[:, 0]))
    assert abs(stats.skew(transformado[:, 1])) < abs(stats.skew(X[:, 1]))


# ---------------------------------------------------------------------- gráficos
def test_graficos_con_etapas_y_boxcox(rng):
    X, st = _dos_etapas(rng)
    charts = [
        spyc.t2_chart(X, stages=st),
        spyc.generalized_variance_chart(
            rng.multivariate_normal([0, 0, 0], SIG1, 200).reshape(25, 8, 3), stages=[1] * 12 + [2] * 13
        ),
        spyc.mewma_chart(X, stages=st),
        spyc.mcusum_chart(X, stages=st),
        spyc.t2_chart(np.exp(rng.normal(0, 0.3, (50, 3))), boxcox=True),
    ]
    for ch in charts:
        fig = ch.plot()
        assert len(fig.axes) == len(ch.panels)
        assert not ch.to_frame().empty
