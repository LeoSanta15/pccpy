"""Carta de zona y MCUSUM de Crosier."""
import numpy as np
import pytest
from scipy import stats

import pccpy
from pccpy.charts.advanced import _zone_scores
from pccpy.multivariate import _mcusum_arl

W = (0, 2, 4, 8)


# ------------------------------------------------------------------------ zona: reglas
def _scores(z, reset=False):
    sc, fl = _zone_scores(np.asarray(z, dtype=float), W, reset)
    return sc.tolist(), fl.tolist()


def test_zona_suma_pesos_del_mismo_lado():
    assert _scores([1.5, 1.5, 1.5, 1.5]) == ([2, 4, 6, 8], [3])


def test_zona_cruzar_la_linea_central_reinicia_y_el_punto_que_cruza_inicia_la_suma():
    assert _scores([2.5, 2.5, -0.5]) == ([4, 8, 0], [1])
    assert _scores([2.5, -2.5, -2.5]) == ([4, 4, 8], [2])


def test_zona_punto_sobre_la_linea_central_reinicia():
    assert _scores([2.5, 0.0, 2.5]) == ([4, 0, 4], [])


def test_zona_punto_mas_alla_de_3_sigmas_senala_de_inmediato():
    assert _scores([0.2, -3.4]) == ([0, 8], [1])


def test_zona_fronteras_van_a_la_zona_mas_lejana():
    assert _scores([1.0])[0] == [2]
    assert _scores([2.0])[0] == [4]
    assert _scores([3.0])[0] == [8]
    assert _scores([0.999])[0] == [0]


def test_zona_reinicio_tras_senal():
    z = [1.5] * 8
    assert _scores(z, reset=False) == ([2, 4, 6, 8, 10, 12, 14, 16], [3, 4, 5, 6, 7])
    assert _scores(z, reset=True) == ([2, 4, 6, 8, 2, 4, 6, 8], [3, 7])


def _arl_exacto_zona():
    """ARL en control (datos N(0,1)) por cadena de Markov sobre el puntaje acumulado."""
    pj = np.array([stats.norm.cdf(1) - stats.norm.cdf(-1),
                   2 * (stats.norm.cdf(2) - stats.norm.cdf(1)),
                   2 * (stats.norm.cdf(3) - stats.norm.cdf(2)),
                   2 * stats.norm.sf(3)])
    cs = [0, 2, 4, 6]
    Q = np.zeros((4, 4))
    for a, c in enumerate(cs):
        for j, w in enumerate(W):
            for dest, prob in ((c + w, pj[j] / 2), (w, pj[j] / 2)):  # mismo lado / lado opuesto
                if dest < 8:
                    Q[a, cs.index(dest)] += prob
    start = np.zeros(4)
    for j, w in enumerate(W):  # primer punto: puntaje = su peso
        if w < 8:
            start[cs.index(w)] += pj[j]
    return 1 + start @ np.linalg.solve(np.eye(4) - Q, np.ones(4))


def test_zona_arl_por_simulacion_coincide_con_cadena_exacta(rng):
    exacto = _arl_exacto_zona()
    largos = []
    for _ in range(3000):
        z = rng.standard_normal(1500)
        _, fl = _zone_scores(z, W, False)
        largos.append(fl[0] + 1 if fl.size else 1500)
    assert np.mean(largos) == pytest.approx(exacto, rel=0.08)


def test_zona_carta_extremo_a_extremo_tiene_el_arl_exacto(rng):
    exacto = _arl_exacto_zona()
    largos = []
    for _ in range(400):
        f = pccpy.zone_chart(rng.standard_normal(800), mu=0.0, sigma=1.0)["Zona"].flagged
        largos.append(f[0] + 1 if f.size else 800)
    assert np.mean(largos) == pytest.approx(exacto, rel=0.2)


