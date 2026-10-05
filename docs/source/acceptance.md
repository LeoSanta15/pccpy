# Muestreo de aceptación (`acceptance_sampling`)

El muestreo de aceptación define un plan de muestreo estadístico para decidir si
aceptar o rechazar un lote de producción basándose en una muestra.
`pccpy` implementa tres esquemas:

| Función | Norma | Criterio |
|---------|-------|----------|
| `acceptance_sampling_attributes` | ANSI/ASQ Z1.4 | Por atributos (defectos contados) |
| `acceptance_sampling_variables` | ANSI/ASQ Z1.9 | Por variables (medición continua) |
| `dodge_romig` | Dodge-Romig | LTPD o AOQL fijo |

---

## Por atributos — Z1.4

### Uso básico

```python
import pccpy as pp

# Lote N=1000, AQL=1 %
plan = pp.acceptance_sampling_attributes(N=1000, aql=1.0)
print(plan.summary())
```

Salida:

```
Plan de muestreo por atributos (Z1.4)
  N=1000  AQL=1.0%  Nivel II
  n=80  Ac=2  Re=3
  LTPD (approx.)=4.7%   AOQL=0.82%
```

El plan dice: toma 80 muestras; acepta si encuentras ≤ 2 defectuosas.

### Parámetros

| Parámetro | Tipo | Predeterminado | Descripción |
|-----------|------|----------------|-------------|
| `N` | `int` | — | Tamaño del lote. |
| `aql` | `float` | — | AQL en porcentaje (p.ej. `1.0` para 1 %). |
| `inspection_level` | `int` | `2` | Nivel de inspección general (1, 2 o 3), con la letra de código de la tabla I de Z1.4. |
| `n` | `int` | `None` | Tamaño de muestra fijo (anula la tabla). |
| `c` | `int` | `None` | Número de aceptación fijo (anula la tabla). |

### Gráfico

```python
plan.plot()   # Curva OC + curva AOQ
```

---

## Por variables — Z1.9

Usa la media y desviación estándar de la muestra para estimar la fracción no
conforme y compararla con el AQL.

```{warning}
La tabla Z1.9 incluida **no reproduce la norma** (sus planes pueden aceptar casi cualquier lote) y la función avisa
con un `UserWarning`. Para decidir con Z1.9, tome `n` y `k` de su ejemplar de la norma y páselos con `n=` y `k=`:
`pp.acceptance_sampling_variables(N=500, aql=1.0, n=20, k=1.7)`.
```

### Uso básico

```python
import numpy as np

rng = np.random.default_rng(0)
plan = pp.acceptance_sampling_variables(N=500, aql=1.0, spec_type='one')

# Evaluar una muestra real
muestra = rng.normal(10.5, 0.2, plan.n)
decision = plan.evaluate(muestra, usl=11.0)
print(decision)
# {'xbar': 10.503, 's': 0.198, 'Q_usl': 2.512, 'k': 1.653, 'accept': True}
```

### Parámetros

| Parámetro | Tipo | Predeterminado | Descripción |
|-----------|------|----------------|-------------|
| `N` | `int` | — | Tamaño del lote. |
| `aql` | `float` | — | AQL en porcentaje. |
| `spec_type` | `str` | `'one'` | `'one'` (unilateral) o `'two'` (bilateral). |
| `inspection_level` | `int` | `2` | Nivel de inspección. |
| `n` | `int` | `None` | Tamaño de muestra fijo. |
| `k` | `float` | `None` | Constante k fija. |

### Gráfico

```python
plan.plot()   # Curva OC
```

---

## Dodge-Romig

Diseñado para minimizar la inspección total promedio (ATI) dado un LTPD o un
AOQL objetivo, asumiendo un proceso promedio conocido.

### Uso básico

```python
# LTPD = 5 % (fracción defectuosa máxima tolerable en el peor caso)
plan = pp.dodge_romig(N=1000, ltpd=0.05, process_avg=0.01)
print(plan.summary())

# AOQL = 2 % (fracción defectuosa promedio de salida máxima)
plan2 = pp.dodge_romig(N=1000, aoql=0.02, process_avg=0.01)
print(plan2.summary())
```

### Parámetros

| Parámetro | Tipo | Predeterminado | Descripción |
|-----------|------|----------------|-------------|
| `N` | `int` | — | Tamaño del lote. |
| `ltpd` | `float` | `None` | LTPD en fracción (p.ej. `0.05` para 5 %). |
| `aoql` | `float` | `None` | AOQL en fracción. Se debe pasar exactamente uno de los dos. |
| `process_avg` | `float` | `0.01` | Fracción defectuosa promedio del proceso. |

### Gráfico

```python
plan.plot()   # Curva OC
```

---

## Exportar a Excel

```python
plan.to_excel("plan_atributos.xlsx")     # requiere openpyxl
plan_v.to_excel("plan_variables.xlsx")
plan_dr.to_excel("dodge_romig.xlsx")
```

---

## Referencia de funciones

```{eval-rst}
.. autofunction:: pccpy.acceptance_sampling_attributes
   :no-index:
```

```{eval-rst}
.. autofunction:: pccpy.acceptance_sampling_variables
   :no-index:
```

```{eval-rst}
.. autofunction:: pccpy.dodge_romig
   :no-index:
```

### Objetos de resultado

```{eval-rst}
.. autoclass:: pccpy.SamplingPlanAttributes
   :members: summary, plot, to_frame, to_excel
   :undoc-members:
   :no-index:
```

```{eval-rst}
.. autoclass:: pccpy.SamplingPlanVariables
   :members: summary, plot, to_frame, to_excel, evaluate
   :undoc-members:
   :no-index:
```

```{eval-rst}
.. autoclass:: pccpy.DodgeRomigPlan
   :members: summary, plot, to_frame, to_excel
   :undoc-members:
   :no-index:
```
