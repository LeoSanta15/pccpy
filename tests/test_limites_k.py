"""Pruebas de la especificación 014 (parte B): ancho de los límites de control con ``k`` y ``alpha``.

Referencias independientes: fórmulas de Montgomery con las constantes de la tabla (d2, d3, c4, c5), la fórmula binomial y de Poisson
a mano, ``scipy.stats.norm`` y simulación. Nunca la salida de pccpy salvo la consistencia entre funciones de pccpy.
"""
import re
import warnings
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

import pccpy

RAIZ = Path(__file__).resolve().parents[1]
D2_2, D3_2 = 2 / np.sqrt(np.pi), np.sqrt(2 - 4 / np.pi)  # rango de 2 normales: media y desviación (cálculo exacto)
D2_5, D3_5, C4_5 = 2.326, 0.864, 0.9400  # Montgomery, tabla de factores (n = 5)
C5_5 = np.sqrt(1 - C4_5**2)


def _x(seed=0, n=80, mu=10.0, sd=1.0):
    return np.random.default_rng(seed).normal(mu, sd, n)


def _g(seed=1, filas=25, n=5, mu=50.0, sd=2.0):
    return np.random.default_rng(seed).normal(mu, sd, (filas, n))


def _sigma_mr(x):
    return np.mean(np.abs(np.diff(x))) / D2_2


# ── S014-RF-04: k en I-MR, Xbar-R y Xbar-S ────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("k", [1.5, 2.0, 2.576, 3.0])
def test_s014_rf_04_imr_k_simetrico(k):
    x = _x()
    s = _sigma_mr(x)
    c = pccpy.imr_chart(x, k=k)
    i, mr = c["I"], c["MR"]
    assert i.ucl[0] - i.center[0] == pytest.approx(k * s, rel=1e-9)
    assert i.center[0] - i.lcl[0] == pytest.approx(k * s, rel=1e-9)
    assert mr.ucl[0] == pytest.approx(D2_2 * s + k * D3_2 * s, rel=1e-9)
    assert mr.lcl[0] == pytest.approx(max(0.0, D2_2 * s - k * D3_2 * s), rel=1e-9)


def test_s014_rf_04_imr_k_pareja_superior_inferior():
    x = _x()
    s = _sigma_mr(x)
    c = pccpy.imr_chart(x, k=(3, 2))
    i, mr = c["I"], c["MR"]
    assert i.ucl[0] - i.center[0] == pytest.approx(3 * s, rel=1e-9)
    assert i.center[0] - i.lcl[0] == pytest.approx(2 * s, rel=1e-9)
    assert mr.ucl[0] == pytest.approx(D2_2 * s + 3 * D3_2 * s, rel=1e-9)
    assert mr.lcl[0] == pytest.approx(max(0.0, D2_2 * s - 2 * D3_2 * s), rel=1e-9)


def test_s014_rf_04_k_3_es_identico_a_no_pasar_k():
    x = _x()
    a, b = pccpy.imr_chart(x), pccpy.imr_chart(x, k=3)
    for pa, pb in zip(a.panels, b.panels):
        np.testing.assert_array_equal(pa.ucl, pb.ucl)
        np.testing.assert_array_equal(pa.lcl, pb.lcl)
        np.testing.assert_array_equal(pa.center, pb.center)
    g = _g()
    a, b = pccpy.xbar_r_chart(g), pccpy.xbar_r_chart(g, k=(3, 3))
    for pa, pb in zip(a.panels, b.panels):
        np.testing.assert_array_equal(pa.ucl, pb.ucl)
        np.testing.assert_array_equal(pa.lcl, pb.lcl)


