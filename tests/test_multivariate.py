"""Cartas multivariadas: T², varianza generalizada y MEWMA.

Las distribuciones de referencia se verifican por simulación Monte Carlo y los
valores por cálculo manual o scipy.
"""
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from scipy.spatial.distance import mahalanobis

import spyc
from spyc.multivariate import ALPHA, _gv_constants, _mewma_arl, _t2_reference

SIGMA = np.array([[1.0, 0.6, 0.3], [0.6, 1.0, 0.2], [0.3, 0.2, 1.0]])


def _batch_t2(x0, xbar, S_inv):
    d = x0 - xbar
    return np.einsum("si,sij,sj->s", d, S_inv, d)


# ------------------------------------------------------------------------------ T²
def test_alpha_es_cola_de_3_sigmas():
    assert ALPHA == pytest.approx(1 - stats.norm.cdf(3), rel=1e-12)


def test_t2_valores_igual_a_mahalanobis_al_cuadrado(rng):
    X = rng.multivariate_normal([1, 2, 3], SIGMA, 40)
    ch = spyc.t2_chart(X)
    S_inv = np.linalg.inv(np.cov(X, rowvar=False))
    esperado = [mahalanobis(x, X.mean(axis=0), S_inv) ** 2 for x in X]
    assert ch["T2"].values == pytest.approx(esperado, rel=1e-9)


def test_t2_subgrupos_igual_a_n_por_mahalanobis(rng):
    G = rng.multivariate_normal([0, 0, 0], SIGMA, 60).reshape(15, 4, 3)
    ch = spyc.t2_chart(G)
    means = G.mean(axis=1)
    S = np.mean([np.cov(g, rowvar=False) for g in G], axis=0)
    esperado = [4 * mahalanobis(m, means.mean(axis=0), np.linalg.inv(S)) ** 2 for m in means]
    assert ch["T2"].values == pytest.approx(esperado, rel=1e-9)
    # misma carta con matriz plana + subgroup_size
    ch2 = spyc.t2_chart(G.reshape(60, 3), subgroup_size=4)
    assert ch2["T2"].values == pytest.approx(ch["T2"].values)


def test_t2_fase1_individuales_distribucion_beta_y_centro(rng):
    m, p, sims = 20, 3, 6000
    X = rng.multivariate_normal(np.zeros(p), SIGMA, (sims, m))
    xbar = X.mean(axis=1)
    Xc = X - xbar[:, None, :]
    S = np.einsum("smi,smj->sij", Xc, Xc) / (m - 1)
    t2 = _batch_t2(X[:, 0, :], xbar, np.linalg.inv(S))
    center, ucl = _t2_reference(p, m, 1, 0.01, "phase1")
    assert np.mean(t2 > ucl) == pytest.approx(0.01, abs=0.004)  # 3 errores estándar
    assert t2.mean() == pytest.approx(center, rel=0.05)


def test_t2_fase2_individuales_distribucion_f(rng):
    m, p, sims = 25, 3, 6000
    H = rng.multivariate_normal(np.zeros(p), SIGMA, (sims, m))
    new = rng.multivariate_normal(np.zeros(p), SIGMA, sims)
    xbar = H.mean(axis=1)
    Hc = H - xbar[:, None, :]
    S = np.einsum("smi,smj->sij", Hc, Hc) / (m - 1)
    t2 = _batch_t2(new, xbar, np.linalg.inv(S))
    center, ucl = _t2_reference(p, m, 1, 0.01, "phase2")
    assert np.mean(t2 > ucl) == pytest.approx(0.01, abs=0.004)
    assert t2.mean() == pytest.approx(center, rel=0.05)


def test_t2_fase1_subgrupos_distribucion(rng):
    m, n, p, sims = 12, 4, 2, 5000
    G = rng.multivariate_normal(np.zeros(p), SIGMA[:p, :p], (sims, m, n))
    means = G.mean(axis=2)
    grand = means.mean(axis=1)
    Sj = G - means[:, :, None, :]
    Sbar = np.einsum("smki,smkj->sij", Sj, Sj) / ((n - 1) * m)
    t2 = n * _batch_t2(means[:, 0, :], grand, np.linalg.inv(Sbar))
    center, ucl = _t2_reference(p, m, n, 0.01, "phase1")
    assert np.mean(t2 > ucl) == pytest.approx(0.01, abs=0.004)
    assert t2.mean() == pytest.approx(center, rel=0.05)


def test_t2_parametros_conocidos_es_chi_cuadrado():
    center, ucl = _t2_reference(3, 50, 1, ALPHA, "known")
    assert center == 3
    assert ucl == pytest.approx(stats.chi2.ppf(1 - ALPHA, 3))


