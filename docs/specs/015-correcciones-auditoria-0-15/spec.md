# 015 — Correcciones de la auditoría estadística 0.15

- **Estado:** implementada
- **Identificador:** S015
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.16.0 (cambia resultados existentes: versión menor)

## Problema

Una auditoría estadística de la 0.15.7 (cuatro revisiones independientes: cartas univariadas, capacidad y normalidad, MSA/tolerancia/muestreo,
multivariadas y ARL) encontró errores que dan **resultados numéricos incorrectos sin aviso**. Cada hallazgo se contrastó contra una referencia
independiente (fórmula escrita aparte, `scipy`/`statsmodels` o Monte Carlo con ≥ 20 semillas) y los de gravedad alta y media se reprodujeron
una segunda vez. Las áreas no mencionadas aquí (constantes, pruebas 2 a 8, T²/MEWMA/MCUSUM, todo el ARL, índices de capacidad, Anderson-Darling,
bootstrap, atípicos Grubbs/ESD/Dixon, Gage R&R por ANOVA, tolerancia) coincidieron con sus referencias.

Esta especificación recoge las correcciones, ordenadas por gravedad. No se pudo contrastar nada con Minitab real: donde una convención de Minitab
está en juego se dice y se decide con la persona responsable.

## Fuera de alcance

- Sustituir las tablas Z1.9/Z1.4 (deuda conocida, sin acceso a la norma).
- Afirmar equivalencia con Minitab.
- Funciones nuevas (por ejemplo, curvas OC hipergeométricas): se anotan como mejoras posibles, no como correcciones.

## Requisitos

### Gravedad alta

### S015-RF-01 — EWMA-P y EWMA-U con tamaño de muestra variable

La varianza del estadístico EWMA con `n` variable es `Vᵢ = (1−λ)²·Vᵢ₋₁ + λ²·σ²(nᵢ)` (con `V₀ = 0`); los límites exactos usan `√Vᵢ`. Hoy se usa
`σ(nᵢ)·√(λ/(2−λ)·(1−(1−λ)^{2i}))`, válida solo con `n` constante. Con `n` constante el resultado no cambia.

**Aceptación:**
- **Dado** `n` alternando 30 y 600 con `p=0.1` y `λ=0.2` **entonces** `panel.sigma` coincide con la recursión escrita aparte (rel. 1e-12) y la tasa de falsas
  alarmas por punto, con 20 semillas, es ≈ 0,0027 (hoy 0,152).
- **Dado** `n` constante **entonces** los límites son idénticos a los de 0.15.7.
- **Referencia independiente:** la recursión de la varianza de un EWMA (Montgomery §9.2 con varianzas distintas por punto) y simulación.

### S015-RF-02 — Dodge-Romig: ATI y AOQL

El ATI es `n + (1−Pa)·(N−n)` (los lotes rechazados se inspeccionan al 100 %); hoy se usa `Pa`. El plan por AOQL debe cumplir `AOQL ≤ objetivo`
(sin la tolerancia de +5 %), con el AOQL del plan calculado como máximo exacto de `Pa(p)·p·(N−n)/N` (no por una rejilla de 400–500 puntos).

**Aceptación:**
- **Dado** `dodge_romig(1000, ltpd=0.05, process_avg=0.01)` **entonces** el plan es n=132, c=3 (ATI 170,4), igual que la búsqueda exhaustiva escrita aparte (hoy n=45, c=0, ATI 392).
- **Dado** `dodge_romig(5000, aoql=0.02, process_avg=0.01)` **entonces** el AOQL real del plan es ≤ 0,02 y su ATI coincide con el de la búsqueda exhaustiva.
- **Dado** `acceptance_sampling_attributes(50000, 0.01)` **entonces** el AOQL es 0,000287 (exacto), no 0,000255.
- **Referencia independiente:** definición de ATI y AOQ de Montgomery cap. 15, búsqueda exhaustiva con `scipy.stats.binom`.

### S015-RF-03 — Carta de corridas con empates

La prueba de tendencias (rachas arriba/abajo) descarta las diferencias nulas pero usa `E = (2n−1)/3` y `V = (16n−29)/90` con la `n` original. Con empates,
`n` pasa a ser el número de puntos que quedan tras quitar las diferencias nulas (`m + 1`).

