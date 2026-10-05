"""Tablas de resultados con etiquetas traducibles y claves estables.

Un ``to_frame()`` devuelve, por defecto, cabeceras en el idioma activo (presentación, como ``summary()``).
Con ``stable=True`` devuelve claves canónicas (inglés, ``snake_case``) que no cambian con el idioma: para código
que indexa la tabla por nombre.
"""
from __future__ import annotations

import pandas as pd

from ._i18n import N_, tr

CLAVE_ESTADISTICO = "statistic"
CLAVE_VALOR = "value"


def tabla_estadisticos(filas, stable: bool = False) -> pd.DataFrame:
    """Tabla de una columna con un estadístico por fila.

    Parameters
    ----------
    filas : sequence of (str | None, str, object)
        ``(clave, etiqueta, valor)``: ``clave`` es la clave estable; ``etiqueta`` el texto en español marcado con
        ``N_()``; una fila ``(None, "", "")`` es un separador (solo aparece con ``stable=False``).
    stable : bool
        ``True`` → índice con las claves canónicas y columnas ``statistic``/``value``.
    """
    if stable:
        filas = [f for f in filas if f[0] is not None]
        indice = pd.Index([c for c, _e, _v in filas], name=CLAVE_ESTADISTICO)
        columna = CLAVE_VALOR
    else:
        indice = pd.Index([tr(e) for _c, e, _v in filas], name=tr(N_("estadístico")))
        columna = tr(N_("valor"))
    return pd.DataFrame({columna: [v for _c, _e, v in filas]}, index=indice)


def renombrar(frame: pd.DataFrame, columnas: dict, stable: bool, indice=None, filas=None) -> pd.DataFrame:
    """Devuelve ``frame`` (con columnas/índice en español) con las cabeceras del idioma activo o con claves estables.

    Parameters
    ----------
    columnas : dict
        ``{columna en español (N_): clave estable}``.
    indice : tuple, optional
        ``(nombre del índice en español (N_), clave estable)``.
    filas : dict, optional
        ``{etiqueta de fila en español (N_): clave estable}`` (solo para tablas cuyas filas son conceptos, no datos).
    """
    salida = frame.rename(columns={es: (clave if stable else tr(es)) for es, clave in columnas.items()})
    if indice is not None:
        es, clave = indice
        salida.index.name = clave if stable else tr(es)
    if filas:
        salida = salida.rename(index={es: (clave if stable else tr(es)) for es, clave in filas.items()})
    return salida


def etiquetas(mapa: dict, stable: bool) -> dict:
    """Clave estable → nombre de columna (la propia clave con ``stable=True``; si no, el texto traducido)."""
    return {k: (k if stable else tr(v)) for k, v in mapa.items()}
