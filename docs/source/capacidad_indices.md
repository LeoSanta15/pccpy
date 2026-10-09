# Índices de capacidad: Cp, Cpk, Pp, Ppk

Los índices de capacidad cuantifican qué tan bien cabe el proceso dentro de las
especificaciones. Esta página explica la diferencia entre ellos, cuándo usar
cada uno y cómo interpretar sus valores.

---

## La pregunta que responden

> "Si el proceso sigue funcionando igual, ¿qué fracción de las piezas caerá
> fuera de especificaciones?"

- **Cp, Cpk** — responden esta pregunta con la variación **dentro de subgrupos**
  (variación a corto plazo; solo el ruido del proceso).
- **Pp, Ppk** — responden con la variación **total u global** (incluye también
  los desplazamientos y derivas a largo plazo).

---

## Las fórmulas

Sea:
- `LSL` = límite de especificación inferior
- `USL` = límite de especificación superior
- `x̄` = media del proceso
- `σ_dentro` = desviación estándar dentro de subgrupos (estimada con R̄/d₂ o S̄/c₄)
- `σ_total` = desviación estándar total (calculada con todos los datos, ddof=1)

| Índice | Fórmula | Mide |
|--------|---------|------|
| **Cp** | (USL − LSL) / (6 · σ_dentro) | Potencial del proceso (sin importar el centrado) |
| **Cpk** | min(USL − x̄, x̄ − LSL) / (3 · σ_dentro) | Capacidad real considerando centrado |
| **Pp** | (USL − LSL) / (6 · σ_total) | Desempeño global (sin importar el centrado) |
| **Ppk** | min(USL − x̄, x̄ − LSL) / (3 · σ_total) | Desempeño real global |

> **Regla práctica:** Si el proceso está bajo control estadístico (sin causas
> especiales), `Cp ≈ Pp` y `Cpk ≈ Ppk`. Si hay una diferencia grande, el proceso
> tiene desplazamientos o derivas: las causas asignables afectan la variación total.

---

## Analogía: el auto en el garage

Imagina que el garage es la tolerancia (USL − LSL) y el auto es el proceso:

- **Cp** — ¿es el auto más angosto que el garage? (solo mide anchos)
- **Cpk** — ¿cabe el auto centrado en el garage? (mide anchura Y posición)
- Si Cp > 1 pero Cpk < 1: el auto cabe en ancho, pero está muy pegado a un lado.

---

## Tabla de referencia

| Valor del índice | Interpretación | Nivel sigma aprox. |
|-----------------|----------------|-------------------|
| < 1.00 | Proceso **no capaz** — produce piezas fuera de especificaciones | < 3σ |
| 1.00 | Límite mínimo aceptable — 2700 PPM esperados | 3σ |
| 1.33 | Estándar de la industria automotriz (PPAP) | 4σ |
| 1.50 | Meta habitual en manufactura | 4.5σ |
| 1.67 | Proceso muy capaz | 5σ |
| 2.00 | Proceso Six Sigma | 6σ |

> Los valores de referencia para Pp y Ppk suelen ser más bajos que para Cp y Cpk
> porque incluyen más fuentes de variación.

---

## Cómo calcularlos con pccpy

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(0)
x = rng.normal(50.0, 0.8, 100)   # proceso con σ ≈ 0.8

res = pp.capability_analysis(x, lsl=47.5, usl=52.5)
print(res.summary())
```

Salida relevante:

```
  ── Capacidad (sigma dentro) ──
  Cp    :  1.05    Cpl   :  1.06    Cpu   :  1.04
  Cpk   :  1.04

  ── Desempeño (sigma total) ──
  Pp    :  1.03    Ppl   :  1.04    Ppu   :  1.02
  Ppk   :  1.02

  Z.Bench : 3.07
  PPM < LEI  :   912    PPM > LES  :  1072    Total :  1984