@pytest.mark.parametrize("k", [2.0, (3, 2)])
def test_s014_rf_04_xbar_r(k):
    g = _g()
    ksup, kinf = (k, k) if np.isscalar(k) else k
    s = np.mean(g.max(axis=1) - g.min(axis=1)) / D2_5
    c = pccpy.xbar_r_chart(g, k=k)
    xb, r = c["Xbar"], c["R"]
    centro = g.mean()
    assert xb.center[0] == pytest.approx(centro)
    assert xb.ucl[0] - centro == pytest.approx(ksup * s / np.sqrt(5), rel=2e-3)
    assert centro - xb.lcl[0] == pytest.approx(kinf * s / np.sqrt(5), rel=2e-3)
    assert r.ucl[0] == pytest.approx(D2_5 * s + ksup * D3_5 * s, rel=3e-3)
    assert r.lcl[0] == pytest.approx(max(0.0, D2_5 * s - kinf * D3_5 * s), rel=3e-3)


@pytest.mark.parametrize("k", [2.0, (3, 2)])
def test_s014_rf_04_xbar_s(k):
    g = _g()
    ksup, kinf = (k, k) if np.isscalar(k) else k
    s = np.mean(g.std(axis=1, ddof=1)) / C4_5
    c = pccpy.xbar_s_chart(g, k=k)
    xb, sp = c["Xbar"], c["S"]
    centro = g.mean()
    assert xb.ucl[0] - centro == pytest.approx(ksup * s / np.sqrt(5), rel=2e-3)
    assert centro - xb.lcl[0] == pytest.approx(kinf * s / np.sqrt(5), rel=2e-3)
    assert sp.ucl[0] == pytest.approx(C4_5 * s + ksup * C5_5 * s, rel=3e-3)
    assert sp.lcl[0] == pytest.approx(max(0.0, C4_5 * s - kinf * C5_5 * s), rel=3e-3)


def test_s014_rf_04_alpha_equivale_a_k():
    x = _x()
    a = pccpy.imr_chart(x, alpha=2 * stats.norm.sf(2))  # bilateral 0,0455 ↔ k = 2
    b = pccpy.imr_chart(x, k=2)
    np.testing.assert_allclose(a["I"].ucl, b["I"].ucl, rtol=1e-9)
    np.testing.assert_allclose(a["I"].lcl, b["I"].lcl, rtol=1e-9)
    par = pccpy.imr_chart(x, alpha=(0.00135, 0.025))  # unilateral por lado ↔ k = (3, 1,96)
    s = _sigma_mr(x)
    assert par["I"].ucl[0] - par["I"].center[0] == pytest.approx(stats.norm.isf(0.00135) * s, rel=1e-9)
    assert par["I"].center[0] - par["I"].lcl[0] == pytest.approx(stats.norm.isf(0.025) * s, rel=1e-9)


# ── S014-RF-05: atributos ─────────────────────────────────────────────────────────────────────────────────────────────

def _atributos(seed=2):
    rng = np.random.default_rng(seed)
    n = rng.integers(80, 160, 30)
    return rng.binomial(n, 0.06), n, rng.poisson(5, 30), rng.integers(1, 4, 30)


def test_s014_rf_05_p_chart_k_punto_a_punto():
    d, n, _, _ = _atributos()
    pbar = d.sum() / n.sum()
    sig = np.sqrt(pbar * (1 - pbar) / n)
    for k, (ks, ki) in ((2.0, (2, 2)), ((3, 2), (3, 2))):
        p = pccpy.p_chart(d, n, k=k)["P"]
        np.testing.assert_allclose(p.ucl, np.minimum(1.0, pbar + ks * sig), rtol=1e-9)
        np.testing.assert_allclose(p.lcl, np.maximum(0.0, pbar - ki * sig), rtol=1e-9)


def test_s014_rf_05_np_c_u():
    d, n, c, u_n = _atributos()
    n0 = int(n[0])
    dd = np.random.default_rng(5).binomial(n0, 0.06, 30)
    pbar = dd.mean() / n0
    s = np.sqrt(n0 * pbar * (1 - pbar))
    npc = pccpy.np_chart(dd, n0, k=2)["NP"]
    assert npc.ucl[0] == pytest.approx(n0 * pbar + 2 * s, rel=1e-9)
    assert npc.lcl[0] == pytest.approx(max(0.0, n0 * pbar - 2 * s), rel=1e-9)
    cc = pccpy.c_chart(c, k=(3, 2))["C"]
    cbar = c.mean()
    assert cc.ucl[0] == pytest.approx(cbar + 3 * np.sqrt(cbar), rel=1e-9)
    assert cc.lcl[0] == pytest.approx(max(0.0, cbar - 2 * np.sqrt(cbar)), rel=1e-9)
    ub = c.sum() / u_n.sum()
    uu = pccpy.u_chart(c, u_n, k=2)["U"]
    np.testing.assert_allclose(uu.ucl, ub + 2 * np.sqrt(ub / u_n), rtol=1e-9)
    np.testing.assert_allclose(uu.lcl, np.maximum(0.0, ub - 2 * np.sqrt(ub / u_n)), rtol=1e-9)


