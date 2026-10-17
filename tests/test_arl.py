# Trazabilidad: S009-RF-01, S009-RF-02, S009-RF-03, S009-RF-04, S009-RF-05 (spec 009, núcleo).
"""Especificación 009: ARL de las cartas Shewhart, CUSUM y EWMA (núcleo).

Referencias independientes (nunca la salida de pccpy):

* Shewhart: fórmula cerrada con ``scipy.stats.norm``.
* CUSUM y EWMA: simulación de Monte Carlo propia de este archivo (vectorizada, 20 semillas) y, como contraste, valores de la
  literatura **recordados de memoria** (Hawkins y Olwell, 1998; Lucas y Saccucci, 1990; Montgomery): no se pudieron consultar,
  así que su tolerancia es la de un valor recordado y no la de una tabla. Si alguno discrepara de la simulación, manda la
  simulación y se anota en la especificación (principio 12 de la constitución).
"""
import functools

import numpy as np
import pytest
from scipy import stats

import pccpy as pp

SEMILLAS = range(20)
CORRIDAS_POR_SEMILLA = 1500


# ------------------------------------------------------------------ simulación propia (independiente de pccpy)
def _simular(kind, shift, semilla, corridas, *, h=4.0, k=0.5, headstart=0.0, lam=0.2, L=3.0, exact=False):
    """Longitudes de racha de ``corridas`` cartas en paralelo (numpy), con el estadístico ~ N(shift, 1)."""
    rng = np.random.default_rng(semilla)
    largo = np.zeros(corridas)
    activo = np.arange(corridas)
    c_mas = np.full(corridas, float(headstart))
    c_menos = np.full(corridas, float(headstart))
    z = np.zeros(corridas)
    t = 0
    while activo.size:
        t += 1
        x = rng.normal(shift, 1.0, activo.size)
        if kind == "shewhart":
            sen = np.abs(x) > L
        elif kind == "cusum":
            c_mas[activo] = np.maximum(0.0, x - k + c_mas[activo])
            c_menos[activo] = np.maximum(0.0, -x - k + c_menos[activo])
            sen = (c_mas[activo] > h) | (c_menos[activo] > h)
        else:  # ewma
            z[activo] = (1 - lam) * z[activo] + lam * x
            var = lam / (2 - lam) * ((1 - (1 - lam) ** (2 * t)) if exact else 1.0)
            sen = np.abs(z[activo]) > L * np.sqrt(var)
        largo[activo[sen]] = t
        activo = activo[~sen]
        if t > 200_000:  # seguro contra bucles infinitos
            raise RuntimeError("simulación sin fin")
    return largo


@functools.cache
def _arl_mc(kind, shift, **kw):
    """ARL por Monte Carlo: 20 semillas x 1 500 corridas."""
    todas = np.concatenate([_simular(kind, shift, s, CORRIDAS_POR_SEMILLA, **dict(kw)) for s in SEMILLAS])
    return float(todas.mean())


def _mc(kind, shift, **kw):
    return _arl_mc(kind, shift, **kw)


# -------------------------------------------------------------------------- RF-01
@pytest.mark.parametrize("k, shift", [(3.0, 0.0), (3.0, 1.0), (3.0, 2.5), (2.0, 0.0), (2.0, 0.7), (1.5, 1.0), (4.0, 3.0)])
def test_s009_rf_01_shewhart_es_la_formula_cerrada(k, shift):
    """S009-RF-01: ARL = 1 / P(|Z| > k), Z ~ N(shift, 1), con scipy.stats.norm (tolerancia relativa 1e-12)."""
    esperado = 1.0 / (stats.norm.cdf(-k - shift) + stats.norm.sf(k - shift))
    assert pp.arl_shewhart(k=k, shift=shift) == pytest.approx(esperado, rel=1e-12)


def test_s009_rf_01_valores_conocidos():
    """S009-RF-01: 370,398 en control y 43,895 con 1σ (calculados aparte), y las cifras de la literatura (de memoria)."""
    assert pp.arl_shewhart(k=3, shift=0) == pytest.approx(1 / (2 * stats.norm.sf(3)), rel=1e-12)
    assert pp.arl_shewhart(k=3, shift=1) == pytest.approx(1 / (stats.norm.cdf(-4) + stats.norm.sf(2)), rel=1e-12)
    # contraste con la literatura recordada de memoria (Montgomery): 370,4 y 43,9
    assert pp.arl_shewhart(k=3, shift=0) == pytest.approx(370.4, abs=0.05)
    assert pp.arl_shewhart(k=3, shift=1) == pytest.approx(43.9, abs=0.05)