def test_t2_fase2_con_historicos_detecta_y_diagnostica(rng):
    hist = rng.multivariate_normal(np.zeros(3), SIGMA, 200)
    X = rng.multivariate_normal(np.zeros(3), SIGMA, 40)
    X[25:, 2] += 6.0
    ch = spyc.t2_chart(X, mu=hist.mean(axis=0), cov=np.cov(hist, rowvar=False), n_hist=200)
    assert ch.params[0]["fase"] == "II"
    post = [i for i in ch["T2"].flagged if i >= 25]  # puntos con la variable 3 desplazada
    assert len(post) >= 10  # de 15 puntos desplazados
    assert ch.contributions(post[0] + 1).idxmax() == "X3"


def test_contribuciones_exactas_con_covarianza_identidad():
    mu, cov = np.zeros(3), np.eye(3)
    X = np.array([[0.1, 4.0, -0.2], [0.0, 0.1, 0.1], [0.3, -0.1, 0.2]])
    ch = spyc.t2_chart(X, mu=mu, cov=cov)
    c = ch.contributions(1)
    assert c.to_numpy() == pytest.approx(X[0] ** 2)  # con Sigma = I: d_j = x_j²
    assert ch["T2"].values[0] == pytest.approx(np.sum(X[0] ** 2))


def test_contribuciones_usan_nombres_de_columna_y_escala_de_subgrupo(rng):
    df = pd.DataFrame(rng.multivariate_normal([0, 0, 0], SIGMA, 40), columns=["largo", "ancho", "peso"])
    ch = spyc.t2_chart(df, subgroup_size=4)
    assert list(ch.contributions(3).index) == ["largo", "ancho", "peso"]
    with pytest.raises(ValueError):
        ch.contributions(0)
    with pytest.raises(ValueError, match="solo están disponibles"):
        spyc.mewma_chart(df).contributions(1)


def test_t2_errores(rng):
    X = rng.multivariate_normal(np.zeros(3), SIGMA, 30)
    with pytest.raises(ValueError, match="juntos"):
        spyc.t2_chart(X, mu=np.zeros(3))
    with pytest.raises(ValueError, match="al menos 2 variables"):
        spyc.t2_chart(X[:, 0:1])
    with pytest.raises(ValueError, match="singular"):
        spyc.t2_chart(np.column_stack([X[:, 0], X[:, 1], X[:, 0] + X[:, 1]]))
    with pytest.raises(ValueError, match="dividir"):
        spyc.t2_chart(X, subgroup_size=7)
    with pytest.raises(ValueError, match="más de 4"):
        spyc.t2_chart(X[:4, :3])
    with pytest.raises(ValueError):
        spyc.t2_chart(X, n_hist=10)
    bad = X.copy()
    bad[2, 1] = np.nan
    with pytest.raises(ValueError, match="faltantes"):
        spyc.t2_chart(bad)


# ------------------------------------------------------------ varianza generalizada
def test_gv_constantes_exactas_para_una_variable():
    for n in (2, 5, 12):
        b1, b2 = _gv_constants(1, n)
        assert b1 == pytest.approx(1.0)
        assert b2 == pytest.approx(2.0 / (n - 1))  # Var(s²)/σ⁴ = 2/(n-1)


@pytest.mark.parametrize("p,n", [(2, 5), (3, 6)])
def test_gv_constantes_por_monte_carlo(rng, p, n):
    S0 = SIGMA[:p, :p]
    X = rng.multivariate_normal(np.zeros(p), S0, (200000, n))
    Xc = X - X.mean(axis=1, keepdims=True)
    S = np.einsum("smi,smj->sij", Xc, Xc) / (n - 1)
    det = np.linalg.det(S)
    b1, b2 = _gv_constants(p, n)
    d0 = np.linalg.det(S0)
    assert det.mean() == pytest.approx(b1 * d0, rel=0.01)
    assert det.var() == pytest.approx(b2 * d0**2, rel=0.05)


def test_gv_lineas_manuales_y_deteccion(rng):
    G = rng.multivariate_normal(np.zeros(3), SIGMA, 200).reshape(25, 8, 3)
    G[10] *= 3  # una muestra con mucha más dispersión
    ch = spyc.generalized_variance_chart(G)
    dets = np.array([np.linalg.det(np.cov(g, rowvar=False)) for g in G])
    Sbar = np.mean([np.cov(g, rowvar=False) for g in G], axis=0)
    b1, b2 = _gv_constants(3, 8)
    pan = ch["|S|"]
    assert pan.values == pytest.approx(dets)
    assert pan.center[0] == pytest.approx(b1 * np.linalg.det(Sbar))
    assert pan.ucl[0] == pytest.approx(np.linalg.det(Sbar) * (b1 + 3 * np.sqrt(b2)))
    assert pan.lcl[0] >= 0
    assert 10 in pan.flagged
    # con Sigma conocida
    ch2 = spyc.generalized_variance_chart(G, cov=SIGMA)
    assert ch2["|S|"].center[0] == pytest.approx(b1 * np.linalg.det(SIGMA))
    assert 10 in ch2["|S|"].flagged


