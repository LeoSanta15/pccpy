"""outlier_test: Grubbs y ESD generalizada contra valores publicados, fórmulas manuales y simulación."""
from __future__ import annotations

import warnings

import numpy as np
import pytest
from scipy import stats

import pccpy as pp

# 54 datos del ejemplo de Rosner (1983), el que usa el manual de estadística del NIST para la prueba ESD generalizada
ROSNER = np.array([
    -0.25, 0.68, 0.94, 1.15, 1.20, 1.26, 1.26, 1.34, 1.38, 1.43, 1.49, 1.49, 1.55, 1.56, 1.58, 1.65, 1.69, 1.70, 1.76,
    1.77, 1.81, 1.91, 1.94, 1.96, 1.99, 2.06, 2.09, 2.10, 2.14, 2.15, 2.23, 2.23, 2.26, 2.35, 2.37, 2.40, 2.47, 2.54,
    2.62, 2.64, 2.90, 2.92, 2.92, 2.93, 3.21, 3.26, 3.30, 3.59, 3.68, 4.30, 4.64, 5.34, 5.42, 6.01])
R_NIST = [3.118, 2.942, 3.179, 2.810, 2.815, 2.848, 2.279, 2.310, 2.101, 2.067]
LAMBDA_NIST = [3.158, 3.151, 3.143, 3.136, 3.128, 3.120, 3.111, 3.103, 3.094, 3.085]


def _g_critico(n, alpha=0.05, bilateral=True):
    """Valor crítico de Grubbs escrito aparte, a partir de la t de Student."""
    t = stats.t.ppf(1 - (alpha / (2 * n) if bilateral else alpha / n), n - 2)
    return (n - 1) / np.sqrt(n) * np.sqrt(t**2 / (n - 2 + t**2))


@pytest.mark.parametrize("n, publicado", [(3, 1.153), (5, 1.715), (10, 2.290), (20, 2.709), (30, 2.908)])
def test_critico_de_grubbs_coincide_con_la_tabla_publicada(n, publicado):
    x = np.random.default_rng(n).normal(size=n)
    paso = pp.outlier_test(x).steps.iloc[0]
    assert paso["critical"] == pytest.approx(publicado, abs=1.5e-3)
    assert paso["critical"] == pytest.approx(_g_critico(n))


def test_estadistico_de_grubbs_y_dato_marcado():
    x = np.array([1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.5, 12.5])
    r = pp.outlier_test(x)
    g = abs(12.5 - x.mean()) / x.std(ddof=1)
    assert r.steps.iloc[0]["statistic"] == pytest.approx(g)
    assert r.has_outliers and r.outlier_indices.tolist() == [12] and r.outlier_values.tolist() == [12.5]


def test_grubbs_no_marca_datos_normales_y_su_nivel_es_el_nominal():
    rng = np.random.default_rng(1)
    rep = 4000
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        marcados = sum(pp.outlier_test(rng.normal(size=10)).has_outliers for _ in range(rep))
    assert marcados / rep == pytest.approx(0.05, abs=0.012)


def test_esd_reproduce_el_ejemplo_del_nist():
    r = pp.outlier_test(ROSNER, method="esd")
    assert r.steps["statistic"].to_numpy() == pytest.approx(R_NIST, abs=2e-3)
    assert r.steps["critical"].to_numpy() == pytest.approx(LAMBDA_NIST, abs=2e-3)
    assert sorted(r.outlier_indices.tolist()) == [51, 52, 53]  # 3 atípicos: 5,34, 5,42 y 6,01
    assert r.outlier_values.tolist() == [6.01, 5.42, 5.34]


def test_esd_encuentra_dos_atipicos_que_se_enmascaran_para_grubbs():
    x = np.append(np.random.default_rng(2).normal(0, 1, 20), [5.0, 5.2])
    assert not pp.outlier_test(x).has_outliers  # enmascaramiento: el 2.º atípico infla s
    r = pp.outlier_test(x, method="esd")
    assert set(r.outlier_indices.tolist()) >= {20, 21}


def test_esd_falsos_positivos_acotados():
    rng = np.random.default_rng(3)
    rep = 1500
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        marcados = sum(pp.outlier_test(rng.normal(size=30), method="esd", max_outliers=3).has_outliers
                       for _ in range(rep))
    assert 0.025 < marcados / rep < 0.075


def test_unilateral_usa_alpha_sobre_n_y_solo_mira_un_lado():
    x = np.append(np.random.default_rng(4).normal(0, 1, 20), [-6.0])
    assert pp.outlier_test(x, sides="lower").has_outliers
    assert not pp.outlier_test(x, sides="upper").has_outliers
    paso = pp.outlier_test(x, sides="lower").steps.iloc[0]
    assert paso["critical"] == pytest.approx(_g_critico(21, bilateral=False))
    assert paso["critical"] < pp.outlier_test(x).steps.iloc[0]["critical"]  # unilateral: umbral más bajo


def test_los_indices_son_los_de_la_entrada_original_con_valores_no_finitos():
    x = np.array([1.2, np.nan, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.5, 12.5])
    with pytest.warns(UserWarning, match="no finito"):
        r = pp.outlier_test(x)
    assert r.outlier_indices.tolist() == [13] and r.outlier_values.tolist() == [12.5] and r.dropped == 1


def test_aviso_si_los_datos_restantes_no_son_normales():
    x = np.random.default_rng(5).exponential(2.0, 60)
    r = pp.outlier_test(x)
    assert r.normality_p < 0.05 and "no parecen normales" in r.summary()
    sano = pp.outlier_test(np.random.default_rng(6).normal(size=40))
    assert "no parecen normales" not in sano.summary()


def test_tabla_resumen_y_traduccion():
    r = pp.outlier_test(ROSNER, method="esd")
    assert list(r.to_frame(stable=True).columns) == ["step", "index", "value", "statistic", "critical", "outlier"]
    assert list(r.to_frame().columns)[0] == "paso"
    assert "ESD generalizada" in r.summary() and "Atípicos declarados" in r.summary()
    with pp.language("en"):
        assert "Generalized ESD" in r.summary() and "Declared outliers" in r.summary()
        assert list(r.to_frame().columns)[0] == "step"


@pytest.mark.parametrize("llamada, texto", [
    (lambda: pp.outlier_test([1.0, 2.0]), "al menos 3"),
    (lambda: pp.outlier_test([1.0, 2.0, 3.0], method="esd"), "al menos 4"),
    (lambda: pp.outlier_test([5.0] * 10), "constantes"),
    (lambda: pp.outlier_test([1, 2, 3, 4], method="x"), "method"),
    (lambda: pp.outlier_test([1, 2, 3, 4], sides="x"), "sides"),
    (lambda: pp.outlier_test([1, 2, 3, 4], alpha=0), "alpha"),
    (lambda: pp.outlier_test(ROSNER, method="esd", max_outliers=0), "max_outliers"),
    (lambda: pp.outlier_test(ROSNER, method="esd", max_outliers=60), "max_outliers"),
])
def test_errores(llamada, texto):
    with pytest.raises(ValueError, match=texto):
        llamada()
