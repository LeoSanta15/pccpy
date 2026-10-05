"""Validación de la instalación: comprueba pccpy contra referencias independientes y genera un informe.

Cada comprobación calcula un resultado con pccpy y lo compara con una **referencia independiente**: una tabla publicada,
una fórmula escrita aparte con NumPy/SciPy, una definición matemática o una simulación con semilla fija. Sirve para
documentar que la versión instalada, en *este* entorno, da los resultados esperados (por ejemplo, para un expediente de
calidad), y se ejecuta sin pytest::

    python -m pccpy.validation                       # resumen y código de salida 0/1
    python -m pccpy.validation --markdown informe.md # informe completo con el entorno

**No es una validación contra Minitab**: Minitab es propietario y aquí no se compara con él. Valida las fórmulas y las
convenciones documentadas por Minitab y la bibliografía contra referencias abiertas.
"""
from __future__ import annotations

import argparse
import math
import platform
import sys
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import scipy
from scipy import stats

from ._constants import control_chart_constants
from ._frames import etiquetas
from ._i18n import N_, tr

_COLUMNAS = {
    "id": N_("id"), "description": N_("descripción"), "source": N_("referencia"), "expected": N_("esperado"),
    "obtained": N_("obtenido"), "error": N_("error"), "tolerance": N_("tolerancia"), "passed": N_("correcta"),
}


@dataclass(frozen=True)
class Check:
    """Una comprobación: lo que debería salir (``expected``), lo que salió (``obtained``) y si coinciden."""

    id: str
    description: str
    source: str
    expected: np.ndarray
    obtained: np.ndarray
    tolerance: float
    error: float
    passed: bool
    detail: str = ""  # texto del error si la comprobación no pudo ejecutarse


@dataclass(frozen=True)
class _Definicion:
    id: str
    description: str  # texto en español marcado con N_()
    source: str
    funcion: Callable[[], tuple]
    tolerance: float
    relative: bool = False
    params: tuple = ()


_REGISTRO: list[_Definicion] = []


def _comprobacion(id: str, description: str, source: str, tolerance: float = 1e-9, relative: bool = False,
                  params: tuple = ()):
    """Registra una comprobación; la función devuelve ``(esperado, obtenido)`` (escalares o arreglos)."""

    def registrar(funcion):
        _REGISTRO.append(_Definicion(id, description, source, funcion, tolerance, relative, params))
        return funcion

    return registrar


# ── 1. constantes de las cartas ──────────────────────────────────────────────
_TABLA = {  # n: (d2, d3, c4, A2, A3, D3, D4, B3, B4); Montgomery, Introduction to SQC, apéndice VI
    2: (1.128, 0.853, 0.7979, 1.880, 2.659, 0.0, 3.267, 0.0, 3.267),
    5: (2.326, 0.864, 0.9400, 0.577, 1.427, 0.0, 2.114, 0.0, 2.089),
    10: (3.078, 0.797, 0.9727, 0.308, 0.975, 0.223, 1.777, 0.284, 1.716),
}
_CLAVES = ("d2", "d3", "c4", "A2", "A3", "D3", "D4", "B3", "B4")


def _constantes(n: int):
    c = control_chart_constants(n)
    return np.array(_TABLA[n]), np.array([c[k] for k in _CLAVES])


for _n in _TABLA:
    _comprobacion(f"constantes-n{_n}", N_("Constantes d2, d3, c4, A2, A3, D3, D4, B3 y B4 para n = {n}"),
                  "Montgomery, Introduction to Statistical Quality Control, tabla de factores", 6e-4, params=(_n,))(
        lambda n=_n: _constantes(n))


# ── 2. límites de control por fórmula manual ─────────────────────────────────
_X = np.array([10.2, 9.8, 10.5, 10.1, 9.7, 10.3, 10.0, 10.6, 9.9, 10.2, 10.4, 9.6, 10.1, 10.3, 9.8])
_G = np.array([[10.2, 9.8, 10.5, 10.1], [9.7, 10.3, 10.0, 10.6], [9.9, 10.2, 10.4, 9.6], [10.1, 10.3, 9.8, 10.0],
               [10.5, 10.2, 9.9, 10.4]])


