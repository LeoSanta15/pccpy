# Intervalos de tolerancia (`tolerance_interval`)

Un **intervalo de tolerancia** (L, U) garantiza que, con confianza `1 − α`,
al menos una fracción `p` de la población cae dentro del intervalo.
Es diferente de un intervalo de confianza para la media y diferente de un
intervalo de predicción: cubre una fracción de la *distribución*, no solo
el valor esperado.

`pccpy` implementa dos métodos:

- **Normal** — asume distribución normal; usa el factor k de Howe (1969) para
  bilateral y la distribución t no central exacta para unilateral. Howe es una
  aproximación: se desvía del k exacto menos de un 0,7 % con `n ≥ 10` y hasta un
  3,8 % con `n = 3`, por lo que con muestras muy pequeñas la confianza real del
  bilateral puede quedar unas décimas por debajo de la pedida.
- **No paramétrico** — libre de distribución; se basa en estadísticos de orden;
  requiere muestras más grandes para la misma cobertura y confianza.

---

## Uso básico

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(1)
x = rng.normal(100, 2, 50)

# Normal bilateral: con 95% de confianza, ≥95% de la población cae en (LI, LS)
res = pp.tolerance_interval(x, coverage=0.95, confidence=0.95)
print(res.summary())
```

Salida:

```
Intervalo de tolerancia (normal, two)
  N=50  Cobertura≥95.0%  Confianza=95.0%
  Media=99.977  Desv.Est.=1.9737
  Factor k = 2.06471
  LI = 95.905   LS = 104.05
```

---

## Parámetros

| Parámetro | Tipo | Predeterminado | Descripción |
|-----------|------|----------------|-------------|
| `data` | array-like | — | Vector 1-D de observaciones. |
| `coverage` | `float` | `0.95` | Fracción mínima de la población a cubrir (p). |
| `confidence` | `float` | `0.95` | Nivel de confianza 1 − α. |
| `sides` | `str` | `'two'` | `'two'` (bilateral), `'lower'` (cota inferior) o `'upper'` (cota superior). |
| `method` | `str` | `'normal'` | `'normal'` o `'nonparametric'`. |

---

## Ejemplos adicionales

### Cota unilateral (solo límite superior)

```python
res_u = pp.tolerance_interval(x, coverage=0.95, confidence=0.95, sides='upper')
print(res_u.summary())
# LS = 103.57   (el 95% de la población cae por debajo de este valor, con 95% confianza)
```

### Intervalo no paramétrico

```python
x300 = rng.normal(100, 2, 300)
res_np = pp.tolerance_interval(
    x300, coverage=0.95, confidence=0.95, method='nonparametric'
)
print(res_np.summary())
# Confianza alcanzada: 98.40%   LI = 95.44   LS = 104.04
```

El intervalo bilateral es `[X₍ᵣ₎, X₍ₙ₊₁₋ᵣ₎]` y su cobertura sigue una Beta(n − 2r + 1, 2r); se elige el **mayor `r`** que
todavía alcanza la confianza pedida, es decir, el intervalo más estrecho válido (con `n = 300`, `r = 4` y confianza
98,4 %; la confianza lograda suele superar la pedida porque `r` es un entero).

> El método no paramétrico puede no ser factible para muestras pequeñas: el bilateral con cobertura 0,95 y confianza
> 0,95 necesita al menos `n = 93`. Si `n` es insuficiente, `tolerance_interval` lanza `ValueError`.

### Desde estadísticos resumen

Cuando solo dispones de media, desviación estándar y n (sin datos crudos):

```python
res = pp.tolerance_interval_summary(
    mean=100.0, std=2.0, n=50,
    coverage=0.95, confidence=0.95,
    sides='two',
)
print(res.summary())
```

---

## Gráfico

```python
res = pp.tolerance_interval(x)
res.plot()
```

El gráfico muestra un histograma con la curva normal ajustada y las cotas del
intervalo marcadas, junto con anotaciones de cobertura y confianza.

---

## Exportar a Excel

```python
res.to_excel("tolerancia.xlsx")   # requiere openpyxl
```

---

## Referencia de `ToleranceResult`

```{eval-rst}
.. autoclass:: pccpy.ToleranceResult
   :members: summary, plot, to_frame, to_excel
   :undoc-members:
   :no-index:
```

### Atributos principales

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `n` | `int` | Número de observaciones. |
| `mean`, `std` | `float` | Media y desviación estándar muestrales. |
| `coverage` | `float` | Fracción de cobertura solicitada (p). |
| `confidence` | `float` | Nivel de confianza solicitado (1 − α). |
| `sides` | `str` | `'two'`, `'lower'` o `'upper'`. |
| `method` | `str` | `'normal'` o `'nonparametric'`. |
| `lower`, `upper` | `float \| None` | Cotas del intervalo. |
| `k_factor` | `float \| None` | Factor k (solo método normal). |
| `achieved_confidence` | `float \| None` | Confianza alcanzada (solo método no paramétrico). |

---

## Referencia de función

```{eval-rst}
.. autofunction:: pccpy.tolerance_interval
   :no-index:
```

```{eval-rst}
.. autofunction:: pccpy.tolerance_interval_summary
   :no-index:
```
