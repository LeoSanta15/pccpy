# 017 — Z1.9: planes de muestreo por variables con las tablas de la norma

- **Estado:** borrador
- **Identificador:** S017
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** por decidir (cambia resultados existentes: los planes de la tabla incluida, que no reproduce la norma)

## Problema

`acceptance_sampling_variables` implementa ANSI/ASQ Z1.9 solo de forma aproximada, y la propia función avisa de ello: *«La tabla Z1.9
incluida es una aproximación que no reproduce la norma (los planes que da pueden aceptar casi cualquier lote)»*. Lo que hay hoy:

- **Tabla de planes incorrecta.** `_Z19_TABLE` tiene solo 6 AQL (0,10 a 4,0 %) y las letras B a K, con pares `(n, k)` «simplificados» que no son los de
  la tabla B-1 de la norma.
- **Letra de código ajena.** Usa la tabla I de **Z1.4** (`_letra_codigo`) y desplaza la letra ±2 para los niveles 1 y 3. Z1.9 tiene su propia tabla de
  letras de código por tamaño de lote y nivel de inspección (tabla A-2), distinta de la de Z1.4.
- **Sin las variantes de la norma:** variabilidad conocida, método del rango, Forma 2 (estimar el porcentaje no conforme del lote y compararlo con
  un máximo `M`, que la norma exige con doble especificación y un solo AQL), inspección rigurosa y reducida.
- **Curva OC aproximada.** `_pa_variables` usa una aproximación normal (Montgomery) para el caso unilateral con σ desconocida; el caso exacto es la
  distribución t no central.
- **Sin guarda del 100 %:** igual que tenía Z1.4 (BUG-25), una muestra mayor o igual que el lote debe inspeccionarse al 100 %.

La persona responsable ya aportó capturas de las tablas de Z1.4; para Z1.9 las tablas **no están disponibles todavía** (la deuda técnica de `CLAUDE.md`
nombra la A-2 y la B-1). Esta especificación fija qué se hará y qué hace falta para hacerlo; **no se puede aprobar ni implementar sin las tablas**.

## Fuera de alcance

- Afirmar equivalencia con Minitab o con software de la norma: no se midió.
- Inventar o reconstruir de memoria las tablas de la norma: solo se transcriben de capturas aportadas y se revisan celda a celda.
- Z1.4 (especificación 016, ya implementada).

## Requisitos

Los requisitos dependen de las tablas que se aporten (ver «Preguntas abiertas»). Los marcados con (A) necesitan la tabla A-2 y la B-1, que son las
mínimas; el resto, las tablas adicionales que se indiquen.

### S017-RF-01 (A) — Letra de código propia de Z1.9

La letra de código sale de la tabla A-2 de Z1.9 (tamaño de lote × nivel de inspección: especiales S3 y S4, y generales I, II y III), no de la tabla I de
Z1.4. Se eliminan el desplazamiento ±2 y la dependencia de `_letra_codigo` de Z1.4.

**Aceptación:**
- **Dado** cada tramo de lote y nivel **entonces** la letra coincide con la tabla A-2 de la captura (tanto los extremos de cada tramo como el interior).
- **Dado** un nivel inexistente **entonces** `ValueError` en español.
- **Referencia independiente:** la tabla A-2 de la captura, transcrita en un test aparte del código y revisada por la persona responsable.

### S017-RF-02 (A) — Planes `(n, k)` de la tabla B-1 (inspección normal, σ desconocida, método de la desviación estándar, Forma 1)

`acceptance_sampling_variables` devuelve, para cada letra y AQL de la tabla B-1, el tamaño de muestra `n` y el factor `k` de la norma, resolviendo las flechas
como en la norma, y deja de avisar de «aproximación» cuando usa la tabla de la norma.

**Aceptación:**
- **Dado** cada celda (letra × AQL) de la tabla B-1 **entonces** `(n, k)` coincide con la captura; los AQL aceptados son los de la tabla (hoy solo 6 de ellos).
- **Dado** `n=` y `k=` explícitos **entonces** el plan se usa tal cual (plan a medida), sin cambios.
- **Dado** el plan de la tabla **entonces** no se emite el `UserWarning` de «aproximación».
- **Referencia independiente:** la tabla B-1 de la captura.

### S017-RF-03 (A) — Criterio de aceptación de la Forma 1

`SamplingPlanVariables.evaluate` acepta con especificación unilateral si `Q = (U − x̄)/s ≥ k` (o `(x̄ − L)/s ≥ k`) y mantiene los resultados actuales
para planes a medida.

**Aceptación:** `evaluate` con datos construidos a mano coincide con la fórmula de la norma (cálculo aparte).

### S017-RF-04 — Guarda del 100 % de inspección

Si el `n` de la tabla es igual o mayor que `N`, el plan lleva `n = N` y un `UserWarning` en español (como Z1.4, S016-RF-04).

**Aceptación:** `N` pequeño con un `n` de la tabla ≥ `N` devuelve `n = N` con aviso; con planes que caben, no cambia nada.

### S017-RF-05 — Curva OC exacta (t no central)

`SamplingPlanVariables.pa(p)` para el caso unilateral con σ desconocida usa la distribución t no central en lugar de la aproximación normal.

