# 004 — Fase I con transformación y ajuste robusto

- **Estado:** implementada
- **Identificador:** S004
- **Responsable de aprobarla:** LeoSanta15 (retroactiva, registrada el 2026-10-16)
- **Versión objetivo:** 0.13.0 (transformación) y 0.14.0 (ajuste robusto)

> **Especificación retroactiva.** Se escribió *después* de implementar la funcionalidad, a partir del CHANGELOG, del código y de los tests existentes de 0.13.0; no precedió al código. Documenta qué se prometió y qué test respalda cada requisito, no un diseño previo. El plan que sí existió antes está en `docs/planes/PLAN_FASE1_TRANSFORMACION.md`.

## Problema

Una Fase I sobre datos asimétricos con límites normales da falsas alarmas; transformar los datos antes con todos los puntos hace que un atípico muy grande deforme lambda y se disimule. Se necesitaba reajustar la transformación en cada pasada, con los puntos que se conservan, y que ese ajuste fuera robusto a los atípicos.

## Fuera de alcance

- `phase_one` con cartas de atributos o multivariadas.
- Elegir automáticamente la transformación.
- El orden de las pasadas de la Fase I (no cambia).

## Requisitos

### S004-RF-01 — Reajuste por pasada y transformación congelada

`phase_one(..., transform='boxcox'|'yeo-johnson'|'johnson')` reajusta la transformación en cada pasada con los puntos que se conservan y congela la de la última en `PhaseOneResult.transformation`; `phase2()` la aplica sin reajustarla, junto con `mu` y `sigma` (en la escala transformada).

**Aceptación:**
- **Dado** una Fase I con transformación, **entonces** equivale a transformar antes con la transformación final fija.
- **Dado** `phase2()`, **entonces** no reajusta y es coherente en escala transformada y original.
- **Dado** una `Transformation` ya ajustada, **entonces** no se reajusta.
- **Referencia independiente:** Fase I escrita aparte con `scipy.stats.boxcox` (comprobación de `run_validation()`).
- **Respaldado por:** `tests/test_fase1_transformacion.py` (`test_reajusta_en_cada_pasada_y_congela_la_ultima`, `test_equivale_a_transformar_antes_con_una_transformacion_fija`, `test_fase2_aplica_la_transformacion_congelada_sin_reajustar`, `test_fase2_en_escala_transformada_y_en_original_son_coherentes`)

### S004-RF-02 — Sin `transform` nada cambia

Sin `transform=` el resultado de `phase_one` es el de antes; `transform` solo se admite en cartas de variables (I-MR, Xbar-R, Xbar-S).

**Aceptación:**
- **Dado** una llamada sin `transform`, **entonces** el resultado es idéntico al anterior.
- **Dado** una carta de atributos con `transform`, **entonces** `ValueError`.
- **Respaldado por:** `tests/test_fase1_transformacion.py` (`test_sin_transform_el_resultado_no_cambia`, `test_transform_solo_en_cartas_de_variables`)

### S004-RF-03 — Fallos y avisos

Box-Cox con datos no positivos falla desde la primera pasada; si la transformación no se puede reajustar, la Fase I se detiene con `reason='transform_failed'` y la carta actual; se avisa si lambda cambia más de 0,5 entre la primera y la última pasada.

**Aceptación:**
- **Dado** datos con ceros o negativos y `boxcox`, **entonces** `ValueError` en la primera pasada.
- **Dado** un reajuste imposible, **entonces** `reason='transform_failed'`.
- **Dado** un salto de lambda mayor que 0,5, **entonces** `UserWarning`.
- **Respaldado por:** `tests/test_fase1_transformacion.py` (`test_boxcox_con_datos_no_positivos_falla_desde_la_primera_pasada`, `test_si_no_se_puede_reajustar_se_detiene_con_la_carta_actual`, `test_avisa_si_lambda_cambia_mucho`)

