"""Etiquetas del eje x de las cartas (fechas, lotes…): detección en los datos de entrada y formato para el gráfico."""
from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

import numpy as np
import pandas as pd

F = TypeVar("F", bound=Callable[..., Any])

# nombre de los argumentos que contienen los datos, por si se pasan con nombre
_ARGUMENTOS_DE_DATOS = ("data", "x", "defectives", "defects", "counts")


def es_temporal(etiquetas) -> bool:
    """True si las etiquetas son fechas/horas/periodos."""
    idx = pd.Index(etiquetas)
    return isinstance(idx, (pd.DatetimeIndex, pd.PeriodIndex, pd.TimedeltaIndex)) or pd.api.types.is_datetime64_any_dtype(idx)


def _indice_util(idx: pd.Index) -> bool:
    """Un índice «informativo»: fechas/periodos o texto. Un RangeIndex (o enteros sueltos) no aporta nada que dibujar."""
    if isinstance(idx, (pd.DatetimeIndex, pd.PeriodIndex, pd.TimedeltaIndex)):
        return True
    return pd.api.types.is_string_dtype(idx) and len(idx) > 0 and all(isinstance(v, str) for v in idx)


def detectar(data, subgroup_size=None, subgroup=None, value=None) -> np.ndarray | None:
    """Etiquetas de cada *punto graficado* deducidas de la entrada, o ``None`` si no hay.

    * Serie/DataFrame con índice de fechas (o de texto): una etiqueta por observación o por fila.
    * Con ``subgroup_size=k``: la etiqueta de la primera observación de cada subgrupo.
    * Con ``subgroup=`` (identificadores) o DataFrame largo: los identificadores de subgrupo, en orden de aparición,
      si son fechas o texto.
    """
    if isinstance(data, pd.DataFrame) and isinstance(subgroup, str):
        ids = pd.Index(data[subgroup].drop_duplicates())
        return np.asarray(ids) if _indice_util(ids) else None
    if subgroup is not None and not isinstance(subgroup, str):
        ids = pd.Index(pd.unique(np.asarray(subgroup)))
        return np.asarray(ids) if _indice_util(ids) else None
    if not isinstance(data, (pd.Series, pd.DataFrame)):
        return None
    idx = data.index
    if not _indice_util(idx):
        return None
    if subgroup_size is not None and int(subgroup_size) > 1:
        idx = idx[:: int(subgroup_size)]
    return np.asarray(idx)


def con_etiquetas(func: F) -> F:
    """Decorador de las funciones de cartas: si la entrada trae fechas (o texto) en su índice, el resultado las conserva."""

    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        resultado = func(*args, **kwargs)
        datos = args[0] if args else next((kwargs[k] for k in _ARGUMENTOS_DE_DATOS if k in kwargs), None)
        etiquetas = detectar(datos, kwargs.get("subgroup_size"), kwargs.get("subgroup"), kwargs.get("value"))
        # si el número no coincide (p. ej. se descartaron NaN) no se adjuntan, para no desalinear
        if etiquetas is not None and getattr(resultado, "panels", None) and len(etiquetas) == len(resultado.panels[0].values):
            resultado.labels = etiquetas
        return resultado

    return envoltura  # type: ignore[return-value]


def formatear(etiquetas, maximo: int = 8) -> tuple[np.ndarray, list[str]]:
    """Posiciones (base 1) y textos de las marcas del eje x: como mucho ``maximo``, repartidas por igual."""
    n = len(etiquetas)
    posiciones = np.unique(np.linspace(0, n - 1, min(maximo, n)).round().astype(int))
    if es_temporal(etiquetas):
        idx = pd.Index(etiquetas)
        if isinstance(idx, pd.PeriodIndex):
            textos = [str(idx[i]) for i in posiciones]
        else:
            ts = pd.DatetimeIndex(idx) if not isinstance(idx, pd.TimedeltaIndex) else idx
            if isinstance(ts, pd.DatetimeIndex):
                tramo = ts.max() - ts.min()
                sin_hora = (ts == ts.normalize()).all()
                if sin_hora:
                    fmt = "%Y-%m-%d"
                elif tramo <= pd.Timedelta(days=2):
                    fmt = "%H:%M"
                else:
                    fmt = "%m-%d %H:%M"
                textos = [ts[i].strftime(fmt) for i in posiciones]
            else:
                textos = [str(ts[i]) for i in posiciones]
    else:
        textos = [str(etiquetas[i]) for i in posiciones]
    return posiciones + 1, textos
