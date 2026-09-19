"""Cartas avanzadas univariadas: MA, Z-MR, I-MR-R/S, G y T.

Las referencias son cálculos manuales, scipy o propiedades estadísticas conocidas.
"""
import numpy as np
import pytest
from scipy import stats

import spyc
from spyc.charts.advanced import _geom_quantile, _weibull_mle


# ------------------------------------------------------------------------------ MA
def test_ma_valores_y_limites_manuales(rng):
    x = rng.normal(10, 2, 30)
    ch = spyc.ma_chart(x, length=4)
    pan = ch["MA"]
    sigma = np.mean(np.abs(np.diff(x))) / 1.1283791671  # rango móvil / d2 exacto
    mu = x.mean()
    for i in range(30):
        w = min(i + 1, 4)
        assert pan.values[i] == pytest.approx(x[max(0, i - 3) : i + 1].mean())
        assert pan.ucl[i] == pytest.approx(mu + 3 * sigma / np.sqrt(w), rel=1e-9)
        assert pan.lcl[i] == pytest.approx(mu - 3 * sigma / np.sqrt(w), rel=1e-9)
    # los límites de los primeros length-1 puntos son distintos; luego constantes
    assert pan.ucl[0] > pan.ucl[1] > pan.ucl[2] > pan.ucl[3]
    assert np.ptp(pan.ucl[3:]) == pytest.approx(0)


def test_ma_con_subgrupos_usa_sigma_sobre_raiz_n(rng):
    d = rng.normal(50, 1, (20, 5))
    ch = spyc.ma_chart(d, length=3, sigma=1.0, mu=50.0)
    assert ch["MA"].ucl[-1] == pytest.approx(50 + 3 * (1 / np.sqrt(5)) / np.sqrt(3))


def test_ma_detecta_desplazamiento_y_valida_length(rng):
    x = np.concatenate([rng.normal(0, 1, 30), rng.normal(2, 1, 20)])
    assert not spyc.ma_chart(x, length=5, mu=0, sigma=1).in_control
    with pytest.raises(ValueError):
        spyc.ma_chart(x, length=1)


# ---------------------------------------------------------------------------- Z-MR
def _datos_zmr(rng):
    parts = np.array(list("AAAAAABBBBBBAAAAAA"))
    x = np.where(parts == "A", rng.normal(50, 1, parts.size), rng.normal(80, 2, parts.size))
    return x, parts


def test_zmr_constantes_documentadas_por_minitab(rng):
    x, parts = _datos_zmr(rng)
    ch = spyc.zmr_chart(x, parts)
    z, mr = ch["Z"], ch["MR"]
    assert (z.center[0], z.ucl[0], z.lcl[0]) == (0.0, 3.0, -3.0)
    assert mr.center[0] == pytest.approx(1.128, abs=5e-4)
    assert mr.ucl[0] == pytest.approx(3.686, abs=5e-4)
    assert mr.lcl[0] == 0.0


def test_zmr_constant_calculo_manual(rng):
    x, parts = _datos_zmr(rng)
    ch = spyc.zmr_chart(x, parts)
    runs = [x[0:6], x[6:12], x[12:18]]
    mrs = np.concatenate([np.abs(np.diff(r)) for r in runs])
    sigma = mrs.mean() / 1.128379167
    mean = {"A": np.r_[x[0:6], x[12:18]].mean(), "B": x[6:12].mean()}
    esperado = np.array([(v - mean[p]) / sigma for v, p in zip(x, parts)])
    assert ch["Z"].values == pytest.approx(esperado, rel=1e-6)
    # el MR se calcula sobre los z de toda la serie
    assert ch["MR"].values[1:] == pytest.approx(np.abs(np.diff(esperado)), rel=1e-6)


