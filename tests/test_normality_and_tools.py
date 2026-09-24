import numpy as np
import pytest

import pccpy
from pccpy._data import stage_slices, to_subgroups
from pccpy.normality import anderson_darling_pvalue


def test_anderson_darling_matches_statsmodels_reference():
    # Valores obtenidos con statsmodels.stats.diagnostic.normal_ad (implementación independiente)
    x1 = [2.1, 2.5, 2.8, 3.0, 3.1, 3.3, 3.9, 4.2, 5.0, 6.7]
    r = pccpy.normality_test(x1)
    assert r.statistic == pytest.approx(0.44640694391334357, rel=1e-9)
    assert r.p_value == pytest.approx(0.22091816577681211, rel=1e-9)
    x2 = [9.8, 10.1, 10.0, 9.9, 10.2, 10.05, 9.95, 10.15, 9.85, 10.0, 10.1, 9.9]
    r2 = pccpy.normality_test(x2)
    assert r2.statistic == pytest.approx(0.1704881845086028, rel=1e-9)
    assert r2.p_value == pytest.approx(0.9096866682225935, rel=1e-9)


def test_pvalue_branches_are_continuous_and_decreasing():
    a2 = np.linspace(0.05, 3, 300)
    p = np.array([anderson_darling_pvalue(a, 50) for a in a2])
    assert np.all(np.diff(p) < 1e-3)  # monótona (tolerancia por empalme de tramos)
    assert p[0] > 0.9 and p[-1] < 1e-4


def test_detects_non_normal_and_accepts_normal():
    rng = np.random.default_rng(3)
    assert pccpy.normality_test(rng.exponential(1, 200)).reject()
    assert not pccpy.normality_test(rng.normal(0, 1, 200)).reject()
    assert pccpy.normality_test(rng.exponential(1, 100), "shapiro").reject()
    assert pccpy.normality_test(rng.exponential(1, 100), "dagostino").reject()
    assert "Anderson-Darling" in str(pccpy.normality_test(rng.normal(0, 1, 30)))


def test_normality_errors():
    with pytest.raises(ValueError):
        pccpy.normality_test([1, 2])
    with pytest.raises(ValueError):
        pccpy.normality_test([5.0] * 10)
    with pytest.raises(ValueError):
        pccpy.normality_test([1, 2, 3, 4, 5], "foo")


def test_pareto_from_raw_and_counts():
    raw = ["a", "b", "a", "c", "a", "b"]
    t = pccpy.pareto(raw)
    assert list(t["categoría"]) == ["a", "b", "c"] and list(t["conteo"]) == [3, 2, 1]
    assert t["acumulado"].iloc[-1] == pytest.approx(100)
    t2 = pccpy.pareto(["x", "y", "z", "w"], [50, 30, 3, 2], other_below=5)
    assert list(t2["categoría"]) == ["x", "y", "Otros"] and t2["conteo"].iloc[-1] == 5
    assert pccpy.pareto(["x", "x", "y"], [1, 2, 4])["categoría"].iloc[0] == "y"  # agrupa repetidos
    with pytest.raises(ValueError):
        pccpy.pareto(["a", "b"], [1])
    with pytest.raises(ValueError):
        pccpy.pareto(["a"], [-1])


def test_to_subgroups_variants_and_errors():
    v = np.arange(12.0)
    assert to_subgroups(v, subgroup_size=4).shape == (3, 4)
    m = to_subgroups(v[:7], subgroup=[1, 1, 1, 2, 2, 3, 3])
    assert m.shape == (3, 3) and np.isnan(m[1, 2])
    with pytest.raises(ValueError):
        to_subgroups(v, subgroup_size=5)  # 12 no divisible por 5
    with pytest.raises(ValueError):
        to_subgroups(v)
    with pytest.raises(ValueError):
        to_subgroups(np.ones((3, 3)), subgroup_size=3)


def test_stage_slices():
    s = stage_slices(6, ["a", "a", "b", "b", "b", "c"])
    assert [lab for lab, _ in s] == ["a", "b", "c"] and list(s[1][1]) == [2, 3, 4]
    assert stage_slices(4, None)[0][0] == 1
