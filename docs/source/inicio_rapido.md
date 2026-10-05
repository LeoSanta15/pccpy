# Inicio rápido

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(1)
x = rng.normal(100, 2, 60)
x[40:] += 3                                   # el proceso se desplaza

carta = pp.imr_chart(x, tests=(1, 2, 3, 4, 5, 6, 7, 8))
print(carta.summary())                        # resumen tipo sesión de Minitab
carta.violations()                            # DataFrame: panel, punto, prueba, descripción
carta.to_frame()                              # todos los valores, límites y pruebas fallidas
carta.plot()                                  # figura de matplotlib
```

Cada tipo de carta tiene su propia página en la {doc}`referencia/index`, con
ejemplos y la descripción exacta de cada parámetro (extraída directamente de los
docstrings, así que siempre coincide con el código instalado).

## Formatos de entrada para cartas de subgrupos

Las cartas `xbar_r_chart`, `xbar_s_chart`, `ewma_chart`, `cusum_chart`,
`ma_chart`, `imr_rs_chart`, `zone_chart`, `capability_analysis` y
`capability_sixpack` aceptan cinco formatos equivalentes:

```python
import pandas as pd

# 1. Matriz 2-D: una fila por subgrupo
g = rng.normal(100, 2, (20, 4))          # 20 subgrupos de tamaño 4
carta = pp.xbar_r_chart(g)

# 2. Vector 1-D + subgroup_size
v = rng.normal(100, 2, 80)               # 80 mediciones
carta = pp.xbar_r_chart(v, subgroup_size=4)

# 3. DataFrame ancho: una fila por subgrupo
df_wide = pd.DataFrame(g, columns=["a", "b", "c", "d"])
carta = pp.xbar_r_chart(df_wide)

# 4. DataFrame largo: una medición por fila
df_largo = pd.DataFrame({"lote": np.repeat(range(20), 4),
                          "medida": g.ravel()})
carta = pp.xbar_r_chart(df_largo, subgroup="lote", value="medida")
# Si solo hay una columna numérica además de subgroup, value se detecta sola.

# 5. Vector 1-D + subgroup_size con sobrante
v2 = rng.normal(100, 2, 82)             # 82 no es múltiplo de 4
# UserWarning: el último subgrupo (2 obs.) se grafica pero NO entra en los límites.
carta = pp.xbar_r_chart(v2, subgroup_size=4)
```

## Diagnóstico rápido del proceso

Cuando tienes datos pero no sabes aún qué análisis aplicar, comienza con
`diagnose()`. Calcula estadísticos descriptivos, prueba de normalidad,
detecta tendencias y valores atípicos, e indica la función de pccpy que
deberías usar a continuación.

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(0)
x = rng.normal(50, 2, 60)

d = pp.diagnose(x, lsl=44, usl=56)   # lsl/usl opcionales
print(d.summary())                    # resumen completo en texto
d.plot()                              # histograma + gráfico de secuencia
d.to_frame()                          # tabla resumen como DataFrame
d.to_excel("diagnostico.xlsx")        # exportar a Excel (requiere openpyxl)
```

La recomendación automática varía según lo que encuentre:

| Condición detectada | Función recomendada |
|---------------------|---------------------|
| Tendencia creciente o decreciente | `run_chart` |
| Con especificaciones, distribución normal | `capability_analysis` |
| Con especificaciones, distribución no normal | `capability_boxcox` |
| Sin especificaciones | `imr_chart` |

Consulta la página {doc}`diagnose` para todos los detalles.

## Carta de corridas y pre-control

```python
# Carta de corridas con 4 pruebas de aleatoriedad
rc = pp.run_chart(x)
print(rc.summary())   # p-valores de agrupamiento, mezclas, tendencias, oscilación
rc.plot()

# Pre-control (Shainin): semáforo verde/amarillo/rojo
pc = pp.precontrol(x, lsl=94, usl=106)
print(pc.summary())   # señales detectadas y conteo de zonas
pc.plot()
```

## EWMA y CUSUM para cartas de atributos

```python
defects = [3, 1, 4, 2, 0, 5, 2, 3, 1, 2]

# EWMA carta P
carta = pp.ewma_p_chart(defects, n=100)        # límites exactos transitorios

# CUSUM carta C
carta = pp.cusum_c_chart(defects)              # h=4, k=0.5 en unidades σ

# Con tamaños de muestra variables (P y U)
n_var = [100, 120, 95, 110, 105, 100, 115, 98, 107, 102]
carta = pp.ewma_p_chart(defects, n=n_var)
```

## Intervalos de tolerancia

```python
rng = np.random.default_rng(1)
x50 = rng.normal(100, 2, 50)

# Normal bilateral: con 95% de confianza, ≥95% de la población cae en (LI, LS)
res = pp.tolerance_interval(x50, coverage=0.95, confidence=0.95)
print(res.summary())   # LI, LS, factor k
res.plot()

# Unilateral (cota superior)
res_u = pp.tolerance_interval(x50, sides='upper')

# No paramétrico (requiere n mayor, p.ej. ≥300 para 95/95)
x300 = rng.normal(100, 2, 300)
res_np = pp.tolerance_interval(x300, method='nonparametric')
```