def test_s009_rf_01_los_valores_por_defecto_son_k3_y_sin_desplazamiento():
    """S009-RF-01: sin argumentos es la carta de 3 sigmas en control."""
    assert pp.arl_shewhart() == pytest.approx(370.3983473449592, rel=1e-12)


def test_s009_rf_01_coincide_con_la_simulacion():
    """S009-RF-01: contraste con el Monte Carlo propio (20 semillas) con k = 2 (ARL ≈ 22) y 1σ de desplazamiento."""
    for shift in (0.0, 1.0):
        assert pp.arl_shewhart(k=2.0, shift=shift) == pytest.approx(_mc("shewhart", shift, L=2.0), rel=0.03)


# -------------------------------------------------------------------------- RF-02
def test_s009_rf_02_cusum_literatura_recordada_de_memoria():
    """S009-RF-02: h=4, k=0,5: ARL ≈ 168 en control y ≈ 8,38 con 1σ (Hawkins y Olwell, de memoria; bilateral)."""
    assert pp.arl_cusum(h=4, k=0.5, shift=0) == pytest.approx(168.0, rel=0.015)
    assert pp.arl_cusum(h=4, k=0.5, shift=1) == pytest.approx(8.38, abs=0.08)


@pytest.mark.parametrize("shift", [0.0, 0.5, 1.0, 2.0])
def test_s009_rf_02_cusum_coincide_con_la_simulacion(shift):
    """S009-RF-02: ARL numérico = Monte Carlo propio (20 semillas x 1 500 corridas), tolerancia relativa 3 %."""
    assert pp.arl_cusum(h=4, k=0.5, shift=shift) == pytest.approx(_mc("cusum", shift, h=4.0, k=0.5), rel=0.03)


def test_s009_rf_02_cusum_con_otros_h_y_k():
    """S009-RF-02: otro par (h, k) = (5, 0,25) contra la simulación."""
    assert pp.arl_cusum(h=5, k=0.25, shift=0.5) == pytest.approx(_mc("cusum", 0.5, h=5.0, k=0.25), rel=0.03)


def test_s009_rf_02_el_arranque_rapido_reduce_el_arl_y_coincide_con_la_simulacion():
    """S009-RF-02: con headstart = h/2 el ARL baja y coincide con el Monte Carlo (Lucas y Crosier, 1982)."""
    sin = pp.arl_cusum(h=4, k=0.5, shift=0, headstart=0.0)
    con = pp.arl_cusum(h=4, k=0.5, shift=0, headstart=2.0)
    assert con < sin
    assert con == pytest.approx(_mc("cusum", 0.0, h=4.0, k=0.5, headstart=2.0), rel=0.03)


# -------------------------------------------------------------------------- RF-03
def test_s009_rf_03_ewma_literatura_recordada_de_memoria():
    """S009-RF-03: λ=0,2: L=2,962 → ARL₀ ≈ 500 (Lucas y Saccucci, de memoria); L=3 → ≈ 561.

    Para L=3 el Monte Carlo propio da 561,4 ± 1,2 con límites asintóticos (200 000 corridas, 40 semillas) y ≈ 552 con límites
    exactos (30 000 corridas, 20 semillas). El README cita «≈ 570 con límites exactos» y «≈ 550 con asintóticos»: no coincide
    con la simulación (y parece tener los dos tipos de límite invertidos); se revisa al implementar.
    """
    assert pp.arl_ewma(weight=0.2, L=2.962, shift=0) == pytest.approx(500.0, rel=0.015)
    assert pp.arl_ewma(weight=0.2, L=3.0, shift=0) == pytest.approx(561.4, rel=0.01)


@pytest.mark.parametrize("shift", [0.0, 0.5, 1.0, 2.0])
def test_s009_rf_03_ewma_coincide_con_la_simulacion(shift):
    """S009-RF-03: ARL numérico = Monte Carlo propio con límites asintóticos, tolerancia relativa 3 %."""
    assert pp.arl_ewma(weight=0.2, L=3.0, shift=shift) == pytest.approx(_mc("ewma", shift, lam=0.2, L=3.0), rel=0.03)


