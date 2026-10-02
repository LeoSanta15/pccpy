# Preguntas frecuentes (FAQ)

---

## Cartas de control

### ¿Por qué el límite inferior de la carta P no aparece?

La carta P calcula el LCI como `p̄ − 3√(p̄(1−p̄)/n)`. Cuando este valor es
negativo, se establece en 0 y no se dibuja línea (no tendría sentido una
fracción defectuosa negativa). Esto es comportamiento normal cuando el AQL es
bajo o los subgrupos son pequeños.

```python
# La señal de LCI = 0 está en carta.panels[0].lcl (verás ceros o NaN)
carta = pp.p_chart(d, n)
import numpy as np
print(np.unique(carta.panels[0].lcl))
```

---

### ¿Por qué Cp es NaN en mis resultados?

`capability_analysis` calcula Cp/Cpk usando la desviación estándar **dentro de
subgrupos** (`sigma_within`). Si pasas datos individuales sin `subgroup_size`,
pccpy usa R̄/d₂ de rangos móviles para estimar σ_dentro.

`Cp = NaN` puede ocurrir en `capability_analysis_summary` si no pasas
`std_within`:

```python
# Sin std_within → Cp y Cpk serán NaN; Pp y Ppk sí se calculan
res = pp.capability_analysis_summary(mean=50, std_overall=1.0, n=100, lsl=47, usl=53)
# Con std_within → Cp y Cpk se calculan
res = pp.capability_analysis_summary(mean=50, std_overall=1.0, n=100, lsl=47, usl=53,
                                     std_within=0.9)
```

---

### ¿Qué diferencia hay entre Cp y Cpk?

- **Cp** mide si el proceso es suficientemente estrecho para caber en la
  especificación (ignorando si está centrado).
- **Cpk** mide tanto el ancho como el centrado. Si el proceso está perfectamente
  centrado, Cp = Cpk.

Un proceso con Cp = 1.5 pero Cpk = 0.8 es un proceso capaz pero mal centrado.
Ver {doc}`capacidad_indices` para la explicación completa.

---

### ¿Qué diferencia hay entre p_chart y laney_p_chart?

La carta P asume que los datos siguen exactamente una distribución binomial.
Cuando los tamaños de subgrupo son grandes o hay correlación entre subgrupos, los
datos muestran **sobredispersión** (más variabilidad de la esperada). En ese caso,
`laney_p_chart` ajusta los límites con un factor σ_z calculado con una regresión
de Laney, evitando falsas alarmas.

Regla práctica: si `laney_p_chart` da límites mucho más amplios que `p_chart`
con los mismos datos, hay sobredispersión y Laney es la opción correcta.

---

### ¿Por qué mis límites de control son diferentes a los de Minitab?

Las diferencias más comunes:

1. **Método de estimación de σ** — pccpy usa `R̄/d₂` por defecto para datos
   individuales. Puedes cambiar con `sigma_method='s'` (usa S̄/c₄).
2. **Constantes** — pccpy y Minitab usan las mismas tablas de constantes (c₄, d₂, d₃).
3. **Subgrupos incompletos** — si el último subgrupo tiene menos observaciones
   de las esperadas, pccpy lo incluye en el gráfico pero lo excluye del cálculo
   de límites (igual que Minitab). Verás una advertencia (`UserWarning`).

---

### ¿Cómo aplico los límites de Fase I a nuevos datos (Fase II)?

```python
# Calcular límites con datos históricos (Fase I)
carta_i = pp.imr_chart(x_historico, tests="all")
mu_i    = carta_i.params[0]["mu"]
sigma_i = carta_i.params[0]["sigma"]

# Aplicar esos límites a datos nuevos (Fase II)
carta_ii = pp.imr_chart(x_nuevo, mu=mu_i, sigma_within=sigma_i, tests=(1,))
```

Para cartas de subgrupos usa `xbar_r_chart(g, mu=..., sigma_within=...)`.

---

### ¿Cómo uso etapas (stages) para marcar un cambio en el proceso?

```python
import numpy as np
# Los primeros 50 puntos son Etapa 1; los siguientes 50 son Etapa 2
etapas = np.r_[np.ones(50), np.full(50, 2)]
carta = pp.imr_chart(x, stages=etapas, tests="all")
# Cada etapa tiene sus propios límites calculados internamente
```

---

## Distribución y normalidad

### ¿Qué hago si mis datos no son normales?

Tienes tres opciones:

1. **Transformación Box-Cox** (recomendada como primer paso):
   ```python
   cap = pp.capability_boxcox(x, lsl=44, usl=56)
   ```