def test_gv_errores(rng):
    X = rng.multivariate_normal(np.zeros(3), SIGMA, 40)
    with pytest.raises(ValueError, match="requiere subgrupos"):
        spyc.generalized_variance_chart(X)
    with pytest.raises(ValueError, match="mayor que el número de variables"):
        spyc.generalized_variance_chart(X[:36], subgroup_size=3)


# --------------------------------------------------------------------------- MEWMA
def test_mewma_limite_coincide_con_valor_publicado():
    # Prabhu y Runger (1997): p=2, lambda=0.1, ARL0=200 -> H = 8.64
    assert spyc.mewma_limit(2, 0.1, 200) == pytest.approx(8.64, abs=0.02)
    assert _mewma_arl(8.64, 2, 0.1) == pytest.approx(200, rel=0.01)


def test_mewma_cadena_converge_con_mas_celdas():
    a, b = _mewma_arl(8.64, 2, 0.1, cells=150), _mewma_arl(8.64, 2, 0.1, cells=600)
    assert a == pytest.approx(b, rel=0.01)


def test_mewma_arl_por_simulacion(rng):
    p, lam, h, runs = 3, 0.2, spyc.mewma_limit(3, 0.2, 100), 4000
    z = np.zeros((runs, p))
    alive = np.ones(runs, dtype=bool)
    length = np.zeros(runs)
    c = h * lam / (2 - lam)
    for _ in range(3000):
        x = rng.standard_normal((runs, p))
        z = (1 - lam) * z + lam * x
        length[alive] += 1
        alive &= (z**2).sum(axis=1) <= c
        if not alive.any():
            break
    assert length.mean() == pytest.approx(100, rel=0.06)


def test_mewma_valores_manuales(rng):
    X = rng.standard_normal((30, 2))
    lam = 0.1
    ch = spyc.mewma_chart(X, weight=lam, mu=np.zeros(2), cov=np.eye(2), ucl=8.64)
    z, esperado = np.zeros(2), []
    for x in X:
        z = lam * x + (1 - lam) * z
        esperado.append(z @ z / (lam / (2 - lam)))  # covarianza asintótica de Z
    assert ch["MEWMA"].values == pytest.approx(esperado, rel=1e-9)
    assert ch["MEWMA"].ucl[0] == 8.64


def test_mewma_detecta_cambio_pequeno_sostenido(rng):
    X = rng.multivariate_normal([0, 0], np.eye(2), 80)
    X[40:] += 0.8
    mu, cov = np.zeros(2), np.eye(2)
    assert not spyc.mewma_chart(X, mu=mu, cov=cov).in_control


def test_mewma_subgrupos_y_errores(rng):
    X = rng.multivariate_normal([0, 0], np.eye(2), 60)
    ch = spyc.mewma_chart(X, subgroup_size=3)
    assert ch.params[0]["puntos"] == 20 and ch.params[0]["tamaño"] == 3
    with pytest.raises(ValueError):
        spyc.mewma_chart(X, weight=0)
    with pytest.raises(ValueError):
        spyc.mewma_limit(2, 0.1, 1.0)


# ---------------------------------------------------------------------------- gráficos
def test_graficos_de_todas_las_cartas_nuevas(rng):
    X = rng.multivariate_normal(np.zeros(3), SIGMA, 60)
    charts = [
        spyc.t2_chart(X),
        spyc.generalized_variance_chart(X, subgroup_size=4),
        spyc.mewma_chart(X),
        spyc.ma_chart(rng.normal(0, 1, 40), length=3),
        spyc.zmr_chart(rng.normal(0, 1, 18), list("AAAAAABBBBBBAAAAAA")),
        spyc.imr_rs_chart(rng.normal(0, 1, (20, 4))),
        spyc.g_chart(rng.geometric(0.03, 40) - 1),
        spyc.t_chart(rng.exponential(5, 40)),
    ]
    for ch in charts:
        fig = ch.plot()
        assert len(fig.axes) == len(ch.panels)
        assert not ch.to_frame().empty
        assert isinstance(ch.summary(), str)


def test_mewma_chart_extremo_a_extremo_tiene_el_arl_pedido(rng):
    mu, cov = np.zeros(2), np.eye(2)
    largos = []
    for _ in range(400):
        ch = spyc.mewma_chart(rng.standard_normal((2500, 2)), mu=mu, cov=cov, arl=100)
        f = ch["MEWMA"].flagged
        largos.append(f[0] + 1 if f.size else 2500)
    assert np.mean(largos) == pytest.approx(100, rel=0.18)
