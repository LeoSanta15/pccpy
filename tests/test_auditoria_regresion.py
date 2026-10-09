"""Hallazgos de la auditoría estadística de 0.13.1: cada uno queda fijado con una referencia escrita aparte."""
import math

import numpy as np
import pytest
from scipy import stats

import pccpy as pp
from pccpy._constants import c4, d2, d3

# ── Fase 1 ───────────────────────────────────────────────────────────────────


def _confianza_bilateral(n, r, p):
    """P(cobertura de [X_(r), X_(n+1-r)] ≥ p): la cobertura es Beta(n − 2r + 1, 2r)."""
    return 1.0 - stats.beta.cdf(p, n - 2 * r + 1, 2 * r)


def test_tolerancia_no_parametrica_bilateral_exige_n_93_para_95_95():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        pp.tolerance_interval(rng.normal(size=92), coverage=0.95, confidence=0.95, method="nonparametric", sides="two")
    r = pp.tolerance_interval(rng.normal(size=93), coverage=0.95, confidence=0.95, method="nonparametric", sides="two")
    assert r.achieved_confidence == pytest.approx(_confianza_bilateral(93, 1, 0.95), abs=1e-12)
    assert r.achieved_confidence == pytest.approx(0.95002, abs=2e-5)


def test_tolerancia_no_parametrica_bilateral_elige_el_intervalo_mas_estrecho_valido():
    x = np.random.default_rng(1).normal(size=300)
    r = pp.tolerance_interval(x, coverage=0.95, confidence=0.95, method="nonparametric", sides="two")
    xs = np.sort(x)
    assert r.lower == xs[3] and r.upper == xs[300 - 4]  # r = 4
    assert r.achieved_confidence == pytest.approx(_confianza_bilateral(300, 4, 0.95), abs=1e-12)
    assert r.achieved_confidence == pytest.approx(0.984, abs=1e-3)


def test_tolerancia_no_parametrica_bilateral_la_confianza_declarada_se_cumple_en_simulacion():
    rng = np.random.default_rng(2)
    n, p = 80, 0.95
    declarada = pp.tolerance_interval(rng.normal(size=n), coverage=p, confidence=0.90, method="nonparametric",
                                      sides="two")
    muestras = rng.normal(size=(20_000, n))
    res = [pp.tolerance_interval(m, coverage=p, confidence=0.90, method="nonparametric", sides="two") for m in muestras[:4000]]
    cobertura = np.array([stats.norm.cdf(q.upper) - stats.norm.cdf(q.lower) for q in res])
    assert (cobertura >= p).mean() == pytest.approx(res[0].achieved_confidence, abs=0.025)
    assert declarada.achieved_confidence == pytest.approx(res[0].achieved_confidence)


def _cpm_a_mano(x, lsl, usl, target):
    s_t = math.sqrt(np.sum((x - target) ** 2) / (x.size - 1))
    if math.isclose(target, (lsl + usl) / 2):
        return (usl - lsl) / (6 * s_t)
    return min(target - lsl, usl - target) / (3 * s_t)


def test_cpm_con_objetivo_descentrado():
    x = np.random.default_rng(3).normal(10.6, 0.6, 60)
    r = pp.capability_analysis(x, lsl=8, usl=13, target=10)
    assert r.cpm == pytest.approx(_cpm_a_mano(x, 8, 13, 10), rel=1e-12)
    centrado = (13 - 8) / (6 * math.sqrt(x.var(ddof=1) + (x.mean() - 10) ** 2))
    assert r.cpm < centrado * 0.85  # la fórmula anterior daba un 25 % más


def test_cpm_con_objetivo_centrado_usa_el_factor_n_menos_1():
    x = np.random.default_rng(4).normal(10.4, 0.5, 40)
    r = pp.capability_analysis(x, lsl=8, usl=13, target=10.5)
    assert r.cpm == pytest.approx(_cpm_a_mano(x, 8, 13, 10.5), rel=1e-12)