### S004-RF-04 — Historial con la transformación de cada pasada

`PhaseOneIteration.transformation` guarda la de cada pasada y `PhaseOneResult.to_frame()` añade el método y `lambda` (`NaN` en Johnson).

**Aceptación:**
- **Dado** una Fase I con varias pasadas, **entonces** cada fila del historial lleva su transformación.
- **Dado** Johnson, **entonces** `lambda` es `NaN`.
- **Respaldado por:** `tests/test_fase1_transformacion.py` (`test_historial_con_la_transformacion_de_cada_pasada`, `test_johnson_en_el_historial_tiene_lambda_nan`, `test_subgrupos_y_yeo_johnson_con_negativos`)

### S004-RF-05 — Ajuste robusto de la transformación

`fit_transformation(datos, método, robust=True)` ajusta sin los puntos fuera del diagrama de cajas ajustado por asimetría (medcouple; Hubert y Vandervieren, 2008) y aplica la transformación a todos; si el recorte quitaría más del 25 % o dejaría menos de 8 puntos, ajusta con todos. `phase_one` lo usa por defecto (`robust_fit=True`) y no afecta a una transformación ya ajustada.

**Aceptación:**
- **Dado** el medcouple, **entonces** coincide con su definición escrita aparte.
- **Dado** datos limpios, **entonces** `robust=True` no cambia el ajuste; con atípicos sí.
- **Dado** un recorte excesivo, **entonces** se ajusta con todos los datos.
- **Dado** simulaciones con dos puntos ×20, **entonces** la Fase I los encuentra más a menudo y las falsas alarmas de la Fase II se quedan cerca del nominal.
- **Referencia independiente:** definición del medcouple con bucles y simulación con semilla fija.
- **Respaldado por:** `tests/test_ajuste_robusto.py` (`test_medcouple_coincide_con_la_definicion`, `test_robust_no_cambia_el_ajuste_con_datos_limpios_y_si_con_atipicos`, `test_si_el_recorte_quitaria_demasiado_se_ajusta_con_todos`, `test_simulacion_el_ajuste_robusto_recupera_los_puntos_contaminados`, `test_la_tasa_de_falsas_alarmas_de_la_fase_ii_sigue_cerca_de_la_nominal`, `test_robust_fit_no_afecta_a_una_transformacion_ya_ajustada`)

### S004-RF-06 — Falsas alarmas de la Fase II

Con datos lognormales, la Fase II tras una Fase I con transformación da menos falsas alarmas que sin transformar.

**Aceptación:**
- **Dado** lognormal bajo control, **entonces** la tasa de falsas alarmas con transformación queda por debajo de la de la carta normal (0,2 % frente a 5,0 % en la medición documentada).
- **Respaldado por:** `tests/test_fase1_transformacion.py` (`test_simulacion_falsas_alarmas_de_fase2_con_datos_lognormales`)

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Datos con ceros o negativos | Box-Cox falla desde la primera pasada; Yeo-Johnson y Johnson aceptan negativos |
| Recorte robusto excesivo | Más del 25 % o menos de 8 puntos: se ajusta con todos |
| Johnson | `lambda` es `NaN` en el historial |
| Subgrupos | I-MR, Xbar-R y Xbar-S con subgrupos funcionan igual |

## Resultados existentes que cambian

**0.14.0:** `phase_one(..., transform=…)` pasó a usar el ajuste robusto por defecto (`robust_fit=True`), de modo que la lambda y los puntos encontrados cambian respecto a 0.13.0 con atípicos grandes (se listó en «Cambios que alteran resultados»; `robust_fit=False` recupera el comportamiento anterior).

## No verificable sin la fuente

No se contrastó con Minitab: el ajuste robusto es una elección propia, respaldada por Hubert y Vandervieren (2008) y por simulación. Los porcentajes de simulación del CHANGELOG son los medidos con semilla fija, no una garantía general.

## Preguntas abiertas

Ninguna.