def _d2_d3(n: int) -> tuple:
    """d2 = E[R] y d3 = sd[R] del rango de n normales estándar, por integración numérica."""
    from scipy import integrate, stats

    f, F = stats.norm.pdf, stats.norm.cdf
    d2 = integrate.quad(lambda x: 1 - F(x) ** n - (1 - F(x)) ** n, -10, 10, epsabs=1e-13, epsrel=1e-13)[0]
    er2 = integrate.dblquad(lambda y, x: n * (n - 1) * f(x) * f(y) * (F(y) - F(x)) ** (n - 2) * (y - x) ** 2,
                            -9, 9, lambda x: x, lambda x: 9, epsabs=1e-12, epsrel=1e-12)[0]
    return d2, math.sqrt(er2 - d2 * d2)


@_comprobacion("limites-imr", N_("Límites de la carta I-MR (X̄ ± 3·MR̄/d2; D4·MR̄)"), "Montgomery (2019), cap. 6", 1e-9)
def _imr():
    from .charts import imr_chart

    mr = np.abs(np.diff(_X))
    d2, d3 = _d2_d3(2)
    esperado = [_X.mean() + 3 * mr.mean() / d2, _X.mean() - 3 * mr.mean() / d2, (1 + 3 * d3 / d2) * mr.mean()]
    c = imr_chart(_X)
    return np.array(esperado), np.array([c["I"].ucl[0], c["I"].lcl[0], c["MR"].ucl[0]])


@_comprobacion("limites-xbar-r", N_("Límites de la carta Xbar-R (X̿ ± A2·R̄; D4·R̄)"), "Montgomery (2019), cap. 6", 1e-9)
def _xbar_r():
    from .charts import xbar_r_chart

    rbar = (np.ptp(_G, axis=1)).mean()
    gm = _G.mean()
    d2, d3 = _d2_d3(4)
    a2, d4 = 3 / (d2 * math.sqrt(4)), 1 + 3 * d3 / d2  # A2 = 3/(d2·√n); D4 = 1 + 3·d3/d2
    c = xbar_r_chart(_G)
    return np.array([gm + a2 * rbar, gm - a2 * rbar, d4 * rbar]), np.array(
        [c["Xbar"].ucl[0], c["Xbar"].lcl[0], c["R"].ucl[0]])


@_comprobacion("limites-xbar-s", N_("Límites de la carta Xbar-S (X̿ ± A3·S̄; B4·S̄)"), "Montgomery (2019), cap. 6", 1e-9)
def _xbar_s():
    from .charts import xbar_s_chart

    sbar = _G.std(axis=1, ddof=1).mean()
    gm = _G.mean()
    c4 = 0.9213177319
    a3, b4 = 3 / (c4 * 2.0), 1 + 3 * math.sqrt(1 - c4**2) / c4
    c = xbar_s_chart(_G)
    return np.array([gm + a3 * sbar, gm - a3 * sbar, b4 * sbar]), np.array(
        [c["Xbar"].ucl[0], c["Xbar"].lcl[0], c["S"].ucl[0]])


_D = np.array([3, 5, 2, 4, 6, 1, 3, 5, 2, 4])
_N = np.array([200, 180, 220, 200, 210, 190, 200, 205, 195, 200])


@_comprobacion("limites-p", N_("Límites de la carta P con n variable (p̄ ± 3·√(p̄(1−p̄)/n))"), "Montgomery (2019), cap. 7", 1e-12)
def _p():
    from .charts import p_chart

    pbar = _D.sum() / _N.sum()
    h = 3 * np.sqrt(pbar * (1 - pbar) / _N)
    c = p_chart(_D, _N)
    return np.concatenate([pbar + h, np.maximum(pbar - h, 0)]), np.concatenate([c["P"].ucl, c["P"].lcl])