def test_cpm_desde_estadisticos_resumen_coincide_con_el_de_los_datos():
    x = np.random.default_rng(5).normal(10.6, 0.6, 50)
    for target in (10.0, 10.5):
        datos = pp.capability_analysis(x, lsl=8, usl=13, target=target)
        resumen = pp.capability_analysis_summary(mean=x.mean(), std_overall=x.std(ddof=1), n=x.size, lsl=8, usl=13,
                                                 target=target)
        assert resumen.cpm == pytest.approx(datos.cpm, rel=1e-12)


def _gage_sin_interaccion(seed=11, p=10, o=3, r=2):
    rng = np.random.default_rng(seed)
    return (50 + rng.normal(0, 2, (p, 1, 1)) + rng.normal(0, 0.4, (1, o, 1)) + rng.normal(0, 0.5, (p, o, r)))


def _gage_modelo_reducido(d):
    p, o, r = d.shape
    gm = d.mean()
    pm, om, cm = d.mean(axis=(1, 2)), d.mean(axis=(0, 2)), d.mean(axis=2)
    ss_p, ss_o = o * r * np.sum((pm - gm) ** 2), p * r * np.sum((om - gm) ** 2)
    ss_int = r * np.sum((cm - pm[:, None] - om[None, :] + gm) ** 2)
    ss_err = np.sum((d - cm[:, :, None]) ** 2)
    df_int, df_err = (p - 1) * (o - 1), p * o * (r - 1)
    p_int = 1 - stats.f.cdf((ss_int / df_int) / (ss_err / df_err), df_int, df_err)
    ms_e = (ss_int + ss_err) / (df_int + df_err)
    var_o = max((ss_o / (o - 1) - ms_e) / (p * r), 0.0)
    var_p = max((ss_p / (p - 1) - ms_e) / (o * r), 0.0)
    return p_int, ms_e, var_o, var_p


def test_gage_rr_con_interaccion_no_significativa_usa_el_modelo_reducido():
    d = _gage_sin_interaccion()
    p_int, ms_e, var_o, var_p = _gage_modelo_reducido(d)
    assert p_int > 0.25  # el caso de prueba debe agrupar la interacción
    r = pp.gage_rr(d, 10, 3, 2)
    assert r.var_interaction == 0.0
    assert r.var_repeatability == pytest.approx(ms_e, rel=1e-12)
    assert r.var_operator == pytest.approx(var_o, rel=1e-12)
    assert r.var_part == pytest.approx(var_p, rel=1e-12)
    assert r.var_total == pytest.approx(ms_e + var_o + var_p, rel=1e-12)
    assert r.anova_reduced is not None and "Partes×Operadores" not in r.anova_reduced.index


def test_gage_rr_umbral_de_interaccion_configurable():
    d = _gage_sin_interaccion()
    por_defecto = pp.gage_rr(d, 10, 3, 2)
    sin_agrupar = pp.gage_rr(d, 10, 3, 2, alpha_interaction=1.0)
    assert sin_agrupar.var_interaction >= 0 and sin_agrupar.anova_reduced is None
    assert sin_agrupar.var_part != por_defecto.var_part


def test_gage_rr_cruzado_exige_al_menos_2_replicas():
    with pytest.raises(ValueError, match="replicates|réplicas"):
        pp.gage_rr(np.random.default_rng(0).normal(size=(10, 3, 1)), 10, 3, 1)


# ── Fase 2 ───────────────────────────────────────────────────────────────────


def _subgrupos_desiguales(seed=7):
    tamanos = [2, 2, 2, 10, 10, 2, 2, 9, 2, 2]
    rng = np.random.default_rng(seed)
    g = np.full((len(tamanos), 10), np.nan)
    for i, n in enumerate(tamanos):
        g[i, :n] = rng.normal(50, 2, n)
    return g, np.array(tamanos)


def test_sigma_rbar_con_subgrupos_desiguales_pondera_por_varianza_inversa():
    g, ns = _subgrupos_desiguales()
    rng = np.array([np.nanmax(f) - np.nanmin(f) for f in g])
    f = np.array([d2(n) ** 2 / d3(n) ** 2 for n in ns])
    esperado = np.sum(f * rng / np.array([d2(n) for n in ns])) / np.sum(f)
    from pccpy._sigma import sigma_subgroups
    assert sigma_subgroups(g, "rbar") == pytest.approx(esperado, rel=1e-12)


