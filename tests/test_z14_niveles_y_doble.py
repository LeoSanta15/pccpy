"""Pruebas de la especificación 016: Z1.4 con niveles especiales S-1 a S-4, muestreo doble y plan que no cabe en el lote.

Las tablas de este archivo están transcritas de las capturas de la norma (tablas I, II-A y III-A) que aportó la persona
responsable, no de la salida de pccpy. La probabilidad de aceptación y el tamaño medio de muestra del plan doble se
calculan aquí con la convolución binomial escrita aparte y con simulación.
"""
import math
import warnings

import numpy as np
import pytest
from scipy import stats

import pccpy as pp
from pccpy.acceptance import _LETRAS_CODIGO, _N_LETRA, _letra_codigo, _plan_z14

# ── Tabla I de Z1.4 (captura): una fila por tramo de lote; columnas S-1, S-2, S-3, S-4, I, II, III ─────────────────────
_NIVELES = ("S-1", "S-2", "S-3", "S-4", 1, 2, 3)
_TABLA_I = [
    # (lote desde, lote hasta, S-1, S-2, S-3, S-4, I, II, III)
    (2, 8, "A", "A", "A", "A", "A", "A", "B"),
    (9, 15, "A", "A", "A", "A", "A", "B", "C"),
    (16, 25, "A", "A", "B", "B", "B", "C", "D"),
    (26, 50, "A", "B", "B", "C", "C", "D", "E"),
    (51, 90, "B", "B", "C", "C", "C", "E", "F"),
    (91, 150, "B", "B", "C", "D", "D", "F", "G"),
    (151, 280, "B", "C", "D", "E", "E", "G", "H"),
    (281, 500, "B", "C", "D", "E", "F", "H", "J"),
    (501, 1200, "C", "C", "E", "F", "G", "J", "K"),
    (1201, 3200, "C", "D", "E", "G", "H", "K", "L"),
    (3201, 10000, "C", "D", "F", "G", "J", "L", "M"),
    (10001, 35000, "C", "D", "F", "H", "K", "M", "N"),
    (35001, 150000, "D", "E", "G", "J", "L", "N", "P"),
    (150001, 500000, "D", "E", "G", "J", "M", "P", "Q"),
    (500001, 10**7, "D", "E", "H", "K", "N", "Q", "R"),
]
_CELDAS_I = [(n, nivel, fila[2 + k]) for fila in _TABLA_I for n in (fila[0], fila[1]) for k, nivel in enumerate(_NIVELES)]


@pytest.mark.parametrize("lote, nivel, letra", [c for c in _CELDAS_I if isinstance(c[1], str)])
def test_s016_rf01_letra_de_codigo_de_los_niveles_especiales(lote, nivel, letra):
    """S016-RF-01: la letra de código de S-1 a S-4 coincide con la tabla I (60 celdas × los dos extremos de cada tramo)."""
    assert _letra_codigo(lote, nivel) == letra


@pytest.mark.parametrize("lote, nivel, letra", [c for c in _CELDAS_I if isinstance(c[1], int)])
def test_s016_rf01_los_niveles_generales_no_cambian(lote, nivel, letra):
    """S016-RF-01: los niveles I, II y III de 0.15.8 coinciden con la tabla I de la captura (guarda: pasa antes del código)."""
    assert _letra_codigo(lote, nivel) == letra


@pytest.mark.parametrize("nivel", ["S-3", "S-4"])
def test_s016_rf01_la_funcion_publica_acepta_los_niveles_especiales(nivel):
    """S016-RF-01: con N = 1 000 y S-3 la letra es E, y con S-4, F; el plan es el de esa letra."""
    plan = pp.acceptance_sampling_attributes(1000, 1.0, inspection_level=nivel)
    letra = {"S-3": "E", "S-4": "F"}[nivel]
    assert plan.n == _plan_z14(letra, 1.0)[0]


@pytest.mark.parametrize("nivel", ["S-5", "S-0", "s-3", "S3", "S 3", 4, 0, None, 2.5])
def test_s016_rf01_un_nivel_inexistente_lanza_value_error(nivel):
    """S016-RF-01: solo se aceptan 1, 2, 3 y «S-1» a «S-4»."""
    with pytest.raises(ValueError):
        pp.acceptance_sampling_attributes(1000, 1.0, inspection_level=nivel)


# ── Tabla II-A (captura): las celdas con números caen en las diagonales Ac = 0, 1, 2, 3, 5, 7, 10, 14, 21 ──────────────
_AQL = [0.010, 0.015, 0.025, 0.040, 0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.0, 1.5, 2.5, 4.0, 6.5, 10.0]
_AC_POR_DIAGONAL = {14: 0, 17: 1, 18: 2, 19: 3, 20: 5, 21: 7, 22: 10, 23: 14, 24: 21}
_TAMANOS = [2, 3, 5, 8, 13, 20, 32, 50, 80, 125, 200, 315, 500, 800, 1250, 2000]


