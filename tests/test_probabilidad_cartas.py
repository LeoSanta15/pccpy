"""Pruebas de la especificación 011: ``ControlChart.probability()`` en las cartas de control.

Las referencias se escriben aparte con ``scipy.stats`` y fórmulas manuales, no con la salida de pccpy (salvo la consistencia
``1 / probability() == arl_*``, que es entre funciones de pccpy).
"""
import warnings

import numpy as np
import pytest
from scipy import stats

import pccpy

LAM, SIGMA, MU = 0.2, 2.0, 50.0


def _g(seed=1, filas=25, n=5):
    return np.random.default_rng(seed).normal(MU, SIGMA, (filas, n))


def _x(seed=0, n=60):
    return np.random.default_rng(seed).normal(10, 1, n)


def _rango(n):
    return stats.studentized_range(n, np.inf)


def _sin_avisos(f, *a, **k):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return f(*a, **k)


# ---------------------------------------------------------------- RF-01
CASOS_DIST = {
    "imr_I": (lambda: pccpy.imr_chart(_x()), "I", "normal"),
    "imr_MR": (lambda: pccpy.imr_chart(_x()), "MR", "range"),
    "xbar_Xbar": (lambda: pccpy.xbar_r_chart(_g()), "Xbar", "normal"),
    "xbar_R": (lambda: pccpy.xbar_r_chart(_g()), "R", "range"),
    "xbar_s_S": (lambda: pccpy.xbar_s_chart(_g()), "S", "sd"),
    "p": (lambda: pccpy.p_chart(np.full(30, 5), np.full(30, 100)), "P", "binomial"),
    "np": (lambda: pccpy.np_chart(np.full(30, 5), np.full(30, 100)), "NP", "binomial"),
    "c": (lambda: pccpy.c_chart(np.full(30, 5)), "C", "poisson"),
    "u": (lambda: pccpy.u_chart(np.full(30, 5), np.full(30, 10)), "U", "poisson"),
    "ewma": (lambda: pccpy.ewma_chart(_x()), "EWMA", "normal"),
    "g": (lambda: pccpy.g_chart(np.random.default_rng(2).geometric(0.02, 30) - 1), "G", "geometric"),
    "t": (lambda: pccpy.t_chart(np.random.default_rng(3).weibull(1.5, 30) * 10), "T", "weibull"),
}


@pytest.mark.parametrize("caso", sorted(CASOS_DIST))
def test_s011_rf_01_cada_panel_guarda_su_distribucion(caso):
    """S011-RF-01: ``panel.dist`` dice la familia y trae un valor por punto de cada parámetro."""
    fabrica, panel, familia = CASOS_DIST[caso]
    p = _sin_avisos(fabrica)[panel]
    assert p.dist["family"] == familia
    parametros = {k: v for k, v in p.dist.items() if k != "family"}
    assert parametros
    assert all(np.size(v) == len(p.values) for v in parametros.values())


def test_s011_rf_01_las_cartas_no_admitidas_no_tienen_distribucion():
    """S011-RF-01: CUSUM, MA, Zona, Laney y multivariadas dejan ``dist`` en ``None``."""
    d = np.random.default_rng(0)
    cartas = [pccpy.cusum_chart(_x()), pccpy.ma_chart(_x()), pccpy.zone_chart(_x(), mu=10.0, sigma=1.0),
              pccpy.laney_p_chart(d.binomial(100, 0.05, 30), np.full(30, 100)),
              pccpy.t2_chart(d.multivariate_normal([0, 0], np.eye(2), 40))]
    for carta in cartas:
        assert all(p.dist is None for p in carta.panels), carta.kind


