# 009 — ARL de las cartas de control

- **Estado:** borrador
- **Identificador:** S009
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.4 (función pública nueva; no cambia ningún resultado existente; decisión de la persona responsable)

## Problema

pccpy solo calcula el ARL (longitud media de racha: número esperado de puntos graficados hasta la primera señal) en dos
casos internos de las cartas multivariadas: `mewma_limit` y `mcusum_limit` lo usan para **fijar el límite** que produce un
ARL en control dado (cadena de Markov de Runger y Prabhu, `_mewma_arl` y `_mcusum_arl` en `multivariate.py`, privadas).
No hay forma de preguntar «¿qué ARL tiene esta carta?» ni «¿qué ARL tiene si la media se desplaza 1σ?», que es lo que se
usa para comparar y diseñar cartas (Shewhart frente a EWMA frente a CUSUM). Hoy las cifras de ARL del README y de la
validación (≈ 168, ≈ 570, ≈ 8) salen de simulaciones o de la literatura, no de una función.

## Fuera de alcance

- Pruebas suplementarias de rachas (pruebas 2 a 8): el ARL con ellas exige una cadena de Markov por regla.
- I-MR y MR, Laney, MA, Zona, EWMA y CUSUM de atributos, y las multivariadas fuera de control.
- Parámetros estimados de los datos (el efecto de estimar μ y σ en la Fase I); se supone μ y σ conocidos.
- Datos no normales o autocorrelacionados (salvo los modelos discretos y de eventos raros de RF-07 y RF-08).

## Supuestos comunes

El estadístico graficado es independiente en el tiempo y sigue el modelo indicado en cada requisito, con parámetros
conocidos. ARL «desde el estado inicial»: puntos graficados hasta la primera señal; la señal cuenta como un punto, así que
el mínimo es 1. `shift` es el desplazamiento de la media **en unidades de σ del estadístico graficado** (para una Xbar con
subgrupos de tamaño `n`, la σ del estadístico es σ/√n: el usuario multiplica por √n).

## Requisitos

### S009-RF-01 — ARL de una carta Shewhart de la media (un punto fuera de los límites)

`arl_shewhart(k=3.0, shift=0.0, method="numeric", ...)`: ARL de una carta con límites a ±`k` sigmas de un estadístico
normal con media `shift` y σ = 1: `1 / P(|Z| > k)`, `Z ~ N(shift, 1)`.

**Aceptación:**
- **Dado** `k = 3` y `shift = 0` **entonces** el ARL es `1 / (2·Φ(−3))` = 370,398… (tolerancia relativa 1e-12).
- **Dado** `k = 3` y `shift = 1` **entonces** el ARL es `1 / (Φ(−4) + Φ(−2))` = 43,894… (tolerancia relativa 1e-12).
- **Referencia independiente:** fórmula cerrada con `scipy.stats.norm` (ya calculada aparte: 370,3983 y 43,8947); valores de
  la literatura (370,4 y 43,9; Montgomery) como contraste, recordados de memoria.

### S009-RF-02 — ARL de una CUSUM tabular bilateral

`arl_cusum(h=4.0, k=0.5, shift=0.0, headstart=0.0, method="numeric", ...)`: ARL de la CUSUM tabular de `cusum_chart`
(`C⁺ᵢ = max(0, zᵢ − k + C⁺ᵢ₋₁)`, `C⁻ᵢ = max(0, −zᵢ − k + C⁻ᵢ₋₁)`, señal con `C > h`).

**Aceptación:**
- **Dado** `h = 4`, `k = 0,5`, `shift = 0` **entonces** ARL ≈ 168 (bilateral).
- **Dado** `h = 4`, `k = 0,5`, `shift = 1` **entonces** ARL ≈ 8,38 (bilateral).
- **Referencia independiente:** (a) valores de la literatura (Hawkins y Olwell, 1998; Lucas y Crosier, 1982), recordados de
  memoria; (b) simulación de Monte Carlo con ≥ 20 semillas; (c) los dos métodos numéricos de RF-04 entre sí. La tolerancia se
  declara según la referencia (principio 13).

### S009-RF-03 — ARL de una EWMA bilateral

`arl_ewma(weight=0.2, L=3.0, shift=0.0, exact_limits=False, method="numeric", ...)`: ARL de la EWMA bilateral con límites
asintóticos (`L·σ·√(λ/(2−λ))`) o exactos (varianza `λ/(2−λ)·(1−(1−λ)^{2i})`).

