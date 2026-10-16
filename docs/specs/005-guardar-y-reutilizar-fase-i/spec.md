# 005 — Guardar y reutilizar una Fase I

- **Estado:** implementada
- **Identificador:** S005
- **Responsable de aprobarla:** LeoSanta15 (retroactiva, registrada el 2026-10-16)
- **Versión objetivo:** 0.13.0

> **Especificación retroactiva.** Se escribió *después* de implementar la funcionalidad, a partir del CHANGELOG, del código y de los tests existentes de 0.13.0; no precedió al código. Documenta qué se prometió y qué test respalda cada requisito, no un diseño previo. El plan que sí existió antes está en `docs/planes/PLAN_FASE1_GUARDAR.md`.

## Problema

Quien ya tiene los datos o los límites de una Fase I (de otra sesión o de otro programa) quería pasar a la Fase II sin repetir la Fase I. No había forma de guardar el resultado ni de crear uno desde límites conocidos.

## Fuera de alcance

- Guardar el gráfico de la Fase I.
- Formatos distintos de JSON (no se usa pickle por seguridad).
- Migraciones entre versiones del esquema (solo se rechaza uno más nuevo).

## Requisitos

### S005-RF-01 — Guardar y restaurar una Fase I

`PhaseOneResult.to_dict()` y `from_dict()` guardan y restauran lo que necesita `phase2()` (función de la carta por nombre, argumentos, límites congelados, transformación) junto con el historial y los puntos excluidos.

**Aceptación:**
- **Dado** cualquiera de las siete cartas soportadas, con y sin `transform=`, **entonces** `phase2()` tras guardar y cargar da exactamente la misma carta que el original.
- **Dado** una transformación, **entonces** se restaura con sus parámetros.
- **Referencia independiente:** los mismos límites pasados directamente a la carta (comprobación de `run_validation()`).
- **Respaldado por:** `tests/test_fase1_guardar.py` (`test_la_fase2_tras_guardar_y_cargar_es_identica`, `test_con_transformacion_se_restaura_con_sus_parametros`)

### S005-RF-02 — Formato JSON sin pickle

El diccionario es serializable en JSON (con `NaN` como `null`); `to_json(path=None)` y `from_json(texto_o_ruta)` lo escriben y leen como texto o archivo UTF-8.

**Aceptación:**
- **Dado** un resultado, **cuando** se serializa, **entonces** `json.dumps` funciona y los `NaN` van como `null`.
- **Dado** texto o ruta, **entonces** `from_json` restaura; **dado** JSON inválido, **entonces** error claro.
- **Respaldado por:** `tests/test_fase1_guardar.py` (`test_el_diccionario_es_json_con_nan_como_null`, `test_to_json_y_from_json_con_texto_y_con_archivo`, `test_from_json_con_errores_claros`)

### S005-RF-03 — Validaciones al guardar y al cargar

`to_dict()` rechaza, con un mensaje que dice cuál es, los argumentos que no se pueden guardar y los límites no finitos; `from_dict()` valida el esquema (rechaza uno más nuevo), la carta y que las claves de los límites correspondan a ella.

**Aceptación:**
- **Dado** un argumento no serializable, **entonces** `ValueError` que nombra el argumento.
- **Dado** un esquema más nuevo o una carta desconocida, **entonces** `ValueError`.
- **Respaldado por:** `tests/test_fase1_guardar.py` (`test_argumentos_que_no_se_pueden_guardar_dan_un_error_que_dice_cual`, `test_from_dict_valida_esquema_carta_y_limites`)

### S005-RF-04 — El resultado cargado no tiene gráfico

El `PhaseOneResult` cargado no tiene `chart` (`None`) ni etiquetas; `summary()` funciona y dibujar avisa con un mensaje claro.

**Aceptación:**
- **Dado** un resultado cargado, **entonces** `chart is None`, `summary()` funciona y pedir el gráfico avisa.
- **Respaldado por:** `tests/test_fase1_guardar.py` (`test_el_resultado_cargado_no_tiene_carta_pero_resume_y_avisa_al_dibujar`)

### S005-RF-05 — Crear una Fase I desde límites conocidos

`PhaseOneResult.from_limits(carta, mu=…, sigma=…)` (o `p=`, `c=`, `u=`; con `transform=` una `Transformation` ya ajustada) crea un resultado sin ejecutar `phase_one`, con `reason='external'` y sin historial; valida que los límites correspondan a la carta, sean finitos y `sigma` positiva.

**Aceptación:**
- **Dado** I-MR, **entonces** equivale a `phase_one` con esos mismos límites.
- **Dado** una transformación fija, **entonces** vuelve igual tras ida y vuelta por JSON.
- **Dado** cartas de atributos, **entonces** funciona con `p`, `c` o `u`.
- **Dado** límites inválidos, **entonces** `ValueError`.
- **Respaldado por:** `tests/test_fase1_guardar.py` (`test_from_limits_equivale_a_phase_one_en_i_mr`, `test_from_limits_con_transformacion_fija_y_ida_y_vuelta_json`, `test_from_limits_en_cartas_de_atributos`, `test_from_limits_valida`)

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Límites no finitos | `to_dict()` y `from_limits()` los rechazan |
| Argumento no serializable | Error que dice cuál es |
| Esquema más nuevo | `from_dict()` lo rechaza |
| Carta de atributos | `from_limits` con `p`, `c` o `u` |

## Resultados existentes que cambian

Ninguno: funcionalidad nueva.

## No verificable sin la fuente

No aplica referencia externa: la propiedad que se verifica es que `phase2()` tras cargar da *exactamente* la misma carta, y se contrasta con los mismos límites pasados a mano.

## Preguntas abiertas

Ninguna.
