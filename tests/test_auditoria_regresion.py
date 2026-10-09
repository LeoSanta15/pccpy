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


def test_un_hueco_en_imr_no_une_observaciones_no_consecutivas():
    x = np.random.default_rng(1).normal(50, 2, 30)
    x[2] = np.nan
    with pytest.warns(UserWarning, match="huecos"):
        c = pp.imr_chart(x)
    mr = c["MR"].values
    assert np.isnan(mr[[2, 3]]).all()
    validos = np.abs(np.diff(x))
    validos = validos[~np.isnan(validos)]  # no incluye |x[3] − x[1]|
    assert c.params[0]["sigma"] == pytest.approx(validos.mean() / d2(2), rel=1e-12)


def test_una_racha_no_cruza_un_hueco():
    from pccpy import rules
    valores = np.r_[np.full(5, 1.0), np.nan, np.full(5, 1.0)]
    marcados = rules.apply_tests(valores, np.zeros(11), np.ones(11), [2], {2: 9})
    assert marcados[2].size == 0  # 5 + 5 puntos del mismo lado, pero separados por un hueco: no son 9 seguidos
    sin_hueco = rules.apply_tests(np.full(11, 1.0), np.zeros(11), np.ones(11), [2], {2: 9})
    assert sin_hueco[2].size > 0


def _longitud_de_racha(carta):
    marcados = carta.panels[0].violations.get(1, [])
    return int(marcados[0]) + 1 if len(marcados) else None


def test_cusum_bilateral_arl0_con_sigma_conocida():
    """Hawkins y Olwell: la CUSUM tabular bilateral con h = 4 y k = 0,5 tiene ARL₀ ≈ 168 (≈ 336 por lado)."""
    rng = np.random.default_rng(21)
    rachas = [_longitud_de_racha(pp.cusum_chart(rng.normal(size=1500), target=0.0, sigma=1.0, h=4.0, k=0.5))
              for _ in range(300)]
    assert np.mean([r for r in rachas if r]) == pytest.approx(168, rel=0.15)


def test_ewma_arl0_con_sigma_conocida():
    """Lucas y Saccucci (1990): λ = 0,2 y L = 3 dan un ARL₀ de unos 550 con límites asintóticos; con los límites exactos
    que ensanchan al inicio, la simulación da ≈ 570."""
    rng = np.random.default_rng(22)
    rachas = [_longitud_de_racha(pp.ewma_chart(rng.normal(size=4000), weight=0.2, k=3.0, target=0.0, sigma=1.0))
              for _ in range(300)]
    assert 440 < np.mean([r for r in rachas if r]) < 650


def test_cusum_con_arranque_rapido_senala_antes_un_desplazamiento_inicial():
    rng = np.random.default_rng(23)
    x = rng.normal(size=60) + 1.0  # desplazamiento de 1 sigma desde el inicio
    sin = _longitud_de_racha(pp.cusum_chart(x, target=0.0, sigma=1.0))
    con = _longitud_de_racha(pp.cusum_chart(x, target=0.0, sigma=1.0, headstart=2.0))
    assert con is not None and (sin is None or con <= sin)
    primer = pp.cusum_chart(np.array([0.0, 0.0]), target=0.0, sigma=1.0, headstart=2.0)
    assert primer.panels[0].values[0] == pytest.approx(max(0.0, 2.0 + 0.0 - 0.5))  # S⁺₀ = headstart


def test_cusum_headstart_se_valida():
    with pytest.raises(ValueError, match="headstart"):
        pp.cusum_chart(np.arange(10.0), headstart=-1.0)
    with pytest.raises(ValueError, match="headstart"):
        pp.cusum_chart(np.arange(10.0), headstart=5.0, h=4.0)


@pytest.mark.parametrize("funcion", [pp.ewma_chart, pp.cusum_chart])
def test_ewma_y_cusum_con_etapas_calculan_limites_por_etapa(funcion):
    rng = np.random.default_rng(24)
    x = np.r_[rng.normal(10, 1, 40), rng.normal(20, 3, 40)]
    etapas = np.r_[np.ones(40), np.full(40, 2)]
    c = funcion(x, stages=etapas)
    assert [p["stage"] for p in c.params] == [1, 2]
    assert c.params[0]["objetivo"] == pytest.approx(10, abs=1) and c.params[1]["objetivo"] == pytest.approx(20, abs=2)
    assert c.params[1]["sigma"] > 2 * c.params[0]["sigma"]


def test_ewma_y_cusum_aceptan_sigma_method_con_subgrupos():
    from pccpy._sigma import sigma_subgroups
    g = np.random.default_rng(25).normal(50, 2, (30, 5))
    for funcion in (pp.ewma_chart, pp.cusum_chart):
        for metodo in ("rbar", "sbar", "pooled"):
            assert funcion(g, sigma_method=metodo).params[0]["sigma"] == pytest.approx(sigma_subgroups(g, metodo))
        with pytest.raises(ValueError, match="sigma_method"):
            funcion(g, sigma_method="mr")


def test_capability_boxcox_acepta_matrices_2d_como_dice_su_docstring():
    g = np.random.default_rng(1).lognormal(2, 0.3, (20, 4))
    a = pp.capability_boxcox(g, 5, 20)
    b = pp.capability_boxcox(g.ravel(), 5, 20, subgroup_size=4)
    c = pp.capability_analysis(g, 5, 20, transform="boxcox")
    assert a.cp == pytest.approx(b.cp, rel=1e-12) and a.cp == pytest.approx(c.cp, rel=1e-9)
    assert a.transform["lambda"] == pytest.approx(b.transform["lambda"])


# ── Fase 4 ───────────────────────────────────────────────────────────────────


def test_imr_avisa_cuando_sigma_es_cero():
    with pytest.warns(UserWarning, match="Sigma estimada = 0"):
        pp.imr_chart(np.full(10, 5.0))


@pytest.mark.parametrize("carta", [pp.p_chart, pp.np_chart, pp.laney_p_chart])
def test_cartas_p_np_y_laney_rechazan_tamanos_de_muestra_no_enteros(carta):
    defectuosos = np.array([2, 3, 1, 4, 2, 3, 2, 1])
    with pytest.raises(ValueError, match="enteros"):
        carta(defectuosos, np.full(8, 50.5))
    carta(defectuosos, np.full(8, 50.0))  # enteros representados como float: válidos


def test_u_chart_si_admite_areas_de_oportunidad_no_enteras():
    pp.u_chart(np.array([2, 3, 1, 4, 2, 3, 2, 1]), np.full(8, 2.5))


def test_ci_de_ppk_con_ppk_infinito_no_emite_runtimewarning():
    import warnings as w
    rng = np.random.default_rng(2)
    x = rng.lognormal(0, 0.3, 40)
    from pccpy.capability import _ci_ppk
    with w.catch_warnings():
        w.simplefilter("error")
        assert _ci_ppk(float("inf"), 40, 0.05) == (float("inf"), float("inf"))
        lo, hi = _ci_ppk(1.2, 40, 0.05)
    assert lo < 1.2 < hi
    with w.catch_warnings():
        w.simplefilter("error", RuntimeWarning)
        pp.capability_analysis(x, 0.0001, 1e9, transform="yeo-johnson")  # límite lejanísimo → índices muy grandes
