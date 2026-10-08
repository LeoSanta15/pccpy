"""Intervalos de confianza por bootstrap (percentil y BCa) para cualquier estadístico de una muestra.

Cuando los datos son asimétricos, los intervalos normales (``x̄ ± t·s/√n``, chi-cuadrado para sigma, Bissell para
Ppk) pierden cobertura. El bootstrap remuestrea los propios datos y no supone ninguna forma:

* **percentil**: los cuantiles ``α/2`` y ``1 − α/2`` de los valores del estadístico en los remuestreos;
* **BCa** (sesgo corregido y acelerado, Efron 1987): ajusta esos cuantiles con una corrección de sesgo ``z0`` y una
  aceleración ``a`` (por jackknife); suele cubrir mejor con asimetría.

La estadística puede devolver un escalar o un vector (p. ej. Pp y Ppk a la vez): se usan los mismos remuestreos para
todas las componentes.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from ._data import as_1d
from ._frames import renombrar
from ._i18n import N_, tr

#: Menos observaciones que esto da un aviso: el bootstrap también pierde cobertura con muestras muy pequeñas.
MIN_N_RECOMENDADO = 20


@dataclass
class BootstrapResult:
    """Resultado de ``bootstrap_ci``: estimación puntual e intervalo (por componente si la estadística es un vector)."""

    estimate: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    method: str
    n: int
    n_boot: int
    n_valid: int
    confidence: float
    seed: int | None
    replicates: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def ci(self) -> tuple:
        """``(inferior, superior)``: escalares si la estadística devuelve un escalar, arreglos si devuelve un vector."""
        if self.estimate.ndim == 0:
            return float(self.lower), float(self.upper)
        return self.lower, self.upper

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Una fila por componente: estimación y límites del intervalo."""
        est, lo, hi = (np.atleast_1d(a) for a in (self.estimate, self.lower, self.upper))
        frame = pd.DataFrame({N_("estimación"): est, N_("límite inferior"): lo, N_("límite superior"): hi})
        return renombrar(frame, {N_("estimación"): "estimate", N_("límite inferior"): "lower",
                                 N_("límite superior"): "upper"}, stable)

    def summary(self) -> str:
        est, lo, hi = (np.atleast_1d(a) for a in (self.estimate, self.lower, self.upper))
        lines = [tr("Intervalo bootstrap {metodo} al {nivel:g}%  (n={n}, remuestreos={b})").format(
            metodo=self.method, nivel=100 * self.confidence, n=self.n, b=self.n_valid)]
        for i, (e, a, b) in enumerate(zip(est, lo, hi)):
            nombre = "" if est.size == 1 else f"[{i}] "
            lines.append(f"  {nombre}{e:.6g}  ({a:.6g}, {b:.6g})")
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()


def _estadistica(statistic, muestra: np.ndarray) -> np.ndarray:
    return np.atleast_1d(np.asarray(statistic(muestra), dtype=float))


def _remuestrear(statistic, x: np.ndarray, idx: np.ndarray, vectorized: bool) -> np.ndarray:
    """Valores de la estadística en cada remuestreo: forma (n_boot, k)."""
    if vectorized:
        r = np.asarray(statistic(x[idx], axis=-1), dtype=float)
        return r.reshape(len(idx), -1)
    return np.array([_estadistica(statistic, x[i]) for i in idx])


def _bca_alfas(theta: np.ndarray, reps: np.ndarray, jack: np.ndarray, alpha: float) -> tuple:
    """Niveles ``(bajo, alto)`` ajustados por BCa para cada componente; ``nan`` donde no se puede (→ percentil)."""
    k = theta.size
    bajo, alto = np.full(k, np.nan), np.full(k, np.nan)
    za = stats.norm.ppf([alpha / 2, 1 - alpha / 2])
    for j in range(k):
        r = reps[:, j]
        r = r[np.isfinite(r)]
        if r.size == 0:
            continue
        prop = (np.sum(r < theta[j]) + 0.5 * np.sum(r == theta[j])) / r.size
        if not 0 < prop < 1:
            continue
        z0 = stats.norm.ppf(prop)
        d = jack[:, j].mean() - jack[:, j]
        den = 6.0 * np.sum(d ** 2) ** 1.5
        a = np.sum(d ** 3) / den if den > 0 else 0.0
        ajust = []
        for z in za:
            denom = 1.0 - a * (z0 + z)
            if denom <= 0:
                ajust.append(np.nan)
            else:
                ajust.append(stats.norm.cdf(z0 + (z0 + z) / denom))
        bajo[j], alto[j] = ajust
    return bajo, alto