# ---------------------------------------------------------------------- zona: la carta
def test_zona_individuales_limites_y_puntaje(rng):
    x = rng.normal(10, 2, 50)
    ch = pccpy.zone_chart(x)
    sigma = np.mean(np.abs(np.diff(x))) / 1.1283791671
    pan = ch["Zona"]
    assert pan.center[0] == pytest.approx(x.mean())
    assert pan.ucl[0] == pytest.approx(x.mean() + 3 * sigma)
    assert pan.lcl[0] == pytest.approx(x.mean() - 3 * sigma)
    sc, fl = _zone_scores((x - x.mean()) / sigma, W, False)
    assert ch["Puntaje"].values == pytest.approx(sc)
    assert pan.flagged.tolist() == fl.tolist()
    assert ch["Puntaje"].ucl[0] == 8


def test_zona_puntos_fuera_de_3_sigmas_siempre_senalan(rng):
    x = rng.normal(0, 1, 60)
    x[30] = 12
    ch = pccpy.zone_chart(x, mu=0.0, sigma=1.0)
    assert 30 in ch["Zona"].flagged
    assert "puntaje" in ch.violations()["descripcion"].iloc[0]


def test_zona_subgrupos_usan_sigma_sobre_raiz_n(rng):
    d = rng.normal(50, 1, (25, 4))
    ch = pccpy.zone_chart(d, sigma=1.0, mu=50.0)
    assert ch["Zona"].ucl[0] == pytest.approx(50 + 3 / 2)
    assert ch["Zona"].sigma[0] == pytest.approx(0.5)
    # sigma estimada = Rbar/d2 igual que la Xbar-R
    a = pccpy.zone_chart(d)["Zona"].ucl[0]
    b = pccpy.xbar_r_chart(d)["Xbar"].ucl[0]
    assert a == pytest.approx(b)


def test_zona_etapas_reinician_el_puntaje(rng):
    x = np.r_[np.full(3, 0.6), np.full(3, 0.6)]  # con sigma=0.3 -> 2σ: zona 3 (peso 4)
    ch = pccpy.zone_chart(x, mu=0.0, sigma=0.3, stages=[1, 1, 1, 2, 2, 2])
    assert ch["Puntaje"].values.tolist() == [4, 8, 12, 4, 8, 12]
    ch2 = pccpy.zone_chart(x, mu=0.0, sigma=0.3)
    assert ch2["Puntaje"].values.tolist() == [4, 8, 12, 16, 20, 24]


def test_zona_pesos_personalizados_y_errores(rng):
    x = np.full(4, 1.5)
    ch = pccpy.zone_chart(x, mu=0.0, sigma=1.0, weights=(0, 1, 2, 4))
    assert ch["Puntaje"].values.tolist() == [1, 2, 3, 4]
    assert list(ch["Zona"].flagged) == [3]
    with pytest.raises(ValueError, match="pesos"):
        pccpy.zone_chart(x, weights=(0, 2, 4))
    with pytest.raises(ValueError, match="pesos"):
        pccpy.zone_chart(x, weights=(0, 4, 2, 8))
    with pytest.raises(ValueError):
        pccpy.zone_chart(rng.normal(0, 1, (10, 3)), sigma_method="mr")
    with pytest.raises(ValueError):
        pccpy.zone_chart(rng.normal(0, 1, 10), sigma_method="rbar")


# -------------------------------------------------------------------------- MCUSUM
def test_mcusum_paso_manual_exacto():
    # d = (3, 4), k = 0.5, Sigma = I -> C = 5, S = d (1 - 0.1) = (2.7, 3.6), Y = 4.5
    ch = pccpy.mcusum_chart(np.array([[3.0, 4.0], [0.0, 0.0], [0.1, 0.1]]),
                           mu=np.zeros(2), cov=np.eye(2), h=100)
    y = ch["MCUSUM"].values
    assert y[0] == pytest.approx(4.5)
    # segundo paso: v = (2.7, 3.6); C = 4.5 -> S = v (1 - 0.5/4.5), Y = 4.0
    assert y[1] == pytest.approx(4.0)
    # tercer paso: v = S + (0.1, 0.1)
    v = np.array([2.7, 3.6]) * (1 - 0.5 / 4.5) + 0.1
    assert y[2] == pytest.approx(np.hypot(*v) - 0.5)


