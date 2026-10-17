# 010 — Probabilidad de un valor en el análisis de capacidad

- **Estado:** aprobada
- **Identificador:** S010
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.4 (método nuevo; no cambia ningún resultado existente; decisión de la persona responsable, junto con
  la leyenda de la CUSUM y el ARL)

## Problema

El análisis de capacidad (`capability_analysis`, `capability_boxcox` y `capability_nonnormal`) da la probabilidad de salirse de
las especificaciones solo en dos puntos fijos: el PPM esperado bajo el LEI y sobre el LES (y su total, el DPMO). No hay forma de
preguntar «¿cuál es la probabilidad de que una pieza quede por debajo de 47?» o «¿entre 48 y 52?» para un valor que el usuario
quiera probar. El resultado ya conoce la distribución (media, sigma, ajuste, transformación) y los límites de especificación;
lo único que falta es el valor a probar. Hoy se puede hacer a mano con `scipy.stats`
(`stats.norm(r.mean, r.sigma_overall).cdf(x)`), pero el usuario tiene que saber qué sigma usar (general o dentro) y, con Box-Cox,
transformar el valor con el `lambda` guardado.

## Fuera de alcance

- Capacidad de atributos (`capability_binomial` y `capability_poisson`): su «probabilidad» es la de un conteo.
- Arreglos de más de una dimensión: los valores son un número o un arreglo de una dimensión.
- Intervalos de confianza de la probabilidad (el error de haber estimado la media y la sigma).
- Cambiar los resultados existentes (`ppm_*`, `dpmo`, `z_*`).
- Una función suelta: el cálculo es un método del resultado (decisión de la persona responsable).

## Requisitos

Todos los valores van en las **unidades originales** de los datos, también cuando el análisis se hizo con una transformación.
Cada valor (`below`, `above` y cada extremo de `between`) puede ser un número o un arreglo de una dimensión; los arreglos se
combinan elemento a elemento (con las reglas de difusión de NumPy: un número se repite) y cada medida del resultado tiene la
forma resultante (un número si todo son números).

### S010-RF-01 — Probabilidad por debajo, por encima o entre valores (distribución normal)

`CapabilityResult.probability(*, below=None, above=None, between=None, sigma="overall", opportunities=1)`: el valor a probar
va en el propio parámetro. Con una observación `X` del proceso (normal con la media `mean` y la sigma indicada):

- `below=a`: `P(X < a)`;
- `above=b`: `P(X > b)`;
- `between=(a, b)`: `P(a ≤ X ≤ b)` (exige `a ≤ b` en cada elemento).

`sigma="overall"` (por defecto) usa `sigma_overall`; `sigma="within"` usa `sigma_within`.

**Aceptación:**
- **Dado** un resultado con `mean = m` y `sigma_overall = s` **cuando** `probability(below=a)` **entonces** `P = Φ((a − m)/s)`
  (`scipy.stats.norm`), con tolerancia relativa 1e-12.
- `above` se calcula con la cola superior (sin cancelación cuando es muy pequeña) y `between` es `Φ((b−m)/s) − Φ((a−m)/s)`.
- `sigma="within"` usa `sigma_within`.
- **Referencia independiente:** `scipy.stats.norm` escrito en el test con la media y la sigma del resultado.

### S010-RF-02 — Fuera de un intervalo y límites de especificación heredados

- `probability(below=a, above=b)` da la probabilidad de quedar **fuera**: `P(X < a) + P(X > b)`, con sus dos partes por separado.
- `probability()` sin argumentos **hereda** los límites de especificación del resultado: `below=lsl` y `above=usl` (el que
  exista). Sin ningún límite de especificación, lanza `ValueError` que pide indicar `below`, `above` o `between`.
- `between` no se combina con `below` ni con `above` (`ValueError`).

**Aceptación:**
- **Dado** un resultado con `lsl` y `usl` **cuando** `probability()` **entonces** es `P(X < lsl) + P(X > usl)`, y coincide con el
  PPM total esperado que el resultado ya informa (RF-07).