**Aceptación:**
- **Dado** datos normales redondeados a la unidad, `n = 30` **cuando** se repite 20 semillas × 500 **entonces** `P(p_trends < 0,05) ≤ 0,07` (hoy 0,38; con datos continuos 0,03).
- **Dado** datos sin empates **entonces** el resultado no cambia.
- Decidido por la persona responsable: con empates, `n` pasa a `m + 1`. Minitab podría hacer otra cosa; no se pudo verificar.

### S015-RF-04 — Prueba de tendencia de `diagnose()` y `wizard()`

La regla actual («más del 80 % o menos del 20 % de las diferencias son positivas», llamada «Mann-Kendall simplificado») casi no detecta tendencias: potencia 0 con
pendientes de 0,1 a 0,5 σ por observación en n = 50, y falsas alarmas del 33 % con n = 3. Se sustituye por la prueba de Mann-Kendall (τ de Kendall contra el índice
con `scipy.stats.kendalltau`, α = 0,05, bilateral), con un mínimo de observaciones para aplicarla.

**Aceptación:**
- **Dado** una deriva total de 3σ en n = 20 y 50 **entonces** la detección es ≥ 90 % y 100 % (hoy 0 %).
- **Dado** datos iid con n = 20, 50 y 100 **entonces** la tasa de falsas alarmas es ≈ 5 % (≤ 7 %).
- **Dado** n < 8 (mínimo propuesto) **entonces** no se evalúa la tendencia y no hay aviso falso; `wizard` con n = 2 o 3 no recomienda `run_chart` por esa causa.
- Decidido por la persona responsable: Mann-Kendall, con un mínimo de 8 observaciones. Cambia las recomendaciones de `diagnose()`/`wizard()`.

### S015-RF-05 — p-valor del kappa de Cohen

El error estándar bajo H₀ es el de Fleiss, Cohen y Everitt (1969), no `√(pₑ/(n(1−pₑ)))`. Hoy la tasa de rechazo bajo H₀ al 5 % es 0,13 % (marginales 85/15, n = 100) y el error estándar sale
1,15 a 1,38 veces mayor con 3 categorías.

**Aceptación:**
- **Dado** marginales 85/15 y `n = 100` **entonces** la tasa de rechazo bajo H₀ (20 semillas × 300) es 0,05 ± 0,01 y el error estándar coincide con `statsmodels.stats.inter_rater.cohens_kappa(...).std_kappa0`.
- **Dado** el valor de kappa **entonces** no cambia.
- Decidido por la persona responsable: error estándar de FCE (1969). Minitab podría usar otro; no se pudo verificar.

### Gravedad media

### S015-RF-06 — `capability_boxcox` con NaN y subgrupos

`capability_boxcox` quita los NaN antes de agrupar con `subgroup_size=`, así que los subgrupos posteriores a un hueco se desplazan. Debe conservar el hueco como `capability_analysis(..., transform="boxcox")` (vía `to_subgroups`).

**Aceptación:**
- **Dado** 10 subgrupos de 5 con un NaN en la posición 2 **entonces** `capability_boxcox(...).sigma_within` coincide con la sigma agrupada con `c4(gl+1)` calculada aparte (0,1897 en el ejemplo de la auditoría; hoy 0,3012) y con `capability_analysis(..., transform="boxcox")`.

### S015-RF-07 — Capacidad con individuales y huecos

El rango móvil de `capability_analysis` no debe cruzar un hueco (decisión S006-RF-06, ya aplicada en `imr_chart`): `σ_within` se calcula igual que en la carta I-MR, también con `'mssd'` y `'median_mr'`.

**Aceptación:**
- **Dado** `y = [10, 10.2, nan, 14, 14.1, 13.9, 10.1, 10, 9.9, 10.2]` **entonces** `sigma_within = 0,6077 = nanmean(|diff|)/d2(2)` (hoy 0,9527) y coincide con `imr_chart(y).params[0]["sigma"]`.

### S015-RF-08 — Último subgrupo incompleto en EWMA, CUSUM y MA

El punto del último subgrupo incompleto debe usar su `nᵢ` real para la sigma del estadístico (`σ/√nᵢ`), como `xbar_r_chart`.

**Aceptación:**
- **Dado** `cusum_chart(x, subgroup_size=5, sigma=1, target=0)` con 101 observaciones **entonces** `panel.sigma[-1] = 1,0` (hoy 0,447); igual en `ewma_chart` y `ma_chart`.
- **Dado** subgrupos completos **entonces** no cambia.

