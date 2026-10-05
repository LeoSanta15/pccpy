"""Capacidad para atributos: se contrasta con referencias independientes (SciPy, definiciones, simulación)."""
from __future__ import annotations

import math

import matplotlib
import numpy as np
import pytest
from scipy import stats

import pccpy as pp

matplotlib.use("Agg")

D = [3, 5, 2, 4, 6, 1, 3, 5]
N = [200, 180, 220, 200, 210, 190, 200, 200]


@pytest.fixture(autouse=True)
def _cerrar():
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


def test_binomial_estimacion_e_intervalo_exacto():
    r = pp.capability_binomial(D, N)
    tot_d, tot_n = sum(D), sum(N)
    assert r.p_bar == pytest.approx(tot_d / tot_n)
    ref = stats.binomtest(tot_d, tot_n).proportion_ci(confidence_level=0.95, method="exact")
    assert r.p_ci == pytest.approx((ref.low, ref.high), abs=1e-9)
    assert r.ppm == pytest.approx(1e6 * tot_d / tot_n)
    assert r.z == pytest.approx(stats.norm.ppf(1 - tot_d / tot_n))
    # el Z más alto corresponde al límite inferior de p
    assert r.z_ci[0] < r.z < r.z_ci[1]
    assert r.z_ci == pytest.approx((stats.norm.isf(ref.high), stats.norm.isf(ref.low)), abs=1e-8)


def test_binomial_homogeneidad_manual():
    r = pp.capability_binomial(D, N)
    p = sum(D) / sum(N)
    chi2 = sum((d - n * p) ** 2 / (n * p * (1 - p)) for d, n in zip(D, N))
    assert r.chi2 == pytest.approx(chi2) and r.chi2_df == 7
    assert r.p_value_homogeneity == pytest.approx(stats.chi2.sf(chi2, 7))
    assert r.homogeneous


def test_binomial_detecta_p_no_constante():
    r = pp.capability_binomial([1, 2, 1, 30, 2, 1, 25, 2], [200] * 8)
    assert not r.homogeneous and "Aviso" in r.summary()
    with pp.language("en"):
        assert "Warning" in r.summary()


def test_binomial_cero_defectuosas_y_todas():
    r = pp.capability_binomial([0, 0, 0], 50)
    assert r.p_bar == 0 and r.p_ci[0] == 0 and r.p_ci[1] == pytest.approx(1 - 0.025 ** (1 / 150))
    assert math.isinf(r.z) and math.isnan(r.p_value_homogeneity)
    assert pp.capability_binomial([10], 10).p_ci[1] == 1


def test_binomial_cobertura_por_simulacion():
    rng = np.random.default_rng(7)
    p, n, rep = 0.03, 400, 1500
    dentro = 0
    for d in rng.binomial(n, p, rep):
        lo, hi = pp.capability_binomial([d], n).p_ci
        dentro += lo <= p <= hi
    assert dentro / rep >= 0.95  # Clopper-Pearson es conservador


def test_poisson_dpu_e_intervalo_garwood():
    d, u = [3, 5, 2, 4, 6, 1, 3, 5], [10, 12, 10, 9, 11, 10, 10, 12]
    r = pp.capability_poisson(d, u)
    D_, U = sum(d), sum(u)
    assert r.dpu == pytest.approx(D_ / U)
    lo = stats.gamma.ppf(0.025, D_) / U  # Garwood = cuantiles de la gamma
    hi = stats.gamma.ppf(0.975, D_ + 1) / U
    assert r.dpu_ci == pytest.approx((lo, hi), rel=1e-9)
    mu = D_ / U
    chi2 = sum((x - w * mu) ** 2 / (w * mu) for x, w in zip(d, u))
    assert r.chi2 == pytest.approx(chi2) and r.p_value_homogeneity == pytest.approx(stats.chi2.sf(chi2, 7))


def test_poisson_oportunidades_dpmo_y_z():
    r = pp.capability_poisson([3, 5, 2, 4], units=10, opportunities=20)
    dpo = 14 / 40 / 20
    assert r.dpmo == pytest.approx(1e6 * dpo) and r.z == pytest.approx(stats.norm.isf(dpo))
    assert "dpmo" in r.to_frame(stable=True).index
    assert "dpmo" not in pp.capability_poisson([3, 5], 10).to_frame(stable=True).index


def test_poisson_cero_defectos():
    r = pp.capability_poisson([0, 0, 0], 5)
    assert r.dpu == 0 and r.dpu_ci[0] == 0 and r.dpu_ci[1] == pytest.approx(-math.log(0.025) / 15, rel=0.2)
    assert r.dpu_ci[1] == pytest.approx(stats.chi2.ppf(0.975, 2) / 30)


@pytest.mark.parametrize("llamada, texto", [
    (lambda: pp.capability_binomial([5, 3], 4), "más defectuosas"),
    (lambda: pp.capability_binomial([-1, 3], 10), "no negativos"),
    (lambda: pp.capability_binomial([1.5], 10), "no negativos"),
    (lambda: pp.capability_binomial([1, 2], [10, 10, 10]), "misma longitud"),
    (lambda: pp.capability_binomial([1], 10, confidence=1.5), "confidence"),
    (lambda: pp.capability_poisson([1], 0), "positivos"),
    (lambda: pp.capability_poisson([1], 1, opportunities=0), "oportunities|positivo"),
])
def test_errores(llamada, texto):
    with pytest.raises(ValueError, match=texto):
        llamada()


def test_frame_estable_y_resumen_en_ingles():
    r = pp.capability_binomial(D, N)
    estable = r.to_frame(stable=True)
    assert {"p_bar_pct", "ppm", "z", "chi2", "p_value_homogeneity"} <= set(estable.index)
    with pp.language("en"):
        assert "binomial data" in r.summary() and "% defective" in r.summary()
        assert r.to_frame().index[3].startswith("% defective")
    assert "datos binomiales" in r.summary()
    assert estable.loc["p_bar_pct", "value"] == pytest.approx(100 * sum(D) / sum(N))


def test_graficos_y_excel(tmp_path):
    for r in (pp.capability_binomial(D, N), pp.capability_poisson(D, 10)):
        fig = r.plot()
        assert len(fig.axes) == 2
        r.save_plot(str(tmp_path / "g.png"))
    from importlib.util import find_spec

    if find_spec("openpyxl"):
        pp.capability_binomial(D, N).to_excel(tmp_path / "c.xlsx")
        assert (tmp_path / "c.xlsx").exists()
