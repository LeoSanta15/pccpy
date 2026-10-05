"""Fase I iterativa: ``phase_one`` excluye los puntos con señal, recalcula y congela los límites para la Fase II."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

import pccpy as pp


def _x(n=60, atipicos=(10, 33), salto=15.0, semilla=2):
    rng = np.random.default_rng(semilla)
    x = rng.normal(100, 2, n)
    for i in atipicos:
        if i < n:
            x[i] += salto
    return x


# ── I-MR ─────────────────────────────────────────────────────────────────────

def test_excluye_los_atipicos_y_converge():
    r = pp.phase_one(pp.imr_chart, _x(), tests=(1,))
    assert r.converged and r.reason == "in_control"
    assert r.excluded.tolist() == [10, 33]
    assert r.kept.size == 58 and r.n_original == 60
    assert r.chart.panels[0].values.size == 58


def test_la_carta_final_es_la_de_los_datos_conservados():
    x = _x()
    r = pp.phase_one(pp.imr_chart, x, tests=(1,))
    directa = pp.imr_chart(x[r.kept], tests=(1,))
    for a, b in zip(r.chart.panels, directa.panels):
        np.testing.assert_array_equal(a.values, b.values)
        np.testing.assert_array_equal(a.ucl, b.ucl)
        np.testing.assert_array_equal(a.lcl, b.lcl)


def test_los_limites_congelados_son_los_de_la_carta_final():
    x = _x()
    r = pp.phase_one(pp.imr_chart, x, tests=(1,))
    p = r.chart.params[0]
    assert r.limits == {"mu": p["media"], "sigma": p["sigma"]}
    fase2 = r.phase2(x[r.kept], tests=(1,))                       # los mismos datos con límites congelados
    np.testing.assert_allclose(fase2.panels[0].ucl, r.chart.panels[0].ucl)
    np.testing.assert_allclose(fase2.panels[0].lcl, r.chart.panels[0].lcl)


def test_la_fase_ii_detecta_un_cambio_con_los_limites_de_la_fase_i():
    rng = np.random.default_rng(11)
    r = pp.phase_one(pp.imr_chart, _x(), tests=(1,))
    nuevos = rng.normal(100, 2, 25)
    nuevos[18:] += 8
    c = r.phase2(nuevos)
    assert c.panels[0].center[0] == pytest.approx(r.limits["mu"])
    assert 18 in set(c.violations(stable=True).query("panel == 'I'")["point"] - 1) or (c.violations(stable=True)["point"].min() >= 19)
    assert not c.in_control
    # sin cambio, los datos nuevos quedan dentro
    assert pp.phase_one(pp.imr_chart, _x(), tests=(1,)).phase2(rng.normal(100, 2, 25)).in_control


def test_la_fase_ii_no_reutiliza_n_ni_los_argumentos_de_datos_de_la_fase_i():
    d = np.random.default_rng(1).binomial(200, 0.05, 40)
    d[7] = 40
    r = pp.phase_one(pp.p_chart, d, n=np.full(40, 200))
    nueva = r.phase2(np.array([8, 9, 30]), n=200)             # otro número de puntos y otro n
    assert nueva.panels[0].values.size == 3 and nueva.panels[0].center[0] == pytest.approx(r.limits["p"])


def test_el_historial_registra_cada_pasada():
    r = pp.phase_one(pp.imr_chart, _x(), tests=(1, 2, 3), exclude_panels=("I", "MR"))
    assert [h.iteration for h in r.history] == list(range(len(r.history)))
    puntos = [h.n_points for h in r.history]
    assert puntos[0] == 60 and puntos == sorted(puntos, reverse=True)
    assert r.history[-1].flagged.size == 0
    f = r.to_frame(stable=True)
    assert list(f.columns) == ["iteration", "n_points", "n_flagged", "center", "sigma"]
    assert f["n_points"].tolist() == puntos
    assert list(r.to_frame().columns) == ["iteración", "puntos", "señales", "centro", "sigma"]


def test_por_defecto_en_imr_solo_cuenta_el_panel_i():
    x = _x()
    solo_i = pp.phase_one(pp.imr_chart, x, tests=(1,))
    todos = pp.phase_one(pp.imr_chart, x, tests=(1,), exclude_panels=("I", "MR"))
    assert solo_i.excluded.size < todos.excluded.size                # el vecino de un atípico dispara el MR
    assert set(solo_i.excluded) <= set(todos.excluded)


def test_exclude_tests_limita_las_pruebas_que_excluyen():
    rng = np.random.default_rng(2)
    x = rng.normal(100, 2, 60)
    x[45] += 20                                                      # prueba 1
    x[10:20] = 100 + np.abs(rng.normal(0, 0.5, 10)) + 0.6            # racha del mismo lado: prueba 2
    todas = pp.phase_one(pp.imr_chart, x, tests=(1, 2), min_points=10, max_excluded=0.9)
    solo1 = pp.phase_one(pp.imr_chart, x, tests=(1, 2), exclude_tests=1, min_points=10, max_excluded=0.9)
    assert solo1.excluded.tolist() == [45]
    assert set(solo1.excluded) < set(todas.excluded) and {18, 19} <= set(todas.excluded)


def test_un_proceso_ya_estable_no_excluye_nada():
    r = pp.phase_one(pp.imr_chart, _x(atipicos=()), tests=(1,))
    assert r.converged and r.excluded.size == 0 and len(r.history) == 1
    assert "Fase I: carta I-MR" in r.summary()


# ── subgrupos y atributos ────────────────────────────────────────────────────

def _subgrupos(filas=30, malo=(4,), salto=6.0, semilla=3):
    rng = np.random.default_rng(semilla)
    g = rng.normal(10, 1, (filas, 5))
    for i in malo:
        g[i] += salto
    return g


@pytest.mark.parametrize("funcion", [pp.xbar_r_chart, pp.xbar_s_chart])
def test_cartas_de_subgrupos_excluyen_subgrupos_completos(funcion):
    g = _subgrupos()
    r = pp.phase_one(funcion, g, tests=(1,))
    assert r.converged and r.excluded.tolist() == [4]
    assert r.chart.panels[0].values.size == 29
    assert set(r.limits) == {"mu", "sigma"}


def test_subgrupos_desde_un_vector_con_subgroup_size_y_con_fechas():
    g = _subgrupos(malo=(6,))
    s = pd.Series(g.ravel(), index=pd.date_range("2026-01-01", periods=g.size, freq="h"))
    r = pp.phase_one(pp.xbar_r_chart, s, subgroup_size=5, tests=(1,))
    assert r.excluded.tolist() == [6]
    assert [pd.Timestamp(v) for v in r.excluded_labels] == [s.index[30]]
    assert "(2026-01-02 06:00)" in r.summary()
    assert r.chart.labels is not None and len(r.chart.labels) == 29


def test_el_subgrupo_incompleto_final_no_entra_en_la_fase_i():
    g = _subgrupos(filas=20, malo=())
    x = np.append(g.ravel(), [10.0, 10.2, 9.9])                      # 103 datos: 20 subgrupos de 5 y 3 sobrantes
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = pp.phase_one(pp.xbar_r_chart, x, subgroup_size=5, tests=(1,))
    assert r.n_original == 20


def test_cartas_de_atributos_con_n_variable():
    rng = np.random.default_rng(5)
    n = rng.integers(150, 250, 40)
    d = rng.binomial(n, 0.05)
    d[7] = int(n[7] * 0.5)
    r = pp.phase_one(pp.p_chart, d, n=n)
    assert r.converged and 7 in r.excluded
    directa = pp.p_chart(d[r.kept], n[r.kept])
    np.testing.assert_allclose(r.chart.panels[0].ucl, directa.panels[0].ucl)
    assert r.limits["p"] == pytest.approx(r.chart.params[0]["centro"])


@pytest.mark.parametrize(("funcion", "kw", "clave"), [
    (pp.np_chart, {"n": 200}, "p"), (pp.c_chart, {}, "c"), (pp.u_chart, {"n": 2.0}, "u"),
])
def test_np_c_y_u(funcion, kw, clave):
    rng = np.random.default_rng(6)
    d = rng.binomial(200, 0.05, 40) if funcion is pp.np_chart else rng.poisson(6, 40)
    d[9] = d[9] * 4 + 20
    r = pp.phase_one(funcion, d, **kw)
    assert 9 in r.excluded and clave in r.limits
    fase2 = r.phase2(d[:5], **kw)
    assert fase2.panels[0].center[0] == pytest.approx(r.chart.panels[0].center[0])


# ── fechas ───────────────────────────────────────────────────────────────────

def test_con_una_serie_con_fechas_el_resultado_conserva_las_fechas():
    x = _x()
    s = pd.Series(x, index=pd.date_range("2026-03-01", periods=60, freq="D"))
    r = pp.phase_one(pp.imr_chart, s, tests=(1,))
    assert [pd.Timestamp(v) for v in r.excluded_labels] == [s.index[10], s.index[33]]
    assert len(r.chart.labels) == 58 and pd.Timestamp(r.chart.labels[10]) == s.index[11]
    assert "11 (2026-03-11)" in r.summary()
    fase2 = r.phase2(s.iloc[:10])
    assert fase2.labels is not None


# ── salvaguardas ─────────────────────────────────────────────────────────────

def test_max_iterations_cero_no_excluye_y_avisa():
    with pytest.warns(UserWarning, match="no convergió"):
        r = pp.phase_one(pp.imr_chart, _x(), tests=(1,), max_iterations=0)
    assert not r.converged and r.reason == "max_iterations" and r.excluded.size == 0
    assert "NO convergió" in r.summary()


def test_min_points_detiene_antes_de_dejar_pocos_puntos():
    with pytest.warns(UserWarning):
        r = pp.phase_one(pp.imr_chart, _x(n=24), tests=(1,), min_points=24)
    assert not r.converged and r.reason == "min_points" and r.excluded.size == 0


def test_max_excluded_detiene_un_proceso_inestable():
    with pytest.warns(UserWarning):
        r = pp.phase_one(pp.imr_chart, _x(), tests=(1,), max_excluded=0.01)
    assert not r.converged and r.reason == "too_many_excluded" and r.excluded.size == 0


@pytest.mark.parametrize(("llamada", "mensaje"), [
    (lambda: pp.phase_one(pp.ewma_chart, _x()), "no está soportada"),
    (lambda: pp.phase_one(pp.imr_chart, _x(), tests=None), "al menos una prueba"),
    (lambda: pp.phase_one(pp.imr_chart, _x(), stages=["a"] * 60), "no admite 'stages'"),
    (lambda: pp.phase_one(pp.imr_chart, _x(n=10)), "al menos 20 puntos"),
    (lambda: pp.phase_one(pp.imr_chart, np.append(_x(), np.nan)), "valores faltantes"),
    (lambda: pp.phase_one(pp.imr_chart, _x(), max_excluded=0), "'max_excluded'"),
])
def test_errores_en_espanol(llamada, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        llamada()


def test_errores_en_ingles():
    with pp.language("en"):
        with pytest.raises(ValueError, match="not supported for this chart"):
            pp.phase_one(pp.ewma_chart, _x())
        with pytest.raises(ValueError, match="at least 20 points"):
            pp.phase_one(pp.imr_chart, _x(n=10))


# ── resumen e idioma ─────────────────────────────────────────────────────────

def test_resumen_en_espanol_e_ingles():
    r = pp.phase_one(pp.imr_chart, _x(), tests=(1,))
    es = r.summary()
    assert "Puntos: 60 → 58 (excluidos: 2)" in es and "Puntos excluidos: 11, 34" in es and "Límites congelados" in es
    with pp.language("en"):
        en = r.summary()
    assert "Points: 60 → 58 (excluded: 2)" in en and "Excluded points: 11, 34" in en and "Limits frozen for Phase II" in en
    assert [l.count("{") for l in es.splitlines()] == [0] * len(es.splitlines())
    assert len(es.splitlines()) == len(en.splitlines())


def test_el_resumen_en_ingles_no_tiene_palabras_en_espanol():
    import re

    with pp.language("en"):
        r = pp.phase_one(pp.imr_chart, _x(), tests=(1,))
        texto = r.summary() + " ".join(map(str, r.to_frame().columns))
        with pytest.warns(UserWarning) as avisos:
            r2 = pp.phase_one(pp.imr_chart, _x(), tests=(1,), max_iterations=0)
        texto += r2.summary() + " ".join(str(a.message) for a in avisos)
    palabras = {p.lower() for p in re.findall(r"[A-Za-zÁ-ú]+", texto)}
    assert not palabras & {"puntos", "pasada", "fase", "límites", "resultado", "excluidos", "carta", "iteración", "señales"}


def test_las_claves_estables_del_historial_no_cambian_con_el_idioma():
    r = pp.phase_one(pp.imr_chart, _x(), tests=(1,))
    with pp.language("en"):
        en = r.to_frame(stable=True)
        assert list(r.to_frame().columns) == ["iteration", "points", "signals", "center", "sigma"]
    assert r.to_frame(stable=True).equals(en)
