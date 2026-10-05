"""Asistente interactivo de selección de análisis SPC — pccpy wizard.

Tres modos:
  'auto'   — analiza los datos y devuelve una recomendación sin interacción.
  'cli'    — menú de preguntas con opciones numeradas en la terminal.
  'widget' — interfaz gráfica para Jupyter (requiere ipywidgets).
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ._i18n import N_, tr

__all__ = ["WidgetSession", "WizardResult", "wizard"]

# ══════════════════════════════════════════════════════════════════════════════
# Resultado
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class WizardResult:
    """Recomendación de análisis devuelta por el asistente."""

    function: str
    params: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    alternatives: list[str] = field(default_factory=list)
    _snippet: str = field(default="", repr=False)

    def snippet(self) -> str:
        """Fragmento de código listo para usar."""
        if self._snippet:
            return textwrap.dedent(tr(self._snippet)).strip()
        args = ", ".join(f"{k}={v!r}" for k, v in self.params.items())
        sep = ", " if args else ""
        return tr("import pccpy as pp\nresultado = pp.{function}(datos{sep}{args})").format(
            function=self.function, sep=sep, args=args)

    def summary(self) -> str:
        lines = [
            "═" * 56,
            tr("  Análisis recomendado : {function}").format(function=self.function),
            tr("  Razón                : {rationale}").format(rationale=tr(self.rationale)),
        ]
        if self.params:
            lines.append(tr("  Parámetros sugeridos : {params}").format(params=self.params))
        if self.alternatives:
            lines.append(tr("  Alternativas         : {alternatives}").format(alternatives=", ".join(self.alternatives)))
        lines += [
            "─" * 56,
            tr("  Código:"),
            "",
        ]
        for ln in self.snippet().splitlines():
            lines.append("    " + ln)
        lines.append("═" * 56)
        return "\n".join(lines)

    def run(self, data: Any, **kwargs: Any) -> Any:
        """Ejecuta el análisis recomendado con los datos dados."""
        import pccpy
        fn = getattr(pccpy, self.function)
        return fn(data, **{**self.params, **kwargs})


# ══════════════════════════════════════════════════════════════════════════════
# Árbol de decisión
# ══════════════════════════════════════════════════════════════════════════════
# Cada nodo es (pregunta, [(texto_opción, nodo_destino), ...])
# Los nodos cuyo nombre empieza por "r:" son hojas que devuelven WizardResult.

_TREE: dict[str, tuple[str, list[tuple[str, str]]]] = {
    # ── raíz ──────────────────────────────────────────────────────────────────
    "root": (
        N_("¿Cuál es tu objetivo principal?"),
        [
            (N_("Monitorear el proceso (cartas de control)"),    "cartas"),
            (N_("Analizar la capacidad del proceso"),            "capacidad"),
            (N_("Sistema de medición (MSA / Gage R&R)"),         "msa"),
            (N_("Muestreo de aceptación"),                       "muestreo"),
            (N_("Análisis exploratorio (normalidad, Pareto)"),   "exploratorio"),
            (N_("Intervalos de tolerancia"),                     "tolerancia"),
            (N_("Carta de corridas o pre-control"),              "corridas"),
        ],
    ),

    # ── cartas ────────────────────────────────────────────────────────────────
    "cartas": (
        N_("¿Qué tipo de datos tienes?"),
        [
            (N_("Mediciones continuas — una por instante (individual)"),  "cartas_ind"),
            (N_("Mediciones continuas — en subgrupos (varias por muestra)"), "cartas_sub"),
            (N_("Fracción defectuosa  (piezas malas / total muestral)"),  "cartas_p"),
            (N_("Número de defectos por unidad inspeccionada"),           "cartas_c"),
            (N_("Varias variables simultáneas (multivariado)"),           "cartas_mv"),
            (N_("Eventos raros (muy poca frecuencia de defectos)"),       "cartas_raros"),
            (N_("Corridas cortas (piezas con distintas especificaciones)"),"r:zmr"),
        ],
    ),

    "cartas_ind": (
        N_("¿Necesitas detectar desplazamientos pequeños (< 1.5σ) con mayor rapidez?"),
        [
            (N_("No — sensibilidad estándar Shewhart"),                   "r:imr"),
            (N_("Sí — desplazamientos graduales sostenidos → EWMA"),      "r:ewma"),
            (N_("Sí — cambios abruptos pequeños → CUSUM"),                "r:cusum"),
            (N_("Hay variación entre subgrupos (turno, lote, cavidad) → I-MR-R/S"), "r:imr_rs"),
        ],
    ),

    "cartas_sub": (
        N_("¿Cuál es el tamaño de los subgrupos?"),
        [
            (N_("≤ 8 observaciones por subgrupo  → Xbar-R"),    "cartas_sub_r"),
            (N_("> 8 observaciones por subgrupo  → Xbar-S"),    "r:xbar_s"),
        ],
    ),

    "cartas_sub_r": (
        N_("¿Necesitas detectar desplazamientos pequeños?"),
        [
            (N_("No — sensibilidad estándar → Xbar-R"),         "r:xbar_r"),
            (N_("Sí — alta sensibilidad → EWMA (subgrupos)"),   "r:ewma_sub"),
        ],
    ),

    "cartas_p": (
        N_("¿El tamaño de muestra es constante entre períodos?"),
        [
            (N_("Sí, constante → NP (número de defectuosos)"),  "r:np"),
            (N_("No, variable  → P (fracción defectuosa)"),     "cartas_p_var"),
        ],
    ),

    "cartas_p_var": (
        N_("¿Sospechas sobredispersión (más variabilidad de la esperada)?"),
        [
            (N_("No o no lo sé → P estándar"),                  "r:p"),
            (N_("Sí — corrige sobredispersión → Laney P′"),     "r:laney_p"),
        ],
    ),

    "cartas_c": (
        N_("¿El área / número de unidades inspeccionadas varía entre muestras?"),
        [
            (N_("No — unidades constantes → C (defectos por muestra)"), "cartas_c_over"),
            (N_("Sí — unidades variables  → U (tasa de defectos)"),     "cartas_u_over"),
        ],
    ),

    "cartas_c_over": (
        N_("¿Sospechas sobredispersión?"),
        [
            (N_("No → C estándar"),                             "r:c"),
            (N_("Sí → Laney U′ (versión robusta de U)"),        "r:laney_u"),
        ],
    ),

    "cartas_u_over": (
        N_("¿Sospechas sobredispersión?"),
        [
            (N_("No → U estándar"),                             "r:u"),
            (N_("Sí → Laney U′"),                               "r:laney_u"),
        ],
    ),

    "cartas_mv": (
        N_("¿Necesitas alta sensibilidad a pequeños desplazamientos?"),
        [
            (N_("No — sensibilidad estándar → T² de Hotelling"), "r:t2"),
            (N_("Sí → MEWMA (media) o MCUSUM (suma acumulada)"), "cartas_mv_ts"),
        ],
    ),

    "cartas_mv_ts": (
        N_("¿Cuál prefieres?"),
        [
            (N_("MEWMA — mejor para desplazamientos sostenidos graduales"), "r:mewma"),
            (N_("MCUSUM — mejor para cambios abruptos pequeños"),           "r:mcusum"),
        ],
    ),

    "cartas_raros": (
        N_("¿Qué mides entre eventos?"),
        [
            (N_("Número de piezas o casos entre eventos → G"),  "r:g"),
            (N_("Tiempo entre eventos → T"),                    "r:t"),
        ],
    ),

    # ── capacidad ─────────────────────────────────────────────────────────────
    "capacidad": (
        N_("¿Los datos siguen distribución normal?"),
        [
            (N_("Sí (o no lo sé — puedes verificar con normality_test)"), "cap_normal"),
            (N_("No — se ajusta a otra distribución conocida"),           "r:cap_nn"),
            (N_("No — intentar transformación Box-Cox automática"),       "r:cap_bc"),
        ],
    ),

    "cap_normal": (
        N_("¿Qué tipo de reporte de capacidad necesitas?"),
        [
            (N_("Índices Cp, Cpk, Pp, Ppk, PPM y Z.Bench"),            "r:capability"),
            (N_("Análisis completo en una sola figura (Sixpack)"),       "r:sixpack"),
            (N_("Solo tengo estadísticos resumen (media, σ, n)"),        "r:cap_summary"),
        ],
    ),

    # ── MSA ───────────────────────────────────────────────────────────────────
    "msa": (
        N_("¿Qué tipo de estudio del sistema de medición necesitas?"),
        [
            (N_("Crossed Gage R&R — todos los operadores miden todas las partes"), "r:gage_rr"),
            (N_("Nested Gage R&R — cada operador mide partes distintas"),          "r:gage_rr_nested"),
            (N_("Estudio Tipo 1 — sesgo y repetibilidad de un instrumento"),       "r:gage_type1"),
            (N_("Linealidad y sesgo — sesgo varía con el valor de referencia?"),   "r:gage_lin"),
            (N_("Concordancia por atributos (Kappa de Cohen / Fleiss)"),           "r:attr_agreement"),
        ],
    ),

    # ── muestreo de aceptación ────────────────────────────────────────────────
    "muestreo": (
        N_("¿Cómo se mide la característica de calidad?"),
        [
            (N_("Por atributos (conforme / no conforme) → norma Z1.4"),  "r:z14"),
            (N_("Por variables (medición continua)      → norma Z1.9"),  "r:z19"),
            (N_("Minimizar inspección total (Dodge-Romig)"),              "muestreo_dr"),
        ],
    ),

    "muestreo_dr": (
        N_("¿Qué restricción defines para el plan Dodge-Romig?"),
        [
            (N_("LTPD fijo — proteger contra calidad inaceptable"),      "r:dr_ltpd"),
            (N_("AOQL fijo — limitar la calidad saliente promedio"),      "r:dr_aoql"),
        ],
    ),

    # ── exploratorio ──────────────────────────────────────────────────────────
    "exploratorio": (
        N_("¿Qué análisis exploratorio necesitas?"),
        [
            (N_("Prueba de normalidad (Anderson-Darling, Shapiro-Wilk)"),   "r:normality"),
            (N_("Diagrama de Pareto (frecuencia de categorías o defectos)"), "r:pareto"),
            (N_("Gráfico de probabilidad normal"),                           "r:prob_plot"),
        ],
    ),

    # ── intervalos de tolerancia ──────────────────────────────────────────────
    "tolerancia": (
        N_("¿Dispones de los datos individuales o solo de estadísticos resumen?"),
        [
            (N_("Tengo los datos individuales"),           "tol_datos"),
            (N_("Solo tengo media, desviación típica y n"), "r:tol_summary"),
        ],
    ),

    "tol_datos": (
        N_("¿Los datos siguen distribución normal?"),
        [
            (N_("Sí — intervalo normal (factor k de Wald-Wolfowitz)"),  "tol_lados"),
            (N_("No — intervalo no paramétrico (estadísticos de orden)"), "r:tol_np"),
        ],
    ),

    "tol_lados": (
        N_("¿Qué tipo de límite necesitas?"),
        [
            (N_("Bilateral  — límite inferior y superior"), "r:tol_two"),
            (N_("Unilateral superior — solo cota máxima"),  "r:tol_upper"),
            (N_("Unilateral inferior — solo cota mínima"),  "r:tol_lower"),
        ],
    ),

    # ── corridas / pre-control ─────────────────────────────────────────────────
    "corridas": (
        N_("¿Qué análisis necesitas?"),
        [
            (N_("Carta de corridas — detectar patrones no aleatorios (p-valores)"), "r:run"),
            (N_("Pre-control (Shainin) — semáforo verde / amarillo / rojo"),        "r:precontrol"),
        ],
    ),
}

# ── Hojas (resultados) ────────────────────────────────────────────────────────

def _r(function: str, rationale: str, params: dict | None = None,
       alts: list[str] | None = None, code: str = "") -> WizardResult:
    return WizardResult(
        function=function,
        params=params or {},
        rationale=rationale,
        alternatives=alts or [],
        _snippet=code,  # texto original (msgid); se traduce y se alinea en snippet()
    )


_RESULTS: dict[str, WizardResult] = {
    "r:imr": _r(
        "imr_chart",
        N_("Datos continuos individuales — carta I-MR estándar Shewhart"),
        {"tests": (1, 2, 3, 4, 5, 6, 7, 8)},
        alts=["ewma_chart", "cusum_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.imr_chart(datos, tests=(1, 2, 3, 4, 5, 6, 7, 8))
            print(carta.summary())
            carta.plot()
        """),
    ),
    "r:ewma": _r(
        "ewma_chart",
        N_("Alta sensibilidad a desplazamientos sostenidos (λ=0.2 recomendado)"),
        {"weight": 0.2, "k": 3.0},
        alts=["imr_chart", "cusum_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.ewma_chart(datos, weight=0.2, k=3.0)
            carta.plot()
        """),
    ),
    "r:cusum": _r(
        "cusum_chart",
        N_("Alta sensibilidad a cambios abruptos pequeños (H=4, K=0.5)"),
        {"h": 4.0, "k": 0.5},
        alts=["imr_chart", "ewma_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.cusum_chart(datos, h=4.0, k=0.5)
            carta.plot()
        """),
    ),
    "r:imr_rs": _r(
        "imr_rs_chart",
        N_("Variación entre y dentro de subgrupos — descompone ambas fuentes"),
        {},
        alts=["imr_chart"],
        code=N_("""
            import pccpy as pp
            # datos: matriz 2-D (n_subgrupos × tamaño_subgrupo)
            carta = pp.imr_rs_chart(datos)
            carta.plot()
        """),
    ),
    "r:xbar_r": _r(
        "xbar_r_chart",
        N_("Datos en subgrupos pequeños (n ≤ 8) — carta Xbar-R"),
        {"tests": (1, 2, 3, 4, 5, 6, 7, 8)},
        alts=["xbar_s_chart", "ewma_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.xbar_r_chart(datos, tests=(1, 2, 3, 4, 5, 6, 7, 8))
            carta.plot()
        """),
    ),
    "r:xbar_s": _r(
        "xbar_s_chart",
        N_("Datos en subgrupos grandes (n > 8) — carta Xbar-S"),
        {"tests": (1, 2, 3, 4, 5, 6, 7, 8)},
        alts=["xbar_r_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.xbar_s_chart(datos, tests=(1, 2, 3, 4, 5, 6, 7, 8))
            carta.plot()
        """),
    ),
    "r:ewma_sub": _r(
        "ewma_chart",
        N_("EWMA para datos en subgrupos con alta sensibilidad"),
        {"weight": 0.2},
        alts=["xbar_r_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.ewma_chart(datos, weight=0.2)
            carta.plot()
        """),
    ),
    "r:np": _r(
        "np_chart",
        N_("Número de defectuosos con tamaño de muestra constante"),
        {},
        alts=["p_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.np_chart(defectuosos, n=tamaño_muestra)
            carta.plot()
        """),
    ),
    "r:p": _r(
        "p_chart",
        N_("Fracción defectuosa con tamaño de muestra variable"),
        {},
        alts=["laney_p_chart", "np_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.p_chart(defectuosos, n=tamaños)
            carta.plot()
        """),
    ),
    "r:laney_p": _r(
        "laney_p_chart",
        N_("Fracción defectuosa con corrección de sobredispersión (Laney P′)"),
        {},
        alts=["p_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.laney_p_chart(defectuosos, n=tamaños)
            carta.plot()
        """),
    ),
    "r:c": _r(
        "c_chart",
        N_("Número de defectos con unidades de inspección constantes"),
        {},
        alts=["u_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.c_chart(defectos)
            carta.plot()
        """),
    ),
    "r:u": _r(
        "u_chart",
        N_("Tasa de defectos por unidad con tamaño de muestra variable"),
        {},
        alts=["laney_u_chart", "c_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.u_chart(defectos, n=unidades)
            carta.plot()
        """),
    ),
    "r:laney_u": _r(
        "laney_u_chart",
        N_("Tasa de defectos con corrección de sobredispersión (Laney U′)"),
        {},
        alts=["u_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.laney_u_chart(defectos, n=unidades)
            carta.plot()
        """),
    ),
    "r:t2": _r(
        "t2_chart",
        N_("T² de Hotelling — monitoreo multivariado estándar"),
        {},
        alts=["mewma_chart", "mcusum_chart"],
        code=N_("""
            import pccpy as pp
            # datos: matriz 2-D (n_observaciones × n_variables)
            carta = pp.t2_chart(datos)
            carta.plot()
        """),
    ),
    "r:mewma": _r(
        "mewma_chart",
        N_("MEWMA — sensibilidad alta a desplazamientos multivariados sostenidos"),
        {"weight": 0.1, "arl": 200},
        alts=["t2_chart", "mcusum_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.mewma_chart(datos, weight=0.1, arl=200)
            carta.plot()
        """),
    ),
    "r:mcusum": _r(
        "mcusum_chart",
        N_("MCUSUM — sensibilidad alta a cambios abruptos multivariados"),
        {"k": 0.5, "arl": 200},
        alts=["t2_chart", "mewma_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.mcusum_chart(datos, k=0.5, arl=200)
            carta.plot()
        """),
    ),
    "r:g": _r(
        "g_chart",
        N_("Eventos raros — número de unidades entre eventos (distribución geométrica)"),
        {},
        alts=["t_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.g_chart(entre_eventos)
            carta.plot()
        """),
    ),
    "r:t": _r(
        "t_chart",
        N_("Eventos raros — tiempo entre eventos (Weibull o exponencial)"),
        {},
        alts=["g_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.t_chart(tiempos)   # dist='weibull' por defecto
            carta.plot()
        """),
    ),
    "r:zmr": _r(
        "zmr_chart",
        N_("Corridas cortas — estandariza cada parte con sus propios parámetros"),
        {},
        alts=["imr_chart"],
        code=N_("""
            import pccpy as pp
            carta = pp.zmr_chart(medidas, partes)
            carta.plot()
        """),
    ),
    "r:capability": _r(
        "capability_analysis",
        N_("Capacidad normal — Cp, Cpk, Pp, Ppk, PPM, Z.Bench"),
        {},
        alts=["capability_sixpack", "capability_nonnormal"],
        code=N_("""
            import pccpy as pp
            res = pp.capability_analysis(datos, lsl=lsl, usl=usl)
            print(res.summary())
            res.plot()
        """),
    ),
    "r:sixpack": _r(
        "capability_sixpack",
        N_("Capability Sixpack — 6 vistas en una figura (igual que Minitab)"),
        {},
        alts=["capability_analysis"],
        code=N_("""
            import pccpy as pp
            import matplotlib.pyplot as plt
            fig, res, carta = pp.capability_sixpack(datos, lsl=lsl, usl=usl)
            plt.show()
        """),
    ),
    "r:cap_summary": _r(
        "capability_analysis_summary",
        N_("Capacidad desde estadísticos resumen (media, σ, n)"),
        {},
        alts=["capability_analysis"],
        code=N_("""
            import pccpy as pp
            res = pp.capability_analysis_summary(
                mean=media, std_overall=sigma, n=n,
                lsl=lsl, usl=usl,
            )
            print(res.summary())
        """),
    ),
    "r:cap_nn": _r(
        "capability_nonnormal",
        N_("Capacidad no normal — ajuste por máxima verosimilitud a distribución alternativa"),
        {"distribution": "weibull"},
        alts=["capability_boxcox"],
        code=N_("""
            import pccpy as pp
            # distribution: 'weibull', 'lognormal', 'gamma', 'loglogistic', ...
            res = pp.capability_nonnormal(datos, lsl=lsl, usl=usl,
                                          distribution='weibull')
            print(res.summary())
        """),
    ),
    "r:cap_bc": _r(
        "capability_boxcox",
        N_("Transformación Box-Cox automática para normalizar los datos"),
        {},
        alts=["capability_nonnormal"],
        code=N_("""
            import pccpy as pp
            res = pp.capability_boxcox(datos, lsl=lsl, usl=usl)
            print(res.summary())   # incluye lambda estimada
        """),
    ),
    "r:gage_rr": _r(
        "gage_rr",
        N_("Crossed Gage R&R — ANOVA (todos los operadores miden todas las partes)"),
        {"method": "anova"},
        alts=["gage_rr_nested"],
        code=N_("""
            import pccpy as pp
            grr = pp.gage_rr(datos, parts=n_partes, operators=n_operadores,
                             replicates=n_replicas, tolerance=tolerancia)
            print(grr.summary())
            grr.plot()
        """),
    ),
    "r:gage_rr_nested": _r(
        "gage_rr_nested",
        N_("Nested Gage R&R — cada operador mide partes distintas"),
        {},
        alts=["gage_rr"],
        code=N_("""
            import pccpy as pp
            grr = pp.gage_rr_nested(datos, parts=n_partes, operators=n_operadores,
                                    replicates=n_replicas)
            print(grr.summary())
        """),
    ),
    "r:gage_type1": _r(
        "gage_type1",
        N_("Estudio Tipo 1 — sesgo, t-test, Cg y Cgk"),
        {},
        alts=["gage_linearity"],
        code=N_("""
            import pccpy as pp
            t1 = pp.gage_type1(mediciones, reference=valor_ref, tolerance=tolerancia)
            print(t1.summary())
        """),
    ),
    "r:gage_lin": _r(
        "gage_linearity",
        N_("Linealidad y sesgo — detecta si el sesgo cambia con el valor medido"),
        {},
        alts=["gage_type1"],
        code=N_("""
            import pccpy as pp
            lin = pp.gage_linearity(mediciones, referencias, tolerance=tolerancia)
            print(lin.summary())
            lin.plot()
        """),
    ),
    "r:attr_agreement": _r(
        "attribute_agreement",
        N_("Concordancia por atributos — Kappa de Cohen por operador + Kappa de Fleiss"),
        {},
        alts=["gage_rr"],
        code=N_("""
            import pccpy as pp
            import pandas as pd
            # df: DataFrame con una columna por operador
            res = pp.attribute_agreement(df, reference=referencia, replicates=n_replicas)
            print(res.summary())
        """),
    ),
    "r:z14": _r(
        "acceptance_sampling_attributes",
        N_("Muestreo de aceptación por atributos — norma ANSI/ASQ Z1.4"),
        {},
        alts=["acceptance_sampling_variables", "dodge_romig"],
        code=N_("""
            import pccpy as pp
            plan = pp.acceptance_sampling_attributes(N=tamaño_lote, aql=aql)
            print(plan.summary())
            plan.plot()
        """),
    ),
    "r:z19": _r(
        "acceptance_sampling_variables",
        N_("Muestreo de aceptación por variables — norma ANSI/ASQ Z1.9"),
        {},
        alts=["acceptance_sampling_attributes"],
        code=N_("""
            import pccpy as pp
            plan = pp.acceptance_sampling_variables(N=tamaño_lote, aql=aql,
                                                    spec_type='one')
            muestra = ...   # array con las mediciones
            dec = plan.evaluate(muestra, usl=usl)
            print(dec)      # {'xbar': ..., 's': ..., 'accept': True/False}
        """),
    ),
    "r:dr_ltpd": _r(
        "dodge_romig",
        N_("Dodge-Romig LTPD — minimiza ATI con tolerancia a calidad mínima aceptable"),
        {},
        alts=["acceptance_sampling_attributes"],
        code=N_("""
            import pccpy as pp
            plan = pp.dodge_romig(N=tamaño_lote, ltpd=ltpd, process_avg=p_promedio)
            print(plan.summary())
        """),
    ),
    "r:dr_aoql": _r(
        "dodge_romig",
        N_("Dodge-Romig AOQL — minimiza ATI con límite de calidad saliente promedio"),
        {},
        alts=["acceptance_sampling_attributes"],
        code=N_("""
            import pccpy as pp
            plan = pp.dodge_romig(N=tamaño_lote, aoql=aoql, process_avg=p_promedio)
            print(plan.summary())
        """),
    ),
    "r:normality": _r(
        "normality_test",
        N_("Prueba de normalidad Anderson-Darling (compatible con Minitab)"),
        {"method": "ad"},
        alts=["probability_plot"],
        code=N_("""
            import pccpy as pp
            res = pp.normality_test(datos, method='ad')
            print(res.summary())
            pp.probability_plot(datos)
        """),
    ),
    "r:pareto": _r(
        "pareto",
        N_("Diagrama de Pareto — ordena categorías por frecuencia acumulada"),
        {},
        alts=[],
        code=N_("""
            import pccpy as pp
            tabla = pp.pareto(categorias)
            pp.plot_pareto(tabla)
        """),
    ),
    "r:prob_plot": _r(
        "probability_plot",
        N_("Gráfico de probabilidad normal con línea Anderson-Darling"),
        {},
        alts=["normality_test"],
        code=N_("""
            import pccpy as pp
            pp.probability_plot(datos)
        """),
    ),
    "r:tol_two": _r(
        "tolerance_interval",
        N_("Intervalo de tolerancia normal bilateral — P(LI ≤ X ≤ LS) ≥ coverage"),
        {"coverage": 0.95, "confidence": 0.95, "sides": "two"},
        alts=["tolerance_interval_summary"],
        code=N_("""
            import pccpy as pp
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95, sides='two')
            print(res.summary())
        """),
    ),
    "r:tol_upper": _r(
        "tolerance_interval",
        N_("Intervalo de tolerancia unilateral superior — P(X ≤ LS) ≥ coverage"),
        {"coverage": 0.95, "confidence": 0.95, "sides": "upper"},
        alts=["tolerance_interval"],
        code=N_("""
            import pccpy as pp
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95, sides='upper')
            print(res.summary())
        """),
    ),
    "r:tol_lower": _r(
        "tolerance_interval",
        N_("Intervalo de tolerancia unilateral inferior — P(X ≥ LI) ≥ coverage"),
        {"coverage": 0.95, "confidence": 0.95, "sides": "lower"},
        alts=["tolerance_interval"],
        code=N_("""
            import pccpy as pp
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95, sides='lower')
            print(res.summary())
        """),
    ),
    "r:tol_np": _r(
        "tolerance_interval",
        N_("Intervalo de tolerancia no paramétrico — estadísticos de orden"),
        {"coverage": 0.95, "confidence": 0.95, "method": "nonparametric"},
        alts=["tolerance_interval"],
        code=N_("""
            import pccpy as pp
            # Requiere n grande (p. ej. ≥ 300 para 95/95 bilateral)
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95,
                                        method='nonparametric')
            print(res.summary())
        """),
    ),
    "r:tol_summary": _r(
        "tolerance_interval_summary",
        N_("Intervalo de tolerancia desde estadísticos resumen (media, σ, n)"),
        {"coverage": 0.95, "confidence": 0.95},
        alts=["tolerance_interval"],
        code=N_("""
            import pccpy as pp
            res = pp.tolerance_interval_summary(mean=media, std=sigma, n=n,
                                                coverage=0.95, confidence=0.95)
            print(res.summary())
        """),
    ),
    "r:run": _r(
        "run_chart",
        N_("Carta de corridas — 4 pruebas de aleatoriedad (p-valores)"),
        {},
        alts=["precontrol"],
        code=N_("""
            import pccpy as pp
            rc = pp.run_chart(datos)
            print(rc.summary())   # p-valores: agrupamiento, mezclas, tendencias, oscilación
            rc.plot()
        """),
    ),
    "r:precontrol": _r(
        "precontrol",
        N_("Pre-control Shainin — semáforo verde / amarillo / rojo basado en tolerancia"),
        {},
        alts=["run_chart"],
        code=N_("""
            import pccpy as pp
            pc = pp.precontrol(datos, lsl=lsl, usl=usl)
            print(pc.summary())
            pc.plot()
        """),
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# Modo CLI
# ══════════════════════════════════════════════════════════════════════════════

def _ask(question: str, options: list[tuple[str, str]]) -> str:
    """Muestra una pregunta con opciones numeradas y devuelve el nodo destino."""
    print()
    pregunta = tr(question)
    print(f"  {pregunta}")
    print()
    for i, (label, _) in enumerate(options, 1):
        etiqueta = tr(label)
        print(f"    [{i}] {etiqueta}")
    print()
    while True:
        raw = input(tr("  Selecciona una opción: ")).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][1]
        print(tr("  ✗ Ingresa un número entre 1 y {n}.").format(n=len(options)))


def _run_cli() -> WizardResult:
    """Recorre el árbol de decisión con preguntas interactivas."""
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print(tr("  ║   pccpy — Asistente de selección de análisis    ║"))
    print("  ╚══════════════════════════════════════════════════╝")

    node = "root"
    while True:
        if node in _RESULTS:
            result = _RESULTS[node]
            print()
            print(result.summary())
            return result
        if node not in _TREE:
            raise RuntimeError(tr("Nodo desconocido en el árbol: {node!r}").format(node=node))
        question, options = _TREE[node]
        node = _ask(question, options)


# ══════════════════════════════════════════════════════════════════════════════
# Modo automático
# ══════════════════════════════════════════════════════════════════════════════

def _run_auto(x: np.ndarray) -> WizardResult:
    """Inspecciona los datos y sugiere el análisis más apropiado."""
    x = np.asarray(x, dtype=float)

    if x.ndim == 2:
        _n_rows, n_cols = x.shape
        if n_cols > 10:
            return _RESULTS["r:t2"]
        if n_cols <= 8:
            return _RESULTS["r:xbar_r"]
        return _RESULTS["r:xbar_s"]

    if x.ndim != 1 or len(x) < 2:
        raise ValueError(tr("'x' debe ser un array 1-D o 2-D con al menos 2 elementos."))

    n = len(x)

    # Detección rápida de tendencia monotónica
    diffs = np.diff(x)
    pct_pos = (diffs > 0).mean()
    if pct_pos > 0.80 or pct_pos < 0.20:
        return _RESULTS["r:run"]

    # Normalidad rápida (z-skewness)
    from scipy import stats as _st
    _, p_norm = _st.normaltest(x)
    is_normal = p_norm > 0.05

    # ¿Suficiente n para capacidad?
    if n >= 30 and is_normal:
        return _RESULTS["r:capability"]

    if n >= 30 and not is_normal:
        return _RESULTS["r:cap_bc"]

    # Pocos datos → carta de control
    return _RESULTS["r:imr"]


# ══════════════════════════════════════════════════════════════════════════════
# Modo widget (Jupyter / ipywidgets)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class WidgetSession:
    """Sesión activa del wizard en modo widget.

    El atributo :attr:`result` es ``None`` hasta que el usuario completa
    la navegación; después contiene el :class:`WizardResult` seleccionado.

    Attributes
    ----------
    result : WizardResult or None
        Recomendación seleccionada por el usuario. ``None`` mientras la
        sesión está abierta.

    Examples
    --------
    >>> session = pp.wizard(mode="widget")   # muestra los botones en Jupyter
    >>> # …el usuario navega y elige…
    >>> print(session.result.snippet())
    """

    result: WizardResult | None = field(default=None)

    def __repr__(self) -> str:
        state = tr("pendiente") if self.result is None else f"result='{self.result.function}'"
        return f"WidgetSession({state})"


def _run_widget() -> WidgetSession:
    """Interfaz gráfica para Jupyter usando ipywidgets."""
    try:
        import ipywidgets as w
        from IPython.display import display
    except ImportError:
        print(tr(
            "ipywidgets no está instalado. Instálalo con:\n"
            "    pip install ipywidgets\n"
            "Cambiando a modo interactivo (CLI)…"
        ))
        # degrada: envuelve el resultado CLI en una WidgetSession
        session = WidgetSession()
        session.result = _run_cli()
        return session

    session = WidgetSession()
    history: list[str] = []
    container = w.VBox(layout=w.Layout(max_width="640px"))

    _PALETTE = {
        "primary": "#2563EB",
        "success_bg": "#F0FDF4",
        "success_border": "#22C55E",
        "back": "#F59E0B",
        "text": "#1E293B",
        "muted": "#64748B",
        "code_bg": "#F8FAFC",
    }

    def _breadcrumb_labels(history: list[str]) -> str:
        parts = []
        for node in history:
            if node in _TREE:
                parts.append(tr(_TREE[node][0])[:28])
        return " › ".join(parts)

    def _render(node: str) -> None:
        children: list[Any] = []

        # Breadcrumb
        if history:
            bc = _breadcrumb_labels(history)
            children.append(w.HTML(
                f"<div style='font-size:11px;color:{_PALETTE['muted']};margin-bottom:6px'>{bc}</div>"
            ))

        # ── Hoja: resultado ────────────────────────────────────────────────
        if node in _RESULTS:
            res = _RESULTS[node]
            session.result = res
            titulo_resultado = tr("✔ Análisis recomendado: <code style='font-size:13px'>{function}</code>").format(
                function=res.function
            )
            justificacion = tr(res.rationale)
            snippet_esc = res.snippet().replace("&", "&amp;").replace("<", "&lt;")
            alts_html = (
                f"<p style='margin:4px 0 0 0;font-size:12px;color:{_PALETTE['muted']}'>"
                + tr("Alternativas: {alternatives}").format(alternatives=", ".join(res.alternatives)) + "</p>"
                if res.alternatives else ""
            )
            children.append(w.HTML(
                f"<div style='border:1px solid {_PALETTE['success_border']};border-radius:8px;"
                f"padding:14px 16px;background:{_PALETTE['success_bg']}'>"
                f"<p style='margin:0 0 4px 0;font-weight:600;color:{_PALETTE['text']}'>"
                f"{titulo_resultado}</p>"
                f"<p style='margin:4px 0;font-size:13px;color:{_PALETTE['text']}'>"
                f"{justificacion}</p>"
                f"<pre style='background:{_PALETTE['code_bg']};border:1px solid #E2E8F0;"
                f"border-radius:6px;padding:10px;font-size:12px;margin:8px 0 0 0;"
                f"overflow-x:auto'>{snippet_esc}</pre>"
                f"{alts_html}"
                f"</div>"
            ))
            if history:
                btn_back = w.Button(
                    description=tr("← Volver"), button_style="",
                    layout=w.Layout(width="110px", margin="8px 0 0 0"),
                    style={"button_color": _PALETTE["back"], "font_weight": "600"},
                )
                def _back_r(_b: Any, _h: list[str] = history) -> None:
                    prev = _h.pop()
                    _render(prev)
                btn_back.on_click(_back_r)
                children.append(btn_back)
            container.children = children
            return

        # ── Nodo: pregunta + botones ───────────────────────────────────────
        question, options = _TREE[node]
        pregunta = tr(question)
        children.append(w.HTML(
            f"<p style='font-weight:600;font-size:14px;color:{_PALETTE['text']};margin:0 0 8px 0'>"
            f"{pregunta}</p>"
        ))
        for idx, (label, dest) in enumerate(options, 1):
            etiqueta = tr(label)
            btn = w.Button(
                description=f"{idx}. {etiqueta}",
                layout=w.Layout(width="100%", min_height="36px", margin="2px 0"),
                style={"button_color": "#EFF6FF", "font_weight": "500"},
            )
            def _click(_b: Any, _dest: str = dest, _node: str = node) -> None:
                history.append(_node)
                _render(_dest)
            btn.on_click(_click)
            children.append(btn)

        if history:
            btn_back = w.Button(
                description=tr("← Volver"), button_style="",
                layout=w.Layout(width="110px", margin="8px 0 0 0"),
                style={"button_color": _PALETTE["back"], "font_weight": "600"},
            )
            def _back_q(_b: Any, _h: list[str] = history) -> None:
                prev = _h.pop()
                _render(prev)
            btn_back.on_click(_back_q)
            children.append(btn_back)

        container.children = children

    _render("root")
    display(container)
    return session


# ══════════════════════════════════════════════════════════════════════════════
# Punto de entrada principal
# ══════════════════════════════════════════════════════════════════════════════

def wizard(
    x: Any = None,
    *,
    mode: str | None = None,
) -> WizardResult | WidgetSession:
    """Asistente interactivo para seleccionar el análisis SPC correcto.

    Parameters
    ----------
    x : array-like, optional
        Datos del proceso. Solo se usan en modo ``'auto'``.
    mode : {'auto', 'cli', 'widget'}, optional
        Modo de operación:

        * ``'auto'``   — analiza *x* y devuelve una recomendación sin interacción.
        * ``'cli'``    — menú de preguntas con opciones numeradas en la terminal.
        * ``'widget'`` — interfaz gráfica para Jupyter (requiere ipywidgets).

        Si se omite y *x* se proporciona, usa ``'auto'``.
        Si se omite y *x* es ``None``, usa ``'cli'``.

    Returns
    -------
    WizardResult
        En modos ``'auto'`` y ``'cli'``.
    WidgetSession
        En modo ``'widget'``. El atributo ``.result`` se llena con el
        :class:`WizardResult` cuando el usuario completa la navegación.
    """
    if mode is None:
        mode = "auto" if x is not None else "cli"

    if mode == "auto":
        if x is None:
            raise ValueError(tr("'x' es obligatorio en mode='auto'."))
        return _run_auto(np.asarray(x, dtype=float))

    if mode == "cli":
        return _run_cli()

    if mode == "widget":
        return _run_widget()

    raise ValueError(tr("mode debe ser 'auto', 'cli' o 'widget'; se recibió {mode!r}.").format(mode=mode))
