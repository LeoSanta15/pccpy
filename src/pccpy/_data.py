"""Conversión y validación de datos de entrada."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from ._i18n import tr


def _excel_writer(path):
    """Abre un ``pd.ExcelWriter`` con openpyxl; da mensaje claro si no está instalado."""
    try:
        return pd.ExcelWriter(path, engine="openpyxl")
    except ImportError:
        raise ImportError(
            tr("openpyxl es necesario para exportar a Excel. Instálalo con:\n"
            "    pip install openpyxl\n"
            "o con la dependencia opcional de pccpy:\n"
            "    pip install pccpy[excel]")
        ) from None


def as_1d(x, name: str = "x", allow_nan: bool = False) -> np.ndarray:
    """Convierte ``x`` (lista, array, Series) a un array float 1-D.

    Si ``x`` contiene ``NaN`` o ``inf`` y ``allow_nan=False``, los valores
    no finitos se eliminan con un ``UserWarning``.
    """
    arr = np.asarray(x, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    if arr.ndim != 1:
        raise ValueError(tr(
            "'{name}' debe ser unidimensional (recibido: {ndim}-D)."
        ).format(name=name, ndim=arr.ndim))
    if arr.size == 0:
        raise ValueError(tr("'{name}' está vacío.").format(name=name))
    if not allow_nan:
        bad = ~np.isfinite(arr)
        if bad.any():
            n_bad = int(bad.sum())
            warnings.warn(
                tr(
                    "'{name}' contiene {n_bad} valor(es) no finito(s) (NaN/inf) en las posiciones "
                    "{positions}. Se excluyen del análisis."
                ).format(name=name, n_bad=n_bad, positions=np.where(bad)[0].tolist()),
                UserWarning,
                stacklevel=3,
            )
            arr = arr[~bad]
            if arr.size == 0:
                raise ValueError(tr(
                    "'{name}' no tiene valores válidos tras eliminar NaN/inf."
                ).format(name=name))
    return arr


def to_subgroups(
    data,
    subgroup_size: int | None = None,
    subgroup=None,
    value: str | None = None,
    *,
    _allow_size_1: bool = False,
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
                    tr(
                        "Con DataFrame en formato largo y 'subgroup' como nombre de columna, "
                        "especifica también 'value' con el nombre de la columna de valores (columnas "
                        "numéricas disponibles: {numeric_cols})."
                    ).format(numeric_cols=numeric_cols)
                )
        vals = data[col_val].to_numpy(dtype=float)
        ids = data[col_sub].to_numpy()
        # Delegamos al camino 1-D + subgroup (array de identificadores)
        subgroup = ids
        data = vals

    # ── DataFrame ancho: filtrar columnas no numéricas antes de convertir ───────
    if isinstance(data, pd.DataFrame) and not isinstance(subgroup, str):
        numeric_cols = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
        dropped = [c for c in data.columns if c not in numeric_cols]
        if dropped:
            warnings.warn(
                tr(
                    "Se ignoraron {n_dropped} columna(s) no numéricas del DataFrame: {dropped}. "
                    "Si querías usar una como identificador de subgrupo, pasa "
                    "subgroup='nombre_columna'."
                ).format(n_dropped=len(dropped), dropped=dropped),
                UserWarning,
                stacklevel=3,
            )
            data = data[numeric_cols]

    arr = np.asarray(data, dtype=float)

    if arr.ndim == 2:
        if subgroup_size is not None or subgroup is not None:
            raise ValueError(
                tr("Con datos 2-D no se debe indicar 'subgroup_size' ni 'subgroup'.")
            )
        mat = arr
        n_complete = mat.shape[0]

    elif arr.ndim == 1:
        if subgroup is not None:
            ids = np.asarray(subgroup)
            if ids.shape != arr.shape:
                raise ValueError(tr("'subgroup' debe tener la misma longitud que los datos."))
            groups = [g.to_numpy(dtype=float) for _, g in pd.Series(arr).groupby(ids, sort=False)]
            m = max(len(g) for g in groups)
            mat = np.full((len(groups), m), np.nan)
            for i, g in enumerate(groups):
                mat[i, : len(g)] = g
            n_complete = mat.shape[0]

        elif subgroup_size is not None:
            m = int(subgroup_size)
            if m < 1:
                raise ValueError(tr("'subgroup_size' debe ser >= 1."))
            if m == 1 and not _allow_size_1:
                raise ValueError(
                    tr("'subgroup_size=1' da subgrupos de un solo elemento; no se puede "
                    "estimar la variación dentro de subgrupos. "
                    "Para datos individuales usa imr_chart() en lugar de xbar_r_chart().")
                )
            remainder = arr.size % m
            if remainder != 0:
                n_complete = arr.size // m
                # Rellenar con NaN para crear el subgrupo incompleto
                padded = np.full((n_complete + 1) * m, np.nan)
                padded[: arr.size] = arr
                mat = padded.reshape(-1, m)
                warnings.warn(
                    tr(
                        "{size} observaciones no forman un número exacto de subgrupos de tamaño {m}. "
                        "El último subgrupo tiene {remainder} de {m} observaciones: se incluye en la "
                        "gráfica pero NO en el cálculo de los límites de control."
                    ).format(size=arr.size, m=m, remainder=remainder),
                    UserWarning,
                    stacklevel=3,
                )
            else:
                mat = arr.reshape(-1, m)
                n_complete = mat.shape[0]
        else:
            raise ValueError(
                tr("Datos 1-D: indique 'subgroup_size' o 'subgroup', o pase una matriz 2-D.")
            )
    else:
        raise ValueError(tr("Los datos deben ser 1-D o 2-D."))

    if mat.shape[0] == 0 or mat.shape[1] == 0:
        raise ValueError(tr("No hay datos."))
    if np.any(np.isinf(mat)):
        raise ValueError(tr("Los datos contienen valores infinitos."))
    if np.any(np.all(np.isnan(mat), axis=1)):
        raise ValueError(tr("Hay subgrupos sin ninguna observación válida."))
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
            tr(
                "'stages' debe tener una etiqueta por punto graficado ({n_points}); recibido: "
                "{shape}."
            ).format(n_points=n_points, shape=st.shape)
        )
    out, seen = [], set()
    start = 0
    for i in range(1, n_points + 1):
        if i == n_points or st[i] != st[start]:
            label = st[start].item() if hasattr(st[start], "item") else st[start]
            if label in seen:
                raise ValueError(
                    tr(
                        "La etapa {label!r} aparece en bloques separados; cada etapa debe ser contigua."
                    ).format(label=label)
                )
            seen.add(label)
            out.append((label, np.arange(start, i)))
            start = i
    return out
