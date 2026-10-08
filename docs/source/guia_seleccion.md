# Guía de selección de carta de control

¿No sabes qué carta usar? Responde las preguntas en orden y llega a la función
correcta en menos de un minuto.

---

## Paso 1 — ¿Qué tipo de dato tienes?

```
¿Son datos continuos (medición numérica)?
  └─ Sí ──► ir a Paso 2
  └─ No (conteo de defectos / defectuosos) ──► ir a Paso 4
```

---

## Paso 2 — ¿Están agrupados en subgrupos?

Un **subgrupo racional** es un conjunto de mediciones tomadas bajo condiciones
muy similares (misma máquina, mismo operador, mismo turno).

```
¿Tienes subgrupos?
  └─ No (una observación por período) ──► ir a Paso 3
  └─ Sí, tamaño 2-9 ──► xbar_r_chart  (Xbar-R)
  └─ Sí, tamaño ≥ 10  ──► xbar_s_chart (Xbar-S)
```

### `xbar_r_chart` — Xbar-R

Para subgrupos pequeños (2–9). Los límites se basan en el rango promedio.

```python
import pccpy as pp, numpy as np
g = np.random.default_rng(0).normal(50, 1, (25, 4))  # 25 subgrupos de 4
carta = pp.xbar_r_chart(g, tests="all")
carta.plot()
```

### `xbar_s_chart` — Xbar-S

Para subgrupos grandes (≥10) o variables. Los límites se basan en la desviación estándar.

```python
g10 = np.random.default_rng(0).normal(50, 1, (20, 10))
carta = pp.xbar_s_chart(g10, tests="all")
```

---

## Paso 3 — Datos individuales (sin subgrupos)

```
¿El proceso es estable y quieres detectar cambios pequeños?
  └─ No (monitoreo general) ──► imr_chart (I-MR)
  └─ Sí, cambios ≤ 1.5σ     ──► ewma_chart (EWMA)
  └─ Sí, cambios en la media ──► cusum_chart (CUSUM)

¿Tus datos siguen una distribución muy sesgada o no normal?
  └─ Sí ──► zmr_chart (Z-MR, con transformación)

¿Tus tiempos entre eventos son el indicador clave?
  └─ Sí ──► t_chart o g_chart

¿Necesitas detectar cambios y al mismo tiempo ver zonas?
  └─ Sí ──► zone_chart
```

### `imr_chart` — I-MR (carta de individuos y rango móvil)

La carta más usada para datos individuales. Detecta desplazamientos de ±3σ.

```python
x = np.random.default_rng(0).normal(50, 1, 60)
carta = pp.imr_chart(x, tests=(1, 2, 3, 4, 5, 6, 7, 8))
carta.plot()
carta.save_plot("imr.png")
```

### `ewma_chart` — Media móvil exponencialmente ponderada

Detecta desplazamientos pequeños acumulando historia. Ideal para cambios de
0.5σ–1.5σ.

```python
carta = pp.ewma_chart(x, weight=0.2, k=3.0)
```

### `cusum_chart` — CUSUM

Suma acumulada de desviaciones. Alta sensibilidad a desplazamientos sostenidos.

```python
carta = pp.cusum_chart(x, k=0.5, h=4.0)
```

### `imr_rs_chart` — I-MR-R/S

Separa la variación entre subgrupos de la variación dentro de subgrupos cuando
tienes subgrupos pero quieres monitorear valores individuales.

---

## Paso 4 — Datos de atributos

```
¿Cuál es tu medida de no calidad?
  ├─ Fracción defectuosa (p) con tamaño de muestra variable ──► p_chart / laney_p_chart
  ├─ Número de defectuosos con tamaño fijo                  ──► np_chart
  ├─ Número de defectos por unidad, muestra variable        ──► u_chart / laney_u_chart
  └─ Número de defectos con unidad de inspección fija       ──► c_chart
```

> **¿Cuándo usar Laney P′ o U′?** Cuando el proceso de producción introduce
> sobredispersión (más variabilidad de la esperada por el binomial o Poisson).
> `laney_p_chart` y `laney_u_chart` ajustan los límites con un factor σ_z para
> evitar falsas alarmas.

```python
# Defectuosos variables (n distinto cada muestra)
d = np.array([3, 1, 4, 2, 0, 5, 2, 3, 1, 2, 4, 1, 3, 2, 1])
n = np.array([100, 95, 110, 100, 98, 105, 100, 100, 95, 100, 110, 100, 98, 100, 102])
carta = pp.p_chart(d, n, tests=[1, 2])

# Defectos por unidad (poisson)
carta = pp.c_chart(d)
carta = pp.u_chart(d, n)
```

---

## Paso 5 — Capacidad del proceso

Una vez que la carta indica proceso **bajo control estadístico**, calcula capacidad:

```
¿Tus datos siguen una distribución normal?
  └─ Sí ──► capability_analysis(x, lsl, usl)
  └─ No ──► capability_boxcox(x, lsl, usl)   (transforma y calcula)
         o  capability_nonnormal(x, lsl, usl, distribution="weibull")

¿Quieres la carta + capacidad en un solo gráfico (6 paneles)?
  └─ Sí ──► capability_sixpack(x, lsl, usl)
```

---

## Paso 6 — No sé por dónde empezar

Usa `diagnose()`. Analiza tus datos, detecta problemas y te dice exactamente
qué función usar:

```python
d = pp.diagnose(x, lsl=44, usl=56)
print(d.summary())          # recomendación automática
d.plot()                    # histograma + secuencia
```

---

## Tabla resumen

| Situación | Función |
|-----------|---------|
| Datos individuales, monitoreo general | `imr_chart` |
| Datos individuales, cambios pequeños | `ewma_chart` o `cusum_chart` |
| Subgrupos pequeños (2–9) | `xbar_r_chart` |
| Subgrupos grandes (≥10) | `xbar_s_chart` |
| Fracción defectuosa, n variable | `p_chart` o `laney_p_chart` |
| Número de defectuosos, n fijo | `np_chart` |
| Defectos por unidad | `u_chart` o `laney_u_chart` |
| Número de defectos, unidad fija | `c_chart` |
| Capacidad, distribución normal | `capability_analysis` |
| Capacidad, distribución no normal | `capability_boxcox` o `capability_nonnormal` |
| Detección de tendencias | `run_chart` |
| Semáforo de producción | `precontrol` |
| No sé qué usar | `diagnose` |

---

## Ver también

- {doc}`inicio_rapido` — ejemplos de cada función
- {doc}`capacidad_indices` — diferencia entre Cp, Cpk, Pp, Ppk
- {doc}`minitab` — equivalencias con Minitab
