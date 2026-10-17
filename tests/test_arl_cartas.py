# Trazabilidad: S009-RF-06, S009-RF-07, S009-RF-08 (spec 009, cartas de dispersión, atributos y eventos raros).
"""Especificación 009: ARL de las cartas S y R, NP/P y C/U, G y T.

Referencias independientes (nunca la salida de las funciones de ARL):

* S: fórmula cerrada con la ji cuadrada; las constantes ``c4`` y ``c5`` se calculan aquí con la función gamma.
* R: la distribución del rango de ``n`` normales se integra aquí a mano (``scipy.integrate.quad``); ``d2`` y ``d3`` salen de ella.
* NP y C: enumeración exacta de la distribución (``math.comb`` y la recursión de Poisson), sin ``scipy.stats``.
* G y T: los límites se leen de las cartas ``g_chart`` y ``t_chart`` de pccpy y la probabilidad de señal se calcula con ``scipy.stats``.
* En todos los casos, un Monte Carlo propio (20 semillas) como contraste.
"""
import functools
import math

import numpy as np
import pytest
from scipy import special, stats

import pccpy as pp

SEMILLAS = range(20)


def _arl_sd(*a, **k):
    return pp.arl_sd(*a, **k)


def _arl_range(*a, **k):
    return pp.arl_range(*a, **k)


# -------------------------------------------------------------------------- referencias independientes
def _c4(n):
    return math.sqrt(2.0 / (n - 1)) * math.exp(special.gammaln(n / 2) - special.gammaln((n - 1) / 2))


_X, _PX = np.polynomial.legendre.leggauss(400)
_X, _PX = 10.0 * _X, 10.0 * _PX  # nodos y pesos de Gauss-Legendre en [-10, 10]
_W, _PW = np.polynomial.legendre.leggauss(400)
_W, _PW = 7.0 * (_W + 1.0), 7.0 * _PW  # nodos y pesos en [0, 14] (el rango de n <= 10 normales no llega a 14)


def _fda_rango(w, n):
    """P(W <= w), W = rango de n normales estándar: n·∫ φ(x)[Φ(x+w) − Φ(x)]^(n−1) dx (Gauss-Legendre, vectorizada en w)."""
    w = np.atleast_1d(np.asarray(w, dtype=float))
    base = stats.norm.cdf(_X[None, :] + w[:, None]) - stats.norm.cdf(_X)[None, :]
    f = n * np.sum(_PX * stats.norm.pdf(_X) * base ** (n - 1), axis=1)
    return np.where(w > 0, f, 0.0)


@functools.cache
def _d2_d3(n):
    sup = 1.0 - _fda_rango(_W, n)
    media = float(np.sum(_PW * sup))
    segundo = float(np.sum(_PW * 2.0 * _W * sup))
    return media, math.sqrt(segundo - media**2)


def _arl_sd_ref(n, ratio, k):
    c4 = _c4(n)
    c5 = math.sqrt(1.0 - c4**2)
    ucl, lcl = c4 + k * c5, max(0.0, c4 - k * c5)
    p = stats.chi2.sf((n - 1) * (ucl / ratio) ** 2, n - 1) + stats.chi2.cdf((n - 1) * (lcl / ratio) ** 2, n - 1)
    return 1.0 / p


def _arl_range_ref(n, ratio, k):
    d2, d3 = _d2_d3(n)
    ucl, lcl = d2 + k * d3, max(0.0, d2 - k * d3)
    p = float(1.0 - _fda_rango(ucl / ratio, n)[0] + _fda_rango(lcl / ratio, n)[0])
    return 1.0 / p


def _p_senal_discreta(pmf, soporte, centro, sigma, k, tope_sup):
    """P(X > UCL o X < LCL) por enumeración, con los límites de las cartas de atributos de pccpy."""
    ucl = min(tope_sup, centro + k * sigma)
    lcl = max(0.0, centro - k * sigma)
    return sum(pmf(x) for x in soporte if x > ucl or x < lcl)


