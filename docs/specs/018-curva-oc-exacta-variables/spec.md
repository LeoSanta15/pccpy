# 018 — Curva OC exacta de los planes por variables (distribución t no central)

- **Estado:** aprobada
- **Identificador:** S018
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.16.1 (cambia resultados existentes: `pa`, `alpha`, `ltpd` y `oc_curve` de los planes unilaterales; se publica como parche por decisión de la persona responsable, como la 0.15.8 y la 0.15.9)

## Problema

`SamplingPlanVariables.pa(p)` (y con él `oc_curve()`, `alpha`, `ltpd`, `plot()` y `summary()`) calcula la probabilidad de aceptación de un plan
**unilateral** con la aproximación normal de Montgomery (2013, sec. 15-3):

`Pa ≈ Φ[(z_p − k)·√n / √(1 + k²/2)]`, con `z_p = Φ⁻¹(1 − p)`.

La probabilidad exacta existe y es sencilla: con la Forma 1 se acepta si `Q = (U − x̄)/s ≥ k`, y `√n·Q` sigue una distribución **t no central** con
`n − 1` grados de libertad y parámetro de no centralidad `δ = z_p·√n`. Por tanto:

`Pa(p) = P( t'_{n−1}(δ = z_{1−p}·√n) ≥ k·√n )`

(derivación: `x̄ = μ + σZ/√n`, `s = σ·√(χ²_{n−1}/(n−1))`, `Z` y `s` independientes; `Q > k ⇔ (z_p√n − Z)/(s/σ) > k√n`).

La aproximación se queda corta con muestras pequeñas, que son las de las tablas de MIL-STD-414 (n = 3 a 200). Valores medidos aquí (aproximación → exacto):

| n | k | p | aproximación | exacto |
|---|---|---|---|---|
| 3 | 1,12 | 0,025 | 0,87296 | 0,89059 |
| 5 | 1,65 | 0,0065 | 0,88749 | 0,89884 |
| 10 | 1,41 | 0,025 | 0,89095 | 0,90011 |
| 35 | 1,89 | 0,010 | 0,93902 | 0,94167 |
| 35 | 1,89 | 0,050 | 0,19245 | 0,20892 |
| 100 | 2,00 | 0,010 | 0,97023 | 0,97075 |

Consecuencias: el riesgo del productor `alpha` (1 − Pa en el AQL) y el `ltpd` (la fracción defectuosa con Pa = 0,10) de un plan quedan algo desviados. Con el plan de `N=1000, aql=1,0` (n = 35, k = 1,89):
`alpha` 0,0610 → 0,0583 y `ltpd` 6,32 % → 6,50 %; con n = 3, k = 1,12 y AQL 2,5 % la diferencia en `alpha` es 0,127 → 0,109.

La docstring de `_pa_variables` ya reconoce que la fórmula unilateral es una aproximación; el caso bilateral con el proceso centrado ya es exacto (integral).

## Fuera de alcance

- **Bilateral con el proceso descentrado:** la integral bilateral actual supone el proceso centrado entre los límites; la OC con la media desplazada necesita otra parametrización y se hace aparte.
- **Forma 2** (estimar el porcentaje no conforme y compararlo con `M`), método del **rango** y variabilidad **conocida**: sin sus tablas (spec 017).
- **Cambiar cualquier plan de la tabla de MIL-STD-414** o la regla de decisión: no cambian `n`, `k` ni `evaluate`.
- Afirmar equivalencia con Minitab o con las tablas OC publicadas (Lieberman y Resnikoff, 1955): no se pudieron consultar.

## Requisitos

### S018-RF-01 — Probabilidad de aceptación unilateral exacta

`SamplingPlanVariables.pa(p)` con `spec_type="one"` devuelve `Pa(p) = P(t'_{n−1}(z_{1−p}·√n) ≥ k·√n)` (distribución t no central), y lo mismo la función interna que usan los planes a medida (`n=`, `k=`).

**Aceptación:**
- **Dado** un plan `(n, k)` y una malla de `p` en (0, 1) **entonces** `pa(p)` coincide con la integral numérica independiente `∫ Φ(√n·(z_p − k·s)) f_s(s) ds` (`f_s` = densidad de `s` con `n − 1` grados de libertad, escrita aparte con `scipy.integrate.quad`) con error relativo < 1e-9 para n ∈ {2, 3, 5, 10, 35, 75, 200}, k ∈ {−0,5; 0; 0,5; 1,5; 2,5} y p ∈ {1e-6, 1e-4, 0,0025, 0,01, 0,1, 0,3, 0,5, 0,9}.
- **Dado** un plan de la tabla (p. ej. n = 35, k = 1,89) **entonces** una simulación con ≥ 20 semillas (100 000 muestras normales cada una, regla `(U − x̄)/s ≥ k`) da una `Pa` media dentro de 3 errores estándar del valor exacto.
- **Referencia independiente:** la integral y la simulación anteriores. No contra la aproximación de Montgomery ni contra la salida de `pccpy` antes del cambio.

