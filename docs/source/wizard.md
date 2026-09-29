# Asistente de selección (`wizard`)

`pp.wizard()` ayuda a elegir el análisis SPC correcto cuando no estás
seguro de qué función usar. Tiene tres modos de operación:

| Modo | Cuándo usarlo |
|------|--------------|
| `'auto'` | Tienes datos y quieres una recomendación inmediata |
| `'cli'` | Quieres responder preguntas en la terminal |
| `'widget'` | Trabajas en Jupyter y prefieres botones |

Todos los modos devuelven (o llenan) un {class}`~pccpy.WizardResult` con
`.snippet()`, `.summary()` y `.run(datos)`.

---

## Modo `auto`

Pasa los datos y el asistente los analiza: detecta si son 1-D o 2-D,
comprueba normalidad y tendencia, y devuelve la función más adecuada.

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(0)
x = rng.normal(50, 2, 60)

res = pp.wizard(x)               # mode='auto' por defecto cuando x no es None
print(res.function)               # 'imr_chart', 'capability_analysis', etc.
print(res.snippet())              # código listo para copiar
print(res.summary())              # explicación completa
```

### Heurística automática

| Datos | Condición | Recomendación |
|-------|-----------|---------------|
| 2-D, columnas > 10 | multivariado | `t2_chart` |
| 2-D, columnas ≤ 8 | subgrupos pequeños | `xbar_r_chart` |
| 2-D, 9-10 columnas | subgrupos medianos | `xbar_s_chart` |
| 1-D, tendencia clara | > 80 % o < 20 % incrementos | `run_chart` |
| 1-D, n ≥ 30, normal | p > 0.05 con especificaciones | `capability_analysis` |
| 1-D, n ≥ 30, no normal | p ≤ 0.05 | `capability_boxcox` |
| 1-D, n < 30 | pocos datos | `imr_chart` |

### Ejecutar directamente

```python
res = pp.wizard(x)
carta = res.run(x)               # llama a pp.imr_chart(x, **res.params)
carta.plot()
```

---

## Modo `cli`

Sin datos: el asistente hace preguntas con opciones numeradas.

```python
res = pp.wizard(mode="cli")
# ¿Cuál es tu objetivo principal?
#   1. Monitorear el proceso (cartas de control)
#   2. Analizar la capacidad del proceso
#   3. Sistema de medición (MSA / Gage R&R)
#   4. Plan de muestreo de aceptación
#   5. Sistema de medición avanzado
#   6. Intervalos de tolerancia estadística
#   7. Carta de corridas / pre-control
# Elige una opción (1-7): _
```

El árbol de preguntas cubre los 30+ análisis disponibles en `pccpy`.
Entradas inválidas se ignoran y se vuelve a preguntar.

---

## Modo `widget`

En Jupyter Notebook / JupyterLab muestra botones interactivos.
Requiere `ipywidgets` (incluido en la mayoría de entornos de Jupyter).

```python
session = pp.wizard(mode="widget")
# <botones aparecen en la celda de Jupyter>

# Una vez que el usuario navega y elige:
print(session.result.function)   # disponible tras seleccionar
print(session.result.snippet())
```

`session` es un {class}`~pccpy.WidgetSession`. Su atributo `.result`
es `None` mientras la sesión está abierta y se llena al llegar a una hoja.

Si `ipywidgets` no está instalado, el modo degrada automáticamente a `'cli'`.

---

## `WizardResult`

```{eval-rst}
.. autoclass:: pccpy.WizardResult
   :members: snippet, summary, run
   :undoc-members:
```

## `WidgetSession`

```{eval-rst}
.. autoclass:: pccpy.WidgetSession
   :members:
   :undoc-members:
```