def test_s014_rf_05_p_se_recorta_en_0_y_1():
    d = np.array([90, 95, 92, 91, 93])
    p = pccpy.p_chart(d, np.full(5, 100), k=40)["P"]
    assert p.ucl.max() == 1.0
    assert p.lcl.min() == 0.0


@pytest.mark.parametrize("nombre", ["laney_p_chart", "laney_u_chart"])
def test_s014_rf_05_laney_escala_con_k(nombre):
    d, n, c, u_n = _atributos()
    args = (d, n) if nombre == "laney_p_chart" else (c, u_n)
    f = getattr(pccpy, nombre)
    a, b = f(*args), f(*args, k=2)
    pa, pb = a.panels[0], b.panels[0]
    np.testing.assert_allclose(pb.ucl - pb.center, (pa.ucl - pa.center) * 2 / 3, rtol=1e-9)
    np.testing.assert_allclose(pb.center, pa.center)


# ── S014-RF-06: Z-MR e I-MR-R/S ───────────────────────────────────────────────────────────────────────────────────────

def test_s014_rf_06_zmr():
    rng = np.random.default_rng(4)
    x = rng.normal(0, 1, 20)
    parts = ["A"] * 10 + ["B"] * 10
    kw = dict(mu={"A": 0, "B": 0}, sigma={"A": 1, "B": 1})
    z = pccpy.zmr_chart(x, parts, k=(3, 2), **kw)["Z"]
    assert z.ucl[0] == pytest.approx(3.0)
    assert z.lcl[0] == pytest.approx(-2.0)
    z2 = pccpy.zmr_chart(x, parts, k=2, **kw)["Z"]
    assert z2.ucl[0] == pytest.approx(2.0)
    assert z2.lcl[0] == pytest.approx(-2.0)


def test_s014_rf_06_imr_rs_escala_con_k():
    g = _g(filas=20, n=4)
    a, b = pccpy.imr_rs_chart(g), pccpy.imr_rs_chart(g, k=2)
    for pa, pb in zip(a.panels, b.panels):
        np.testing.assert_allclose(pb.ucl - pb.center, (pa.ucl - pa.center) * 2 / 3, rtol=1e-9)


# ── S014-RF-07: la prueba 1 sigue a los límites ──────────────────────────────────────────────────────────────────────

def _con_atipicos():
    x = _x(seed=7, n=100)
    x[[20, 55]] += 4
    x[[40, 80]] -= 3.5
    return x


def test_s014_rf_07_prueba_1_coincide_con_los_limites_dibujados():
    x = _con_atipicos()
    for k in (2.0, (3, 2), (2.5, 3.5)):
        c = pccpy.imr_chart(x, k=k)
        i = c["I"]
        fuera = set(np.flatnonzero((i.values > i.ucl) | (i.values < i.lcl)))
        assert set(i.violations.get(1, [])) == fuera
        assert fuera  # hay puntos que comprobar


def test_s014_rf_07_test_params_1_gana_y_avisa():
    x = _con_atipicos()
    with pytest.warns(UserWarning):
        c = pccpy.imr_chart(x, k=2, test_params={1: 3})
    i = c["I"]
    sigma = c.params[0]["sigma"]
    z = np.abs(i.values - i.center) / sigma
    assert set(i.violations.get(1, [])) == set(np.flatnonzero(z > 3))


