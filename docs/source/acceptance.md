# Muestreo de aceptación (`acceptance_sampling`)

El muestreo de aceptación define un plan de muestreo estadístico para decidir si
aceptar o rechazar un lote de producción basándose en una muestra.
`pccpy` implementa tres esquemas:

| Función | Norma | Criterio |
|---------|-------|----------|
| `acceptance_sampling_attributes` | ANSI/ASQ Z1.4 | Por atributos (defectos contados) |
| `acceptance_sampling_variables` | MIL-STD-414 | Por variables (medición continua) |
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
| `inspection_level` | `int` o `str` | `2` | Nivel de inspección general (1, 2 o 3) o especial (`"S-1"` a `"S-4"`), con la letra de código de la tabla I de Z1.4. |
| `n` | `int` | `None` | Tamaño de muestra fijo (anula la tabla). |
| `c` | `int` | `None` | Número de aceptación fijo (anula la tabla). |
| `sampling` | `str` | `"single"` | `"single"` (tabla II-A) o `"double"` (tabla III-A: devuelve un `DoublePlanAttributes`). |

### Gráfico

```python
plan.plot()   # Curva OC + curva AOQ
```

### Inspección al 100 %

Si la muestra de la tabla es igual o mayor que el lote, la norma manda inspeccionar todo el lote. El plan devuelto lleva `n = N` (con
el `Ac` de la tabla) y se avisa con un `UserWarning`; antes devolvía la muestra de la tabla aunque no cupiera en el lote (un error).

### Muestreo doble

Con `sampling="double"` se usa la tabla III-A (inspección normal): una primera muestra `n1` y, si no basta para decidir, una segunda `n2`.
Se acepta con la primera si hay `ac1` defectuosos o menos, se rechaza con `re1` o más y, entre ambos, se toma la segunda y se acepta si el total
es `ac2` o menos (`re2 = ac2 + 1`).

```python
doble = pp.acceptance_sampling_attributes(N=1000, aql=1.0, sampling="double")
doble.pa(0.01)    # probabilidad de aceptación exacta, con la binomial
doble.asn(0.01)   # tamaño medio de muestra: n1 + n2·P(ac1 < d1 < re1)
doble.plot()      # OC + AOQ + ASN
```

No hay plan doble para AQL 0,010 y 0,015 % (`ValueError`) y la letra A usa el plan de la letra B (con aviso). La inspección rigurosa y
reducida y el muestreo múltiple no están incluidos. Las tablas I, II-A y III-A se transcribieron de capturas de la norma, no de su texto.

---

## Por variables — MIL-STD-414

Usa la media y desviación estándar de la muestra para decidir con el método del factor de aceptabilidad `k`: se acepta
si `Q = (U − x̄)/s ≥ k` (o `(x̄ − L)/s ≥ k`). Los planes salen de las tablas A-2 (letra de código por tamaño de lote y
nivel de inspección I a V) y B-1 (`n` y `k` por letra y AQL) de **MIL-STD-414 (11 de junio de 1957)**, método de la
desviación estándar, especificación unilateral, Forma 1.

```{warning}
No es ANSI/ASQ Z1.9: sus tablas no están disponibles (`standard="z1.9"` lanza `ValueError`). Las tablas de MIL-STD-414 se
transcribieron de capturas de la norma, no de su texto, y no se comprobó que coincidan con Minitab ni con Z1.9. La Forma 2,
la inspección reducida, el método del rango y la doble especificación no están incluidos: para una doble especificación dé
su plan con `n=` y `k=`. Si el `n` de la tabla es igual o mayor que el lote, se inspecciona todo el lote (`n = N`) con un aviso.
```

### Uso básico

```python
import numpy as np

rng = np.random.default_rng(0)
plan = pp.acceptance_sampling_variables(N=500, aql=1.0)   # letra I (nivel IV): n = 25, k = 1.85

# Evaluar una muestra real
muestra = rng.normal(10.5, 0.2, plan.n)
decision = plan.evaluate(muestra, usl=11.0)
print(decision)
# {'xbar': ..., 's': ..., 'Q_usl': ..., 'accept': True, 'criterion': 'Q=... ≥ k=1.8500'}
```

### Parámetros

| Parámetro | Tipo | Predeterminado | Descripción |
|-----------|------|----------------|-------------|
| `N` | `int` | — | Tamaño del lote. |
| `aql` | `float` | — | AQL en %: 0.04, 0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.00, 1.50, 2.50, 4.00, 6.50, 10.00 o 15.00. |
| `spec_type` | `str` | `'one'` | `'one'` (unilateral); `'two'` solo con `n=` y `k=`. |
| `inspection_level` | `int` | `4` | Nivel de inspección de 1 a 5 (I a V de la tabla A-2). |
| `inspection` | `str` | `'normal'` | `'normal'` o `'tightened'` (rigurosa: la columna del AQL inmediatamente inferior). |
| `n` | `int` | `None` | Tamaño de muestra fijo. |
| `k` | `float` | `None` | Constante k fija. |
| `standard` | `str` | `'mil-std-414'` | Norma de las tablas; `'z1.9'` lanza `ValueError`. |

### Gráfico

```python
plan.plot()   # Curva OC
```

La probabilidad de aceptación de un plan unilateral es exacta (distribución t no central: `Pa = P(t'(n−1; z·√n) ≥ k·√n)`), con datos normales e independientes. La curva OC bilateral supone el proceso centrado entre los límites.

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
