# 006 — Correcciones de la auditoría estadística de 0.13.1

- **Estado:** implementada
- **Identificador:** S006
- **Responsable de aprobarla:** LeoSanta15 (retroactiva, registrada el 2026-10-16)
- **Versión objetivo:** 0.14.0 (cambia resultados existentes)

> **Especificación retroactiva.** Se escribió *después* de implementar la funcionalidad, a partir del CHANGELOG, del código y de los tests existentes de 0.14.0; no precedió al código. Documenta qué se prometió y qué test respalda cada requisito, no un diseño previo. El plan que sí existió antes está en `docs/planes/ (la auditoría de 0.13.1 no tuvo plan propio; su lista de hallazgos está en el CHANGELOG de 0.14.0)`.

## Problema

Una auditoría de 0.13.1 encontró resultados numéricos incorrectos o poco defendibles en la tolerancia no paramétrica, el Cpm, el Gage R&R, la sigma con subgrupos desiguales, las pruebas del panel MR, los huecos en I-MR y las cartas EWMA/CUSUM. Cada hallazgo se fijó con un test que antes fallaba.

## Fuera de alcance

- La tolerancia no paramétrica unilateral (spec 001).
- Diferencias con Minitab no verificadas (valores por defecto de EWMA/CUSUM).

## Requisitos

### S006-RF-01 — Tolerancia no paramétrica bilateral

La confianza del intervalo `[X_(r), X_(n+1−r)]` usa la Beta(n−2r+1, 2r) y se elige el **mayor `r`** que alcanza la confianza pedida (el intervalo más estrecho válido).

**Aceptación:**
- **Dado** 95 % / 95 %, **entonces** el tamaño mínimo es n = 93 (antes aceptaba desde 60).
- **Dado** n = 300, **entonces** `r = 4` y confianza 98,4 %.
- **Dado** simulaciones normales, **entonces** la confianza declarada se cumple.
- **Referencia independiente:** cola binomial `P(Bin(n, p) ≤ n − 2r)`.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_tolerancia_no_parametrica_bilateral_exige_n_93_para_95_95`, `test_tolerancia_no_parametrica_bilateral_elige_el_intervalo_mas_estrecho_valido`, `test_tolerancia_no_parametrica_bilateral_la_confianza_declarada_se_cumple_en_simulacion`)

### S006-RF-02 — Cpm con objetivo descentrado

`Cpm = min(T − LEI, LES − T) / (3·s_T)` con `s_T² = Σ(xᵢ − T)²/(n − 1)`, también desde estadísticos de resumen.

**Aceptación:**
- **Dado** LEI = 8, LES = 13, T = 10, **entonces** el valor es el de la fórmula escrita aparte (1,349, no 1,688).
- **Dado** el objetivo centrado, **entonces** usa el factor `n/(n − 1)`.
- **Referencia independiente:** fórmula de Minitab escrita aparte.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_cpm_con_objetivo_descentrado`, `test_cpm_con_objetivo_centrado_usa_el_factor_n_menos_1`, `test_cpm_desde_estadisticos_resumen_coincide_con_el_de_los_datos`)

### S006-RF-03 — Gage R&R: modelo reducido y AIAG

Si la interacción partes×operadores no es significativa (`p > alpha_interaction`, 0,25 por defecto) se quita del modelo y se usa el error agrupado; con `replicates < 2` falla con `ValueError`; el método Xbar-R usa `d2*` (constantes K de AIAG).

**Aceptación:**
- **Dado** una interacción no significativa, **entonces** componentes, F y p salen del ANOVA sin interacción calculado aparte.
- **Dado** `alpha_interaction`, **entonces** el umbral es configurable.
- **Dado** `replicates < 2`, **entonces** `ValueError`.
- **Dado** K1 y K2, **entonces** coinciden con el manual MSA de AIAG (4.ª ed.).
- **Referencia independiente:** ANOVA con NumPy y valores publicados de AIAG.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_gage_rr_con_interaccion_no_significativa_usa_el_modelo_reducido`, `test_gage_rr_umbral_de_interaccion_configurable`, `test_gage_rr_cruzado_exige_al_menos_2_replicas`, `test_constantes_k_de_aiag_con_d2_estrella`, `test_gage_rr_xbar_r_sigue_aiag`)

### S006-RF-04 — Sigma con subgrupos de distinto tamaño

`'rbar'` y `'sbar'` promedian ponderando por varianza inversa (`d2²/d3²` y `c4²/(1 − c4²)`); con tamaño constante no cambia.

**Aceptación:**
- **Dado** subgrupos desiguales, **entonces** coincide con los pesos escritos aparte.
- **Dado** tamaño constante, **entonces** no hay cambio.
- **Referencia independiente:** constantes de Montgomery y pesos escritos aparte.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_sigma_rbar_con_subgrupos_desiguales_pondera_por_varianza_inversa`, `test_sigma_sbar_con_subgrupos_desiguales_pondera_por_varianza_inversa`, `test_sigma_con_tamano_constante_no_cambia`)

