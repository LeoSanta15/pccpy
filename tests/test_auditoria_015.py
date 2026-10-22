"""Pruebas de la especificación 015: correcciones de la auditoría estadística de la 0.15.

Cada prueba cita su requisito (``S015-RF-nn``). Las referencias son independientes de pccpy: recursiones y fórmulas
escritas aparte en el propio test, ``scipy.stats``, ``statsmodels`` (cuando está instalado) y simulaciones con varias semillas.
"""
import math
import warnings
from pathlib import Path

import numpy as np
import pytest
from scipy import optimize, stats

import pccpy as pp
from pccpy._constants import c4, d2

RAIZ = Path(__file__).resolve().parents[1]


# ── S015-RF-01: EWMA-P/U con n variable ──────────────────────────────────────

def _sigma_ewma_exacta(n, p, lam):
    s2 = p * (1 - p) / n
    v, out = 0.0, []
    for s in s2:
        v = (1 - lam) ** 2 * v + lam**2 * s
        out.append(math.sqrt(v))
    return np.array(out)


def test_s015_rf01_sigma_ewma_p_con_n_variable():
    """S015-RF-01: ``panel.sigma`` sigue la recursión Vᵢ = (1−λ)²Vᵢ₋₁ + λ²σ²(nᵢ)."""
    n = np.where(np.arange(60) % 2 == 0, 30, 600)
    ch = pp.ewma_p_chart(np.full(60, 3), n, p=0.1)
    np.testing.assert_allclose(ch.panels[0].sigma, _sigma_ewma_exacta(n, 0.1, 0.2), rtol=1e-12)


def test_s015_rf01_falsas_alarmas_ewma_p_con_n_variable():
    """S015-RF-01: con n alternando 30 y 600 la tasa de falsas alarmas por punto es ≈ 0,0027 (hoy 0,15)."""
    n = np.where(np.arange(60) % 2 == 0, 30, 600)
    fuera = []
    for semilla in range(20):
        rng = np.random.default_rng(semilla)
        for _ in range(50):
            pan = pp.ewma_p_chart(rng.binomial(n, 0.1), n, p=0.1).panels[0]
            fuera.append(((pan.values > pan.ucl) | (pan.values < pan.lcl))[30:].mean())
    assert np.mean(fuera) < 0.008


def test_s015_rf01_n_constante_no_cambia():
    """S015-RF-01: con n constante los límites son los de la fórmula cerrada de Montgomery."""
    lam, p, n = 0.2, 0.1, 50
    ch = pp.ewma_p_chart(np.full(25, 5), np.full(25, n), p=p, weight=lam)
    i = np.arange(1, 26)
    cerrada = math.sqrt(p * (1 - p) / n) * np.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * i)))
    np.testing.assert_allclose(ch.panels[0].sigma, cerrada, rtol=1e-12)


# ── S015-RF-02: Dodge-Romig ─────────────────────────────────────────────────

def _pa(n, c, p):
    return stats.binom.cdf(c, n, p)


def _aoql_exacto(n, c, N):
    """Máximo de Pa(p)·p·(N−n)/N: rejilla gruesa y refinamiento local (escrito aparte de pccpy)."""
    ps = np.linspace(1e-6, 0.6, 3001)
    v = _pa(n, c, ps) * ps * (N - n) / N
    i = int(v.argmax())
    lo, hi = ps[max(i - 1, 0)], ps[min(i + 1, len(ps) - 1)]
    r = optimize.minimize_scalar(lambda p: -_pa(n, c, p) * p * (N - n) / N, bounds=(lo, hi), method="bounded",
                                 options={"xatol": 1e-12})
    return max(-r.fun, v.max())


def _optimo(N, cumple, p_medio):
    """Búsqueda exhaustiva: para cada c el menor n que cumple el criterio y, entre ellos, el menor ATI."""
    mejores = []
    for c in range(20):
        for n in range(c + 1, N + 1):
            if cumple(n, c):
                mejores.append((n + (1 - _pa(n, c, p_medio)) * (N - n), n, c))
                break
    return min(mejores)