**Aceptación:**
- **Dado** `λ = 0,2`, `L = 2,962`, `shift = 0` **entonces** ARL ≈ 500 (valor de diseño de Lucas y Saccucci, 1990).
- **Dado** `λ = 0,2`, `L = 3`, `shift = 0`, límites asintóticos **entonces** ARL ≈ 570 (cifra que cita el README).
- **Dado** `λ = 1` **entonces** el ARL es el de la Shewhart de RF-01 con el mismo `L`.
- **Referencia independiente:** literatura (recordada de memoria) y Monte Carlo con ≥ 20 semillas; la identidad `λ = 1`.

### S009-RF-04 — Elección del método

Cada función tiene un parámetro `method`: `"numeric"` (por defecto), `"markov"` o `"simulation"`.

- `"numeric"`: fórmula cerrada (Shewhart) o ecuación integral con cuadratura de Gauss-Legendre (CUSUM y EWMA).
- `"markov"`: cadena de Markov con celdas (Brook y Evans, 1972, para la CUSUM; Lucas y Saccucci, 1990, para la EWMA).
- `"simulation"`: Monte Carlo, con `n_runs` (por defecto 10 000) y `seed` (por defecto `None`; se puede fijar para reproducir).

**Aceptación:**
- **Dado** cada función **cuando** se llama sin `method` **entonces** usa `"numeric"`.
- **Dado** un `method` que la función no admite (p. ej. `"markov"` en la Shewhart, que es exacta) o desconocido **entonces**
  `ValueError` en español.
- **Dado** `"simulation"` con la misma `seed` **entonces** el resultado es idéntico; con `n_runs` grande, coincide con
  `"numeric"` dentro del error de Monte Carlo (≈ ARL/√n_runs).
- **Dado** `"numeric"` y `"markov"` **entonces** coinciden con la precisión declarada del método de celdas.

### S009-RF-05 — Entrada y casos borde

`ValueError` en español para parámetros inválidos y resultado coherente en los extremos.

**Aceptación:**
- `k <= 0`, `h <= 0`, `weight` fuera de `(0, 1]`, `L <= 0`, `headstart` fuera de `[0, h)`, `n_runs < 1`, o valores no
  finitos → `ValueError`.
- El ARL es simétrico en `shift` (carta bilateral): `arl(shift) == arl(−shift)`.
- El ARL decrece al crecer `|shift|` y tiende a 1; nunca baja de 1.
- `shift` como arreglo devuelve un arreglo (para dibujar la curva ARL frente al desplazamiento).

### S009-RF-06 — ARL de las cartas Shewhart de dispersión (S y R)

`arl_sd(n, ratio=1.0, k=3.0)` y `arl_range(n, ratio=1.0, k=3.0)`: ARL de las cartas S y R con los límites que usa pccpy
(`B3`, `B4` y `D3`, `D4` con `k = 3`), cuando la σ del proceso pasa a `ratio × σ₀` (`ratio = 1` es el ARL en control).

- S: `(n − 1)·S²/σ² ~ χ²(n − 1)` → fórmula cerrada con `scipy.stats.chi2`.
- R: distribución del rango de `n` normales con `scipy.stats.studentized_range(n, ∞)`.

**Aceptación:**
- **Dado** `n = 5`, `ratio = 1`, `k = 3` **entonces** el ARL de la S es ≈ 256,5 y el de la R ≈ 217,2 (calculados aparte con
  `scipy`; no son cifras de la literatura).
- **Referencia independiente:** fórmula cerrada con `scipy` y Monte Carlo con ≥ 20 semillas; `ratio > 1` da ARL menor.

### S009-RF-07 — ARL de las cartas Shewhart de atributos (NP/P y C/U)

`arl_binomial(n, p0, p1=None, k=3.0)` y `arl_poisson(c0, c1=None, k=3.0)`: ARL de las cartas NP (tamaño de muestra constante)
y C con límites `centro ± k·σ` (con el LCI recortado en 0) cuando el parámetro real pasa de `p0` a `p1` (o de `c0` a `c1`);
`p1 = None` da el ARL en control. La P y la U con tamaño constante se obtienen con `n` y `c0 = n·u0`. Con tamaños variables no
hay ARL único (fuera de alcance).

**Aceptación:**
- **Dado** `n = 100`, `p0 = 0,05` **entonces** el ARL en control es `1 / P(X > UCL o X < LCL)` con la binomial, calculado
  aparte con `scipy.stats.binom` (el ARL en control **no** es 370,4: la distribución es discreta y asimétrica).