### S010-RF-03 — Resultados con transformación

Con un resultado de `capability_boxcox` o de `capability_analysis(..., transform=...)` (`result.transform` no es `None`), la
media y las sigmas están en la escala transformada. `probability` transforma los valores con la misma transformación antes de
calcular la probabilidad normal. Las transformaciones admitidas (Box-Cox, Yeo-Johnson y Johnson) son crecientes, así que
`below`, `above` y `between` conservan su sentido.

**Aceptación:**
- **Dado** un resultado con Box-Cox y `lambda = λ` **cuando** `probability(below=a)` **entonces** `P = Φ((T(a) − m)/s)` con
  `T(a) = (a^λ − 1)/λ` escrita en el test (con `ln a` si `λ = 0`).
- **Referencia independiente:** la fórmula de Box-Cox escrita aparte; no la salida de `Transformation.forward`.

### S010-RF-04 — Probabilidad con distribución no normal

`NonNormalCapabilityResult.probability(*, below=None, above=None, between=None, sigma="overall", opportunities=1)` usa la
distribución ajustada (`frozen`): `cdf` para `below`, `sf` para `above` y `cdf(b) − cdf(a)` para `between`; sin argumentos hereda
`lsl` y `usl`. Esta distribución no tiene una sigma «dentro»: con `sigma="within"` lanza `ValueError`.

**Aceptación:**
- **Dado** un ajuste lognormal **cuando** `probability(below=a)` **entonces** coincide con la `cdf` de la distribución ajustada por
  `scipy.stats` aparte (re-ajuste en el test, `lognorm.fit(x, floc=0)`).
- **Tolerancia:** relativa 1e-3. Los ajustes de máxima verosimilitud varían en la cuarta o quinta cifra entre versiones de
  SciPy (el optimizador de SciPy se detiene en ~3·10⁻⁶; principio 13), así que la referencia independiente (el re-ajuste) no
  puede ser más exacta que eso.

### S010-RF-05 — Devuelve todas las medidas que apliquen

`probability` devuelve un `ProbabilityResult` con todas las medidas a la vez, no una sola a elegir:

| Campo | Valor | Aplica |
|---|---|---|
| `probability` | `p`, entre 0 y 1 | siempre |
| `ppm` | `1e6 · p` (partes por millón) | siempre |
| `dpmo` | `1e6 · p` (defectos por millón de oportunidades; un defecto por oportunidad) | cuando el evento es un **defecto**: `below`, `above` y fuera de un intervalo |
| `dpu` | `opportunities · p` (defectos por unidad con `opportunities` oportunidades de defecto; por defecto 1) | cuando el evento es un defecto |

Con `between` (la zona buena, no un defecto), `dpmo` y `dpu` **no aplican** y valen `None`. El resultado trae además `p_below` y
`p_above` (las dos partes, `None` si no hay), el evento (`event`: `"below"`, `"above"`, `"outside"` o `"between"`), los valores
usados y la sigma elegida. Con arreglos, las medidas son arreglos de la forma resultante. Tiene `to_frame(stable=False)` (una fila por
elemento; con claves canónicas si `stable=True`) y `summary()`.

**Aceptación:**
- `ppm == 1e6 · probability` y `dpmo == ppm` (cuando aplica).
- `probability(below=a, opportunities=3).dpu == 3 · probability`; con `opportunities=1`, `dpu == probability`.
- `probability(between=(a, b)).dpmo is None` y `.dpu is None`.
- **Referencia independiente:** las definiciones de PPM, DPMO y DPU escritas en el test.

### S010-RF-06 — Entrada y casos borde

`ValueError` en español para entradas inválidas y resultado coherente en los extremos.

