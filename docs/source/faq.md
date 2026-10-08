# Preguntas frecuentes (FAQ)

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
# Fase I iterativa: excluye los puntos con señal y recalcula hasta que no quede ninguna
fase1 = pp.phase_one(pp.imr_chart, x_historico, tests=(1, 2, 3))

# Fase II: aplicar esos límites congelados a datos nuevos
carta_ii = fase1.phase2(x_nuevo, tests=(1,))
```

También se puede hacer a mano: `pp.imr_chart(x_nuevo, mu=carta_i.params[0]["media"], sigma=carta_i.params[0]["sigma"])`.
Para cartas de subgrupos usa `xbar_r_chart(g, mu=..., sigma=...)`.

---

### ¿Excluir puntos en la Fase I es siempre correcto?

No. Solo tiene sentido si has encontrado y corregido la **causa especial** de cada punto; si no, los límites
quedan artificialmente estrechos y la Fase II dará falsas alarmas. Por eso `phase_one()` se detiene (y avisa)
si tendría que excluir más del 25 % de los puntos (`max_excluded`), si quedarían menos de 20 puntos
(`min_points`) o si no converge en `max_iterations` pasadas: en esos casos el proceso no es estable y hay que investigarlo.

---

### ¿Cómo muestro fechas en el eje x de la carta?

Pasa una serie de pandas con índice de fechas (`pd.Series(x, index=fechas)`): la carta rotula el eje con ellas.
Para otras etiquetas (lotes, turnos) usa `carta.with_labels(etiquetas)`.

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

1. **Transformación Box-Cox** (primer paso si los datos y los límites son positivos):
   ```python
   cap = pp.capability_boxcox(x, lsl=44, usl=56)
   ```
2. **Ajuste a una distribución no normal** (Weibull, lognormal, gamma, etc.):
   ```python
   cap = pp.capability_nonnormal(x, lsl=44, usl=56, distribution="weibull")
   ```
   `diagnose(x, lsl=44, usl=56)` te dice cuál de las dos conviene (y por qué los datos no son normales).
3. **Intervalos sin suponer normalidad** para Pp y Ppk, con cualquiera de las anteriores o con datos normales:
   ```python
   cap = pp.capability_analysis(x, lsl=44, usl=56, ci_method="bootstrap", seed=1)
   ```
   El PPM observado (`cap.ppm_obs`) no depende de ninguna distribución.

Para los **intervalos de confianza** de la media, la mediana y la desviación estándar sin suponer normalidad:
`pp.bootstrap_summary(x, seed=1)` da los tres con intervalo bootstrap BCa y, como referencia, el intervalo clásico
(`t` de Student, chi-cuadrado y estadísticos de orden). Con datos asimétricos el clásico de la desviación estándar
suele quedarse corto.

Para las **cartas de control** con datos asimétricos usa `transform=` (`'boxcox'`, `'yeo-johnson'` o `'johnson'`):
`pp.imr_chart(x, transform='yeo-johnson')`. Los límites y las pruebas se calculan en la escala transformada y, por
defecto, el panel de valores individuales (o de medias) se dibuja en unidades originales con límites asimétricos
(`scale='transformed'` lo deja todo en la escala transformada).

Las cartas de medias (Xbar-R, Xbar-S) son bastante robustas a la no normalidad cuando los subgrupos tienen
más de 5 observaciones, por el teorema central del límite. Con subgrupos de 2 a 5 observaciones y datos
asimétricos la librería avisa, y la carta de **individuales (I-MR)** no tiene esa protección: con datos
asimétricos sus límites pueden dar falsas alarmas del lado de la cola larga.

---

### ¿Cuántas observaciones necesito para que la prueba de normalidad sea válida?

`diagnose()` y `normality_test()` usan `scipy.stats.normaltest` (D'Agostino-
Pearson). Se necesitan **al menos 8 observaciones**; con menos, la función
devuelve `is_normal=True` y `normality_p=NaN` para evitar resultados engañosos.

---

## Compatibilidad con seaborn, plotly y otras librerías

### ¿Puedo usar pccpy junto a seaborn?

Sí. pccpy usa matplotlib internamente y sus funciones `plot()` están aisladas con
`plt.rc_context({})`, de modo que los estilos de seaborn no afectan el aspecto de
los gráficos de pccpy.

```python
import seaborn as sns
import pccpy as pp

sns.set_theme(style="darkgrid")          # cambia el estilo global de matplotlib
carta = pp.imr_chart(x)
carta.plot()                             # se renderiza con los estilos internos de pccpy
```

---

### ¿Los gráficos de pccpy acumulan figuras abiertas?

`plot()` crea una figura nueva cada vez que se llama y **no la cierra**. En un
bucle largo esto genera la advertencia `More than 20 figures have been opened`.

Opciones para evitarlo:

```python
import matplotlib.pyplot as plt

