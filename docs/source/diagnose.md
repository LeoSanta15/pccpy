# Diagnóstico rápido (`diagnose`)

`pp.diagnose()` analiza un vector de datos de proceso y devuelve un
{class}`~pccpy.DiagnoseResult` con estadísticos descriptivos, prueba de
normalidad, detección de tendencia, valores atípicos y una recomendación de
qué función usar a continuación.

Es el punto de partida ideal cuando no sabes aún qué análisis aplicar.

---

## Uso básico

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(0)
x = rng.normal(50, 2, 60)

d = pp.diagnose(x, lsl=44, usl=56)
print(d.summary())
```

Salida (extracto):

```
════════════════════════════════════════════════════════════
  DIAGNÓSTICO RÁPIDO DEL PROCESO
════════════════════════════════════════════════════════════
  N               : 60
  Media           : 50.0824
  Desv. estándar  : 1.9978
  CV              : 3.97 %
  Mínimo / Máximo : 45.2671  /  54.1569
  Mediana         : 50.1632
  Asimetría       : 0.0531
  Curtosis        : -0.1987

  ── Normalidad (prueba de normalidad) ──
  Estadístico     : 0.1843
  Valor p         : 0.9120
  Distribución    : Normal (p > 0.05)

  ── Análisis recomendado ──
  Función : capability_analysis
  ...