**Aceptación:**
- `sigma` fuera de `{"overall", "within"}` → `ValueError`.
- `between` que no sea un par `(a, b)` o con `a > b` en algún elemento, o combinado con `below`/`above` → `ValueError`.
- Valores con NaN → `ValueError`; `±inf` es válido (`below=+inf` da 1, `above=+inf` da 0, `below=−inf` da 0).
- Arreglos de más de una dimensión, vacíos o que no se pueden combinar (formas incompatibles) → `ValueError`.
- Con arreglos, cada elemento da el mismo resultado que la llamada con ese número solo.
- `opportunities` no entero o < 1 → `ValueError`.
- Con sigma 0 (datos constantes) la probabilidad es un escalón: 0 o 1 según el lado, y 0,5 si el valor es la media.

### S010-RF-07 — Coherencia con los resultados existentes

`probability` debe reproducir lo que el resultado ya informa en los límites de especificación.

**Aceptación:**
- `probability().ppm == ppm_overall[2]`, `p_below·1e6 == ppm_overall[0]` y `p_above·1e6 == ppm_overall[1]`; con `sigma="within"`,
  `ppm_within`.
- En un resultado no normal, lo mismo con `ppm_expected`.
- Con transformación, lo mismo con `lsl` y `usl` en unidades originales.
- `probability().dpmo` coincide con `CapabilityResult.dpmo`.

### S010-RF-08 — Validación, documentación, exportación y traducciones

**Aceptación:**
- Una comprobación en `run_validation()` (62 en total) con referencia independiente y tolerancia justificada.
- `ProbabilityResult` se exporta en `pccpy` y `__all__`; el método y el resultado tienen docstring en español con los supuestos
  (normalidad en la escala indicada, parámetros estimados tratados como conocidos).
- Una sección en la guía `docs/source/capacidad_indices.md` con un ejemplo ejecutable y en el README (es/en).
- Mensajes y etiquetas con `tr()` y traducción al inglés (pendiente de revisión experta en SPC).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Sin argumentos y con LEI y LES | Fuera de especificaciones: `P(X < LEI) + P(X > LES)` |
| Sin argumentos y sin límites | `ValueError` que pide indicar `below`, `above` o `between` |
| Valor en la media | `below` = `above` = 0,5 |
| `below=[44, 45, 46]` | Tres probabilidades, una por valor |
| `below=[44, 45]` y `above=56` | `above` se repite: dos probabilidades de quedar fuera |
| Arreglo vacío o de dos dimensiones | `ValueError` |
| `±inf` | 0 o 1, sin error |
| `between=(a, a)` | 0 |
| Cola muy pequeña (a 10 sigmas) | `above` con la cola superior, sin cancelación |
| Sigma 0 | Escalón 0/1 (0,5 en la media) |
| Con transformación y `sigma="within"` | Válido (la sigma «dentro» también está en la escala transformada) |
| No normal y `sigma="within"` | `ValueError` |

## Resultados existentes que cambian

Ninguno. Método y clase de resultado nuevos.

## No verificable sin la fuente

No se ha comparado con Minitab: no sé si Minitab ofrece un cálculo equivalente ni cómo lo llama. La probabilidad supone que la
distribución (normal en la escala indicada, o la ajustada) es la del proceso y trata la media y la sigma estimadas como
conocidas: no incluye la incertidumbre de haberlas estimado.

## Decisiones de la persona responsable

1. **Medidas:** devolver todas las que apliquen (probabilidad, PPM, DPMO y DPU), no una a elegir.
2. **Parámetros:** `below`, `above` y `between` (el valor va en el propio parámetro); no hay un `x` aparte.
3. **Sigma:** general por defecto y, si el usuario quiere, la de dentro.
4. **Alcance:** distribución normal y no normal; los valores pueden ser números o arreglos.
5. **Forma:** método del resultado.
6. **Versión:** 0.15.4.

7. **`dpmo` y `dpu` con `between`:** no aplican (la zona buena no es un defecto); valen `None`.
8. **`dpu`:** `opportunities · p` con `opportunities = 1` por defecto.
9. **Sin argumentos:** `probability()` hereda `lsl` y `usl` del resultado.

## Preguntas abiertas

Ninguna.
