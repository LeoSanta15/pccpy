"""Capacidad del proceso para datos de atributos (equivalente a Minitab: Capability Analysis > Binomial / Poisson).

* **Binomial** (unidades defectuosas en muestras de tamaño ``n``): proporción defectiva ``p̄ = Σd / Σn`` con intervalo
  exacto de Clopper-Pearson, PPM defectivo, nivel Z del proceso ``Z = Φ⁻¹(1 − p̄)`` (con el intervalo que sale del de
  ``p̄``) y la prueba chi-cuadrado de que ``p`` es constante entre muestras.
* **Poisson** (defectos en ``u`` unidades): defectos por unidad ``DPU = Σd / Σu`` con intervalo exacto de Garwood, y la
  prueba chi-cuadrado de dispersión (¿es constante la tasa entre muestras?). Con ``opportunities=`` se añaden el DPMO y el
  nivel Z.

La prueba de homogeneidad avisa de lo que importa en la práctica: si ``p`` (o la tasa) no es constante, ``p̄`` no
describe un proceso estable y la capacidad calculada no es fiable (revise antes la carta de control).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from ._data import _excel_writer, as_1d
from ._frames import tabla_estadisticos
from ._i18n import N_, tr

NAN = float("nan")


def _z(p: float) -> float:
    """Nivel Z del proceso: Φ⁻¹(1 − p)."""
    if not 0 <= p <= 1:
        return NAN
    return float(stats.norm.isf(p)) if 0 < p < 1 else (math.inf if p == 0 else -math.inf)


def _contar(valor, nombre: str) -> np.ndarray:
    x = as_1d(valor, nombre)
    if x.size == 0:
        raise ValueError(tr("'{nombre}' no puede estar vacío.").format(nombre=nombre))
    if np.any(x < 0) or np.any(x != np.round(x)):
        raise ValueError(tr("'{nombre}' debe contener enteros no negativos.").format(nombre=nombre))
    return x


def _tamanos(n, k: int) -> np.ndarray:
    a = np.asarray(n, dtype=float)
    if a.ndim == 0:
        a = np.full(k, float(a))
    a = a.ravel()
    if a.size != k:
        raise ValueError(tr("'n' debe ser un número o tener la misma longitud que los datos ({k}).").format(k=k))
    return a


def _nivel(confidence: float) -> float:
    if not 0 < confidence < 1:
        raise ValueError(tr("'confidence' debe estar en (0, 1)."))
    return float(confidence)


# ─────────────────────────────────────────────────────────── binomial ─────────
@dataclass
class BinomialCapabilityResult:
    """Capacidad binomial: proporción defectiva, PPM y nivel Z con sus intervalos."""

    n_samples: int
    n_total: float
    defectives: float
    p_bar: float
    p_ci: tuple[float, float]
    ppm: float
    ppm_ci: tuple[float, float]
    z: float
    z_ci: tuple[float, float]
    chi2: float
    chi2_df: int
    p_value_homogeneity: float
    ci_level: float
    p_min: float
    p_max: float
    proportions: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)
    sizes: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)
    counts: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def homogeneous(self) -> bool:
        """``True`` si no se rechaza que ``p`` sea constante entre muestras (nivel 0,05)."""
        return not (self.p_value_homogeneity < 0.05)

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico; con ``stable=True`` claves canónicas en inglés)."""
        pct = round(100 * self.ci_level, 4)
        rows = [
            ("n_samples", N_("Muestras"), self.n_samples), ("n_total", N_("Unidades inspeccionadas"), self.n_total),
            ("defectives", N_("Defectuosas"), self.defectives),
            ("p_bar_pct", N_("% defectivo (p̄)"), 100 * self.p_bar),
            ("p_lower_pct", N_("% defectivo, límite inferior"), 100 * self.p_ci[0]),
            ("p_upper_pct", N_("% defectivo, límite superior"), 100 * self.p_ci[1]),
            ("ppm", N_("PPM defectivo"), self.ppm),
            ("ppm_lower", N_("PPM, límite inferior"), self.ppm_ci[0]),
            ("ppm_upper", N_("PPM, límite superior"), self.ppm_ci[1]),
            ("z", N_("Z del proceso"), self.z),
            ("z_lower", N_("Z, límite inferior"), self.z_ci[0]), ("z_upper", N_("Z, límite superior"), self.z_ci[1]),
            ("p_min_pct", N_("% defectivo mínimo"), 100 * self.p_min), ("p_max_pct", N_("% defectivo máximo"), 100 * self.p_max),
            ("chi2", N_("Chi-cuadrado (p constante)"), self.chi2), ("chi2_df", N_("GL"), self.chi2_df),
            ("p_value_homogeneity", N_("Valor p (p constante)"), self.p_value_homogeneity),
            ("ci_level_pct", N_("Nivel de confianza (%)"), pct),
        ]
        return tabla_estadisticos(rows, stable)

    def summary(self) -> str:
        pct = 100 * self.ci_level
        lines = [
            tr("Capacidad del proceso — datos binomiales"),
            tr("  Muestras={k}  Unidades={n:g}  Defectuosas={d:g}").format(k=self.n_samples, n=self.n_total,
                                                                          d=self.defectives),
            tr("  % defectivo={p:.4f}  IC {nivel:g}%: ({lo:.4f}, {hi:.4f})").format(
                p=100 * self.p_bar, nivel=pct, lo=100 * self.p_ci[0], hi=100 * self.p_ci[1]),
            tr("  PPM defectivo={ppm:.1f}  IC: ({lo:.1f}, {hi:.1f})").format(
                ppm=self.ppm, lo=self.ppm_ci[0], hi=self.ppm_ci[1]),
            tr("  Z del proceso={z:.3f}  IC: ({lo:.3f}, {hi:.3f})").format(z=self.z, lo=self.z_ci[0], hi=self.z_ci[1]),
        ]
        if not math.isnan(self.p_value_homogeneity):
            lines.append(tr("  p constante: chi²={c:.2f} (GL={gl}), valor p={p:.4f}").format(
                c=self.chi2, gl=self.chi2_df, p=self.p_value_homogeneity))
            if not self.homogeneous:
                lines.append(tr("  Aviso: p no es constante entre muestras; el proceso no es estable y la capacidad "
                                "calculada no es fiable (revise la carta P)."))
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def to_excel(self, path) -> None:
        """Exporta el resumen a un archivo Excel (.xlsx). Requiere ``openpyxl``."""
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Capacidad"))

    def plot(self, **kwargs):
        """Proporción defectiva por muestra y estimación acumulada con su intervalo."""
        from .plotting import plot_capability_attributes

        return plot_capability_attributes(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def clopper_pearson(d: float, n: float, confidence: float = 0.95) -> tuple[float, float]:
    """Intervalo exacto (Clopper-Pearson) de una proporción: ``d`` defectuosas en ``n`` unidades."""
    a = 1 - confidence
    lo = 0.0 if d == 0 else float(stats.beta.ppf(a / 2, d, n - d + 1))
    hi = 1.0 if d == n else float(stats.beta.ppf(1 - a / 2, d + 1, n - d))
    return lo, hi


def capability_binomial(defectives, n, *, confidence: float = 0.95) -> BinomialCapabilityResult:
    """Capacidad del proceso con datos binomiales (unidades defectuosas por muestra).

    Parameters
    ----------
    defectives : array-like
        Número de unidades defectuosas en cada muestra.
    n : int | array-like
        Tamaño de las muestras (constante o uno por muestra).
    confidence : float
        Nivel de confianza de los intervalos (por defecto 0,95).

    Returns
    -------
    BinomialCapabilityResult
    """
    nivel = _nivel(confidence)
    d = _contar(defectives, "defectives")
    tam = _tamanos(n, d.size)
    if np.any(tam <= 0) or np.any(tam != np.round(tam)):
        raise ValueError(tr("'n' debe contener enteros positivos."))
    if np.any(d > tam):
        raise ValueError(tr("Hay más defectuosas que unidades en alguna muestra."))
    D, N = float(d.sum()), float(tam.sum())
    p = D / N
    lo, hi = clopper_pearson(D, N, nivel)
    prop = d / tam
    if d.size > 1 and 0 < p < 1:
        chi2 = float(np.sum((d - tam * p) ** 2 / (tam * p * (1 - p))))
        gl = d.size - 1
        pv = float(stats.chi2.sf(chi2, gl))
    else:
        chi2, gl, pv = NAN, max(d.size - 1, 0), NAN
    return BinomialCapabilityResult(
        n_samples=int(d.size), n_total=N, defectives=D, p_bar=p, p_ci=(lo, hi), ppm=1e6 * p,
        ppm_ci=(1e6 * lo, 1e6 * hi), z=_z(p), z_ci=(_z(hi), _z(lo)), chi2=chi2, chi2_df=gl,
        p_value_homogeneity=pv, ci_level=nivel, p_min=float(prop.min()), p_max=float(prop.max()),
        proportions=prop, sizes=tam, counts=d)


# ─────────────────────────────────────────────────────────── Poisson ──────────
@dataclass
class PoissonCapabilityResult:
    """Capacidad Poisson: defectos por unidad (DPU) con su intervalo exacto."""

    n_samples: int
    units_total: float
    defects: float
    dpu: float
    dpu_ci: tuple[float, float]
    dpu_min: float
    dpu_max: float
    chi2: float
    chi2_df: int
    p_value_homogeneity: float
    ci_level: float
    opportunities: float | None = None
    dpmo: float = NAN
    z: float = NAN
    rates: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)
    units: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)
    counts: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def homogeneous(self) -> bool:
        """``True`` si no se rechaza que la tasa sea constante entre muestras (nivel 0,05)."""
        return not (self.p_value_homogeneity < 0.05)

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico; con ``stable=True`` claves canónicas en inglés)."""
        rows = [
            ("n_samples", N_("Muestras"), self.n_samples), ("units_total", N_("Unidades inspeccionadas"), self.units_total),
            ("defects", N_("Defectos"), self.defects), ("dpu", N_("DPU (defectos por unidad)"), self.dpu),
            ("dpu_lower", N_("DPU, límite inferior"), self.dpu_ci[0]),
            ("dpu_upper", N_("DPU, límite superior"), self.dpu_ci[1]),
            ("dpu_min", N_("DPU mínimo"), self.dpu_min), ("dpu_max", N_("DPU máximo"), self.dpu_max),
            ("chi2", N_("Chi-cuadrado (tasa constante)"), self.chi2), ("chi2_df", N_("GL"), self.chi2_df),
            ("p_value_homogeneity", N_("Valor p (tasa constante)"), self.p_value_homogeneity),
            ("ci_level_pct", N_("Nivel de confianza (%)"), round(100 * self.ci_level, 4)),
        ]
        if self.opportunities is not None:
            rows += [("opportunities", N_("Oportunidades por unidad"), self.opportunities),
                     ("dpmo", N_("DPMO"), self.dpmo), ("z", N_("Z del proceso"), self.z)]
        return tabla_estadisticos(rows, stable)

    def summary(self) -> str:
        pct = 100 * self.ci_level
        lines = [
            tr("Capacidad del proceso — datos Poisson"),
            tr("  Muestras={k}  Unidades={u:g}  Defectos={d:g}").format(k=self.n_samples, u=self.units_total,
                                                                       d=self.defects),
            tr("  DPU={dpu:.5f}  IC {nivel:g}%: ({lo:.5f}, {hi:.5f})").format(
                dpu=self.dpu, nivel=pct, lo=self.dpu_ci[0], hi=self.dpu_ci[1]),
        ]
        if self.opportunities is not None:
            lines.append(tr("  DPMO={dpmo:.1f}  Z del proceso={z:.3f}").format(dpmo=self.dpmo, z=self.z))
        if not math.isnan(self.p_value_homogeneity):
            lines.append(tr("  Tasa constante: chi²={c:.2f} (GL={gl}), valor p={p:.4f}").format(
                c=self.chi2, gl=self.chi2_df, p=self.p_value_homogeneity))
            if not self.homogeneous:
                lines.append(tr("  Aviso: la tasa no es constante entre muestras; el proceso no es estable y la "
                                "capacidad calculada no es fiable (revise la carta U)."))
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def to_excel(self, path) -> None:
        """Exporta el resumen a un archivo Excel (.xlsx). Requiere ``openpyxl``."""
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Capacidad"))

    def plot(self, **kwargs):
        """Defectos por unidad en cada muestra y estimación acumulada con su intervalo."""
        from .plotting import plot_capability_attributes

        return plot_capability_attributes(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def garwood(d: float, exposure: float, confidence: float = 0.95) -> tuple[float, float]:
    """Intervalo exacto (Garwood) de una tasa de Poisson: ``d`` defectos en ``exposure`` unidades."""
    a = 1 - confidence
    lo = 0.0 if d == 0 else float(stats.chi2.ppf(a / 2, 2 * d)) / (2 * exposure)
    hi = float(stats.chi2.ppf(1 - a / 2, 2 * d + 2)) / (2 * exposure)
    return lo, hi


def capability_poisson(defects, units=1, *, opportunities: float | None = None,
                       confidence: float = 0.95) -> PoissonCapabilityResult:
    """Capacidad del proceso con datos Poisson (defectos por muestra de ``units`` unidades).

    Parameters
    ----------
    defects : array-like
        Número de defectos observados en cada muestra.
    units : int | float | array-like
        Unidades inspeccionadas en cada muestra (constante o una por muestra). Por defecto 1.
    opportunities : float, opcional
        Oportunidades de defecto por unidad. Si se indica, se calculan el DPMO y el nivel Z.
    confidence : float
        Nivel de confianza del intervalo (por defecto 0,95).

    Returns
    -------
    PoissonCapabilityResult
    """
    nivel = _nivel(confidence)
    d = _contar(defects, "defects")
    u = _tamanos(units, d.size)
    if np.any(u <= 0):
        raise ValueError(tr("'units' debe contener valores positivos."))
    if opportunities is not None and not opportunities > 0:
        raise ValueError(tr("'opportunities' debe ser positivo."))
    D, U = float(d.sum()), float(u.sum())
    dpu = D / U
    lo, hi = garwood(D, U, nivel)
    tasa = d / u
    if d.size > 1 and dpu > 0:
        chi2 = float(np.sum((d - u * dpu) ** 2 / (u * dpu)))
        gl = d.size - 1
        pv = float(stats.chi2.sf(chi2, gl))
    else:
        chi2, gl, pv = NAN, max(d.size - 1, 0), NAN
    dpmo = 1e6 * dpu / opportunities if opportunities is not None else NAN
    z = _z(dpu / opportunities) if opportunities is not None else NAN
    return PoissonCapabilityResult(
        n_samples=int(d.size), units_total=U, defects=D, dpu=dpu, dpu_ci=(lo, hi), dpu_min=float(tasa.min()),
        dpu_max=float(tasa.max()), chi2=chi2, chi2_df=gl, p_value_homogeneity=pv, ci_level=nivel,
        opportunities=opportunities, dpmo=dpmo, z=z, rates=tasa, units=u, counts=d)
