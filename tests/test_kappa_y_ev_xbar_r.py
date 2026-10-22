"""Pruebas de la especificación 019: kappa indefinido y p-valor unilateral; EV del Gage R&R Xbar-R con `d2`.

Referencias escritas aparte: la definición del kappa (`κ = (pₒ − pₑ)/(1 − pₑ)`), el error estándar de Fleiss, Cohen y
Everitt (1969), `statsmodels` (`std_kappa0`, cuando está instalado), `d2(2) = 2/√π`, `d2(3)` por integración numérica de la
media del rango de variables normales, y simulaciones con 20 semillas. Nunca la salida anterior de pccpy.
"""
import math
import warnings

import numpy as np
import pandas as pd
import pytest
from scipy import stats
from scipy.integrate import quad

import pccpy as pp
from pccpy.msa import _cohen_kappa, _fleiss_kappa


# ── referencias independientes ────────────────────────────────────────────────────────────────────────────────────────
def _tabla(a, b, cats):
    return np.array([[np.sum((a == i) & (b == j)) for j in cats] for i in cats], dtype=float)


def _kappa_fce(tabla):
    """Kappa y error estándar bajo H0 de Fleiss, Cohen y Everitt (1969)."""
    n = tabla.sum()
    p = tabla / n
    fila, col = p.sum(1), p.sum(0)
    po, pe = np.trace(p), float(fila @ col)
    kappa = (po - pe) / (1 - pe)
    var0 = (pe + pe**2 - float(np.sum(fila * col * (fila + col)))) / (n * (1 - pe) ** 2)
    return kappa, math.sqrt(var0)


def _d2_referencia(m: int) -> float:
    """Media del rango de m variables N(0, 1): ∫ [1 − Φ(x)^m − (1 − Φ(x))^m] dx."""
    return quad(lambda x: 1.0 - stats.norm.cdf(x) ** m - stats.norm.sf(x) ** m, -np.inf, np.inf, epsabs=1e-13)[0]


# ── S019-RF-01: kappa indefinido si pe = 1 ───────────────────────────────────────────────────────────────────────────
def test_s019_rf01_cohen_con_una_sola_categoria_es_nan():
    """S019-RF-01: dos evaluadores que usan una sola categoría → κ y p son nan (0/0) y el acuerdo es 100 %."""
    kappa, p, pct = _cohen_kappa(np.zeros(10, int), np.zeros(10, int), [0, 1])
    assert math.isnan(kappa) and math.isnan(p)
    assert pct == 100.0


def test_s019_rf01_fleiss_con_una_sola_categoria_es_nan():
    """S019-RF-01: Fleiss con `Pe = 1` (todos los evaluadores eligen la misma categoría) es nan, no 1,0."""
    ratings = pd.DataFrame(np.zeros((8, 3), int))
    assert math.isnan(_fleiss_kappa(ratings, [0, 1]))


def test_s019_rf01_cohen_con_pe_menor_que_uno_no_cambia():
    """S019-RF-01 (guarda: pasa antes del código): con `pe < 1` el kappa es el de la definición."""
    rng = np.random.default_rng(3)
    a = rng.choice([0, 1], 50, p=[0.7, 0.3])
    b = np.where(rng.random(50) < 0.7, a, 1 - a)
    esperado, _ = _kappa_fce(_tabla(a, b, [0, 1]))
    assert _cohen_kappa(a, b, [0, 1])[0] == pytest.approx(esperado, rel=1e-12)


def _datos_con_un_operador_constante() -> pd.DataFrame:
    """20 piezas × 2 réplicas: el operador A dice siempre «ok»; B y C mezclan «ok» y «mal»."""
    rng = np.random.default_rng(7)
    ref = rng.choice(["ok", "mal"], 20, p=[0.6, 0.4])
    b = np.where(rng.random(40) < 0.85, np.repeat(ref, 2), np.where(np.repeat(ref, 2) == "ok", "mal", "ok"))
    c = np.where(rng.random(40) < 0.8, np.repeat(ref, 2), np.where(np.repeat(ref, 2) == "ok", "mal", "ok"))
    return pd.DataFrame({"A": ["ok"] * 40, "B": b, "C": c}), ref


def test_s019_rf01_operador_constante_en_attribute_agreement():
    """S019-RF-01: el operador que siempre dice «ok» tiene κ y p nan en la repetibilidad (acuerdo 100 %); B y C no cambian."""
    df, ref = _datos_con_un_operador_constante()
    res = pp.attribute_agreement(df, reference=ref, replicates=2)
    fila = res.kappa_within.loc["A"]
    assert math.isnan(fila["kappa"]) and math.isnan(fila["p_valor"])
    assert fila["% acuerdo"] == 100.0
    assert res.kappa_within.loc[["B", "C"], "kappa"].notna().all()