def bootstrap_ci(
    data,
    statistic,
    *,
    method: str = "bca",
    n_boot: int = 2000,
    confidence: float = 0.95,
    seed: int | None = None,
    vectorized: bool = False,
) -> BootstrapResult:
    """Intervalo de confianza bootstrap para ``statistic(data)``.

    Parameters
    ----------
    data : array-like
        Muestra 1-D (los valores no finitos se eliminan con un aviso).
    statistic : callable
        Función de una muestra 1-D que devuelve un escalar o un vector (``np.mean``, ``np.std``, …). Con
        ``vectorized=True`` debe aceptar ``axis=-1`` y se llama una sola vez con todos los remuestreos (mucho más
        rápido, p. ej. ``np.mean``).
    method : str
        ``'bca'`` (por defecto) o ``'percentile'``.
    n_boot : int
        Número de remuestreos (por defecto 2000).
    confidence : float
        Nivel de confianza (por defecto 0,95).
    seed : int, opcional
        Semilla del generador aleatorio, para resultados reproducibles.
    vectorized : bool
        Ver ``statistic``.

    Returns
    -------
    BootstrapResult
        ``result.ci`` da ``(inferior, superior)``; ``result.estimate`` la estimación con la muestra original.

    Notes
    -----
    Si la distribución bootstrap de una componente es degenerada (todos los remuestreos iguales) el intervalo se
    reduce a la estimación y se avisa; si BCa no se puede calcular (corrección de sesgo infinita) se usa el percentil
    y se avisa. Las estadísticas no finitas en algún remuestreo se descartan (con aviso si son más del 5 %).
    """
    if method not in ("bca", "percentile"):
        raise ValueError(tr("'method' debe ser 'bca' o 'percentile'."))
    if not 0 < confidence < 1:
        raise ValueError(tr("'confidence' debe estar en (0, 1)."))
    if int(n_boot) != n_boot or n_boot < 100:
        raise ValueError(tr("'n_boot' debe ser un entero ≥ 100."))
    if not callable(statistic):
        raise TypeError(tr("'statistic' debe ser una función."))
    x = as_1d(data, "data")
    n = x.size
    if n < 2:
        raise ValueError(tr("Se necesitan al menos 2 observaciones."))
    if n < MIN_N_RECOMENDADO:
        warnings.warn(tr("Con n={n} (< {minimo}) el bootstrap también pierde cobertura; interprete el intervalo con "
                         "cautela.").format(n=n, minimo=MIN_N_RECOMENDADO), UserWarning, stacklevel=2)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(int(n_boot), n))
    crudo = np.asarray(statistic(x), dtype=float)
    escalar = crudo.ndim == 0
    theta = np.atleast_1d(crudo)
    reps = _remuestrear(statistic, x, idx, vectorized)
    if reps.shape[1] != theta.size:
        raise ValueError(tr("'statistic' debe devolver siempre el mismo número de valores."))

    k = theta.size
    finitos = np.all(np.isfinite(reps), axis=1)
    n_valid = int(finitos.sum())
    if n_valid < 0.95 * n_boot:
        warnings.warn(tr("La estadística no fue finita en {mal} de {total} remuestreos; se descartan.").format(
            mal=int(n_boot) - n_valid, total=int(n_boot)), UserWarning, stacklevel=2)
    if n_valid < 50:
        raise ValueError(tr("Muy pocos remuestreos válidos ({n}); revise la estadística.").format(n=n_valid))
    reps = reps[finitos]

    alfa = 1 - confidence
    bajo = np.full(k, alfa / 2)
    alto = np.full(k, 1 - alfa / 2)
    usado = method
    if method == "bca":
        jack = np.array([_estadistica(statistic, np.delete(x, i)) for i in range(n)])
        b, a = _bca_alfas(theta, reps, jack, alfa)
        ok = np.isfinite(b) & np.isfinite(a)
        if not ok.all():
            warnings.warn(tr("BCa no se puede calcular para alguna componente (el estimador queda en un extremo de la "
                             "distribución bootstrap); se usa el percentil en ella."), UserWarning, stacklevel=2)
            usado = "bca/percentile"
        bajo[ok], alto[ok] = b[ok], a[ok]

    lo = np.array([np.quantile(reps[:, j], bajo[j]) for j in range(k)])
    hi = np.array([np.quantile(reps[:, j], alto[j]) for j in range(k)])
    degenerada = np.ptp(reps, axis=0) == 0
    if degenerada.any():
        warnings.warn(tr("La distribución bootstrap es degenerada (todos los remuestreos dan el mismo valor); el "
                         "intervalo se reduce a la estimación."), UserWarning, stacklevel=2)
        lo[degenerada] = theta[degenerada]
        hi[degenerada] = theta[degenerada]

    est = theta[0] if escalar else theta
    if escalar:
        lo, hi = lo[0], hi[0]
    return BootstrapResult(
        estimate=np.asarray(est), lower=np.asarray(lo), upper=np.asarray(hi), method=usado, n=n, n_boot=int(n_boot),
        n_valid=n_valid, confidence=float(confidence), seed=seed, replicates=reps)