════════════════════════════════════════════════════════════
```

---

## Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `x` | array-like | Vector 1-D de observaciones del proceso. |
| `lsl` | `float`, opcional | Límite de especificación inferior (LEI). |
| `usl` | `float`, opcional | Límite de especificación superior (LES). |
| `target` | `float`, opcional | Valor objetivo (nominal). |

Requiere al menos **4 observaciones**.

---

## Gráfico rápido

```python
d = pp.diagnose(x, lsl=44, usl=56)
fig = d.plot()
fig.show()
```

El gráfico incluye:

- **Histograma** con curva normal ajustada, líneas de especificación (LEI/LES)
  y valor objetivo.
- **Gráfico de secuencia** con la media marcada y los valores atípicos
  resaltados en rojo.

---

## Qué analiza

### Estadísticos básicos

N, media, desviación estándar, CV, mínimo, máximo, mediana, asimetría y curtosis.

### Normalidad

Prueba de normalidad (`scipy.stats.normaltest`). Un valor p > 0.05 indica
distribución aproximadamente normal.

> Con menos de 8 observaciones la prueba no es válida; `diagnose` devuelve
> `is_normal = True` y `normality_p = nan` en ese caso.

#### Por qué no es normal

Si la prueba rechaza la normalidad, `diagnose` estudia la causa (`non_normal_reason`):

- `'outliers'`: hay algún punto muy lejano (a más de 3·RIC de los cuartiles) y sin los atípicos los datos son normales y
  simétricos. Conviene investigar esos puntos antes de transformar nada.
- `'skewed'`: la asimetría es marcada (|asimetría| ≥ 0,5). `transform_normalizes` dice si Box-Cox (solo con datos
  positivos) deja los datos normales y `best_distribution` da la distribución de menor AIC si mejora a la normal en más
  de 2 puntos (lognormal, Weibull, gamma o log-logística con datos positivos; logística o valores extremos si no).
- `'shape'`: no normal sin asimetría marcada (colas pesadas, varias modas…).

La causa es una heurística: en simulación acierta ≈ 98 % con datos lognormales y ≈ 96 % con una normal contaminada con
tres atípicos lejanos; con asimetría muy leve puede confundirla con atípicos.

### Pruebas formales de atípicos

`diagnose` marca los atípicos con la regla de Tukey (IQR × 1,5), que es descriptiva. Para una prueba de hipótesis usa
`outlier_test`:

```python
r = pp.outlier_test(x)                        # Grubbs: un atípico (el más extremo)
r = pp.outlier_test(x, method="esd")          # ESD generalizada de Rosner: hasta max_outliers atípicos
r.outlier_indices, r.outlier_values, r.to_frame(), r.summary()
pp.outlier_test(x, sides="upper")             # solo valores demasiado altos (o "lower")
```

| Método | Contrasta | Cuándo |
|---|---|---|
| `"grubbs"` | un solo atípico | muestras pequeñas con a lo sumo un punto sospechoso |
| `"esd"` | hasta `max_outliers` (por defecto `min(10, (n − 1) // 2)`) | varios sospechosos; evita que se enmascaren entre sí (conviene `n ≥ 25`) |

Los valores críticos se verificaron contra la tabla publicada de Grubbs y contra el ejemplo de Rosner (1983) del manual
del NIST. Con datos normales Grubbs marca ≈ 5 % de las muestras, el nivel nominal.

```{warning}
Ambas pruebas **suponen que los datos sin los atípicos son normales** (el resultado incluye el valor p de Shapiro-Wilk
de los datos restantes y avisa si es < 0,05). Declarar un punto atípico **no justifica eliminarlo**: investiga su origen.
Con datos de proceso ordenados en el tiempo, usa las cartas de control y sus pruebas de causas especiales. No se
recomienda elegir el método de análisis posterior según el resultado de esta prueba: distorsiona la cobertura de los
intervalos.
```

### Tendencia

Detección simplificada basada en el porcentaje de incrementos consecutivos:
más del 80 % indica tendencia creciente; menos del 20 %, decreciente.

### Valores atípicos

Método IQR × 1.5: puntos por debajo de Q1 − 1.5·IQR o por encima de
Q3 + 1.5·IQR.

### Cp y Cpk estimados

Si se proporcionan `lsl` y/o `usl`, se calculan los índices de capacidad
preliminares:

```
Cp  = (USL − LSL) / (6 · s)
Cpk = min(USL − x̄, x̄ − LSL) / (3 · s)
```

---

## Recomendación automática

| Condición | Función recomendada |
|-----------|---------------------|
| Tendencia detectada | `run_chart` |
| Con especificaciones y distribución normal | `capability_analysis` |
| Con especificaciones, no normal por valores atípicos | `capability_analysis` (y alerta para investigarlos) |
| Con especificaciones, no normal y Box-Cox normaliza (datos, límites y objetivo positivos) | `capability_boxcox` |
| Con especificaciones, no normal y una distribución gana a la normal por AIC | `capability_nonnormal(distribution=…)` |
| Con especificaciones, no normal y sin un modelo claramente mejor | `capability_analysis` (con aviso de cautela y `ci_method='bootstrap'`) |
| Sin especificaciones | `imr_chart` (con aviso si los datos son asimétricos) |

---

## Referencia de `DiagnoseResult`

```{eval-rst}
.. autoclass:: pccpy.DiagnoseResult
   :members: summary, plot
   :undoc-members:
   :no-index:
   :exclude-members: lsl, usl, target, cp, cpk, n, mean, std, cv,
                     min_val, max_val, median, skewness, kurtosis,
                     normality_stat, normality_p, is_normal,
                     has_trend, trend_direction, outlier_count,
                     outlier_indices, recommended_function,
                     recommended_snippet, issues
```

### Atributos principales

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `n` | `int` | Número de observaciones. |
| `mean`, `std` | `float` | Media y desviación estándar muestrales. |
| `cv` | `float` | Coeficiente de variación (%). |
| `min_val`, `max_val` | `float` | Mínimo y máximo. |
| `median` | `float` | Mediana. |
| `skewness`, `kurtosis` | `float` | Asimetría y curtosis (exceso). |
| `normality_stat`, `normality_p` | `float` | Estadístico y valor p de la prueba de normalidad. |
| `is_normal` | `bool` | `True` si `normality_p > 0.05`. |
| `has_trend` | `bool` | `True` si se detectó tendencia. |
| `trend_direction` | `str` | `'creciente'`, `'decreciente'` o `''`. |
| `outlier_count` | `int` | Número de valores atípicos detectados (IQR). |
| `outlier_indices` | `list[int]` | Índices de los valores atípicos. |
| `non_normal_reason` | `str` | `'outliers'`, `'skewed'`, `'shape'` o `''` (si es normal). |
| `transform_normalizes` | `bool \| None` | ¿Box-Cox normaliza los datos? `None` si no aplica. |
| `best_distribution` | `str \| None` | Distribución de menor AIC si gana a la normal. |
| `recommended_function` | `str` | Nombre de la función recomendada. |
| `recommended_snippet` | `str` | Código listo para copiar. |
| `issues` | `list[str]` | Lista de alertas (distribución, tendencia, capacidad). |
| `lsl`, `usl`, `target` | `float \| None` | Especificaciones pasadas. |
| `cp`, `cpk` | `float \| None` | Índices de capacidad estimados (requieren `lsl` y `usl`). |
