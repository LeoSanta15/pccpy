"""Conversión y validación de datos de entrada."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def as_1d(x, name: str = "x", allow_nan: bool = False) -> np.ndarray:
    """Convierte ``x`` (lista, array, Series) a un array float 1-D."""
    arr = np.asarray(x, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    if arr.ndim != 1:
        raise ValueError(f"'{name}' debe ser unidimensional (recibido: {arr.ndim}-D).")
    if arr.size == 0:
        raise ValueError(f"'{name}' está vacío.")
    if not allow_nan and not np.all(np.isfinite(arr)):
        raise ValueError(f"'{name}' contiene valores faltantes o infinitos.")
    return arr


def to_subgroups(
    data,
    subgroup_size: Optional[int] = None,
    subgroup=None,
) -> np.ndarray:
    """Devuelve una matriz (k subgrupos x m columnas) rellena con NaN.

    Formatos aceptados (los mismos que ofrece Minitab):

    * ``data`` 2-D (array o DataFrame): cada **fila** es un subgrupo.
    * ``data`` 1-D + ``subgroup_size``: observaciones consecutivas se agrupan de
      a ``subgroup_size``.
    * ``data`` 1-D + ``subgroup`` (identificadores, misma longitud): cada valor
      distinto de ``subgroup`` define un subgrupo, en orden de aparición. Permite
      subgrupos de tamaño desigual.
    """
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 2:
        if subgroup_size is not None or subgroup is not None:
            raise ValueError(
                "Con datos 2-D no se debe indicar 'subgroup_size' ni 'subgroup'."
            )
        mat = arr
    elif arr.ndim == 1:
        if subgroup is not None:
            ids = np.asarray(subgroup)
            if ids.shape != arr.shape:
                raise ValueError("'subgroup' debe tener la misma longitud que los datos.")
            groups = [g.to_numpy(dtype=float) for _, g in pd.Series(arr).groupby(ids, sort=False)]
            m = max(len(g) for g in groups)
            mat = np.full((len(groups), m), np.nan)
            for i, g in enumerate(groups):
                mat[i, : len(g)] = g
        elif subgroup_size is not None:
            m = int(subgroup_size)
            if m < 1:
                raise ValueError("'subgroup_size' debe ser >= 1.")
            if arr.size % m != 0:
                raise ValueError(
                    f"{arr.size} observaciones no se pueden dividir en subgrupos de {m}."
                )
            mat = arr.reshape(-1, m)
        else:
            raise ValueError(
                "Datos 1-D: indique 'subgroup_size' o 'subgroup', o pase una matriz 2-D."
            )
    else:
        raise ValueError("Los datos deben ser 1-D o 2-D.")

    if mat.shape[0] == 0 or mat.shape[1] == 0:
        raise ValueError("No hay datos.")
    if np.any(np.isinf(mat)):
        raise ValueError("Los datos contienen valores infinitos.")
    if np.any(np.all(np.isnan(mat), axis=1)):
        raise ValueError("Hay subgrupos sin ninguna observación válida.")
    return mat


def stage_slices(n_points: int, stages) -> list:
    """Lista de (etiqueta, índices) con las etapas en orden de aparición.

    Cada etapa debe ser un bloque contiguo (como exige Minitab).
    """
    if stages is None:
        return [(1, np.arange(n_points))]
    st = np.asarray(stages)
    if st.shape != (n_points,):
        raise ValueError(
            f"'stages' debe tener una etiqueta por punto graficado ({n_points}); "
            f"recibido: {st.shape}."
        )
    out, seen = [], set()
    start = 0
    for i in range(1, n_points + 1):
        if i == n_points or st[i] != st[start]:
            label = st[start].item() if hasattr(st[start], "item") else st[start]
            if label in seen:
                raise ValueError(
                    f"La etapa {label!r} aparece en bloques separados; "
                    "cada etapa debe ser contigua."
                )
            seen.add(label)
            out.append((label, np.arange(start, i)))
            start = i
    return out