def test_s015_rf02_dodge_romig_ltpd_minimiza_el_ati_correcto():
    """S015-RF-02: ATI = n + (1−Pa)(N−n); el plan es el de la búsqueda exhaustiva (n=132, c=3; hoy n=45, c=0)."""
    N, ltpd, pbar = 1000, 0.05, 0.01
    _, n_ref, c_ref = _optimo(N, lambda n, c: _pa(n, c, ltpd) <= 0.10, pbar)
    plan = pp.dodge_romig(N, ltpd=ltpd, process_avg=pbar)
    assert (plan.n, plan.c) == (n_ref, c_ref) == (132, 3)


def test_s015_rf02_dodge_romig_aoql_cumple_el_objetivo_y_es_optimo():
    """S015-RF-02: el AOQL real es ≤ objetivo (sin holgura del 5 %) y el plan es el de menor ATI."""
    N, objetivo, pbar = 5000, 0.02, 0.01

    def cumple(n, c):
        return _aoql_exacto(n, c, N) <= objetivo

    mejores = []
    for c in range(20):
        lo, hi = c + 1, N
        if not cumple(hi, c):
            continue
        while lo < hi:  # el AOQL decrece con n: bisección
            mid = (lo + hi) // 2
            if cumple(mid, c):
                hi = mid
            else:
                lo = mid + 1
        mejores.append((lo + (1 - _pa(lo, c, pbar)) * (N - lo), lo, c))
    _, n_ref, c_ref = min(mejores)
    plan = pp.dodge_romig(N, aoql=objetivo, process_avg=pbar)
    assert _aoql_exacto(plan.n, plan.c, N) <= objetivo
    assert (plan.n, plan.c) == (n_ref, c_ref)


def test_s015_rf02_aoql_z14_es_el_maximo_exacto():
    """S015-RF-02: el AOQL de Z1.4 es el máximo exacto de la curva AOQ (0,000287; hoy 0,000255 por la rejilla)."""
    plan = pp.acceptance_sampling_attributes(50000, 0.01)
    assert plan.aoq_max == pytest.approx(_aoql_exacto(plan.n, plan.c, 50000), rel=1e-4)
    assert plan.aoq_max == pytest.approx(0.000287, abs=1e-6)


# ── S015-RF-03: carta de corridas con empates ────────────────────────────────

def test_s015_rf03_tendencias_con_empates_calibradas():
    """S015-RF-03: con datos redondeados (n=30) P(p_trends < 0,05) ≤ 0,07 (hoy 0,38)."""
    tasas = []
    for semilla in range(20):
        rng = np.random.default_rng(semilla)
        tasas.append(np.mean([pp.run_chart(np.round(rng.normal(size=30))).p_trends < 0.05 for _ in range(200)]))
    assert np.mean(tasas) <= 0.07


def test_s015_rf03_sin_empates_no_cambia():
    """S015-RF-03: sin empates E=(2n−1)/3 y V=(16n−29)/90 con la n original."""
    x = np.random.default_rng(5).normal(size=40)
    d = np.sign(np.diff(x))
    r = 1 + np.sum(d[1:] != d[:-1])
    z = (r - (2 * 40 - 1) / 3) / math.sqrt((16 * 40 - 29) / 90)
    assert pp.run_chart(x).p_trends == pytest.approx(stats.norm.cdf(z), rel=1e-12)


def test_s015_rf03_con_empates_usa_m_mas_uno():
    """S015-RF-03: con empates, n pasa a ser m+1 (m = diferencias no nulas)."""
    x = np.array([1, 2, 2, 3, 1, 1, 4, 2, 5, 5, 3, 6, 2, 2, 7], dtype=float)
    d = np.sign(np.diff(x))
    d = d[d != 0]
    n = len(d) + 1
    r = 1 + np.sum(d[1:] != d[:-1])
    z = (r - (2 * n - 1) / 3) / math.sqrt((16 * n - 29) / 90)
    assert pp.run_chart(x).p_trends == pytest.approx(stats.norm.cdf(z), rel=1e-12)


# ── S015-RF-04: tendencia de diagnose() y wizard() ───────────────────────────