@_comprobacion("limites-np-c-u", N_("Límites de las cartas NP, C y U"), "Montgomery (2019), cap. 7", 1e-12)
def _np_c_u():
    from .charts import c_chart, np_chart, u_chart

    pbar = _D.sum() / (200 * len(_D))
    np_ucl = 200 * pbar + 3 * math.sqrt(200 * pbar * (1 - pbar))
    cbar = _D.mean()
    nu = np.full(len(_D), 2.0)
    ubar = _D.sum() / nu.sum()
    return (np.array([np_ucl, cbar + 3 * math.sqrt(cbar), ubar + 3 * math.sqrt(ubar / 2)]),
            np.array([np_chart(_D, 200)["NP"].ucl[0], c_chart(_D)["C"].ucl[0], u_chart(_D, nu)["U"].ucl[0]]))


# ── 3. pruebas de causas especiales (patrones construidos a mano) ────────────
_PATRONES = [  # (prueba, datos con mu=0 y sigma=1, índices (base 0) que deben marcarse)
    (1, [0] * 10 + [3.5] + [0] * 9, [10]),
    (2, [1] * 9 + [-1], [8]),
    (3, [0, 0.2, 0.4, 0.6, 0.8, 1.0], [5]),
    (4, [1, -1] * 7, [13]),
    (5, [2.5, 0, 2.5], [2]),
    (6, [1.5, 1.5, 0, 1.5, 1.5], [4]),
    (7, [0.5] * 15, [14]),
    (8, [1.5, -1.5] * 4, [7]),
]


def _marcados(prueba: int, datos: list) -> list:
    from .charts import imr_chart

    c = imr_chart(np.array(datos, dtype=float), mu=0.0, sigma=1.0, tests=(prueba,))
    return c["I"].violations.get(prueba, np.array([], dtype=int)).tolist()


for _t, _d, _e in _PATRONES:
    _comprobacion(f"prueba-{_t}", N_("Prueba de causas especiales {t}: marca el punto que completa el patrón"),
                  "Western Electric / Nelson; documentación de Minitab", 0.0, params=(_t,))(
        (lambda t=_t, d=_d, e=_e: (np.array(e, dtype=float), np.array(_marcados(t, d), dtype=float))))


@_comprobacion("prueba-1-simulacion", N_("Tasa de falsas alarmas de la prueba 1 en 400 000 puntos normales (≈ 0,0027)"),
               "Φ(−3)·2 = 0,0026998; simulación con semilla fija", 4e-4)
def _falsas_alarmas():
    from .charts import imr_chart

    x = np.random.default_rng(20260105).normal(size=400_000)
    c = imr_chart(x, mu=0.0, sigma=1.0, tests=(1,))
    return 2 * stats.norm.cdf(-3), c["I"].flagged.size / x.size


# ── 4. capacidad ─────────────────────────────────────────────────────────────
@_comprobacion("capacidad-indices", N_("Cp, Cpk, Pp y Ppk desde estadísticos (media 50, σ dentro 1,5, σ global 2, LEI 44, LES 58)"),
               "Definiciones: Cp = (LES−LEI)/6σ; Cpk = mín(LES−μ, μ−LEI)/3σ", 1e-12)
def _cap_indices():
    from .capability import capability_analysis_summary

    r = capability_analysis_summary(50.0, 2.0, 100, lsl=44, usl=58, std_within=1.5)
    return np.array([14 / 9, 6 / 4.5, 14 / 12, 6 / 6]), np.array([r.cp, r.cpk, r.pp, r.ppk])


@_comprobacion("capacidad-zbench", N_("Z.Bench y PPM esperado globales desde la distribución normal"),
               "Z.Bench = Φ⁻¹(1 − P(fuera de especificaciones)); SciPy", 1e-6)
def _cap_z():
    from .capability import capability_analysis_summary

    p = stats.norm.cdf(-(58 - 50) / 2) + stats.norm.cdf(-(50 - 44) / 2)
    r = capability_analysis_summary(50.0, 2.0, 100, lsl=44, usl=58, std_within=1.5)
    return np.array([stats.norm.isf(p), p * 1e6]), np.array([r.z_bench_overall, r.ppm_overall[2]])