# ---------------------------------------------------------------- RF-02
def test_s011_rf_02_xbar_es_normal_con_sigma_sobre_raiz_n():
    """S011-RF-02: ``P(Xbar < a) = Φ((a − m)/(s/√5))`` con tolerancia relativa 1e-12."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    ref = stats.norm(MU, SIGMA / np.sqrt(5))
    assert carta.probability(below=49.0).probability == pytest.approx(ref.cdf(49.0), rel=1e-12)
    assert carta.probability(above=51.5).probability == pytest.approx(ref.sf(51.5), rel=1e-12)
    assert carta.probability(between=(49.5, 50.5)).probability == pytest.approx(ref.cdf(50.5) - ref.cdf(49.5), rel=1e-12)
    fuera = carta.probability(below=48.0, above=52.0)
    assert fuera.event == "outside"
    assert fuera.probability == pytest.approx(ref.cdf(48.0) + ref.sf(52.0), rel=1e-12)


def test_s011_rf_02_i_es_normal_con_la_sigma_dada():
    """S011-RF-02: el panel I usa ``mu`` y ``sigma``."""
    carta = pccpy.imr_chart(_x(), mu=10.0, sigma=1.5)
    assert carta.probability(above=12.0).probability == pytest.approx(stats.norm(10, 1.5).sf(12.0), rel=1e-12)


@pytest.mark.parametrize("span", [2, 3])
def test_s011_rf_02_mr_es_el_rango_de_span_normales(span):
    """S011-RF-02: ``P(MR > b) = studentized_range(span, ∞).sf(b/σ)``."""
    carta = pccpy.imr_chart(_x(), mu=10.0, sigma=1.5, span=span)
    assert carta.probability(panel="MR", above=3.0).probability == pytest.approx(_rango(span).sf(3.0 / 1.5), rel=1e-9)


def test_s011_rf_02_r_es_el_rango_de_n_normales():
    """S011-RF-02: ``P(R > b) = studentized_range(5, ∞).sf(b/s)``."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    assert carta.probability(panel="R", above=6.0).probability == pytest.approx(_rango(5).sf(6.0 / SIGMA), rel=1e-9)
    assert carta.probability(panel="R", between=(2.0, 6.0)).probability == pytest.approx(
        _rango(5).cdf(3.0) - _rango(5).cdf(1.0), rel=1e-9)


