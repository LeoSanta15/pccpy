# 010 — Probabilidad de un valor x en el análisis de capacidad

- **Estado:** borrador
- **Identificador:** S010
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** [NECESITA ACLARACIÓN: ver pregunta 3] (método nuevo; no cambia ningún resultado existente)

## Problema

El análisis de capacidad (`capability_analysis`, `capability_boxcox` y `capability_nonnormal`) da la probabilidad de salirse de
las especificaciones solo en dos puntos fijos: el PPM esperado bajo el LEI y sobre el LES (y su total, el DPMO). No hay forma de
preguntar «¿cuál es la probabilidad de que una pieza quede por debajo de 47?» o «¿entre 48 y 52?» para un valor `x` que el
usuario quiera probar. Hoy se puede hacer a mano con `scipy.stats` (`stats.norm(r.mean, r.sigma_overall).cdf(x)`), pero el
usuario tiene que saber qué sigma usar (general o dentro) y, con Box-Cox, transformar `x` con el `lambda` guardado.

## Fuera de alcance

- Capacidad de atributos (`capability_binomial` y `capability_poisson`): su «probabilidad» es la de un conteo, no la de un valor
  continuo.
- Probabilidades condicionales o intervalos de confianza de la probabilidad (el error de estimar la media y la sigma).
- Cambiar los resultados existentes (`ppm_*`, `dpmo`, `z_*`).
- Una función suelta: el cálculo es un método del resultado (decisión de la persona responsable).

## Requisitos

Todos los valores `x` van en las **unidades originales** de los datos, también cuando el análisis se hizo con una
transformación.

### S010-RF-01 — Probabilidad con distribución normal

`CapabilityResult.probability(x, kind="below", x2=None, unit="probability", sigma="overall", opportunities=1)`:
probabilidad de que una observación del proceso, normal con la media `mean` y la sigma indicada, quede:

- `kind="below"`: por debajo de `x`, `P(X < x)`;
- `kind="above"`: por encima de `x`, `P(X > x)`;
- `kind="between"`: entre `x` y `x2`, `P(x ≤ X ≤ x2)` (exige `x2 ≥ x`).

`sigma="overall"` (por defecto) usa `sigma_overall`; `sigma="within"` usa `sigma_within`. `x` y `x2` pueden ser un número o un
arreglo (el resultado tiene la misma forma).

**Aceptación:**
- **Dado** un resultado con `mean = m` y `sigma_overall = s` **cuando** `probability(x)` **entonces** es `Φ((x − m)/s)`
  (`scipy.stats.norm`), con tolerancia relativa 1e-12.
- `above` es `1 − P(below)` calculado con la cola superior (sin cancelación cuando es muy pequeña) y `between` es
  `Φ((x2−m)/s) − Φ((x−m)/s)`.
- `sigma="within"` usa `sigma_within`.
- **Referencia independiente:** `scipy.stats.norm` escrito en el test con la media y la sigma del resultado.

### S010-RF-02 — Resultados con transformación

Con un resultado de `capability_boxcox` o de `capability_analysis(..., transform=...)` (`result.transform` no es `None`), la
media y las sigmas están en la escala transformada. `probability` transforma `x` (y `x2`) con la misma transformación antes de
calcular la probabilidad normal. Las transformaciones admitidas (Box-Cox, Yeo-Johnson y Johnson) son crecientes, así que
`below`, `above` y `between` conservan su sentido.

**Aceptación:**
- **Dado** un resultado con Box-Cox y `lambda = λ` **cuando** `probability(x)` **entonces** es `Φ((T(x) − m)/s)` con
  `T(x) = (x^λ − 1)/λ` escrita en el test (con `ln x` si `λ = 0`).
- **Referencia independiente:** la fórmula de Box-Cox escrita aparte; no la salida de `Transformation.forward`.

### S010-RF-03 — Probabilidad con distribución no normal

`NonNormalCapabilityResult.probability(x, kind="below", x2=None, unit="probability", sigma="overall", opportunities=1)`: usa la
distribución ajustada (`frozen`): `cdf` para `below`, `sf` para `above` y `cdf(x2) − cdf(x)` para `between`. Esta distribución
no tiene una sigma «dentro»: con `sigma="within"` lanza `ValueError`.

**Aceptación:**
- **Dado** un ajuste lognormal **cuando** `probability(x)` **entonces** coincide con la `cdf` de la distribución ajustada por
  `scipy.stats` aparte (re-ajuste en el test, `lognorm.fit(x, floc=0)`).
- **Tolerancia:** relativa 1e-3. Los ajustes de máxima verosimilitud varían en la cuarta o quinta cifra entre versiones de
  SciPy (el optimizador de SciPy se detiene en ~3·10⁻⁶; principio 13), así que la referencia independiente (el re-ajuste) no
  puede ser más exacta que eso.

### S010-RF-04 — Unidades de la respuesta

`unit` elige cómo se expresa el resultado de `p`:

| `unit` | Valor |
|---|---|
| `"probability"` (por defecto) | `p`, entre 0 y 1 |
| `"ppm"` | `1e6 · p` (partes por millón fuera del intervalo) |
| `"dpmo"` | `1e6 · p` (defectos por millón de oportunidades; un defecto por oportunidad) |
| `"dpu"` | `opportunities · p` (defectos esperados por unidad con `opportunities` oportunidades de defecto) |

**Aceptación:**
- `probability(x, unit="ppm") == 1e6 · probability(x)` y `unit="dpmo"` da el mismo número que `"ppm"`.
- `probability(x, unit="dpu", opportunities=3) == 3 · probability(x)`; con `opportunities=1` (por defecto), `"dpu"` es igual
  que `"probability"`.
- **Referencia independiente:** las definiciones de PPM, DPMO y DPU escritas en el test; coherencia con `dpmo` de
  `CapabilityResult` (que es el PPM total esperado general).

### S010-RF-05 — Entrada y casos borde

`ValueError` en español para entradas inválidas y resultado coherente en los extremos.

**Aceptación:**
- `kind` fuera de `{"below", "above", "between"}`, `unit` fuera de `{"probability", "ppm", "dpmo", "dpu"}`, `sigma` fuera de
  `{"overall", "within"}` → `ValueError`.
- `kind="between"` sin `x2`, o `x2 < x`, o `x2` con otro `kind` → `ValueError`.
- `x` con NaN → `ValueError`; `x = ±inf` es válido (`below(+inf) = 1`, `above(+inf) = 0`, `below(−inf) = 0`).
- `opportunities` no entero o < 1 → `ValueError`.
- Con sigma 0 (datos constantes) la probabilidad es un escalón: 0 o 1 según el lado, y 0,5 si `x` es la media.
- `x` como lista, arreglo o escalar; un escalar devuelve un `float` y un arreglo, un arreglo.

### S010-RF-06 — Coherencia con los resultados existentes

`probability` debe reproducir lo que el resultado ya informa en los límites de especificación.

**Aceptación:**
- `probability(lsl, "below", unit="ppm")` == `ppm_overall[0]` y `probability(usl, "above", unit="ppm")` == `ppm_overall[1]`;
  con `sigma="within"`, `ppm_within[0]` y `ppm_within[1]`.
- En un resultado no normal, `probability(lsl, "below", unit="ppm")` == `ppm_expected[0]` y `probability(usl, "above",
  unit="ppm")` == `ppm_expected[1]`.
- Con transformación, lo mismo con `lsl` y `usl` en unidades originales.

### S010-RF-07 — Validación, documentación y traducciones

**Aceptación:**
- Una comprobación en `run_validation()` (62 en total) con referencia independiente y tolerancia justificada.
- Docstring en español con los supuestos (normalidad en la escala indicada, parámetros estimados tratados como conocidos).
- Una sección en la guía `docs/source/capacidad_indices.md` con un ejemplo ejecutable y en el README (es/en).
- Mensajes con `tr()` y traducción al inglés (pendiente de revisión experta en SPC).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `x` en la media | `below` = `above` = 0,5 |
| `x = ±inf` | 0 o 1, sin error |
| `x2 == x` en `between` | 0 |
| Cola muy pequeña (`x` a 10 sigmas) | `above` con la cola superior, sin cancelación |
| Sigma 0 | Escalón 0/1 (0,5 en la media) |
| Resultado con transformación y `sigma="within"` | Válido (la sigma «dentro» también está en la escala transformada) |
| No normal y `sigma="within"` | `ValueError` |
| `x` como lista | Se acepta; devuelve un arreglo |

## Resultados existentes que cambian

Ninguno. Método nuevo.

## No verificable sin la fuente

No se ha comparado con Minitab: no sé si Minitab ofrece un cálculo equivalente ni cómo lo llama. La probabilidad supone que la
distribución (normal en la escala indicada, o la ajustada) es la del proceso y trata la media y la sigma estimadas como
conocidas: no incluye la incertidumbre de haberlas estimado.

## Preguntas abiertas

- [NECESITA ACLARACIÓN: 1. **Semántica de `dpmo` y `dpu`.** Propuesta (RF-04): `ppm` y `dpmo` son `1e6·p` (para una sola
  característica con una oportunidad por pieza son el mismo número, como ya hace `CapabilityResult.dpmo`) y `dpu` es
  `opportunities·p` con `opportunities=1` por defecto, de modo que sin ese parámetro `dpu` coincide con la probabilidad. ¿Te
  sirve, o `dpu` debería ser otra cosa (por ejemplo, el número esperado de defectos en una pieza con varias características)?]
- [NECESITA ACLARACIÓN: 2. **Forma de la llamada.** Propuesta: `kind="below"|"above"|"between"` con `x2` para el extremo
  superior, y `x` como escalar o arreglo. Alternativa: `below=`, `above=` y `between=(a, b)` como parámetros opcionales y
  excluyentes. ¿Cuál prefieres?]
- [NECESITA ACLARACIÓN: 3. **Versión.** Es un método nuevo que no cambia resultados. Si entra antes del PR de versión pendiente
  (0.15.4, que lleva la leyenda de la CUSUM y el ARL), iría en la 0.15.4; si no, en la 0.15.5. ¿Esperamos a incluirlo en la
  0.15.4?]
