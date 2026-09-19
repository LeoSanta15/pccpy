import math

import pytest

from spyc import c4, c5, control_chart_constants, d2, d3

# Tablas publicadas (Montgomery, Introduction to Statistical Quality Control, Apéndice VI)
N = list(range(2, 11))
D2 = [1.128, 1.693, 2.059, 2.326, 2.534, 2.704, 2.847, 2.970, 3.078]
D3 = [0.853, 0.888, 0.880, 0.864, 0.848, 0.833, 0.820, 0.808, 0.797]
C4 = [0.7979, 0.8862, 0.9213, 0.9400, 0.9515, 0.9594, 0.9650, 0.9693, 0.9727]
A2 = [1.880, 1.023, 0.729, 0.577, 0.483, 0.419, 0.373, 0.337, 0.308]
D3_LOW = [0, 0, 0, 0, 0, 0.076, 0.136, 0.184, 0.223]
D4 = [3.267, 2.574, 2.282, 2.114, 2.004, 1.924, 1.864, 1.816, 1.777]
B3 = [0, 0, 0, 0, 0.030, 0.118, 0.185, 0.239, 0.284]
B4 = [3.267, 2.568, 2.266, 2.089, 1.970, 1.882, 1.815, 1.761, 1.716]


@pytest.mark.parametrize("i,n", list(enumerate(N)))
def test_matches_published_tables(i, n):
    c = control_chart_constants(n)
    assert c["d2"] == pytest.approx(D2[i], abs=1e-3)
    assert c["d3"] == pytest.approx(D3[i], abs=1e-3)
    assert c["c4"] == pytest.approx(C4[i], abs=1e-4)
    assert c["A2"] == pytest.approx(A2[i], abs=1e-3)
    assert c["D3"] == pytest.approx(D3_LOW[i], abs=1e-3)
    assert c["D4"] == pytest.approx(D4[i], abs=1e-3)
    assert c["B3"] == pytest.approx(B3[i], abs=1e-3)
    assert c["B4"] == pytest.approx(B4[i], abs=1e-3)


def test_c5_definition_and_large_n():
    assert c5(5) == pytest.approx(math.sqrt(1 - c4(5) ** 2))
    assert c4(1000) == pytest.approx(1 - 1 / (4 * 1000), abs=1e-4)  # asintótica
    assert d2(50) > d2(25) > d2(10)


def test_invalid_n():
    with pytest.raises(ValueError):
        d2(1)
    with pytest.raises(ValueError):
        control_chart_constants(0)
