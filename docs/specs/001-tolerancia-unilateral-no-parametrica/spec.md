# 001 — Tolerancia no paramétrica unilateral: cota más ajustada

- **Estado:** implementada
- **Identificador:** S001
- **Responsable de aprobarla:** LeoSanta15 (aprobada el 2026-10-15)
- **Versión objetivo:** 0.15.0 (cambia resultados existentes)

## Problema

`tolerance_interval(method="nonparametric", sides="lower"|"upper")` devuelve siempre el estadístico de orden extremo
(`r = 1`, es decir, el mínimo o el máximo de la muestra) mientras ese extremo alcance la confianza pedida. La cota es
**válida** pero la más conservadora posible: la confianza lograda se acerca a 1 en lugar de a la pedida.

Se detectó al corregir la tolerancia bilateral en 0.14.0 (que sí elige el intervalo más estrecho válido) y se dejó fuera
de aquel cambio porque la auditoría no lo incluía.

Ejemplo (cobertura 0,95, confianza 0,95, `n = 300`, cota inferior): la implementación usa `r = 1` con confianza
`1 − 0,95³⁰⁰ = 0,9999998`, mientras que `r = 9` sigue cumpliendo con confianza 0,966 y da una cota notablemente más
alta (menos conservadora) con la garantía pedida.

## Fuera de alcance

- La tolerancia no paramétrica bilateral (ya corregida en 0.14.0).
- El método normal.
- Intervalos de tolerancia no paramétricos con otros esquemas de interpolación entre estadísticos de orden.

## Requisitos

### S001-RF-01 — Elegir el índice más ajustado que cumple la confianza

Con `sides="lower"` o `"upper"`, el índice de orden debe ser el **mayor** `r` tal que
`P(Bin(n, 1 − p) ≥ r) ≥ confianza`; la cota es `X_(r)` (inferior) o `X_(n+1−r)` (superior).

**Aceptación:**
- **Dado** `n = 300`, cobertura 0,95 y confianza 0,95, **cuando** se pide la cota inferior, **entonces** `r = 9`,
  `lower == sort(x)[8]` y `achieved_confidence ≈ 0,96593`.
- **Dado** los mismos datos, **cuando** se pide la cota superior, **entonces** `upper == sort(x)[300 − 9]`.
- **Referencia independiente:** cola binomial `scipy.stats.binom.sf(r − 1, n, 1 − p)`, tolerancia 1e-12.

### S001-RF-02 — La confianza declarada se cumple

La `achieved_confidence` debe coincidir con la probabilidad real de que la cota deje al menos la cobertura pedida.

**Aceptación:**
- **Dado** normales simuladas con semilla fija (≥ 20 000 réplicas), `n = 100`, cobertura 0,9 y confianza 0,9,
  **cuando** se calcula la cota inferior, **entonces** la fracción de réplicas en que la población por encima de la
  cota es ≥ 0,9 queda a ±1 punto de `achieved_confidence`.

### S001-RF-03 — Tamaño mínimo sin cambios

El tamaño mínimo para que exista cota sigue siendo el de `r = 1`.

**Aceptación:**
- **Dado** cobertura 0,95 y confianza 0,95, **cuando** `n = 58`, **entonces** `ValueError`; **cuando** `n = 59`,
  **entonces** se acepta con `r = 1`.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `n` justo en el mínimo | `r = 1`, igual que hoy |
| Muestra con valores repetidos | La cota es el valor del estadístico de orden, sin interpolar |
| Confianza 0,999 o cobertura 0,999 | Mismo criterio; `ValueError` si ni `r = 1` cumple |
| Valores no finitos en la muestra | Igual que hoy (`as_1d` avisa y los descarta) |

## Resultados existentes que cambian

Las cotas unilaterales no paramétricas con `n` por encima del mínimo se desplazan hacia el centro de la muestra y su
`achieved_confidence` baja hacia la pedida. Con `n = 300`, 0,95 / 0,95: de `X_(1)` (confianza 0,9999998) a `X_(9)`
(0,96593). El CHANGELOG lo listará en «Cambios que alteran resultados».

## No verificable sin la fuente

Qué elige Minitab para la cota unilateral no paramétrica (no se pudo consultar). Se aplica el mismo criterio que a la
bilateral: el intervalo más estrecho que cumple la confianza.

## Preguntas abiertas

Ninguna.

**Decisión (LeoSanta15, 2026-10-15):** sin parámetro para conservar el comportamiento anterior; basta con avisar el
cambio en el CHANGELOG, en «Cambios que alteran resultados».
