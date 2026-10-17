# 009 — ARL de las cartas Shewhart, EWMA y CUSUM

- **Estado:** borrador
- **Identificador:** S009
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** [NECESITA ACLARACIÓN: ver pregunta 6] (función pública nueva; no cambia ningún resultado existente)

## Problema

pccpy solo calcula el ARL (longitud media de racha: número esperado de puntos graficados hasta la primera señal) en dos
casos internos de las cartas multivariadas: `mewma_limit` y `mcusum_limit` lo usan para **fijar el límite** que produce un
ARL en control dado (cadena de Markov de Runger y Prabhu, `_mewma_arl` y `_mcusum_arl` en `multivariate.py`, privadas).
No hay forma de preguntar «¿qué ARL tiene esta carta?» ni «¿qué ARL tiene si la media se desplaza 1σ?» para las cartas
univariadas, que es lo que se usa para comparar y diseñar cartas (Shewhart frente a EWMA frente a CUSUM). Hoy las cifras
de ARL del README y de la validación (≈ 168, ≈ 570, ≈ 8) salen de simulaciones o de la literatura, no de una función.

## Fuera de alcance

- Pruebas suplementarias de rachas (pruebas 2 a 8): el ARL con ellas exige una cadena de Markov por regla.
- Cartas de atributos (P, NP, C, U), I-MR y MR, G y T, y las multivariadas fuera de control.
- Parámetros estimados de los datos (el efecto de estimar μ y σ en un Fase I); se supone μ y σ conocidos.
- Datos no normales o autocorrelacionados.
- Un ARL general por simulación para cualquier carta (ver pregunta 2).

## Requisitos

Supuestos comunes: el estadístico graficado es normal, independiente en el tiempo, con media `shift` (en unidades de su
propia σ) y σ = 1 una vez estandarizado; ARL «desde el estado inicial» (puntos graficados hasta la primera señal, la
señal cuenta como un punto, así que el ARL mínimo es 1).

### S009-RF-01 — ARL de una carta Shewhart (un punto fuera de los límites)

El sistema debe calcular el ARL exacto de una carta Shewhart con límites a ±`k` sigmas: `1 / (1 − P(|Z| < k))` con
`Z ~ N(shift, 1)`.

**Aceptación:**
- **Dado** `k = 3` y `shift = 0` **cuando** se calcula **entonces** el ARL es `1 / (2·Φ(−3)) = 370,398…` (tolerancia
  relativa 1e-12).
- **Dado** `k = 3` y `shift = 1` **entonces** el ARL es `1 / (Φ(−4) + Φ(−2))` = 43,89… calculado aparte con
  `scipy.stats.norm` (tolerancia relativa 1e-12).
- **Referencia independiente:** fórmula cerrada con `scipy.stats.norm`; valores conocidos de la literatura (370,4 y 43,9;
  Montgomery, *Introduction to SQC*) citados como contraste.

### S009-RF-02 — ARL de una CUSUM tabular bilateral

El sistema debe calcular el ARL de la CUSUM tabular bilateral (la de `cusum_chart`: `C⁺ᵢ = max(0, zᵢ − k + C⁺ᵢ₋₁)`,
`C⁻ᵢ = max(0, −zᵢ − k + C⁻ᵢ₋₁)`, señal con `C > h`) con `h`, `k`, `shift` y `headstart` dados.

**Aceptación:**
- **Dado** `h = 4`, `k = 0,5`, `shift = 0` **entonces** ARL ≈ 168 (bilateral).
- **Dado** `h = 4`, `k = 0,5`, `shift = 1` **entonces** ARL ≈ 8,38 (bilateral).
- **Referencia independiente:** (a) valores de la literatura (Hawkins y Olwell, 1998; Lucas y Crosier, 1982); (b) simulación
  de Monte Carlo con ≥ 20 semillas; (c) la aproximación de Siegmund para cada lado como contraste de orden de magnitud. La
  tolerancia se declara según la referencia (principio 13).

### S009-RF-03 — ARL de una EWMA bilateral

El sistema debe calcular el ARL de la EWMA bilateral con límites exactos (varianza `λ/(2−λ)·(1−(1−λ)^{2i})` tendiendo a
la asintótica) o asintóticos, con `weight` (λ), `L` y `shift` dados.

**Aceptación:**
- **Dado** `λ = 0,2`, `L = 2,962` y `shift = 0` **entonces** ARL ≈ 500 (valor de diseño de Lucas y Saccucci, 1990).
- **Dado** `λ = 0,2`, `L = 3` y `shift = 0` **entonces** ARL ≈ 570 con límites asintóticos (cifra que ya cita el README).
- **Referencia independiente:** literatura (Lucas y Saccucci, 1990) y Monte Carlo con ≥ 20 semillas.

### S009-RF-04 — Entrada y casos borde

