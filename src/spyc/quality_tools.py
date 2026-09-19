"""Herramientas de calidad complementarias: diagrama de Pareto."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def pareto(categories, counts=None, *, other_below: Optional[float] = None) -> pd.DataFrame:
    """Tabla de Pareto ordenada de mayor a menor frecuencia.

    * ``categories`` con ``counts``: una categoría por elemento con su frecuencia.
    * ``categories`` sin ``counts``: lista de ocurrencias crudas (se cuentan).

    ``other_below``: porcentaje (p. ej. 5) por debajo del cual las categorías se
    agrupan en "Otros" (que siempre queda al final, como en Minitab).
    """
    cats = pd.Series(np.asarray(categories, dtype=object))
    if counts is None:
        table = cats.value_counts().rename("conteo")
    else:
        vals = np.asarray(counts, dtype=float)
        if vals.shape != cats.shape:
            raise ValueError("'categories' y 'counts' deben tener la misma longitud.")
        if np.any(vals < 0):
            raise ValueError("Las frecuencias no pueden ser negativas.")
        table = pd.Series(vals, index=cats.values, name="conteo").groupby(level=0).sum()
    table = table.sort_values(ascending=False, kind="stable")
    total = table.sum()
    if total <= 0:
        raise ValueError("La suma de frecuencias debe ser positiva.")

    if other_below is not None:
        small = table / total * 100 < other_below
        if small.sum() > 1:
            table = pd.concat([table[~small], pd.Series({"Otros": table[small].sum()}, name="conteo")])
    df = table.rename_axis("categoría").reset_index()
    df["porcentaje"] = df["conteo"] / total * 100
    df["acumulado"] = df["porcentaje"].cumsum()
    return df


def plot_pareto(table: pd.DataFrame, *, ax=None):
    """Dibuja el diagrama de Pareto a partir de la tabla de :func:`pareto`."""
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(table))
    ax.bar(x, table["conteo"], color="#1f4e9c")
    ax.set_xticks(x)
    ax.set_xticklabels(table["categoría"].astype(str), rotation=30, ha="right")
    ax.set_ylabel("Conteo")
    ax2 = ax.twinx()
    ax2.plot(x, table["acumulado"], "o-", color="#d62728")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Porcentaje acumulado")
    ax.set_title("Diagrama de Pareto")
    if fig is not None:
        fig.tight_layout()
    return ax.figure