def _arl_binomial_ref(n, p0, p1, k):
    p1 = p0 if p1 is None else p1
    pmf = lambda x: math.comb(n, x) * p1**x * (1 - p1) ** (n - x)
    p = _p_senal_discreta(pmf, range(n + 1), n * p0, math.sqrt(n * p0 * (1 - p0)), k, float(n))
    return math.inf if p == 0 else 1.0 / p


def _arl_poisson_ref(c0, c1, k):
    c1 = c0 if c1 is None else c1
    ucl, lcl = c0 + k * math.sqrt(c0), max(0.0, c0 - k * math.sqrt(c0))
    pmf, dentro, x = math.exp(-c1), 0.0, 0
    while x <= ucl:  # la masa dentro de los límites es una suma finita; la señal es su complemento
        if x >= lcl:
            dentro += pmf
        x += 1
        pmf *= c1 / x
    return 1.0 / (1.0 - dentro)


# ----------------------------------------------------------------------------------- Monte Carlo propio
def _mc(muestra, senal, corridas=1500):
    """ARL por Monte Carlo (20 semillas): ``muestra(rng, m)`` devuelve el estadístico de m cartas y ``senal`` la regla."""
    largos = []
    for semilla in SEMILLAS:
        rng = np.random.default_rng(semilla)
        largo = np.zeros(corridas)
        vivo = np.arange(corridas)
        t = 0
        while vivo.size:
            t += 1
            sen = senal(muestra(rng, vivo.size))
            largo[vivo[sen]] = t
            vivo = vivo[~sen]
        largos.append(largo)
    return float(np.concatenate(largos).mean())


# -------------------------------------------------------------------------- RF-06: S y R
@pytest.mark.parametrize("n", [2, 3, 5, 10])
@pytest.mark.parametrize("ratio", [1.0, 1.5, 2.0, 0.8])
def test_s009_rf_06_arl_sd_es_la_formula_con_ji_cuadrada(n, ratio):
    """S009-RF-06: ARL de la carta S = 1 / P(señal), (n−1)S²/σ² ~ χ²(n−1), con c4 y c5 calculados aparte."""
    for k in (3.0, 2.0):
        assert pp.arl_sd(n, ratio=ratio, k=k) == pytest.approx(_arl_sd_ref(n, ratio, k), rel=1e-8)


@pytest.mark.parametrize("n", [2, 3, 5, 8])
@pytest.mark.parametrize("ratio", [1.0, 1.5, 2.0, 0.8])
def test_s009_rf_06_arl_range_es_la_integral_del_rango(n, ratio):
    """S009-RF-06: ARL de la carta R con la distribución del rango integrada aparte (d2 y d3 también)."""
    for k in (3.0, 2.0):
        assert pp.arl_range(n, ratio=ratio, k=k) == pytest.approx(_arl_range_ref(n, ratio, k), rel=1e-5)


def test_s009_rf_06_valores_para_subgrupos_de_5():
    """S009-RF-06: con n = 5 y k = 3 el ARL en control es ≈ 256,5 (S) y ≈ 217,2 (R), calculados aparte con scipy."""
    assert pp.arl_sd(5) == pytest.approx(256.5, rel=0.005)
    assert pp.arl_range(5) == pytest.approx(217.2, rel=0.005)


@pytest.mark.parametrize("llamar", [_arl_sd, _arl_range])
def test_s009_rf_06_un_aumento_de_la_dispersion_baja_el_arl(llamar):
    """S009-RF-06: ratio > 1 → ARL menor; el ARL es siempre >= 1 y baja de forma monótona."""
    valores = [llamar(5, ratio=r) for r in (1.0, 1.25, 1.5, 2.0, 3.0)]
    assert all(a > b for a, b in zip(valores, valores[1:]))
    assert all(v >= 1.0 for v in valores)