def test_s019_rf01_summary_to_frame_y_excel_no_lanzan_con_nan(tmp_path):
    """S019-RF-01: `summary()`, `to_frame()`, `kappa_within_frame()` y `to_excel()` muestran nan sin lanzar."""
    df, ref = _datos_con_un_operador_constante()
    res = pp.attribute_agreement(df, reference=ref, replicates=2)
    assert res.summary()
    assert res.to_frame(stable=True).shape[0] > 0
    assert math.isnan(res.kappa_within_frame(stable=True).loc["A", "kappa"])
    pytest.importorskip("openpyxl")
    res.to_excel(tmp_path / "kappa.xlsx")
    assert (tmp_path / "kappa.xlsx").exists()


def test_s019_rf01_todos_los_evaluadores_con_una_categoria():
    """S019-RF-01: si todo el estudio es «ok», Fleiss y el kappa de cada operador son nan y no hay excepción."""
    df = pd.DataFrame({"A": ["ok"] * 20, "B": ["ok"] * 20})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = pp.attribute_agreement(df, replicates=2)
    assert math.isnan(res.fleiss_kappa)
    assert res.kappa_within["kappa"].isna().all()
    assert "nan" in res.summary().lower()


# ── S019-RF-02: p-valor unilateral ───────────────────────────────────────────────────────────────────────────────────
def test_s019_rf02_p_unilateral_con_el_error_estandar_de_fce():
    """S019-RF-02: `p = norm.sf(κ/SE₀)` con el error estándar de FCE (1969); el kappa no cambia."""
    rng = np.random.default_rng(1)
    cats = [0, 1, 2]
    for _ in range(3):
        a = rng.choice(cats, 60, p=[0.7, 0.2, 0.1])
        b = np.where(rng.random(60) < 0.6, a, rng.choice(cats, 60, p=[0.3, 0.3, 0.4]))
        k_ref, se0 = _kappa_fce(_tabla(a, b, cats))
        k, p, _ = _cohen_kappa(a, b, cats)
        assert k == pytest.approx(k_ref, rel=1e-12)
        assert p == pytest.approx(stats.norm.sf(k_ref / se0), rel=1e-9)


def test_s019_rf02_coincide_con_statsmodels():
    """S019-RF-02: `p = norm.sf(κ/std_kappa0)` con el `std_kappa0` de statsmodels."""
    sm = pytest.importorskip("statsmodels.stats.inter_rater")
    rng = np.random.default_rng(4)
    cats = [0, 1, 2]
    a = rng.choice(cats, 80, p=[0.6, 0.3, 0.1])
    b = np.where(rng.random(80) < 0.5, a, rng.choice(cats, 80))
    r = sm.cohens_kappa(_tabla(a, b, cats))
    assert _cohen_kappa(a, b, cats)[1] == pytest.approx(stats.norm.sf(r.kappa / r.std_kappa0), rel=1e-6)


def test_s019_rf02_kappa_negativo_no_es_significativo():
    """S019-RF-02: con κ < 0 (desacuerdo sistemático) `p > 0,5`."""
    a = np.array([0, 1] * 20)
    b = 1 - a
    kappa, p, _ = _cohen_kappa(a, b, [0, 1])
    assert kappa < 0
    assert p > 0.5


def test_s019_rf02_kappa_cero_da_p_un_medio():
    """S019-RF-02: con κ = 0 exacto (tabla 25/25/25/25) `p = 0,5`."""
    a = np.array([0] * 50 + [1] * 50)
    b = np.array([0] * 25 + [1] * 25 + [0] * 25 + [1] * 25)
    kappa, p, _ = _cohen_kappa(a, b, [0, 1])
    assert kappa == pytest.approx(0.0, abs=1e-12)
    assert p == pytest.approx(0.5, abs=1e-9)


def _tasa_de_rechazo(marginal: float, n: int) -> float:
    """Tasa de rechazo al 5 % bajo H0 (dos evaluadores independientes), 20 semillas × 300 muestras."""
    cats = [0, 1]
    tasas = []
    for semilla in range(20):
        rng = np.random.default_rng(100 + semilla)
        rech = 0
        for _ in range(300):
            a = rng.choice(cats, n, p=[marginal, 1 - marginal])
            b = rng.choice(cats, n, p=[marginal, 1 - marginal])
            rech += _cohen_kappa(a, b, cats)[1] < 0.05
        tasas.append(rech / 300)
    return float(np.mean(tasas))


def test_s019_rf02_tasa_de_rechazo_unilateral_bajo_h0_con_marginales_equilibrados():
    """S019-RF-02 (calibración): marginales 50/50, n = 100: la tasa de rechazo unilateral al 5 % es 0,05 ± 0,01 (medida 0,047)."""
    assert _tasa_de_rechazo(0.5, 100) == pytest.approx(0.05, abs=0.01)