- **Referencia independiente:** `scipy.stats.binom` y `scipy.stats.poisson` más Monte Carlo con ≥ 20 semillas.

### S009-RF-08 — ARL de las cartas G y T

`arl_g(p0, p1=None, k=3.0)` y `arl_t(shape, scale_ratio=1.0, k=3.0, distribution="weibull")`: ARL de las cartas G y T con
los límites que calcula pccpy (percentiles de la geométrica, de la Weibull o de la exponencial) cuando el parámetro real
cambia. G: `P(señal) = P(X > UCL)` con la geométrica; T: `P(T < LCL) + P(T > UCL)` con la Weibull/exponencial desplazada.

**Aceptación:**
- **Dado** `p0 = 0,02` y `k = 3` **entonces** el ARL en control es `1 / P(X > UCL)` con la geométrica, calculado aparte con
  `scipy.stats.geom`; con las cartas de pccpy los límites son los mismos que los de `g_chart`.
- **Dado** la T con `shape` y `scale_ratio = 1` **entonces** el ARL es `1 / (2·Φ(−3))` = 370,4 (los límites son los
  percentiles `Φ(±3)`).
- **Referencia independiente:** `scipy.stats.geom` y `scipy.stats.weibull_min`, más Monte Carlo.

### S009-RF-09 — Validación, documentación y exportación

**Aceptación:**
- Una comprobación por función en `run_validation()`, con referencia independiente y tolerancia justificada.
- El docstring de cada función dice qué se supone (normalidad o el modelo discreto, parámetros conocidos, sin pruebas
  suplementarias) y la precisión del método.
- Las funciones se exportan en `__init__.py` y `__all__`, con una página de la guía y un ejemplo ejecutable (curva ARL de la
  Shewhart, la EWMA y la CUSUM frente al desplazamiento).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `shift = 0` | ARL en control (ARL₀) |
| `shift` muy grande (≥ 10) | ARL → 1 |
| `shift` negativo | Igual que el positivo (carta bilateral) |
| `headstart` cercano a `h` | ARL menor; sin error |
| `weight = 1` en la EWMA | Igual que la Shewhart de RF-01 |
| `k` pequeño en la Shewhart | ARL cercano a 1; sin desbordes |
| `n = 2` en la R o la S | Válido (mínimo del subgrupo) |
| `p0` extremo en la G | ARL finito; sin desbordes |
| NaN o inf | `ValueError` |

## Resultados existentes que cambian

Ninguno. Funciones públicas nuevas.

## No verificable sin la fuente

Las cifras de la literatura (168, 8,38, 500, 570, 370,4, 43,9) las recuerdo y las cito de memoria: no pude consultar
Hawkins y Olwell (1998), Lucas y Saccucci (1990), Lucas y Crosier (1982), Brook y Evans (1972) ni Montgomery desde este
entorno. Cada una se respalda con un cálculo independiente (fórmula cerrada o Monte Carlo) y consta como «recordada de
memoria» (principio 12). Los ARL de la S, la R, la binomial, la Poisson y las G y T no tienen cifra de literatura citada:
salen de fórmulas cerradas con `scipy`. Tampoco se ha comparado con el ARL de Minitab.

## Decisiones de la persona responsable

1. **Alcance:** Shewhart, CUSUM y EWMA, y además todo lo que se pueda calcular con rigor: las cartas de dispersión (S y R),
   las de atributos (NP/P y C/U con tamaño constante) y las de eventos raros (G y T) quedan incluidas (RF-06 a RF-08).
   El agente propuso la lista; recortarla es decisión de la persona responsable al aprobar.
2. **Simulación:** el usuario elige entre el cálculo exacto o numérico y la simulación (`method`).
3. **API:** funciones paramétricas por carta (no una única `arl(chart)`).
4. **Subgrupos:** `shift` en σ del estadístico graficado; el usuario multiplica por √n.
5. **Método numérico:** ambos disponibles, ecuación integral con cuadratura y cadena de Markov con celdas; por defecto el
   método numérico (ecuación integral). *Interpretación del agente: «método numérico» = la ecuación integral; si se refería
   a otra cosa, se corrige.*
6. **Versión:** 0.15.4, junto con la leyenda de la CUSUM (spec 008).

## Preguntas abiertas

Ninguna.
