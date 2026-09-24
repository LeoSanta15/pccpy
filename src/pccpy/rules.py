"""Pruebas para causas especiales (las 8 pruebas de Minitab / reglas de Nelson).

Convenciones (las mismas que Minitab):

* Las zonas se miden en unidades de la sigma **del estadístico graficado**
  (para X-barra es sigma/sqrt(n_i), y por eso varían con el tamaño del subgrupo).
* Cuando un patrón se cumple, se marca el punto que lo *completa*; si el patrón
  continúa, se marca cada punto adicional.
* Los valores exactamente iguales entre sí rompen una tendencia (prueba 3) y los
  puntos sobre la línea central rompen una racha (prueba 2).
* Las pruebas 5 y 6 marcan el último punto de la ventana solo si ese punto es
  uno de los que exceden la zona (el que completa el patrón).
"""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np

TEST_DESCRIPTIONS: dict[int, str] = {
    1: "1 punto a más de {k} desviaciones estándar de la línea central",
    2: "{k} puntos consecutivos del mismo lado de la línea central",
    3: "{k} puntos consecutivos, todos ascendentes o todos descendentes",
    4: "{k} puntos consecutivos alternando arriba y abajo",
    5: "{k} de {k1} puntos a más de 2 desviaciones estándar (mismo lado)",
    6: "{k} de {k1} puntos a más de 1 desviación estándar (mismo lado)",
    7: "{k} puntos consecutivos a menos de 1 desviación estándar (ambos lados)",
    8: "{k} puntos consecutivos a más de 1 desviación estándar (ambos lados)",
}


def describe(test: int, k=None) -> str:
    """Descripción de la prueba con su parámetro K ya sustituido."""
    k = DEFAULT_K[test] if k is None else k
    return TEST_DESCRIPTIONS[test].format(k=f"{k:g}", k1=f"{k + 1:g}")

#: Parámetro K por defecto de cada prueba (valores por defecto de Minitab).
DEFAULT_K: dict[int, float] = {1: 3, 2: 9, 3: 6, 4: 14, 5: 2, 6: 4, 7: 15, 8: 8}

#: Pruebas disponibles según la familia de gráfico.
FAMILIES: dict[str, tuple] = {
    "full": (1, 2, 3, 4, 5, 6, 7, 8),  # I, X-barra
    "basic": (1, 2, 3, 4),  # MR, R, S, P, NP, C, U, Laney
    "only1": (1,),  # EWMA, CUSUM
}


def normalize_tests(tests) -> tuple:
    """Acepta ``"all"``, ``None`` (ninguna), un entero o un iterable de enteros."""
    if tests is None:
        return ()
    if isinstance(tests, str):
        if tests.lower() == "all":
            return tuple(range(1, 9))
        raise ValueError("'tests' debe ser 'all', None o una lista de enteros 1-8.")
    if isinstance(tests, (int, np.integer)):
        tests = [tests]
    out = sorted({int(t) for t in tests})
    bad = [t for t in out if t not in TEST_DESCRIPTIONS]
    if bad:
        raise ValueError(f"Pruebas no válidas: {bad}. Use enteros entre 1 y 8.")
    return tuple(out)


def _run_positions(mask: np.ndarray) -> np.ndarray:
    """Para cada índice, longitud de la racha de True que termina en él (0 si False)."""
    pos = np.zeros(mask.size, dtype=int)
    c = 0
    for i, m in enumerate(mask):
        c = c + 1 if m else 0
        pos[i] = c
    return pos


def test1(z: np.ndarray, k: float = 3) -> np.ndarray:
    return np.flatnonzero(np.abs(z) > k)


def test2(z: np.ndarray, k: int = 9) -> np.ndarray:
    above = _run_positions(z > 0)
    below = _run_positions(z < 0)
    return np.flatnonzero((above >= k) | (below >= k))


def test3(values: np.ndarray, k: int = 6) -> np.ndarray:
    d = np.diff(values)
    up = _run_positions(d > 0)
    down = _run_positions(d < 0)
    flagged = np.zeros(values.size, dtype=bool)
    flagged[1:] = (up >= k - 1) | (down >= k - 1)
    return np.flatnonzero(flagged)


def test4(values: np.ndarray, k: int = 14) -> np.ndarray:
    s = np.sign(np.diff(values))
    if s.size < 2:
        return np.array([], dtype=int)
    alt = (s[:-1] * s[1:]) < 0  # cambio de sentido entre diferencias consecutivas
    pos = _run_positions(alt)
    flagged = np.zeros(values.size, dtype=bool)
    flagged[2:] = pos >= (k - 2)
    return np.flatnonzero(flagged)


def _k_of_n(z: np.ndarray, k: int, zone: float) -> np.ndarray:
    n = k + 1
    flagged = np.zeros(z.size, dtype=bool)
    for i in range(n - 1, z.size):
        w = z[i - n + 1 : i + 1]
        if z[i] > zone and np.sum(w > zone) >= k or z[i] < -zone and np.sum(w < -zone) >= k:
            flagged[i] = True
    return np.flatnonzero(flagged)


def test5(z: np.ndarray, k: int = 2) -> np.ndarray:
    return _k_of_n(z, k, 2.0)


def test6(z: np.ndarray, k: int = 4) -> np.ndarray:
    return _k_of_n(z, k, 1.0)


def test7(z: np.ndarray, k: int = 15) -> np.ndarray:
    return np.flatnonzero(_run_positions(np.abs(z) < 1.0) >= k)


def test8(z: np.ndarray, k: int = 8) -> np.ndarray:
    return np.flatnonzero(_run_positions(np.abs(z) > 1.0) >= k)


def apply_tests(
    values: np.ndarray,
    center: np.ndarray,
    sigma: np.ndarray,
    tests: Iterable[int],
    params: dict[int, float] | None = None,
) -> dict[int, np.ndarray]:
    """Aplica las pruebas ``tests`` y devuelve ``{prueba: índices marcados}``.

    ``values``, ``center`` y ``sigma`` son arrays de la misma longitud (sigma es la
    desviación estándar del estadístico graficado en cada punto). Los NaN se ignoran.
    """
    params = params or {}
    values = np.asarray(values, dtype=float)
    center = np.broadcast_to(np.asarray(center, dtype=float), values.shape)
    sigma = np.broadcast_to(np.asarray(sigma, dtype=float), values.shape)

    with np.errstate(divide="ignore", invalid="ignore"):
        z = (values - center) / sigma
    valid = np.isfinite(values) & np.isfinite(z)
    where = np.flatnonzero(valid)
    v, zz = values[valid], z[valid]

    fns = {
        1: lambda k: test1(zz, k),
        2: lambda k: test2(zz, int(k)),
        3: lambda k: test3(v, int(k)),
        4: lambda k: test4(v, int(k)),
        5: lambda k: test5(zz, int(k)),
        6: lambda k: test6(zz, int(k)),
        7: lambda k: test7(zz, int(k)),
        8: lambda k: test8(zz, int(k)),
    }
    out: dict[int, np.ndarray] = {}
    for t in tests:
        k = params.get(t, DEFAULT_K[t])
        idx = fns[t](k)
        out[t] = where[idx] if v.size else np.array([], dtype=int)
    return out