# Opción 1: cerrar manualmente
for x_lote in lotes:
    fig = pp.imr_chart(x_lote).plot()
    fig.savefig(f"carta_{i}.png")
    plt.close(fig)

# Opción 2: usar save_plot() (cierra la figura internamente)
for i, x_lote in enumerate(lotes):
    pp.imr_chart(x_lote).save_plot(f"carta_{i}.png")

# Opción 3: cerrar todas al salir del bucle
for x_lote in lotes:
    carta = pp.imr_chart(x_lote)
    # … hacer algo con carta.to_frame() …
plt.close("all")
```

---

### ¿Puedo combinar pccpy con plotly?

Plotly y matplotlib son sistemas independientes. `plot()` devuelve un
`matplotlib.figure.Figure` que no se puede insertar directamente en plotly.

Para integrar en una app Dash o Plotly puedes convertir la figura:

```python
import plotly.tools as tls
import pccpy as pp

fig_mpl = pp.imr_chart(x).plot()
fig_plotly = tls.mpl_to_plotly(fig_mpl)  # conversión aproximada
```

O exportar como imagen PNG y usarla en plotly con `plotly.graph_objects.Image`.

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

## Datos de entrada

### ¿Mis datos tienen valores faltantes (NaN) o infinitos?

pccpy **no cancela el análisis**: filtra automáticamente los valores no finitos y
emite un `UserWarning` indicando cuántos y en qué posiciones. El análisis continúa
con los valores válidos restantes.

```python
import numpy as np, warnings
import pccpy as pp

x = [1.2, np.nan, 3.4, 2.8, np.inf, 3.1]
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    carta = pp.imr_chart(x)
# w[0].message describe los valores excluidos
# carta tiene 4 puntos (2 NaN/inf eliminados)
```

> Si quieres que los valores faltantes **sí detengan** el análisis, filtra el array
> antes de pasarlo: `x = x[np.isfinite(x)]` + comprueba que `len(x) > 0`.

---

### ¿Por qué aparece un `UserWarning` sobre columnas no numéricas en mi DataFrame?

Cuando pasas un DataFrame ancho con columnas de texto (etiquetas, categorías,
fechas), pccpy las ignora automáticamente y emite una advertencia:

```
UserWarning: Se ignoraron 1 columna(s) no numéricas del DataFrame: ['lote'].
Si querías usar una como identificador de subgrupo, pasa subgroup='lote'.
```

```python
import pandas as pd, pccpy as pp

df = pd.DataFrame({
    "lote":   ["A", "A", "B", "B", "C", "C"],
    "medida": [10.1, 9.9, 10.3, 10.0, 9.8, 10.2],
})

# ❌ columna 'lote' se ignora con advertencia
# carta = pp.xbar_r_chart(df)

# ✅ pasa 'lote' como identificador de subgrupo
carta = pp.xbar_r_chart(df, subgroup="lote", value="medida")
```

---

### ¿Puedo hacer `capability_analysis()` sin límites de especificación?

Sí. Desde v0.10.7 ya no es obligatorio pasar `lsl` o `usl`. Los índices que
dependen de especificaciones (Cp, Cpk, Pp, Ppk…) se devuelven como `NaN` y
`summary()` los marca con `*`.

```python
import pccpy as pp

# Solo estadísticos descriptivos y sigma_within / sigma_overall
r = pp.capability_analysis(x)
print(r.sigma_within, r.sigma_overall)  # valores válidos
print(r.cp)                             # nan
```

---

### ¿Qué pasa si todos mis datos son iguales (variación cero)?

Si la desviación estándar del proceso es cero (todos los valores idénticos),
pccpy emite un `UserWarning` y devuelve `NaN` para todos los índices de
capacidad en vez de lanzar `ZeroDivisionError`.

```python
import pccpy as pp, warnings

x = [10.0] * 30  # datos constantes
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    r = pp.capability_analysis(x, lsl=9, usl=11)
# w contiene la advertencia sobre variación cero
# r.cp, r.cpk, r.pp, r.ppk son NaN
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

### `ValueError: 'subgroup_size=1' da subgrupos de un solo elemento`

`xbar_r_chart` y otras cartas de subgrupos no pueden estimar la variación
**dentro** del subgrupo si cada subgrupo tiene una sola observación. Para
datos individuales usa `imr_chart` en su lugar:

```python
# ❌ no funciona con subgrupos de 1
# pp.xbar_r_chart(x, subgroup_size=1)

# ✅ carta correcta para datos individuales
carta = pp.imr_chart(x)
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
