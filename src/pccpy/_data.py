"""Conversión y validación de datos de entrada."""
from __future__ import annotations

import warnings

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
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
) -> tuple[np.ndarray, int]:
    """Devuelve ``(mat, n_complete)``: matriz (k × m) y número de subgrupos completos.

    ``n_complete`` indica cuántos subgrupos deben usarse para estimar los límites
    de control. Si todos son completos, ``n_complete == mat.shape[0]``. Cuando el
    último subgrupo es incompleto (resto de dividir por ``subgroup_size``), se
    incluye en la gráfica pero se excluye del cálculo de límites, y se emite un
    ``UserWarning`` describiendo la situación.

    Formatos aceptados (los mismos que ofrece Minitab):

    * ``data`` 2-D (array o DataFrame): cada **fila** es un subgrupo.
    * ``data`` 1-D + ``subgroup_size``: observaciones consecutivas se agrupan de
      a ``subgroup_size``. Si el total no es divisible, el último subgrupo queda
      incompleto: se grafica pero no entra en el cálculo de límites.
    * ``data`` 1-D + ``subgroup`` (identificadores, misma longitud): cada valor
      distinto de ``subgroup`` define un subgrupo en orden de aparición. Permite
      subgrupos de tamaño desigual.
    * ``data`` DataFrame (formato largo) + ``subgroup`` nombre de columna + ``value``
      nombre de columna (opcional si hay una sola columna numérica): extrae los
      valores y los identificadores de subgrupo directamente del DataFrame.
    """
    # ── Formato largo: DataFrame + subgroup como nombre de columna ──────────────
    if isinstance(data, pd.DataFrame) and isinstance(subgroup, str):
        col_sub = subgroup
        if value is not None:
            col_val = value
        else:
            numeric_cols = [
                c for c in data.columns
                if c != col_sub and pd.api.types.is_numeric_dtype(data[c])
            ]
            if len(numeric_cols) == 1:
                col_val = numeric_cols[0]
            else:
                raise ValueError(
                    "Con DataFrame en formato largo y 'subgroup' como nombre de columna, "
                    "especifica también 'value' con el nombre de la columna de valores "
                    f"(columnas numéricas disponibles: {numeric_cols})."
                )
        vals = data[col_val].to_numpy(dtype=float)
        ids = data[col_sub].to_numpy()
        # Delegamos al camino 1-D + subgroup (array de identificadores)
        subgroup = ids
        data = vals

    arr = np.asarray(data, dtype=float)

    if arr.ndim == 2:
        if subgroup_size is not None or subgroup is not None:
            raise ValueError(
                "Con datos 2-D no se debe indicar 'subgroup_size' ni 'subgroup'."
            )
        mat = arr
        n_complete = mat.shape[0]

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
            n_complete = mat.shape[0]

        elif subgroup_size is not None:
            m = int(subgroup_size)
            if m < 1:
                raise ValueError("'subgroup_size' debe ser >= 1.")
            remainder = arr.size % m
            if remainder != 0:
                n_complete = arr.size // m
                # Rellenar con NaN para crear el subgrupo incompleto
                padded = np.full((n_complete + 1) * m, np.nan)
                padded[: arr.size] = arr
                mat = padded.reshape(-1, m)
                warnings.warn(
                    f"{arr.size} observaciones no forman un número exacto de subgrupos "
                    f"de tamaño {m}. El último subgrupo tiene {remainder} de {m} "
                    f"observaciones: se incluye en la gráfica pero NO en el cálculo de "
                    f"los límites de control.",
                    UserWarning,
                    stacklevel=3,
                )
            else:
                mat = arr.reshape(-1, m)
                n_complete = mat.shape[0]
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
    return mat, n_complete


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