def _tendencia_en_diagnose(n, deriva_total, semillas=20, por_semilla=40):
    cuenta = 0
    total = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for s in range(semillas):
            rng = np.random.default_rng(s)
            for _ in range(por_semilla):
                x = rng.normal(size=n) + deriva_total * np.arange(n) / (n - 1)
                cuenta += bool(pp.diagnose(x).has_trend)
                total += 1
    return cuenta / total


@pytest.mark.parametrize("n", [20, 50])
def test_s015_rf04_detecta_una_deriva_de_3_sigma(n):
    """S015-RF-04: una deriva total de 3σ se detecta en ≥ 90 % de los casos (hoy 0 %)."""
    assert _tendencia_en_diagnose(n, 3.0) >= 0.9


@pytest.mark.parametrize("n", [20, 50, 100])
def test_s015_rf04_falsas_alarmas_cerca_de_5_por_ciento(n):
    """S015-RF-04: con datos iid la tasa de falsas alarmas es ≤ 7 %."""
    assert _tendencia_en_diagnose(n, 0.0) <= 0.07


def test_s015_rf04_direccion_de_la_tendencia():
    x = np.arange(30, dtype=float) + np.random.default_rng(0).normal(0, 0.5, 30)
    assert pp.diagnose(x).trend_direction == "increasing"
    assert pp.diagnose(-x).trend_direction == "decreasing"


def test_s015_rf04_no_evalua_la_tendencia_con_menos_de_8_observaciones():
    """S015-RF-04: con n < 8 no se evalúa la tendencia (hoy una serie creciente de 6 puntos la marca)."""
    assert not pp.diagnose(np.arange(6, dtype=float)).has_trend


@pytest.mark.parametrize("n", [2, 3, 5])
def test_s015_rf04_wizard_no_recomienda_run_chart_por_tendencia_con_n_pequeno(n):
    """S015-RF-04: con n pequeño una serie monótona no hace que ``wizard`` recomiende ``run_chart``."""
    assert pp.wizard(np.arange(n, dtype=float)).function != "run_chart"


def test_s015_rf04_wizard_detecta_tendencia_real():
    x = np.arange(30, dtype=float) + np.random.default_rng(1).normal(0, 0.5, 30)
    assert pp.wizard(x).function == "run_chart"


# ── S015-RF-05: p-valor del kappa de Cohen ───────────────────────────────────

def _kappa_fce(tabla):
    """Kappa y error estándar bajo H0 de Fleiss, Cohen y Everitt (1969), escritos aparte."""
    tabla = np.asarray(tabla, float)
    n = tabla.sum()
    p = tabla / n
    fila, col = p.sum(1), p.sum(0)
    po, pe = np.trace(p), float(fila @ col)
    kappa = (po - pe) / (1 - pe)
    var0 = (pe + pe**2 - float(np.sum(fila * col * (fila + col)))) / (n * (1 - pe) ** 2)
    return kappa, math.sqrt(var0)


def _tabla(a, b, cats):
    return np.array([[np.sum((a == i) & (b == j)) for j in cats] for i in cats])


def test_s015_rf05_error_estandar_de_fleiss_cohen_everitt():
    """S015-RF-05: el p-valor usa el error estándar de FCE (1969); el kappa no cambia."""
    from pccpy.msa import _cohen_kappa

    rng = np.random.default_rng(1)
    cats = [0, 1, 2]
    for _ in range(3):
        a = rng.choice(cats, 60, p=[0.7, 0.2, 0.1])
        b = np.where(rng.random(60) < 0.6, a, rng.choice(cats, 60, p=[0.3, 0.3, 0.4]))
        k_ref, se0 = _kappa_fce(_tabla(a, b, cats))
        k, p, _ = _cohen_kappa(a, b, cats)
        assert k == pytest.approx(k_ref, rel=1e-12)
        assert p == pytest.approx(stats.norm.sf(k_ref / se0), rel=1e-9)   # unilateral desde la 019 (S019-RF-02)