def test_s011_rf_02_r_coincide_con_la_simulacion_de_20_semillas():
    """S011-RF-02: el rango de 5 normales simuladas (20 semillas) da la misma probabilidad, dentro del error de Monte Carlo."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    b, total, n_sim = 6.0, 0, 0
    for semilla in range(20):
        z = np.random.default_rng(1000 + semilla).normal(0, SIGMA, (50_000, 5))
        total += int(np.sum(np.ptp(z, axis=1) > b))
        n_sim += 50_000
    p_mc = total / n_sim
    esperado = carta.probability(panel="R", above=b).probability
    assert abs(p_mc - esperado) < 4 * np.sqrt(esperado * (1 - esperado) / n_sim)


def test_s011_rf_02_s_usa_la_ji_cuadrada():
    """S011-RF-02: ``P(S > b) = χ²(n−1).sf((n−1)(b/σ)²)``."""
    carta = pccpy.xbar_s_chart(_g(), mu=MU, sigma=SIGMA)
    b = 3.0
    assert carta.probability(panel="S", above=b).probability == pytest.approx(
        stats.chi2.sf(4 * (b / SIGMA) ** 2, 4), rel=1e-9)


def test_s011_rf_02_ewma_usa_la_sigma_de_su_punto():
    """S011-RF-02: la EWMA es normal con ``σ·√(λ/(2−λ)·(1−(1−λ)^{2t}))`` en el punto ``t``."""
    carta = pccpy.ewma_chart(_x(), weight=LAM, target=10.0, sigma=1.0)
    for t in (1, 10):
        s_t = np.sqrt(LAM / (2 - LAM) * (1 - (1 - LAM) ** (2 * t)))
        assert carta.probability(above=10.3, point=t).probability == pytest.approx(stats.norm(10.0, s_t).sf(10.3), rel=1e-9)


# ---------------------------------------------------------------- RF-03
def test_s011_rf_03_np_es_binomial():
    """S011-RF-03: ``P(NP > UCL) = 1 − binom.cdf(⌊UCL⌋, 100, 0,05)``."""
    d = np.random.default_rng(4).binomial(100, 0.05, 30)
    carta = pccpy.np_chart(d, np.full(30, 100), p=0.05)
    ucl = carta["NP"].ucl[0]
    assert carta.probability(above=ucl).probability == pytest.approx(1 - stats.binom.cdf(np.floor(ucl), 100, 0.05), rel=1e-12)
    assert carta.probability(below=3).probability == pytest.approx(stats.binom.cdf(2, 100, 0.05), rel=1e-12)  # estricto: X < 3


def test_s011_rf_03_c_es_poisson():
    """S011-RF-03: ``P(C < LCL) = poisson.cdf(⌈LCL⌉ − 1, c)`` con una carta cuyo LCI es positivo."""
    d = np.random.default_rng(5).poisson(25, 30)
    carta = pccpy.c_chart(d, c=25.0)
    lcl = carta["C"].lcl[0]
    assert lcl == pytest.approx(10.0)
    assert carta.probability(below=lcl).probability == pytest.approx(stats.poisson.cdf(np.ceil(lcl) - 1, 25.0), rel=1e-12)
    assert carta.probability(above=40.5).probability == pytest.approx(stats.poisson.sf(40, 25.0), rel=1e-12)


def test_s011_rf_03_p_usa_la_proporcion_y_el_n_del_punto():
    """S011-RF-03: en la carta P el valor es una proporción (``Y = conteo/n``); sin redondeo de coma flotante (0,07·100 ≠ 7)."""
    d = np.random.default_rng(6).binomial(100, 0.05, 30)
    carta = pccpy.p_chart(d, np.full(30, 100), p=0.05)
    assert carta.probability(below=0.035).probability == pytest.approx(stats.binom.cdf(3, 100, 0.05), rel=1e-12)
    assert carta.probability(below=0.07).probability == pytest.approx(stats.binom.cdf(6, 100, 0.05), rel=1e-12)
    assert carta.probability(above=0.07).probability == pytest.approx(stats.binom.sf(7, 100, 0.05), rel=1e-12)


def test_s011_rf_03_u_es_poisson_de_c_por_n():
    """S011-RF-03: en la carta U el valor son defectos por unidad: ``Y = conteo/n`` con Poisson(u·n)."""
    d = np.random.default_rng(7).poisson(20, 30)
    carta = pccpy.u_chart(d, np.full(30, 10), u=2.0)
    assert carta.probability(above=3.0).probability == pytest.approx(stats.poisson.sf(30, 20.0), rel=1e-12)
    assert carta.probability(below=1.25).probability == pytest.approx(stats.poisson.cdf(12, 20.0), rel=1e-12)


# ---------------------------------------------------------------- RF-04
def test_s011_rf_04_g_es_geometrica():
    """S011-RF-04: ``P(X > UCL) = geom.sf(⌊UCL⌋ + 1, p)`` y ``P(X < a) = geom.cdf(⌈a⌉, p)``."""
    carta = pccpy.g_chart(np.random.default_rng(2).geometric(0.02, 30) - 1, p=0.02)
    ucl = carta["G"].ucl[0]
    assert carta.probability(above=ucl).probability == pytest.approx(stats.geom.sf(np.floor(ucl) + 1, 0.02), rel=1e-12)
    assert carta.probability(below=10.5).probability == pytest.approx(stats.geom.cdf(11, 0.02), rel=1e-12)
    assert carta.probability(below=0).probability == 0.0 and carta.probability(above=-1).probability == 1.0
    assert carta.probability().probability == pytest.approx(stats.geom.sf(np.floor(ucl) + 1, 0.02), rel=1e-12)


def test_s011_rf_04_g_coincide_con_arl_g():
    """S011-RF-04: ``1 / probability()`` es el ARL en control de ``arl_g``."""
    carta = pccpy.g_chart(np.random.default_rng(2).geometric(0.02, 30) - 1, p=0.02)
    assert 1.0 / carta.probability().probability == pytest.approx(pccpy.arl_g(0.02), rel=1e-9)


def test_s011_rf_04_t_es_weibull():
    """S011-RF-04: ``P(T < a) = weibull_min.cdf(a, forma, escala)``; sin argumentos, ``2·Φ(−3)``."""
    x = np.random.default_rng(3).weibull(1.5, 30) * 10
    carta = pccpy.t_chart(x, shape=1.5, scale=10.0)
    assert carta.probability(below=4.0).probability == pytest.approx(stats.weibull_min.cdf(4.0, 1.5, scale=10.0), rel=1e-12)
    assert carta.probability(above=25.0).probability == pytest.approx(stats.weibull_min.sf(25.0, 1.5, scale=10.0), rel=1e-12)
    assert carta.probability(below=-1.0).probability == 0.0
    assert carta.probability().probability == pytest.approx(2 * stats.norm.sf(3.0), rel=1e-9)
    assert 1.0 / carta.probability().probability == pytest.approx(pccpy.arl_t(shape=1.5), rel=1e-9)


def test_s011_rf_04_t_exponencial_es_weibull_de_forma_1():
    """S011-RF-04: con distribución exponencial la forma es 1."""
    x = np.random.default_rng(3).exponential(10, 30)
    carta = pccpy.t_chart(x, distribution="exponential", scale=10.0)
    assert carta.probability(above=25.0).probability == pytest.approx(np.exp(-2.5), rel=1e-12)


# ---------------------------------------------------------------- RF-05
def test_s011_rf_05_sin_argumentos_i_es_dos_phi_de_menos_3():
    """S011-RF-05: carta I a 3σ: ``2·Φ(−3) = 0,0026998``."""
    carta = pccpy.imr_chart(_x(), mu=10.0, sigma=1.0)
    assert carta.probability().probability == pytest.approx(2 * stats.norm.sf(3.0), rel=1e-12)
    assert carta.probability().event == "outside"


@pytest.mark.parametrize(("carta", "panel", "arl"), [
    (lambda: pccpy.imr_chart(_x(), mu=10.0, sigma=1.0), "I", lambda: pccpy.arl_shewhart(k=3)),
    (lambda: pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA), "Xbar", lambda: pccpy.arl_shewhart(k=3)),
    (lambda: pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA), "R", lambda: pccpy.arl_range(5)),
    (lambda: pccpy.xbar_s_chart(_g(), mu=MU, sigma=SIGMA), "S", lambda: pccpy.arl_sd(5)),
    (lambda: pccpy.np_chart(np.full(30, 5), np.full(30, 100), p=0.05), "NP", lambda: pccpy.arl_binomial(100, 0.05)),
    (lambda: pccpy.c_chart(np.full(30, 9), c=9.0), "C", lambda: pccpy.arl_poisson(9.0)),
])
def test_s011_rf_05_la_inversa_es_el_arl_en_control(carta, panel, arl):
    """S011-RF-05: ``1 / probability()`` coincide con el ARL en control de ``arl_*`` con los mismos límites."""
    p = carta().probability(panel=panel).probability
    assert 1.0 / p == pytest.approx(arl(), rel=1e-6)


# ---------------------------------------------------------------- RF-06
def test_s011_rf_06_p_con_n_variable_pide_point():
    """S011-RF-06: sin ``point=`` y con la distribución cambiando, ``ValueError`` que menciona ``point=``."""
    n = np.array([100, 150, 200] * 10)
    carta = pccpy.p_chart(np.full(30, 5), n, p=0.05)
    with pytest.raises(ValueError, match=r"point="):
        carta.probability(above=0.08)
    r = carta.probability(above=0.08, point=[1, 3])
    esperado = [stats.binom.sf(8, 100, 0.05), stats.binom.sf(16, 200, 0.05)]
    assert np.shape(r.probability) == (2,)
    assert r.probability == pytest.approx(esperado, rel=1e-12)
    assert list(r.point) == [1, 3]
    assert carta.probability(above=0.08, point=2).probability == pytest.approx(stats.binom.sf(12, 150, 0.05), rel=1e-12)


def test_s011_rf_06_con_etapas_el_punto_decide_la_etapa():
    """S011-RF-06: con ``point=`` en la 2.ª etapa se usan su media y su sigma (calculadas aparte de los datos)."""
    x = np.r_[np.random.default_rng(8).normal(10, 1, 30), np.random.default_rng(9).normal(20, 2, 30)]
    carta = pccpy.imr_chart(x, stages=[1] * 30 + [2] * 30)
    x2 = x[30:]
    media, sigma = x2.mean(), np.mean(np.abs(np.diff(x2))) / 1.1283791670955126
    assert carta.probability(above=23.0, point=45).probability == pytest.approx(stats.norm(media, sigma).sf(23.0), rel=1e-9)
    with pytest.raises(ValueError, match=r"point="):
        carta.probability(above=23.0)


def test_s011_rf_06_ewma_pide_point_y_usa_la_sigma_del_primer_punto():
    """S011-RF-06: la σ de la EWMA cambia en los primeros puntos."""
    carta = pccpy.ewma_chart(_x(), weight=LAM, target=10.0, sigma=1.0)
    with pytest.raises(ValueError, match=r"point="):
        carta.probability(above=10.3)
    s1 = np.sqrt(LAM / (2 - LAM) * (1 - (1 - LAM) ** 2))
    assert carta.probability(above=10.3, point=1).probability == pytest.approx(stats.norm(10.0, s1).sf(10.3), rel=1e-9)


def test_s011_rf_06_sin_point_si_la_distribucion_no_cambia():
    """S011-RF-06: con una distribución igual en todos los puntos no hace falta ``point=``."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    assert carta.probability(above=51.0).point is None
    assert carta.probability(above=51.0, point=3).probability == carta.probability(above=51.0).probability


