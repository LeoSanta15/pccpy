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
| Con especificaciones y distribución no normal | `capability_boxcox` |
| Sin especificaciones | `imr_chart` |

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
| `recommended_function` | `str` | Nombre de la función recomendada. |
| `recommended_snippet` | `str` | Código listo para copiar. |
| `issues` | `list[str]` | Lista de alertas (distribución, tendencia, capacidad). |
| `lsl`, `usl`, `target` | `float \| None` | Especificaciones pasadas. |
| `cp`, `cpk` | `float \| None` | Índices de capacidad estimados (requieren `lsl` y `usl`). |