```

Acceder a los valores individuales:

```python
print(f"Cp  = {res.cp:.3f}")
print(f"Cpk = {res.cpk:.3f}")
print(f"Pp  = {res.pp:.3f}")
print(f"Ppk = {res.ppk:.3f}")
print(f"PPM total = {res.ppm_overall[2]:.0f}")
```

---

## ¿Cuándo uso Cp/Cpk y cuándo Pp/Ppk?

| Situación | Índice recomendado | Por qué |
|-----------|--------------------|---------|
| Proceso nuevo, primera validación | Pp, Ppk | Aún no hay historia suficiente para estimar σ_dentro con fiabilidad |
| Proceso en producción continua bajo control estadístico | Cp, Cpk | Mide el potencial "limpio" sin ruido de largo plazo |
| Auditoría o reporte PPAP / APQP | Cp, Cpk Y Pp, Ppk | Los requisitos suelen pedir ambos |
| Proceso con derivas conocidas | Pp, Ppk | La deriva forma parte de la variación real del cliente |

---

## Cpm — índice de centrado (Taguchi)

`Cpm` penaliza la distancia al objetivo (target) además de la dispersión:

```
s_T² = Σ(xᵢ − T)² / (n − 1) = s² + n/(n − 1) · (x̄ − T)²

Cpm = min(T − LSL, USL − T) / (3 · s_T)
```

Con el objetivo en el punto medio de la especificación, `min(T − LSL, USL − T) = (USL − LSL)/2` y la fórmula queda
`Cpm = (USL − LSL) / (6 · s_T)`. Con un objetivo descentrado se usa la distancia al límite más cercano, como Minitab. Con
`capability_analysis_summary` (sin datos crudos) se usa la misma `s_T²` a partir de `s` y `x̄`.

Se activa automáticamente en `capability_analysis` si pasas `target`:

```python
res = pp.capability_analysis(x, lsl=47.5, usl=52.5, target=50.0)
print(f"Cpm = {res.cpm:.3f}")
```

---

## Z.Bench — nivel sigma del proceso

`Z.Bench` es el cuantil de la distribución normal que corresponde al PPM total
esperado. Es la forma más directa de comunicar el nivel sigma del proceso al
equipo directivo:

```python
# El mismo índice, calculado internamente por pccpy
print(f"Z.Bench = {res.z_bench_overall:.2f}  ({res.ppm_overall[2]:.0f} PPM)")
```

| Z.Bench | PPM aprox. | Nivel sigma (con desplazamiento 1.5σ) |
|---------|-----------|---------------------------------------|
| 3.0 | 2 700 | 3σ |
| 4.0 | 63 | 4σ |
| 4.5 | 3.4 | 6σ (con desplazamiento) |
| 6.0 | 0.001 | 6σ (centrado) |

---

## Ver también

- {doc}`guia_seleccion` — cuándo hacer análisis de capacidad
- {doc}`referencia/capacidad` — referencia completa de `capability_analysis`
- {doc}`faq` — "¿Por qué Cp ≠ Cpk?" y otras preguntas frecuentes


## Transformar los datos: Box-Cox, Yeo-Johnson y Johnson

Con `transform=` se normalizan los datos (y los límites de especificación y el objetivo) y los índices se calculan en la
escala transformada; los límites, el objetivo y el PPM observado se informan en unidades originales.

```python
pp.capability_analysis(x, lsl=15, usl=32, transform="yeo-johnson")
pp.capability_analysis(x, lsl=15, usl=32, transform="johnson")     # elige SU, SB o SL
pp.capability_analysis(g, lsl=15, usl=32, transform="boxcox", ci_method="bootstrap")  # también con subgrupos
```

| `transform` | Datos admitidos | Notas |
|-------------|-----------------|-------|
| `"boxcox"` | estrictamente positivos (y límites positivos) | equivale a `capability_boxcox` |
| `"yeo-johnson"` | cualquier valor (ceros y negativos) | lambda por máxima verosimilitud |
| `"johnson"` | cualquier valor | ajusta las familias SU (sin límites), SB (acotada) y SL (lognormal de tres parámetros) y elige la que deja los datos más normales (mayor valor p de Anderson-Darling) |

- Con Johnson SB o SL, un límite de especificación fuera del soporte de la distribución (por ejemplo más allá de la cota
  superior de SB) no puede superarse: los índices salen infinitos. Es coherente, no un error.
- `sigma_within` no se puede combinar con `transform` (está en la escala original).
- `pp.fit_transformation(datos, método)` devuelve una `Transformation` con `forward()` (a la escala normal),
  `inverse()` (a la original) e `info()`, por si quieres aplicarla a otros valores.
- Con `ci_method="bootstrap"` los parámetros de la transformación se mantienen fijos en los remuestreos: el intervalo no
  recoge su incertidumbre.

## Intervalos de confianza con datos asimétricos

Los intervalos de Pp y Ppk por defecto (chi-cuadrado y Bissell) suponen normalidad. Con datos asimétricos pueden quedar
cortos, sobre todo el de **Pp**, que depende de la desviación estándar. Con `ci_method="bootstrap"` los intervalos salen
de remuestrear los datos:

```python
r = pp.capability_analysis(datos, lsl=6, usl=22, ci_method="bootstrap", seed=1)
r.pp_ci, r.ppk_ci          # BCa por defecto; bootstrap_method="percentile" para el percentil
pp.capability_boxcox(datos, 6, 22, ci_method="bootstrap", seed=1)   # sobre los datos transformados