def test_mcusum_valores_iguales_a_la_recursion_manual(rng):
    X = rng.multivariate_normal([0, 0, 0], [[1, .5, 0], [.5, 1, 0], [0, 0, 1]], 60)
    S = np.array([[1, .5, 0], [.5, 1, 0], [0, 0, 1]])
    ch = pccpy.mcusum_chart(X, mu=np.zeros(3), cov=S, k=0.7, h=50)
    Si, s, esperado = np.linalg.inv(S), np.zeros(3), []
    for x in X:
        v = s + x
        c = np.sqrt(v @ Si @ v)
        s = v * (1 - 0.7 / c) if c > 0.7 else np.zeros(3)
        esperado.append(np.sqrt(s @ Si @ s))
    assert ch["MCUSUM"].values == pytest.approx(esperado)


def test_mcusum_cadena_converge():
    a, b = _mcusum_arl(5.5, 2, 0.5, cells=150), _mcusum_arl(5.5, 2, 0.5, cells=600)
    assert a == pytest.approx(b, rel=0.01)
    assert 195 < b < 208  # h = 5.5, p = 2, k = 0.5 da un ARL cercano a 200


@pytest.mark.parametrize("p", [1, 2, 4])
def test_mcusum_arl_por_simulacion_vectorial(rng, p):
    k = 0.5
    h = pccpy.mcusum_limit(p, k, 100)
    runs = 4000
    s = np.zeros((runs, p))
    alive = np.ones(runs, dtype=bool)
    length = np.zeros(runs)
    for _ in range(2500):
        v = s + rng.standard_normal((runs, p))  # simulación vectorial: sin usar la reducción radial
        c = np.linalg.norm(v, axis=1)
        s = np.where((c > k)[:, None], v * (1 - k / np.maximum(c, 1e-12))[:, None], 0.0)
        length[alive] += 1
        alive &= np.linalg.norm(s, axis=1) <= h
        if not alive.any():
            break
    assert length.mean() == pytest.approx(100, rel=0.07)


def test_mcusum_detecta_desplazamiento_pequeno_y_sostenido(rng):
    X = rng.multivariate_normal([0, 0], np.eye(2), 80)
    X[40:] += 0.8
    ch = pccpy.mcusum_chart(X, mu=np.zeros(2), cov=np.eye(2))
    assert (ch["MCUSUM"].flagged >= 40).any()  # señala tras el cambio


def test_mcusum_subgrupos_errores_y_limite_monotono(rng):
    X = rng.multivariate_normal([0, 0], np.eye(2), 60)
    ch = pccpy.mcusum_chart(X, subgroup_size=3)
    assert ch.params[0]["puntos"] == 20 and ch.params[0]["tamaño"] == 3
    with pytest.raises(ValueError):
        pccpy.mcusum_chart(X, k=-1)
    with pytest.raises(ValueError):
        pccpy.mcusum_chart(X, h=0)
    with pytest.raises(ValueError, match="juntos"):
        pccpy.mcusum_chart(X, mu=np.zeros(2))
    with pytest.raises(ValueError):
        pccpy.mcusum_limit(2, 0.5, 1.0)
    assert pccpy.mcusum_limit(2, 0.5, 100) < pccpy.mcusum_limit(2, 0.5, 200) < pccpy.mcusum_limit(2, 0.5, 500)


def test_graficos_zona_y_mcusum(rng):
    ch1 = pccpy.zone_chart(rng.normal(0, 1, 40))
    ch2 = pccpy.mcusum_chart(rng.multivariate_normal([0, 0], np.eye(2), 40))
    for ch in (ch1, ch2):
        fig = ch.plot()
        assert len(fig.axes) == len(ch.panels)
        assert not ch.to_frame().empty
    assert len(ch1.plot(zones=True).axes) == 2
