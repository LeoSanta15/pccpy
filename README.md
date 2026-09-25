# pccpy

[![PyPI version](https://img.shields.io/pypi/v/pccpy.svg)](https://pypi.org/project/pccpy/)
[![Python](https://img.shields.io/pypi/pyversions/pccpy.svg)](https://pypi.org/project/pccpy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Control Estadístico de Procesos (SPC) en Python, al estilo Minitab.**

`pccpy` es una librería de SPC en español diseñada para ingenieros y técnicos que conocen
Minitab y quieren hacer el mismo análisis desde Python. Todas las convenciones de
nomenclatura (LCS/LCI, LEI/LES, Cp/Cpk/Pp/Ppk, Z.Bench, PPM, Anderson-Darling),
los métodos de estimación de sigma y las 8 pruebas de causas especiales siguen lo que
documenta Minitab.

---

## Índice

1. [Instalación](#instalación)
2. [Inicio rápido](#inicio-rápido)
3. [Cartas de variables](#cartas-de-variables)
   - [I-MR](#carta-i-mr)
   - [Xbar-R y Xbar-S](#cartas-xbar-r-y-xbar-s)
   - [Formatos de entrada de datos](#formatos-de-entrada-de-datos)
   - [Parámetros históricos y etapas](#parámetros-históricos-y-etapas)
4. [Cartas de atributos](#cartas-de-atributos)
5. [Cartas de tiempo ponderado](#cartas-de-tiempo-ponderado)
   - [EWMA](#ewma)
   - [CUSUM](#cusum)
   - [Media móvil](#media-móvil)
6. [Cartas avanzadas](#cartas-avanzadas)
   - [Z-MR (corridas cortas)](#z-mr-corridas-cortas)
   - [I-MR-R/S (variación entre/dentro)](#i-mr-rs-variación-entrodentro)
   - [Eventos raros (G y T)](#eventos-raros-g-y-t)
7. [Cartas multivariadas](#cartas-multivariadas)
   - [T² de Hotelling](#t²-de-hotelling)
   - [Varianza generalizada](#varianza-generalizada)
   - [MEWMA](#mewma)
   - [MCUSUM](#mcusum)
   - [Etapas y Box-Cox en cartas multivariadas](#etapas-y-box-cox-en-cartas-multivariadas)
8. [Pruebas de causas especiales](#pruebas-de-causas-especiales)
9. [Visualización de las cartas](#visualización-de-las-cartas)
10. [Capacidad del proceso](#capacidad-del-proceso)
11. [Normalidad, Pareto y constantes SPC](#normalidad-pareto-y-constantes-spc)
12. [Acceso a los datos del resultado](#acceso-a-los-datos-del-resultado)
13. [Validación](#validación)
14. [Desarrollo](#desarrollo)
15. [Licencia](#licencia)

---

## Instalación

```bash
pip install pccpy
```

Desde GitHub (versión de desarrollo):

```bash
pip install git+https://github.com/LeoSanta15/pccpy.git
```

Requiere Python ≥ 3.9 con NumPy, SciPy, pandas y matplotlib.

---

## Inicio rápido

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(1)
x = rng.normal(100, 2, 60)
x[40:] += 3           # el proceso se desplaza en la observación 41

# Calcular carta I-MR con las 8 pruebas de causas especiales
carta = pp.imr_chart(x, tests=(1, 2, 3, 4, 5, 6, 7, 8))

print(carta.summary())        # resumen tipo sesión de Minitab
carta.violations()            # DataFrame: panel, punto, prueba, descripción
carta.to_frame()              # todos los valores, límites y pruebas fallidas
carta.plot()                  # figura de matplotlib (se muestra con plt.show())
```

---

## Cartas de variables

### Carta I-MR

La carta **Individuales y Rango Móvil** es la opción estándar cuando cada observación
es una medición única (no hay subgrupos). Produce dos paneles:
- **Panel I:** valores individuales con límites ±3σ en torno a la media.
- **Panel MR:** rangos móviles sucesivos con su límite superior.

```python
import numpy as np
import pccpy as pp

x = np.array([10.2, 10.5, 9.8, 10.1, 10.4, 9.9, 10.3, 10.6,
               9.7, 10.0, 10.2, 10.8, 9.6, 10.1, 10.3])

carta = pp.imr_chart(
    x,
    span=2,                # longitud del rango móvil (defecto: 2, igual que Minitab)
    sigma_method="mr",     # estimador de sigma: 'mr' (defecto), 'median_mr', 'mssd'
    tests=(1, 2, 3),       # qué pruebas de causas especiales activar
)
print(carta.summary())
```

**Opciones de `sigma_method`:**

| Método | Cálculo | Cuándo usarlo |
|--------|---------|---------------|
| `'mr'` | `MR_prom / d2` | por defecto; el mismo que Minitab |
| `'median_mr'` | `mediana(MR) / 0.9540` | más robusto ante valores atípicos (solo span=2) |
| `'mssd'` | `√(MSSD / 2)` | cuando no hay observaciones consecutivas correladas |

---

### Cartas Xbar-R y Xbar-S

Cuando los datos se recogen en **subgrupos** (varias mediciones por muestra), las
cartas **Xbar-R** (subgrupos pequeños, n ≤ 8) y **Xbar-S** (subgrupos grandes, n > 8)
estiman sigma usando la variación **dentro** de cada subgrupo, lo que las hace más
sensibles a desplazamientos de la media que la carta I-MR.

```python
datos = np.array([
    [20.1, 20.3, 20.0, 20.2, 19.9],
    [20.4, 20.1, 20.5, 20.2, 20.3],
    # ... una fila por subgrupo
])

carta_r = pp.xbar_r_chart(
    datos,
    sigma_method="rbar",  # 'rbar' (defecto) o 'pooled'
    tests=(1, 2, 3, 4, 5, 6, 7, 8),
)

carta_s = pp.xbar_s_chart(
    datos,
    sigma_method="sbar",  # 'sbar' (defecto) o 'pooled'
)
```

**Opciones de `sigma_method` para Xbar:**

| Método | Cálculo | Cuándo usarlo |
|--------|---------|---------------|
| `'rbar'` | `R_prom / d2(n)` | Xbar-R, subgrupos de tamaño fijo (igual que Minitab) |
| `'pooled'` | `S_pooled / c4(n_total)` | Xbar-R o Xbar-S, mejor estimación con muchos subgrupos |
| `'sbar'` | `S_prom / c4(n)` | Xbar-S, subgrupos de tamaño fijo (igual que Minitab) |

---

### Formatos de entrada de datos

Todas las cartas de variables aceptan tres formatos equivalentes:

```python
# 1. Matriz 2-D: cada fila es un subgrupo
datos_2d = np.array([[20.1, 20.3, 20.0],
                     [20.4, 20.1, 20.5],
                     [19.9, 20.2, 20.1]])
pp.xbar_r_chart(datos_2d)

# 2. Vector 1-D + tamaño de subgrupo fijo
vector = datos_2d.ravel()            # [20.1, 20.3, 20.0, 20.4, 20.1, 20.5, ...]
pp.xbar_r_chart(vector, subgroup_size=3)

# 3. Vector 1-D + identificador de subgrupo (permite tamaños desiguales)
ids = np.repeat(["S1", "S2", "S3"], 3)
pp.xbar_r_chart(vector, subgroup=ids)

# También acepta pandas Series y DataFrame directamente
import pandas as pd
df = pd.DataFrame({"medida": vector, "subgrupo": ids})
pp.xbar_r_chart(df["medida"], subgroup=df["subgrupo"])
```

---

### Parámetros históricos y etapas

Equivalente a *Opciones de estimación* y *Etapas* en Minitab:

```python
# Parámetros conocidos (no se estiman de los datos)
pp.imr_chart(x, mu=100.0, sigma=2.0)

# Etapas: los límites se calculan de forma independiente por etapa
etapas = ["Antes"] * 30 + ["Después"] * 30
carta = pp.imr_chart(x, stages=etapas)
carta.params        # lista de dicts, uno por etapa
carta.params[0]     # {'stage': 'Antes', 'media': ..., 'sigma': ..., ...}
carta.params[1]     # {'stage': 'Después', 'media': ..., 'sigma': ..., ...}

# Combinación: parámetros históricos + etapas (los mismos parámetros para todas)
pp.imr_chart(x, mu=100, sigma=2, stages=etapas)
```

---

## Cartas de atributos

Cuando la característica de calidad es **discreta** (piezas defectuosas, número de
defectos) se usan cartas de atributos. Las cartas de Laney corrigen la
**sobredispersión** (variabilidad mayor a la esperada por el modelo teórico), un
problema frecuente con tamaños de muestra grandes.

```python
# P: fracción defectuosa (n puede variar entre muestras)
defectuosos = np.array([3, 5, 2, 4, 6, 1, 3, 5, 2, 4])
n_muestral  = np.full(10, 200)    # tamaño de cada muestra
pp.p_chart(defectuosos, n=n_muestral)

# NP: número de defectuosos (requiere n constante)
pp.np_chart(defectuosos, n=200)

# C: número de defectos por unidad (n fijo = 1 unidad por muestra)
defectos = np.array([2, 1, 3, 0, 4, 2, 1, 3, 2, 1])
pp.c_chart(defectos)

# U: tasa de defectos por unidad (n puede variar)
n_unidades = np.array([1, 1, 2, 1, 2, 1, 1, 2, 1, 2])
pp.u_chart(defectos, n=n_unidades)

# Laney P': igual que P pero corrige sobredispersión (phi != 1)
pp.laney_p_chart(defectuosos, n=n_muestral)

# Laney U': igual que U pero corrige sobredispersión
pp.laney_u_chart(defectos, n=n_unidades)
```

Cuando `n` es un escalar se aplica el mismo tamaño a todas las muestras. Con `n`
variable los límites se calculan individualmente para cada punto.

---

## Cartas de tiempo ponderado

### EWMA

La carta **Media Móvil Exponencialmente Ponderada** es más sensible que I-MR a
pequeños desplazamientos de la media (típicamente ≤ 1.5σ). Los límites exactos se
ensanchan en los primeros puntos hasta estabilizarse, igual que Minitab.

```python
carta = pp.ewma_chart(
    x,
    weight=0.2,    # λ: factor de suavizado (0 < λ ≤ 1); menor = más memoria
    k=3.0,         # multiplicador de sigma para los límites (defecto: 3)
    tests=(1,),    # solo la prueba 1 tiene sentido en EWMA
)
# El 'sigma_method' de la carta subyacente se configura con sigma_method='mr'
```

**Guía de selección de λ:**

| λ | Detecta mejor | Memoria |
|---|---------------|--------|
| 0.05 – 0.10 | desplazamientos muy pequeños (¼σ) | mucha |
| 0.20 | desplazamientos moderados (½σ – 1σ) | moderada (recomendado Minitab) |
| 0.40+ | parecido a carta Shewhart | poca |

---

### CUSUM

La carta **Suma Acumulada** también detecta pequeños desplazamientos. Usa el esquema
tabular de Hawkins: dos acumuladores (superior `C⁺` e inferior `C⁻`) que parten de 0
y se comparan con el límite de decisión `H`.

```python
carta = pp.cusum_chart(
    x,
    h=4.0,    # límite de decisión H (en unidades de sigma); defecto: 4 (= 4σ)
    k=0.5,    # zona de referencia K (en unidades de sigma); defecto: 0.5
    # Con H=4, K=0.5 el ARL en control es ≋370 (estándar de la industria)
    tests=(1,),
)
```

> **Regla práctica:** `H = 4σ` y `K = 0.5σ` equilibran la detección de un desplazamiento
> de 1σ con un ARL fuera de control ≈ 10 y un ARL en control ≈ 370.

---

### Media móvil

La carta **MA** promedia los últimos `length` puntos para suavizar el ruido.
Los primeros `length - 1` puntos usan el promedio de los datos disponibles,
por lo que sus límites son más amplios.

```python
pp.ma_chart(
    x,
    length=5,   # ventana de la media móvil; defecto: 3
    tests=(1,),
)
```

---

## Cartas avanzadas

### Z-MR (corridas cortas)

Cuando se fabrican **piezas con especificaciones distintas** (distintas medias o
variabilidades nominales) no se pueden trazar en la misma carta I-MR estándar.
La carta **Z-MR** estandariza cada observación con los parámetros de su parte,
permitiendo visualizar todas en una sola carta con límites ±3.

```python
partes   = ["A"] * 10 + ["B"] * 10 + ["A"] * 10
medidas  = np.r_[
    rng.normal(50, 1, 10),   # parte A: media 50, sigma 1
    rng.normal(80, 2, 10),   # parte B: media 80, sigma 2
    rng.normal(50, 1, 10),   # parte A de nuevo
]

carta = pp.zmr_chart(
    medidas,
    partes,
    sigma_method="by_part",  # 'constant', 'relative', 'by_part', 'by_run'
    # mu y sigma: dict {parte: valor} para parámetros históricos o nominales
    # mu={"A": 50, "B": 80}, sigma={"A": 1, "B": 2}
)
```

**Opciones de `sigma_method` para Z-MR:**

| Método | Descripción |
|--------|-------------|
| `'constant'` | misma sigma para todas las partes |
| `'relative'` | sigma proporcional a la media de la parte |
| `'by_part'` | sigma estimada por rango móvil dentro de cada parte (defecto) |
| `'by_run'` | sigma estimada por rango móvil dentro de cada corrida (bloque consecutivo) |

---

### I-MR-R/S (variación entre/dentro)

Cuando los subgrupos tienen una variación **entre subgrupos** grande (diferencias
de operario, turno, lote), la carta Xbar-R genera falsas alarmas porque su límite
de control solo refleja la variación **dentro**. La carta **I-MR-R/S** descompone
es dos fuentes y las trata por separado.

```python
# sub: matriz (n_subgrupos x tamaño_subgrupo)
sub = rng.normal(20, 1, (25, 5)) + rng.normal(0, 1.5, (25, 1))  # variación entre grupos

carta = pp.imr_rs_chart(
    sub,
    within="r",   # 'r' (rango, defecto) o 's' (desviación estándar)
)
carta.params[0]
# {'sigma_dentro': 0.97, 'sigma_entre': 1.48, 'sigma_entre_dentro': 1.79, ...}
```

---

### Eventos raros (G y T)

Cuando los eventos son tan infrecuentes que las cartas P o C darían muchos
puntos en cero, se usan las cartas G (número de casos/piezas entre eventos) y
T (tiempo entre eventos).

```python
# G: número de casos entre eventos (distribución geométrica)
entre_eventos = rng.geometric(0.02, 40) - 1   # p = probabilidad del evento
pp.g_chart(entre_eventos)

# T: tiempo entre eventos (distribución Weibull o exponencial)
tiempos = rng.weibull(1.5, 40) * 30
pp.t_chart(tiempos)          # Weibull (defecto)
pp.t_chart(tiempos, dist="exp")  # exponencial
```

Los límites de la carta G se basan en percentiles exactos de la distribución
geométrica; los de la carta T en los de la Weibull o exponencial ajustada por
máxima verosimilitud.

---

## Cartas multivariadas

### T² de Hotelling

Equivalente multivariado de la carta I-MR o Xbar. Detecta desplazamientos
simultáneos en varias variables correlacionadas. El método `contributions()`
identifica qué variable(s) causaron la señal.

```python
Sigma = [[1, .6, .3], [.6, 1, .2], [.3, .2, 1]]
hist  = rng.multivariate_normal([0, 0, 0], Sigma, 100)   # datos de Fase I
nuev  = rng.multivariate_normal([0, 0, 0], Sigma, 50)
nuev[35:, 2] += 4     # variable 3 se desplaza en el punto 36

# --- Fase I: parámetros estimados de los mismos datos ---
carta1 = pp.t2_chart(hist)
print(carta1.summary())

# --- Fase II: parámetros tomados del periodo histórico ---
carta2 = pp.t2_chart(
    nuev,
    mu=hist.mean(axis=0),
    cov=np.cov(hist, rowvar=False),
    n_hist=100,     # n de la estimación histórica (afecta el límite)
)

# Diagnosticar: ¿qué variable causó la señal en el punto 36?
carta2.contributions(36)     # pandas Series con la contribución de cada variable

# Con subgrupos (una fila = una observación; subgroup_size agrupa de a n filas)
pp.t2_chart(nuev, subgroup_size=5)

# Con DataFrame: los nombres de columna aparecen en contributions()
import pandas as pd
df = pd.DataFrame(nuev, columns=["Temperatura", "Presión", "Flujo"])
pp.t2_chart(df)
```

**Tipo de límite según lo que se provea:**

| `mu` / `cov` | `n_hist` | Distribución | Fase |
|---|---|---|---|
| No dados | — | Beta (individuales) / F (subgrupos) | I |
| Dados | Dado | F ajustada a n_hist | II |
| Dados | No dado | χ² | parámetros conocidos |

---

### Varianza generalizada

Panel complementario al T² para **datos en subgrupos**: monitorea la dispersión
multivariada mediante el determinante de la matriz de covarianza muestral `|S|`.

```python
pp.generalized_variance_chart(
    nuev,
    subgroup_size=5,
    mu=hist.mean(axis=0),
    cov=np.cov(hist, rowvar=False),
)
```

---

### MEWMA

Versión multivariada de la carta EWMA. Muy sensible a desplazamientos pequeños
y sostenidos en el vector de medias.

```python
carta = pp.mewma_chart(
    nuev,
    mu=hist.mean(axis=0),
    cov=np.cov(hist, rowvar=False),
    weight=0.1,    # λ (defecto: 0.1)
    arl=200,       # ARL objetivo en control (el límite H se calcula automáticamente)
)

# Calcular el límite H por separado
H = pp.mewma_limit(p=3, weight=0.1, arl=200)
print(f"H = {H:.3f}")   # p: número de variables
```

---

### MCUSUM

Versión multivariada de la carta CUSUM (esquema de Crosier). También detecta
pequeños desplazamientos sostenidos.

```python
carta = pp.mcusum_chart(
    nuev,
    mu=hist.mean(axis=0),
    cov=np.cov(hist, rowvar=False),
    k=0.5,     # zona de referencia (defecto: 0.5)
    arl=200,   # el límite H se calcula automáticamente
)

H = pp.mcusum_limit(p=3, k=0.5, arl=200)
```

---

### Etapas y Box-Cox en cartas multivariadas

Las 4 cartas multivariadas (T², varianza generalizada, MEWMA y MCUSUM) aceptan
`stages` y `boxcox`, igual que las cartas univariadas:

```python
etapas = [1] * 40 + [2] * 40

# Sin mu/cov: cada etapa re-estima sus parámetros
c = pp.t2_chart(datos, stages=etapas)
c.stage_mean[1]     # vector de medias de la etapa 1
c.stage_mean[2]     # vector de medias de la etapa 2
c.contributions(45) # usa la media/covarianza de la etapa del punto 45

# Con mu/cov: los mismos parámetros en todas las etapas
pp.t2_chart(datos, mu=mu, cov=cov, n_hist=100, stages=etapas)

# MEWMA y MCUSUM reinician el acumulador al empezar cada etapa
pp.mewma_chart(datos, stages=etapas)
pp.mcusum_chart(datos, stages=etapas)

# Box-Cox: estima una lambda por variable (no compatible con mu/cov históricos)
c = pp.t2_chart(datos_positivos, boxcox=True)
c.params[0]["lambda_boxcox"]    # {'Var1': 0.42, 'Var2': 1.13, ...}
pp.mewma_chart(datos_positivos, boxcox=True)
pp.mcusum_chart(datos_positivos, boxcox=True)
```

---

## Pruebas de causas especiales

`pccpy` implementa las **8 pruebas de Western Electric / Nelson** tal como
las documenta Minitab, con sus parámetros K por defecto:

| Nú | Descripción | K defecto | Equivalente Minitab |
|----|-------------|-----------|---------------------|
| 1 | 1 punto más allá de Kσ | 3 | Prueba 1 |
| 2 | K puntos consecutivos en el mismo lado de la LC | 9 | Prueba 2 |
| 3 | K puntos consecutivos en tendencia (subiendo o bajando) | 6 | Prueba 3 |
| 4 | K puntos alternando arriba/abajo | 14 | Prueba 4 |
| 5 | 2 de 3 puntos más allá de 2σ en el mismo lado | 2 | Prueba 5 |
| 6 | 4 de 5 puntos más allá de 1σ en el mismo lado | 4 | Prueba 6 |
| 7 | K puntos consecutivos entre ±1σ | 15 | Prueba 7 |
| 8 | K puntos consecutivos en lados alternos de la LC más allá de 1σ | 8 | Prueba 8 |

```python
# Seleccionar pruebas y ajustar parámetros
carta = pp.imr_chart(
    x,
    tests=(1, 2, 5),            # solo activar las pruebas 1, 2 y 5
    test_params={2: 7, 5: 3},   # cambiar el K de la prueba 2 a 7 y el de la 5 a 3
)

# Activar todas las pruebas
carta = pp.imr_chart(x, tests="all")

# Sin pruebas (solo calcular los límites)
carta = pp.imr_chart(x, tests=None)

# Ver los puntos fuera de control
carta.violations()          # DataFrame: panel, punto, prueba, valor, descripcion
carta.in_control            # True si ninguna prueba falló
carta.panels[0].flagged     # índices (base 0) de puntos marcados en el panel I
```

Cada tipo de carta aplica el subconjunto que corresponde:
- **Completo (1-8):** carta I, Xbar, Z
- **Básicas (1-4):** carta MR, R, S, G, T, atributos (P, NP, C, U, Laney)
- **Solo prueba 1:** EWMA, CUSUM, MA, T², MEWMA, MCUSUM

---

## Visualización de las cartas

Todas las cartas se grafican con `plot_control_chart()`. Los gráficos incluyen
por defecto las **líneas de zonas ±1σ y ±2σ** (en gris punteado), igual que
Minitab, y marcan en rojo los puntos que fallan alguna prueba con el número
de la prueba.

```python
import matplotlib.pyplot as plt

carta = pp.imr_chart(x, tests=(1, 2, 3))

# Con zonas σ visibles (por defecto)
fig = pp.plot_control_chart(carta)
plt.show()

# Sin zonas (solo LCS, LC, LCI)
fig = pp.plot_control_chart(carta, zones=False)

# Con título personalizado y tamaño de figura
fig = pp.plot_control_chart(carta, title="Diámetro del eje (mm)", figsize=(14, 7))

# Acceso directo desde el objeto carta
carta.plot(title="Mi carta")
```

Las **zonas sigma** en la carta permiten aplicar visualmente las pruebas 5, 6, 7 y 8:
- **Zona A** (±2σ a ±3σ): p. ej. prueba 5 — 2 de 3 puntos en zona A
- **Zona B** (±1σ a ±2σ): p. ej. prueba 6 — 4 de 5 puntos en zona B o más allá
- **Zona C** (0 a ±1σ): p. ej. prueba 7 — 15 puntos consecutivos en zona C

---

## Capacidad del proceso

### Capacidad normal

```python
datos = rng.normal(10, 0.1, 100)

res = pp.capability_analysis(
    datos,
    lsl=9.7,           # Límite de Especificación Inferior
    usl=10.3,          # Límite de Especificación Superior
    target=10.0,       # objetivo (para Cpm; opcional)
    subgroup_size=5,   # con subgrupos: sigma_dentro ≠ sigma_general
)
print(res.summary())
# Cp, CPL, CPU, Cpk, Pp, PPL, PPU, Ppk, Cpm, Z.Bench sup/inf, PPM total

res.to_frame()   # todos los índices como DataFrame
res.plot()       # histograma con curvas dentro / general y especificaciones
```

**Diferencia Cp/Cpk vs Pp/Ppk:**

| Índice | σ usada | Interpreta |
|--------|---------|------------|
| Cp, Cpk | sigma **dentro** de subgrupos | capacidad potencial del proceso estable |
| Pp, Ppk | sigma **general** (todos los datos) | rendimiento real incluyendo variación entre subgrupos |

Si el proceso está en control, Cpk ≈ Ppk. Una diferencia grande indica inestabilidad
o variación entre subgrupos.

---

### Capacidad no normal

Cuando los datos no siguen una distribución normal (confirmado con `normality_test`)
se pueden usar 9 distribuciones alternativas:

```python
res_nn = pp.capability_nonnormal(
    datos,
    lsl=1.0,
    usl=20.0,
    distribution="weibull",   # ver lista abajo
)
print(res_nn.summary())
```

**Distribuciones disponibles:**
`"normal"`, `"lognormal"`, `"weibull"`, `"gamma"`, `"exponential"`,
`"loglogistic"`, `"logistic"`, `"largest_extreme"`, `"smallest_extreme"`

Los parámetros se ajustan por máxima verosimilitud. Los índices Pp/Ppk se calculan
por el **método de percentiles** (ISO 22514-2), que es compatible con Minitab.

---

### Capacidad con transformación Box-Cox

```python
res_bc = pp.capability_boxcox(
    datos,
    lsl=1.0,
    usl=20.0,
    # lam=None  # si es None, se estima por máxima verosimilitud
)
print(res_bc.summary())
res_bc.transform     # {'lambda': 0.42}
```

---

### Capability Sixpack

Genera las **6 vistas** del Capability Sixpack de Minitab en una sola figura:
carta de control (dentro), rango/desviación (dentro), últimas 25 obs/subgrupos,
histograma de capacidad, gráfico de probabilidad normal y gráfico de capacidad.

```python
fig, res, carta = pp.capability_sixpack(
    datos,
    lsl=9.7,
    usl=10.3,
    subgroup_size=5,
    tests=(1,),
)
plt.show()
# fig: figura de matplotlib
# res: CapabilityResult con todos los índices
# carta: ControlChart (Xbar-R, Xbar-S o I-MR según el tamaño de subgrupo)
```

---

## Normalidad, Pareto y constantes SPC

### Prueba de normalidad

```python
result = pp.normality_test(
    datos,
    method="ad",      # 'ad' Anderson-Darling (defecto), 'shapiro', 'dagostino'
)
print(result.summary())
# Estadístico: 0.312, Valor p: 0.534, Conclusión: no se rechaza normalidad (α=0.05)

result.statistic    # valor del estadístico
result.pvalue       # valor p
result.normal       # True si no se rechaza normalidad a α = 0.05

# Gráfico de probabilidad normal con Anderson-Darling
pp.probability_plot(datos)
```

---

### Pareto

```python
defectos = ["Rayado", "Abolladura", "Rayado", "Pintura", "Rayado",
             "Abolladura", "Otro", "Rayado", "Pintura", "Abolladura"]

tabla = pp.pareto(defectos)
print(tabla)
#       categoria  frecuencia  porcentaje  acumulado
# 0       Rayado           4        40.0       40.0
# 1  Abolladura           3        30.0       70.0
# 2      Pintura           2        20.0       90.0
# 3         Otro           1        10.0      100.0

pp.plot_pareto(tabla)   # diagrama de Pareto con curva acumulada
```

---

### Constantes SPC

Calculadas por **integración numérica** para cualquier `n ≥ 2` —no solo para los
valores tabulados hasta n = 25 que suelen publicarse en libros.

```python
pp.d2(5)   # 2.3259  (factor para estimar sigma desde R; n=5)
pp.d3(5)   # 0.8641  (para el límite del rango móvil)
pp.c4(5)   # 0.9400  (factor para estimar sigma desde s)
pp.c5(5)   # 0.3412  (para el límite de la desviación estándar)

# Tabla completa de constantes para n=5
pp.control_chart_constants(5)
# {'n': 5, 'd2': 2.326, 'd3': 0.864, 'c4': 0.940, 'c5': 0.341,
#  'A2': 0.577, 'A3': 1.342, 'D3': 0.0, 'D4': 2.115, 'B3': 0.0, 'B4': 2.089}
```

---

## Acceso a los datos del resultado

Todas las cartas de control devuelven un objeto `ControlChart` (las multivariadas
devuelven `MultivariateChart`). Se puede acceder a todos los datos calculados:

```python
carta = pp.imr_chart(x, tests=(1, 2, 3))

# --- Acceso por nombre de panel ---
panel_i  = carta["I"]    # panel de individuales
panel_mr = carta["MR"]   # panel de rango móvil

# Arrays NumPy directos
panel_i.values    # valores graficados
panel_i.center    # línea central (LC)
panel_i.ucl       # límite de control superior (LCS)
panel_i.lcl       # límite de control inferior (LCI)
panel_i.sigma     # sigma estimada punto a punto
panel_i.stage     # etiqueta de etapa de cada punto
panel_i.flagged   # índices base-0 de puntos marcados

# --- DataFrame de un panel ---
panel_i.to_frame()
# columnas: punto, etapa, valor, LC, LCS, LCI, pruebas_fallidas

# --- DataFrame ancho (todos los paneles) ---
carta.to_frame()
# columnas: punto, etapa, I_valor, I_LC, I_LCS, I_LCI, I_pruebas_fallidas,
#            MR_valor, MR_LC, MR_LCS, MR_LCI, MR_pruebas_fallidas

# --- Puntos fuera de control ---
carta.violations()
# columnas: panel, punto, prueba, valor, descripcion

# --- Parámetros estimados ---
carta.params        # lista de dicts, uno por etapa
carta.params[0]     # {'stage': 1, 'media': 10.2, 'sigma': 0.31, 'MR_prom': 0.35, 'n': 30}

# --- Estado del proceso ---
carta.in_control    # True si no hay ningún punto fuera de control
carta.summary()     # resumen en texto

# --- Acceso programatico a violaciones por prueba ---
carta.panels[0].violations   # dict {prueba: array de índices}
```

---

## Validación

186 pruebas automatizadas. Las referencias son independientes de pccpy:

- Constantes d2, d3, c4 frente a tablas publicadas (Montgomery).
- Límites I-MR, Xbar-R y Xbar-S frente al cálculo manual con A2, D3, D4, A3, B3, B4.
- Anderson-Darling frente a `statsmodels` (coincide a 9 decimales).
- EWMA y CUSUM frente a la recursión manual.
- Las 8 pruebas de causas especiales frente a casos construidos a mano, incluidos
  los casos límite.
- T²: valores frente a `scipy.spatial.distance.mahalanobis`; límites de Fase I y II
  por simulación Monte Carlo.
- Varianza generalizada: constantes b1 y b2 por simulación de matrices de covarianza.
- MEWMA: el límite para p=2, λ=0.1, ARL=200 da 8.63 (publicado: 8.64, Prabhu y Runger 1997).
- G y T: cuantiles frente a `scipy.stats`, y máxima verosimilitud Weibull por
  su ecuación de score.

> **Nota:** pccpy sigue las fórmulas y convenciones que Minitab documenta, pero
> no se ha comparado corrida a corrida contra el software Minitab por ausencia de
> licencia. Si encuentras una diferencia, abre un
> [issue](https://github.com/LeoSanta15/pccpy/issues).

---

## Desarrollo

```bash
git clone https://github.com/LeoSanta15/pccpy.git
cd pccpy
pip install -e ".[dev]"

pytest --cov=pccpy          # pruebas + cobertura
ruff check src/              # estilo y errores comunes
mypy src/pccpy               # verificación de tipos
```

Para generar la documentación localmente:

```bash
pip install -e ".[docs]"
sphinx-build -b html docs/source docs/build
# Abrir docs/build/index.html
```

Ver [`CHANGELOG.md`](CHANGELOG.md) para el historial de versiones y
[`CONTRIBUTING.md`](CONTRIBUTING.md) para las normas de contribución.

---

## Licencia

MIT — ver [LICENSE](LICENSE).