def test_zmr_by_part_y_by_run(rng):
    x, parts = _datos_zmr(rng)
    ch = spyc.zmr_chart(x, parts, sigma_method="by_part")
    mrs_a = np.concatenate([np.abs(np.diff(x[0:6])), np.abs(np.diff(x[12:18]))])
    mrs_b = np.abs(np.diff(x[6:12]))
    sa, sb = mrs_a.mean() / 1.128379167, mrs_b.mean() / 1.128379167
    assert ch["Z"].values[0] == pytest.approx((x[0] - np.r_[x[0:6], x[12:18]].mean()) / sa)
    assert ch["Z"].values[6] == pytest.approx((x[6] - x[6:12].mean()) / sb)
    ch2 = spyc.zmr_chart(x, parts, sigma_method="by_run")
    assert ch2["Z"].values[12] == pytest.approx(
        (x[12] - np.r_[x[0:6], x[12:18]].mean()) / (np.abs(np.diff(x[12:18])).mean() / 1.128379167)
    )


def test_zmr_relative_usa_logaritmo(rng):
    x = np.exp(rng.normal(3, 0.1, 18))
    parts = np.array(list("AAAAAABBBBBBAAAAAA"))
    ch = spyc.zmr_chart(x, parts, sigma_method="relative")
    y = np.log(x)
    ya = np.r_[y[0:6], y[12:18]]
    mrs = np.concatenate([np.abs(np.diff(y[a:b])) for a, b in ((0, 6), (6, 12), (12, 18))])
    assert ch["Z"].values[0] == pytest.approx((y[0] - ya.mean()) / (mrs.mean() / 1.128379167))
    with pytest.raises(ValueError):
        spyc.zmr_chart(-x, parts, sigma_method="relative")


def test_zmr_valores_historicos_y_errores(rng):
    x, parts = _datos_zmr(rng)
    ch = spyc.zmr_chart(x, parts, mu={"A": 50.0, "B": 80.0}, sigma=1.5)
    assert ch["Z"].values[0] == pytest.approx((x[0] - 50) / 1.5)
    assert ch["Z"].values[6] == pytest.approx((x[6] - 80) / 1.5)
    with pytest.raises(ValueError, match="Falta la media"):
        spyc.zmr_chart(x, parts, mu={"A": 50.0})
    with pytest.raises(ValueError, match="una etiqueta por observación"):
        spyc.zmr_chart(x, parts[:-1])
    with pytest.raises(ValueError):
        spyc.zmr_chart([1.0, 2, 3, 4], list("ABAB"), sigma_method="by_run")  # corridas de 1 dato


def test_zmr_detecta_valor_extremo(rng):
    x, parts = _datos_zmr(rng)
    x[3] += 25
    assert not spyc.zmr_chart(x, parts, mu={"A": 50.0, "B": 80.0}, sigma=1.5).in_control


# ---------------------------------------------------------------------- I-MR-R/S
def test_imr_rs_limites_manuales(rng):
    d = rng.normal(20, 1, (25, 5)) + rng.normal(0, 1.5, (25, 1))
    ch = spyc.imr_rs_chart(d)
    means = d.mean(axis=1)
    sigma_x = np.mean(np.abs(np.diff(means))) / 1.128379167
    assert ch["I"].center[0] == pytest.approx(means.mean())
    assert ch["I"].ucl[0] == pytest.approx(means.mean() + 3 * sigma_x)
    assert ch["MR"].center[0] == pytest.approx(1.128379167 * sigma_x)
    # el panel R coincide con el de una Xbar-R
    assert ch["R"].ucl == pytest.approx(spyc.xbar_r_chart(d)["R"].ucl)
    assert ch["R"].center == pytest.approx(spyc.xbar_r_chart(d)["R"].center)


def test_imr_rs_variacion_entre_no_da_falsas_alarmas(rng):
    d = rng.normal(0, 1, (60, 4)) + rng.normal(0, 4, (60, 1))  # entre >> dentro
    assert spyc.xbar_r_chart(d, tests=(1,)).violations().shape[0] > 5  # Xbar-R alarma
    assert spyc.imr_rs_chart(d)["I"].flagged.size <= 2