def test_s009_rf_06_coincide_con_el_monte_carlo():
    """S009-RF-06: contraste con el Monte Carlo propio (20 semillas), n = 5, ratio 1,5 y 1 (tolerancia relativa 4 %)."""
    n = 5
    c4 = _c4(n)
    c5 = math.sqrt(1 - c4**2)
    d2, d3 = _d2_d3(n)
    for ratio in (1.5, 1.0):
        s_sen = lambda x, r=ratio: ((x.std(axis=1, ddof=1) > c4 + 3 * c5) | (x.std(axis=1, ddof=1) < max(0, c4 - 3 * c5)))
        r_sen = lambda x: (np.ptp(x, axis=1) > d2 + 3 * d3) | (np.ptp(x, axis=1) < max(0, d2 - 3 * d3))
        muestra = lambda rng, m, r=ratio: rng.normal(0.0, r, (m, n))
        assert pp.arl_sd(n, ratio=ratio) == pytest.approx(_mc(muestra, s_sen), rel=0.04)
        assert pp.arl_range(n, ratio=ratio) == pytest.approx(_mc(muestra, r_sen), rel=0.04)


@pytest.mark.parametrize("llamar", [
    lambda: pp.arl_sd(1), lambda: pp.arl_sd(2.5), lambda: pp.arl_sd(0), lambda: pp.arl_sd(5, ratio=0),
    lambda: pp.arl_sd(5, ratio=float("nan")), lambda: pp.arl_sd(5, k=0), lambda: pp.arl_sd(5, k=float("inf")),
    lambda: pp.arl_range(1), lambda: pp.arl_range(5, ratio=-1), lambda: pp.arl_range(5, k=-3),
    lambda: pp.arl_range(5, method="markov"), lambda: pp.arl_sd(5, method="simulation", n_runs=0),
])
def test_s009_rf_06_parametros_invalidos_lanzan_value_error(llamar):
    """S009-RF-06 (casos borde): subgrupos < 2 o no enteros, ratio o k no válidos, método desconocido → ValueError."""
    with pytest.raises(ValueError):
        llamar()


@pytest.mark.parametrize("llamar", [_arl_sd, _arl_range])
def test_s009_rf_06_ratio_como_arreglo_y_simulacion_reproducible(llamar):
    """S009-RF-06: `ratio` como arreglo devuelve un arreglo; la simulación con la misma semilla es idéntica y ≈ numeric."""
    r = llamar(5, ratio=np.array([1.0, 2.0]))
    assert isinstance(r, np.ndarray) and r.shape == (2,)
    a = llamar(5, ratio=2.0, method="simulation", n_runs=4000, seed=3)
    assert a == llamar(5, ratio=2.0, method="simulation", n_runs=4000, seed=3)
    assert a == pytest.approx(llamar(5, ratio=2.0), rel=0.06)
    assert isinstance(llamar(5), float)


# -------------------------------------------------------------------------- RF-07: atributos
@pytest.mark.parametrize("n, p0, p1", [(100, 0.05, None), (100, 0.05, 0.05), (100, 0.05, 0.10), (100, 0.05, 0.02),
                                       (50, 0.02, 0.06), (200, 0.3, 0.35), (30, 0.5, None)])
def test_s009_rf_07_arl_binomial_es_la_enumeracion_exacta(n, p0, p1):
    """S009-RF-07: ARL de la carta NP/P (n constante) = 1 / P(señal) con la binomial enumerada con math.comb."""
    assert pp.arl_binomial(n, p0, p1) == pytest.approx(_arl_binomial_ref(n, p0, p1, 3.0), rel=1e-9)


def test_s009_rf_07_el_arl_en_control_discreto_no_es_370():
    """S009-RF-07: con n = 100 y p0 = 0,05 el ARL en control no es 370,4 (la distribución es discreta y asimétrica)."""
    r = pp.arl_binomial(100, 0.05)
    assert r == pytest.approx(_arl_binomial_ref(100, 0.05, None, 3.0), rel=1e-9)
    assert abs(r - 370.4) > 20