## Muestreo de aceptación

```python
# Z1.4 por atributos: lote N=1000, AQL=1%
plan = pp.acceptance_sampling_attributes(N=1000, aql=1.0)
print(plan.summary())   # n, Ac, Re, LTPD, AOQL
plan.plot()             # curva OC + curva AOQ

# Z1.9 por variables: lote N=500, AQL=1%, especificación unilateral
plan_v = pp.acceptance_sampling_variables(N=500, aql=1.0, spec_type='one')
# Evaluar una muestra real
muestra = rng.normal(10.5, 0.2, plan_v.n)
decision = plan_v.evaluate(muestra, usl=11.0)
print(decision)   # {'xbar': ..., 's': ..., 'Q_usl': ..., 'accept': True/False}

# Dodge-Romig: LTPD=5%, promedio de proceso=1%
plan_dr = pp.dodge_romig(N=500, ltpd=0.05, process_avg=0.01)
print(plan_dr.summary())
```

## MSA / Gage R&R

```python
import numpy as np, pccpy as pp
rng = np.random.default_rng(0)

# Datos: 10 partes × 3 operadores × 2 réplicas
data = rng.normal(0, 1, 10 * 3 * 2)

# Crossed Gage R&R (ANOVA)
grr = pp.gage_rr(data, parts=10, operators=3, replicates=2)
print(grr.summary())   # %Contribución, %Var. estudio, NDC
print(grr.anova_table)
grr.plot()

# Método Xbar-R (clásico AIAG)
grr_xr = pp.gage_rr(data, parts=10, operators=3, replicates=2, method='xbar_r')

# Estudio Tipo 1: sesgo y repetibilidad (25 mediciones de pieza de referencia)
ref_meas = rng.normal(10.02, 0.05, 25)
t1 = pp.gage_type1(ref_meas, reference=10.0, tolerance=0.5)
print(t1.summary())   # Sesgo, t-test, Cg, Cgk

# Linealidad y sesgo
refs       = np.repeat([2, 4, 6, 8, 10], 5)
mediciones = refs + rng.normal(0.05, 0.1, len(refs))
lin = pp.gage_linearity(mediciones, refs, tolerance=10.0)
print(lin.summary())  # Pendiente, R², Linealidad (%)

# Concordancia por atributos (Kappa)
import pandas as pd
clasificaciones = pd.DataFrame({
    'Op1': ['G', 'D', 'G', 'G', 'D'] * 4,
    'Op2': ['G', 'D', 'G', 'D', 'D'] * 4,
    'Op3': ['G', 'G', 'G', 'G', 'D'] * 4,
})
referencia = np.array(['G', 'D', 'G', 'G', 'D'] * 2)
atr = pp.attribute_agreement(clasificaciones, reference=referencia, replicates=2)
print(atr.summary())  # Kappa de Cohen por operador + Kappa de Fleiss
```

## Funciones desde estadísticos resumen

Cuando solo dispones de estadísticos agregados (media, desviación y n), sin los
datos individuales, usa las variantes `_summary`:

```python
# Intervalo de tolerancia normal bilateral 95/95 desde resumen
res = pp.tolerance_interval_summary(
    mean=100.0, std=2.0, n=50,
    coverage=0.95, confidence=0.95, sides="two",
)
print(res.summary())   # mismos campos que tolerance_interval

# Estudio Tipo 1 (sesgo y repetibilidad) desde media, s y n
t1 = pp.gage_type1_summary(
    mean=10.02, std=0.05, n=25,
    reference=10.0, tolerance=0.5,
)
print(t1.summary())    # Sesgo, t-stat, Cg, Cgk

# Capacidad del proceso desde estadísticos resumen
rs = pp.capability_analysis_summary(
    mean=50.0, std_overall=2.0, n=200,
    lsl=44, usl=56,
    std_within=1.8,       # opcional: si no se da, Cp/Cpk = NaN
)
print(rs.summary())    # Pp, Ppk y (si se da std_within) Cp, Cpk
```

Estos resultados devuelven el mismo tipo de objeto que su contraparte con datos
individuales, por lo que `to_frame()`, `summary()` y demás métodos funcionan igual.

## Fase I y Fase II — congelar límites históricos

En un estudio de **Fase I** calculas los límites con datos históricos y verificas
que el proceso estaba bajo control. En **Fase II** aplicas esos mismos límites a
producción nueva para detectar cambios.

`phase_one()` hace la Fase I **de forma iterativa**: calcula la carta, excluye los puntos con señal,
recalcula los límites y repite hasta que no quede ninguna señal. Con `phase2()` aplicas los límites
resultantes a los datos nuevos:

```python
import numpy as np, pccpy as pp

# ── Fase I: datos históricos ────────────────────────────────────
fase1 = pp.phase_one(pp.imr_chart, x_historico, tests=(1, 2, 3))
print(fase1.summary())        # puntos excluidos, límites congelados y cada pasada
fase1.excluded                # posiciones (base 0) de los puntos excluidos
fase1.chart.plot()            # carta con los límites definitivos

# ── Fase II: datos nuevos con los límites congelados ────────────
carta_ii = fase1.phase2(x_nuevo, tests=(1, 2))
carta_ii.plot()
```

Funciona con `imr_chart`, `xbar_r_chart`, `xbar_s_chart`, `p_chart`, `np_chart`, `c_chart` y `u_chart`
(en las de atributos, pasa `n=`). Tres salvaguardas evitan «limpiar» un proceso que no es estable:
`max_iterations`, `min_points` y `max_excluded` (por defecto no se excluye más del 25 % de los puntos);
si saltan, el resultado no converge y se avisa. **Excluye puntos solo si has encontrado y corregido su causa especial.**

Si prefieres hacerlo a mano, fija la media y la sigma estimadas (las claves de `params` son
`'media'` y `'sigma'`):

```python
carta_i = pp.imr_chart(x_historico, tests="all")
mu_i    = carta_i.params[0]["media"]
sigma_i = carta_i.params[0]["sigma"]
carta_ii = pp.imr_chart(x_nuevo, mu=mu_i, sigma=sigma_i, tests=(1, 2))

# Xbar-R con límites fijados
carta_ii = pp.xbar_r_chart(g_nuevo, mu=mu_i, sigma=sigma_i)
```

Para marcar múltiples etapas dentro de un mismo gráfico (Minitab "stages"):

```python
etapas = np.r_[np.ones(50), np.full(50, 2)]   # 50 puntos en cada etapa
carta = pp.imr_chart(x, stages=etapas, tests="all")
# Cada etapa tiene sus propios límites calculados por separado
```

## Fechas (o lotes) en el eje x

Si los datos son una serie de pandas con **índice de fechas** (o de texto, como números de lote), la carta
las conserva: el eje x se rotula con ellas, `to_frame()` y `violations()` añaden la columna `etiqueta` y
`summary()` muestra la fecha junto a cada punto. Los puntos siguen graficándose por orden de muestreo
(como Minitab); las fechas solo rotulan el eje.

```python
import pandas as pd

serie = pd.Series(x, index=pd.date_range("2026-03-01", periods=len(x), freq="D"))
carta = pp.imr_chart(serie, tests=(1, 2))
carta.plot()                 # eje «Fecha»
carta.violations()           # incluye la columna «etiqueta» con la fecha de cada señal
```

También funciona con subgrupos (`subgroup_size=`, un DataFrame con fechas en las filas, o `subgroup=` con
fechas) y con las cartas de atributos y multivariadas. Para otras etiquetas, usa
`carta.with_labels([...])` (una por punto graficado).

## Guardar gráficos

Todos los resultados tienen `save_plot()`:

```python
# Guardar como PNG, PDF o SVG con una sola línea
carta.save_plot("carta_imr.png")                 # 150 dpi por defecto
carta.save_plot("carta_imr.pdf")                 # vectorial
cap.save_plot("capacidad.png",  dpi=200)         # alta resolución
tol.save_plot("tolerancia.svg")                  # editable
# Pasar kwargs del método plot()
carta.save_plot("carta_sinzonas.png", zones=False)
```

## Un vistazo por tema

- **Variables** (I-MR, Xbar-R, Xbar-S, media móvil, Z-MR, I-MR-R/S, Zona):
  {doc}`referencia/variables` y {doc}`referencia/avanzadas`.
- **Atributos** (P, NP, C, U, Laney P′/U′): {doc}`referencia/atributos`.
- **Tiempo ponderado** (EWMA, CUSUM): {doc}`referencia/tiempo_ponderado`.
- **Carta de corridas, pre-control, EWMA/CUSUM atributos**:
  {doc}`referencia/run_chart_y_precontrol`.
- **Multivariadas** (T², varianza generalizada, MEWMA, MCUSUM, con etapas y
  Box-Cox): {doc}`referencia/multivariadas`.
- **Capacidad del proceso** (incluyendo DPMO y nivel sigma):
  {doc}`referencia/capacidad`.
- **Intervalos de tolerancia**: {doc}`referencia/tolerancia`.
- **Muestreo de aceptación** (Z1.4, Z1.9, Dodge-Romig):
  {doc}`referencia/muestreo_aceptacion`.
- **MSA / Gage R&R** (cruzado, anidado, Tipo 1, linealidad, atributos):
  {doc}`referencia/msa`.
- **Normalidad, Pareto y constantes**: {doc}`referencia/normalidad_y_herramientas`
  y {doc}`referencia/constantes`.
- **Objetos de resultado** (`ControlChart`, `MultivariateChart`, `Panel`, y los
  resultados de capacidad, normalidad y análisis de proceso):
  {doc}`referencia/resultados`.
