"""MSA / Gage R&R: estudios de sistemas de medición.

Implementa los estudios de medición más usados en Minitab:
* Crossed Gage R&R (ANOVA y Xbar-R)
* Nested Gage R&R (solo ANOVA)
* Type 1 Study (sesgo y repetibilidad)
* Linearity and Bias Study
* Attribute Agreement Analysis (Kappa)

Referencias
-----------
* AIAG MSA Reference Manual, 4th ed. (2010).
* Montgomery, D.C. (2013). *Introduction to Statistical Quality Control*, 7th ed.
* Minitab (2023). Gage R&R Study — Stat > Quality Tools > Gage Study.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from ._data import as_1d

NAN = float("nan")


# ─────────────────────────────────────────────────────────── helpers ──────────
def _to_matrix(data, parts, operators, replicates) -> np.ndarray:
    """Convierte datos a matriz [parts × operators × replicates].

    Acepta:
    - ndarray 1-D de longitud p*o*r (ordenado: p varía más lento, r más rápido)
    - ndarray 3-D ya en formato [p, o, r]
    """
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 1:
        if len(arr) != parts * operators * replicates:
            raise ValueError(
                f"Longitud de datos ({len(arr)}) ≠ parts*operators*replicates "
                f"({parts}×{operators}×{replicates}={parts*operators*replicates})."
            )
        arr = arr.reshape(parts, operators, replicates)
    elif arr.ndim == 3:
        if arr.shape != (parts, operators, replicates):
            raise ValueError(
                f"Forma del array {arr.shape} ≠ ({parts}, {operators}, {replicates})."
            )
    else:
        raise ValueError("Los datos deben ser 1-D o 3-D.")
    return arr


# ──────────────────────────────────────────── Crossed Gage R&R ANOVA ──────────
@dataclass
class GageRRResult:
    """Resultado de :func:`gage_rr`.

    Atributos
    ---------
    method : str
        ``'anova'`` o ``'xbar_r'``.
    study_variation : float
        Multiplicador para la variación de estudio (por defecto 6).
    var_repeatability : float
        Varianza de repetibilidad (EV²).
    var_reproducibility : float
        Varianza total de reproducibilidad (AV² + IA²).
    var_operator : float
        Varianza de operador (AV²).
    var_interaction : float
        Varianza de interacción parte×operador (IA²). 0 para Xbar-R.
    var_part : float
        Varianza parte a parte (PV²).
    var_gage : float
        Varianza del sistema de medición (EV² + AV² + IA²).
    var_total : float
        Varianza total.
    pct_gage : float
        %Contribución del Gage R&R (= var_gage / var_total × 100).
    pct_repeatability : float
        %Contribución de repetibilidad.
    pct_reproducibility : float
        %Contribución de reproducibilidad.
    pct_part : float
        %Contribución parte a parte.
    study_var_gage : float
        Variación de estudio del Gage (= K × σ_gage).
    study_var_total : float
        Variación de estudio total (= K × σ_total).
    pct_study_var : float
        % Variación de estudio del Gage vs total.
    ndc : int
        Número de categorías distintas.
    anova_table : pd.DataFrame o None
        Tabla ANOVA (solo método 'anova').
    """

    method: str
    study_variation: float
    parts: int
    operators: int
    replicates: int
    var_repeatability: float
    var_reproducibility: float
    var_operator: float
    var_interaction: float
    var_part: float
    var_gage: float
    var_total: float
    pct_gage: float
    pct_repeatability: float
    pct_reproducibility: float
    pct_part: float
    study_var_gage: float
    study_var_total: float
    pct_study_var: float
    ndc: int
    anova_table: pd.DataFrame | None = None
    _data: np.ndarray = field(repr=False, default=None)  # type: ignore[assignment, arg-type]

    def to_frame(self) -> pd.DataFrame:
        K = self.study_variation
        sv = K
        rows = [
            ("Método", self.method),
            ("Partes (p)", self.parts),
            ("Operadores (o)", self.operators),
            ("Réplicas (r)", self.replicates),
            ("Mult. estudio (K)", sv),
            ("", ""),
            ("Varianza repetibilidad (EV²)", round(self.var_repeatability, 6)),
            ("Varianza operador (AV²)", round(self.var_operator, 6)),
            ("Varianza interacción (IA²)", round(self.var_interaction, 6)),
            ("Varianza reproducibilidad", round(self.var_reproducibility, 6)),
            ("Varianza Gage R&R", round(self.var_gage, 6)),
            ("Varianza parte a parte (PV²)", round(self.var_part, 6)),
            ("Varianza total", round(self.var_total, 6)),
            ("", ""),
            ("%Contribución Gage R&R", round(self.pct_gage, 2)),
            ("%Contribución repetibilidad", round(self.pct_repeatability, 2)),
            ("%Contribución reproducibilidad", round(self.pct_reproducibility, 2)),
            ("%Contribución parte a parte", round(self.pct_part, 2)),
            ("", ""),
            ("Var. estudio Gage R&R", round(self.study_var_gage, 6)),
            ("Var. estudio total", round(self.study_var_total, 6)),
            ("%Var. estudio Gage R&R", round(self.pct_study_var, 2)),
            ("NDC (núm. categorías distintas)", self.ndc),
        ]
        return pd.DataFrame(rows, columns=["estadístico", "valor"]).set_index("estadístico")

    def summary(self) -> str:
        lines = [
            (
                f"Gage R&R ({self.method}) — {self.parts} partes × "
                f"{self.operators} operadores × {self.replicates} réplicas"
            ),
            f"  K = {self.study_variation}  (variación de estudio = K·σ)",
            "",
            "  Fuente              Var          %Contribución",
            f"  Repetibilidad       {self.var_repeatability:10.5f}   {self.pct_repeatability:6.2f}%",
            f"  Reproducibilidad    {self.var_reproducibility:10.5f}   {self.pct_reproducibility:6.2f}%",
            f"    Operador          {self.var_operator:10.5f}",
            f"    Interacción       {self.var_interaction:10.5f}",
            f"  Gage R&R            {self.var_gage:10.5f}   {self.pct_gage:6.2f}%",
            f"  Parte a parte       {self.var_part:10.5f}   {self.pct_part:6.2f}%",
            f"  Total               {self.var_total:10.5f}  100.00%",
            "",
            f"  %Var. estudio Gage R&R = {self.pct_study_var:.2f}%   NDC = {self.ndc}",
        ]
        return "\n".join(lines)

    def to_excel(self, path) -> None:
        """Exporta el Gage R&R a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        Hojas: Resumen, ANOVA (si está disponible).
        """
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            self.to_frame().to_excel(writer, sheet_name="Resumen")
            if self.anova_table is not None:
                self.anova_table.to_excel(writer, sheet_name="ANOVA")

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_gage_rr
        return plot_gage_rr(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt
        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def _gage_rr_anova(data: np.ndarray, study_variation: float,
                   tolerance: float | None, crossed: bool) -> GageRRResult:
    """ANOVA Gage R&R (crossed o nested)."""
    p, o, r = data.shape
    grand_mean = data.mean()

    # Sums of squares
    # SS_parts
    part_means = data.mean(axis=(1, 2))  # shape (p,)
    SS_parts = o * r * np.sum((part_means - grand_mean) ** 2)
    df_parts = p - 1

    # SS_operators
    op_means = data.mean(axis=(0, 2))  # shape (o,)
    SS_ops = p * r * np.sum((op_means - grand_mean) ** 2)
    df_ops = o - 1

    MS_parts = SS_parts / df_parts if df_parts > 0 else NAN
    MS_ops = SS_ops / df_ops if df_ops > 0 else NAN

    if crossed:
        # SS_interaction
        cell_means = data.mean(axis=2)  # shape (p, o)
        SS_int = r * np.sum((cell_means - part_means[:, None] - op_means[None, :] + grand_mean) ** 2)
        df_int = (p - 1) * (o - 1)
        # SS_error (within cells)
        SS_err = np.sum((data - cell_means[:, :, None]) ** 2)
        df_err = p * o * (r - 1)
        MS_int = SS_int / df_int if df_int > 0 else NAN
        MS_err = SS_err / df_err if df_err > 0 else NAN

        # F statistics and p-values
        F_parts = MS_parts / MS_int if (MS_int and MS_int > 0) else NAN
        F_ops = MS_ops / MS_int if (MS_int and MS_int > 0) else NAN
        F_int = MS_int / MS_err if (MS_err and MS_err > 0) else NAN

        pv_parts = 1 - stats.f.cdf(F_parts, df_parts, df_int) if not math.isnan(F_parts) else NAN
        pv_ops = 1 - stats.f.cdf(F_ops, df_ops, df_int) if not math.isnan(F_ops) else NAN
        pv_int = 1 - stats.f.cdf(F_int, df_int, df_err) if not math.isnan(F_int) else NAN

        anova_df = pd.DataFrame({
            "Fuente": ["Partes", "Operadores", "Partes×Operadores", "Error (Repetibilidad)"],
            "GL": [df_parts, df_ops, df_int, df_err],
            "SC": [round(SS_parts, 5), round(SS_ops, 5), round(SS_int, 5), round(SS_err, 5)],
            "CM": [round(MS_parts, 5), round(MS_ops, 5), round(MS_int, 5), round(MS_err, 5)],
            "F": [round(F_parts, 4), round(F_ops, 4), round(F_int, 4), ""],
            "p-valor": [round(pv_parts, 5), round(pv_ops, 5), round(pv_int, 5), ""],
        }).set_index("Fuente")

        # Variance components
        var_err = max(MS_err, 0.0)  # repeatability
        var_int_raw = (MS_int - MS_err) / r
        # If interaction not significant (p>0.25 common cutoff), pool into error
        if pv_int > 0.25:
            # recompute without interaction
            SS_err2 = SS_int + SS_err
            df_err2 = df_int + df_err
            var_err = SS_err2 / df_err2
            var_int = 0.0
        else:
            var_int = max(var_int_raw, 0.0)

        var_op = max((MS_ops - MS_int) / (p * r), 0.0)
        var_parts = max((MS_parts - MS_int) / (o * r), 0.0)

    else:  # nested
        # In nested design, each operator measures a different set of parts.
        # SS_parts(within operators) = operator-specific
        SS_err = np.sum((data - data.mean(axis=2, keepdims=True)) ** 2)
        df_err = p * o * (r - 1)
        MS_err = SS_err / df_err if df_err > 0 else NAN

        # parts nested within operators
        op_part_means = data.mean(axis=2)  # (p, o)
        SS_parts_nested = r * np.sum((op_part_means - op_means[None, :]) ** 2)
        df_parts_nested = o * (p - 1)
        MS_parts_nested = SS_parts_nested / df_parts_nested

        F_ops = MS_ops / MS_parts_nested if MS_parts_nested > 0 else NAN
        F_parts = MS_parts_nested / MS_err if MS_err and MS_err > 0 else NAN
        pv_ops = 1 - stats.f.cdf(F_ops, df_ops, df_parts_nested) if not math.isnan(F_ops) else NAN
        pv_parts = 1 - stats.f.cdf(F_parts, df_parts_nested, df_err) if not math.isnan(F_parts) else NAN

        anova_df = pd.DataFrame({
            "Fuente": ["Operadores", "Partes(Operadores)", "Error"],
            "GL": [df_ops, df_parts_nested, df_err],
            "SC": [round(SS_ops, 5), round(SS_parts_nested, 5), round(SS_err, 5)],
            "CM": [round(MS_ops, 5), round(MS_parts_nested, 5), round(MS_err, 5)],
            "F": [round(F_ops, 4), round(F_parts, 4), ""],
            "p-valor": [round(pv_ops, 5), round(pv_parts, 5), ""],
        }).set_index("Fuente")

        var_err = max(MS_err, 0.0)
        var_int = 0.0
        var_op = max((MS_ops - MS_parts_nested) / (p * r), 0.0)
        var_parts = max((MS_parts_nested - MS_err) / r, 0.0)

    var_repro = var_op + var_int
    var_gage = var_err + var_repro
    var_total = var_gage + var_parts

    K = study_variation
    pct = lambda v: (v / var_total * 100) if var_total > 0 else NAN

    sv_gage = K * math.sqrt(var_gage)
    sv_total = K * math.sqrt(var_total)
    pct_sv = (sv_gage / sv_total * 100) if sv_total > 0 else NAN
    ndc = max(1, int(math.sqrt(2) * math.sqrt(var_parts) / math.sqrt(var_gage))) if var_gage > 0 else 1

    return GageRRResult(
        method="anova",
        study_variation=K,
        parts=p, operators=o, replicates=r,
        var_repeatability=var_err,
        var_reproducibility=var_repro,
        var_operator=var_op,
        var_interaction=var_int,
        var_part=var_parts,
        var_gage=var_gage,
        var_total=var_total,
        pct_gage=pct(var_gage),
        pct_repeatability=pct(var_err),
        pct_reproducibility=pct(var_repro),
        pct_part=pct(var_parts),
        study_var_gage=sv_gage,
        study_var_total=sv_total,
        pct_study_var=pct_sv,
        ndc=ndc,
        anova_table=anova_df,
        _data=data,
    )


def _gage_rr_xbar_r(data: np.ndarray, study_variation: float) -> GageRRResult:
    """Gage R&R por el método Xbar-R (AIAG MSA)."""
    from ._constants import d2
    p, o, r = data.shape

    # Ranges within each cell (part × operator)
    ranges = data.max(axis=2) - data.min(axis=2)  # (p, o)
    Rbar = ranges.mean()
    d2_r = d2(r)
    # EV (repetibilidad)
    sigma_ev = Rbar / d2_r
    var_err = sigma_ev ** 2

    # Reproducibilidad — rango de medias de operadores
    op_means = data.mean(axis=(0, 2))  # (o,)
    R_op = op_means.max() - op_means.min()
    d2_o = d2(o)
    sigma_av_raw = R_op / d2_o
    # Correct for sample size
    var_op_raw = max(sigma_av_raw ** 2 - var_err / (p * r), 0.0)
    var_op = var_op_raw
    var_repro = var_op

    # Part variation — rango de medias de partes
    part_means = data.mean(axis=(1, 2))  # (p,)
    R_part = part_means.max() - part_means.min()
    d2_p = d2(p)
    sigma_pv = R_part / d2_p
    var_parts = max(sigma_pv ** 2 - var_err / (o * r), 0.0)

    var_gage = var_err + var_repro
    var_total = var_gage + var_parts

    K = study_variation
    pct = lambda v: (v / var_total * 100) if var_total > 0 else NAN
    sv_gage = K * math.sqrt(var_gage)
    sv_total = K * math.sqrt(var_total)
    pct_sv = (sv_gage / sv_total * 100) if sv_total > 0 else NAN
    ndc = max(1, int(math.sqrt(2) * math.sqrt(var_parts) / math.sqrt(var_gage))) if var_gage > 0 else 1

    return GageRRResult(
        method="xbar_r",
        study_variation=K,
        parts=p, operators=o, replicates=r,
        var_repeatability=var_err,
        var_reproducibility=var_repro,
        var_operator=var_op,
        var_interaction=0.0,
        var_part=var_parts,
        var_gage=var_gage,
        var_total=var_total,
        pct_gage=pct(var_gage),
        pct_repeatability=pct(var_err),
        pct_reproducibility=pct(var_repro),
        pct_part=pct(var_parts),
        study_var_gage=sv_gage,
        study_var_total=sv_total,
        pct_study_var=pct_sv,
        ndc=ndc,
        anova_table=None,
        _data=data,
    )


def gage_rr(
    data,
    parts: int,
    operators: int,
    replicates: int,
    *,
    method: str = "anova",
    study_variation: float = 6.0,
    tolerance: float | None = None,
) -> GageRRResult:
    """Gage R&R cruzado (Crossed Gage R&R).

    Cada operador mide cada parte en cada réplica (diseño completamente cruzado).

    Parameters
    ----------
    data : array-like
        Mediciones. Puede ser:

        * Vector 1-D de longitud ``parts × operators × replicates`` ordenado
          de manera que las partes varían más lento, luego operadores, luego
          réplicas.
        * Array 3-D de forma ``(parts, operators, replicates)``.

    parts : int
        Número de partes.
    operators : int
        Número de operadores.
    replicates : int
        Número de réplicas por parte y operador.
    method : str
        ``'anova'`` (por defecto) o ``'xbar_r'``.
    study_variation : float
        Multiplicador K para la variación de estudio (= K·σ). Por defecto 6
        (equivalente a ±3σ, igual que Minitab).
    tolerance : float, opcional
        Tolerancia del proceso (LES − LEI). Si se proporciona, se incluye
        el % sobre tolerancia en el resumen.

    Returns
    -------
    GageRRResult
    """
    arr = _to_matrix(data, parts, operators, replicates)
    if method == "anova":
        return _gage_rr_anova(arr, study_variation, tolerance, crossed=True)
    elif method == "xbar_r":
        return _gage_rr_xbar_r(arr, study_variation)
    else:
        raise ValueError("'method' debe ser 'anova' o 'xbar_r'.")


def gage_rr_nested(
    data,
    parts: int,
    operators: int,
    replicates: int,
    *,
    study_variation: float = 6.0,
) -> GageRRResult:
    """Gage R&R anidado (Nested Gage R&R).

    Cada operador mide un conjunto distinto de partes (las partes están
    anidadas dentro de operadores).

    Parameters
    ----------
    data : array-like
        Mediciones en formato ``(parts, operators, replicates)``.
    parts : int
        Número de partes **por** operador.
    operators : int
        Número de operadores.
    replicates : int
        Número de réplicas.
    study_variation : float
        Multiplicador K. Por defecto 6.

    Returns
    -------
    GageRRResult
    """
    arr = _to_matrix(data, parts, operators, replicates)
    return _gage_rr_anova(arr, study_variation, None, crossed=False)


# ───────────────────────────────────────────────────── Type 1 Study ───────────
@dataclass
class Type1Result:
    """Resultado de :func:`gage_type1`.

    Atributos
    ---------
    reference : float
        Valor de referencia.
    n : int
        Número de mediciones.
    mean : float
        Media de las mediciones.
    std : float
        Desviación estándar.
    bias : float
        Sesgo = media − referencia.
    bias_pct : float
        Sesgo como % de la variación de estudio (K·σ) o tolerancia.
    t_stat : float
        Estadístico t para H₀: sesgo = 0.
    p_value : float
        p-valor bilateral del test de sesgo.
    cg : float
        Índice Cg (= K·tolerance / (2·study_variation·σ)).
    cgk : float
        Índice Cgk (corrige por sesgo).
    study_variation : float
        Variación de estudio (K·σ).
    tolerance : float o None
        Tolerancia del proceso.
    """

    reference: float
    n: int
    mean: float
    std: float
    bias: float
    bias_pct: float
    t_stat: float
    p_value: float
    cg: float
    cgk: float
    study_variation: float
    tolerance: float | None

    def to_frame(self) -> pd.DataFrame:
        rows = [
            ("N", self.n),
            ("Media", round(self.mean, 6)),
            ("Desv.Est.", round(self.std, 6)),
            ("Referencia", self.reference),
            ("Sesgo", round(self.bias, 6)),
            ("Sesgo (%)", round(self.bias_pct, 3)),
            ("t", round(self.t_stat, 4)),
            ("p-valor (sesgo=0)", round(self.p_value, 5)),
            ("Cg", round(self.cg, 3) if not math.isnan(self.cg) else "—"),
            ("Cgk", round(self.cgk, 3) if not math.isnan(self.cgk) else "—"),
            ("Variación de estudio", round(self.study_variation, 6)),
        ]
        if self.tolerance is not None:
            rows.append(("Tolerancia", self.tolerance))
        return pd.DataFrame(rows, columns=["estadístico", "valor"]).set_index("estadístico")

    def summary(self) -> str:
        cg_s = f"{self.cg:.3f}" if not math.isnan(self.cg) else "N/D"
        cgk_s = f"{self.cgk:.3f}" if not math.isnan(self.cgk) else "N/D"
        return (
            f"Estudio Tipo 1  (N={self.n}  Ref={self.reference})\n"
            f"  Media={self.mean:.5g}  Desv.Est.={self.std:.5g}\n"
            f"  Sesgo={self.bias:.5g} ({self.bias_pct:.2f}%)  "
            f"t={self.t_stat:.4f}  p={self.p_value:.5f}\n"
            f"  Cg={cg_s}  Cgk={cgk_s}"
        )

    def to_excel(self, path) -> None:
        """Exporta el Estudio Tipo 1 a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            self.to_frame().to_excel(writer, sheet_name="Tipo1")

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_type1
        return plot_type1(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt
        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def gage_type1(
    data,
    reference: float,
    *,
    tolerance: float | None = None,
    study_variation: float = 6.0,
) -> Type1Result:
    """Estudio Tipo 1: sesgo y repetibilidad de una sola fuente de medición.

    Parameters
    ----------
    data : array-like
        Mediciones repetidas de la misma pieza de referencia.
    reference : float
        Valor verdadero (de referencia) de la pieza.
    tolerance : float, opcional
        LES − LEI. Si se proporciona, Cg y Cgk se calculan en base a ella.
    study_variation : float
        Multiplicador K (por defecto 6).

    Returns
    -------
    Type1Result
    """
    x = as_1d(data, "data")
    n = len(x)
    if n < 2:
        raise ValueError("Se necesitan al menos 2 mediciones.")

    xbar = float(x.mean())
    s = float(x.std(ddof=1))
    bias = xbar - reference
    sv = study_variation * s

    # Test sesgo = 0
    t_stat = bias * math.sqrt(n) / s if s > 0 else NAN
    p_value = float(2 * stats.t.sf(abs(t_stat), n - 1)) if not math.isnan(t_stat) else NAN

    # Cg, Cgk requieren tolerancia
    if tolerance is not None and tolerance > 0:
        cg = 0.1 * tolerance / (study_variation * s) if s > 0 else NAN
        cgk = (0.1 * tolerance - abs(bias)) / (study_variation / 2 * s) if s > 0 else NAN
        bias_pct = bias / (study_variation * s) * 100 if sv > 0 else NAN
    else:
        cg = NAN
        cgk = NAN
        bias_pct = bias / sv * 100 if sv > 0 else NAN

    return Type1Result(
        reference=reference, n=n, mean=xbar, std=s,
        bias=bias, bias_pct=bias_pct,
        t_stat=t_stat, p_value=p_value,
        cg=cg, cgk=cgk,
        study_variation=sv, tolerance=tolerance,
    )


def gage_type1_summary(
    mean: float,
    std: float,
    n: int,
    reference: float,
    *,
    tolerance: float | None = None,
    study_variation: float = 6.0,
) -> Type1Result:
    """Estudio Tipo 1 a partir de estadísticos resumen.

    Equivalente a :func:`gage_type1` pero acepta media, desviación estándar y
    tamaño de muestra en lugar de datos crudos.

    Parameters
    ----------
    mean : float
        Media de las mediciones repetidas.
    std : float
        Desviación estándar muestral (ddof=1).
    n : int
        Número de mediciones.
    reference : float
        Valor verdadero (de referencia) de la pieza.
    tolerance : float, opcional
        LES − LEI. Si se proporciona, Cg y Cgk se calculan en base a ella.
    study_variation : float
        Multiplicador K (por defecto 6).

    Returns
    -------
    Type1Result
    """
    if n < 2:
        raise ValueError("'n' debe ser ≥ 2.")
    if std <= 0:
        raise ValueError("'std' debe ser positivo.")

    xbar, s = float(mean), float(std)
    bias = xbar - reference
    sv = study_variation * s

    t_stat = bias * math.sqrt(n) / s
    p_value = float(2 * stats.t.sf(abs(t_stat), n - 1))

    if tolerance is not None and tolerance > 0:
        cg = 0.1 * tolerance / (study_variation * s)
        cgk = (0.1 * tolerance - abs(bias)) / (study_variation / 2 * s)
        bias_pct = bias / sv * 100
    else:
        cg = NAN
        cgk = NAN
        bias_pct = bias / sv * 100 if sv > 0 else NAN

    return Type1Result(
        reference=reference, n=n, mean=xbar, std=s,
        bias=bias, bias_pct=bias_pct,
        t_stat=t_stat, p_value=p_value,
        cg=cg, cgk=cgk,
        study_variation=sv, tolerance=tolerance,
    )


# ─────────────────────────────────────────────── Linearity & Bias ─────────────
@dataclass
class LinearityResult:
    """Resultado de :func:`gage_linearity`.

    Atributos
    ---------
    references : ndarray
        Valores de referencia únicos.
    biases : ndarray
        Sesgo medio en cada valor de referencia.
    slope : float
        Pendiente de la regresión sesgo ~ referencia.
    intercept : float
        Intercepto.
    r_squared : float
        R² de la regresión.
    p_slope : float
        p-valor del test de linealidad (H₀: slope = 0).
    p_intercept : float
        p-valor H₀: intercept = 0.
    linearity : float
        abs(slope) × rango de referencias (variación de linealidad).
    linearity_pct : float
        Linealidad como % de la variación de estudio (si se da tolerancia).
    avg_bias : float
        Sesgo promedio general.
    avg_bias_pct : float
        Sesgo promedio como % de variación de estudio.
    """

    references: np.ndarray
    biases: np.ndarray
    slope: float
    intercept: float
    r_squared: float
    p_slope: float
    p_intercept: float
    linearity: float
    linearity_pct: float
    avg_bias: float
    avg_bias_pct: float
    tolerance: float | None
    _all_refs: np.ndarray = field(repr=False)
    _all_biases: np.ndarray = field(repr=False)

    def to_frame(self) -> pd.DataFrame:
        rows = [
            ("Nº de valores referencia", len(self.references)),
            ("Pendiente", round(self.slope, 6)),
            ("Intercepto", round(self.intercept, 6)),
            ("R²", round(self.r_squared, 5)),
            ("p-valor (pendiente=0)", round(self.p_slope, 5)),
            ("p-valor (intercepto=0)", round(self.p_intercept, 5)),
            ("Linealidad", round(self.linearity, 6)),
            ("Linealidad (%)", round(self.linearity_pct, 3)),
            ("Sesgo promedio", round(self.avg_bias, 6)),
            ("Sesgo promedio (%)", round(self.avg_bias_pct, 3)),
        ]
        return pd.DataFrame(rows, columns=["estadístico", "valor"]).set_index("estadístico")

    def summary(self) -> str:
        return (
            f"Linealidad y sesgo\n"
            f"  Pendiente={self.slope:.5g}  Intercepto={self.intercept:.5g}\n"
            f"  R²={self.r_squared:.4f}  p(pendiente=0)={self.p_slope:.5f}\n"
            f"  Linealidad={self.linearity:.5g} ({self.linearity_pct:.2f}%)\n"
            f"  Sesgo promedio={self.avg_bias:.5g} ({self.avg_bias_pct:.2f}%)"
        )

    def to_excel(self, path) -> None:
        """Exporta el análisis de linealidad a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        """
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            self.to_frame().to_excel(writer, sheet_name="Linealidad")

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_linearity
        return plot_linearity(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt
        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def gage_linearity(
    measurements,
    references,
    *,
    tolerance: float | None = None,
    study_variation: float = 6.0,
) -> LinearityResult:
    """Estudio de linealidad y sesgo del sistema de medición.

    Parameters
    ----------
    measurements : array-like
        Vector de mediciones (pueden ser múltiples por valor de referencia).
    references : array-like
        Vector de valores de referencia correspondiente a cada medición.
    tolerance : float, opcional
        LES − LEI para calcular % de variación de estudio.
    study_variation : float
        Multiplicador K (por defecto 6).

    Returns
    -------
    LinearityResult
    """
    m = np.asarray(measurements, dtype=float).ravel()
    r = np.asarray(references, dtype=float).ravel()
    if len(m) != len(r):
        raise ValueError("'measurements' y 'references' deben tener la misma longitud.")
    if len(m) < 3:
        raise ValueError("Se necesitan al menos 3 pares para la regresión.")

    bias_all = m - r
    refs_unique = np.unique(r)

    # Mean bias per reference level
    biases = np.array([bias_all[r == ref].mean() for ref in refs_unique])

    # Regression: bias ~ reference (using all individual points)
    n = len(m)
    slope, intercept, r_val, p_val, _se_slope = stats.linregress(r, bias_all)
    r_sq = r_val ** 2

    # p-value for intercept
    y_hat = intercept + slope * r
    resid = bias_all - y_hat
    MSE = (resid ** 2).sum() / (n - 2)
    x_mean = r.mean()
    Sxx = ((r - x_mean) ** 2).sum()
    se_intercept = math.sqrt(MSE * (1.0 / n + x_mean ** 2 / Sxx)) if Sxx > 0 else NAN
    t_int = intercept / se_intercept if not math.isnan(se_intercept) else NAN
    p_intercept = float(2 * stats.t.sf(abs(t_int), n - 2)) if not math.isnan(t_int) else NAN

    ref_range = float(refs_unique.max() - refs_unique.min())
    linearity = abs(slope) * ref_range

    denom = tolerance if (tolerance and tolerance > 0) else study_variation * math.sqrt(MSE)
    lin_pct = linearity / denom * 100 if denom > 0 else NAN
    avg_bias = float(bias_all.mean())
    avg_bias_pct = avg_bias / denom * 100 if denom > 0 else NAN

    return LinearityResult(
        references=refs_unique, biases=biases,
        slope=float(slope), intercept=float(intercept),
        r_squared=float(r_sq), p_slope=float(p_val), p_intercept=float(p_intercept),
        linearity=linearity, linearity_pct=lin_pct,
        avg_bias=avg_bias, avg_bias_pct=avg_bias_pct,
        tolerance=tolerance,
        _all_refs=r, _all_biases=bias_all,
    )


# ─────────────────────────────────── Attribute Agreement Analysis (Kappa) ────
@dataclass
class AttributeAgreementResult:
    """Resultado de :func:`attribute_agreement`.

    Atributos
    ---------
    kappa_within : pd.DataFrame
        Kappa de cada operador consigo mismo (repetibilidad).
    kappa_vs_reference : pd.DataFrame
        Kappa de cada operador vs referencia.
    kappa_overall : float
        Kappa global de todos los operadores vs referencia.
    fleiss_kappa : float
        Kappa de Fleiss (acuerdo entre todos los operadores).
    pct_agreement_within : pd.Series
        % de acuerdo de cada operador consigo mismo.
    pct_agreement_vs_ref : pd.Series
        % de acuerdo de cada operador vs referencia.
    pct_agreement_overall : float
        % de acuerdo global vs referencia.
    """

    kappa_within: pd.DataFrame
    kappa_vs_reference: pd.DataFrame
    kappa_overall: float
    fleiss_kappa: float
    pct_agreement_within: pd.Series
    pct_agreement_vs_ref: pd.Series
    pct_agreement_overall: float
    categories: list
    _data: pd.DataFrame = field(repr=False)

    def to_frame(self) -> pd.DataFrame:
        rows: list[tuple] = [
            ("Kappa global vs referencia", round(self.kappa_overall, 5)),
            ("Kappa de Fleiss (entre operadores)", round(self.fleiss_kappa, 5)),
            ("% Acuerdo global vs referencia", round(self.pct_agreement_overall, 2)),
        ]
        return pd.DataFrame(rows, columns=["estadístico", "valor"]).set_index("estadístico")

    def summary(self) -> str:
        lines = [
            "Análisis de concordancia por atributos",
            f"  Kappa global vs referencia = {self.kappa_overall:.4f}",
            f"  Kappa de Fleiss             = {self.fleiss_kappa:.4f}",
            f"  % Acuerdo global vs ref     = {self.pct_agreement_overall:.1f}%",
            "",
            "  Kappa por operador vs referencia:",
        ]
        for op, row in self.kappa_vs_reference.iterrows():
            lines.append(f"    {op}: κ={row['kappa']:.4f}  p-valor={row['p_valor']:.5f}  "
                         f"Acuerdo={row['% acuerdo']:.1f}%")
        return "\n".join(lines)

    def to_excel(self, path) -> None:
        """Exporta la concordancia por atributos a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        Hojas: Resumen, KappaVsReferencia (si hay más de un operador).
        """
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            self.to_frame().to_excel(writer, sheet_name="Resumen")
            if not self.kappa_vs_reference.empty:
                self.kappa_vs_reference.to_excel(writer, sheet_name="KappaVsReferencia")

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_attribute_agreement
        return plot_attribute_agreement(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt
        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def _cohen_kappa(a: np.ndarray, b: np.ndarray, categories) -> tuple[float, float, float]:
    """Kappa de Cohen entre dos vectores a y b. Devuelve (kappa, p_valor, pct)."""
    n = len(a)
    cats = list(categories)
    mat = np.zeros((len(cats), len(cats)), dtype=float)
    for ai, bi in zip(a, b):
        i, j = cats.index(ai), cats.index(bi)
        mat[i, j] += 1
    po = mat.diagonal().sum() / n
    row_sums = mat.sum(axis=1) / n
    col_sums = mat.sum(axis=0) / n
    pe = float(np.dot(row_sums, col_sums))
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    # Standard error for test kappa=0
    se = math.sqrt(pe / (n * (1 - pe))) if pe < 1 and n > 0 else 1e-9
    z = kappa / se if se > 0 else NAN
    p_val = float(2 * stats.norm.sf(abs(z))) if not math.isnan(z) else NAN
    return float(kappa), float(p_val), float(po * 100)


def _fleiss_kappa(ratings: pd.DataFrame, categories) -> float:
    """Kappa de Fleiss para múltiples evaluadores y categorías."""
    # ratings: shape (n_items, n_raters)
    n, k = ratings.shape
    cats = list(categories)
    c = len(cats)
    # Count matrix: (n, c)
    counts = np.zeros((n, c), dtype=float)
    for j, cat in enumerate(cats):
        counts[:, j] = (ratings == cat).sum(axis=1)
    pj = counts.sum(axis=0) / (n * k)
    pi_arr = ((counts ** 2).sum(axis=1) - k) / (k * (k - 1)) if k > 1 else np.ones(n)
    P_bar = pi_arr.mean()
    Pe = float((pj ** 2).sum())
    return (P_bar - Pe) / (1 - Pe) if Pe < 1 else 1.0


def attribute_agreement(
    data: pd.DataFrame | np.ndarray,
    *,
    reference: pd.Series | np.ndarray | None = None,
    operators: list[str] | None = None,
    replicates: int = 2,
) -> AttributeAgreementResult:
    """Análisis de concordancia por atributos (Kappa de Cohen y Fleiss).

    Parameters
    ----------
    data : DataFrame o ndarray
        Clasificaciones de los operadores. Si es DataFrame, cada columna es
        un operador y cada fila una observación (parte × réplica). Si es
        ndarray, forma ``(n_parts × replicates, n_operators)``.
    reference : array-like, opcional
        Clasificación de referencia (de longitud n_parts × replicates o n_parts).
        Si tiene longitud n_parts, se repite ``replicates`` veces.
    operators : list[str], opcional
        Nombres de los operadores.
    replicates : int
        Número de réplicas por parte (usado para calcular acuerdo dentro del
        mismo operador).

    Returns
    -------
    AttributeAgreementResult
    """
    if isinstance(data, np.ndarray):
        df = pd.DataFrame(data, columns=operators or [f"Op{i+1}" for i in range(data.shape[1])])
    else:
        df = data.copy()
        if operators:
            df.columns = operators

    n_total = len(df)
    n_parts = n_total // replicates
    ops = list(df.columns)

    # Categories
    all_vals = df.values.ravel()
    if reference is not None:
        ref_arr = np.asarray(reference)
        if len(ref_arr) == n_parts:
            ref_arr = np.repeat(ref_arr, replicates)
        all_vals = np.concatenate([all_vals, ref_arr])
    categories = sorted({v for v in all_vals if pd.notna(v)})

    # Kappa within (each operator vs itself across replicates)
    kappa_within_rows = []
    pct_within = {}
    for op in ops:
        vals = df[op].to_numpy()
        # Split into replicates
        reps = [vals[i::replicates] for i in range(replicates)]
        if len(reps) >= 2:
            k_sum, p_sum, pct_sum = 0.0, 0.0, 0.0
            cnt = 0
            for i in range(len(reps)):
                for j in range(i + 1, len(reps)):
                    k, p, pct = _cohen_kappa(reps[i], reps[j], categories)
                    k_sum += k; p_sum += p; pct_sum += pct; cnt += 1
            kappa_within_rows.append({"operador": op, "kappa": k_sum / cnt,
                                      "p_valor": p_sum / cnt, "% acuerdo": pct_sum / cnt})
            pct_within[op] = pct_sum / cnt
        else:
            kappa_within_rows.append({"operador": op, "kappa": NAN, "p_valor": NAN, "% acuerdo": NAN})
            pct_within[op] = NAN
    kappa_within_df = pd.DataFrame(kappa_within_rows).set_index("operador")

    # Kappa vs reference
    kappa_ref_rows = []
    pct_vs_ref = {}
    if reference is not None:
        ref_arr = np.asarray(reference)
        if len(ref_arr) == n_parts:
            ref_arr = np.repeat(ref_arr, replicates)
        for op in ops:
            k, p, pct = _cohen_kappa(df[op].to_numpy(), ref_arr, categories)
            kappa_ref_rows.append({"operador": op, "kappa": k, "p_valor": p, "% acuerdo": pct})
            pct_vs_ref[op] = pct
        # Overall: flatten all operators vs reference (transpose so ops are first dim)
        all_op_vals = df.values.T.ravel()
        all_ref_vals = np.tile(ref_arr, len(ops))
        k_overall, _, pct_overall = _cohen_kappa(all_op_vals, all_ref_vals, categories)
    else:
        k_overall, pct_overall = NAN, NAN
    kappa_ref_df = pd.DataFrame(kappa_ref_rows).set_index("operador") if kappa_ref_rows else pd.DataFrame()

    # Fleiss kappa (between all operators, one row per part-replicate)
    fleiss_k = _fleiss_kappa(df, categories)

    return AttributeAgreementResult(
        kappa_within=kappa_within_df,
        kappa_vs_reference=kappa_ref_df,
        kappa_overall=float(k_overall),
        fleiss_kappa=float(fleiss_k),
        pct_agreement_within=pd.Series(pct_within, name="% acuerdo"),
        pct_agreement_vs_ref=pd.Series(pct_vs_ref, name="% acuerdo"),
        pct_agreement_overall=float(pct_overall),
        categories=categories,
        _data=df,
    )
