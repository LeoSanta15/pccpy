"""Ajuste robusto de la transformación: medcouple, diagrama de cajas ajustado y ``robust=`` / ``robust_fit=``."""
import numpy as np
import pytest

import pccpy as pp
from pccpy.transforms import adjusted_boxplot_mask, medcouple

pytestmark = pytest.mark.filterwarnings("ignore:La transformación cambió mucho", "ignore:La Fase I no convergió")


def _medcouple_lento(v):
    v = np.sort(v)
    m = np.median(v)
    h = [((b - m) - (m - a)) / (b - a) for a in v[v <= m] for b in v[v >= m] if b > a]
    return float(np.median(h))


@pytest.mark.parametrize("semilla", range(5))
def test_medcouple_coincide_con_la_definicion(semilla):
    x = np.random.default_rng(semilla).lognormal(0, 0.8, 60)
    assert medcouple(x) == pytest.approx(_medcouple_lento(x), abs=1e-12)


def test_medcouple_signo_y_simetria():
    rng = np.random.default_rng(1)
    assert abs(medcouple(rng.normal(0, 1, 2000))) < 0.05
    assert medcouple(rng.exponential(1, 2000)) > 0.15
    assert medcouple(-rng.exponential(1, 2000)) < -0.15
    assert medcouple(np.array([5.0, 5.0, 5.0, 5.0])) == 0.0  # sin pares válidos


def test_caja_ajustada_no_marca_la_cola_larga_natural_pero_si_un_atipico_lejano():
    rng = np.random.default_rng(2)
    x = rng.lognormal(1, 0.6, 500)
    assert (~adjusted_boxplot_mask(x)).mean() < 0.03  # la caja normal marcaría mucho más en una lognormal
    x[0] = x.max() * 20
    assert not adjusted_boxplot_mask(x)[0]


@pytest.mark.parametrize("metodo", ["boxcox", "yeo-johnson", "johnson"])
def test_robust_no_cambia_el_ajuste_con_datos_limpios_y_si_con_atipicos(metodo):
    rng = np.random.default_rng(3)
    x = rng.lognormal(1, 0.6, 120)
    limpio = pp.fit_transformation(x, metodo).forward(x)
    robusto = pp.fit_transformation(x, metodo, robust=True).forward(x)
    assert np.corrcoef(limpio, robusto)[0, 1] > 0.99
    x[[5, 50]] *= 25
    sin = pp.fit_transformation(x, metodo)
    con = pp.fit_transformation(x, metodo, robust=True)
    ref = pp.fit_transformation(np.delete(x, [5, 50]), metodo)
    if metodo != "johnson":  # lambda: el ajuste robusto queda mucho más cerca del de los datos sin atípicos
        assert abs(con.params["lambda"] - ref.params["lambda"]) < abs(sin.params["lambda"] - ref.params["lambda"]) / 1.5


def test_si_el_recorte_quitaria_demasiado_se_ajusta_con_todos():
    rng = np.random.default_rng(4)
    x = np.concatenate([rng.normal(0, 1, 30), rng.normal(100, 1, 30)])  # dos poblaciones: la caja ajustada recorta mucho
    a = pp.fit_transformation(x, "yeo-johnson", robust=True)
    b = pp.fit_transformation(x, "yeo-johnson")
    kept = adjusted_boxplot_mask(x).mean()
    if kept < 0.75:
        assert a.params == b.params


def _recuperacion(robust_fit, gen, k=20, repeticiones=40):
    rng = np.random.default_rng(11)
    ok = 0
    for _ in range(repeticiones):
        x = gen(rng, 100)
        x[[20, 70]] *= k
        r = pp.phase_one(pp.imr_chart, x, transform="yeo-johnson", tests=(1,), robust_fit=robust_fit)
        ok += {20, 70} <= set(r.excluded)
    return ok / repeticiones


def test_simulacion_el_ajuste_robusto_recupera_los_puntos_contaminados():
    lognormal = lambda r, n: r.lognormal(1, 0.6, n)  # noqa: E731
    weibull = lambda r, n: r.weibull(1.5, n) * 10  # noqa: E731
    con, sin = _recuperacion(True, lognormal), _recuperacion(False, lognormal)
    assert con >= 0.6 and con > sin + 0.3  # la mejora grande está en la lognormal
    con, sin = _recuperacion(True, weibull), _recuperacion(False, weibull)
    assert con >= 0.7 and con >= sin


def test_la_tasa_de_falsas_alarmas_de_la_fase_ii_sigue_cerca_de_la_nominal():
    rng = np.random.default_rng(12)
    tasas = []
    for _ in range(40):
        x = rng.lognormal(1, 0.6, 100)
        nuevos = rng.lognormal(1, 0.6, 2000)
        r = pp.phase_one(pp.imr_chart, x, transform="yeo-johnson", tests=(1,))
        tasas.append(r.phase2(nuevos, tests=(1,)).panels[0].flagged.size / 2000)
    assert np.mean(tasas) < 0.006


def test_robust_fit_no_afecta_a_una_transformacion_ya_ajustada():
    x = np.random.default_rng(7).gamma(4.0, 2.0, 90) + 1.0
    t = pp.fit_transformation(x, "boxcox")
    a = pp.phase_one(pp.imr_chart, x, transform=t, tests=(1,), robust_fit=True)
    b = pp.phase_one(pp.imr_chart, x, transform=t, tests=(1,), robust_fit=False)
    assert a.limits == b.limits and a.excluded.tolist() == b.excluded.tolist()
