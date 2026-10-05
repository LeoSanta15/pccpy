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

from ._i18n import tr

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
            return self._snippet
        args = ", ".join(f"{k}={v!r}" for k, v in self.params.items())
        sep = ", " if args else ""
        return f"import pccpy as pp\nresultado = pp.{self.function}(datos{sep}{args})"

    def summary(self) -> str:
        lines = [
            "═" * 56,
            f"  Análisis recomendado : {self.function}",
            f"  Razón                : {self.rationale}",
        ]
        if self.params:
            lines.append(f"  Parámetros sugeridos : {self.params}")
        if self.alternatives:
            lines.append(f"  Alternativas         : {', '.join(self.alternatives)}")
        lines += [
            "─" * 56,
            "  Código:",
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
        "¿Cuál es tu objetivo principal?",
        [
            ("Monitorear el proceso (cartas de control)",    "cartas"),
            ("Analizar la capacidad del proceso",            "capacidad"),
            ("Sistema de medición (MSA / Gage R&R)",         "msa"),
            ("Muestreo de aceptación",                       "muestreo"),
            ("Análisis exploratorio (normalidad, Pareto)",   "exploratorio"),
            ("Intervalos de tolerancia",                     "tolerancia"),
            ("Carta de corridas o pre-control",              "corridas"),
        ],
    ),

    # ── cartas ────────────────────────────────────────────────────────────────
    "cartas": (
        "¿Qué tipo de datos tienes?",
        [
            ("Mediciones continuas — una por instante (individual)",  "cartas_ind"),
            ("Mediciones continuas — en subgrupos (varias por muestra)", "cartas_sub"),
            ("Fracción defectuosa  (piezas malas / total muestral)",  "cartas_p"),
            ("Número de defectos por unidad inspeccionada",           "cartas_c"),
            ("Varias variables simultáneas (multivariado)",           "cartas_mv"),
            ("Eventos raros (muy poca frecuencia de defectos)",       "cartas_raros"),
            ("Corridas cortas (piezas con distintas especificaciones)","r:zmr"),
        ],
    ),

    "cartas_ind": (
        "¿Necesitas detectar desplazamientos pequeños (< 1.5σ) con mayor rapidez?",
        [
            ("No — sensibilidad estándar Shewhart",                   "r:imr"),
            ("Sí — desplazamientos graduales sostenidos → EWMA",      "r:ewma"),
            ("Sí — cambios abruptos pequeños → CUSUM",                "r:cusum"),
            ("Hay variación entre subgrupos (turno, lote, cavidad) → I-MR-R/S", "r:imr_rs"),
        ],
    ),

    "cartas_sub": (
        "¿Cuál es el tamaño de los subgrupos?",
        [
            ("≤ 8 observaciones por subgrupo  → Xbar-R",    "cartas_sub_r"),
            ("> 8 observaciones por subgrupo  → Xbar-S",    "r:xbar_s"),
        ],
    ),

    "cartas_sub_r": (
        "¿Necesitas detectar desplazamientos pequeños?",
        [
            ("No — sensibilidad estándar → Xbar-R",         "r:xbar_r"),
            ("Sí — alta sensibilidad → EWMA (subgrupos)",   "r:ewma_sub"),
        ],
    ),

    "cartas_p": (
        "¿El tamaño de muestra es constante entre períodos?",
        [
            ("Sí, constante → NP (número de defectuosos)",  "r:np"),
            ("No, variable  → P (fracción defectuosa)",     "cartas_p_var"),
        ],
    ),

    "cartas_p_var": (
        "¿Sospechas sobredispersión (más variabilidad de la esperada)?",
        [
            ("No o no lo sé → P estándar",                  "r:p"),
            ("Sí — corrige sobredispersión → Laney P′",     "r:laney_p"),
        ],
    ),

    "cartas_c": (
        "¿El área / número de unidades inspeccionadas varía entre muestras?",
        [
            ("No — unidades constantes → C (defectos por muestra)", "cartas_c_over"),
            ("Sí — unidades variables  → U (tasa de defectos)",     "cartas_u_over"),
        ],
    ),

    "cartas_c_over": (
        "¿Sospechas sobredispersión?",
        [
            ("No → C estándar",                             "r:c"),
            ("Sí → Laney U′ (versión robusta de U)",        "r:laney_u"),
        ],
    ),

    "cartas_u_over": (
        "¿Sospechas sobredispersión?",
        [
            ("No → U estándar",                             "r:u"),
            ("Sí → Laney U′",                               "r:laney_u"),
        ],
    ),

    "cartas_mv": (
        "¿Necesitas alta sensibilidad a pequeños desplazamientos?",
        [
            ("No — sensibilidad estándar → T² de Hotelling", "r:t2"),
            ("Sí → MEWMA (media) o MCUSUM (suma acumulada)", "cartas_mv_ts"),
        ],
    ),

    "cartas_mv_ts": (
        "¿Cuál prefieres?",
        [
            ("MEWMA — mejor para desplazamientos sostenidos graduales", "r:mewma"),
            ("MCUSUM — mejor para cambios abruptos pequeños",           "r:mcusum"),
        ],
    ),

    "cartas_raros": (
        "¿Qué mides entre eventos?",
        [
            ("Número de piezas o casos entre eventos → G",  "r:g"),
            ("Tiempo entre eventos → T",                    "r:t"),
        ],
    ),

    # ── capacidad ─────────────────────────────────────────────────────────────
    "capacidad": (
        "¿Los datos siguen distribución normal?",
        [
            ("Sí (o no lo sé — puedes verificar con normality_test)", "cap_normal"),
            ("No — se ajusta a otra distribución conocida",           "r:cap_nn"),
            ("No — intentar transformación Box-Cox automática",       "r:cap_bc"),
        ],
    ),

    "cap_normal": (
        "¿Qué tipo de reporte de capacidad necesitas?",
        [
            ("Índices Cp, Cpk, Pp, Ppk, PPM y Z.Bench",            "r:capability"),
            ("Análisis completo en una sola figura (Sixpack)",       "r:sixpack"),
            ("Solo tengo estadísticos resumen (media, σ, n)",        "r:cap_summary"),
        ],
    ),

    # ── MSA ───────────────────────────────────────────────────────────────────
    "msa": (
        "¿Qué tipo de estudio del sistema de medición necesitas?",
        [
            ("Crossed Gage R&R — todos los operadores miden todas las partes", "r:gage_rr"),
            ("Nested Gage R&R — cada operador mide partes distintas",          "r:gage_rr_nested"),
            ("Estudio Tipo 1 — sesgo y repetibilidad de un instrumento",       "r:gage_type1"),
            ("Linealidad y sesgo — sesgo varía con el valor de referencia?",   "r:gage_lin"),
            ("Concordancia por atributos (Kappa de Cohen / Fleiss)",           "r:attr_agreement"),
        ],
    ),

    # ── muestreo de aceptación ────────────────────────────────────────────────
    "muestreo": (
        "¿Cómo se mide la característica de calidad?",
        [
            ("Por atributos (conforme / no conforme) → norma Z1.4",  "r:z14"),
            ("Por variables (medición continua)      → norma Z1.9",  "r:z19"),
            ("Minimizar inspección total (Dodge-Romig)",              "muestreo_dr"),
        ],
    ),

    "muestreo_dr": (
        "¿Qué restricción defines para el plan Dodge-Romig?",
        [
            ("LTPD fijo — proteger contra calidad inaceptable",      "r:dr_ltpd"),
            ("AOQL fijo — limitar la calidad saliente promedio",      "r:dr_aoql"),
        ],
    ),

    # ── exploratorio ──────────────────────────────────────────────────────────
    "exploratorio": (
        "¿Qué análisis exploratorio necesitas?",
        [
            ("Prueba de normalidad (Anderson-Darling, Shapiro-Wilk)",   "r:normality"),
            ("Diagrama de Pareto (frecuencia de categorías o defectos)", "r:pareto"),
            ("Gráfico de probabilidad normal",                           "r:prob_plot"),
        ],
    ),

    # ── intervalos de tolerancia ──────────────────────────────────────────────
    "tolerancia": (
        "¿Dispones de los datos individuales o solo de estadísticos resumen?",
        [
            ("Tengo los datos individuales",           "tol_datos"),
            ("Solo tengo media, desviación típica y n", "r:tol_summary"),
        ],
    ),

    "tol_datos": (
        "¿Los datos siguen distribución normal?",
        [
            ("Sí — intervalo normal (factor k de Wald-Wolfowitz)",  "tol_lados"),
            ("No — intervalo no paramétrico (estadísticos de orden)", "r:tol_np"),
        ],
    ),

    "tol_lados": (
        "¿Qué tipo de límite necesitas?",
        [
            ("Bilateral  — límite inferior y superior", "r:tol_two"),
            ("Unilateral superior — solo cota máxima",  "r:tol_upper"),
            ("Unilateral inferior — solo cota mínima",  "r:tol_lower"),
        ],
    ),

    # ── corridas / pre-control ─────────────────────────────────────────────────
    "corridas": (
        "¿Qué análisis necesitas?",
        [
            ("Carta de corridas — detectar patrones no aleatorios (p-valores)", "r:run"),
            ("Pre-control (Shainin) — semáforo verde / amarillo / rojo",        "r:precontrol"),
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
        _snippet=textwrap.dedent(code).strip() if code else "",
    )


_RESULTS: dict[str, WizardResult] = {
    "r:imr": _r(
        "imr_chart",
        "Datos continuos individuales — carta I-MR estándar Shewhart",
        {"tests": (1, 2, 3, 4, 5, 6, 7, 8)},
        alts=["ewma_chart", "cusum_chart"],
        code="""
            import pccpy as pp
            carta = pp.imr_chart(datos, tests=(1, 2, 3, 4, 5, 6, 7, 8))
            print(carta.summary())
            carta.plot()
        """,
    ),
    "r:ewma": _r(
        "ewma_chart",
        "Alta sensibilidad a desplazamientos sostenidos (λ=0.2 recomendado)",
        {"weight": 0.2, "k": 3.0},
        alts=["imr_chart", "cusum_chart"],
        code="""
            import pccpy as pp
            carta = pp.ewma_chart(datos, weight=0.2, k=3.0)
            carta.plot()
        """,
    ),
    "r:cusum": _r(
        "cusum_chart",
        "Alta sensibilidad a cambios abruptos pequeños (H=4, K=0.5)",
        {"h": 4.0, "k": 0.5},
        alts=["imr_chart", "ewma_chart"],
        code="""
            import pccpy as pp
            carta = pp.cusum_chart(datos, h=4.0, k=0.5)
            carta.plot()
        """,
    ),
    "r:imr_rs": _r(
        "imr_rs_chart",
        "Variación entre y dentro de subgrupos — descompone ambas fuentes",
        {},
        alts=["imr_chart"],
        code="""
            import pccpy as pp
            # datos: matriz 2-D (n_subgrupos × tamaño_subgrupo)
            carta = pp.imr_rs_chart(datos)
            carta.plot()
        """,
    ),
    "r:xbar_r": _r(
        "xbar_r_chart",
        "Datos en subgrupos pequeños (n ≤ 8) — carta Xbar-R",
        {"tests": (1, 2, 3, 4, 5, 6, 7, 8)},
        alts=["xbar_s_chart", "ewma_chart"],
        code="""
            import pccpy as pp
            carta = pp.xbar_r_chart(datos, tests=(1, 2, 3, 4, 5, 6, 7, 8))
            carta.plot()
        """,
    ),
    "r:xbar_s": _r(
        "xbar_s_chart",
        "Datos en subgrupos grandes (n > 8) — carta Xbar-S",
        {"tests": (1, 2, 3, 4, 5, 6, 7, 8)},
        alts=["xbar_r_chart"],
        code="""
            import pccpy as pp
            carta = pp.xbar_s_chart(datos, tests=(1, 2, 3, 4, 5, 6, 7, 8))
            carta.plot()
        """,
    ),
    "r:ewma_sub": _r(
        "ewma_chart",
        "EWMA para datos en subgrupos con alta sensibilidad",
        {"weight": 0.2},
        alts=["xbar_r_chart"],
        code="""
            import pccpy as pp
            carta = pp.ewma_chart(datos, weight=0.2)
            carta.plot()
        """,
    ),
    "r:np": _r(
        "np_chart",
        "Número de defectuosos con tamaño de muestra constante",
        {},
        alts=["p_chart"],
        code="""
            import pccpy as pp
            carta = pp.np_chart(defectuosos, n=tamaño_muestra)
            carta.plot()
        """,
    ),
    "r:p": _r(
        "p_chart",
        "Fracción defectuosa con tamaño de muestra variable",
        {},
        alts=["laney_p_chart", "np_chart"],
        code="""
            import pccpy as pp
            carta = pp.p_chart(defectuosos, n=tamaños)
            carta.plot()
        """,
    ),
    "r:laney_p": _r(
        "laney_p_chart",
        "Fracción defectuosa con corrección de sobredispersión (Laney P′)",
        {},
        alts=["p_chart"],
        code="""
            import pccpy as pp
            carta = pp.laney_p_chart(defectuosos, n=tamaños)
            carta.plot()
        """,
    ),
    "r:c": _r(
        "c_chart",
        "Número de defectos con unidades de inspección constantes",
        {},
        alts=["u_chart"],
        code="""
            import pccpy as pp
            carta = pp.c_chart(defectos)
            carta.plot()
        """,
    ),
    "r:u": _r(
        "u_chart",
        "Tasa de defectos por unidad con tamaño de muestra variable",
        {},
        alts=["laney_u_chart", "c_chart"],
        code="""
            import pccpy as pp
            carta = pp.u_chart(defectos, n=unidades)
            carta.plot()
        """,
    ),
    "r:laney_u": _r(
        "laney_u_chart",
        "Tasa de defectos con corrección de sobredispersión (Laney U′)",
        {},
        alts=["u_chart"],
        code="""
            import pccpy as pp
            carta = pp.laney_u_chart(defectos, n=unidades)
            carta.plot()
        """,
    ),
    "r:t2": _r(
        "t2_chart",
        "T² de Hotelling — monitoreo multivariado estándar",
        {},
        alts=["mewma_chart", "mcusum_chart"],
        code="""
            import pccpy as pp
            # datos: matriz 2-D (n_observaciones × n_variables)
            carta = pp.t2_chart(datos)
            carta.plot()
        """,
    ),
    "r:mewma": _r(
        "mewma_chart",
        "MEWMA — sensibilidad alta a desplazamientos multivariados sostenidos",
        {"weight": 0.1, "arl": 200},
        alts=["t2_chart", "mcusum_chart"],
        code="""
            import pccpy as pp
            carta = pp.mewma_chart(datos, weight=0.1, arl=200)
            carta.plot()
        """,
    ),
    "r:mcusum": _r(
        "mcusum_chart",
        "MCUSUM — sensibilidad alta a cambios abruptos multivariados",
        {"k": 0.5, "arl": 200},
        alts=["t2_chart", "mewma_chart"],
        code="""
            import pccpy as pp
            carta = pp.mcusum_chart(datos, k=0.5, arl=200)
            carta.plot()
        """,
    ),
    "r:g": _r(
        "g_chart",
        "Eventos raros — número de unidades entre eventos (distribución geométrica)",
        {},
        alts=["t_chart"],
        code="""
            import pccpy as pp
            carta = pp.g_chart(entre_eventos)
            carta.plot()
        """,
    ),
    "r:t": _r(
        "t_chart",
        "Eventos raros — tiempo entre eventos (Weibull o exponencial)",
        {},
        alts=["g_chart"],
        code="""
            import pccpy as pp
            carta = pp.t_chart(tiempos)   # dist='weibull' por defecto
            carta.plot()
        """,
    ),
    "r:zmr": _r(
        "zmr_chart",
        "Corridas cortas — estandariza cada parte con sus propios parámetros",
        {},
        alts=["imr_chart"],
        code="""
            import pccpy as pp
            carta = pp.zmr_chart(medidas, partes)
            carta.plot()
        """,
    ),
    "r:capability": _r(
        "capability_analysis",
        "Capacidad normal — Cp, Cpk, Pp, Ppk, PPM, Z.Bench",
        {},
        alts=["capability_sixpack", "capability_nonnormal"],
        code="""
            import pccpy as pp
            res = pp.capability_analysis(datos, lsl=lsl, usl=usl)
            print(res.summary())
            res.plot()
        """,
    ),
    "r:sixpack": _r(
        "capability_sixpack",
        "Capability Sixpack — 6 vistas en una figura (igual que Minitab)",
        {},
        alts=["capability_analysis"],
        code="""
            import pccpy as pp
            import matplotlib.pyplot as plt
            fig, res, carta = pp.capability_sixpack(datos, lsl=lsl, usl=usl)
            plt.show()
        """,
    ),
    "r:cap_summary": _r(
        "capability_analysis_summary",
        "Capacidad desde estadísticos resumen (media, σ, n)",
        {},
        alts=["capability_analysis"],
        code="""
            import pccpy as pp
            res = pp.capability_analysis_summary(
                mean=media, std_overall=sigma, n=n,
                lsl=lsl, usl=usl,
            )
            print(res.summary())
        """,
    ),
    "r:cap_nn": _r(
        "capability_nonnormal",
        "Capacidad no normal — ajuste por máxima verosimilitud a distribución alternativa",
        {"distribution": "weibull"},
        alts=["capability_boxcox"],
        code="""
            import pccpy as pp
            # distribution: 'weibull', 'lognormal', 'gamma', 'loglogistic', ...
            res = pp.capability_nonnormal(datos, lsl=lsl, usl=usl,
                                          distribution='weibull')
            print(res.summary())
        """,
    ),
    "r:cap_bc": _r(
        "capability_boxcox",
        "Transformación Box-Cox automática para normalizar los datos",
        {},
        alts=["capability_nonnormal"],
        code="""
            import pccpy as pp
            res = pp.capability_boxcox(datos, lsl=lsl, usl=usl)
            print(res.summary())   # incluye lambda estimada
        """,
    ),
    "r:gage_rr": _r(
        "gage_rr",
        "Crossed Gage R&R — ANOVA (todos los operadores miden todas las partes)",
        {"method": "anova"},
        alts=["gage_rr_nested"],
        code="""
            import pccpy as pp
            grr = pp.gage_rr(datos, parts=n_partes, operators=n_operadores,
                             replicates=n_replicas, tolerance=tolerancia)
            print(grr.summary())
            grr.plot()
        """,
    ),
    "r:gage_rr_nested": _r(
        "gage_rr_nested",
        "Nested Gage R&R — cada operador mide partes distintas",
        {},
        alts=["gage_rr"],
        code="""
            import pccpy as pp
            grr = pp.gage_rr_nested(datos, parts=n_partes, operators=n_operadores,
                                    replicates=n_replicas)
            print(grr.summary())
        """,
    ),
    "r:gage_type1": _r(
        "gage_type1",
        "Estudio Tipo 1 — sesgo, t-test, Cg y Cgk",
        {},
        alts=["gage_linearity"],
        code="""
            import pccpy as pp
            t1 = pp.gage_type1(mediciones, reference=valor_ref, tolerance=tolerancia)
            print(t1.summary())
        """,
    ),
    "r:gage_lin": _r(
        "gage_linearity",
        "Linealidad y sesgo — detecta si el sesgo cambia con el valor medido",
        {},
        alts=["gage_type1"],
        code="""
            import pccpy as pp
            lin = pp.gage_linearity(mediciones, referencias, tolerance=tolerancia)
            print(lin.summary())
            lin.plot()
        """,
    ),
    "r:attr_agreement": _r(
        "attribute_agreement",
        "Concordancia por atributos — Kappa de Cohen por operador + Kappa de Fleiss",
        {},
        alts=["gage_rr"],
        code="""
            import pccpy as pp
            import pandas as pd
            # df: DataFrame con una columna por operador
            res = pp.attribute_agreement(df, reference=referencia, replicates=n_replicas)
            print(res.summary())
        """,
    ),
    "r:z14": _r(
        "acceptance_sampling_attributes",
        "Muestreo de aceptación por atributos — norma ANSI/ASQ Z1.4",
        {},
        alts=["acceptance_sampling_variables", "dodge_romig"],
        code="""
            import pccpy as pp
            plan = pp.acceptance_sampling_attributes(N=tamaño_lote, aql=aql)
            print(plan.summary())
            plan.plot()
        """,
    ),
    "r:z19": _r(
        "acceptance_sampling_variables",
        "Muestreo de aceptación por variables — norma ANSI/ASQ Z1.9",
        {},
        alts=["acceptance_sampling_attributes"],
        code="""
            import pccpy as pp
            plan = pp.acceptance_sampling_variables(N=tamaño_lote, aql=aql,
                                                    spec_type='one')
            muestra = ...   # array con las mediciones
            dec = plan.evaluate(muestra, usl=usl)
            print(dec)      # {'xbar': ..., 's': ..., 'accept': True/False}
        """,
    ),
    "r:dr_ltpd": _r(
        "dodge_romig",
        "Dodge-Romig LTPD — minimiza ATI con tolerancia a calidad mínima aceptable",
        {},
        alts=["acceptance_sampling_attributes"],
        code="""
            import pccpy as pp
            plan = pp.dodge_romig(N=tamaño_lote, ltpd=ltpd, process_avg=p_promedio)
            print(plan.summary())
        """,
    ),
    "r:dr_aoql": _r(
        "dodge_romig",
        "Dodge-Romig AOQL — minimiza ATI con límite de calidad saliente promedio",
        {},
        alts=["acceptance_sampling_attributes"],
        code="""
            import pccpy as pp
            plan = pp.dodge_romig(N=tamaño_lote, aoql=aoql, process_avg=p_promedio)
            print(plan.summary())
        """,
    ),
    "r:normality": _r(
        "normality_test",
        "Prueba de normalidad Anderson-Darling (compatible con Minitab)",
        {"method": "ad"},
        alts=["probability_plot"],
        code="""
            import pccpy as pp
            res = pp.normality_test(datos, method='ad')
            print(res.summary())
            pp.probability_plot(datos)
        """,
    ),
    "r:pareto": _r(
        "pareto",
        "Diagrama de Pareto — ordena categorías por frecuencia acumulada",
        {},
        alts=[],
        code="""
            import pccpy as pp
            tabla = pp.pareto(categorias)
            pp.plot_pareto(tabla)
        """,
    ),
    "r:prob_plot": _r(
        "probability_plot",
        "Gráfico de probabilidad normal con línea Anderson-Darling",
        {},
        alts=["normality_test"],
        code="""
            import pccpy as pp
            pp.probability_plot(datos)
        """,
    ),
    "r:tol_two": _r(
        "tolerance_interval",
        "Intervalo de tolerancia normal bilateral — P(LI ≤ X ≤ LS) ≥ coverage",
        {"coverage": 0.95, "confidence": 0.95, "sides": "two"},
        alts=["tolerance_interval_summary"],
        code="""
            import pccpy as pp
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95, sides='two')
            print(res.summary())
        """,
    ),
    "r:tol_upper": _r(
        "tolerance_interval",
        "Intervalo de tolerancia unilateral superior — P(X ≤ LS) ≥ coverage",
        {"coverage": 0.95, "confidence": 0.95, "sides": "upper"},
        alts=["tolerance_interval"],
        code="""
            import pccpy as pp
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95, sides='upper')
            print(res.summary())
        """,
    ),
    "r:tol_lower": _r(
        "tolerance_interval",
        "Intervalo de tolerancia unilateral inferior — P(X ≥ LI) ≥ coverage",
        {"coverage": 0.95, "confidence": 0.95, "sides": "lower"},
        alts=["tolerance_interval"],
        code="""
            import pccpy as pp
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95, sides='lower')
            print(res.summary())
        """,
    ),
    "r:tol_np": _r(
        "tolerance_interval",
        "Intervalo de tolerancia no paramétrico — estadísticos de orden",
        {"coverage": 0.95, "confidence": 0.95, "method": "nonparametric"},
        alts=["tolerance_interval"],
        code="""
            import pccpy as pp
            # Requiere n grande (p. ej. ≥ 300 para 95/95 bilateral)
            res = pp.tolerance_interval(datos, coverage=0.95, confidence=0.95,
                                        method='nonparametric')
            print(res.summary())
        """,
    ),
    "r:tol_summary": _r(
        "tolerance_interval_summary",
        "Intervalo de tolerancia desde estadísticos resumen (media, σ, n)",
        {"coverage": 0.95, "confidence": 0.95},
        alts=["tolerance_interval"],
        code="""
            import pccpy as pp
            res = pp.tolerance_interval_summary(mean=media, std=sigma, n=n,
                                                coverage=0.95, confidence=0.95)
            print(res.summary())
        """,
    ),
    "r:run": _r(
        "run_chart",
        "Carta de corridas — 4 pruebas de aleatoriedad (p-valores)",
        {},
        alts=["precontrol"],
        code="""
            import pccpy as pp
            rc = pp.run_chart(datos)
            print(rc.summary())   # p-valores: agrupamiento, mezclas, tendencias, oscilación
            rc.plot()
        """,
    ),
    "r:precontrol": _r(
        "precontrol",
        "Pre-control Shainin — semáforo verde / amarillo / rojo basado en tolerancia",
        {},
        alts=["run_chart"],
        code="""
            import pccpy as pp
            pc = pp.precontrol(datos, lsl=lsl, usl=usl)
            print(pc.summary())
            pc.plot()
        """,
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# Modo CLI
# ══════════════════════════════════════════════════════════════════════════════

def _ask(question: str, options: list[tuple[str, str]]) -> str:
    """Muestra una pregunta con opciones numeradas y devuelve el nodo destino."""
    print()
    print(f"  {question}")
    print()
    for i, (label, _) in enumerate(options, 1):
        print(f"    [{i}] {label}")
    print()
    while True:
        raw = input("  Selecciona una opción: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][1]
        print(f"  ✗ Ingresa un número entre 1 y {len(options)}.")


def _run_cli() -> WizardResult:
    """Recorre el árbol de decisión con preguntas interactivas."""
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║   pccpy — Asistente de selección de análisis    ║")
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
        state = "pendiente" if self.result is None else f"result='{self.result.function}'"
        return f"WidgetSession({state})"


def _run_widget() -> WidgetSession:
    """Interfaz gráfica para Jupyter usando ipywidgets."""
    try:
        import ipywidgets as w
        from IPython.display import display
    except ImportError:
        print(
            "ipywidgets no está instalado. Instálalo con:\n"
            "    pip install ipywidgets\n"
            "Cambiando a modo interactivo (CLI)…"
        )
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
                parts.append(_TREE[node][0][:28])
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
            snippet_esc = res.snippet().replace("&", "&amp;").replace("<", "&lt;")
            alts_html = (
                f"<p style='margin:4px 0 0 0;font-size:12px;color:{_PALETTE['muted']}'>"
                f"Alternativas: {', '.join(res.alternatives)}</p>"
                if res.alternatives else ""
            )
            children.append(w.HTML(
                f"<div style='border:1px solid {_PALETTE['success_border']};border-radius:8px;"
                f"padding:14px 16px;background:{_PALETTE['success_bg']}'>"
                f"<p style='margin:0 0 4px 0;font-weight:600;color:{_PALETTE['text']}'>"
                f"✔ Análisis recomendado: <code style='font-size:13px'>{res.function}</code></p>"
                f"<p style='margin:4px 0;font-size:13px;color:{_PALETTE['text']}'>"
                f"{res.rationale}</p>"
                f"<pre style='background:{_PALETTE['code_bg']};border:1px solid #E2E8F0;"
                f"border-radius:6px;padding:10px;font-size:12px;margin:8px 0 0 0;"
                f"overflow-x:auto'>{snippet_esc}</pre>"
                f"{alts_html}"
                f"</div>"
            ))
            if history:
                btn_back = w.Button(
                    description="← Volver", button_style="",
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
        children.append(w.HTML(
            f"<p style='font-weight:600;font-size:14px;color:{_PALETTE['text']};margin:0 0 8px 0'>"
            f"{question}</p>"
        ))
        for idx, (label, dest) in enumerate(options, 1):
            btn = w.Button(
                description=f"{idx}. {label}",
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
                description="← Volver", button_style="",
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