def test_s015_rf05_coincide_con_statsmodels():
    """S015-RF-05: el error estándar coincide con ``statsmodels`` (``std_kappa0``)."""
    sm = pytest.importorskip("statsmodels.stats.inter_rater")
    from pccpy.msa import _cohen_kappa

    rng = np.random.default_rng(4)
    cats = [0, 1, 2]
    a = rng.choice(cats, 80, p=[0.6, 0.3, 0.1])
    b = np.where(rng.random(80) < 0.5, a, rng.choice(cats, 80))
    r = sm.cohens_kappa(_tabla(a, b, cats))
    _, p, _ = _cohen_kappa(a, b, cats)
    assert p == pytest.approx(stats.norm.sf(r.kappa / r.std_kappa0), rel=1e-6)   # unilateral desde la 019 (S019-RF-02)


def test_s015_rf05_tasa_de_rechazo_bajo_h0():
    """S015-RF-05: con marginales 85/15 y n=100 la tasa de rechazo al 5 % es 0,05 ± 0,01 (hoy 0,0013)."""
    from pccpy.msa import _cohen_kappa

    cats = [0, 1]
    tasas = []
    for semilla in range(20):
        rng = np.random.default_rng(100 + semilla)
        rech = 0
        for _ in range(300):
            a = rng.choice(cats, 100, p=[0.85, 0.15])
            b = rng.choice(cats, 100, p=[0.85, 0.15])
            p = _cohen_kappa(a, b, cats)[1]
            rech += (p < 0.025) or (p > 0.975)   # prueba bilateral al 5 % a partir del p unilateral (S019-RF-02)
        tasas.append(rech / 300)
    assert np.mean(tasas) == pytest.approx(0.05, abs=0.01)


# ── S015-RF-06 y RF-07: capacidad con huecos ─────────────────────────────────

def test_s015_rf06_capability_boxcox_conserva_el_hueco():
    """S015-RF-06: ``capability_boxcox`` agrupa como ``capability_analysis(transform="boxcox")``."""
    rng = np.random.default_rng(2)
    g = rng.lognormal(0, 0.1, (10, 5)) * np.repeat(rng.uniform(1, 3, 10)[:, None], 5, axis=1)
    x = g.ravel().copy()
    x[2] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = pp.capability_analysis(x, 0.5, 6, subgroup_size=5, transform="boxcox")
        b = pp.capability_boxcox(x, 0.5, 6, subgroup_size=5)
    lam = b.transform["lambda"]
    z = (g**lam - 1) / lam
    z.ravel()[2] = np.nan
    n_i = np.sum(~np.isnan(z), axis=1)
    s_i = np.nanstd(z, axis=1, ddof=1)
    gl = np.sum(n_i - 1)
    ref = math.sqrt(np.sum((n_i - 1) * s_i**2) / gl) / c4(int(gl) + 1)
    assert b.sigma_within == pytest.approx(ref, rel=1e-9)
    assert b.sigma_within == pytest.approx(a.sigma_within, rel=1e-9)


def test_s015_rf07_individuales_con_hueco_no_cruzan_el_hueco():
    """S015-RF-07: σ_within = nanmean(|diff|)/d2(2) = 0,6077 y coincide con I-MR (hoy 0,9527)."""
    y = np.array([10, 10.2, np.nan, 14, 14.1, 13.9, 10.1, 10, 9.9, 10.2])
    ref = np.nanmean(np.abs(np.diff(y))) / d2(2)
    assert ref == pytest.approx(0.6077, abs=1e-4)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = pp.capability_analysis(y, 5, 20)
        ch = pp.imr_chart(y)
    assert r.sigma_within == pytest.approx(ref, rel=1e-9)
    assert r.sigma_within == pytest.approx(ch.params[0]["sigma"], rel=1e-9)


# ── S015-RF-08: último subgrupo incompleto ───────────────────────────────────

def test_s015_rf08_cusum_ultimo_subgrupo_incompleto():
    """S015-RF-08: el punto del último subgrupo (1 observación) tiene σ = 1,0 (hoy 0,447)."""
    x = np.random.default_rng(0).normal(size=101)
    ch = pp.cusum_chart(x, subgroup_size=5, sigma=1, target=0)
    assert ch.panels[0].sigma[-1] == pytest.approx(1.0)