def test_s009_rf_03_ewma_con_limites_exactos_es_menor_y_coincide_con_la_simulacion():
    """S009-RF-03: con límites exactos (más estrechos al inicio) el ARL₀ baja y coincide con el Monte Carlo."""
    asintotico = pp.arl_ewma(weight=0.2, L=3.0, shift=0, exact_limits=False)
    exacto = pp.arl_ewma(weight=0.2, L=3.0, shift=0, exact_limits=True)
    assert exacto < asintotico
    assert exacto == pytest.approx(_mc("ewma", 0.0, lam=0.2, L=3.0, exact=True), rel=0.03)


@pytest.mark.parametrize("shift", [0.0, 1.0, 2.0])
def test_s009_rf_03_con_weight_1_la_ewma_es_la_shewhart(shift):
    """S009-RF-03: λ = 1 → la EWMA es la Shewhart con el mismo L (identidad)."""
    assert pp.arl_ewma(weight=1.0, L=3.0, shift=shift) == pytest.approx(pp.arl_shewhart(k=3.0, shift=shift), rel=1e-6)


def test_s009_rf_03_otro_peso_contra_la_simulacion():
    """S009-RF-03: λ = 0,05, L = 2,6 con 1σ de desplazamiento contra la simulación."""
    assert pp.arl_ewma(weight=0.05, L=2.6, shift=1.0) == pytest.approx(_mc("ewma", 1.0, lam=0.05, L=2.6), rel=0.03)


# -------------------------------------------------------------------------- RF-04
@pytest.mark.parametrize("llamar", [
    lambda **kw: pp.arl_cusum(h=4, k=0.5, shift=1.0, **kw),
    lambda **kw: pp.arl_ewma(weight=0.2, L=3.0, shift=1.0, **kw),
])
def test_s009_rf_04_el_metodo_por_defecto_es_numeric(llamar):
    """S009-RF-04: sin `method` se usa "numeric"."""
    assert llamar() == llamar(method="numeric")


@pytest.mark.parametrize("llamar, shift", [
    (lambda shift, **kw: pp.arl_cusum(h=4, k=0.5, shift=shift, **kw), 0.0),
    (lambda shift, **kw: pp.arl_cusum(h=4, k=0.5, shift=shift, **kw), 1.0),
    (lambda shift, **kw: pp.arl_ewma(weight=0.2, L=3.0, shift=shift, **kw), 0.0),
    (lambda shift, **kw: pp.arl_ewma(weight=0.2, L=3.0, shift=shift, **kw), 1.0),
])
def test_s009_rf_04_numeric_y_markov_coinciden(llamar, shift):
    """S009-RF-04: los dos métodos deterministas coinciden con tolerancia relativa 2e-3 (precisión del método de celdas)."""
    assert llamar(shift, method="markov") == pytest.approx(llamar(shift, method="numeric"), rel=2e-3)


def test_s009_rf_04_simulacion_es_reproducible_con_la_misma_semilla():
    """S009-RF-04: misma `seed` → resultado idéntico; semillas distintas → resultados distintos."""
    a = pp.arl_cusum(h=4, k=0.5, shift=1.0, method="simulation", n_runs=500, seed=7)
    b = pp.arl_cusum(h=4, k=0.5, shift=1.0, method="simulation", n_runs=500, seed=7)
    c = pp.arl_cusum(h=4, k=0.5, shift=1.0, method="simulation", n_runs=500, seed=8)
    assert a == b
    assert a != c


@pytest.mark.parametrize("llamar, esperado", [
    (lambda **kw: pp.arl_shewhart(k=2.0, shift=0.0, **kw), 1 / (2 * stats.norm.sf(2))),
    (lambda **kw: pp.arl_cusum(h=4, k=0.5, shift=1.0, **kw), None),
    (lambda **kw: pp.arl_ewma(weight=0.2, L=3.0, shift=1.0, **kw), None),
])
def test_s009_rf_04_simulacion_coincide_con_numeric_dentro_del_error_de_monte_carlo(llamar, esperado):
    """S009-RF-04: con 20 000 corridas el error de Monte Carlo es ≈ ARL/√n (≈ 0,7 %); tolerancia relativa 4 %."""
    referencia = llamar(method="numeric") if esperado is None else esperado
    assert llamar(method="simulation", n_runs=20_000, seed=1) == pytest.approx(referencia, rel=0.04)


@pytest.mark.parametrize("llamar", [
    lambda **kw: pp.arl_shewhart(**kw),
    lambda **kw: pp.arl_cusum(**kw),
    lambda **kw: pp.arl_ewma(**kw),
])
def test_s009_rf_04_un_metodo_desconocido_lanza_value_error(llamar):
    """S009-RF-04: un `method` desconocido lanza ValueError."""
    with pytest.raises(ValueError):
        llamar(method="aproximado")