def test_imr_rs_recupera_sigmas_entre_y_dentro(rng):
    d = rng.normal(0, 1.0, (4000, 5)) + rng.normal(0, 2.0, (4000, 1))
    prm = spyc.imr_rs_chart(d).params[0]
    assert prm["sigma_dentro"] == pytest.approx(1.0, rel=0.03)
    assert prm["sigma_entre"] == pytest.approx(2.0, rel=0.05)
    assert prm["sigma_entre_dentro"] == pytest.approx(np.hypot(1.0, 2.0), rel=0.04)
    assert prm["sigma_entre_dentro"] == pytest.approx(
        np.hypot(prm["sigma_entre"], prm["sigma_dentro"])
    )


def test_imr_rs_sigma_entre_es_cero_si_las_medias_son_iguales(rng):
    base = rng.normal(0, 1, 5)
    d = np.array([rng.permutation(base) for _ in range(12)])  # misma media en todos
    prm = spyc.imr_rs_chart(d).params[0]
    assert prm["sigma_dentro"] > 0
    assert prm["sigma_entre"] == 0.0
    assert prm["sigma_entre_dentro"] == pytest.approx(prm["sigma_dentro"])


def test_imr_rs_variante_s_y_moda(rng):
    d = rng.normal(10, 1, (20, 6))
    ch = spyc.imr_rs_chart(d, within="s", sigma_method="pooled")
    assert ch.kind == "I-MR-S"
    assert ch["S"].ucl == pytest.approx(spyc.xbar_s_chart(d, sigma_method="pooled")["S"].ucl)
    # subgrupos de tamaños todos distintos: no hay moda > 1/2 -> entre/dentro = NaN
    v = rng.normal(10, 1, 3 + 4 + 5 + 6)
    ids = np.repeat([1, 2, 3, 4], [3, 4, 5, 6])
    prm = spyc.imr_rs_chart(v, subgroup=ids).params[0]
    assert np.isnan(prm["sigma_entre"]) and np.isnan(prm["sigma_entre_dentro"])


def test_imr_rs_historicos_y_errores(rng):
    d = rng.normal(10, 1, (20, 5))
    ch = spyc.imr_rs_chart(d, mu=10.0, sigma_within=1.0, sigma_between=2.0)
    assert ch["I"].ucl[0] == pytest.approx(10 + 3 * np.sqrt(4 + 1 / 5))
    with pytest.raises(ValueError):
        spyc.imr_rs_chart(d, within="x")
    with pytest.raises(ValueError):
        spyc.imr_rs_chart(d, within="r", sigma_method="sbar")


# ------------------------------------------------------------------------------ G
def test_g_interpolacion_entre_cuantiles_vecinos():
    p = 0.01
    for q in (0.5, 0.99865):
        kb = int(stats.geom.ppf(q, p))  # menor k con cdf >= q (scipy)
        pa, pb = stats.geom.cdf(kb - 1, p), stats.geom.cdf(kb, p)
        esperado = (kb - 1) + (q - pa) / (pb - pa)
        assert _geom_quantile(p, q) == pytest.approx(esperado, rel=1e-9)
        assert kb - 1 < _geom_quantile(p, q) <= kb


def test_g_lineas_y_prueba_1(rng):
    x = rng.geometric(0.02, 60) - 1
    x[30] = 900
    ch = spyc.g_chart(x)
    prm = ch.params[0]
    assert prm["p"] == pytest.approx(1 / (1 + x.mean()))
    pan = ch["G"]
    assert pan.lcl[0] == 0
    assert pan.center[0] == pytest.approx(_geom_quantile(prm["p"], 0.5) - 1)
    assert pan.ucl[0] == pytest.approx(_geom_quantile(prm["p"], stats.norm.cdf(3)) - 1)
    assert 30 in pan.violations[1]
    assert set(pan.violations[1]) == set(np.flatnonzero(x > pan.ucl[0]))
    assert "geométrica" in ch.violations()["descripcion"].iloc[0]