def test_s011_rf_06_point_fuera_de_rango():
    """S011-RF-06: ``point`` fuera de ``1..n`` es un error."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    for malo in (0, 26, -1, [1, 99], 1.5):
        with pytest.raises(ValueError):
            carta.probability(above=51.0, point=malo)


# ---------------------------------------------------------------- RF-07
def test_s011_rf_07_box_cox_en_unidades_originales():
    """S011-RF-07: ``P(I < a) = Φ((T(a) − m)/s)`` con Box-Cox escrito en el test; el valor va en unidades originales."""
    x = np.random.default_rng(10).lognormal(1.0, 0.3, 60)
    carta = pccpy.imr_chart(x, transform="boxcox")
    lam = carta.transformation.params["lambda"]
    m, s = carta.params[0]["mean"], carta.params[0]["sigma"]

    def T(a):
        return np.log(a) if lam == 0 else (a ** lam - 1) / lam

    assert carta.probability(below=2.5).probability == pytest.approx(stats.norm(m, s).cdf(T(2.5)), rel=1e-9)
    assert carta.probability(above=4.0).probability == pytest.approx(stats.norm(m, s).sf(T(4.0)), rel=1e-9)
    assert carta.probability(below=-1.0).probability == 0.0  # fuera del dominio de Box-Cox: sin masa por debajo


def test_s011_rf_07_escala_transformada_y_paneles_de_dispersion():
    """S011-RF-07: con ``scale='transformed'`` los valores ya están transformados; MR siempre en la escala transformada."""
    x = np.random.default_rng(10).lognormal(1.0, 0.3, 60)
    carta = pccpy.imr_chart(x, transform="boxcox", scale="transformed")
    m, s = carta.params[0]["mean"], carta.params[0]["sigma"]
    assert carta.probability(below=m + 0.5).probability == pytest.approx(stats.norm(m, s).cdf(m + 0.5), rel=1e-9)
    original = pccpy.imr_chart(x, transform="boxcox")
    assert original.probability(panel="MR", above=0.8).probability == pytest.approx(_rango(2).sf(0.8 / s), rel=1e-9)
    assert carta.probability(panel="MR", above=0.8).probability == pytest.approx(_rango(2).sf(0.8 / s), rel=1e-9)


# ---------------------------------------------------------------- RF-08
def test_s011_rf_08_devuelve_probability_result_sin_defectos():
    """S011-RF-08: el mismo ``ProbabilityResult``; ``dpmo``, ``dpu`` y ``sigma`` valen ``None``; ``panel`` y ``point`` informan."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    r = carta.probability(below=49.0, panel="Xbar", point=[1, 2])
    assert isinstance(r, pccpy.ProbabilityResult)
    assert r.panel == "Xbar" and list(r.point) == [1, 2]
    assert r.dpmo is None and r.dpu is None and r.sigma is None and r.opportunities == 1
    assert r.ppm == pytest.approx(1e6 * np.asarray(r.probability), rel=1e-12)
    assert carta.probability(below=49.0).panel == "Xbar"  # el primer panel


