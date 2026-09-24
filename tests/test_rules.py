import numpy as np
import pytest

from pccpy import rules


def idx(a):
    return list(map(int, a))


def test_test1():
    z = np.array([0, 3.5, -3.2, 2.9, 3.0])
    assert idx(rules.test1(z)) == [1, 2]  # 3.0 exacto no excede
    assert idx(rules.test1(z, k=2.5)) == [1, 2, 3, 4]


def test_test2_runs_same_side():
    assert idx(rules.test2(np.full(9, 0.5))) == [8]
    assert idx(rules.test2(np.full(8, 0.5))) == []
    assert idx(rules.test2(np.full(11, -0.5))) == [8, 9, 10]  # cada punto adicional
    broken = np.r_[np.full(5, 1.0), 0.0, np.full(5, 1.0)]  # un punto en la línea central rompe
    assert idx(rules.test2(broken)) == []


def test_test3_trend():
    assert idx(rules.test3(np.arange(6.0))) == [5]
    assert idx(rules.test3(np.arange(5.0))) == []
    assert idx(rules.test3(-np.arange(7.0))) == [5, 6]
    tie = np.array([1, 2, 3, 3, 4, 5, 6.0])  # el empate rompe la tendencia
    assert idx(rules.test3(tie)) == []


def test_test4_alternating():
    alt = np.array([0, 1] * 7, dtype=float)  # 14 puntos alternando
    assert idx(rules.test4(alt)) == [13]
    assert idx(rules.test4(alt[:13])) == []
    assert idx(rules.test4(np.array([0, 1] * 8, dtype=float))) == [13, 14, 15]


def test_test5_two_of_three_beyond_2sigma():
    assert idx(rules.test5(np.array([0, 2.5, 2.6]))) == [2]
    assert idx(rules.test5(np.array([2.5, 0, 2.6]))) == [2]
    assert idx(rules.test5(np.array([2.5, -2.5, 2.6]))) == [2]  # 2 de 3 del mismo lado
    assert idx(rules.test5(np.array([2.5, -2.5, -0.1]))) == []
    assert idx(rules.test5(np.array([2.5, 0, 0, 2.6]))) == []  # fuera de la ventana de 3


def test_test6_four_of_five_beyond_1sigma():
    assert idx(rules.test6(np.array([1.5, 1.5, 0, 1.5, 1.5]))) == [4]
    assert idx(rules.test6(np.array([1.5, 1.5, 0, 0, 1.5]))) == []
    assert idx(rules.test6(np.array([-1.5, -1.5, -1.5, 0, -1.5]))) == [4]


def test_test7_stratification():
    assert idx(rules.test7(np.full(15, 0.3))) == [14]
    assert idx(rules.test7(np.full(14, 0.3))) == []
    assert idx(rules.test7(np.tile([0.5, -0.5], 8))) == [14, 15]


def test_test8_mixture():
    z = np.tile([1.5, -1.5], 4)  # 8 puntos a más de 1 sigma en ambos lados
    assert idx(rules.test8(z)) == [7]
    assert idx(rules.test8(z[:7])) == []


def test_apply_tests_ignores_nan_and_uses_sigma():
    vals = np.array([np.nan, 10.0, 10.0, 16.5])
    out = rules.apply_tests(vals, np.full(4, 10.0), np.full(4, 2.0), [1])
    assert idx(out[1]) == [3]  # (16.5-10)/2 = 3.25 > 3; índice original, no el comprimido


def test_apply_tests_custom_k():
    z = np.full(7, 1.0)
    out = rules.apply_tests(z, np.zeros(7), np.ones(7), [2], {2: 7})
    assert idx(out[2]) == [6]


def test_zero_sigma_is_safe():
    out = rules.apply_tests(np.ones(5), np.ones(5), np.zeros(5), [1, 2])
    assert all(len(v) == 0 for v in out.values())


def test_normalize_tests():
    assert rules.normalize_tests("all") == tuple(range(1, 9))
    assert rules.normalize_tests(None) == ()
    assert rules.normalize_tests(3) == (3,)
    assert rules.normalize_tests([2, 1, 2]) == (1, 2)
    with pytest.raises(ValueError):
        rules.normalize_tests([9])
    with pytest.raises(ValueError):
        rules.normalize_tests("some")


def test_describe_substitutes_k():
    assert "2 de 3" in rules.describe(5)
    assert "7 puntos" in rules.describe(2, 7)
