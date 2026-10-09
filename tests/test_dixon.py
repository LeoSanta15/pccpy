"""Prueba de Dixon con valores críticos calculados (integral exacta bajo normalidad)."""
import warnings

import numpy as np
import pandas as pd
import pytest

import pccpy as pp
from pccpy import outliers

# Q crítico de r10 para el sospechoso mínimo o máximo, bilateral (Rorabacher, 1991; Dixon, 1951)
PUBLICADOS = {
    0.10: {3: .941, 4: .765, 5: .642, 6: .560, 7: .507, 8: .468, 9: .437, 10: .412},
    0.05: {3: .970, 4: .829, 5: .710, 6: .625, 7: .568, 8: .526, 9: .493, 10: .466},
    0.01: {3: .994, 4: .926, 5: .821, 6: .740, 7: .680, 8: .634, 9: .598, 10: .568},
}


@pytest.mark.parametrize("alfa", sorted(PUBLICADOS))
def test_r10_reproduce_las_tablas_publicadas(alfa):
    for n, publicado in PUBLICADOS[alfa].items():
        assert outliers._dixon_critico(n, "r10", alfa / 2) == pytest.approx(publicado, abs=6e-3)


@pytest.mark.parametrize(("razon", "n"), [("r10", 6), ("r11", 9), ("r21", 12), ("r22", 18)])
def test_los_criticos_calculados_dejan_la_cola_esperada_en_simulacion(razon, n):
    """Monte Carlo independiente: con el crítico unilateral α = 0,025 se supera en ≈ 2,5 % de las muestras normales."""
    k, m = outliers.DIXON_RAZONES[razon]
    crit = outliers._dixon_critico(n, razon, 0.025)
    x = np.sort(np.random.default_rng(5).normal(size=(200_000, n)), axis=1)
    q = (x[:, k] - x[:, 0]) / (x[:, n - 1 - m] - x[:, 0])
    assert (q > crit).mean() == pytest.approx(0.025, abs=0.0015)


def test_la_cola_es_1_en_cero_y_decrece():
    assert outliers._dixon_p_cola(1e-9, 8, 1, 1) == pytest.approx(1.0, abs=1e-6)
    valores = [outliers._dixon_p_cola(c, 8, 1, 1) for c in (0.2, 0.4, 0.6, 0.8)]
    assert all(a > b for a, b in zip(valores, valores[1:]))


def test_estadistico_y_decision_en_un_caso_a_mano():
    x = np.array([2.1, 2.3, 2.2, 2.4, 2.0, 2.2, 3.9])
    r = pp.outlier_test(x, method="dixon")
    assert r.ratio == "r10" and r.has_outliers and r.outlier_indices.tolist() == [6]
    fila = r.steps.iloc[0]
    assert fila["statistic"] == pytest.approx((3.9 - 2.4) / (3.9 - 2.0))
    assert fila["critical"] == pytest.approx(PUBLICADOS[0.05][7], abs=6e-3)


def test_razon_automatica_segun_n():
    rng = np.random.default_rng(1)
    elegida = {n: pp.outlier_test(rng.normal(size=n), method="dixon").ratio for n in (5, 9, 12, 20)}
    assert elegida == {5: "r10", 9: "r11", 12: "r21", 20: "r22"}


def test_lados_y_razon_explicita():
    x = np.array([-6.0, -0.4, -0.2, 0.0, 0.1, 0.3, 0.5, 0.6, 0.9, 1.0])
    assert pp.outlier_test(x, method="dixon", sides="lower").outlier_indices.tolist() == [0]
    assert not pp.outlier_test(x, method="dixon", sides="upper").has_outliers
    r = pp.outlier_test(x, method="dixon", dixon_ratio="r22")
    assert r.ratio == "r22" and r.outlier_indices.tolist() == [0]
    assert pp.outlier_test(x, method="dixon", sides="two").steps.iloc[0]["index"] == 0


def test_dos_atipicos_del_mismo_lado_enmascaran_r10_pero_no_r21():
    x = np.array([5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 8.8, 9.0])
    assert not pp.outlier_test(x, method="dixon", dixon_ratio="r10", sides="upper").has_outliers
    assert pp.outlier_test(x, method="dixon", dixon_ratio="r21", sides="upper").has_outliers


def test_los_indices_son_los_de_la_entrada_original_con_nan():
    x = np.array([2.1, np.nan, 2.3, 2.2, 2.4, 2.0, 2.2, 3.9])
    with pytest.warns(UserWarning, match="no finito"):
        r = pp.outlier_test(x, method="dixon")
    assert r.outlier_indices.tolist() == [7] and r.n == 7


def test_errores_y_avisos():
    with pytest.raises(ValueError, match="al menos"):
        pp.outlier_test([1.0, 2.0], method="dixon")
    with pytest.raises(ValueError, match="al menos"):
        pp.outlier_test([1.0, 2.0, 3.0, 4.0], method="dixon", dixon_ratio="r22")
    with pytest.raises(ValueError, match="dixon_ratio"):
        pp.outlier_test([1.0, 2.0, 3.0, 4.0], method="dixon", dixon_ratio="r99")
    with pytest.raises(ValueError, match="repetidos"):
        pp.outlier_test([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 5.0], method="dixon", dixon_ratio="r11")
    with pytest.raises(ValueError, match="como máximo"):
        pp.outlier_test(np.random.default_rng(0).normal(size=101), method="dixon")
    with pytest.warns(UserWarning, match="muestras pequeñas"):
        pp.outlier_test(np.random.default_rng(0).normal(size=40), method="dixon")


def test_to_frame_y_summary_nombran_la_razon():
    r = pp.outlier_test([2.1, 2.3, 2.2, 2.4, 2.0, 2.2, 3.9], method="dixon")
    assert "Dixon (r10)" in r.summary()
    assert isinstance(r.to_frame(stable=True), pd.DataFrame) and r.to_frame(stable=True).shape[0] == 1


def test_tasa_de_falsos_positivos_bilateral_no_supera_alfa():
    rng = np.random.default_rng(8)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tasa = np.mean([pp.outlier_test(rng.normal(size=8), method="dixon").has_outliers for _ in range(4000)])
    assert tasa <= 0.05 + 0.012  # α/2 por cola es ligeramente conservador