def test_s015_rf08_ewma_ultimo_subgrupo_incompleto():
    """S015-RF-08: la σ del estadístico EWMA sigue la recursión con σ²/nᵢ (21 subgrupos: 20 de 5 y uno de 1)."""
    x = np.random.default_rng(0).normal(size=101)
    s = pp.ewma_chart(x, subgroup_size=5, sigma=1, target=0).panels[0].sigma
    var_i = np.r_[np.full(20, 1 / 5), 1.0]
    v, ref = 0.0, []
    for vi in var_i:
        v = 0.8**2 * v + 0.2**2 * vi
        ref.append(math.sqrt(v))
    np.testing.assert_allclose(s, ref, rtol=1e-12)


def test_s015_rf08_ma_ultimo_subgrupo_incompleto():
    """S015-RF-08: en MA la σ del último punto es mayor que la del anterior (menos observaciones)."""
    x = np.random.default_rng(0).normal(size=101)
    s = pp.ma_chart(x, subgroup_size=5, sigma=1, mu=0).panels[0].sigma
    assert s[-1] > s[-2]


def test_s015_rf08_subgrupos_completos_no_cambian():
    x = np.random.default_rng(0).normal(size=100)
    s = pp.cusum_chart(x, subgroup_size=5, sigma=1, target=0).panels[0].sigma
    np.testing.assert_allclose(s, 1 / math.sqrt(5))


# ── S015-RF-09: phase_one con center="median" ────────────────────────────────

def test_s015_rf09_phase2_con_center_median_imr():
    """S015-RF-09: ``phase2()`` usa el centro congelado y no vuelve a pasar ``center`` (hoy ``ValueError``)."""
    x = np.random.default_rng(0).normal(100, 2, 40)
    r = pp.phase_one(pp.imr_chart, x, center="median")
    ch = r.phase2(np.random.default_rng(1).normal(100, 2, 20))
    assert ch.panels[0].center[0] == pytest.approx(r.limits["mu"])


def test_s015_rf09_phase2_con_center_median_xbar():
    g = np.random.default_rng(0).normal(100, 2, (30, 5))
    r = pp.phase_one(pp.xbar_r_chart, g, center="median")
    ch = r.phase2(np.random.default_rng(1).normal(100, 2, (10, 5)))
    assert ch.panels[0].center[0] == pytest.approx(r.limits["mu"])


def test_s015_rf09_from_limits_con_center_median():
    r = pp.PhaseOneResult.from_limits(pp.imr_chart, mu=100, sigma=2, center="median")
    ch = r.phase2(np.random.default_rng(1).normal(100, 2, 20))
    assert ch.panels[0].center[0] == pytest.approx(100.0)


# ── S015-RF-10 y RF-11: Gage R&R y linealidad ────────────────────────────────

def test_s015_rf10_gage_rr_tolerancia():
    """S015-RF-10: ``tolerance=`` produce %Tolerancia = 100·6σ/T (hoy sin efecto)."""
    d = np.random.default_rng(0).normal(0, 1, 60)
    g = pp.gage_rr(d, 10, 3, 2, tolerance=20.0)
    assert g.pct_tolerance_gage == pytest.approx(100 * 6 * math.sqrt(g.var_gage) / 20.0, rel=1e-12)
    assert g.pct_tolerance_repeatability == pytest.approx(100 * 6 * math.sqrt(g.var_repeatability) / 20.0, rel=1e-12)
    assert g.pct_tolerance_reproducibility == pytest.approx(100 * 6 * math.sqrt(g.var_reproducibility) / 20.0, rel=1e-12)
    assert "pct_tolerance_gage" in g.to_frame(stable=True).to_string()
    assert g.summary() != pp.gage_rr(d, 10, 3, 2).summary()


def test_s015_rf10_sin_tolerancia_no_aparece():
    d = np.random.default_rng(0).normal(0, 1, 60)
    g = pp.gage_rr(d, 10, 3, 2)
    assert "pct_tolerance_gage" not in g.to_frame(stable=True).to_string()