# no normal: se vuelve a ajustar la distribución en cada remuestreo (más lento: n_boot=1000 por defecto)
pp.capability_nonnormal(datos, 6, 22, distribution="weibull", ci_method="bootstrap", seed=1).ppk_ci
```

- Es opt-in: sin `ci_method` nada cambia.
- Se remuestrean las observaciones (Pp y Ppk usan la desviación estándar general). Con Box-Cox el lambda se mantiene fijo
  en los remuestreos: el intervalo no recoge la incertidumbre de lambda.
- En simulación (gamma(2), n = 150) el intervalo normal de Pp cubre ≈ 81 % y BCa ≈ 92 %; para Ppk ambos son razonables
  (≈ 88 % y ≈ 91 %), porque ahí el intervalo normal ya aguanta mejor.
- `capability_nonnormal` no daba ningún intervalo: con el bootstrap da el de Pp y Ppk, que incluye la incertidumbre del
  ajuste de la distribución.

## Capacidad para atributos

Con datos de atributos (unidades defectuosas o conteo de defectos) no existen Cp ni Cpk: la capacidad es la **tasa de
defectos**, con su intervalo exacto.

```python
import pccpy as pp

r = pp.capability_binomial([3, 5, 2, 4, 6, 1, 3, 5], n=200)
print(r.summary())            # % defectivo, PPM, Z del proceso e intervalos
r.homogeneous                 # ¿p es constante entre muestras?

q = pp.capability_poisson([3, 5, 2, 4, 6, 1, 3, 5], units=10, opportunities=20)
q.dpu, q.dpu_ci, q.dpmo, q.z
```

| Dato | Función | Estimador | Intervalo |
|------|---------|-----------|-----------|
| Unidades defectuosas en muestras de tamaño `n` | `capability_binomial` | `p̄ = Σd / Σn`, PPM = 10⁶·p̄, `Z = Φ⁻¹(1 − p̄)` | Clopper-Pearson (exacto) |
| Defectos en `units` unidades | `capability_poisson` | `DPU = Σd / Σu`; con `opportunities=`, DPMO y `Z` | Garwood (exacto) |

Ambas calculan la **prueba chi-cuadrado de que la tasa es constante** entre muestras. Si el valor p es pequeño
(`homogeneous` es `False`), el proceso no es estable y la capacidad calculada no es fiable: revise primero la carta P o U
(y use `phase_one()` para depurar la Fase I). `r.plot()` muestra la tasa por muestra y la estimación acumulada con su
intervalo, para ver si ya se estabilizó.
