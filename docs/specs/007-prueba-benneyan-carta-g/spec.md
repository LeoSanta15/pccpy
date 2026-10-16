# 007 — Prueba de Benneyan en la carta G

- **Estado:** aprobada
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
  (`ceil(ln α / ln p)`; definición propia de pccpy, ver «No verificable sin la fuente»).
- **Referencia independiente:** cálculo manual de `p^c` y simulación Monte Carlo (≥ 20 semillas) de la tasa de falsas
  alarmas por punto; tolerancia declarada según el número de simulaciones.

### S007-RF-02 — Opt-in y marca

El sistema debe aplicar la prueba solo si se pide, y marcar los puntos que la incumplen.

**Aceptación:**
- **Dado** `g_chart(x, p=…, benneyan=True)` **cuando** hay `c` o más ceros consecutivos **entonces** quedan marcados,
  por defecto, el `c`-ésimo cero de la racha y los siguientes (`benneyan_marks="from_c"`), y `violations()` los lista con
  la clave `"B"` y una descripción propia.
- **Dado** `benneyan_marks="run"` **entonces** se marcan todos los ceros de la racha que alcanza `c`, incluidos los
  anteriores al `c`-ésimo. Cualquier otro valor lanza `ValueError`.
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
| `benneyan=True` con `tests=()` | La prueba se aplica igualmente (es una opción propia) |

## Resultados existentes que cambian

Ninguno: opt-in con `benneyan=False` por defecto (decisión de la persona responsable; Minitab la activa por defecto, pccpy
no, para no cambiar resultados existentes). Se anotará en el README, en «Notas sobre diferencias posibles con Minitab».

## No verificable sin la fuente

No pude abrir las páginas de Minitab (`support.minitab.com` bloqueado desde este entorno) ni el artículo de Benneyan
(2001). Lo único contrastado, por una búsqueda web: Minitab dice que la prueba falla con demasiados puntos consecutivos
iguales a 0, que los marca con «B», que el número de puntos depende de la tasa de falsas alarmas y de la probabilidad del
evento, y que redondea hacia arriba. **La fórmula exacta de `c` no está confirmada** y la persona responsable indicó que no se puede consultar: la de RF-01
es una definición propia de pccpy (`p^c ≤ α` con `α = 1 − Φ(k)`), no verificada contra Minitab, y así debe decirlo el
docstring. No se afirma equivalencia con Minitab.

## Decisiones de la persona responsable

1. **Fórmula de `c`:** no hay fuente que consultar; se usa la hipótesis `c = ceil(ln α / ln p)` y se declara como
   definición propia, sin afirmar equivalencia con Minitab.
2. **Qué se marca:** por defecto, desde el `c`-ésimo cero consecutivo en adelante (`benneyan_marks="from_c"`); parámetro
   opcional `benneyan_marks="run"` para marcar toda la racha. Descartado: fijar un único criterio sin opción.
3. **API:** parámetro `benneyan` (no entra en `tests=`) y clave de violación `"B"`.
4. **Opt-in:** `benneyan=False` por defecto. Descartado: activarla por defecto como Minitab (cambiaría resultados).

## Preguntas abiertas

Ninguna.