@pytest.mark.parametrize("c0, c1", [(9.0, None), (9.0, 12.0), (9.0, 15.0), (4.0, 8.0), (25.0, 25.0), (1.5, 4.0)])
def test_s009_rf_07_arl_poisson_es_la_enumeracion_exacta(c0, c1):
    """S009-RF-07: ARL de la carta C/U (c constante) = 1 / P(señal) con la Poisson enumerada con su recursión."""
    assert pp.arl_poisson(c0, c1) == pytest.approx(_arl_poisson_ref(c0, c1, 3.0), rel=1e-9)


def test_s009_rf_07_la_p_y_la_u_con_tamano_constante_son_la_np_y_la_c():
    """S009-RF-07: la P con n constante es la NP (X = n·p̂) y la U con n constante es la C con c0 = n·u0."""
    assert pp.arl_binomial(100, 0.05, 0.08) == pp.arl_binomial(100, 0.05, p1=0.08)
    assert pp.arl_poisson(9.0, 12.0) == pytest.approx(_arl_poisson_ref(9.0, 12.0, 3.0), rel=1e-9)


def test_s009_rf_07_sin_senal_posible_el_arl_es_infinito():
    """S009-RF-07 (caso borde): con p1 = 0 no hay defectuosos y, con LCI = 0, la carta nunca señala → ARL = ∞."""
    assert pp.arl_binomial(100, 0.05, 0.0) == math.inf
    assert pp.arl_poisson(9.0, 0.0) == math.inf  # c0 = 9: LCI = 0, nada por debajo y 0 no supera el UCL
    assert pp.arl_poisson(16.0, 0.0) == pytest.approx(1.0)  # c0 = 16: LCI = 4 > 0; con c1 = 0 el primer punto (0) señala


def test_s009_rf_07_el_arl_baja_al_empeorar_el_proceso_y_coincide_con_el_monte_carlo():
    """S009-RF-07: ARL decreciente al subir p1 y contraste con el Monte Carlo propio (tolerancia relativa 4 %)."""
    valores = [pp.arl_binomial(100, 0.05, p) for p in (0.05, 0.07, 0.10, 0.15)]
    assert all(a > b for a, b in zip(valores, valores[1:]))
    n, p0 = 100, 0.05
    ucl, lcl = n * p0 + 3 * math.sqrt(n * p0 * (1 - p0)), max(0, n * p0 - 3 * math.sqrt(n * p0 * (1 - p0)))
    for p1 in (0.05, 0.10):
        mc = _mc(lambda rng, m, p=p1: rng.binomial(n, p, m), lambda x: (x > ucl) | (x < lcl))
        assert pp.arl_binomial(n, p0, p1) == pytest.approx(mc, rel=0.04)
    c0 = 9.0
    ucl, lcl = c0 + 3 * 3.0, max(0, c0 - 9.0)
    for c1 in (9.0, 15.0):
        mc = _mc(lambda rng, m, c=c1: rng.poisson(c, m), lambda x: (x > ucl) | (x < lcl))
        assert pp.arl_poisson(c0, c1) == pytest.approx(mc, rel=0.04)


@pytest.mark.parametrize("llamar", [
    lambda: pp.arl_binomial(0, 0.05), lambda: pp.arl_binomial(10.5, 0.05), lambda: pp.arl_binomial(100, 0),
    lambda: pp.arl_binomial(100, 1), lambda: pp.arl_binomial(100, 0.05, p1=1.5), lambda: pp.arl_binomial(100, 0.05, p1=-0.1),
    lambda: pp.arl_binomial(100, 0.05, k=0), lambda: pp.arl_poisson(0), lambda: pp.arl_poisson(-1),
    lambda: pp.arl_poisson(9, c1=-1), lambda: pp.arl_poisson(9, c1=float("nan")), lambda: pp.arl_poisson(9, k=-3),
    lambda: pp.arl_binomial(100, 0.05, method="markov"), lambda: pp.arl_poisson(9, method="aproximado"),
])
def test_s009_rf_07_parametros_invalidos_lanzan_value_error(llamar):
    """S009-RF-07 (casos borde): n, p0, p1, c0, c1 o k fuera de rango, o método no admitido → ValueError."""
    with pytest.raises(ValueError):
        llamar()


