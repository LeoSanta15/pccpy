"""EWMA y CUSUM de atributos (P, C, U): se contrastan con un cálculo manual independiente."""
from __future__ import annotations

import numpy as np
import pytest

import pccpy as pp

D = np.array([4, 6, 5, 3, 7, 5, 4, 6, 12, 14, 13, 15, 12, 11], dtype=float)
N = np.array([100, 120, 100, 90, 110, 100, 100, 120, 100, 100, 110, 100, 90, 100], dtype=float)


def _ewma_manual(y, centro, sigma, lam, k):
    z, prev = [], centro
    for v in y:
        prev = lam * v + (1 - lam) * prev
        z.append(prev)
    z = np.array(z)
    i = np.arange(1, len(y) + 1)
    s = sigma * np.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * i)))
    return z, centro + k * s, np.maximum(0, centro - k * s)


def _cusum_manual(z, k):
    cp = cm = 0.0
    up, lo = [], []
    for v in z:
        cp = max(0, v - k + cp)
        cm = max(0, -v - k + cm)
        up.append(cp)
        lo.append(-cm)
    return np.array(up), np.array(lo)


def test_ewma_p_contra_formula_manual():
    ch = pp.ewma_p_chart(D, N)
    p = D.sum() / N.sum()
    z, ucl, lcl = _ewma_manual(D / N, p, np.sqrt(p * (1 - p) / N), 0.2, 3.0)
    pan = ch["EWMA-P"]
    assert np.allclose(pan.values, z) and np.allclose(pan.ucl, ucl) and np.allclose(pan.lcl, lcl)


def test_ewma_c_y_u_contra_formula_manual():
    c = pp.ewma_c_chart(D, weight=0.3, k=2.5)
    z, ucl, lcl = _ewma_manual(D, D.mean(), np.full(len(D), np.sqrt(D.mean())), 0.3, 2.5)
    assert np.allclose(c["EWMA-C"].values, z) and np.allclose(c["EWMA-C"].ucl, ucl)
    u = pp.ewma_u_chart(D, N)
    mu = D.sum() / N.sum()
    z, ucl, lcl = _ewma_manual(D / N, mu, np.sqrt(mu / N), 0.2, 3.0)
    assert np.allclose(u["EWMA-U"].values, z) and np.allclose(u["EWMA-U"].lcl, lcl)


def test_ewma_detecta_el_desplazamiento_y_parametros_historicos():
    ch = pp.ewma_p_chart(D, N, p=0.05)
    marcados = ch["EWMA-P"].violations[1]
    assert len(marcados) > 0 and marcados.min() >= 8
    assert pp.ewma_c_chart(D, c=5.0)["EWMA-C"].center[0] == 5.0


def test_cusum_contra_formula_manual():
    p = D.sum() / N.sum()
    z = (D / N - p) / np.sqrt(p * (1 - p) / N)
    up, lo = _cusum_manual(z, 0.5)
    ch = pp.cusum_p_chart(D, N)
    pan = ch["CUSUM-P"]
    assert np.allclose(pan.values, up) and np.allclose(pan.secondary, lo)
    assert np.allclose(pan.ucl, 4.0) and np.allclose(pan.lcl, -4.0)
    assert len(pan.violations[1]) > 0


def test_cusum_c_y_u():
    zc = (D - D.mean()) / np.sqrt(D.mean())
    up, lo = _cusum_manual(zc, 0.25)
    pan = pp.cusum_c_chart(D, h=5, k=0.25)["CUSUM-C"]
    assert np.allclose(pan.values, up) and np.allclose(pan.ucl, 5.0)
    mu = D.sum() / N.sum()
    up, lo = _cusum_manual((D / N - mu) / np.sqrt(mu / N), 0.5)
    pan = pp.cusum_u_chart(D, N, u=mu)["CUSUM-U"]
    assert np.allclose(pan.values, up) and np.allclose(pan.secondary, lo)


def test_proceso_estable_no_da_senal():
    rng = np.random.default_rng(3)
    d = rng.poisson(5, 60).astype(float)
    assert len(pp.cusum_c_chart(d)["CUSUM-C"].violations[1]) == 0
    assert len(pp.ewma_c_chart(d)["EWMA-C"].violations[1]) == 0


@pytest.mark.parametrize("llamada, texto", [
    (lambda: pp.ewma_p_chart([5, 20], [10, 10]), "mayores"),
    (lambda: pp.ewma_p_chart(D, N, weight=0), "weight"),
    (lambda: pp.ewma_p_chart(D, N, weight=1.5), "weight"),
    (lambda: pp.cusum_p_chart([5, 20], [10, 10]), "mayores"),
    (lambda: pp.cusum_p_chart(D, N, h=0), "'h'"),
    (lambda: pp.cusum_u_chart(D, N, k=-1), "'h'"),
])
def test_errores(llamada, texto):
    with pytest.raises(ValueError, match=texto):
        llamada()


def test_grafico_y_resumen():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for ch in (pp.ewma_p_chart(D, N), pp.cusum_p_chart(D, N), pp.cusum_c_chart(D)):
        assert ch.summary()
        ch.plot()
        plt.close("all")