# ── 5. normalidad e intervalos de tolerancia ─────────────────────────────────
@_comprobacion("anderson-darling", N_("Estadístico A² de Anderson-Darling de la prueba de normalidad"),
               "scipy.stats.anderson", 1e-10)
def _ad():
    from .normality import normality_test

    x = np.array([10.1, 10.0, 10.2, 9.9, 10.05, 10.12, 9.95, 10.08, 10.01, 9.97, 10.3, 9.8])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ref = stats.anderson(x).statistic
    return ref, normality_test(x).statistic


@_comprobacion("tolerancia-unilateral", N_("Factor k del intervalo de tolerancia unilateral (n = 10, 95/95)"),
               "t no central exacta: k = t'(γ; n−1, z_p·√n)/√n; tabla publicada: 2,911", 1e-9)
def _k_uni():
    from .tolerance import tolerance_interval_summary

    n, p, g = 10, 0.95, 0.95
    ref = stats.nct.ppf(g, n - 1, stats.norm.ppf(p) * math.sqrt(n)) / math.sqrt(n)
    return ref, tolerance_interval_summary(0.0, 1.0, n, coverage=p, confidence=g, sides="upper").k_factor


@_comprobacion("tolerancia-bilateral", N_("Factor k del intervalo de tolerancia bilateral (n = 10, 95/95)"),
               "Tabla de factores K para límites de tolerancia normales (3,379); aproximación de Howe", 5e-3)
def _k_bi():
    from .tolerance import tolerance_interval_summary

    return 3.379, tolerance_interval_summary(0.0, 1.0, 10, coverage=0.95, confidence=0.95).k_factor


# ── 6. muestreo de aceptación ────────────────────────────────────────────────
@_comprobacion("z14-plan", N_("Plan Z1.4 para lote 1000, AQL 1,0 %, nivel II: n = 80 (código J), Ac = 2"),
               "ANSI/ASQ Z1.4, tabla II-A", 0.0)
def _z14():
    from .acceptance import acceptance_sampling_attributes

    plan = acceptance_sampling_attributes(N=1000, aql=1.0)
    return np.array([80.0, 2.0]), np.array([plan.n, plan.c], dtype=float)


@_comprobacion("z14-tabla", N_("Celdas conocidas de la tabla Z1.4 (n y Ac en varias letras y AQL)"),
               "ANSI/ASQ Z1.4, tabla II-A", 0.0)
def _z14_tabla():
    from .acceptance import acceptance_sampling_attributes

    celdas = [  # (N del lote, AQL %, n, Ac)
        (400, 1.0, 50, 1), (200, 1.5, 32, 1), (1000, 0.65, 80, 1), (1000, 1.5, 80, 3), (1000, 2.5, 80, 5),
        (1000, 4.0, 80, 7), (1000, 6.5, 80, 10), (2000, 0.65, 125, 2), (2000, 1.0, 125, 3), (5000, 1.0, 200, 5),
        (5000, 0.25, 200, 1), (20000, 1.0, 315, 7), (100000, 1.0, 500, 10), (200000, 1.0, 800, 14),
        (600000, 1.0, 1250, 21),
    ]
    esperado = np.array([(n, ac) for _, _, n, ac in celdas], dtype=float)
    obtenido = np.array([(p.n, p.c) for p in (acceptance_sampling_attributes(N=N, aql=a) for N, a, _, _ in celdas)],
                        dtype=float)
    return esperado, obtenido


@_comprobacion("curva-oc", N_("Probabilidad de aceptación del plan (n = 80, c = 2) para p = 0,5 %, 1 % y 3 %"),
               "Distribución binomial acumulada; SciPy", 1e-12)
def _oc():
    from .acceptance import acceptance_sampling_attributes

    plan = acceptance_sampling_attributes(N=1000, aql=1.0)
    p = np.array([0.005, 0.01, 0.03])
    return stats.binom.cdf(2, 80, p), np.array([plan.pa(v) for v in p])


@_comprobacion("capacidad-binomial", N_("Capacidad binomial: p̄, intervalo exacto de Clopper-Pearson y Z del proceso"),
               "scipy.stats.binomtest (intervalo exacto); Z = Φ⁻¹(1 − p̄)", 1e-9)
