"""Herramientas de calidad complementarias: diagrama de Pareto."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ._frames import renombrar
from ._i18n import N_, tr

_COLUMNAS = {
    N_("categoría"): "category", N_("conteo"): "count", N_("porcentaje"): "percent", N_("acumulado"): "cumulative_percent",
}


def pareto(categories, counts=None, *, other_below: float | None = None, stable: bool = False) -> pd.DataFrame:
    """Tabla de Pareto ordenada de mayor a menor frecuencia.

    * ``categories`` con ``counts``: una categoría por elemento con su frecuencia.
    * ``categories`` sin ``counts``: lista de ocurrencias crudas (se cuentan).

    ``other_below``: porcentaje (p. ej. 5) por debajo del cual las categorías se
    agrupan en "Otros" (que siempre queda al final, como en Minitab; el nombre se traduce al idioma activo).

    Las columnas salen en el idioma activo; con ``stable=True`` son ``category``, ``count``, ``percent`` y
    ``cumulative_percent`` (no cambian con el idioma).
    """
    cats = pd.Series(np.asarray(categories, dtype=object))
    if counts is None:
        table = cats.value_counts().rename("conteo")
    else:
        vals = np.asarray(counts, dtype=float)
        if vals.shape != cats.shape:
            raise ValueError(tr("'categories' y 'counts' deben tener la misma longitud."))
        if np.any(vals < 0):
            raise ValueError(tr("Las frecuencias no pueden ser negativas."))
        table = pd.Series(vals, index=cats.values, name="conteo").groupby(level=0).sum()
    table = table.sort_values(ascending=False, kind="stable")
    total = table.sum()
    if total <= 0:
        raise ValueError(tr("La suma de frecuencias debe ser positiva."))

    if other_below is not None:
        small = table / total * 100 < other_below
        if small.sum() > 1:
            table = pd.concat([table[~small], pd.Series({tr("Otros"): table[small].sum()}, name="conteo")])
    df = table.rename_axis("categoría").reset_index()
    df["porcentaje"] = df["conteo"] / total * 100
    df["acumulado"] = df["porcentaje"].cumsum()
    return renombrar(df, _COLUMNAS, stable)


def plot_pareto(table: pd.DataFrame, *, ax=None):
    """Dibuja el diagrama de Pareto a partir de la tabla de :func:`pareto`."""
    fig = None
    if ax is None:
        with plt.rc_context({}):
            fig, ax = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(table))
    # por posición: la tabla puede venir con las cabeceras de cualquier idioma o con las claves estables
    categoria, conteo, acumulado = table.iloc[:, 0], table.iloc[:, 1], table.iloc[:, 3]
    ax.bar(x, conteo, color="#1f4e9c")
    ax.set_xticks(x)
    ax.set_xticklabels(categoria.astype(str), rotation=30, ha="right")
    ax.set_ylabel(tr("Conteo"))
    ax2 = ax.twinx()
    ax2.plot(x, acumulado, "o-", color="#d62728")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel(tr("Porcentaje acumulado"))
    ax.set_title(tr("Diagrama de Pareto"))
    if fig is not None:
        fig.tight_layout()
    return ax.figure
