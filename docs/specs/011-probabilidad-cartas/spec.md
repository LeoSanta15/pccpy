# 011 — Probabilidad de un valor en las cartas de control

- **Estado:** borrador
- **Identificador:** S011
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.5 (método nuevo; no cambia ningún resultado existente; decisión de la persona responsable)

## Problema

La especificación 010 permite preguntar a un resultado de capacidad «¿cuál es la probabilidad de que una pieza quede por debajo
de 47?». Las cartas de control no lo permiten: una carta conoce su línea central, sus límites y su sigma por punto, pero no hay
forma de preguntar «¿cuál es la probabilidad de que la media de un subgrupo de 5 piezas pase de 52?», «¿y de que el rango pase
de 4?» o «¿con qué probabilidad un punto de esta carta P cae fuera de los límites?». Hoy se puede hacer a mano con `scipy.stats`
si el usuario sabe qué distribución sigue cada estadístico (normal, rango de normales, χ², binomial, Poisson) y de dónde
sacar `n`, `μ` y `σ` por punto; con una transformación, además, tiene que transformar el valor.

El ARL (especificación 009) ya contesta una pregunta parecida (cuántos puntos hasta la primera señal), pero no la
probabilidad de un valor cualquiera, y se calcula a partir de parámetros sueltos, no de una carta ya construida.

El estadístico de cada panel tiene una distribución conocida cuando el proceso está en control con los parámetros de la carta:

| Panel | Estadístico graficado | Distribución en control |
|---|---|---|
| I, Xbar | valor o media del subgrupo | normal(`center`, `sigma` del punto) |
| MR | rango móvil de `span` valores | `σ` × rango de `span` normales estándar |
| R | rango del subgrupo de tamaño `n` | `σ` × rango de `n` normales estándar |
| S | desviación estándar del subgrupo | `σ` × √(χ²ₙ₋₁/(n−1)) |
| P, NP | proporción o conteo de defectuosos | binomial(`n`, `p`) |
| C, U | defectos o defectos por unidad | Poisson(`c·n`) |
| EWMA | valor suavizado | normal(`μ`, σ del punto), exacta para cada punto |
| G | cantidad entre eventos `X` = 0, 1, 2… | geométrica: `P(X = k) = p(1−p)ᵏ` con la `p` de la carta |
| T | tiempo entre eventos | Weibull(`forma`, `escala`); con distribución exponencial, `forma` = 1 |

## Fuera de alcance

- CUSUM, MA, Zona, Laney P'/U' y las cartas multivariadas: o no hay una distribución marginal de forma cerrada (CUSUM) o
  son otra especificación (el resto). Se dice así en el error, no se aproxima.
- Probabilidades **fuera de control** (con un desplazamiento, `shift=`): ya las da el ARL (`arl_*`); aquí el proceso es el de la
  carta (decisión de la persona responsable).
- Las pruebas suplementarias (2 a 8): la probabilidad es la de un punto, no la de una racha.
- Intervalos de confianza (el error de haber estimado la media y la sigma): se tratan como conocidas.
- Cambiar resultados existentes ni el cálculo de ninguna carta.

## Requisitos

La carta sabe de qué distribución es cada estadístico (RF-01). Los valores van en las unidades en que se ve el panel (con
`transform=` y `scale="original"`, las originales). Cada valor puede ser un número o un arreglo de una dimensión, como en la 010.

### S011-RF-01 — La carta conserva la distribución del estadístico de cada panel

Cada panel de una carta admitida guarda la información para reconstruir su distribución en control por punto: familia y
parámetros (`n`, `p`, `σ`, `span`…). Es información nueva; los valores, límites, pruebas y demás campos no cambian.

**Aceptación:**
- **Dado** una carta I-MR, Xbar-R, Xbar-S, P, NP, C, U o EWMA **cuando** se construye **entonces** cada panel dice su familia
  (`"normal"`, `"range"`, `"sd"`, `"binomial"`, `"poisson"`) y sus parámetros por punto.