### S018-RF-02 — `alpha` y `ltpd` con la OC exacta

`alpha = 1 − Pa(AQL)` y `ltpd` (la `p` con `Pa = 0,10`, por búsqueda de raíz) se calculan con la `Pa` exacta, tanto en los planes de la tabla como en los a medida.

**Aceptación:**
- **Dado** `acceptance_sampling_variables(1000, 1.0)` (n = 35, k = 1,89) **entonces** `alpha = 0,05833` y `ltpd = 6,50 %` (±1e-4 relativo; valores de la integral independiente).
- **Dado** un plan cuya `Pa(AQL) < 0,10` **entonces** `ltpd` es `nan` (como hoy, sin lanzar).
- **Dado** `oc_curve()` **entonces** `P(aceptar)` es no creciente en `p`, empieza en 1 y está en [0, 1].

### S018-RF-03 — Casos extremos sin ruido numérico

`Pa(0) = 1`, `Pa(1) = 0`; sin `RuntimeWarning` ni `nan` para `n` grande (hasta 2 000), `p` muy pequeña (1e-12) o `k` negativa o cero.

**Aceptación:**
- **Dado** esos casos **entonces** el resultado es finito, está en [0, 1] y no emite avisos (`warnings.simplefilter("error")`).
- **Dado** n = 2 (un grado de libertad) **entonces** coincide con la integral independiente.

### S018-RF-04 — La OC bilateral no cambia

`spec_type="two"` conserva la integral exacta con el proceso centrado.

**Aceptación:** `pa(p)` de un plan bilateral a medida coincide con su valor actual (cálculo independiente por simulación ≥ 20 semillas, no con la salida anterior). Pasa antes del código (protege lo que no cambia).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `p = 0` o `p = 1` | 1 y 0 exactos |
| `n = 2` | 1 grado de libertad; coincide con la integral |
| `k ≤ 0` | válido; `Pa ≥ 0,5` en el caso `k = 0` con `p ≤ 0,5` |
| `n` muy grande (2 000) | sin aviso ni `nan` |
| `p` muy pequeña (1e-12) | `δ` grande: finito y sin aviso |
| Plan bilateral | sin cambios (RF-04) |

## Resultados existentes que cambian

Cambian `pa`, `oc_curve`, `alpha`, `ltpd`, el gráfico OC y `summary()` de **todos los planes unilaterales**, con diferencias de 0,0005 a 0,018 en la `Pa` en los ejemplos medidos (mayores con muestras pequeñas). Ejemplo: `acceptance_sampling_variables(1000, 1.0)`: `alpha` 0,0610 → 0,0583 y `ltpd` 6,32 % → 6,50 %. No cambian `n`, `k`, la letra de código ni `evaluate`. Se regeneran los goldens (`oc_variables`, `muestreo_variables`) y se listan en «Cambios que alteran resultados» del CHANGELOG.

## No verificable sin la fuente

- No se pudieron consultar las tablas OC publicadas de Lieberman y Resnikoff (1955) ni las curvas de MIL-STD-414: la referencia es la integral numérica independiente y la simulación, no la norma.
- La exactitud de `scipy.stats.nct` en las versiones mínimas declaradas (scipy 1.9) no se midió: la medida de este borrador usa scipy 1.18 (acuerdo con la integral de 4·10⁻¹⁴ en la malla anterior). Lo vigila el trabajo `versiones-minimas` del CI.

## Preguntas abiertas

Ninguna. Decididas por la persona responsable (con las recomendaciones de la propuesta):

1. **Cálculo:** `scipy.stats.nct.sf` directamente. Si el CI en scipy 1.9 (versiones mínimas) mostrara diferencias con la integral, se vuelve a la integral para todo. Alternativa descartada: la integral en todos los casos (más lenta).
2. **Versión:** 0.16.1 (parche), aunque cambian `alpha`, `ltpd` y la curva de todos los planes unilaterales; así lo decide la persona responsable (la recomendación era 0.17.0). Se avisa igualmente en «Cambios que alteran resultados» del CHANGELOG. Alternativa descartada: versión menor 0.17.0.
3. **OC bilateral con el proceso descentrado:** fuera de alcance (hoy no existe y requiere parametrizar la media). Alternativa descartada: añadirla aquí con un argumento `shift=`.
