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


# ───────────────────────────────────────────────── resumen: media, mediana y sigma ──
_NOMBRES = {"mean": N_("Media"), "median": N_("Mediana"), "std": N_("Desv.Est.")}


def _estadisticas_basicas(m: np.ndarray, axis: int = -1) -> np.ndarray:
    """Media, mediana y desviación estándar (n − 1) a lo largo de ``axis``; la salida añade un eje final de 3."""
    return np.stack([m.mean(axis=axis), np.median(m, axis=axis), m.std(axis=axis, ddof=1)], axis=-1)


def _mediana_sin_distribucion(x: np.ndarray, confianza: float) -> tuple[float, float]:
    """Intervalo de la mediana por estadísticos de orden (binomial con p = 0,5): cobertura ≥ ``confianza``."""
    xs, n = np.sort(x), x.size
    alfa = 1 - confianza
    k = 1  # mayor k tal que P(B ≤ k − 1) ≤ α/2, con B ~ Binomial(n, 0,5)
    while k < n and stats.binom.cdf(k, n, 0.5) <= alfa / 2:
        k += 1
    if stats.binom.cdf(k - 1, n, 0.5) > alfa / 2:  # muestra demasiado pequeña para esa confianza
        return float(xs[0]), float(xs[-1])
    return float(xs[k - 1]), float(xs[n - k])


@dataclass
class BootstrapSummary:
    """Media, mediana y desviación estándar con su intervalo bootstrap y el intervalo clásico de referencia."""

    statistics: tuple
    estimate: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    classic_lower: np.ndarray
    classic_upper: np.ndarray
    n: int
    method: str
    n_boot: int
    confidence: float
    seed: int | None
    bootstrap: BootstrapResult = field(repr=False, default=None)  # type: ignore[assignment]

    def ci(self, statistic: str) -> tuple:
        """Intervalo bootstrap ``(inferior, superior)`` de ``'mean'``, ``'median'`` o ``'std'``."""
        i = self.statistics.index(statistic)
        return float(self.lower[i]), float(self.upper[i])

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Una fila por estadístico: estimación, intervalo bootstrap e intervalo clásico (de referencia)."""
        frame = pd.DataFrame({
            N_("estimación"): self.estimate, N_("límite inferior"): self.lower, N_("límite superior"): self.upper,
            N_("clásico inferior"): self.classic_lower, N_("clásico superior"): self.classic_upper,
        }, index=[_NOMBRES[s] for s in self.statistics])
        out = renombrar(frame, {
            N_("estimación"): "estimate", N_("límite inferior"): "lower", N_("límite superior"): "upper",
            N_("clásico inferior"): "classic_lower", N_("clásico superior"): "classic_upper"}, stable)
        out.index = list(self.statistics) if stable else [tr(_NOMBRES[s]) for s in self.statistics]
        out.index.name = "statistic" if stable else tr(N_("estadístico"))
        return out

    def summary(self) -> str:
        lines = [tr("Resumen con intervalos bootstrap {metodo} al {nivel:g}%  (n={n}, remuestreos={b})").format(
            metodo=self.method, nivel=100 * self.confidence, n=self.n, b=self.bootstrap.n_valid)]
        for i, s in enumerate(self.statistics):
            lines.append(tr("  {nombre:<10}{est:.6g}  bootstrap ({lo:.6g}, {hi:.6g})  clásico ({clo:.6g}, {chi:.6g})").format(
                nombre=tr(_NOMBRES[s]), est=self.estimate[i], lo=self.lower[i], hi=self.upper[i],
                clo=self.classic_lower[i], chi=self.classic_upper[i]))
        lines.append(tr("  Clásico: t de Student (media), chi-cuadrado (desviación estándar) y estadísticos de orden "
                        "(mediana); los dos primeros suponen normalidad."))
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()


def bootstrap_summary(data, *, method: str = "bca", n_boot: int = 2000, confidence: float = 0.95,
                      seed: int | None = None) -> BootstrapSummary:
    """Media, mediana y desviación estándar con intervalos bootstrap, junto a los intervalos clásicos.

    Los intervalos clásicos (t de Student para la media, chi-cuadrado para la desviación estándar y estadísticos de orden
    para la mediana) van como referencia: los dos primeros suponen normalidad y con datos asimétricos pueden perder
    cobertura (el de la desviación estándar, mucho). Los tres estadísticos se calculan sobre los mismos remuestreos.

    Parameters
    ----------
    data : array-like
        Muestra 1-D.
    method, n_boot, confidence, seed :
        Ver :func:`bootstrap_ci`.

    Returns
    -------
    BootstrapSummary
    """
    r = bootstrap_ci(data, _estadisticas_basicas, method=method, n_boot=n_boot, confidence=confidence, seed=seed,
                     vectorized=True)
    x = as_1d(data, "data")
    n = x.size
    media, s = float(x.mean()), float(x.std(ddof=1))
    alfa = 1 - confidence
    h = stats.t.ppf(1 - alfa / 2, n - 1) * s / np.sqrt(n)
    med_lo, med_hi = _mediana_sin_distribucion(x, confidence)
    cl = [media - h, med_lo, s * np.sqrt((n - 1) / stats.chi2.ppf(1 - alfa / 2, n - 1))]
    ch = [media + h, med_hi, s * np.sqrt((n - 1) / stats.chi2.ppf(alfa / 2, n - 1))]
    lo, hi = r.ci
    return BootstrapSummary(
        statistics=("mean", "median", "std"), estimate=np.asarray(r.estimate), lower=np.asarray(lo),
        upper=np.asarray(hi), classic_lower=np.array(cl), classic_upper=np.array(ch), n=n, method=r.method,
        n_boot=r.n_boot, confidence=float(confidence), seed=seed, bootstrap=r)
