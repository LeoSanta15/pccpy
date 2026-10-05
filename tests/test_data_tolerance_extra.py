"""Entrada de datos (``_data``), intervalos de tolerancia y capacidad de atributos: validaciones y caminos poco usados."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import pccpy as pp
from pccpy._data import as_1d, to_subgroups


# ───────────────────────────────────────────────────────────── as_1d ──────────
def test_as_1d_escalar_vacio_y_dimension():
    assert as_1d(5).tolist() == [5.0]
    with pytest.raises(ValueError, match="vacío"):
        as_1d([])
    with pytest.raises(ValueError, match="unidimensional"):
        as_1d([[1, 2], [3, 4]])


def test_as_1d_elimina_no_finitos_con_aviso_y_falla_si_no_queda_nada():
    with pytest.warns(UserWarning, match="no finito"):
        assert as_1d([1, np.nan, 3, np.inf]).tolist() == [1.0, 3.0]
    with pytest.warns(UserWarning), pytest.raises(ValueError, match="valores válidos"):
        as_1d([np.nan, np.nan])
    assert np.isnan(as_1d([1, np.nan], allow_nan=True)[1])


# ─────────────────────────────────────────────────────── to_subgroups ─────────
def test_formato_largo_con_columna_de_valores_explicita_o_unica():
    df = pd.DataFrame({"lote": ["a", "a", "b", "b", "c", "c"], "x": [1.0, 2, 3, 4, 5, 6]})
    mat, n = to_subgroups(df, subgroup="lote")
    assert mat.tolist() == [[1, 2], [3, 4], [5, 6]] and n == 3
    df["y"] = 0.0
    assert to_subgroups(df, subgroup="lote", value="x")[0].shape == (3, 2)
    with pytest.raises(ValueError, match="value"):
        to_subgroups(df, subgroup="lote")  # dos columnas numéricas: ambiguo


def test_dataframe_ancho_ignora_columnas_no_numericas():
    df = pd.DataFrame({"a": [1.0, 2], "b": [3.0, 4], "texto": ["u", "v"]})
    with pytest.warns(UserWarning, match="no numéricas"):
        mat, _ = to_subgroups(df)
    assert mat.shape == (2, 2)


def test_subgrupos_desiguales_por_identificador_y_longitud_distinta():
    mat, n = to_subgroups([1.0, 2, 3, 4, 5], subgroup=["a", "a", "b", "b", "b"])
    assert mat.shape == (2, 3) and np.isnan(mat[0, 2]) and n == 2
    with pytest.raises(ValueError, match="misma longitud"):
        to_subgroups([1.0, 2, 3], subgroup=["a", "b"])


def test_subgroup_size_invalido_y_subgrupo_incompleto():
    with pytest.raises(ValueError, match=">= 1"):
        to_subgroups([1.0, 2], subgroup_size=0)
    with pytest.raises(ValueError, match="un solo elemento"):
        to_subgroups([1.0, 2], subgroup_size=1)
    with pytest.warns(UserWarning, match="subgrupo"):
        mat, n = to_subgroups(np.arange(1.0, 8.0), subgroup_size=3)
    assert mat.shape == (3, 3) and n == 2


@pytest.mark.parametrize("llamada, texto", [
    (lambda: to_subgroups([1.0, 2, 3]), "subgroup_size"),
    (lambda: to_subgroups(np.ones((3, 2)), subgroup_size=2), "2-D"),
    (lambda: to_subgroups(np.ones((2, 2, 2))), "1-D o 2-D"),
    (lambda: to_subgroups(np.empty((0, 3))), "No hay datos"),
    (lambda: to_subgroups(np.array([[1.0, np.inf], [1.0, 2.0]])), "infinitos"),
    (lambda: to_subgroups(np.array([[1.0, 2.0], [np.nan, np.nan]])), "sin ninguna"),
])
def test_to_subgroups_errores(llamada, texto):
    with pytest.raises(ValueError, match=texto):
        llamada()


# ──────────────────────────────────────────────────────────── tolerancia ──────
X = np.random.default_rng(11).normal(50, 2, 120)


@pytest.mark.parametrize("kw, texto", [
    (dict(coverage=0), "coverage"), (dict(coverage=1), "coverage"),
    (dict(confidence=0), "confidence"), (dict(confidence=1.2), "confidence"),
    (dict(sides="tres"), "sides"),
])
def test_tolerancia_validaciones(kw, texto):
    with pytest.raises(ValueError, match=texto):
        pp.tolerance_interval(X, **kw)
    with pytest.raises(ValueError, match=texto):
        pp.tolerance_interval_summary(50, 2, 30, **kw)


def test_tolerancia_pocas_observaciones_y_resumen_invalido():
    with pytest.raises(ValueError, match="2 observaciones"):
        pp.tolerance_interval([1.0])
    with pytest.raises(ValueError, match="'n'"):
        pp.tolerance_interval_summary(50, 2, 1)


@pytest.mark.parametrize("sides", ["lower", "upper"])
def test_no_parametrico_unilateral_contra_binomial(sides):
    r = pp.tolerance_interval(X, coverage=0.90, confidence=0.95, sides=sides, method="nonparametric")
    xs = np.sort(X)
    n = len(X)
    # índice mínimo r con P(Bin(n, 1-p) >= r) >= confianza (definición de estadístico de orden)
    k = next(i for i in range(1, n + 1) if stats.binom.sf(i - 1, n, 0.10) >= 0.95)
    if sides == "lower":
        assert r.lower == xs[k - 1] and r.upper is None
    else:
        assert r.upper == xs[n - k] and r.lower is None


@pytest.mark.parametrize("sides", ["two", "lower", "upper"])
def test_no_parametrico_muestra_insuficiente(sides):
    with pytest.raises(ValueError, match="insuficiente"):
        pp.tolerance_interval(X[:10], coverage=0.99, confidence=0.99, sides=sides, method="nonparametric")


# ────────────────────────────────────────── capacidad de atributos (resto) ────
def test_poisson_aviso_de_dispersion_y_excel(tmp_path):
    r = pp.capability_poisson([1, 2, 1, 30, 2, 1, 25, 2], 5, opportunities=10)
    assert not r.homogeneous and "Aviso" in r.summary() and "DPMO" in r.summary()
    from importlib.util import find_spec

    if find_spec("openpyxl"):
        r.to_excel(tmp_path / "p.xlsx")
        assert (tmp_path / "p.xlsx").exists()


def test_binomial_errores_de_tamano_y_vacio():
    with pytest.raises(ValueError, match="positivos"):
        pp.capability_binomial([1, 2], [10, 0])
    with pytest.raises(ValueError, match="vacío"):
        pp.capability_binomial([], 10)
    with pytest.raises(ValueError, match="confidence"):
        pp.capability_poisson([1, 2], confidence=0)