def _datos_linealidad(seed=3):
    rng = np.random.default_rng(seed)
    refs = np.repeat([2.0, 4.0, 6.0, 8.0, 10.0], 12)
    return refs + 0.7 - 0.117 * refs + rng.normal(0, 0.2, 60), refs


def test_s015_rf11_porcentaje_de_linealidad_aiag():
    """S015-RF-11: %Linealidad = 100·|pendiente| (AIAG); hoy se divide por 6·s_residual (84,3 %)."""
    m, refs = _datos_linealidad()
    lin = pp.gage_linearity(m, refs)
    assert lin.linearity_pct == pytest.approx(100 * abs(lin.slope), rel=1e-12)
    assert lin.linearity_pct < 20


def test_s015_rf11_porcentaje_de_sesgo_con_variacion_del_proceso():
    """S015-RF-11: %Sesgo = 100·|sesgo medio| / variación del proceso."""
    m, refs = _datos_linealidad()
    lin = pp.gage_linearity(m, refs, process_variation=12.0)
    assert lin.avg_bias_pct == pytest.approx(100 * abs(lin.avg_bias) / 12.0, rel=1e-12)


# ── S015-RF-12: límites de |S| ───────────────────────────────────────────────

@pytest.mark.parametrize("p,n", [(2, 5), (3, 6)])
def test_s015_rf12_limite_superior_de_s_por_percentiles(p, n):
    """S015-RF-12: P(|S| > LCS) = 0,00135 ± 5 % (hoy 0,0197). Referencia: |S| = Π χ²_{n−i}/(n−1)^p (Bartlett)."""
    ch = pp.generalized_variance_chart(np.random.default_rng(0).normal(size=(20 * n, p)), subgroup_size=n,
                                       cov=np.eye(p), k=3)
    ucl = ch["|S|"].ucl[0]
    rng = np.random.default_rng(7)
    det = np.ones(4_000_000)
    for i in range(1, p + 1):
        det *= rng.chisquare(n - i, size=det.size)
    det /= (n - 1) ** p
    assert (det > ucl).mean() == pytest.approx(0.00135, rel=0.05)


# ── S015-RF-13: casos borde ──────────────────────────────────────────────────

def test_s015_rf13_prueba_1_con_sigma_cero():
    """S015-RF-13: un punto fuera de límites degenerados (σ = 0) se marca."""
    ch = pp.imr_chart([5.0] * 7 + [9.0, 5.0, 5.0], sigma=0.0)
    assert 7 in ch.panels[0].violations[1]


def test_s015_rf13_precontrol_con_nan():
    """S015-RF-13: un NaN no es «verde»: se excluye con aviso (R-09)."""
    with pytest.warns(UserWarning):
        r = pp.precontrol([10, np.nan, 10], 0, 20)
    assert len(r.zones) == 2


def test_s015_rf13_gage_rr_con_nan():
    d = np.random.default_rng(0).normal(0, 1, 60)
    d[5] = np.nan
    with pytest.raises(ValueError):
        pp.gage_rr(d, 10, 3, 2)


def test_s015_rf13_gage_rr_con_un_operador():
    with pytest.raises(ValueError):
        pp.gage_rr(np.random.default_rng(0).normal(0, 1, 20), 10, 1, 2)


def test_s015_rf13_ltpd_de_plan_a_medida():
    """S015-RF-13: ``ltpd`` no sale NaN si Pa(AQL) < 0,10 (n=200, c=5, AQL=10 %)."""
    plan = pp.acceptance_sampling_attributes(1000, 10.0, n=200, c=5)
    ref = optimize.brentq(lambda p: stats.binom.cdf(5, 200, p) - 0.10, 1e-9, 0.999)
    assert not math.isnan(plan.ltpd)
    assert plan.ltpd == pytest.approx(ref, rel=1e-6)
    assert plan.ltpd == pytest.approx(0.0459, abs=1e-4)


def test_s015_rf13_p_chart_valida_p():
    with pytest.raises(ValueError):
        pp.p_chart([1, 2, 3], [10, 10, 10], p=1.5)


# ── S015-RF-14: estimadores y aproximaciones ─────────────────────────────────