def test_sigma_sbar_con_subgrupos_desiguales_pondera_por_varianza_inversa():
    g, ns = _subgrupos_desiguales()
    s = np.array([np.nanstd(f, ddof=1) for f in g])
    h = np.array([c4(n) ** 2 / (1 - c4(n) ** 2) for n in ns])
    esperado = np.sum(h * s / np.array([c4(n) for n in ns])) / np.sum(h)
    from pccpy._sigma import sigma_subgroups
    assert sigma_subgroups(g, "sbar") == pytest.approx(esperado, rel=1e-12)


def test_sigma_con_tamano_constante_no_cambia():
    from pccpy._sigma import sigma_subgroups
    g = np.random.default_rng(8).normal(50, 2, (20, 5))
    rng = g.max(axis=1) - g.min(axis=1)
    assert sigma_subgroups(g, "rbar") == pytest.approx(np.mean(rng / d2(5)), rel=1e-12)
    assert sigma_subgroups(g, "sbar") == pytest.approx(np.mean(g.std(axis=1, ddof=1) / c4(5)), rel=1e-12)


def test_constantes_k_de_aiag_con_d2_estrella():
    from pccpy._constants import d2_star
    assert 1 / d2_star(3, 1) == pytest.approx(0.5231, abs=1e-3)   # K2 con 3 operadores
    assert 1 / d2_star(10, 1) == pytest.approx(0.3146, abs=1e-3)  # K3 con 10 partes
    assert 1 / d2_star(2, 1) == pytest.approx(0.7071, abs=1e-3)   # K2 con 2 operadores
    assert d2_star(5, 10**9) == pytest.approx(d2(5), rel=1e-6)    # con g grande tiende a d2


def test_gage_rr_xbar_r_sigue_aiag():
    from pccpy._constants import d2_star
    d = np.random.default_rng(9).normal(50, 2, (10, 3, 2)) + np.random.default_rng(10).normal(0, 3, (10, 1, 1))
    p, o, r = d.shape
    ev = (d.max(axis=2) - d.min(axis=2)).mean() / d2_star(r, p * o)
    om, pm = d.mean(axis=(0, 2)), d.mean(axis=(1, 2))
    av = math.sqrt(max((np.ptp(om) / d2_star(o, 1)) ** 2 - ev**2 / (p * r), 0.0))
    pv = np.ptp(pm) / d2_star(p, 1)
    res = pp.gage_rr(d, p, o, r, method="xbar_r")
    assert math.sqrt(res.var_repeatability) == pytest.approx(ev, rel=1e-9)
    assert math.sqrt(res.var_operator) == pytest.approx(av, rel=1e-9)
    assert math.sqrt(res.var_part) == pytest.approx(pv, rel=1e-9)


# ── Fase 3 ───────────────────────────────────────────────────────────────────


def test_el_panel_mr_solo_aplica_la_prueba_1():
    """Con 100 puntos estables y tests='all', las rachas del panel MR (autocorrelado y asimétrico) daban señales en ~45 %."""
    con_otras = 0
    for semilla in range(200):
        x = np.random.default_rng(semilla).normal(size=100)
        v = pp.imr_chart(x, tests="all")["MR"].violations
        con_otras += any(len(v.get(t, [])) for t in (2, 3, 4, 5, 6, 7, 8))
    assert con_otras == 0


def test_los_paneles_r_y_s_mantienen_las_pruebas_1_a_4():
    from pccpy import rules
    assert rules.FAMILIES["basic"] == (1, 2, 3, 4) and rules.FAMILIES["only1"] == (1,)
    g = np.random.default_rng(3).normal(size=(40, 5))
    for carta in (pp.xbar_r_chart(g, tests="all"), pp.xbar_s_chart(g, tests="all")):
        assert set(carta.panels[1].violations) <= {1, 2, 3, 4}