def _cap_binomial():
    from .capability_attr import capability_binomial

    d, n = 29, 1600
    ic = stats.binomtest(d, n).proportion_ci(confidence_level=0.95, method="exact")
    esperado = [d / n, ic.low, ic.high, stats.norm.isf(d / n)]
    r = capability_binomial([3, 5, 2, 4, 6, 1, 3, 5], [200] * 8)
    return np.array(esperado), np.array([r.p_bar, r.p_ci[0], r.p_ci[1], r.z])


@_comprobacion("capacidad-poisson", N_("Capacidad Poisson: DPU e intervalo exacto de Garwood (cuantiles de la gamma)"),
               "Garwood (1936): cuantiles de la distribución gamma", 1e-9)
def _cap_poisson():
    from .capability_attr import capability_poisson

    d, u = 29, 84.0
    esperado = [d / u, stats.gamma.ppf(0.025, d) / u, stats.gamma.ppf(0.975, d + 1) / u]
    r = capability_poisson([3, 5, 2, 4, 6, 1, 3, 5], [10, 12, 10, 9, 11, 10, 10, 12])
    return np.array(esperado), np.array([r.dpu, r.dpu_ci[0], r.dpu_ci[1]])


# ── 7. sistemas de medición ──────────────────────────────────────────────────
@_comprobacion("gage-rr-anova", N_("Componentes de varianza del Gage R&R cruzado (ANOVA de dos factores con interacción)"),
               "Cuadrados medios esperados del ANOVA cruzado; AIAG MSA 4ª ed.", 1e-9)
def _grr():
    from .msa import gage_rr

    rng = np.random.default_rng(7)
    a, b, r = 8, 3, 3
    parte = rng.normal(0, 2, a)[:, None, None]
    oper = rng.normal(0, 0.5, b)[None, :, None]
    inter = rng.normal(0, 0.6, (a, b))[:, :, None]
    y = 10 + parte + oper + inter + rng.normal(0, 0.3, (a, b, r))
    media = y.mean()
    mp, mo = y.mean(axis=(1, 2)), y.mean(axis=(0, 2))
    mpo = y.mean(axis=2)
    ss_p = b * r * ((mp - media) ** 2).sum()
    ss_o = a * r * ((mo - media) ** 2).sum()
    ss_po = r * ((mpo - mp[:, None] - mo[None, :] + media) ** 2).sum()
    ss_e = ((y - mpo[:, :, None]) ** 2).sum()
    ms_p, ms_o = ss_p / (a - 1), ss_o / (b - 1)
    ms_po, ms_e = ss_po / ((a - 1) * (b - 1)), ss_e / (a * b * (r - 1))
    esperado = np.array([ms_e, max((ms_o - ms_po) / (a * r), 0.0), max((ms_po - ms_e) / r, 0.0),
                         max((ms_p - ms_po) / (b * r), 0.0)])
    res = gage_rr(y.ravel(), parts=a, operators=b, replicates=r)
    return esperado, np.array([res.var_repeatability, res.var_operator, res.var_interaction, res.var_part])


@_comprobacion("gage-tipo1", N_("Estudio Tipo 1: sesgo, Cg y Cgk (K = 20 %, 6σ)"),
               "Minitab: Cg = 0,2·T/(6s); Cgk = (0,1·T − |sesgo|)/(3s)", 1e-12)
def _tipo1():
    from .msa import gage_type1

    x = np.array([10.1, 10.0, 10.2, 9.9, 10.05, 10.12, 9.95, 10.08, 10.01, 9.97])
    tol, s = 0.5, x.std(ddof=1)
    esperado = [x.mean() - 10.0, 0.2 * tol / (6 * s), (0.1 * tol - abs(x.mean() - 10.0)) / (3 * s)]
    r = gage_type1(x, reference=10.0, tolerance=tol)
    return np.array(esperado), np.array([r.bias, r.cg, r.cgk])