def test_s011_rf_08_to_frame_con_panel_y_point_solo_en_cartas():
    """S011-RF-08: ``to_frame(stable=True)`` añade ``panel`` y ``point``; el de capacidad no cambia."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    marco = carta.probability(below=[48.0, 49.0], point=[1, 2]).to_frame(stable=True)
    assert {"panel", "point", "probability", "ppm"} <= set(marco.columns) and len(marco) == 2
    cap = pccpy.capability_analysis(np.random.default_rng(7).normal(50, 2, 120), lsl=44, usl=56, subgroup_size=1)
    columnas = list(cap.probability(below=47).to_frame(stable=True).columns)
    assert columnas == ["event", "below", "above", "between_lower", "between_upper", "probability", "ppm", "dpmo", "dpu"]
    assert cap.probability(below=47).panel is None and cap.probability(below=47).point is None


# ---------------------------------------------------------------- RF-09
def test_s011_rf_09_cartas_no_admitidas():
    """S011-RF-09: CUSUM, MA, Zona, Laney y multivariadas lanzan ``ValueError``."""
    d = np.random.default_rng(0)
    cartas = [pccpy.cusum_chart(_x()), pccpy.ma_chart(_x()), pccpy.zone_chart(_x(), mu=10.0, sigma=1.0),
              pccpy.laney_p_chart(d.binomial(100, 0.05, 30), np.full(30, 100)),
              pccpy.t2_chart(d.multivariate_normal([0, 0], np.eye(2), 40))]
    for carta in cartas:
        with pytest.raises(ValueError):
            carta.probability(above=1.0)


def test_s011_rf_09_entradas_invalidas():
    """S011-RF-09: panel inexistente, ``between`` mal formado, NaN, arreglos raros y formas incompatibles."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    casos = [
        {"panel": "Z", "below": 1.0}, {"between": (51.0, 49.0)}, {"between": (1.0,)},
        {"between": (49.0, 51.0), "below": 50.0}, {"below": float("nan")}, {"below": []}, {"below": [[1.0, 2.0]]},
        {"below": [1.0, 2.0], "above": [1.0, 2.0, 3.0]},
    ]
    for kw in casos:
        with pytest.raises(ValueError):
            carta.probability(**kw)