- Los valores, `center`, `ucl`, `lcl`, `sigma` y `violations` de todas las cartas existentes son idénticos a los de antes
  (tests de regresión existentes y `tests/golden/`).
- **Referencia independiente:** los tests existentes; no se compara con la salida de pccpy sino con la carta anterior.

### S011-RF-02 — `ControlChart.probability()` para cartas de variables

`ControlChart.probability(*, panel=None, below=None, above=None, between=None, point=None)` calcula, con la distribución en
control del panel (`panel=None` es el primer panel):

- `below=a`: `P(X < a)`; `above=b`: `P(X > b)`; `between=(a, b)`: `P(a ≤ X ≤ b)`; `below` y `above` juntos: probabilidad de
  quedar fuera (suma de las dos partes), como en la 010.
- Para I, Xbar y EWMA: normal con el `center` y la `sigma` del punto.
- Para MR y R: `σ·W`, con `W` el rango de `span` o `n` normales estándar (`scipy.stats.studentized_range` con infinitos grados
  de libertad). Para S: `σ·√(χ²ₙ₋₁/(n−1))`. En estos tres, `below ≤ 0` da 0.

**Aceptación:**
- **Dado** una carta Xbar-R con `n = 5`, `μ = m`, `σ = s` **cuando** `probability(below=a)` **entonces** `P = Φ((a − m)/(s/√5))`
  (`scipy.stats.norm`), con tolerancia relativa 1e-12.
- **Dado** un panel R con `n = 5` **cuando** `probability(above=b, panel="R")` **entonces** coincide con
  `scipy.stats.studentized_range(5, inf).sf(b/s)`; y con el rango de 5 normales simuladas (≥ 20 semillas) dentro del error
  de Monte Carlo.
- Para S, la referencia es `scipy.stats.chi2` escrita en el test.

### S011-RF-03 — `ControlChart.probability()` para cartas de atributos

Para P, NP, C y U la distribución es discreta (binomial con `n` y `p` del punto; Poisson con `c·n`); `below=a` es
`P(Y < a)` (estricto) y `above=b` es `P(Y > b)` (estricto), con `Y` el estadístico graficado. En P y U, el valor está en la
misma unidad que el panel (proporción o defectos por unidad): `Y = conteo/n`.

**Aceptación:**
- **Dado** una carta NP con `n = 100` y `p = 0,05` **cuando** `probability(above=UCL)` **entonces** `P = 1 − binom.cdf(⌊UCL⌋, 100, 0,05)`
  (`scipy.stats.binom`, tolerancia relativa 1e-12).
- **Dado** una carta C con `c = 9` **cuando** `probability(below=LCL)` **entonces** `P = poisson.cdf(⌈LCL⌉ − 1, 9)`.
- En una carta P con `n` variable, la probabilidad depende del punto (RF-06).

### S011-RF-04 — Cartas de eventos raros (G y T)

Para la carta G, `X` es la cantidad entre eventos (0, 1, 2…) con distribución geométrica de parámetro `p` (el de la carta);
`Y = X + 1` sigue `scipy.stats.geom(p)`. `below=a` es `P(X < a) = geom.cdf(⌈a⌉, p)` (0 si `a ≤ 0`) y `above=b` es
`P(X > b) = geom.sf(⌊b⌋ + 1, p)`. Para la carta T, el tiempo sigue la Weibull de forma y escala de la carta (la exponencial es
forma 1): `below=a` es `1 − exp(−(a/escala)^forma)` y `above=b` es `exp(−(b/escala)^forma)`; `below ≤ 0` da 0.

**Aceptación:**
- **Dado** una carta G con `p = 0,02` **cuando** `probability(above=UCL)` **entonces** `geom.sf(⌊UCL⌋ + 1, 0,02)`
  (`scipy.stats.geom`, tolerancia relativa 1e-12); sin argumentos, la probabilidad de superar el límite superior (el inferior es 0 y
  no tiene masa por debajo).