def test_g_tasa_de_falsa_alarma_cercana_a_0_00135(rng):
    p = 0.005
    x = rng.geometric(p, 400000) - 1
    ch = spyc.g_chart(x, p=p)
    frac = np.mean(x > ch["G"].ucl[0])
    assert 0.0004 < frac < 0.003


def test_g_pruebas_2_a_4_y_errores(rng):
    x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10.0] * 3)
    ch = spyc.g_chart(x, tests=(1, 3))
    assert 3 in ch["G"].violations  # racha ascendente
    with pytest.raises(ValueError):
        spyc.g_chart([1, -2, 3])
    with pytest.raises(ValueError, match="Todos los conteos son 0"):
        spyc.g_chart([0, 0, 0])
    with pytest.raises(ValueError):
        spyc.g_chart([1, 2, 3], p=1.5)


# ------------------------------------------------------------------------------ T
def test_t_mle_weibull_coincide_con_scipy_y_ecuacion_de_score(rng):
    x = stats.weibull_min.rvs(1.7, scale=40, size=200, random_state=rng.integers(1e9))
    c, sc = _weibull_mle(x)
    c_sp, _, sc_sp = stats.weibull_min.fit(x, floc=0)
    # scipy usa un optimizador numérico menos preciso; la prueba rigurosa es la ecuación de score
    assert c == pytest.approx(c_sp, rel=1e-2)
    assert sc == pytest.approx(sc_sp, rel=1e-2)
    score = np.sum(x**c * np.log(x)) / np.sum(x**c) - 1 / c - np.mean(np.log(x))
    assert abs(score) < 1e-8
    assert sc == pytest.approx(np.mean(x**c) ** (1 / c))


def test_t_limites_son_percentiles_weibull(rng):
    x = stats.weibull_min.rvs(1.5, scale=30, size=80, random_state=rng.integers(1e9))
    ch = spyc.t_chart(x)
    c, sc = ch.params[0]["forma"], ch.params[0]["escala"]
    d = stats.weibull_min(c, scale=sc)
    pan = ch["T"]
    assert pan.center[0] == pytest.approx(d.ppf(0.5))
    assert pan.lcl[0] == pytest.approx(d.ppf(stats.norm.cdf(-3)))
    assert pan.ucl[0] == pytest.approx(d.ppf(stats.norm.cdf(3)))


def test_t_exponencial_historicos_y_errores(rng):
    x = rng.exponential(10, 50)
    ch = spyc.t_chart(x, distribution="exponential")
    assert ch.params[0]["escala"] == pytest.approx(x.mean())
    assert ch["T"].center[0] == pytest.approx(x.mean() * np.log(2))
    ch2 = spyc.t_chart(x, shape=2.0, scale=15.0)
    assert ch2["T"].center[0] == pytest.approx(15 * np.log(2) ** 0.5)
    with pytest.raises(ValueError, match="positivas"):
        spyc.t_chart([1.0, 0.0, 2.0])
    with pytest.raises(ValueError):
        spyc.t_chart(x, shape=2.0)
    with pytest.raises(ValueError):
        spyc.t_chart(x, distribution="normal")


def test_t_detecta_duracion_extrema(rng):
    x = rng.exponential(10, 60)
    x[20] = 400
    assert 20 in spyc.t_chart(x)["T"].violations[1]


def test_etapas_en_cartas_de_eventos_raros(rng):
    x = np.concatenate([rng.geometric(0.05, 30), rng.geometric(0.005, 30)]) - 1
    ch = spyc.g_chart(x, stages=[1] * 30 + [2] * 30)
    assert len(ch.params) == 2
    assert ch["G"].ucl[0] < ch["G"].ucl[-1]


# ----------------------------------------------------------- corrección en EWMA
def test_ewma_descripcion_refleja_k(rng):
    x = np.concatenate([rng.normal(0, 1, 20), rng.normal(4, 1, 10)])
    ch = spyc.ewma_chart(x, k=2.5, target=0.0, sigma=1.0)
    assert not ch.in_control
    assert "2.5" in ch.violations()["descripcion"].iloc[0]