@_comprobacion("linealidad", N_("Linealidad y sesgo: pendiente, ordenada y R² de datos sin ruido (sesgo = 0,1 + 0,02·ref)"),
               "Regresión lineal exacta", 1e-9)
def _lin():
    from .msa import gage_linearity

    ref = np.repeat(np.array([2.0, 4.0, 6.0, 8.0, 10.0]), 4)
    medicion = ref + 0.1 + 0.02 * ref
    r = gage_linearity(medicion, ref)
    return np.array([0.02, 0.1, 1.0]), np.array([r.slope, r.intercept, r.r_squared])


@_comprobacion("kappa", N_("Kappa de Cohen de un operador frente a la referencia (50 piezas; po = 0,7, pe = 0,5 → κ = 0,4)"),
               "κ = (po − pe)/(1 − pe)", 1e-12)
def _kappa():
    from .msa import attribute_agreement

    ref = np.array(["B"] * 25 + ["M"] * 25)
    op = np.array(["B"] * 20 + ["M"] * 5 + ["B"] * 10 + ["M"] * 15)    # a=20, b=5, c=10, d=15
    r = attribute_agreement(pd.DataFrame({"A": op}), reference=ref, replicates=1)
    return 0.4, float(r.kappa_vs_reference.loc["A", "kappa"])


# ── 8. multivariadas ─────────────────────────────────────────────────────────
@_comprobacion("t2-mahalanobis", N_("T² de Hotelling de observaciones individuales con parámetros históricos"),
               "T² = (x − μ)ᵀ Σ⁻¹ (x − μ) = distancia de Mahalanobis²; scipy.spatial.distance", 1e-9)
def _t2():
    from scipy.spatial.distance import mahalanobis

    from .multivariate import t2_chart

    rng = np.random.default_rng(3)
    cov = np.array([[2.0, 0.6, 0.2], [0.6, 1.0, 0.1], [0.2, 0.1, 1.5]])
    mu = np.array([1.0, 2.0, 3.0])
    x = rng.multivariate_normal(mu, cov, 25)
    inv = np.linalg.inv(cov)
    c = t2_chart(x, mu=mu, cov=cov)
    return np.array([mahalanobis(v, mu, inv) ** 2 for v in x]), c["T2"].values


@_comprobacion("mewma-limite", N_("Límite H de la MEWMA para p = 2, λ = 0,1 y ARL en control = 200"),
               "Prabhu y Runger (1997): H = 8,64", 2e-2)
def _mewma():
    from .multivariate import mewma_limit

    return 8.64, mewma_limit(2, 0.1, 200.0)


# ── informe ──────────────────────────────────────────────────────────────────
@dataclass
class ValidationReport:
    """Resultado de ``run_validation``: las comprobaciones y el entorno en que se ejecutaron."""

    checks: list[Check]
    environment: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """``True`` si todas las comprobaciones son correctas."""
        return all(c.passed for c in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.passed]

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Una fila por comprobación (con ``stable=True``, columnas con claves en inglés)."""
        col = etiquetas(_COLUMNAS, stable)
        return pd.DataFrame({
            col["id"]: [c.id for c in self.checks], col["description"]: [c.description for c in self.checks],
            col["source"]: [c.source for c in self.checks], col["error"]: [c.error for c in self.checks],
            col["tolerance"]: [c.tolerance for c in self.checks], col["passed"]: [c.passed for c in self.checks],
        })

    def summary(self) -> str:
        """Resumen en texto: comprobaciones correctas y, si las hay, las fallidas."""
        lines = [tr("Validación de pccpy {version}: {ok} de {total} comprobaciones correctas").format(
            version=self.environment.get("pccpy", ""), ok=sum(c.passed for c in self.checks), total=len(self.checks))]
        for c in self.failures:
            lines.append(tr("  FALLA {id}: {description} (error {error:.3g} > tolerancia {tolerance:.3g}) {detail}").format(
                id=c.id, description=c.description, error=c.error, tolerance=c.tolerance, detail=c.detail).rstrip())
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Informe completo en Markdown: entorno, resultado de cada comprobación y referencias."""
        ent = self.environment
        ok = sum(c.passed for c in self.checks)
        marca = "✔" if self.passed else "✘"
        out = [
            "# " + tr("Informe de validación de pccpy"), "",
            "- " + tr("Fecha (UTC)") + ": " + str(ent.get("fecha", "")), "- pccpy: " + str(ent.get("pccpy", "")),
            "- Python: " + str(ent.get("python", "")) + " (" + str(ent.get("plataforma", "")) + ")",
            "- NumPy " + str(ent.get("numpy", "")) + ", SciPy " + str(ent.get("scipy", "")) + ", pandas "
            + str(ent.get("pandas", "")), "",
            "**" + tr("Resultado") + ": " + marca + " " + str(ok) + "/" + str(len(self.checks)) + "**", "",
            "| id | " + tr("Descripción") + " | " + tr("Referencia") + " | " + tr("Error") + " | " + tr("Tolerancia")
            + " | |", "|---|---|---|---|---|---|",
        ]
        for c in self.checks:
            out.append(f"| {c.id} | {c.description} | {c.source} | {c.error:.3g} | {c.tolerance:.3g} | "
                       f"{'✔' if c.passed else '✘ ' + c.detail} |")
        out += ["", tr("Las referencias son tablas publicadas, fórmulas escritas aparte con NumPy/SciPy o simulaciones con "
                       "semilla fija. No es una comparación con Minitab.")]
        return "\n".join(out) + "\n"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()