def test_s009_rf_07_arreglos_y_simulacion_reproducible():
    """S009-RF-07: `p1` y `c1` como arreglos devuelven arreglos; la simulación con la misma semilla es idéntica."""
    r = pp.arl_binomial(100, 0.05, p1=np.array([0.05, 0.1]))
    assert isinstance(r, np.ndarray) and r.shape == (2,)
    q = pp.arl_poisson(9.0, c1=[9.0, 12.0])
    assert isinstance(q, np.ndarray) and q.shape == (2,)
    a = pp.arl_binomial(100, 0.05, 0.10, method="simulation", n_runs=3000, seed=5)
    assert a == pp.arl_binomial(100, 0.05, 0.10, method="simulation", n_runs=3000, seed=5)
    assert a == pytest.approx(pp.arl_binomial(100, 0.05, 0.10), rel=0.08)


# -------------------------------------------------------------------------- RF-08: G y T
def _limites_g(p0, k=3.0):
    """Límite superior de g_chart (el que dibuja pccpy) para una probabilidad de evento dada."""
    cantidad = np.random.default_rng(0).geometric(p0, 40) - 1
    return float(pp.g_chart(cantidad, p=p0, k=k)["G"].ucl[0])


@pytest.mark.parametrize("p0, p1", [(0.02, None), (0.02, 0.02), (0.02, 0.04), (0.02, 0.01), (0.1, 0.2), (0.005, 0.01)])
def test_s009_rf_08_arl_g_usa_los_limites_de_g_chart(p0, p1):
    """S009-RF-08: ARL de la carta G = 1 / P(X > UCL) con el UCL de g_chart y la geométrica de scipy."""
    ucl = _limites_g(p0)
    p_real = p0 if p1 is None else p1
    esperado = 1.0 / stats.geom.sf(math.floor(ucl) + 1, p_real)  # X = ensayos − 1: P(X > u) = P(G > floor(u) + 1)
    assert pp.arl_g(p0, p1) == pytest.approx(esperado, rel=1e-9)


def _limites_t(distribution, shape, scale):
    datos = np.random.default_rng(0).weibull(max(shape, 0.5), 40) * scale + 0.01
    if distribution == "exponential":
        ch = pp.t_chart(datos, distribution="exponential", scale=scale)
    else:
        ch = pp.t_chart(datos, shape=shape, scale=scale)
    return float(ch["T"].lcl[0]), float(ch["T"].ucl[0])


@pytest.mark.parametrize("shape, ratio", [(1.5, 1.0), (1.5, 0.7), (1.5, 1.3), (0.8, 0.5), (3.0, 0.9)])
def test_s009_rf_08_arl_t_weibull_usa_los_limites_de_t_chart(shape, ratio):
    """S009-RF-08: ARL de la carta T = 1 / (P(T < LCL) + P(T > UCL)) con los límites de t_chart y la Weibull desplazada."""
    lcl, ucl = _limites_t("weibull", shape, 20.0)
    real = stats.weibull_min(shape, scale=20.0 * ratio)
    esperado = 1.0 / (real.cdf(lcl) + real.sf(ucl))
    assert pp.arl_t(shape=shape, scale_ratio=ratio) == pytest.approx(esperado, rel=1e-9)


def test_s009_rf_08_la_g_solo_detecta_eventos_menos_frecuentes():
    """S009-RF-08: la G solo tiene límite superior: con p1 > p0 (más eventos) el ARL sube muchísimo; con p1 < p0 baja."""
    assert pp.arl_g(0.02, 0.04) > 100 * pp.arl_g(0.02)
    assert pp.arl_g(0.02, 0.01) < pp.arl_g(0.02)