def test_s016_rf02_los_tamanos_de_muestra_por_letra():
    """S016-RF-02: A…R tienen las muestras 2, 3, 5, 8, 13, 20, 32, 50, 80, 125, 200, 315, 500, 800, 1250, 2000 (tabla II-A)."""
    assert _LETRAS_CODIGO == list("ABCDEFGHJKLMNPQR")
    assert _N_LETRA == _TAMANOS


def test_s016_rf02_las_celdas_numeradas_de_la_diagonal():
    """S016-RF-02: cada celda con números de la tabla II-A (Ac y Re = Ac + 1, con la muestra de su letra) coincide."""
    for i, letra in enumerate("ABCDEFGHJKLMNPQR"):
        for j, aql in enumerate(_AQL):
            if i + j in _AC_POR_DIAGONAL:
                n, ac = _plan_z14(letra, aql)
                assert (n, ac) == (_TAMANOS[i], _AC_POR_DIAGONAL[i + j]), (letra, aql)


def test_s016_rf02_toda_celda_con_flecha_apunta_a_un_plan_numerado_de_su_columna():
    """S016-RF-02: con flecha, el plan es una celda numerada de la misma columna de AQL (no un tamaño o Ac inventado)."""
    for i, letra in enumerate("ABCDEFGHJKLMNPQR"):
        for j, aql in enumerate(_AQL):
            n, ac = _plan_z14(letra, aql)
            fila = _TAMANOS.index(n)
            assert fila + j in _AC_POR_DIAGONAL and _AC_POR_DIAGONAL[fila + j] == ac, (letra, aql)


def test_s016_rf02_las_flechas_confirmadas_por_la_persona_responsable():
    """S016-RF-02: letra A con AQL 10 % → n = 5, Ac = 1; letra F con AQL 0,40 % → plan 0/1 (confirmado sobre la captura)."""
    assert _plan_z14("A", 10.0) == (5, 1)
    assert _plan_z14("F", 0.40)[1] == 0


# ── S016-RF-04: el plan no puede tener más muestra que el lote ───────────────────────────────────────────────────────
@pytest.mark.parametrize("lote, aql", [(10, 0.01), (20, 0.01), (200, 0.01), (100, 0.015)])
def test_s016_rf04_una_muestra_mayor_que_el_lote_es_inspeccion_al_100_por_ciento(lote, aql):
    """S016-RF-04: con la muestra de la tabla ≥ el lote, n = N con el Ac de la tabla y un aviso (hoy n = 1250 > N)."""
    with pytest.warns(UserWarning, match="100"):
        plan = pp.acceptance_sampling_attributes(lote, aql)
    assert plan.n == lote
    assert plan.c == _plan_z14(_letra_codigo(lote, 2), aql)[1]
    assert plan.aoq_max >= 0 and not math.isnan(plan.aoq_max)


def test_s016_rf04_una_muestra_igual_al_lote_tambien_es_inspeccion_al_100_por_ciento():
    """S016-RF-04: «igual o mayor» (la norma): N = 5 y AQL 10 → la tabla da n = 5, Ac = 1."""
    with pytest.warns(UserWarning, match="100"):
        plan = pp.acceptance_sampling_attributes(5, 10.0)
    assert (plan.n, plan.c) == (5, 1)


