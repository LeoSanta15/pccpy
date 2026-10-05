"""Muestreo de aceptación: Z1.4 (atributos), Z1.9 (variables) y Dodge-Romig.

Referencias
-----------
* ANSI/ASQ Z1.4-2008: Sampling Procedures and Tables for Inspection by Attributes.
* ANSI/ASQ Z1.9-2008: Sampling Procedures and Tables for Inspection by Variables.
* Dodge, H.F. & Romig, H.G. (1959). Sampling Inspection Tables. Wiley.
* Montgomery, D.C. (2013). *Introduction to Statistical Quality Control*, 7th ed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq

from ._data import _excel_writer
from ._frames import renombrar, tabla_estadisticos
from ._i18n import N_, tr

_COLUMNAS_OC = {N_("p_defectivo"): "defective_fraction", N_("P(aceptar)"): "p_accept"}
_COLUMNAS_AOQ = {N_("p_defectivo"): "defective_fraction", N_("AOQ"): "aoq"}


# ──────────────────────────────────────────────────── curva OC (binomial) ────
def _pa_binomial(n: int, c: int, p: float) -> float:
    """P(aceptar | fracción defectiva p) para un plan (n, c) por atributos."""
    return float(stats.binom.cdf(c, n, p))


def _pa_binomial_arr(n: int, c: int, p_arr: np.ndarray) -> np.ndarray:
    return stats.binom.cdf(c, n, p_arr)


# ─────────────────────────────────────────────────────────── Z1.4 ─────────────
# Tablas simplificadas de la norma Z1.4 — niveles de inspección II (general).
# Formato: AQL → [(n, c), ...] para tamaños de lote crecientes.
# Tamaños de lote: 2-8, 9-15, 16-25, 26-50, 51-90, 91-150, 151-280, 281-500,
#   501-1200, 1201-3200, 3201-10000, 10001-35000, 35001-150000, 150001-500000, >500000
_LOTE_LIMITES = [8, 15, 25, 50, 90, 150, 280, 500, 1200, 3200, 10000, 35000, 150000, 500000]

# Letra de código según tamaño de lote e inspección general nivel II
_LETRAS_CODIGO = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q"]

def _letra_codigo(N: int) -> str:
    for lim, letra in zip(_LOTE_LIMITES, _LETRAS_CODIGO):
        if N <= lim:
            return letra
    return "Q"


# Tabla II-A de Z1.4 (inspección normal, muestreo simple). Cada letra tiene un tamaño de muestra; el número de
# aceptación depende de la diagonal i + j (i = posición de la letra, j = posición del AQL): la diagonal 14 es Ac = 0 y
# a partir de la 17 sigue la serie 1, 2, 3, 5, 7, 10, 14, 21. Entre ambas diagonales (y fuera de ellas) la norma usa
# flechas: se aplica el plan al que apuntan, con otro tamaño de muestra.
_N_LETRA = [2, 3, 5, 8, 13, 20, 32, 50, 80, 125, 200, 315, 500, 800, 1250]
_AC_DIAGONAL = {14: 0, 17: 1, 18: 2, 19: 3, 20: 5, 21: 7, 22: 10, 23: 14, 24: 21}


def _plan_z14(letra: str, aql: float) -> tuple[int, int]:
    """Plan (n, Ac) de la tabla Z1.4 para una letra y un AQL, resolviendo las flechas de la norma."""
    i, j = _LETRAS_CODIGO.index(letra), _AQL_STEPS.index(aql)
    s = i + j
    if s < 14:  # a la izquierda de Ac = 0: ↓ al plan con Ac = 0 y más muestra
        s = 14
    elif 14 < s < 17:  # entre Ac = 0 y Ac = 1: ↑ al plan con Ac = 0 (si no existe, ↓ al de Ac = 1)
        s = 14 if 14 - j >= 0 else 17
    elif s > 24:  # más allá de Ac = 21: ↑ a ese plan con menos muestra
        s = 24
    return _N_LETRA[s - j], _AC_DIAGONAL[s]


_AQL_STEPS = [0.010, 0.015, 0.025, 0.040, 0.065, 0.10, 0.15, 0.25, 0.40, 0.65,
              1.0, 1.5, 2.5, 4.0, 6.5, 10.0]


def _nearest_aql(aql: float) -> float:
    return min(_AQL_STEPS, key=lambda a: abs(a - aql))


@dataclass
class SamplingPlanAttributes:
    """Plan de muestreo de aceptación por atributos.

    Atributos
    ---------
    N : int
        Tamaño del lote.
    n : int
        Tamaño de la muestra.
    c : int
        Número de aceptación.
    aql : float
        AQL usado (% o fracción).
    alpha : float
        Riesgo del productor (P(rechazar | AQL)).
    beta : float
        Riesgo del consumidor (P(aceptar | LTPD)).
    ltpd : float
        LTPD real del plan.
    aoq_max : float
        AOQL (calidad media de salida máxima).
    method : str
        ``'z1.4'`` o ``'custom'``.
    """

    N: int
    n: int
    c: int
    aql: float
    alpha: float
    beta: float
    ltpd: float
    aoq_max: float
    method: str
    _p_arr: np.ndarray = field(repr=False)
    _pa_arr: np.ndarray = field(repr=False)

    def pa(self, p: float) -> float:
        """Probabilidad de aceptar para fracción defectiva p."""
        return _pa_binomial(self.n, self.c, p)

    def oc_curve(self, stable: bool = False) -> pd.DataFrame:
        """Curva OC: fracción defectiva vs probabilidad de aceptación.

        Con ``stable=True`` las columnas son ``defective_fraction`` y ``p_accept`` (no cambian con el idioma).
        """
        return renombrar(pd.DataFrame({"p_defectivo": self._p_arr, "P(aceptar)": self._pa_arr}), _COLUMNAS_OC, stable)

    def aoq_curve(self, stable: bool = False) -> pd.DataFrame:
        """Curva de calidad media de salida (AOQ) vs fracción defectiva entrante.

        Con ``stable=True`` las columnas son ``defective_fraction`` y ``aoq``.
        """
        aoq = self._pa_arr * self._p_arr * (self.N - self.n) / self.N
        return renombrar(pd.DataFrame({"p_defectivo": self._p_arr, "AOQ": aoq}), _COLUMNAS_AOQ, stable)

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico; con ``stable=True`` claves canónicas en inglés)."""
        rows = [
            ("lot_size", N_("N (tamaño de lote)"), self.N),
            ("sample_size", N_("n (tamaño de muestra)"), self.n),
            ("acceptance_number", N_("c (número de aceptación)"), self.c),
            ("aql_pct", N_("AQL (%)"), round(self.aql, 4)),
            ("ltpd_pct", N_("LTPD (%)"), round(self.ltpd * 100, 4)),
            ("alpha", N_("α (riesgo productor)"), round(self.alpha, 5)),
            ("beta", N_("β (riesgo consumidor = 0.10)"), round(self.beta, 5)),
            ("aoql_pct", N_("AOQL (%)"), round(self.aoq_max * 100, 4)),
            ("method", N_("Método"), self.method),
        ]
        return tabla_estadisticos(rows, stable)

    def summary(self) -> str:
        return "\n".join([
            tr("Plan de muestreo por atributos ({method})").format(method=self.method),
            tr("  Lote N={N}  Muestra n={n}  Ac={c}  Re={r}").format(N=self.N, n=self.n, c=self.c, r=self.c + 1),
            tr("  AQL={aql:.3g}%  α={alpha:.4f}  LTPD={ltpd:.3g}%  β=0.10").format(
                aql=self.aql, alpha=self.alpha, ltpd=self.ltpd * 100),
            tr("  AOQL={aoql:.3g}%").format(aoql=self.aoq_max * 100),
        ])

    def to_excel(self, path) -> None:
        """Exporta el plan de muestreo a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Plan"))

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        """Curva OC y curva AOQ."""
        from .plotting import plot_sampling_attributes
        return plot_sampling_attributes(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt
        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def _build_attr_plan(N: int, n: int, c: int, aql_frac: float, method: str) -> SamplingPlanAttributes:
    p_arr = np.linspace(0, min(1.0, max(0.5, aql_frac * 10)), 400)
    pa_arr = _pa_binomial_arr(n, c, p_arr)

    alpha = 1.0 - _pa_binomial(n, c, aql_frac)

    # LTPD @ beta=0.10
    try:
        ltpd = brentq(lambda p: _pa_binomial(n, c, p) - 0.10, aql_frac, 1.0 - 1e-9)
    except ValueError:
        ltpd = float("nan")

    # AOQL
    aoq_arr = pa_arr * p_arr * (N - n) / N
    aoq_max = float(aoq_arr.max())

    return SamplingPlanAttributes(
        N=N, n=n, c=c, aql=aql_frac * 100, alpha=alpha,
        beta=0.10, ltpd=ltpd, aoq_max=aoq_max, method=method,
        _p_arr=p_arr, _pa_arr=pa_arr,
    )


def acceptance_sampling_attributes(
    N: int,
    aql: float,
    *,
    inspection_level: int = 2,
    n: int | None = None,
    c: int | None = None,
) -> SamplingPlanAttributes:
    """Plan de muestreo de aceptación por atributos (ANSI/ASQ Z1.4).

    Parameters
    ----------
    N : int
        Tamaño del lote.
    aql : float
        AQL en porcentaje (p.ej. 1.0 para 1%). Valores válidos de Z1.4:
        0.010, 0.015, 0.025, 0.040, 0.065, 0.10, 0.15, 0.25, 0.40, 0.65,
        1.0, 1.5, 2.5, 4.0, 6.5, 10.0.
    inspection_level : int
        Nivel de inspección general (1, 2 o 3). Por defecto 2.
    n : int, opcional
        Tamaño de muestra personalizado (omite la tabla Z1.4).
    c : int, opcional
        Número de aceptación personalizado.

    Returns
    -------
    SamplingPlanAttributes
    """
    if N < 2:
        raise ValueError(tr("N debe ser ≥ 2."))
    if not 0 < aql <= 10:
        raise ValueError(tr("'aql' debe estar en (0, 10] %."))

    if n is not None and c is not None:
        aql_frac = aql / 100.0
        return _build_attr_plan(N, n, c, aql_frac, "custom")

    # Use Z1.4 table
    # Adjust letter for inspection level (level I shifts left 2, level III shifts right 2)
    letra = _letra_codigo(N)
    letters = _LETRAS_CODIGO
    idx = letters.index(letra)
    if inspection_level == 1:
        idx = max(0, idx - 2)
    elif inspection_level == 3:
        idx = min(len(letters) - 1, idx + 2)
    letra = letters[idx]

    aql_key = _nearest_aql(aql)
    n_plan, c_plan = _plan_z14(letra, aql_key)
    aql_frac = aql_key / 100.0
    return _build_attr_plan(N, n_plan, c_plan, aql_frac, "z1.4")


# ─────────────────────────────────────────────────────────── Z1.9 ─────────────
@dataclass
class SamplingPlanVariables:
    """Plan de muestreo de aceptación por variables (ANSI/ASQ Z1.9 / método k).

    Atributos
    ---------
    N : int
        Tamaño del lote.
    n : int
        Tamaño de la muestra.
    k : float
        Factor de aceptabilidad k.
    aql : float
        AQL en %.
    spec_type : str
        ``'one'`` (unilateral) o ``'two'`` (bilateral).
    alpha : float
        Riesgo del productor.
    ltpd : float
        LTPD (p en % a beta=0.10).
    method : str
        ``'z1.9'`` o ``'custom'``.
    """

    N: int
    n: int
    k: float
    aql: float
    spec_type: str
    alpha: float
    ltpd: float
    method: str

    def pa(self, p: float) -> float:
        """P(aceptar | fracción defectiva p) — aproximación normal."""
        return _pa_variables(self.n, self.k, p, self.spec_type)

    def oc_curve(self, stable: bool = False) -> pd.DataFrame:
        """Curva OC del plan (``stable=True``: columnas ``defective_fraction`` y ``p_accept``)."""
        p_arr = np.linspace(0, min(0.5, self.ltpd * 3), 300)
        pa_arr = np.array([self.pa(p) for p in p_arr])
        return renombrar(pd.DataFrame({"p_defectivo": p_arr, "P(aceptar)": pa_arr}), _COLUMNAS_OC, stable)

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico; con ``stable=True`` claves canónicas en inglés)."""
        rows = [
            ("lot_size", N_("N (tamaño de lote)"), self.N),
            ("sample_size", N_("n (tamaño de muestra)"), self.n),
            ("k", N_("k (factor de aceptabilidad)"), round(self.k, 4)),
            ("aql_pct", N_("AQL (%)"), round(self.aql, 4)),
            ("ltpd_pct", N_("LTPD (%)"), round(self.ltpd * 100, 4)),
            ("alpha", N_("α (riesgo productor)"), round(self.alpha, 5)),
            ("beta", N_("β (riesgo consumidor = 0.10)"), 0.10),
            ("spec_type", N_("Tipo de especificación"), self.spec_type),
            ("method", N_("Método"), self.method),
        ]
        return tabla_estadisticos(rows, stable)

    def summary(self) -> str:
        return "\n".join([
            tr("Plan de muestreo por variables ({method})").format(method=self.method),
            tr("  Lote N={N}  Muestra n={n}  k={k:.4f}").format(N=self.N, n=self.n, k=self.k),
            tr("  AQL={aql:.3g}%  α={alpha:.4f}  LTPD={ltpd:.3g}%  β=0.10").format(
                aql=self.aql, alpha=self.alpha, ltpd=self.ltpd * 100),
            tr("  Especificación: {spec_type}").format(spec_type=self.spec_type),
        ])

    def to_excel(self, path) -> None:
        """Exporta el plan de muestreo por variables a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Plan"))

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_sampling_variables
        return plot_sampling_variables(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt
        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)

    def evaluate(self, sample: np.ndarray, usl: float | None = None,
                 lsl: float | None = None) -> dict:
        """Evalúa si aceptar el lote a partir de la muestra.

        Returns dict con keys: xbar, s, Q_usl, Q_lsl, accept, criterion.
        """
        x = np.asarray(sample, dtype=float).ravel()
        xbar = float(x.mean())
        s = float(x.std(ddof=1))
        result: dict = {"xbar": xbar, "s": s}
        if usl is not None:
            result["Q_usl"] = (usl - xbar) / s if s > 0 else float("inf")
        if lsl is not None:
            result["Q_lsl"] = (xbar - lsl) / s if s > 0 else float("inf")

        if self.spec_type == "one":
            q = result.get("Q_usl", result.get("Q_lsl", float("nan")))
            result["accept"] = q >= self.k
            result["criterion"] = f"Q={q:.4f} {'≥' if result['accept'] else '<'} k={self.k:.4f}"
        else:  # two
            qu = result.get("Q_usl", float("inf"))
            ql = result.get("Q_lsl", float("inf"))
            result["accept"] = (qu >= self.k) and (ql >= self.k)
            result["criterion"] = (f"Q_usl={qu:.4f}, Q_lsl={ql:.4f} "
                                   f"vs k={self.k:.4f}")
        return result


def _pa_variables(n: int, k: float, p: float, spec_type: str) -> float:
    """P(aceptar | p) para un plan de variables con factor k.

    Aproximación normal de Montgomery (2013) sec. 15-3.
    """
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0
    zp = stats.norm.ppf(1.0 - p)
    if spec_type == "one":
        # Pa ≈ Phi(zp - k*sqrt(n) / sqrt(1 + k^2/2))
        nc = (zp - k) * math.sqrt(n) / math.sqrt(1.0 + k ** 2 / 2.0)
        return float(stats.norm.cdf(nc))
    else:
        # Two-sided: approximate as product of two one-sided
        pa1 = _pa_variables(n, k, p / 2.0, "one")
        return float(pa1 ** 2)


# Tabla Z1.9 simplificada: (AQL_pct, inspection_level_letter) → (n, k)
# Nivel de inspección II normal, una especificación (one-sided)
_Z19_TABLE: dict[tuple[float, str], tuple[int, float]] = {
    # AQL%, letter → (n, k)
    (0.10, "B"): (3, 1.12), (0.10, "C"): (3, 1.12), (0.10, "D"): (4, 1.17),
    (0.10, "E"): (5, 1.24), (0.10, "F"): (7, 1.33), (0.10, "G"): (10, 1.41),
    (0.10, "H"): (15, 1.50), (0.10, "J"): (20, 1.57), (0.10, "K"): (25, 1.62),
    (0.25, "B"): (3, 0.958), (0.25, "C"): (3, 0.958), (0.25, "D"): (4, 0.992),
    (0.25, "E"): (5, 1.03), (0.25, "F"): (7, 1.09), (0.25, "G"): (10, 1.16),
    (0.25, "H"): (15, 1.24), (0.25, "J"): (20, 1.30), (0.25, "K"): (25, 1.35),
    (0.65, "B"): (3, 0.663), (0.65, "C"): (3, 0.663), (0.65, "D"): (4, 0.692),
    (0.65, "E"): (5, 0.736), (0.65, "F"): (7, 0.810), (0.65, "G"): (10, 0.874),
    (0.65, "H"): (15, 0.955), (0.65, "J"): (20, 1.01), (0.65, "K"): (25, 1.05),
    (1.00, "B"): (3, 0.493), (1.00, "C"): (3, 0.493), (1.00, "D"): (4, 0.516),
    (1.00, "E"): (5, 0.566), (1.00, "F"): (7, 0.646), (1.00, "G"): (10, 0.716),
    (1.00, "H"): (15, 0.797), (1.00, "J"): (20, 0.851), (1.00, "K"): (25, 0.893),
    (2.50, "B"): (3, 0.120), (2.50, "C"): (3, 0.120), (2.50, "D"): (4, 0.152),
    (2.50, "E"): (5, 0.197), (2.50, "F"): (7, 0.280), (2.50, "G"): (10, 0.356),
    (2.50, "H"): (15, 0.437), (2.50, "J"): (20, 0.489), (2.50, "K"): (25, 0.529),
    (4.00, "B"): (3, -0.051), (4.00, "C"): (3, -0.051), (4.00, "D"): (4, -0.031),
    (4.00, "E"): (5, 0.011), (4.00, "F"): (7, 0.100), (4.00, "G"): (10, 0.173),
    (4.00, "H"): (15, 0.250), (4.00, "J"): (20, 0.303), (4.00, "K"): (25, 0.342),
}

_AQL_Z19 = [0.10, 0.25, 0.65, 1.0, 2.5, 4.0]


def acceptance_sampling_variables(
    N: int,
    aql: float,
    *,
    spec_type: str = "one",
    inspection_level: int = 2,
    n: int | None = None,
    k: float | None = None,
) -> SamplingPlanVariables:
    """Plan de muestreo de aceptación por variables (ANSI/ASQ Z1.9).

    Parameters
    ----------
    N : int
        Tamaño del lote.
    aql : float
        AQL en porcentaje. Valores Z1.9: 0.10, 0.25, 0.65, 1.0, 2.5, 4.0.
    spec_type : str
        ``'one'`` (una especificación, unilateral) o ``'two'`` (bilateral).
    inspection_level : int
        Nivel de inspección general (1, 2 o 3). Por defecto 2.
    n : int, opcional
        Tamaño de muestra personalizado.
    k : float, opcional
        Factor k personalizado.

    Returns
    -------
    SamplingPlanVariables
    """
    if N < 2:
        raise ValueError(tr("N debe ser ≥ 2."))
    if not 0 < aql <= 10:
        raise ValueError(tr("'aql' debe estar en (0, 10] %."))
    if spec_type not in ("one", "two"):
        raise ValueError(tr("'spec_type' debe ser 'one' o 'two'."))

    aql_frac = aql / 100.0

    if n is not None and k is not None:
        alpha = 1.0 - _pa_variables(n, k, aql_frac, spec_type)
        try:
            ltpd = brentq(lambda p: _pa_variables(n, k, p, spec_type) - 0.10, aql_frac, 0.9999)
        except ValueError:
            ltpd = float("nan")
        return SamplingPlanVariables(N=N, n=n, k=k, aql=aql, spec_type=spec_type,
                                     alpha=alpha, ltpd=ltpd, method="custom")

    # Z1.9 table lookup
    letra = _letra_codigo(N)
    letters = _LETRAS_CODIGO
    idx = letters.index(letra)
    if inspection_level == 1:
        idx = max(0, idx - 2)
    elif inspection_level == 3:
        idx = min(len(letters) - 1, idx + 2)
    letra = letters[idx]

    aql_key = min(_AQL_Z19, key=lambda a: abs(a - aql))
    key = (aql_key, letra)
    if key not in _Z19_TABLE:
        raise ValueError(tr(
            "Combinación AQL={aql_key}% y letra={letra} no disponible en la tabla Z1.9."
        ).format(aql_key=aql_key, letra=letra))

    n_plan, k_plan = _Z19_TABLE[key]
    alpha = 1.0 - _pa_variables(n_plan, k_plan, aql_key / 100.0, spec_type)
    try:
        ltpd = brentq(lambda p: _pa_variables(n_plan, k_plan, p, spec_type) - 0.10,
                      aql_key / 100.0, 0.9999)
    except ValueError:
        ltpd = float("nan")

    return SamplingPlanVariables(N=N, n=n_plan, k=k_plan, aql=aql_key, spec_type=spec_type,
                                 alpha=alpha, ltpd=ltpd, method="z1.9")


# ─────────────────────────────────────────────────── Dodge-Romig ──────────────
@dataclass
class DodgeRomigPlan:
    """Plan Dodge-Romig por atributos.

    Atributos
    ---------
    N : int
        Tamaño del lote.
    n : int
        Tamaño de la muestra.
    c : int
        Número de aceptación.
    plan_type : str
        ``'LTPD'`` o ``'AOQL'``.
    target : float
        LTPD o AOQL objetivo (fracción, no %).
    process_avg : float
        Promedio de proceso asumido (fracción defectiva).
    aoql : float
        AOQL real del plan.
    ltpd : float
        LTPD real del plan.
    """

    N: int
    n: int
    c: int
    plan_type: str
    target: float
    process_avg: float
    aoql: float
    ltpd: float
    _p_arr: np.ndarray = field(repr=False)
    _pa_arr: np.ndarray = field(repr=False)

    def pa(self, p: float) -> float:
        return _pa_binomial(self.n, self.c, p)

    def oc_curve(self, stable: bool = False) -> pd.DataFrame:
        """Curva OC del plan (``stable=True``: columnas ``defective_fraction`` y ``p_accept``)."""
        return renombrar(pd.DataFrame({"p_defectivo": self._p_arr, "P(aceptar)": self._pa_arr}), _COLUMNAS_OC, stable)

    def aoq_curve(self, stable: bool = False) -> pd.DataFrame:
        """Curva AOQ del plan (``stable=True``: columnas ``defective_fraction`` y ``aoq``)."""
        aoq = self._pa_arr * self._p_arr * (self.N - self.n) / self.N
        return renombrar(pd.DataFrame({"p_defectivo": self._p_arr, "AOQ": aoq}), _COLUMNAS_AOQ, stable)

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla resumen (una fila por estadístico; con ``stable=True`` claves canónicas en inglés)."""
        objetivo = "LTPD" if self.plan_type == "LTPD" else "AOQL"
        rows = [
            ("lot_size", N_("N (tamaño de lote)"), self.N),
            ("sample_size", N_("n (tamaño de muestra)"), self.n),
            ("acceptance_number", N_("c (número de aceptación)"), self.c),
            ("plan_type", N_("Tipo de plan"), self.plan_type),
            ("target_pct", tr("{kind} objetivo (%)").format(kind=objetivo), round(self.target * 100, 4)),
            ("process_avg_pct", N_("Promedio de proceso (%)"), round(self.process_avg * 100, 4)),
            ("aoql_pct", N_("AOQL (%)"), round(self.aoql * 100, 4)),
            ("ltpd_pct", N_("LTPD (β=0.10) (%)"), round(self.ltpd * 100, 4)),
        ]
        return tabla_estadisticos(rows, stable)

    def summary(self) -> str:
        return "\n".join([
            tr("Plan Dodge-Romig ({plan_type})").format(plan_type=self.plan_type),
            tr("  Lote N={N}  Muestra n={n}  Ac={c}  Re={r}").format(N=self.N, n=self.n, c=self.c, r=self.c + 1),
            tr("  {kind} objetivo={target:.3g}%  Promedio proceso={process_avg:.3g}%").format(
                kind="LTPD" if self.plan_type == "LTPD" else "AOQL", target=self.target * 100,
                process_avg=self.process_avg * 100),
            tr("  AOQL={aoql:.3g}%  LTPD={ltpd:.3g}%").format(aoql=self.aoql * 100, ltpd=self.ltpd * 100),
        ])

    def to_excel(self, path) -> None:
        """Exporta el plan Dodge-Romig a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with _excel_writer(path) as writer:
            self.to_frame().to_excel(writer, sheet_name=tr("Plan"))

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_sampling_attributes
        return plot_sampling_attributes(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt
        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def _dodge_romig_ltpd(N: int, ltpd: float, process_avg: float) -> tuple[int, int]:
    """Encuentra (n, c) mínimo tal que Pa(LTPD) ≤ 0.10 minimizando ATI."""
    best_n, best_c, best_ati = N, 0, float("inf")
    # Buscar en rango razonable de c
    for c in range(20):
        # Encuentra n mínimo tal que Pa(ltpd) ≤ 0.10 con este c
        if _pa_binomial(c + 1, c, ltpd) <= 0.10:
            n = c + 1
        else:
            try:
                # Busca el n mínimo por búsqueda lineal
                for n_try in range(c + 1, min(N + 1, 2000)):
                    if _pa_binomial(n_try, c, ltpd) <= 0.10:
                        n = n_try
                        break
                else:
                    continue
            except (ValueError, OverflowError, ZeroDivisionError):
                continue
        if n > N:
            continue
        # ATI = n + Pa(process_avg) * (N - n)
        pa_avg = _pa_binomial(n, c, process_avg)
        ati = n + pa_avg * (N - n)
        if ati < best_ati:
            best_ati, best_n, best_c = ati, n, c
    return best_n, best_c


def _dodge_romig_aoql(N: int, aoql: float, process_avg: float) -> tuple[int, int]:
    """Encuentra (n, c) tal que el AOQL real ≈ objetivo, minimizando ATI."""
    p_arr = np.linspace(1e-6, 0.5, 500)
    best_n, best_c, best_ati = N, 0, float("inf")
    for c in range(20):
        for n_try in range(c + 1, min(N + 1, 1000)):
            pa_arr = _pa_binomial_arr(n_try, c, p_arr)
            aoq_arr = pa_arr * p_arr * (N - n_try) / N
            computed_aoql = float(aoq_arr.max())
            if computed_aoql <= aoql * 1.05:  # within 5% tolerance
                pa_avg = _pa_binomial(n_try, c, process_avg)
                ati = n_try + pa_avg * (N - n_try)
                if ati < best_ati:
                    best_ati, best_n, best_c = ati, n_try, c
                break
    return best_n, best_c


def dodge_romig(
    N: int,
    *,
    ltpd: float | None = None,
    aoql: float | None = None,
    process_avg: float = 0.01,
) -> DodgeRomigPlan:
    """Plan de muestreo Dodge-Romig por atributos.

    Proporciona protección al consumidor (LTPD) o calidad media de salida
    máxima (AOQL), minimizando el número promedio de inspección total (ATI).

    Parameters
    ----------
    N : int
        Tamaño del lote.
    ltpd : float, opcional
        LTPD objetivo en fracción (p.ej. 0.03 para 3%). Exactamente uno de
        ``ltpd`` o ``aoql`` debe especificarse.
    aoql : float, opcional
        AOQL objetivo en fracción.
    process_avg : float
        Promedio de proceso (fracción defectiva) estimado. Por defecto 0.01.

    Returns
    -------
    DodgeRomigPlan
    """
    if (ltpd is None) == (aoql is None):
        raise ValueError(tr("Especifica exactamente uno de 'ltpd' o 'aoql'."))
    if N < 2:
        raise ValueError(tr("N debe ser ≥ 2."))
    if not 0 < process_avg < 1:
        raise ValueError(tr("'process_avg' debe estar en (0, 1)."))

    if ltpd is not None:
        if not 0 < ltpd < 1:
            raise ValueError(tr("'ltpd' debe estar en (0, 1)."))
        n, c = _dodge_romig_ltpd(N, ltpd, process_avg)
        plan_type = "LTPD"
        target = ltpd
    else:
        assert aoql is not None
        if not 0 < aoql < 1:
            raise ValueError(tr("'aoql' debe estar en (0, 1)."))
        n, c = _dodge_romig_aoql(N, aoql, process_avg)
        plan_type = "AOQL"
        target = aoql

    p_arr = np.linspace(0, min(0.5, target * 5), 400)
    pa_arr = _pa_binomial_arr(n, c, p_arr)
    aoq_arr = pa_arr * p_arr * (N - n) / N
    computed_aoql = float(aoq_arr.max())
    try:
        computed_ltpd = brentq(lambda p: _pa_binomial(n, c, p) - 0.10, 1e-9, 1.0 - 1e-9)
    except ValueError:
        computed_ltpd = float("nan")

    return DodgeRomigPlan(
        N=N, n=n, c=c, plan_type=plan_type, target=target,
        process_avg=process_avg, aoql=computed_aoql, ltpd=computed_ltpd,
        _p_arr=p_arr, _pa_arr=pa_arr,
    )