def test_s014_rf_07_sin_k_test_params_1_sigue_igual_y_sin_aviso():
    x = _con_atipicos()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        c = pccpy.imr_chart(x, test_params={1: 2})
    i = c["I"]
    sigma = c.params[0]["sigma"]
    assert set(i.violations.get(1, [])) == set(np.flatnonzero(np.abs(i.values - i.center) / sigma > 2))
    assert i.ucl[0] - i.center[0] == pytest.approx(3 * sigma)


def test_s014_rf_07_pruebas_2_a_8_no_cambian_con_k():
    x = _x(seed=3, n=200)
    kw = dict(mu=10.0, sigma=1.0, tests="all")
    a, b = pccpy.imr_chart(x, **kw), pccpy.imr_chart(x, k=2, **kw)
    for t in range(2, 9):
        np.testing.assert_array_equal(a["I"].violations.get(t, []), b["I"].violations.get(t, []))
    assert any(len(a["I"].violations.get(t, [])) for t in range(2, 9))


# ── S014-RF-08: validación ───────────────────────────────────────────────────────────────────────────────────────────

INVALIDOS = [
    {"k": 0}, {"k": -1}, {"k": float("nan")}, {"k": float("inf")}, {"k": "3"}, {"k": True}, {"k": (3, 3, 3)}, {"k": (3,)},
    {"k": (3, -1)}, {"alpha": 0}, {"alpha": 1}, {"alpha": float("nan")}, {"alpha": (0.01, 1.5)}, {"k": 3, "alpha": 0.01},
]


@pytest.mark.parametrize("kw", INVALIDOS, ids=lambda d: ",".join(f"{a}={b!r}" for a, b in d.items()))
def test_s014_rf_08_valores_invalidos_lanzan_value_error_traducible(kw):
    x = _x()
    with pccpy.language("es"), pytest.raises(ValueError) as es:
        pccpy.imr_chart(x, **kw)
    with pccpy.language("en"), pytest.raises(ValueError) as en:
        pccpy.imr_chart(x, **kw)
    assert str(es.value) != str(en.value)


@pytest.mark.parametrize("f, args", [
    (pccpy.xbar_r_chart, (_g(),)), (pccpy.xbar_s_chart, (_g(),)), (pccpy.p_chart, (np.array([3, 4, 5]), 100)),
    (pccpy.c_chart, (np.array([3, 4, 5]),)), (pccpy.imr_rs_chart, (_g(),)),
])
def test_s014_rf_08_todas_las_cartas_validan_k(f, args):
    with pytest.raises(ValueError):
        f(*args, k=-2)
    with pytest.raises(ValueError):
        f(*args, k=2, alpha=0.05)


# ── S014-RF-09: transform, stages, mu y sigma ────────────────────────────────────────────────────────────────────────

def test_s014_rf_09_transform_aplica_k_en_la_escala_transformada():
    x = np.random.default_rng(1).lognormal(1.0, 0.4, 80)
    c = pccpy.imr_chart(x, transform="boxcox", k=2)
    t = c.transformation
    prm = c.params[0]
    centro_t, sigma_t = prm["mean"], prm["sigma"]
    i = c["I"]
    np.testing.assert_allclose(i.ucl, t.inverse(np.full(x.size, centro_t + 2 * sigma_t)), rtol=1e-9)
    np.testing.assert_allclose(i.lcl, t.inverse(np.full(x.size, centro_t - 2 * sigma_t)), rtol=1e-9)


def test_s014_rf_09_etapas_mu_y_sigma():
    x = np.r_[_x(seed=1, n=30, mu=10), _x(seed=2, n=30, mu=20)]
    etapas = [1] * 30 + [2] * 30
    c = pccpy.imr_chart(x, stages=etapas, k=2)
    i = c["I"]
    for ini, fin in ((0, 30), (30, 60)):
        s = _sigma_mr(x[ini:fin])
        assert i.ucl[ini] - i.center[ini] == pytest.approx(2 * s, rel=1e-9)
    h = pccpy.imr_chart(x, mu=10.0, sigma=1.0, k=(3, 2))["I"]
    assert h.ucl[0] == pytest.approx(13.0)
    assert h.lcl[0] == pytest.approx(8.0)


