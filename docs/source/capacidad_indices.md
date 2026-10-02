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
print(f"PPM total = {res.ppm_total:.0f}")
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
Cpm = (USL − LSL) / (6 · √(σ² + (x̄ − target)²))
```

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
print(f"Z.Bench = {res.z_bench:.2f}  ({res.ppm_total:.0f} PPM)")
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