def test_s019_rf02_la_prueba_z_es_liberal_con_marginales_asimetricos():
    """S019-RF-02 (límite conocido): con marginales 85/15 y n = 100 la prueba z unilateral rechaza de más (medida 0,0675 al 5 %),
    porque la distribución de κ bajo H0 es asimétrica; con n = 400 baja a 0,054. No es un error del código: es la aproximación normal."""
    tasa = _tasa_de_rechazo(0.85, 100)
    assert 0.05 < tasa < 0.08


# ── S019-RF-03: EV del Xbar-R con d2 ─────────────────────────────────────────────────────────────────────────────────
def _estudio(partes: int, operadores: int, replicas: int, semilla: int = 5) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    return (50 + rng.normal(0, 3, (partes, 1, 1)) + rng.normal(0, 0.5, (1, operadores, 1))
            + rng.normal(0, 1.0, (partes, operadores, replicas)))


def _rbar(d: np.ndarray) -> float:
    return float((d.max(axis=2) - d.min(axis=2)).mean())


@pytest.mark.parametrize("replicas, k1", [(2, 0.8862), (3, 0.5908)])
def test_s019_rf03_k1_de_aiag_con_mas_de_15_combinaciones(replicas, k1):
    """S019-RF-03: 10 partes × 3 operadores (30 combinaciones) → `K1 = 1/d2(r)` = 0,8862 (2 ensayos) y 0,5908 (3 ensayos)."""
    d = _estudio(10, 3, replicas)
    assert 1.0 / _d2_referencia(replicas) == pytest.approx(k1, abs=1e-4)
    res = pp.gage_rr(d, 10, 3, replicas, method="xbar_r")
    assert math.sqrt(res.var_repeatability) == pytest.approx(_rbar(d) / _d2_referencia(replicas), rel=1e-9)


def test_s019_rf03_con_pocas_combinaciones_conserva_d2_estrella():
    """S019-RF-03 (guarda: pasa antes del código): 3 × 2 = 6 combinaciones, 2 ensayos → `d2*(2, 6) = √(4/π + (2 − 4/π)/6)`."""
    d = _estudio(3, 2, 2)
    d2_estrella = math.sqrt(4 / math.pi + (2 - 4 / math.pi) / 6)   # d2(2)² = 4/π y d3(2)² = 2 − 4/π
    res = pp.gage_rr(d, 3, 2, 2, method="xbar_r")
    assert math.sqrt(res.var_repeatability) == pytest.approx(_rbar(d) / d2_estrella, rel=1e-9)


def test_s019_rf03_umbral_en_15_y_16_combinaciones():
    """S019-RF-03: 15 combinaciones (3 × 5) usan `d2*`; 16 (4 × 4) usan `d2` (2 ensayos)."""
    d15, d16 = _estudio(3, 5, 2), _estudio(4, 4, 2)
    d2_est15 = math.sqrt(4 / math.pi + (2 - 4 / math.pi) / 15)
    ev15 = math.sqrt(pp.gage_rr(d15, 3, 5, 2, method="xbar_r").var_repeatability)
    ev16 = math.sqrt(pp.gage_rr(d16, 4, 4, 2, method="xbar_r").var_repeatability)
    assert ev15 == pytest.approx(_rbar(d15) / d2_est15, rel=1e-9)
    assert ev16 == pytest.approx(_rbar(d16) / (2 / math.sqrt(math.pi)), rel=1e-9)


def test_s019_rf03_k2_y_k3_no_cambian():
    """S019-RF-03 (guarda: pasa antes del código): AV con `K2` y PV con `K3` de AIAG; 2 partes × 2 operadores × 2 ensayos."""
    d = _estudio(2, 2, 2)
    ev2 = (_rbar(d) / math.sqrt(4 / math.pi + (2 - 4 / math.pi) / 4)) ** 2     # d2*(2, 4)
    om, pm = d.mean(axis=(0, 2)), d.mean(axis=(1, 2))
    av = max((np.ptp(om) / math.sqrt(2)) ** 2 - ev2 / (2 * 2), 0.0)             # K2 = 1/√2 con 2 operadores
    pv = (np.ptp(pm) / math.sqrt(2)) ** 2                                       # K3 = 1/√2 con 2 partes
    res = pp.gage_rr(d, 2, 2, 2, method="xbar_r")
    assert res.var_operator == pytest.approx(av, rel=1e-9)
    assert res.var_part == pytest.approx(pv, rel=1e-9)


def test_s019_rf03_av_con_k2_de_aiag_resta_la_ev_nueva():
    """S019-RF-03: con 30 combinaciones el AV usa `K2 = 0,5231` (3 operadores) y resta la EV calculada con `d2`."""
    d = _estudio(10, 3, 2)
    ev2 = (_rbar(d) / _d2_referencia(2)) ** 2
    om = d.mean(axis=(0, 2))
    av = max((np.ptp(om) * 0.5231) ** 2 - ev2 / (10 * 2), 0.0)
    res = pp.gage_rr(d, 10, 3, 2, method="xbar_r")
    assert res.var_operator == pytest.approx(av, rel=2e-3)   # K2 tabulado a 4 decimales