def test_s016_rf04_si_la_muestra_cabe_no_hay_aviso_ni_cambio():
    """S016-RF-04: con N = 1 000 y AQL 1,0 el plan sigue siendo el de 0.15.8 (n = 80, Ac = 2) y no avisa."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        plan = pp.acceptance_sampling_attributes(1000, 1.0)
    assert (plan.n, plan.c) == (80, 2)


# ── S016-RF-03 y RF-05: muestreo doble ────────────────────────────────────────────────────────────────────────────────
def _doble(lote=1000, aql=1.0, **kw):
    return pp.acceptance_sampling_attributes(lote, aql, sampling="double", **kw)


# Tabla III-A (captura): los 8 planes con números (Ac1, Re1 de la primera muestra y Ac2, Re2 de la acumulada) caen en las
# diagonales 17 a 24 (como los planes simples con Ac ≥ 1); la celda 0 2 / 1 2 más a la izquierda está en la letra R
# (confirmado por la persona responsable). Las muestras n1 = n2 de las letras B a R son 2, 3, 5, …, 1250.
_PLANES_DOBLES = [(0, 2, 1, 2), (0, 3, 3, 4), (1, 3, 4, 5), (2, 5, 6, 7), (3, 7, 8, 9), (5, 9, 12, 13), (7, 11, 18, 19), (11, 16, 26, 27)]
# Mayor lote de cada letra B…R con el nivel III de la tabla I (la muestra acumulada 2·n1 siempre cabe en el lote)
_LOTE_NIVEL_III = {"B": 8, "C": 15, "D": 25, "E": 50, "F": 90, "G": 150, "H": 280, "J": 500, "K": 1200, "L": 3200, "M": 10000,
                   "N": 35000, "P": 150000, "Q": 500000, "R": 600000}


def test_s016_rf03_las_celdas_numeradas_de_la_tabla_iii_a():
    """S016-RF-03: cada celda con números de la tabla III-A (letras B a R, diagonales 17 a 24) coincide con la captura."""
    comprobadas = 0
    for i, letra in enumerate("ABCDEFGHJKLMNPQR"):
        if letra == "A":
            continue
        for j, aql in enumerate(_AQL):
            if 17 <= i + j <= 24:
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    plan = pp.acceptance_sampling_attributes(_LOTE_NIVEL_III[letra], aql, inspection_level=3, sampling="double")
                esperado = (_TAMANOS[i - 1], _TAMANOS[i - 1]) + _PLANES_DOBLES[i + j - 17]
                assert (plan.n1, plan.n2, plan.ac1, plan.re1, plan.ac2, plan.re2) == esperado, (letra, aql)
                comprobadas += 1
    assert comprobadas == 84  # 15 letras (B a R) × los AQL de 0,010 a 10 % que caen en las diagonales 17 a 24


def test_s016_rf03_el_parametro_sampling_solo_acepta_single_o_double():
    """S016-RF-03: ``sampling`` distinto de «single» y «double» lanza ValueError en español."""
    with pytest.raises(ValueError):
        pp.acceptance_sampling_attributes(1000, 1.0, sampling="triple")


def test_s016_rf03_el_simple_sigue_siendo_el_valor_por_defecto():
    assert pp.acceptance_sampling_attributes(1000, 1.0, sampling="single").n == pp.acceptance_sampling_attributes(1000, 1.0).n


def test_s016_rf03_estructura_del_plan_doble():
    """S016-RF-03: n2 = n1 (acumulado 2·n1), re1 > ac1, re2 = ac2 + 1 y ac2 > ac1; las muestras son las de la tabla."""
    for aql in _AQL[2:]:
        for lote in (12, 40, 120, 300, 1000, 3000, 20000):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plan = _doble(lote, aql)
            assert plan.re2 == plan.ac2 + 1
            if plan.n2 > 0:
                assert plan.n2 == plan.n1 and plan.n1 in _TAMANOS
                assert plan.re1 > plan.ac1 >= 0 and plan.ac2 > plan.ac1
            else:  # inspección al 100 %: todo el lote en la primera muestra
                assert plan.n1 == lote and plan.ac1 == plan.ac2


@pytest.mark.parametrize("aql", [0.010, 0.015])
def test_s016_rf03_sin_plan_doble_para_los_aql_mas_bajos(aql):
    """S016-RF-03: con AQL 0,010 y 0,015 % la tabla III-A no trae plan doble (la estrella manda usar el simple): ValueError."""
    with pytest.raises(ValueError, match="single"):
        _doble(1000, aql)


def _pa_doble(plan, p):
    """P(aceptar) del plan doble por convolución binomial, escrita aparte de pccpy."""
    tot = stats.binom.cdf(plan.ac1, plan.n1, p)
    for d1 in range(plan.ac1 + 1, plan.re1):
        tot += stats.binom.pmf(d1, plan.n1, p) * stats.binom.cdf(plan.ac2 - d1, plan.n2, p)
    return tot


@pytest.mark.parametrize("p", [0.0, 0.002, 0.01, 0.03, 0.08, 0.3])
def test_s016_rf03_probabilidad_de_aceptacion_exacta(p):
    """S016-RF-03: ``pa(p)`` = P(d1 ≤ ac1) + Σ P(d1)·P(d2 ≤ ac2 − d1), con la binomial."""
    plan = _doble()
    assert plan.pa(p) == pytest.approx(_pa_doble(plan, p), abs=1e-12)


def test_s016_rf03_probabilidad_de_aceptacion_contra_simulacion():
    """S016-RF-03: 20 semillas × 20 000 lotes, tolerancia 0,005."""
    plan = _doble()
    for p in (0.01, 0.03):
        estimaciones = []
        for semilla in range(20):
            rng = np.random.default_rng(semilla)
            d1 = rng.binomial(plan.n1, p, 20000)
            d2 = rng.binomial(plan.n2, p, 20000)
            acepta = (d1 <= plan.ac1) | ((d1 > plan.ac1) & (d1 < plan.re1) & (d1 + d2 <= plan.ac2))
            estimaciones.append(acepta.mean())
        assert plan.pa(p) == pytest.approx(np.mean(estimaciones), abs=0.005)


def test_s016_rf05_tamano_medio_de_muestra_asn():
    """S016-RF-05: ASN(p) = n1 + n2·P(ac1 < d1 < re1), acotado por n1 y n1 + n2."""
    plan = _doble()
    for p in (0.0, 0.005, 0.02, 0.05, 0.2):
        continuar = stats.binom.cdf(plan.re1 - 1, plan.n1, p) - stats.binom.cdf(plan.ac1, plan.n1, p)
        assert plan.asn(p) == pytest.approx(plan.n1 + plan.n2 * continuar, abs=1e-9)
        assert plan.n1 - 1e-9 <= plan.asn(p) <= plan.n1 + plan.n2 + 1e-9
    assert plan.asn(0.0) == pytest.approx(plan.n1)


def test_s016_rf05_curvas_y_tablas_del_plan_doble():
    """S016-RF-05: oc_curve, aoq_curve y asn_curve con claves estables en inglés; to_frame(stable=True) con las claves del plan."""
    plan = _doble()
    oc = plan.oc_curve(stable=True)
    assert list(oc.columns)[:2] == ["defective_fraction", "p_accept"]
    assert plan.oc_curve().shape == oc.shape
    aoq = plan.aoq_curve(stable=True)
    assert list(aoq.columns)[:2] == ["defective_fraction", "aoq"]
    asn = plan.asn_curve(stable=True)
    assert list(asn.columns)[:2] == ["defective_fraction", "asn"]
    marco = plan.to_frame(stable=True)
    for clave in ("lot_size", "sample_size_1", "sample_size_2", "acceptance_number_1", "rejection_number_1",
                  "acceptance_number_2", "rejection_number_2", "aql_pct", "aoql_pct"):
        assert clave in marco.index, clave
    assert "Z1.4" in plan.summary() or "z1.4" in plan.summary().lower()


def test_s016_rf05_el_aoql_del_plan_doble_es_el_maximo_exacto():
    """S016-RF-05: AOQ(p) = p·[Pa₁·(N − n1) + Pa₂·(N − n1 − n2)]/N (Grant y Leavenworth), con la binomial escrita aparte."""
    plan = _doble()
    ps = np.linspace(1e-6, 0.5, 20001)
    pa1 = stats.binom.cdf(plan.ac1, plan.n1, ps)
    pa2 = np.zeros_like(ps)
    for d1 in range(plan.ac1 + 1, plan.re1):
        pa2 += stats.binom.pmf(d1, plan.n1, ps) * stats.binom.cdf(plan.ac2 - d1, plan.n2, ps)
    aoq = ps * (pa1 * (plan.N - plan.n1) + pa2 * (plan.N - plan.n1 - plan.n2)) / plan.N
    assert plan.aoq_max == pytest.approx(aoq.max(), rel=2e-3)


def test_s016_rf03_la_letra_a_usa_el_plan_doble_de_la_letra_b_con_aviso():
    """S016-RF-03: lote de 2 a 8 con muestreo doble → plan de la letra B y UserWarning (decidido)."""
    with pytest.warns(UserWarning, match="B"):
        plan_a = _doble(7, 10.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        plan_b = _doble(12, 10.0)  # lote de 9 a 15: letra B, nivel II (sin aviso)
    assert (plan_a.n1, plan_a.n2, plan_a.ac1, plan_a.re1, plan_a.ac2, plan_a.re2) == (
        plan_b.n1, plan_b.n2, plan_b.ac1, plan_b.re1, plan_b.ac2, plan_b.re2)


def test_s016_rf04_el_doble_que_no_cabe_en_el_lote_es_inspeccion_al_100_por_ciento():
    """S016-RF-04: con muestra acumulada ≥ lote (2·n1 ≥ N) se inspecciona todo el lote en la primera muestra y se avisa."""
    with pytest.warns(UserWarning, match="100"):
        plan = _doble(10, 1.0)
    assert (plan.n1, plan.n2) == (10, 0)
    assert plan.ac1 == plan.ac2 and plan.re2 == plan.ac2 + 1
    assert plan.aoq_max >= 0 and not math.isnan(plan.aoq_max)


def test_s016_rf03_niveles_especiales_con_muestreo_doble():
    """S016-RF-01 y RF-03 juntos: el nivel S-3 también sirve con ``sampling="double"``."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plan = _doble(1000, 1.0, inspection_level="S-3")
    assert plan.n1 in _TAMANOS
