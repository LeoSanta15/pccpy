# Datos asimétricos y no normales

La mayoría de las herramientas de control de calidad suponen datos normales. Cuando no lo son, `pccpy` ofrece tres caminos:
**diagnosticar** por qué, **transformar** los datos hasta que sean casi normales y **calcular la incertidumbre sin suponer
normalidad** (bootstrap). Esta guía dice cuál usar en cada caso.

## 1. Primero, diagnosticar

```python
import pccpy as pp

d = pp.diagnose(x, lsl=44, usl=56)
print(d.summary())
d.non_normal_reason        # 'outliers', 'skewed' o 'shape' ('' si es normal)
d.recommended_snippet      # el fragmento que recomienda, listo para ejecutar
```

| `non_normal_reason` | Qué significa | Qué hacer |
|---|---|---|
| `'outliers'` | hay puntos muy lejanos y sin ellos los datos son normales | investigarlos antes de transformar nada |
| `'skewed'` | asimetría marcada (\|asimetría\| ≥ 0,5) | transformar (sección 2) o ajustar una distribución |
| `'shape'` | no normal sin asimetría marcada (colas pesadas, varias modas) | ajustar una distribución o usar intervalos bootstrap |

La causa es una heurística, no un veredicto (en simulación acierta ≈ 98 % con datos lognormales y ≈ 96 % con una normal
contaminada con atípicos lejanos). `diagnose` también dice si Box-Cox o Yeo-Johnson dejan los datos normales y qué
distribución ajusta mejor por AIC.

## 2. Transformar: `transform=`

| `transform` | Datos | Cuándo |
|---|---|---|
| `'boxcox'` | estrictamente positivos (y límites positivos) | asimetría moderada con datos positivos |
| `'yeo-johnson'` | cualquier valor | lo mismo, pero con ceros o negativos |
| `'johnson'` | cualquier valor | formas que los anteriores no normalizan (elige SU, SB o SL) |

```python
# capacidad: índices en la escala transformada; límites, objetivo y PPM observado en unidades originales
pp.capability_analysis(x, lsl=44, usl=56, transform="yeo-johnson")

# cartas de control: límites y pruebas en la escala transformada; el panel I (o X̄) se dibuja en unidades originales
carta = pp.imr_chart(x, transform="yeo-johnson")                      # scale="transformed" lo deja todo transformado
pp.xbar_r_chart(g, transform="boxcox")
nueva = pp.imr_chart(x_nuevos, transform=carta.transformation,        # la misma transformación para datos nuevos
                     mu=carta.params[0]["media"], sigma=carta.params[0]["sigma"])
```

En una carta con transformación los límites quedan **asimétricos** en unidades originales, y los paneles de dispersión
(MR, R, S) se quedan en la escala transformada porque su valor no tiene equivalente en unidades originales. En simulación
(datos lognormales, σ = 0,8, bajo control) la carta I normal marca ≈ 1,9 % de puntos por encima del límite superior; con
`transform="boxcox"`, ≈ 0,3 %.

## 3. Ajustar una distribución en vez de transformar

```python
pp.capability_nonnormal(x, lsl=44, usl=56, distribution="weibull")   # lognormal, gamma, loglogistic, …
```

Calcula los índices por percentiles de la distribución ajustada. Úsala cuando una distribución conocida describe bien el
proceso (tiempos de vida, concentraciones…). `diagnose` indica la de menor AIC.

## 4. Incertidumbre sin suponer normalidad: bootstrap

Los intervalos clásicos (t de Student, chi-cuadrado, Bissell) pierden cobertura con datos asimétricos, sobre todo los de la
desviación estándar y los de Pp.

```python
pp.capability_analysis(x, lsl=44, usl=56, ci_method="bootstrap", seed=1)       # intervalos de Pp y Ppk
pp.capability_nonnormal(x, lsl=44, usl=56, distribution="weibull", ci_method="bootstrap", seed=1)
pp.bootstrap_summary(x, seed=1)           # media, mediana y desviación estándar, con el intervalo clásico al lado
pp.bootstrap_ci(x, np.var, vectorized=True, seed=1)   # cualquier otro estadístico
```

| Caso (simulación) | Intervalo clásico | Bootstrap BCa |
|---|---|---|
| Desviación estándar, gamma(2), n = 60 | ≈ 83 % | ≈ 92 % |
| Pp, gamma(2), n = 150 | ≈ 81 % | ≈ 92 % |
| Ppk, gamma(2), n = 150 | ≈ 88 % | ≈ 91 % |
| Media, gamma(2), n = 60 | razonable (teorema central del límite) | comparable, no mejor |

Cobertura nominal 95 %. Para la media el intervalo t ya aguanta bien; el bootstrap aporta sobre todo en la desviación
estándar y en los índices de capacidad.

## 5. Subgrupos pequeños

Con subgrupos de 5 observaciones o menos y datos asimétricos, las medias no se aproximan a la normal y los límites de
Xbar-R/S pueden dar falsas alarmas. La librería avisa; la solución es `transform=` (sección 2).

## Límites y precauciones

- `phase_one(..., transform="yeo-johnson")` (solo en I-MR, Xbar-R y Xbar-S) reajusta la transformación en cada pasada con los puntos que se conservan y congela la de la última para `phase2()`, junto con `mu` y `sigma` (en la escala transformada). Avisa si lambda cambia más de 0,5 entre la primera y la última pasada: la Fase I no es estable. Con una `Transformation` ya ajustada no se reajusta.
- **Detección de puntos con causa especial en la Fase I con transformación.** La transformación se ajusta por máxima verosimilitud en la primera pasada con *todos* los datos, así que un atípico muy grande tira de lambda y queda más disimulado. En simulación (100 datos, dos puntos multiplicados por 20, 100 repeticiones) la Fase I encontró los dos puntos en el 12 % (lognormal) y el 65 % (Weibull) de los casos con Yeo-Johnson, y en el 100 % y el 94 % sin transformar. A cambio, sin transformar la prueba 1 da falsas alarmas en la Fase II del 5,0 % (lognormal) y del 2,1 % (Weibull) frente al 0,27 % nominal; con la transformación quedan en 0,2 % y 0,1 %. Si sospechas de atípicos extremos, investígalos antes con `outlier_test()` o `diagnose()`, o pasa una `Transformation` ajustada a datos que ya conoces bajo control.
- Con `transform=` y `ci_method="bootstrap"` los parámetros de la transformación se mantienen fijos en los remuestreos
  (el intervalo no recoge su incertidumbre). Con Johnson SB o SL un límite fuera del soporte no puede superarse: los
  índices salen infinitos.
- El bootstrap también pierde cobertura con muestras pequeñas: avisa con n < 20. En `capability_nonnormal` es más lento
  (un ajuste por remuestreo): 1000 remuestreos y método percentil por defecto.
- Una transformación no arregla datos con atípicos o varias poblaciones mezcladas: investiga primero la causa.
- Los datos de atributos (binomial, Poisson) no se transforman: `capability_binomial` y `capability_poisson` usan
  intervalos exactos.