def test_s015_rf14_mssd_insesgado():
    """S015-RF-14: E[σ̂]/σ = 1,000 ± 0,003 con n = 10 en 20 semillas (hoy 0,962)."""
    razones = []
    for semilla in range(20):
        x = np.random.default_rng(semilla).normal(0, 1, (20000, 10))
        d = np.diff(x, axis=1)
        razones.append(np.mean(np.sqrt(np.sum(d**2, axis=1) / (2 * 9))))
    # la referencia del propio test fija el sesgo sin corregir; pccpy debe devolver el estimador corregido
    sesgo_sin_corregir = np.mean(razones)
    assert sesgo_sin_corregir < 0.97
    est = []
    for semilla in range(20):
        x = np.random.default_rng(semilla).normal(0, 1, (400, 10))
        est.append(np.mean([pp.imr_chart(f, sigma_method="mssd").params[0]["sigma"] for f in x]))
    assert np.mean(est) == pytest.approx(1.0, abs=0.003)


@pytest.mark.parametrize("n", [2, 3, 10, 30])
def test_s015_rf14_constante_c_mssd_contra_monte_carlo(n):
    """S015-RF-14: ``c_mssd(n)`` = E[√(MSSD/2)]/σ por integración numérica; contraste con Monte Carlo (20 semillas)."""
    from pccpy._constants import c_mssd

    valores = []
    for semilla in range(20):
        d = np.diff(np.random.default_rng(semilla).normal(size=(20000, n)), axis=1)
        valores.append(np.mean(np.sqrt(np.sum(d**2, axis=1) / (2 * (n - 1)))))
    assert c_mssd(n) == pytest.approx(np.mean(valores), abs=0.002)
    assert c_mssd(2) == pytest.approx(math.sqrt(2 / math.pi), rel=1e-9)


def test_s015_rf14_curva_oc_variables_bilateral():
    """S015-RF-14: Pa bilateral (n=20, k=1,5, p=0,10) coincide con Monte Carlo (0,495; hoy 0,451)."""
    from pccpy.acceptance import _pa_variables

    n, k, p = 20, 1.5, 0.10
    z = stats.norm.isf(p / 2)
    pa = []
    for semilla in range(20):
        X = np.random.default_rng(semilla).normal(0, 1, (20000, n))
        m, s = X.mean(1), X.std(1, ddof=1)
        pa.append(np.mean(((z - m) / s >= k) & ((m + z) / s >= k)))
    assert _pa_variables(n, k, p, "two") == pytest.approx(np.mean(pa), abs=0.01)


def test_s015_rf14_diagnose_no_afirma_investigar_solo_por_el_iqr():
    """S015-RF-14: con n grande la regla del IQR da «posibles atípicos», no «investiga su origen»."""
    x = np.random.default_rng(3).normal(size=500)
    r = pp.diagnose(x)
    assert r.outlier_count > 0
    assert "Investiga su origen" not in "\n".join(r.issues)


# ── S015-RF-15: documentación ────────────────────────────────────────────────

def test_s015_rf15_seccion_de_diferencias_con_minitab_en_los_readme():
    """S015-RF-15: los README tienen la sección de diferencias posibles con Minitab (R-02)."""
    assert "Notas sobre diferencias posibles con Minitab" in (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "Notes on possible differences with Minitab" in (RAIZ / "README_en.md").read_text(encoding="utf-8")


def test_s015_rf15_comentario_de_normalidad_de_diagnose():
    """S015-RF-15: el comentario de normalidad de ``diagnose`` no cita Anderson-Darling (usa D'Agostino K²)."""
    fuente = (RAIZ / "src/pccpy/_diagnose.py").read_text(encoding="utf-8")
    assert "Anderson-Darling vía scipy" not in fuente


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7])
def test_s015_rf15_wizard_con_n_pequeno_no_avisa(n):
    """S015-RF-15: ``wizard`` con 3 ≤ n ≤ 7 sin tendencia no llama a ``normaltest`` (sin avisos ni error)."""
    x = np.array([1.0, 3.0, 2.0, 4.0, 1.5, 3.5, 2.5][:n])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pp.wizard(x)