# ── S014-RF-10: params, probability() y ARL ──────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kw, esperado", [
    ({}, (3.0, 3.0)), ({"k": 2}, (2.0, 2.0)), ({"k": (3, 2)}, (3.0, 2.0)),
    ({"alpha": 0.0455}, (stats.norm.isf(0.0455 / 2),) * 2), ({"alpha": (0.00135, 0.025)}, (stats.norm.isf(0.00135), stats.norm.isf(0.025))),
])
def test_s014_rf_10_params_guarda_k_upper_y_k_lower(kw, esperado):
    p = pccpy.imr_chart(_x(), **kw).params[0]
    assert p["k_upper"] == pytest.approx(esperado[0])
    assert p["k_lower"] == pytest.approx(esperado[1])


def test_s014_rf_10_summary_muestra_las_claves_traducidas():
    c = pccpy.imr_chart(_x(), k=(3, 2))
    with pccpy.language("es"):
        assert "k_sup=3" in c.summary() and "k_inf=2" in c.summary()
    with pccpy.language("en"):
        assert "k_upper=3" in c.summary() and "k_lower=2" in c.summary()
    with pccpy.language("es"):  # con los límites a 3σ el resumen queda como antes
        assert "k_sup" not in pccpy.imr_chart(_x()).summary()


def test_s014_rf_10_probability_coincide_con_el_arl_y_con_scipy():
    x = _x()
    c = pccpy.imr_chart(x, mu=10.0, sigma=1.0, k=2)
    p = c.probability().probability
    assert p == pytest.approx(2 * stats.norm.sf(2), rel=1e-9)
    assert 1 / p == pytest.approx(float(pccpy.arl_shewhart(k=2)), rel=1e-6)
    c2 = pccpy.imr_chart(x, mu=10.0, sigma=1.0, k=(3, 2))
    assert c2.probability().probability == pytest.approx(stats.norm.sf(3) + stats.norm.sf(2), rel=1e-9)


def test_s014_rf_10_probabilidad_de_la_carta_r_y_p_contra_simulacion():
    """Referencia: simulación con 20 semillas (tolerancia 5 % relativo)."""
    ksup, kinf = 3.0, 1.0
    sd = 1.0
    c = pccpy.xbar_r_chart(np.zeros((5, 5)) + np.arange(25).reshape(5, 5) * 0.001, mu=0.0, sigma=sd, k=(ksup, kinf))
    r = c["R"]
    tasas = []
    for seed in range(20):
        g = np.random.default_rng(seed).normal(0, sd, (20000, 5))
        rango = g.max(axis=1) - g.min(axis=1)
        tasas.append(np.mean((rango > r.ucl[0]) | (rango < r.lcl[0])))
    assert c.probability(panel="R", point=1).probability == pytest.approx(np.mean(tasas), rel=0.05)
    n, p0 = 100, 0.05
    cp = pccpy.p_chart(np.array([5, 5, 5, 5]), n, p=p0, k=(3, 2))
    pp = cp["P"]
    tasas = []
    for seed in range(20):
        d = np.random.default_rng(seed).binomial(n, p0, 40000) / n
        tasas.append(np.mean((d > pp.ucl[0]) | (d < pp.lcl[0])))
    assert cp.probability(point=1).probability == pytest.approx(np.mean(tasas), rel=0.05)


# ── S014-RF-11: alpha y k_from_confidence ────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("conf, k", [(0.9973, 3.0), (0.95, 1.959964), (0.99, 2.575829), (0.6827, 1.0)])
def test_s014_rf_11_k_from_confidence(conf, k):
    assert pccpy.k_from_confidence(conf) == pytest.approx(k, abs=2e-3)
    assert pccpy.k_from_confidence(conf) == pytest.approx(stats.norm.ppf(1 - (1 - conf) / 2))


@pytest.mark.parametrize("conf", [0, 1, -0.1, 1.2, float("nan")])
def test_s014_rf_11_k_from_confidence_fuera_de_rango(conf):
    with pytest.raises(ValueError):
        pccpy.k_from_confidence(conf)