def _entorno() -> dict:
    from . import __version__

    return {"fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "pccpy": __version__,
            "python": platform.python_version(), "plataforma": platform.platform(), "numpy": np.__version__,
            "scipy": scipy.__version__, "pandas": pd.__version__}


def run_validation(ids=None) -> ValidationReport:
    """Ejecuta las comprobaciones de validación y devuelve el informe.

    Parameters
    ----------
    ids : iterable of str, optional
        Solo las comprobaciones con estos identificadores (por defecto, todas; ver ``ValidationReport.to_frame()``).

    Returns
    -------
    ValidationReport
        ``report.passed`` es ``True`` si todo coincide con las referencias.
    """
    elegidas = [d for d in _REGISTRO if ids is None or d.id in set(ids)]
    checks = []
    for d in elegidas:
        detalle = ""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                esperado, obtenido = d.funcion()
            e, o = np.atleast_1d(np.asarray(esperado, dtype=float)), np.atleast_1d(np.asarray(obtenido, dtype=float))
            if e.shape != o.shape:
                raise ValueError(tr("formas distintas {e} y {o}").format(e=e.shape, o=o.shape))
            diff = np.abs(e - o)
            if d.relative:
                diff = diff / np.maximum(np.abs(e), 1e-300)
            error = float(np.max(diff)) if diff.size else 0.0
            ok = bool(error <= d.tolerance) and bool(np.all(np.isfinite(o)))
        except Exception as exc:  # noqa: BLE001 - una comprobación rota se informa, no detiene el resto
            e = o = np.array([np.nan])
            error, ok, detalle = float("inf"), False, f"{type(exc).__name__}: {exc}"
        nombre = tr(d.description)
        if d.params:
            nombre = nombre.format(n=d.params[0], t=d.params[0])
        checks.append(Check(d.id, nombre, d.source, e, o, d.tolerance, error, ok, detalle))
    return ValidationReport(checks, _entorno())


def main(argv=None) -> int:
    """Línea de órdenes: ``python -m pccpy.validation [--markdown ARCHIVO]``; devuelve 0 si todo es correcto."""
    ap = argparse.ArgumentParser(prog="python -m pccpy.validation", description=__doc__.split("\n\n")[0])
    ap.add_argument("--markdown", metavar="ARCHIVO", help="escribe el informe completo en Markdown")
    args = ap.parse_args(argv)
    informe = run_validation()
    print(informe.summary())
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(informe.to_markdown())
        print(tr("Informe escrito en {path}").format(path=args.markdown))
    return 0 if informe.passed else 1


if __name__ == "__main__":
    sys.exit(main())