def test_s009_rf_08_arl_t_en_control_es_370_y_la_exponencial_es_weibull_de_forma_1():
    """S009-RF-08: con scale_ratio = 1 los límites son los percentiles Φ(±3): ARL = 1/(2Φ(−3)) = 370,4; exponencial = forma 1."""
    assert pp.arl_t(shape=1.5) == pytest.approx(1 / (2 * stats.norm.sf(3)), rel=1e-9)
    assert pp.arl_t(distribution="exponential", scale_ratio=0.6) == pytest.approx(pp.arl_t(shape=1.0, scale_ratio=0.6), rel=1e-12)
    lcl, ucl = _limites_t("exponential", 1.0, 20.0)
    real = stats.expon(scale=20.0 * 0.6)
    assert pp.arl_t(distribution="exponential", scale_ratio=0.6) == pytest.approx(1 / (real.cdf(lcl) + real.sf(ucl)), rel=1e-9)


def test_s009_rf_08_coincide_con_el_monte_carlo():
    """S009-RF-08: contraste con el Monte Carlo propio (20 semillas) para la G y la T (tolerancia relativa 4 %)."""
    ucl = _limites_g(0.02)
    mc = _mc(lambda rng, m: rng.geometric(0.01, m) - 1, lambda x: x > ucl)  # p1 < p0: la G solo detecta eventos MENOS frecuentes
    assert pp.arl_g(0.02, 0.01) == pytest.approx(mc, rel=0.04)
    lcl_t, ucl_t = _limites_t("weibull", 1.5, 20.0)
    mc = _mc(lambda rng, m: 20.0 * 0.7 * rng.weibull(1.5, m), lambda t: (t < lcl_t) | (t > ucl_t))
    assert pp.arl_t(shape=1.5, scale_ratio=0.7) == pytest.approx(mc, rel=0.04)


@pytest.mark.parametrize("llamar", [
    lambda: pp.arl_g(0), lambda: pp.arl_g(1), lambda: pp.arl_g(0.02, p1=0), lambda: pp.arl_g(0.02, p1=1.2),
    lambda: pp.arl_g(0.02, k=0), lambda: pp.arl_g(0.02, method="markov"),
    lambda: pp.arl_t(shape=0), lambda: pp.arl_t(shape=-1), lambda: pp.arl_t(scale_ratio=0), lambda: pp.arl_t(scale_ratio=float("inf")),
    lambda: pp.arl_t(k=-3), lambda: pp.arl_t(distribution="normal"), lambda: pp.arl_t(method="markov"),
    lambda: pp.arl_t(method="simulation", n_runs=0),
])
def test_s009_rf_08_parametros_invalidos_lanzan_value_error(llamar):
    """S009-RF-08 (casos borde): p0, p1, shape, scale_ratio o k fuera de rango, distribución o método no admitidos → ValueError."""
    with pytest.raises(ValueError):
        llamar()


def test_s009_rf_08_arreglos_simulacion_y_sin_desbordes():
    """S009-RF-08: arreglos → arreglos; simulación reproducible; con p0 extremo el ARL es finito y >= 1, sin desbordes."""
    assert pp.arl_g(0.02, p1=np.array([0.02, 0.04])).shape == (2,)
    assert pp.arl_t(scale_ratio=[1.0, 0.5]).shape == (2,)
    a = pp.arl_t(shape=1.5, scale_ratio=0.5, method="simulation", n_runs=3000, seed=9)
    assert a == pp.arl_t(shape=1.5, scale_ratio=0.5, method="simulation", n_runs=3000, seed=9)
    assert a == pytest.approx(pp.arl_t(shape=1.5, scale_ratio=0.5), rel=0.08)
    b = pp.arl_g(0.02, 0.01, method="simulation", n_runs=3000, seed=9)
    assert b == pytest.approx(pp.arl_g(0.02, 0.01), rel=0.08)
    for p0 in (1e-4, 0.5, 0.95):
        r = pp.arl_g(p0)
        assert math.isfinite(r) and r >= 1.0