- **Dado** una carta T con forma `c` y escala `s` **cuando** `probability(below=a)` **entonces** `weibull_min.cdf(a, c, scale=s)`;
  sin argumentos, `P(T < LCI) + P(T > LCS)` = `2·Φ(−3)` con los límites de 3σ.
- **Referencia independiente:** `scipy.stats.geom` y `scipy.stats.weibull_min` escritos en el test; consistencia de `1/probability()`
  con `arl_g` y `arl_t`.

### S011-RF-05 — Sin argumentos: probabilidad de señal de un punto

`probability()` sin `below`, `above` ni `between` da la probabilidad de que un punto quede **fuera de los límites de control**
del panel en ese punto: `P(X < LCI) + P(X > LCS)` con la distribución en control (la probabilidad de falsa alarma de la prueba 1).

**Aceptación:**
- **Dado** una carta I con 3σ **cuando** `probability()` **entonces** `0,0026998…` (`2·norm.sf(3)`).
- **Dado** una carta con señal de un solo punto y parámetros constantes **entonces** `1/probability()` coincide con el ARL en
  control que dan `arl_shewhart`, `arl_range`, `arl_sd`, `arl_binomial` o `arl_poisson` con los mismos límites (consistencia entre
  funciones de pccpy; la referencia independiente es el cálculo con `scipy.stats`).

### S011-RF-06 — Elección del punto y de la etapa

Cuando la distribución cambia de un punto a otro (tamaño de muestra variable en P/U/Xbar/R/S, etapas con distintas medias o
sigmas, EWMA en sus primeros puntos), `point=` (un entero base 1 o un arreglo) indica de qué puntos se pide; la etapa
se deduce del punto. Sin `point=`, si la distribución es la misma en todos los puntos se usa esa; si no, `ValueError` pide `point=`.
Con `point=` array, el resultado tiene un elemento por punto (se combina con arreglos de valores elemento a elemento, como en la 010).

**Aceptación:**
- **Dado** una carta P con `n = 100, 150, 200` **cuando** `probability(above=0.08, point=[1, 3])` **entonces** dos
  probabilidades, cada una con su `n`.
- **Dado** esa misma carta **cuando** `probability(above=0.08)` **entonces** `ValueError` que menciona `point=`.
- **Dado** una carta con dos etapas **cuando** `point=` cae en la segunda **entonces** usa la media y la sigma de la segunda.

### S011-RF-07 — Cartas con transformación

Con `transform=` y `scale="original"`, los valores van en unidades originales y se transforman antes (la misma regla que la
010: la transformación es creciente); con `scale="transformed"`, ya están en la escala transformada. Solo los paneles de
posición (I y Xbar) tienen unidades originales; los de dispersión (MR, R, S) se piden en la escala transformada.

**Aceptación:**
- **Dado** una I-MR con Box-Cox **cuando** `probability(below=a)` **entonces** `Φ((T(a) − m)/s)` con `T` escrita en el test.
- **Dado** un panel de dispersión **cuando** hay transformación **entonces** los valores se interpretan en la escala transformada
  (documentado y probado).

### S011-RF-08 — Resultado

Devuelve el mismo `ProbabilityResult` de la especificación 010 (decisión de la persona responsable), con `event`, `probability`,
`ppm`, `p_below`, `p_above` y los valores usados. En una carta el evento no es un defecto: `dpmo` y `dpu` valen `None`, `sigma` es
`None` y `opportunities` es 1. La clase gana dos campos opcionales, `panel` y `point` (el panel y los puntos de la carta de que
se pidió; `None` en los resultados de capacidad), que `to_frame()` muestra como columnas solo cuando existen
(clave estable `panel` y `point`). Con arreglos, las medidas son arreglos de la forma resultante. El ARL de la señal de un punto
es `1/probability` (el usuario lo calcula; no hay campo `arl`).

**Aceptación:**
- `ppm == 1e6 · probability`; `dpmo is None` y `dpu is None`; `to_frame(stable=True)` con claves canónicas en inglés y las
  columnas `panel` y `point`.
