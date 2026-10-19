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

from ._i18n import N_, tr

TEST_DESCRIPTIONS: dict[int, str] = {
    1: N_("1 punto a más de {k} desviaciones estándar de la línea central"),
    2: N_("{k} puntos consecutivos del mismo lado de la línea central"),
    3: N_("{k} puntos consecutivos, todos ascendentes o todos descendentes"),
    4: N_("{k} puntos consecutivos alternando arriba y abajo"),
    5: N_("{k} de {k1} puntos a más de 2 desviaciones estándar (mismo lado)"),
    6: N_("{k} de {k1} puntos a más de 1 desviación estándar (mismo lado)"),
    7: N_("{k} puntos consecutivos a menos de 1 desviación estándar (ambos lados)"),
    8: N_("{k} puntos consecutivos a más de 1 desviación estándar (ambos lados)"),
}

#: Descripción de la prueba de Benneyan de la carta G (clave de violación ``"B"``).
BENNEYAN_DESCRIPTION = N_("Racha de conteos consecutivos iguales a 0 (prueba de Benneyan)")


def describe(test: int, k=None) -> str:
    """Descripción de la prueba con su parámetro K ya sustituido."""
    k = DEFAULT_K[test] if k is None else k
    return tr(TEST_DESCRIPTIONS[test]).format(k=f"{k:g}", k1=f"{k + 1:g}")

#: Parámetro K por defecto de cada prueba (valores por defecto de Minitab).
DEFAULT_K: dict[int, float] = {1: 3, 2: 9, 3: 6, 4: 14, 5: 2, 6: 4, 7: 15, 8: 8}

#: Pruebas disponibles según la familia de gráfico.
FAMILIES: dict[str, tuple] = {
    "full": (1, 2, 3, 4, 5, 6, 7, 8),  # I, X-barra
    "basic": (1, 2, 3, 4),  # R, S (aproximadas: los rangos no son normales), P, NP, C, U, Laney
    "only1": (1,),  # MR (rangos móviles autocorrelacionados y asimétricos), EWMA, CUSUM
}


def normalize_tests(tests) -> tuple:
    """Acepta ``"all"``, ``None`` (ninguna), un entero o un iterable de enteros."""
    if tests is None:
        return ()
    if isinstance(tests, str):
        if tests.lower() == "all":
            return tuple(range(1, 9))
        raise ValueError(tr("'tests' debe ser 'all', None o una lista de enteros 1-8."))
    if isinstance(tests, (int, np.integer)):
        tests = [tests]
    out = sorted({int(t) for t in tests})
    bad = [t for t in out if t not in TEST_DESCRIPTIONS]
    if bad:
        raise ValueError(tr("Pruebas no válidas: {bad}. Use enteros entre 1 y 8.").format(bad=bad))
    return tuple(out)


def _run_positions(mask: np.ndarray) -> np.ndarray:
    """Para cada índice, longitud de la racha de True que termina en él (0 si False)."""
    pos = np.zeros(mask.size, dtype=int)
    c = 0
    for i, m in enumerate(mask):
        c = c + 1 if m else 0
        pos[i] = c
    return pos


def test1(z: np.ndarray, k: float = 3, k_lower: float | None = None) -> np.ndarray:
    """Puntos a más de ``k`` sigmas del centro; con ``k_lower`` el límite inferior está a ``k_lower`` sigmas."""
    if k_lower is None:
        return np.flatnonzero(np.abs(z) > k)
    return np.flatnonzero((z > k) | (z < -k_lower))


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


def _aplicar_prueba(t: int, k: float, v: np.ndarray, zz: np.ndarray, k_lower: float | None = None) -> np.ndarray:
    """Posiciones (dentro de ``v``) que marca la prueba ``t`` con parámetro ``k``; las pruebas 3 y 4 usan los valores."""
    if t == 1:
        return test1(zz, k, k_lower)
    if t == 3:
        return test3(v, int(k))
    if t == 4:
        return test4(v, int(k))
    fn = {2: test2, 5: test5, 6: test6, 7: test7, 8: test8}[t]
    return fn(zz, int(k))


def apply_tests(
    values: np.ndarray,
    center: np.ndarray,
    sigma: np.ndarray,
    tests: Iterable[int],
    params: dict[int, float] | None = None,
    *,
    limits: tuple[float, float] | None = None,
    rescale_zones: bool = False,
) -> dict[int, np.ndarray]:
    """Aplica las pruebas ``tests`` y devuelve ``{prueba: índices marcados}``.

    ``values``, ``center`` y ``sigma`` son arrays de la misma longitud (sigma es la
    desviación estándar del estadístico graficado en cada punto). Los NaN se ignoran y **cortan** las rachas: las
    pruebas se aplican por separado a cada tramo de puntos consecutivos válidos, de modo que una racha no une
    observaciones separadas por un hueco.

    ``limits = (k_superior, k_inferior)`` son los anchos de los límites de control en sigmas: la prueba 1 los usa como umbral
    de cada lado salvo que ``params`` traiga uno explícito (el mismo para los dos lados). Las zonas de las pruebas 2 a 8 quedan en
    1σ y 2σ; con ``rescale_zones`` se miden en tercios de cada ``k`` (``k/3`` y ``2k/3``).
    """
    params = params or {}
    values = np.asarray(values, dtype=float)
    center = np.broadcast_to(np.asarray(center, dtype=float), values.shape)
    sigma = np.broadcast_to(np.asarray(sigma, dtype=float), values.shape)

    with np.errstate(divide="ignore", invalid="ignore"):
        z = (values - center) / sigma
    z = np.where((sigma == 0) & (values == center), 0.0, z)  # sigma = 0: un punto en el centro no está desviado
    z_zona = z
    if rescale_zones and limits is not None:
        z_zona = np.where(z > 0, z * 3.0 / limits[0], z * 3.0 / limits[1])
    valid = np.isfinite(values) & ~np.isnan(z)  # z = ±inf (sigma = 0 con el punto fuera del centro) es válido
    where = np.flatnonzero(valid)
    # tramos de puntos válidos consecutivos (un hueco corta las rachas)
    cortes = np.flatnonzero(np.diff(where) > 1) + 1
    tramos = np.split(where, cortes) if where.size else []

    out: dict[int, list[np.ndarray]] = {t: [] for t in tests}
    for pos in tramos:
        for t in tests:
            if t == 1 and 1 not in params and limits is not None:
                out[t].append(pos[test1(z[pos], limits[0], limits[1])])
            else:
                out[t].append(pos[_aplicar_prueba(t, params.get(t, DEFAULT_K[t]), values[pos], z_zona[pos] if t != 1 else z[pos])])
    return {t: (np.concatenate(v).astype(int) if v else np.array([], dtype=int)) for t, v in out.items()}
