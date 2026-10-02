"""Intervalos de tolerancia (normal y libre de distribución).

Un intervalo de tolerancia (L, U) garantiza que, con confianza ``1−α``, al
menos una fracción ``p`` de la población cae dentro del intervalo.

Referencias
-----------
* Howe, W.G. (1969). Two-sided tolerance limits for normal populations.
  *JASA*, 64(326), 610–620.
* Wald, A. & Wolfowitz, J. (1946). Tolerance limits for a normal distribution.
  *Ann. Math. Statist.*, 17(2), 208–215.
* Young, D.S. (2010). tolerance: An R package for estimating tolerance intervals.
  *JSS*, 36(5).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from ._data import as_1d, _excel_writer

NAN = float("nan")


# ─────────────────────────────────────────────────── factor k para normal ─────
def _k_normal_two(n: int, p: float, confidence: float) -> float:
    """Factor k de Howe (1969) para intervalo bilateral normal."""
    alpha = 1.0 - confidence
    z = stats.norm.ppf((1.0 + p) / 2.0)
    chi2_a = stats.chi2.ppf(alpha, n - 1)
    return float(z * math.sqrt((n - 1) * (1.0 + 1.0 / n) / chi2_a))


def _k_normal_one(n: int, p: float, confidence: float) -> float:
    """Factor k exacto (t no central) para intervalo unilateral normal."""
    nc = stats.norm.ppf(p) * math.sqrt(n)
    return float(stats.nct.ppf(confidence, n - 1, nc) / math.sqrt(n))


# ──────────────────────────────────────────────── índice para no paramétrico ──
def _nonparam_indices(n: int, p: float, confidence: float, sides: str):
    """Devuelve (r, achieved_conf) para el intervalo no paramétrico.

    r es el índice inferior (1-based); el superior es n-r+1 para dos lados,
    o r para la cota unilateral.
    """
    alpha = 1.0 - confidence
    if sides == "two":
        for r in range(1, n // 2 + 1):
            # P(cobertura >= p) = P(Beta(n-2r+1, 2r-1) >= p)
            # = P(Beta >= p) = 1 - I_p(n-2r+1, 2r-1)... wait, regularized
            # = betainc complement
            achieved = 1.0 - stats.beta.cdf(p, n - 2 * r + 1, 2 * r - 1)
            if achieved >= 1.0 - alpha:
                return r, float(achieved)
        return None, NAN
    else:  # one-sided
        for r in range(1, n + 1):
            if sides == "lower":
                # P(X_(r) < p-fraction lower bound) = P(Bin(n, 1-p) >= r)
                achieved = float(stats.binom.sf(r - 1, n, 1.0 - p))
            else:
                achieved = float(stats.binom.sf(r - 1, n, 1.0 - p))
            if achieved >= 1.0 - alpha:
                return r, float(achieved)
        return None, NAN


# ─────────────────────────────────────────────────────────── result object ────
@dataclass
class ToleranceResult:
    """Resultado de :func:`tolerance_interval`.

    Atributos
    ---------
    n : int
        Número de observaciones.
    mean, std : float
        Media y desviación estándar muestrales.
    coverage : float
        Fracción mínima de la población cubierta (p).
    confidence : float
        Nivel de confianza (1−α).
    sides : str
        ``'two'``, ``'lower'`` o ``'upper'``.
    method : str
        ``'normal'`` o ``'nonparametric'``.
    lower, upper : float o None
        Cotas del intervalo.
    k_factor : float o None
        Factor k (solo para el método normal).
    achieved_confidence : float o None
        Confianza alcanzada (solo para el método no paramétrico).
    """

    n: int
    mean: float
    std: float
    coverage: float
    confidence: float
    sides: str
    method: str
    lower: float | None
    upper: float | None
    k_factor: float | None = None
    achieved_confidence: float | None = None
    data: np.ndarray = None  # type: ignore[assignment]

    def to_frame(self) -> pd.DataFrame:
        """Tabla resumen de una fila por estadístico."""
        rows = [
            ("N", self.n),
            ("Media", self.mean),
            ("Desv.Est.", self.std),
            ("Cobertura (p)", self.coverage),
            ("Confianza (1−α)", self.confidence),
            ("Método", self.method),
            ("Lados", self.sides),
        ]
        if self.k_factor is not None:
            rows.append(("Factor k", round(self.k_factor, 5)))
        if self.achieved_confidence is not None:
            rows.append(("Confianza alcanzada", round(self.achieved_confidence, 5)))
        if self.lower is not None:
            rows.append(("Límite inferior", self.lower))
        if self.upper is not None:
            rows.append(("Límite superior", self.upper))
        return pd.DataFrame(rows, columns=["estadístico", "valor"]).set_index("estadístico")

    def summary(self) -> str:
        o = self
        p100, g100 = round(o.coverage * 100, 1), round(o.confidence * 100, 1)
        achieved = (f"  Confianza alcanzada: {o.achieved_confidence * 100:.2f}%"
                    if o.achieved_confidence is not None else "")
        k_txt = f"  Factor k = {o.k_factor:.5f}" if o.k_factor is not None else ""
        lines = [
            f"Intervalo de tolerancia ({o.method}, {o.sides})",
            f"  N={o.n}  Cobertura≥{p100}%  Confianza={g100}%",
            f"  Media={o.mean:.5g}  Desv.Est.={o.std:.5g}",
        ]
        if k_txt:
            lines.append(k_txt)
        if achieved:
            lines.append(achieved)
        interval = []
        if o.lower is not None:
            interval.append(f"LI = {o.lower:.5g}")
        if o.upper is not None:
            interval.append(f"LS = {o.upper:.5g}")
        lines.append("  " + "   ".join(interval))
        return "\n".join(lines)

    def to_excel(self, path) -> None:
        """Exporta el intervalo de tolerancia a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name="Tolerancia")

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        """Histograma con el intervalo de tolerancia superpuesto."""
        from .plotting import plot_tolerance

        return plot_tolerance(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


# ──────────────────────────────────────────────────────────── public API ──────
def tolerance_interval(
    data,
    coverage: float = 0.95,
    confidence: float = 0.95,
    *,
    sides: str = "two",
    method: str = "normal",
) -> ToleranceResult:
    """Intervalo de tolerancia estadístico.

    Calcula un intervalo (L, U) tal que, con confianza ``confidence``,
    al menos una fracción ``coverage`` de la población cae en (L, U).

    Parameters
    ----------
    data : array-like
        Vector 1-D de observaciones.
    coverage : float
        Fracción mínima de la población a cubrir (p). Por defecto 0.95.
    confidence : float
        Nivel de confianza 1−α. Por defecto 0.95.
    sides : str
        ``'two'`` (bilateral), ``'lower'`` (cota inferior) o ``'upper'``
        (cota superior). Por defecto ``'two'``.
    method : str
        ``'normal'`` — asume distribución normal; usa la aproximación de Howe
        (1969) para bilateral y la t no central exacta para unilateral.

        ``'nonparametric'`` — libre de distribución; se basa en estadísticos
        de orden; requiere muestras más grandes para la misma cobertura y
        confianza.

    Returns
    -------
    ToleranceResult

    Examples
    --------
    >>> import numpy as np, pccpy as pp
    >>> rng = np.random.default_rng(1)
    >>> x = rng.normal(100, 2, 50)
    >>> res = pp.tolerance_interval(x, coverage=0.95, confidence=0.95)
    >>> print(res.summary())
    """
    x = as_1d(data, "data")
    n = len(x)
    if n < 2:
        raise ValueError("Se necesitan al menos 2 observaciones.")
    if not 0 < coverage < 1:
        raise ValueError("'coverage' debe estar en (0, 1).")
    if not 0 < confidence < 1:
        raise ValueError("'confidence' debe estar en (0, 1).")
    if sides not in ("two", "lower", "upper"):
        raise ValueError("'sides' debe ser 'two', 'lower' o 'upper'.")
    if method not in ("normal", "nonparametric"):
        raise ValueError("'method' debe ser 'normal' o 'nonparametric'.")

    xbar, s = float(x.mean()), float(x.std(ddof=1))

    if method == "normal":
        if sides == "two":
            k = _k_normal_two(n, coverage, confidence)
            lower, upper = xbar - k * s, xbar + k * s
        elif sides == "lower":
            k = _k_normal_one(n, coverage, confidence)
            lower, upper = xbar - k * s, None
        else:
            k = _k_normal_one(n, coverage, confidence)
            lower, upper = None, xbar + k * s
        return ToleranceResult(
            n=n, mean=xbar, std=s, coverage=coverage, confidence=confidence,
            sides=sides, method=method, lower=lower, upper=upper,
            k_factor=k, data=x,
        )

    # nonparametric
    xs = np.sort(x)
    if sides == "two":
        r, ach = _nonparam_indices(n, coverage, confidence, "two")
        if r is None:
            raise ValueError(
                f"El tamaño de muestra n={n} es insuficiente para el intervalo "
                f"no paramétrico con cobertura={coverage} y confianza={confidence}."
            )
        lower, upper = float(xs[r - 1]), float(xs[n - r])
    elif sides == "lower":
        r, ach = _nonparam_indices(n, coverage, confidence, "lower")
        if r is None:
            raise ValueError(f"n={n} insuficiente para el intervalo no paramétrico solicitado.")
        lower, upper = float(xs[r - 1]), None
    else:
        r, ach = _nonparam_indices(n, coverage, confidence, "upper")
        if r is None:
            raise ValueError(f"n={n} insuficiente para el intervalo no paramétrico solicitado.")
        lower, upper = None, float(xs[n - r])

    return ToleranceResult(
        n=n, mean=xbar, std=s, coverage=coverage, confidence=confidence,
        sides=sides, method=method, lower=lower, upper=upper,
        achieved_confidence=ach, data=x,
    )


def tolerance_interval_summary(
    mean: float,
    std: float,
    n: int,
    coverage: float = 0.95,
    confidence: float = 0.95,
    *,
    sides: str = "two",
) -> ToleranceResult:
    """Intervalo de tolerancia normal a partir de estadísticos resumen.

    Equivalente a :func:`tolerance_interval` con ``method='normal'``, pero
    acepta la media, desviación estándar y tamaño de muestra directamente
    en lugar de datos crudos.

    Parameters
    ----------
    mean : float
        Media muestral.
    std : float
        Desviación estándar muestral (ddof=1).
    n : int
        Número de observaciones.
    coverage : float
        Fracción mínima de la población a cubrir (p). Por defecto 0.95.
    confidence : float
        Nivel de confianza 1−α. Por defecto 0.95.
    sides : str
        ``'two'``, ``'lower'`` o ``'upper'``. Por defecto ``'two'``.

    Returns
    -------
    ToleranceResult

    Examples
    --------
    >>> import pccpy as pp
    >>> res = pp.tolerance_interval_summary(mean=100.0, std=2.0, n=50)
    >>> print(res.summary())
    """
    if std <= 0:
        raise ValueError("'std' debe ser positivo.")
    if n < 2:
        raise ValueError("'n' debe ser ≥ 2.")
    if not 0 < coverage < 1:
        raise ValueError("'coverage' debe estar en (0, 1).")
    if not 0 < confidence < 1:
        raise ValueError("'confidence' debe estar en (0, 1).")
    if sides not in ("two", "lower", "upper"):
        raise ValueError("'sides' debe ser 'two', 'lower' o 'upper'.")

    xbar, s = float(mean), float(std)
    if sides == "two":
        k = _k_normal_two(n, coverage, confidence)
        lower, upper = xbar - k * s, xbar + k * s
    elif sides == "lower":
        k = _k_normal_one(n, coverage, confidence)
        lower, upper = xbar - k * s, None
    else:
        k = _k_normal_one(n, coverage, confidence)
        lower, upper = None, xbar + k * s

    return ToleranceResult(
        n=n, mean=xbar, std=s, coverage=coverage, confidence=confidence,
        sides=sides, method="normal", lower=lower, upper=upper,
        k_factor=k, data=np.array([]),
    )