def test_s014_rf_11_alpha_un_valor_es_bilateral_y_un_par_es_unilateral():
    x = _x()
    a = pccpy.imr_chart(x, alpha=0.0027).params[0]
    b = pccpy.imr_chart(x, alpha=(0.00135, 0.00135)).params[0]
    assert a["k_upper"] == pytest.approx(3.0, abs=2e-3)
    assert (b["k_upper"], b["k_lower"]) == pytest.approx((3.0, 3.0), abs=2e-3)


# ── S014-RF-12: zonas reescalables ───────────────────────────────────────────────────────────────────────────────────

def _viol(x, tests, **kw):
    return pccpy.imr_chart(np.asarray(x, dtype=float), mu=0.0, sigma=1.0, tests=tests, **kw)["I"].violations


def test_s014_rf_12_por_defecto_las_zonas_siguen_en_1_y_2_sigma():
    x = [0, 0, 1.5, 1.5, 0, 0, 0, 0.8, 0.8, 0.8, 0.8, 0]
    for kw in ({}, {"k": 2}, {"k": 2, "rescale_zones": False}):
        v = _viol(x, (5, 6), **kw)
        assert len(v.get(5, [])) == 0 and len(v.get(6, [])) == 0


def test_s014_rf_12_rescale_zones_mueve_las_fronteras_a_k_sobre_3():
    # k = 2: fronteras en 2/3 σ y 4/3 σ; 1,5σ (dos de tres) activa la prueba 5 y 0,8σ (cuatro de cinco) la 6
    v5 = _viol([0, 0, 1.5, 1.5, 0, 0], (5,), k=2, rescale_zones=True)
    assert 3 in v5.get(5, [])
    v6 = _viol([0, 0.8, 0.8, 0.8, 0.8, 0], (6,), k=2, rescale_zones=True)
    assert 4 in v6.get(6, [])


def test_s014_rf_12_con_k_3_no_cambia_nada():
    rng = np.random.default_rng(9)
    x = rng.normal(0, 1, 300)
    a = _viol(x, "all")
    b = _viol(x, "all", k=3, rescale_zones=True)
    for t in range(1, 9):
        np.testing.assert_array_equal(a.get(t, []), b.get(t, []))


def test_s014_rf_12_zonas_asimetricas_por_lado():
    # k = (3, 1,5): arriba la frontera de la zona A sigue en 2σ; abajo pasa a 1σ
    arriba = _viol([0, 0, 1.5, 1.5, 0, 0], (5,), k=(3, 1.5), rescale_zones=True)
    abajo = _viol([0, 0, -1.5, -1.5, 0, 0], (5,), k=(3, 1.5), rescale_zones=True)
    assert len(arriba.get(5, [])) == 0
    assert 3 in abajo.get(5, [])


# ── S014-RF-13: documentación ────────────────────────────────────────────────────────────────────────────────────────

ENCABEZADO = {"README.md": r"^###? .*`k`.*`alpha`", "README_en.md": r"^###? .*`k`.*`alpha`"}


@pytest.mark.parametrize("nombre", ["README.md", "README_en.md"])
def test_s014_rf_13_el_readme_documenta_k_alpha_y_su_fragmento_corre(nombre):
    texto = (RAIZ / nombre).read_text(encoding="utf-8")
    m = re.search(ENCABEZADO[nombre], texto, re.MULTILINE)
    assert m, f"{nombre}: falta la sección de `k` y `alpha`"
    seccion = texto[m.start():]
    seccion = seccion[: re.search(r"^## ", seccion[3:], re.MULTILINE).start() + 3] if re.search(r"^## ", seccion[3:], re.MULTILINE) else seccion
    for palabra in ("k_from_confidence", "rescale_zones"):
        assert palabra in seccion
    bloques = re.findall(r"```python\n(.*?)```", seccion, re.DOTALL)
    assert bloques
    ns: dict = {}
    import matplotlib

    matplotlib.use("Agg")
    exec("import numpy as np\nimport pccpy as pp\nrng = np.random.default_rng(1)\nx = rng.normal(10, 1, 60)\n" + "\n".join(bloques), ns)