### S006-RF-05 — Pruebas del panel MR

El panel MR aplica solo la prueba 1 (los rangos móviles están autocorrelacionados y son asimétricos); R y S mantienen las pruebas 1–4.

**Aceptación:**
- **Dado** 100 puntos estables y `tests="all"`, **entonces** la prueba 2 no salta en el panel MR.
- **Dado** R y S, **entonces** siguen con las pruebas 1–4.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_el_panel_mr_solo_aplica_la_prueba_1`, `test_los_paneles_r_y_s_mantienen_las_pruebas_1_a_4`)

### S006-RF-06 — Huecos en I-MR

Un NaN o inf en `imr_chart` conserva su posición (como hueco): ningún rango móvil ni racha une observaciones no consecutivas; `phase_one` deja los excluidos como huecos.

**Aceptación:**
- **Dado** un NaN en medio, **entonces** el MR vecino es NaN y la serie no se compacta.
- **Dado** una racha, **entonces** no cruza un hueco.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_un_hueco_en_imr_no_une_observaciones_no_consecutivas`, `test_una_racha_no_cruza_un_hueco`)

### S006-RF-07 — EWMA y CUSUM

`sigma_method`, `stages` (el estadístico se reinicia por etapa) y, en CUSUM, `headstart`; con sigma conocida, ARL₀ de la CUSUM bilateral (h = 4, k = 0,5) ≈ 168 y de la EWMA (λ = 0,2, L = 3) ≈ 570.

**Aceptación:**
- **Dado** sigma conocida, **entonces** los ARL₀ medidos por simulación coinciden con esos valores.
- **Dado** `headstart`, **entonces** la CUSUM señala antes un desplazamiento inicial y el parámetro se valida.
- **Dado** `stages` o `sigma_method`, **entonces** los límites se calculan por etapa o con el método pedido.
- **Referencia independiente:** simulación con semilla fija.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_cusum_bilateral_arl0_con_sigma_conocida`, `test_ewma_arl0_con_sigma_conocida`, `test_cusum_con_arranque_rapido_senala_antes_un_desplazamiento_inicial`, `test_cusum_headstart_se_valida`, `test_ewma_y_cusum_con_etapas_calculan_limites_por_etapa`, `test_ewma_y_cusum_aceptan_sigma_method_con_subgrupos`)

### S006-RF-08 — Validaciones y avisos menores

`capability_boxcox` acepta matrices 2-D; `imr_chart` avisa si sigma = 0; las cartas p, np y Laney rechazan tamaños de muestra no enteros (la u sí admite áreas no enteras); el IC de Ppk con Ppk infinito no emite `RuntimeWarning`.

**Aceptación:**
- **Dado** cada caso, **entonces** el comportamiento descrito.
- **Respaldado por:** `tests/test_auditoria_regresion.py` (`test_capability_boxcox_acepta_matrices_2d_como_dice_su_docstring`, `test_imr_avisa_cuando_sigma_es_cero`, `test_cartas_p_np_y_laney_rechazan_tamanos_de_muestra_no_enteros`, `test_u_chart_si_admite_areas_de_oportunidad_no_enteras`, `test_ci_de_ppk_con_ppk_infinito_no_emite_runtimewarning`)

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Subgrupos de tamaño constante | Sin cambio respecto a antes |
| Interacción no significativa | Modelo reducido con error agrupado |
| Ppk infinito | IC `(inf, inf)` sin `RuntimeWarning` |
| Valores no finitos en I-MR | Se conservan como huecos |

## Resultados existentes que cambian

Sí, y es la razón de la versión menor 0.14.0 (se listaron en «Cambios que alteran resultados»): tolerancia bilateral (n mínimo 60 → 93; confianza real 91 % en vez de 98,3 % con n = 80), Cpm (hasta 25 % menos con objetivo descentrado), Gage R&R (modelo reducido y `d2*`; reproducibilidad ≈ 13 % mayor con 3 operadores en Xbar-R), sigma ponderada (varianza 2,3 veces menor con tamaños desiguales), panel MR (solo prueba 1) y huecos en I-MR.

## No verificable sin la fuente

Los valores por defecto de EWMA/CUSUM (método de sigma y reinicio por etapa) **no están verificados contra Minitab**. `d2*` es una aproximación (K1 queda un 0,4 % por encima del valor publicado). El Howe del k bilateral normal es una aproximación documentada.

## Preguntas abiertas

Ninguna.
