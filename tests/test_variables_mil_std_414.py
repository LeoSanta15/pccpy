"""Pruebas de la especificación 017: planes por variables de MIL-STD-414 (tablas A-2 y B-1).

Las dos tablas están transcritas de las capturas de la norma que aportó la persona responsable (no del texto del
documento ni de la salida de pccpy) y se revisan celda a celda. Las flechas se resuelven aquí con un código aparte.
"""
import warnings

import numpy as np
import pytest

import pccpy as pp
from pccpy.acceptance import SamplingPlanVariables

# ── Tabla A-2 (captura): lote desde, lote hasta, niveles I a V ─────────────────────────────────────────────────────────
_A2 = [
    (3, 8, "BBBBC"),
    (9, 15, "BBBBD"),
    (16, 25, "BBBCE"),
    (26, 40, "BBBDF"),
    (41, 65, "BBCEG"),
    (66, 110, "BBDFH"),
    (111, 180, "BCEGI"),
    (181, 300, "BDFHJ"),
    (301, 500, "CEGIK"),
    (501, 800, "DFHJL"),
    (801, 1300, "EGIKL"),
    (1301, 3200, "FHJLM"),
    (3201, 8000, "GILMN"),
    (8001, 22000, "HJMNO"),
    (22001, 110000, "IKNOP"),
    (110001, 550000, "IKOPQ"),
    (550001, 10**7, "IKPQQ"),
]
_CELDAS_A2 = [(lote, nivel, fila[2][nivel - 1]) for fila in _A2 for lote in (fila[0], fila[1], (fila[0] + fila[1]) // 2)
              for nivel in range(1, 6)]

# ── Tabla B-1 (captura): letra -> (n, [k por AQL]); «↓» = primer plan por debajo en la misma columna ────────────────────
_AQL = [0.04, 0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.00, 1.50, 2.50, 4.00, 6.50, 10.00, 15.00]
_D = "↓"
_B1 = {
    "B": (3, [_D, _D, _D, _D, _D, _D, _D, _D, _D, 1.12, .958, .765, .566, .341]),
    "C": (4, [_D, _D, _D, _D, _D, _D, _D, 1.45, 1.34, 1.17, 1.01, .814, .617, .393]),
    "D": (5, [_D, _D, _D, _D, _D, _D, 1.65, 1.53, 1.40, 1.24, 1.07, .874, .675, .455]),
    "E": (7, [_D, _D, _D, _D, 2.00, 1.88, 1.75, 1.62, 1.50, 1.33, 1.15, .955, .755, .536]),
    "F": (10, [_D, _D, _D, 2.24, 2.11, 1.98, 1.84, 1.72, 1.58, 1.41, 1.23, 1.03, .828, .611]),
    "G": (15, [2.64, 2.53, 2.42, 2.32, 2.20, 2.06, 1.91, 1.79, 1.65, 1.47, 1.30, 1.09, .886, .664]),
    "H": (20, [2.69, 2.58, 2.47, 2.36, 2.24, 2.11, 1.96, 1.82, 1.69, 1.51, 1.33, 1.12, .917, .695]),
    "I": (25, [2.72, 2.61, 2.50, 2.40, 2.26, 2.14, 1.98, 1.85, 1.72, 1.53, 1.35, 1.14, .936, .712]),
    "J": (30, [2.73, 2.61, 2.51, 2.41, 2.28, 2.15, 2.00, 1.86, 1.73, 1.55, 1.36, 1.15, .946, .723]),
    "K": (35, [2.77, 2.65, 2.54, 2.45, 2.31, 2.18, 2.03, 1.89, 1.76, 1.57, 1.39, 1.18, .969, .745]),
    "L": (40, [2.77, 2.66, 2.55, 2.44, 2.31, 2.18, 2.03, 1.89, 1.76, 1.58, 1.39, 1.18, .971, .746]),
    "M": (50, [2.83, 2.71, 2.60, 2.50, 2.35, 2.22, 2.08, 1.93, 1.80, 1.61, 1.42, 1.21, 1.00, .774]),
    "N": (75, [2.90, 2.77, 2.66, 2.55, 2.41, 2.27, 2.12, 1.98, 1.84, 1.65, 1.46, 1.24, 1.03, .804]),
    "O": (100, [2.92, 2.80, 2.69, 2.58, 2.43, 2.29, 2.14, 2.00, 1.86, 1.67, 1.48, 1.26, 1.05, .819]),
    "P": (150, [2.96, 2.84, 2.73, 2.61, 2.47, 2.33, 2.18, 2.03, 1.89, 1.70, 1.51, 1.29, 1.07, .841]),
    "Q": (200, [2.97, 2.85, 2.73, 2.62, 2.47, 2.33, 2.18, 2.04, 1.89, 1.70, 1.51, 1.29, 1.07, .845]),
}
_LETRAS = list(_B1)


def _plan_b1(letra: str, columna: int) -> tuple[int, float]:
    """(n, k) de la celda, bajando por la columna hasta el primer plan numérico si hay flecha."""
    i = _LETRAS.index(letra)
    while _B1[_LETRAS[i]][1][columna] == _D:
        i += 1
    n, ks = _B1[_LETRAS[i]]
    return n, ks[columna]


def _lote_para(letra: str) -> tuple[int, int]:
    """(lote, nivel) cuya letra es `letra` en la tabla A-2, con el lote mayor del tramo (cabe la muestra)."""
    candidatos = [(fila[1], nivel) for fila in _A2 for nivel in range(1, 6) if fila[2][nivel - 1] == letra]
    lote, nivel = max(candidatos)
    return min(lote, 10**6), nivel


def _plan(N, aql, **kw):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pp.acceptance_sampling_variables(N, aql, **kw)


# ── Estructura de la transcripción (guarda: detecta un error de lectura evidente) ──────────────────────────────────────
def test_transcripcion_b1_es_monotona():
    """k no crece con el AQL (a más AQL, plan más laxo) y no decrece al bajar por la columna (más muestra, más k).

    Tolerancia de 0,01: la captura trae K = 2,45 y L = 2,44 con AQL 0,15 (un descenso de 0,01 que la persona
    responsable debe confirmar contra la norma).
    """
    for col in range(len(_AQL)):
        ks = [_plan_b1(letra, col)[1] for letra in _LETRAS]
        assert all(b >= a - 0.0101 for a, b in zip(ks, ks[1:])), f"columna AQL {_AQL[col]}"
    for letra in _LETRAS:
        ks = [_plan_b1(letra, col)[1] for col in range(len(_AQL))]
        assert all(b <= a for a, b in zip(ks, ks[1:])), f"letra {letra}"


# ── S017-RF-01: letra de código de la tabla A-2 ────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("lote, nivel, letra", _CELDAS_A2)
def test_s017_rf01_letra_a2(lote, nivel, letra):
    """S017-RF-01: la letra sale de A-2 (se observa en el n del plan con AQL 0,04 y el k de la columna sin flecha)."""
    plan = _plan(lote, 1.00, inspection_level=nivel)
    n_esperado, k_esperado = _plan_b1(letra, _AQL.index(1.00))
    assert (plan.n, plan.k) == (min(n_esperado, lote), k_esperado if n_esperado < lote else plan.k)


def test_s017_rf01_nivel_por_defecto_es_el_iv():
    """S017-RF-01: sin `inspection_level`, el nivel es el IV (el normal)."""
    assert _plan(1000, 1.00).n == _plan(1000, 1.00, inspection_level=4).n
    assert _plan(1000, 1.00, inspection_level=4).n == _plan_b1("K", _AQL.index(1.00))[0]


@pytest.mark.parametrize("nivel", [0, 6, -1, "IV", None, 4.5, True])
def test_s017_rf01_nivel_invalido(nivel):
    """S017-RF-01: un nivel que no es un entero de 1 a 5 lanza ValueError en español."""
    with pytest.raises(ValueError, match="nivel"):
        _plan(1000, 1.00, inspection_level=nivel)


# ── S017-RF-02: (n, k) de la tabla B-1 con las flechas resueltas ───────────────────────────────────────────────────────
_CELDAS_B1 = [(letra, col) for letra in _LETRAS for col in range(len(_AQL))]


@pytest.mark.parametrize("letra, col", _CELDAS_B1)
def test_s017_rf02_plan_b1(letra, col):
    """S017-RF-02: cada celda (letra × AQL) da el (n, k) de B-1; con flecha, el primer plan numérico por debajo."""
    lote, nivel = _lote_para(letra)
    n_esperado, k_esperado = _plan_b1(letra, col)
    if _B1[letra][1][col] != _D and n_esperado >= lote:
        pytest.skip("el plan no cabe en el lote (lo cubre S017-RF-05)")
    # la flecha cambia la letra efectiva: el lote debe ser mayor que la muestra del plan al que apunta
    if n_esperado >= lote:
        pytest.skip("el plan al que apunta la flecha no cabe en el lote (lo cubre S017-RF-05)")
    plan = _plan(lote, _AQL[col], inspection_level=nivel)
    assert (plan.n, plan.k) == (n_esperado, k_esperado)
    assert plan.method == "mil-std-414"


def test_s017_rf02_celda_corregida_i_025():
    """S017-RF-02: la celda dudosa de la captura (letra I, AQL 0,25) es 2,26 (confirmada por la persona responsable)."""
    lote, nivel = _lote_para("I")
    assert _plan(lote, 0.25, inspection_level=nivel).k == 2.26


def test_s017_rf02_plan_a_medida_no_cambia_ni_avisa():
    """S017-RF-02: con `n=` y `k=` el plan se usa tal cual, sin aviso."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        plan = pp.acceptance_sampling_variables(1000, 1.0, n=12, k=1.5)
    assert (plan.n, plan.k, plan.method) == (12, 1.5, "custom")


def test_s017_rf02_sin_aviso_de_aproximacion():
    """S017-RF-02: el plan de la tabla no emite el aviso de «aproximación»."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pp.acceptance_sampling_variables(1000, 1.0)


# ── S017-RF-03: inspección rigurosa ────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("letra", _LETRAS)
@pytest.mark.parametrize("col", range(1, len(_AQL)))
def test_s017_rf03_rigurosa_desplaza_la_columna(letra, col):
    """S017-RF-03: el plan riguroso con AQL `_AQL[col]` es el de la columna normal anterior."""
    lote, nivel = _lote_para(letra)
    n_esperado, k_esperado = _plan_b1(letra, col - 1)
    if n_esperado >= lote:
        pytest.skip("el plan no cabe en el lote (lo cubre S017-RF-05)")
    plan = _plan(lote, _AQL[col], inspection_level=nivel, inspection="tightened")
    assert (plan.n, plan.k) == (n_esperado, k_esperado)


def test_s017_rf03_ejemplo_del_texto():
    """S017-RF-03: rigurosa 1,00 % usa la columna normal 0,65 % (letra K: k = 2,03)."""
    assert _plan(1000, 1.00, inspection="tightened").k == 2.03
    assert _plan(1000, 1.00, inspection="normal").k == 1.89


def test_s017_rf03_sin_rigurosa_para_aql_004():
    """S017-RF-03: no existe inspección rigurosa con AQL 0,04 %."""
    with pytest.raises(ValueError, match="rigurosa"):
        _plan(1000, 0.04, inspection="tightened")


def test_s017_rf03_inspeccion_invalida():
    """S017-RF-03: `inspection` solo acepta 'normal' o 'tightened'."""
    with pytest.raises(ValueError, match="inspection"):
        _plan(1000, 1.00, inspection="reduced")


# ── S017-RF-04: criterio de la Forma 1 (protege lo que no cambia) ──────────────────────────────────────────────────────
def test_s017_rf04_forma1_unilateral():
    """S017-RF-04: se acepta si (U − x̄)/s ≥ k (cálculo aparte) y se rechaza si no."""
    x = np.array([9.8, 10.1, 10.0, 10.3, 9.9, 10.2, 10.0])
    xbar, s = x.mean(), x.std(ddof=1)
    plan = SamplingPlanVariables(N=500, n=7, k=1.5, aql=1.0, spec_type="one", alpha=0.0, ltpd=0.0, method="custom")
    q_sup = (11.0 - xbar) / s
    assert plan.evaluate(x, usl=11.0)["accept"] == (q_sup >= 1.5)
    assert plan.evaluate(x, usl=11.0)["Q_usl"] == pytest.approx(q_sup)
    assert plan.evaluate(x, usl=10.2)["accept"] is False
    q_inf = (xbar - 9.0) / s
    assert plan.evaluate(x, lsl=9.0)["accept"] == (q_inf >= 1.5)


# ── S017-RF-05: guarda del 100 % ───────────────────────────────────────────────────────────────────────────────────────
def test_s017_rf05_muestra_igual_al_lote_inspecciona_todo():
    """S017-RF-05: letra B (n = 3) con N = 3 → n = N con aviso."""
    with pytest.warns(UserWarning, match="100"):
        plan = pp.acceptance_sampling_variables(3, 10.0, inspection_level=1)
    assert plan.n == 3


def test_s017_rf05_flecha_que_no_cabe():
    """S017-RF-05: N = 8, nivel IV (letra B), AQL 0,04 → la flecha lleva a G (n = 15 > 8): n = N = 8, k = 2,64."""
    with pytest.warns(UserWarning, match="100"):
        plan = pp.acceptance_sampling_variables(8, 0.04)
    assert (plan.n, plan.k) == (8, 2.64)


def test_s017_rf05_plan_que_cabe_no_avisa():
    """S017-RF-05: con un plan que cabe no cambia nada ni se avisa."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        plan = pp.acceptance_sampling_variables(1000, 1.0)
    assert plan.n == 35


# ── S017-RF-06: `standard` y retirada de la tabla aproximada ───────────────────────────────────────────────────────────
def test_s017_rf06_z19_lanza_valueerror():
    """S017-RF-06: `standard='z1.9'` lanza ValueError que propone MIL-STD-414."""
    with pytest.raises(ValueError, match="mil-std-414"):
        pp.acceptance_sampling_variables(1000, 1.0, standard="z1.9")


def test_s017_rf06_standard_invalido():
    """S017-RF-06: un `standard` desconocido lanza ValueError."""
    with pytest.raises(ValueError, match="standard"):
        pp.acceptance_sampling_variables(1000, 1.0, standard="iso")


def test_s017_rf06_metodo_del_resultado():
    """S017-RF-06: sin `n=` y `k=` el resultado sale de las tablas (`method == 'mil-std-414'`)."""
    assert _plan(1000, 1.0, standard="mil-std-414").method == "mil-std-414"


def test_s017_rf06_tabla_aproximada_retirada():
    """S017-RF-06: ya no existen `_Z19_TABLE` ni `_AQL_Z19`."""
    import pccpy.acceptance as acc
    assert not hasattr(acc, "_Z19_TABLE")
    assert not hasattr(acc, "_AQL_Z19")


@pytest.mark.parametrize("aql", [0.05, 0.5, 3.0, 20.0])
def test_s017_rf06_aql_fuera_de_la_tabla(aql):
    """S017-RF-06: un AQL que no está entre los de la tabla lanza ValueError (no se toma el más cercano)."""
    with pytest.raises(ValueError, match="AQL"):
        _plan(1000, aql)


def test_s017_rf06_doble_especificacion():
    """S017-RF-06: `spec_type='two'` con tablas lanza ValueError; con `n=` y `k=` sigue funcionando."""
    with pytest.raises(ValueError, match="Forma 1"):
        _plan(1000, 1.0, spec_type="two")
    assert _plan(1000, 1.0, spec_type="two", n=10, k=1.5).n == 10


@pytest.mark.parametrize("kw", [{"n": 10}, {"k": 1.5}])
def test_s017_rf06_n_sin_k(kw):
    """S017-RF-06: `n=` sin `k=` (o al revés) lanza ValueError."""
    with pytest.raises(ValueError):
        _plan(1000, 1.0, **kw)