El sistema debe rechazar parámetros inválidos con un `ValueError` en español y devolver un resultado coherente en los
extremos.

**Aceptación:**
- `k <= 0`, `h <= 0`, `weight` fuera de `(0, 1]`, `L <= 0`, `headstart` fuera de `[0, h)`, o valores no finitos →
  `ValueError`.
- El ARL es simétrico en `shift` (bilateral): `arl(shift) == arl(−shift)`.
- El ARL decrece al crecer `|shift|` y tiende a 1 con desplazamientos grandes; nunca baja de 1.
- `shift` como arreglo devuelve un arreglo (para dibujar la curva ARL frente al desplazamiento).

### S009-RF-05 — Validación y documentación

El sistema debe sumar comprobaciones a `run_validation()` y documentar los supuestos en el docstring y la guía.

**Aceptación:**
- Una comprobación por función en `run_validation()` con referencia independiente y tolerancia justificada.
- El docstring de cada función dice qué se supone (normalidad, μ y σ conocidos, sin pruebas suplementarias).
- Una página o sección de la guía con un ejemplo ejecutable (curva ARL de Shewhart, EWMA y CUSUM frente al
  desplazamiento).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `shift = 0` | ARL en control (ARL₀) |
| `shift` muy grande (≥ 10) | ARL → 1 |
| `shift` negativo | Igual que el positivo (carta bilateral) |
| `headstart` cercano a `h` | ARL menor; sin error |
| `weight = 1` en la EWMA | Es la Shewhart: debe dar el mismo ARL que RF-01 |
| `k` pequeño en la Shewhart | ARL cercano a 1; sin desbordes |
| NaN o inf | `ValueError` |

## Resultados existentes que cambian

Ninguno. Función pública nueva.

## No verificable sin la fuente

Las cifras de la literatura (168, 8,38, 500, 570, 370,4, 43,9) las recuerdo y las cito de memoria: no pude consultar
Hawkins y Olwell (1998), Lucas y Saccucci (1990), Lucas y Crosier (1982) ni Montgomery desde este entorno. Cada una se
respalda con un cálculo independiente (fórmula cerrada o Monte Carlo) y consta como «recordada de memoria» (principio 12).
Tampoco se ha comparado con el ARL que muestre Minitab.

## Preguntas abiertas

- [NECESITA ACLARACIÓN: 1. **Alcance de la primera versión.** Propuesta: solo Shewhart (RF-01), CUSUM (RF-02) y EWMA
  (RF-03), con las cartas univariadas por subgrupos o individuales con media conocida. ¿Falta alguna o sobra alguna?]
- [NECESITA ACLARACIÓN: 2. **Simulación.** ¿Incluimos un ARL por simulación (`method="simulation"`) como respaldo para
  cualquier carta, o solo los métodos exactos o numéricos de arriba? Propuesta: solo los exactos/numéricos ahora.]
- [NECESITA ACLARACIÓN: 3. **API.** Propuesta: tres funciones paramétricas, `arl_shewhart(k=3, shift=0)`,
  `arl_cusum(h=4, k=0.5, shift=0, headstart=0)` y `arl_ewma(weight=0.2, L=3, shift=0, exact_limits=False)`, con `shift`
  en unidades de σ del estadístico graficado. Alternativa: una sola `arl(chart, shift)` que lea los parámetros de la
  carta; más cómoda, pero ata el cálculo al objeto y a lo que guarda cada carta. ¿Cuál prefieres, y añadimos después
  `chart.arl(shift)`?]
- [NECESITA ACLARACIÓN: 4. **Subgrupos.** Para Xbar con subgrupos de tamaño `n`, la σ del estadístico es σ/√n. ¿`shift` va
  en σ del estadístico (propuesta; el usuario multiplica por √n) o añadimos el parámetro `n` para dar el desplazamiento en
  σ de la variable individual?]
- [NECESITA ACLARACIÓN: 5. **Método numérico de CUSUM y EWMA.** Propuesta: ecuación integral con cuadratura de Gauss-Legendre
  (Crowder 1987 para la EWMA; Brook y Evans 1972 o Champ y Rigdon para la CUSUM), con el número de nodos como parámetro
  oculto y un valor por defecto que dé 4 cifras de precisión; la precisión se declara y se contrasta con la simulación.
  Alternativa: cadena de Markov con celdas (como `_mewma_arl`), más simple pero menos precisa con el mismo coste.]
- [NECESITA ACLARACIÓN: 6. **Versión.** Pediste incluir esto en el lanzamiento de la próxima versión. Es una función
  pública nueva que no cambia ningún resultado. Según CLAUDE.md («cambia resultados → versión menor; no → parche») sería
  0.15.4, junto con la leyenda de la CUSUM (spec 008). Por semver una función nueva suele ser menor (0.16.0). ¿Cuál
  usamos?]
