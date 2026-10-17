# 014 — Dirección de la tendencia de `diagnose()` en inglés

- **Estado:** borrador
- **Identificador:** S014
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** [NECESITA ACLARACIÓN: 0.15.6 (como la 012, aunque es incompatible) o 0.16.0 (versión menor, como pide CLAUDE.md para un cambio de resultados)]

## Problema

`DiagnoseResult.trend_direction` devuelve `'creciente'` o `'decreciente'` (o `''`): un **valor de código en español** que no depende del idioma
elegido. Es el mismo principio de la spec 012: el código y los datos con clave van en inglés; solo lo que se muestra depende del idioma.
Quien escriba `if d.trend_direction == "creciente"` hoy depende de un literal en español.

## Fuera de alcance

- `issues`, `recommended_snippet` y demás textos que se muestran: siguen traduciéndose por idioma.
- Otros valores de `DiagnoseResult` (`non_normal_reason` ya devuelve `'outliers'`, `'skewed'`, `'shape'`).
- Revisar otros módulos: este cambio es solo `diagnose()`. Si se encuentra otro valor de código en español, se anota aparte.

## Requisitos

### S014-RF-01 — Valores en inglés

`trend_direction` devuelve `'increasing'`, `'decreasing'` o `''`, iguales en cualquier idioma. Sin alias: `'creciente'`/`'decreciente'` dejan de existir
(consistente con la decisión de la spec 012).

**Aceptación:**
- **Dado** datos con tendencia creciente/decreciente **cuando** se llama a `diagnose()` **entonces** `trend_direction` es `'increasing'`/`'decreasing'`
  con el idioma `es` y con `en`.
- **Referencia independiente:** el signo de la pendiente de una recta de mínimos cuadrados (`scipy.stats.linregress`) sobre los datos del test.

### S014-RF-02 — Lo que se muestra sigue traducido

`summary()`, `to_frame()` y el texto «Se detectó tendencia …» muestran «creciente»/«decreciente» en español y «increasing»/«decreasing» en inglés
(`_tendencia()` traduce desde las claves inglesas).

**Aceptación:** el texto de `summary()` en español queda **idéntico** al de `tests/golden/i18n_es.json` (que no se regenera); en inglés se
muestra la traducción. `to_frame(stable=True)` da el valor canónico en inglés.

### S014-RF-03 — Código y documentación

Los literales de `src/`, tests, README, guías y catálogos usan los valores nuevos; una sola lista de equivalencias se escribe en el CHANGELOG para que quien
compare con `'creciente'` sepa qué cambiar.

**Aceptación:** `grep -rn "'creciente'\|\"creciente\"\|'decreciente'\|\"decreciente\"" src tests docs README*.md` solo encuentra la tabla de
traducción de `_tendencia()`, los golden y el CHANGELOG.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Sin tendencia | `trend_direction == ''` y `has_trend == False`, como hoy |
| Datos con n mínimo | Igual que hoy (el umbral de tendencia no cambia) |
| `trend_direction` impreso con `PCCPY_LANG=en` | El valor guardado es `'increasing'`; el texto mostrado también |

## Resultados existentes que cambian

`DiagnoseResult.trend_direction`: de `'creciente'`/`'decreciente'` a `'increasing'`/`'decreasing'`. Es **incompatible** para quien compare con el literal español;
no cambia ningún cálculo.

## No verificable sin la fuente

Nada: la regla de la tendencia (`pct_inc > 0.80` / `< 0.20`) no cambia.

## Preguntas abiertas

- [NECESITA ACLARACIÓN: versión objetivo (0.15.6 o 0.16.0).]