- Los resultados de capacidad de la 010 no cambian: mismas columnas y mismos valores (tests de la 010 sin tocar).

### S011-RF-09 — Entrada y casos borde

`ValueError` en español para: panel inexistente; carta no admitida (CUSUM, MA, Zona, Laney, multivariadas); `between`
mal formado o con `a > b`; NaN; arreglos vacíos o de varias dimensiones; formas incompatibles; `point` fuera de rango.
`±inf` es válido. `below ≤ 0` en MR, R y S da 0; `above` ≤ 0 da 1. Con sigma = 0 (datos constantes), escalón 0/1 (0,5 en el
centro).

**Aceptación:**
- Cada caso de la lista anterior lanza el `ValueError` indicado (en español, con `tr()`), salvo `±inf`, `below ≤ 0` y sigma = 0,
  que dan el resultado descrito.
- **Referencia independiente:** los valores límite de `scipy.stats` (0 y 1 en las colas, escalón con sigma 0).

### S011-RF-10 — Validación, documentación, exportación y traducciones

**Aceptación:**
- Una comprobación en `run_validation()` (63 en total) con referencia independiente (`scipy.stats`) para cada familia de
  distribución (normal, rango, desviación estándar, binomial, Poisson, geométrica y Weibull).
- Docstrings en español; una sección en la guía de cartas de control (y en `arl.md`, que ya habla de probabilidades de
  señal) con un ejemplo ejecutable; README (es/en); traducciones; CHANGELOG.
- El docstring de `ProbabilityResult` refleja que sirve a capacidad y a cartas (campos `panel` y `point`).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Carta I, sin argumentos | `2·Φ(−3)` = 0,0026998 |
| Carta P con `n` variable y sin `point=` | `ValueError` que pide `point=` |
| Carta con etapas y `point=` en la 2.ª | Parámetros de la 2.ª etapa |
| EWMA, primer punto | σ del primer punto (más estrecha que la asintótica) |
| `probability(panel="R", below=0)` | 0 |
| `probability(above=+inf)` | 0; `below=+inf` da 1 |
| Panel de dispersión con transformación | Escala transformada (documentado) |
| CUSUM / Laney / MA / Zona / multivariadas | `ValueError` con el motivo |
| Carta G, `below ≤ 0` | 0 (no hay masa por debajo de 0) |
| Carta G, `above` negativo | 1 (`X ≥ 0`) |
| Carta T, `below ≤ 0` | 0 |
| Carta T exponencial | Weibull con `forma = 1` |
| LCI negativo recortado a 0 (cartas C/U) | `below=LCL` da 0 |
| `below=[44, 45]` y `above=56` | `above` se repite (como en la 010) |

## Resultados existentes que cambian

Ninguno. Se añaden un campo informativo a los paneles y un método a `ControlChart`; el cálculo de las cartas no se toca.

## No verificable sin la fuente

No sé si Minitab ofrece un cálculo equivalente. Las distribuciones del rango y de S asumen normalidad de las observaciones y
parámetros conocidos; con `sigma_method` distinto del estimador de la carta, la σ es la de la carta. Los límites de las cartas
de atributos son los de 3σ aproximados que usa pccpy; la probabilidad es la exacta (binomial/Poisson) con esos límites.

## Decisiones de la persona responsable

1. **Alcance de la primera entrega:** I, MR, Xbar, R, S, P, NP, C, U y EWMA, **más G y T**; fuera CUSUM, MA, Zona, Laney y
   multivariadas.
2. **Resultado:** reutilizar `ProbabilityResult` de la 010 (con `dpmo`/`dpu` = `None` en cartas), no crear una clase propia.
3. **`shift=`:** no se incluye (es el ARL).
4. **Punto por defecto:** opción A: si la distribución cambia entre puntos y no se indica `point=`, `ValueError` que pide
   `point=`; si es la misma en todos, no hace falta.
5. **Versión:** 0.15.5.

## Preguntas abiertas

Ninguna.
