# 003 — Pruebas formales de atípicos (Grubbs, ESD y Dixon)

- **Estado:** implementada
- **Identificador:** S003
- **Responsable de aprobarla:** LeoSanta15 (retroactiva, registrada el 2026-10-16)
- **Versión objetivo:** 0.13.0 (Grubbs y ESD) y 0.14.0 (Dixon)

> **Especificación retroactiva.** Se escribió *después* de implementar la funcionalidad, a partir del CHANGELOG, del código y de los tests existentes de 0.13.0; no precedió al código. Documenta qué se prometió y qué test respalda cada requisito, no un diseño previo. El plan que sí existió antes está en `docs/planes/PLAN_NO_NORMALIDAD.md`.

## Problema

Decidir si un punto es un atípico a ojo no es defendible en un sistema de calidad. `pccpy` necesitaba pruebas formales con nivel conocido para datos aproximadamente normales, sin que `outlier_test` se convierta en una regla para eliminar datos (la documentación lo advierte).

## Fuera de alcance

- Eliminar o corregir los atípicos encontrados.
- Atípicos en datos que no son aproximadamente normales (solo se avisa).
- La prueba de Dixon para n > 100.

## Requisitos

### S003-RF-01 — Grubbs: valor crítico y nivel

`outlier_test(x, method="grubbs")` contrasta un único atípico con el estadístico G y el valor crítico t de Grubbs, con nivel nominal α.

**Aceptación:**
- **Dado** n y α de la tabla publicada de Grubbs, **entonces** el crítico coincide con la tabla.
- **Dado** normales simuladas, **entonces** marca ≈ α de las muestras.
- **Referencia independiente:** tabla publicada de Grubbs y simulación con semilla fija.
- **Respaldado por:** `tests/test_outlier_test.py` (`test_critico_de_grubbs_coincide_con_la_tabla_publicada`, `test_estadistico_de_grubbs_y_dato_marcado`, `test_grubbs_no_marca_datos_normales_y_su_nivel_es_el_nominal`)

### S003-RF-02 — ESD generalizada (Rosner)

`method="esd"` encuentra hasta `max_outliers` atípicos sin enmascaramiento, con los valores críticos de Rosner (1983).

**Aceptación:**
- **Dado** el ejemplo de Rosner (1983) del manual del NIST, **entonces** encuentra 3 atípicos.
- **Dado** dos atípicos que se enmascaran entre sí para Grubbs, **entonces** la ESD los encuentra.
- **Dado** normales simuladas con 3 atípicos buscados, **entonces** la tasa de falsos positivos queda cerca de α.
- **Referencia independiente:** ejemplo del NIST y simulación.
- **Respaldado por:** `tests/test_outlier_test.py` (`test_esd_reproduce_el_ejemplo_del_nist`, `test_esd_encuentra_dos_atipicos_que_se_enmascaran_para_grubbs`, `test_esd_falsos_positivos_acotados`)

### S003-RF-03 — Pruebas unilaterales

Con `sides="upper"` o `"lower"` se mira un solo lado y el nivel usa `α/n` en lugar de `α/(2n)`.

**Aceptación:**
- **Dado** un atípico en la cola contraria, **cuando** `sides` mira el otro lado, **entonces** no se marca.
- **Referencia independiente:** crítico t con `α/n` calculado aparte.
- **Respaldado por:** `tests/test_outlier_test.py` (`test_unilateral_usa_alpha_sobre_n_y_solo_mira_un_lado`)

### S003-RF-04 — Índices, aviso de normalidad y resumen

Los índices devueltos son los de la entrada original aunque haya valores no finitos; se avisa si los datos restantes no parecen normales (Shapiro-Wilk); `to_frame(stable=)` y `summary()` describen cada paso; los errores de entrada son claros.

**Aceptación:**
- **Dado** datos con NaN, **entonces** los índices apuntan a la entrada original.
- **Dado** datos restantes no normales, **entonces** `UserWarning`.
- **Dado** argumentos inválidos, **entonces** `ValueError` con mensaje en español (y su traducción).
- **Respaldado por:** `tests/test_outlier_test.py` (`test_los_indices_son_los_de_la_entrada_original_con_valores_no_finitos`, `test_aviso_si_los_datos_restantes_no_son_normales`, `test_tabla_resumen_y_traduccion`, `test_errores`)

### S003-RF-05 — Prueba de Dixon con valores críticos calculados

`method="dixon"` (`dixon_ratio="auto"|"r10"|"r11"|"r21"|"r22"`) contrasta un atípico con la razón de Dixon; los valores críticos se **calculan** (cuadratura de Gauss-Legendre de `P(Q > c)` bajo normalidad, invertida con `brentq`) en lugar de tabularse. Admite 3 ≤ n ≤ 100 y avisa con n > 30.

**Aceptación:**
- **Dado** `r10` y 90, 95 y 99 %, **entonces** el crítico bilateral reproduce la tabla de Rorabacher (1991) a menos de 0,006.
- **Dado** cualquier razón, **entonces** el crítico unilateral α = 0,025 deja ≈ 2,5 % en cola en una simulación de Monte Carlo.
- **Dado** `auto`, **entonces** elige `r10` (3–7), `r11` (8–10), `r21` (11–13) o `r22` (14–30).
- **Dado** dos atípicos del mismo lado, **entonces** `r10` se enmascara y `r21` no.
- **Referencia independiente:** tabla de Rorabacher (1991) y Monte Carlo.
- **Respaldado por:** `tests/test_dixon.py` (`test_r10_reproduce_las_tablas_publicadas`, `test_los_criticos_calculados_dejan_la_cola_esperada_en_simulacion`, `test_razon_automatica_segun_n`, `test_dos_atipicos_del_mismo_lado_enmascaran_r10_pero_no_r21`, `test_tasa_de_falsos_positivos_bilateral_no_supera_alfa`)

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Valores no finitos | Se excluyen del análisis y los índices siguen siendo los de la entrada original |
| Datos constantes | Error claro: no hay dispersión que contrastar |
| n menor que el mínimo | `ValueError` (Grubbs n ≥ 3; Dixon 3 ≤ n ≤ 100) |
| Dixon con n > 30 | `UserWarning`: la prueba está pensada para muestras pequeñas |

## Resultados existentes que cambian

Ninguno: funcionalidad nueva (opt-in).

## No verificable sin la fuente

La tabla de Rorabacher (1991) para `r10` se transcribió **sin acceso a la fuente**; la coincidencia de las 24 cifras con el valor calculado a ≤ 0,005, junto con la simulación de Monte Carlo, es lo que la respalda. No se afirma que la tabla de Dixon (1951) coincida. Las razones `r11`, `r21` y `r22` se respaldan solo con simulación.

## Preguntas abiertas

Ninguna.