def test_s009_rf_04_la_shewhart_no_admite_markov():
    """S009-RF-04: la Shewhart es exacta; "markov" no se admite y lanza ValueError en español."""
    with pytest.raises(ValueError, match="markov"):
        pp.arl_shewhart(k=3, method="markov")


# -------------------------------------------------------------------------- RF-05
@pytest.mark.parametrize("llamar", [
    lambda: pp.arl_shewhart(k=0),
    lambda: pp.arl_shewhart(k=-1),
    lambda: pp.arl_shewhart(k=float("nan")),
    lambda: pp.arl_shewhart(k=3, shift=float("inf")),
    lambda: pp.arl_shewhart(k=3, shift=float("nan")),
    lambda: pp.arl_cusum(h=0),
    lambda: pp.arl_cusum(h=-4),
    lambda: pp.arl_cusum(k=-0.1),
    lambda: pp.arl_cusum(headstart=-1),
    lambda: pp.arl_cusum(h=4, headstart=4),
    lambda: pp.arl_cusum(shift=float("nan")),
    lambda: pp.arl_ewma(weight=0),
    lambda: pp.arl_ewma(weight=1.5),
    lambda: pp.arl_ewma(weight=-0.2),
    lambda: pp.arl_ewma(L=0),
    lambda: pp.arl_ewma(L=-3),
    lambda: pp.arl_ewma(shift=float("inf")),
    lambda: pp.arl_cusum(method="simulation", n_runs=0),
    lambda: pp.arl_ewma(method="simulation", n_runs=-5),
])
def test_s009_rf_05_los_parametros_invalidos_lanzan_value_error(llamar):
    """S009-RF-05: parámetros fuera de rango o no finitos lanzan ValueError."""
    with pytest.raises(ValueError):
        llamar()


@pytest.mark.parametrize("llamar", [
    lambda s: pp.arl_shewhart(k=3, shift=s),
    lambda s: pp.arl_cusum(h=4, k=0.5, shift=s),
    lambda s: pp.arl_ewma(weight=0.2, L=3.0, shift=s),
])
def test_s009_rf_05_el_arl_es_simetrico_en_el_desplazamiento(llamar):
    """S009-RF-05: carta bilateral → arl(shift) == arl(−shift)."""
    for s in (0.3, 1.0, 2.0):
        assert llamar(-s) == pytest.approx(llamar(s), rel=1e-9)


@pytest.mark.parametrize("llamar", [
    lambda s: pp.arl_shewhart(k=3, shift=s),
    lambda s: pp.arl_cusum(h=4, k=0.5, shift=s),
    lambda s: pp.arl_ewma(weight=0.2, L=3.0, shift=s),
])
def test_s009_rf_05_el_arl_decrece_con_el_desplazamiento_y_nunca_baja_de_1(llamar):
    """S009-RF-05: ARL decreciente en |shift|, ≥ 1 siempre, y ≈ 1 con un desplazamiento enorme."""
    valores = [llamar(s) for s in (0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0)]
    assert all(a > b for a, b in zip(valores, valores[1:]))
    assert all(v >= 1.0 for v in valores)
    assert valores[-1] < 1.01


@pytest.mark.parametrize("llamar", [
    lambda s: pp.arl_shewhart(k=3, shift=s),
    lambda s: pp.arl_cusum(h=4, k=0.5, shift=s),
    lambda s: pp.arl_ewma(weight=0.2, L=3.0, shift=s),
])
def test_s009_rf_05_un_arreglo_de_desplazamientos_da_un_arreglo(llamar):
    """S009-RF-05: `shift` como arreglo devuelve un arreglo del mismo tamaño con los valores escalares; el escalar, un float."""
    shifts = np.array([0.0, 0.5, 1.0, 2.0])
    r = llamar(shifts)
    assert isinstance(r, np.ndarray) and r.shape == shifts.shape
    np.testing.assert_allclose(r, [llamar(float(s)) for s in shifts], rtol=1e-12)
    assert isinstance(llamar(1.0), float)
    assert llamar([0.0, 1.0]).shape == (2,)


def test_s009_rf_05_la_shewhart_con_k_pequeno_no_desborda():
    """S009-RF-05 (caso borde): con k muy pequeño el ARL está entre 1 y 2, sin desbordes."""
    assert 1.0 <= pp.arl_shewhart(k=1e-6) < 1.0001
