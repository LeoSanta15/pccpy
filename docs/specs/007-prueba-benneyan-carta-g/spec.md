# 007 — Prueba de Benneyan en la carta G

- **Estado:** borrador
- **Identificador:** S007
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.16.0 (nueva opción; ver «Resultados existentes que cambian»)

## Problema

En la carta G el límite inferior es 0, así que la prueba 1 nunca detecta que los eventos se están volviendo **más
frecuentes** (menos casos entre eventos): un conteo 0 es el valor mínimo posible y no cae «bajo» el límite. Benneyan
propone para ello una prueba de rachas: señal cuando hay demasiados puntos consecutivos iguales a 0. Minitab la incluye
en la carta G (según su documentación pública, se marca con «B» y, por defecto, se aplica junto con las pruebas 1 y 2).
`g_chart` hoy no la tiene: el docstring lo dice (`charts/advanced.py`, «No incluye la prueba de Benneyan») y es el primer
pendiente de `CLAUDE.md`.

Ejemplo: con `p = 0,05` y 12 conteos seguidos iguales a 0, ninguna prueba actual avisa, aunque esa racha ocurre por azar
con probabilidad `0,05¹² ≈ 2·10⁻¹⁶`.

## Fuera de alcance

- Carta T (el equivalente de tiempos); Benneyan no define allí una prueba equivalente que se haya podido consultar.
- Cambiar los límites o la línea central de la carta G.
- Afirmar equivalencia con Minitab: solo se compara con lo que su documentación dice (ver «No verificable sin la fuente»).

## Requisitos

### S007-RF-01 — Umbral de la racha

El sistema debe calcular el número `c` de conteos consecutivos iguales a 0 que producen la señal, a partir de la
probabilidad de evento `p` de la etapa y de la tasa de falsas alarmas asociada al parámetro `k` de la carta
(`α = 1 − Φ(k)`, 0,00135 con `k = 3`).

**Aceptación:**
- **Dado** `p = 0,05` y `k = 3` **cuando** se calcula `c` **entonces** `c` es el menor entero con `p^c ≤ α`
  (`ceil(ln α / ln p)`; [NECESITA ACLARACIÓN: ver pregunta 1]).
- **Referencia independiente:** cálculo manual de `p^c` y simulación Monte Carlo (≥ 20 semillas) de la tasa de falsas
  alarmas por punto; tolerancia declarada según el número de simulaciones.

### S007-RF-02 — Opt-in y marca

El sistema debe aplicar la prueba solo si se pide, y marcar los puntos que la incumplen.

**Aceptación:**
- **Dado** `g_chart(x, p=…, benneyan=True)` **cuando** hay `c` o más ceros consecutivos **entonces** quedan marcados
  los puntos de la racha desde el que completa `c` (ver pregunta 2) y `violations()` los lista con una descripción
  propia.
- **Dado** `benneyan=False` (valor por defecto) **entonces** el resultado es idéntico al de 0.15.1.

### S007-RF-03 — Etapas

El sistema debe contar las rachas dentro de cada etapa y con el `p` de esa etapa, sin unir ceros de etapas distintas.

**Aceptación:**
- **Dado** una racha de ceros que cruza el límite entre dos etapas **cuando** se aplica la prueba **entonces** cada etapa
  cuenta solo sus propios ceros.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Ningún cero en los datos | Sin señal; no es un error |
| Todos los conteos 0 y `p` dado | Señal en cada punto desde el `c`-ésimo; sin `p` ya lanza el error actual |
| `p` extremo (0,999 o 1e-9) | `c` finito y ≥ 1; sin desbordes |
| Valores NaN/inf | Los rechaza `as_1d` como hoy |
| Serie más corta que `c` | Sin señal |
| `benneyan=True` con `tests=()` | La prueba se aplica igualmente (es una opción propia) [pregunta 3] |

## Resultados existentes que cambian

Ninguno: opt-in con `benneyan=False` por defecto. [NECESITA ACLARACIÓN: ver pregunta 4 — Minitab la activa por defecto;
activarla aquí cambiaría resultados y exigiría versión menor con aviso.]

## No verificable sin la fuente

No pude abrir las páginas de Minitab (`support.minitab.com` bloqueado desde este entorno) ni el artículo de Benneyan
(2001). Lo único contrastado, por una búsqueda web: Minitab dice que la prueba falla con demasiados puntos consecutivos
iguales a 0, que los marca con «B», que el número de puntos depende de la tasa de falsas alarmas y de la probabilidad del
evento, y que redondea hacia arriba. **La fórmula exacta de `c` no está confirmada**; la de RF-01 es una hipótesis.

## Preguntas abiertas

- [NECESITA ACLARACIÓN: 1. Fórmula de `c`. Hipótesis: `c = ceil(ln α / ln p)` con `α = 1 − Φ(k)`. ¿Puede consultar la
  página «Methods and formulas for G Chart» de su Minitab o el artículo de Benneyan y confirmarla o corregirla? Si no, se
  documenta como «definición propia de pccpy, no verificada contra Minitab».]
- [NECESITA ACLARACIÓN: 2. ¿Se marca solo el punto que completa la racha (y los siguientes ceros) o todos los de la
  racha? Propuesta: desde el `c`-ésimo cero consecutivo en adelante.]
- [NECESITA ACLARACIÓN: 3. API: `benneyan: bool = False` frente a incluirla en `tests=` con un valor propio (hoy las
  claves de `violations` son enteros 1–8). Propuesta: parámetro `benneyan` y clave de violación `"B"`.]
- [NECESITA ACLARACIÓN: 4. ¿Opt-in (0.16.0 sin cambio de resultados) o activada por defecto como Minitab (cambia
  resultados de `g_chart`)? Propuesta: opt-in, conforme al principio 3 de la constitución.]