2. **Ajuste a una distribución no normal** (Weibull, lognormal, gamma, etc.):
   ```python
   cap = pp.capability_nonnormal(x, lsl=44, usl=56, dist="weibull")
   ```
3. **Índices no paramétricos** (percentiles observados):
   ```python
   cap = pp.capability_nonnormal(x, lsl=44, usl=56, dist="nonparametric")
   ```

Las cartas I-MR y Xbar-R son robustas a la no normalidad si n > 4 por subgrupo
(por el teorema central del límite).

---

### ¿Cuántas observaciones necesito para que la prueba de normalidad sea válida?

`diagnose()` y `normality_test()` usan `scipy.stats.normaltest` (D'Agostino-
Pearson). Se necesitan **al menos 8 observaciones**; con menos, la función
devuelve `is_normal=True` y `normality_p=NaN` para evitar resultados engañosos.

---

## Exportación y visualización

### ¿Cómo guardo el gráfico en un archivo?

Todos los objetos de resultado tienen `save_plot()`:

```python
# PNG para presentaciones
carta.save_plot("carta.png", dpi=200)

# PDF vectorial para reportes
cap.save_plot("capacidad.pdf")

# SVG editable
tol.save_plot("tolerancia.svg")

# Pasar argumentos adicionales al método plot()
carta.save_plot("carta_sinzonas.png", zones=False)
```

---

### ¿Cómo exporto a Excel?

```python
carta.to_excel("carta.xlsx")       # cada panel en una hoja + hoja de violaciones
cap.to_excel("capacidad.xlsx")
tol.to_excel("tolerancia.xlsx")
d.to_excel("diagnostico.xlsx")     # DiagnoseResult

# Varios análisis en un solo archivo
import pandas as pd
with pd.ExcelWriter("reporte.xlsx", engine="openpyxl") as writer:
    cap.to_frame().to_excel(writer, sheet_name="Capacidad")
    carta.to_frame().to_excel(writer, sheet_name="Carta")
    carta.violations().to_excel(writer, sheet_name="Violaciones", index=False)
```

> Requiere `openpyxl`: `pip install pccpy[excel]`

---

### ¿Cómo muestro los gráficos en un Jupyter Notebook?

```python
%matplotlib inline   # al inicio del notebook (una sola vez)

import pccpy as pp
carta = pp.imr_chart(x)
carta.plot()   # se muestra directamente en el notebook
```

O si prefieres mostrar explícitamente:

```python
import matplotlib.pyplot as plt
fig = carta.plot()
plt.show()
```

---

### ¿Puedo personalizar el aspecto del gráfico?

`plot()` devuelve un objeto `matplotlib.figure.Figure` estándar que puedes
modificar después:

```python
fig = carta.plot()
fig.axes[0].set_title("Carta I-MR — Línea A", fontsize=14)
fig.set_size_inches(14, 6)
fig.savefig("carta_custom.png", dpi=150, bbox_inches="tight")
```

---

## Errores comunes

### `ValueError: Datos 1-D: indique 'subgroup_size' o 'subgroup'`

Las cartas de subgrupos (`xbar_r_chart`, `xbar_s_chart`, `imr_rs_chart`,
`zone_chart`, `ma_chart`) requieren datos en forma de subgrupos. Soluciones:

```python
# Opción 1: pasar una matriz 2-D
g = x.reshape(-1, 4)   # 4 mediciones por subgrupo
carta = pp.xbar_r_chart(g)

# Opción 2: indicar subgroup_size
carta = pp.xbar_r_chart(x, subgroup_size=4)

# Opción 3: DataFrame largo con columna de subgrupo
carta = pp.xbar_r_chart(df, subgroup="lote", value="diametro_mm")
```

---

### `ValueError: diagnose requiere al menos 4 observaciones`

`diagnose()` necesita mínimo 4 datos para calcular estadísticos básicos.

---

### `ValueError: Combinación AQL=X% y letra=Y no disponible en la tabla Z1.9`

Las tablas Z1.9 (muestreo por variables) no cubren todas las combinaciones de
AQL y tamaño de lote. Prueba:
- Reducir el tamaño del lote N
- Cambiar el nivel de inspección: `inspection_level=1`
- Usar muestreo por atributos: `acceptance_sampling_attributes(N, aql)`

---

### `ModuleNotFoundError: No module named 'openpyxl'`

`openpyxl` es una dependencia opcional. Instálala con:

```bash
pip install pccpy[excel]
# o
pip install openpyxl
```

---

## Ver también

- {doc}`guia_seleccion` — árbol de decisión para elegir la carta
- {doc}`capacidad_indices` — Cp, Cpk, Pp, Ppk explicados
- {doc}`tutorial_real` — flujo completo con datos reales
- {doc}`minitab` — equivalencias con Minitab