**Aceptación:**
- **Dado** un plan `(n, k)` y una fracción no conforme `p` **entonces** `pa(p)` coincide con una simulación de 20 semillas × 20 000 lotes (tolerancia 0,005) y con
  `scipy.stats.nct` calculado aparte.
- **Referencia independiente:** `scipy.stats.nct` y Monte Carlo. Cambia los valores de `pa`, `alpha`, `ltpd` y `oc_curve` de los planes por variables (ver
  «Resultados existentes que cambian»).

### S017-RF-06 (con tablas adicionales) — Forma 2, doble especificación

Con doble especificación y un solo AQL la norma exige la Forma 2: estimar el porcentaje no conforme del lote (superior e inferior) y compararlo con un máximo
`M`. La estimación sale de `Q` y `n` por la distribución beta (fórmula de la norma, comprobable con `scipy.stats.beta`); `M` sale de la tabla de la norma.

**Aceptación:** pendiente de las tablas de `M` (ver preguntas abiertas).

### S017-RF-07 (con tablas adicionales) — Inspección rigurosa y reducida

Parámetro de severidad (`normal`, `tightened`, `reduced`) con las tablas correspondientes.

**Aceptación:** pendiente de las tablas (ver preguntas abiertas).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| AQL que no está en la tabla | El más cercano, como hoy (o `ValueError`: ver pregunta 6) |
| Celda de la tabla con flecha | Se resuelve como indica la norma (se anota la regla en el plan) |
| `n` de la tabla ≥ `N` | Inspección al 100 % con aviso (RF-04) |
| `spec_type="two"` sin Forma 2 | Aviso o `ValueError` según la decisión de la pregunta 2 |
| `n=` sin `k=` (o al revés) | `ValueError` en español |
| `inspection_level` inexistente | `ValueError` en español |

## Resultados existentes que cambian

Cambian **todos los planes de `acceptance_sampling_variables` que salen de la tabla** (no los que se dan con `n=` y `k=`): hoy son aproximados y no reproducen
la norma, de modo que `n`, `k`, `alpha` y `ltpd` serán distintos. Con RF-05 cambian además `pa`, `alpha` y `ltpd` de todos los planes por variables
(unilaterales). Se listan en «Cambios que alteran resultados» del CHANGELOG, con el valor anterior y el nuevo. Versión menor (cambia resultados), salvo decisión
contraria de la persona responsable.

## No verificable sin la fuente

- **Todo.** Sin las tablas de la norma no hay referencia independiente para `(n, k)`, las letras de código ni `M`. Las tablas se transcribirán de capturas (como en
  Z1.4), con el riesgo de leer mal una celda; la persona responsable las revisa celda a celda antes de la Fase 1.
- La numeración de las tablas de Z1.9 que se citan aquí (A-2, B-1, y las de `M`, rango y variabilidad conocida) sale de la deuda técnica de `CLAUDE.md` y de lo
  recordado de la norma, y **debe confirmarla quien tenga la norma**.
- No se midió si Minitab o el software de la norma devuelven los mismos planes.

## Preguntas abiertas

- [NECESITA ACLARACIÓN: **Tablas disponibles.** ¿Qué tablas de Z1.9 se pueden aportar? Como mínimo la A-2 (letras de código) y la B-1 (planes normal y rigurosa,
  σ desconocida, método s). Las demás (reducida; `M` para la Forma 2; método del rango; variabilidad conocida; reglas de cambio) definen qué requisitos
  entran. Sin al menos A-2 y B-1 no se puede aprobar.]
- [NECESITA ACLARACIÓN: **Forma 2 y doble especificación.** ¿Se incluye la Forma 2 (RF-06)? La Forma 1 solo sirve con especificación unilateral o con dos AQL
  separados; para doble especificación con un solo AQL la norma pide la Forma 2. Si no se incluye, ¿`spec_type="two"` con la tabla lanza `ValueError` o se
  avisa y se usa la Forma 1 con los dos lados por separado?]
- [NECESITA ACLARACIÓN: **Inspección rigurosa y reducida.** ¿Se hacen aquí (con sus tablas) o en una especificación aparte, como en Z1.4?]
- [NECESITA ACLARACIÓN: **Curva OC exacta.** ¿RF-05 (t no central) entra en esta especificación (cambia `pa`, `alpha` y `ltpd` de todos los planes por variables) o se
  deja aparte para que el cambio por las tablas sea fácil de revisar?]
- [NECESITA ACLARACIÓN: **Nombres de los niveles.** Z1.9 rotula sus niveles especiales «S3» y «S4» (sin guion, a diferencia de «S-1» a «S-4» de Z1.4). ¿La función
  acepta `"S3"`/`"S4"` o se unifica con el guion? Y los niveles generales siguen siendo 1, 2 y 3.]
- [NECESITA ACLARACIÓN: **AQL fuera de la tabla.** Hoy se usa el AQL más cercano. ¿Se mantiene, o un AQL que no está en la tabla de Z1.9 lanza `ValueError`
  (como las normas piden usar los valores preferidos)?]
- [NECESITA ACLARACIÓN: **Compatibilidad.** `inspection_level` hoy desplaza la letra ±2 (nivel 1 y 3). Al usar la tabla A-2 ese desplazamiento desaparece y los
  resultados con los niveles 1 y 3 cambian. ¿Se acepta sin alias ni periodo de transición (como en 0.15.5 y 0.15.8)?]