### S015-RF-09 — `phase_one(..., center="median")` y `phase2()`

`phase_one` congela `mu` y `phase2()` vuelve a pasar `mu` y `center="median"`, que `resolve_center` rechaza. Con `mu` congelado, `phase2()` y `from_limits()` no deben pasar `center` (el centro ya es el congelado).

**Aceptación:**
- **Dado** `r = phase_one(imr_chart, x, center="median")` **entonces** `r.phase2(x_nuevos)` devuelve la carta con el mismo centro congelado, y lo mismo con `xbar_r_chart` y `from_limits(..., center="median")`.
- **Dado** archivos de Fase I guardados antes **entonces** se siguen leyendo.

### S015-RF-10 — `gage_rr(..., tolerance=)`

El parámetro `tolerance` no tiene efecto aunque el docstring y el README lo prometen. Se calcula `%Tolerancia = 100·(study_variation·σ)/T` para repetibilidad, reproducibilidad y Gage R&R total.

**Aceptación:**
- **Dado** `gage_rr(..., tolerance=5.0)` **entonces** `to_frame()` y `summary()` incluyen `%Tolerancia` (= `100·6σ_GRR/T` con `study_variation = 6`) y sin `tolerance` no aparece.
- Decidido por la persona responsable: se implementa `%Tolerancia` (no se quita el parámetro).

### S015-RF-11 — %Linealidad y %Sesgo (AIAG)

`%Linealidad = 100·|pendiente|` (Linealidad = |pendiente|·variación del proceso), `%Sesgo = 100·|sesgo medio|/variación del proceso` (AIAG MSA 3.ª ed.). Hoy el denominador es `6·s_residual`, que mide el instrumento, no el proceso.

**Aceptación:**
- **Dado** pendiente −0,117 **entonces** `%Linealidad = 11,7 %` (hoy 84,3 %) cuando la variación del proceso se da o se estima de los datos como en AIAG.
- Decidido por la persona responsable: definición de AIAG. `%Linealidad = 100·|pendiente|` no necesita parámetro nuevo; `%Sesgo` sí (variación del proceso, opcional). No se pudo comprobar la fórmula de Minitab.

### S015-RF-12 — Carta |S| (varianza generalizada)

Los límites `b1 ± k√b2` (aproximación normal, Montgomery 11.3) dan `P(|S| > LCS) ≈ 0,0197` (ARL₀ ≈ 50), unas 7 veces la nominal 0,00135 (con `k = 3`), y el LCI queda en 0.

**Aceptación:**
- **Dado** `generalized_variance_chart(..., k=3)` **entonces** los límites se calculan por percentiles de la distribución de `|S|` con `P(|S| > LCS) = 0,00135` (± 5 %), y el docstring y el README describen el método.
- Decidido por la persona responsable: percentiles exactos de la distribución de `|S|` (el método se documenta en el docstring y el README).

### Gravedad baja

### S015-RF-13 — Casos borde y validación de entrada

- **Prueba 1 con sigma = 0:** un punto fuera de un LCS = 0 debe marcarse (`z = ±inf` no se descarta como inválido); `p_chart` valida `0 < p < 1` (o avisa con `p = 0`).
- **`precontrol` con NaN:** pasa por `as_1d` (R-09); un NaN no es «verde».
- **`gage_rr` con NaN o con 1 operador:** `ValueError` claro en vez de NaN en silencio.
- **LTPD de planes a medida:** no sale NaN cuando `Pa(AQL) < 0,10` (la búsqueda parte de un punto más alto).

**Aceptación:** un test de regresión por caso (falla con el código actual): `imr_chart([5]*7+[9,5,5], sigma=0.0)` marca el 9; `precontrol([10, nan, 10], 0, 20).zones` no devuelve `['G','G','G']`; `gage_rr` con NaN lanza `ValueError`; `LTPD(n=200, c=5, AQL=0.10)` = 0,0459.

### S015-RF-14 — Estimadores y aproximaciones