def test_s011_rf_09_extremos():
    """S011-RF-09: ±inf válidos; ``below ≤ 0`` en R, S y MR da 0 y ``above ≤ 0`` da 1."""
    r = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    assert r.probability(below=np.inf).probability == 1.0 and r.probability(above=np.inf).probability == 0.0
    assert r.probability(below=-np.inf).probability == 0.0
    assert r.probability(panel="R", below=0.0).probability == 0.0 and r.probability(panel="R", above=0.0).probability == 1.0
    assert pccpy.xbar_s_chart(_g(), mu=MU, sigma=SIGMA).probability(panel="S", below=0.0).probability == 0.0
    assert pccpy.imr_chart(_x(), mu=10.0, sigma=1.0).probability(panel="MR", below=0.0).probability == 0.0


def test_s011_rf_09_sigma_cero_es_un_escalon():
    """S011-RF-09: con sigma 0 la probabilidad es 0/1 (0,5 en el centro)."""
    carta = _sin_avisos(pccpy.imr_chart, np.full(30, 5.0))
    assert carta.probability(below=4.0).probability == 0.0
    assert carta.probability(below=6.0).probability == 1.0
    assert carta.probability(below=5.0).probability == 0.5


def test_s011_rf_09_arreglos_elemento_a_elemento():
    """S011-RF-09: cada elemento da lo mismo que la llamada con ese número; ``above`` se repite."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    valores = [48.0, 49.0, 50.0]
    r = carta.probability(below=valores)
    for i, v in enumerate(valores):
        assert r.probability[i] == pytest.approx(carta.probability(below=v).probability, rel=1e-12)
    f = carta.probability(below=[48.0, 49.0], above=52.0)
    assert np.shape(f.probability) == (2,)


def test_s011_rf_09_el_error_se_traduce():
    """S011-RF-09: los mensajes van con ``tr()``: el texto en inglés difiere del español."""
    carta = pccpy.xbar_r_chart(_g(), mu=MU, sigma=SIGMA)
    with pccpy.language("es"), pytest.raises(ValueError) as es:
        carta.probability(panel="Z", below=1.0)
    with pccpy.language("en"), pytest.raises(ValueError) as en:
        carta.probability(panel="Z", below=1.0)
    assert str(es.value) != str(en.value)


# ---------------------------------------------------------------- RF-10
def test_s011_rf_10_validacion_documentacion_y_docstring():
    """S011-RF-10: la validación suma ``probabilidad-cartas`` (63 en total) y los docstrings mencionan ``panel`` y ``point``."""
    from pccpy.validation import run_validation

    informe = run_validation()
    assert len(informe.checks) == 63
    ids = {c.id: c.passed for c in informe.checks}
    assert ids.get("probabilidad-cartas") is True
    assert "point" in pccpy.ProbabilityResult.__doc__ and "panel" in pccpy.ProbabilityResult.__doc__
    assert pccpy.ControlChart.probability.__doc__


def test_s011_rf_10_el_ejemplo_de_la_guia_se_ejecuta():
    """S011-RF-10: el ejemplo de ``docs/source/arl.md`` con ``.probability(`` se ejecuta tal como está escrito."""
    import re
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[1] / "docs" / "source" / "arl.md").read_text(encoding="utf-8")
    bloques = [b for b in re.findall(r"```python\n(.*?)```", texto, re.DOTALL) if ".probability(" in b]
    assert bloques
    for b in bloques:
        exec(b, {})  # noqa: S102