- **`sigma_method="mssd"`:** sesgado hacia abajo (E[σ̂]/σ = 0,962 con n = 10); se divide por `c_mssd(n) = E[√(MSSD/2)]/σ`, calculada exactamente con la forma cuadrática del estadístico y contrastada con Monte Carlo.
- **Curva OC de variables bilateral:** `Pa(p/2)²` se queda corta (0,451 frente a 0,495 ± 0,004 por Monte Carlo con n = 20, k = 1,5, p = 0,10); se calcula con la distribución correcta o se documenta la aproximación.
- **Repetibilidad del acuerdo por atributos:** no promediar p-valores de pares (no es una prueba válida).
- **Atípicos IQR de `diagnose()`:** marca al menos uno en el 52 % de las muestras normales de n = 100 (95 % con n = 500); se ajusta la redacción («posibles atípicos según la regla del IQR»), sin cambiar el conteo.

**Aceptación:** el comportamiento queda corregido o documentado en cada caso, con su test (`'mssd'` con `E[σ̂]/σ = 1,000 ± 0,003` en 20 semillas); `diagnose()` ya no afirma «investiga su origen» solo por la regla del IQR con n grande.
- Decidido por la persona responsable: `mssd` se **corrige** con una constante de insesgamiento `c_mssd(n)` (cambia el resultado de `'mssd'`; Minitab podría usar otra y no se pudo verificar); en el IQR de `diagnose()` se **cambia la redacción** (el conteo no cambia).

### S015-RF-15 — Documentación

- Sección «Notas sobre diferencias posibles con Minitab» en `README.md` y `README_en.md` (R-02): Johnson por máxima verosimilitud frente al método de percentiles de Chou, Box-Cox, covarianza de T² en Fase I con individuales (clásica, no de diferencias sucesivas), covarianza asintótica de la MEWMA, kappa entre evaluadores y su repetibilidad, tendencia de `diagnose`, `mssd`.
- Los comentarios de `DiagnoseResult` dicen «Anderson-Darling» y el código usa D'Agostino K²: se corrigen.
- `wizard()` llama a `normaltest` sin la guardia de n < 8 que sí tiene `diagnose()` (posible regresión de BUG-10 con scipy 1.9): se añade la guardia y se prueba con la versión mínima del CI.
- La regla 2-D del `wizard` mezcla «columnas = tamaño de subgrupo» con «columnas = variables»: se aclara la pregunta o la regla.

**Aceptación:** `sphinx-build -W` sin avisos; el job `versiones-minimas` pasa un test de `wizard` con 3 ≤ n ≤ 7 sin tendencia.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `n` constante en EWMA-P/U | Idéntico a 0.15.7 |
| Datos de carta de corridas sin empates | Idéntico a 0.15.7 |
| Subgrupos completos en EWMA/CUSUM/MA | Idéntico a 0.15.7 |
| Dodge-Romig sin plan que cumpla | Error o aviso claro (como hoy), no un plan que viole el objetivo |
| `diagnose` con n < 8 | Sin prueba de tendencia, sin avisos de scipy |
| Archivos de Fase I de 0.15.x | Se siguen leyendo |

## Resultados existentes que cambian

Cambian (versión 0.16.0, a listar en «Cambios que alteran resultados»): límites de EWMA-P/U con `n` variable; planes y AOQL de Dodge-Romig y AOQL de Z1.4; p-valor de tendencias de la carta de corridas con empates;
`has_trend` de `diagnose()`/`wizard()` y sus recomendaciones; p-valor del kappa de Cohen; sigma dentro y capacidad con huecos (`capability_boxcox`, individuales); sigma del último subgrupo incompleto en EWMA/CUSUM/MA;
%Linealidad/%Sesgo y, según las decisiones, límites de |S| y `%Tolerancia`. Con datos sin los casos descritos no cambia nada.

## No verificable sin la fuente

- Minitab: la fórmula del error estándar del kappa, del tratamiento de empates en la carta de corridas, de %Linealidad/%Sesgo, de la constante del `mssd`, del límite de |S| y de la tendencia de `diagnose` (no tiene equivalente).
- AIAG MSA 3.ª ed.: la definición de %Linealidad y %Sesgo está recordada de memoria; se contrasta con un cálculo escrito aparte, no con el manual.

## Preguntas abiertas

Ninguna. Decididas por la persona responsable: empates con `m + 1` (RF-03), Mann-Kendall con mínimo de 8 observaciones (RF-04), error estándar de FCE (RF-05), `%Tolerancia` implementado (RF-10), AIAG (RF-11), percentiles exactos de `|S|` (RF-12), `mssd` corregido e IQR con otra redacción (RF-14) y una sola especificación con versión 0.16.0.
