# pccpy

[![PyPI version](https://img.shields.io/pypi/v/pccpy.svg)](https://pypi.org/project/pccpy/)
[![Python](https://img.shields.io/pypi/pyversions/pccpy.svg)](https://pypi.org/project/pccpy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/LeoSanta15/pccpy/blob/main/LICENSE)

**Control Estadístico de Procesos (SPC) en Python, al estilo Minitab.**

> 🇬🇧 [English version](https://github.com/LeoSanta15/pccpy/blob/main/README_en.md)

`pccpy` es una librería de SPC en español diseñada para ingenieros y técnicos que conocen
Minitab y quieren hacer el mismo análisis desde Python. Todas las convenciones de
nomenclatura (LCS/LCI, LEI/LES, Cp/Cpk/Pp/Ppk, Z.Bench, PPM, Anderson-Darling),
los métodos de estimación de sigma y las 8 pruebas de causas especiales siguen lo que
documenta Minitab.

---

## Índice

1. [Instalación](#instalación)
   - [Idioma de los mensajes](#idioma-de-los-mensajes)
2. [Inicio rápido](#inicio-rápido)
3. [Ejemplos con resultados](#ejemplos-con-resultados)
4. [Cartas de variables](#cartas-de-variables)
   - [I-MR](#carta-i-mr)
   - [Xbar-R y Xbar-S](#cartas-xbar-r-y-xbar-s)
   - [Formatos de entrada de datos](#formatos-de-entrada-de-datos)
   - [Parámetros históricos y etapas](#parámetros-históricos-y-etapas)
   - [Fase I iterativa](#fase-i-iterativa)
   - [Fechas en el eje x](#fechas-en-el-eje-x)
5. [Cartas de atributos](#cartas-de-atributos)
6. [Cartas de tiempo ponderado](#cartas-de-tiempo-ponderado)
   - [EWMA](#ewma)
   - [CUSUM](#cusum)
   - [Media móvil](#media-móvil)
7. [Cartas avanzadas](#cartas-avanzadas)
   - [Z-MR (corridas cortas)](#z-mr-corridas-cortas)
   - [I-MR-R/S (variación entre/dentro)](#i-mr-rs-variación-entrodentro)
   - [Eventos raros (G y T)](#eventos-raros-g-y-t)
   - [ARL (longitud media de racha)](#arl-longitud-media-de-racha)
8. [Cartas multivariadas](#cartas-multivariadas)
   - [T² de Hotelling](#t²-de-hotelling)
   - [Varianza generalizada](#varianza-generalizada)
   - [MEWMA](#mewma)
   - [MCUSUM](#mcusum)
   - [Etapas y Box-Cox en cartas multivariadas](#etapas-y-box-cox-en-cartas-multivariadas)
9. [Pruebas de causas especiales](#pruebas-de-causas-especiales)
10. [Visualización de las cartas](#visualización-de-las-cartas)
11. [Capacidad del proceso](#capacidad-del-proceso)
12. [Normalidad, Pareto y constantes SPC](#normalidad-pareto-y-constantes-spc)
13. [Carta de corridas y pre-control](#carta-de-corridas-y-pre-control)
14. [EWMA y CUSUM para atributos](#ewma-y-cusum-para-atributos)
15. [Intervalos de tolerancia](#intervalos-de-tolerancia)
16. [Muestreo de aceptación](#muestreo-de-aceptación)
17. [MSA / Gage R&R](#msa--gage-rr)
18. [Acceso a los datos del resultado](#acceso-a-los-datos-del-resultado)
19. [Validación](#validación)
20. [Desarrollo](#desarrollo)
21. [Licencia](#licencia)

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

### Idioma de los mensajes

Los textos de pccpy están en español. El idioma se puede cambiar (desde 0.11.0 —la documentación y este README también están en inglés— se traducen los mensajes de error y aviso, los `summary()`, las cabeceras de `to_frame()` —con `stable=True` para claves fijas—, los gráficos, el asistente `wizard()` y las demás tablas; el inglés está pendiente de revisión por una persona del dominio):

```python
import pccpy as pp

pp.available_languages()   # ['en', 'es']
pp.set_language("en")      # o PCCPY_LANG=en; también: with pp.language("en"): ...
```

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

## Ejemplos con resultados

Figuras y salidas reales de los ejemplos [`examples/basic_example.py`](https://github.com/LeoSanta15/pccpy/blob/main/examples/basic_example.py) y
[`examples/advanced_example.py`](https://github.com/LeoSanta15/pccpy/blob/main/examples/advanced_example.py), con la semilla `default_rng(2026)`. El código es el mismo en
todos los idiomas; las salidas, las etiquetas y los gráficos siguen el idioma de pccpy (aquí, español). Los fragmentos son extractos
que se ejecutan en secuencia (los datos se generan con el mismo `rng`); las salidas se acortan con «…» y completas están en
[`output_basic_example.txt`](https://github.com/LeoSanta15/pccpy/blob/main/docs/imagenes/es/output_basic_example.txt) y
[`output_advanced_example.txt`](https://github.com/LeoSanta15/pccpy/blob/main/docs/imagenes/es/output_advanced_example.txt). Se regeneran con
`python scripts/generar_figuras_readme.py`. Con `import numpy as np` y `import pccpy as pp`.

### Valores individuales (I-MR)

Un proceso que se desplaza de 100 a 103 en la observación 41, con las pruebas 1 a 6.

```python
rng = np.random.default_rng(2026)
x = np.r_[rng.normal(100, 1.5, 40), rng.normal(103, 1.5, 20)]   # el proceso pasa de 100 a 103
chart = pp.imr_chart(x, tests=[1, 2, 3, 4, 5, 6])
print(chart.summary())
chart.plot()
```

```text
Carta de control I-MR
  Parámetros: media=101.347, sigma=1.45895, MR_prom=1.64624, n=60
  Pruebas solicitadas: 1, 2, 3, 4, 5, 6
  Puntos marcados: 44
    [I] punto 10: prueba 6 (valor 99.6611) - 4 de 5 puntos a más de 1 desviación estándar (mismo lado)
    [I] punto 13: prueba 2 (valor 99.9038) - 9 puntos consecutivos del mismo lado de la línea central
```

![Carta I-MR con el desplazamiento y las pruebas marcadas](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/imr.png)

### Subgrupos (Xbar-R)

25 subgrupos de 5 piezas, sin señales.

```python
subgroups = rng.normal(50, 0.8, (25, 5))
xr = pp.xbar_r_chart(subgroups, tests="all")
print(xr.summary())
xr.plot(zones=True)
```

```text
Carta de control Xbar-R
  Parámetros: media=50.0238, sigma=0.876888, subgrupos=25, tamaño=5
  Pruebas solicitadas: 1, 2, 3, 4, 5, 6, 7, 8
  Resultado: sin puntos fuera de control
```

![Carta Xbar-R](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/xbar_r.png)

### Atributos (carta P con n variable)

30 muestras de entre 150 y 250 piezas, con 4 % de defectuosos.

```python
n = rng.integers(150, 250, 30)
defectives = rng.binomial(n, 0.04)
pp.p_chart(defectives, n, tests=[1, 2, 3, 4]).plot()
```

![Carta P con límites variables](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/p.png)

### Capacidad del proceso y Sixpack

Capacidad normal con límites 95 y 105, y las seis vistas del Capability Sixpack.

```python
data = rng.normal(100.4, 1.5, 150)
cap = pp.capability_analysis(data, lsl=95, usl=105, target=100)
print(cap.summary())
print(round(cap.cpk, 3), round(cap.ppk, 3))
fig, _, _ = pp.capability_sixpack(subgroups, lsl=48, usl=52, target=50)
```

```text
Análisis de capacidad del proceso (distribución normal)
  LEI=95.0000  Objetivo=100.0000  LES=105.0000
  N=150  Media=100.44554  Desv.Est.(dentro)=1.37977 [mr]  Desv.Est.(general)=1.52887
  Capacidad potencial (dentro):
    Cp=1.21  CPL=1.32  CPU=1.10  Cpk=1.10
    Z.Bench=3.28
  Desempeño general:
    Pp=1.09  PPL=1.19  PPU=0.99  Ppk=0.99  Cpm=1.05
    IC 95% Pp: (0.97, 1.21)   IC 95% Ppk: (0.87, 1.12)
    Z.Bench=2.94  Z.LEI=3.56  Z.LES=2.98  Nivel Sigma=2.94  DPMO=1,630
  Desempeño (PPM):            < LEI       > LES      Total
    Observado               0.00        0.00       0.00
    Esperado dentro        39.62      481.91     521.53
    Esperado general      184.16     1446.09    1630.25
  …
1.1 0.993
```

![Capability Sixpack](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/sixpack.png)

### Datos no normales (Weibull y Box-Cox)

Prueba de normalidad y capacidad con la distribución ajustada y con Box-Cox.

```python
w = rng.weibull(1.8, 200) * 3 + 0.5
print(pp.normality_test(w))
print(pp.capability_nonnormal(w, lsl=0.1, usl=12, distribution="weibull").summary())
print(pp.capability_boxcox(w, lsl=0.1, usl=12).summary())
```

```text
Anderson-Darling: estadístico = 3.3147, valor p < 0.005 (n = 200)
Análisis de capacidad (no normal) - distribución weibull
  LEI=0.1000  LES=12.0000  N=200  logL=-363.872  AIC=731.745
  Percentiles: 0.135% = 0.17925   50% = 3.13714   99.865% = 8.82399
  Pp=1.38  PPL=1.03  PPU=1.56  Ppk=1.03
  Desempeño (PPM):            < LEI       > LES      Total
    Observado               0.00        0.00       0.00
    Esperado              378.35        2.46     380.81
  …
Análisis de capacidad del proceso (distribución normal)
  LEI=0.1000  Objetivo=*  LES=12.0000
  N=200  Media=1.18909  Desv.Est.(dentro)=0.58063 [mr]  Desv.Est.(general)=0.58889
  Transformación Box-Cox con lambda = 0.1615 (Media, Desv.Est. y Z.* están en la escala transformada; LEI/LES/objetivo y PPM observado, en unidades originales)
  Capacidad potencial (dentro):
    Cp=1.43  CPL=1.79  CPU=1.07  Cpk=1.07
    Z.Bench=3.22
  Desempeño general:
    Pp=1.41  PPL=1.76  PPU=1.06  Ppk=1.06  Cpm=*
    IC 95% Pp: (1.27, 1.55)   IC 95% Ppk: (0.94, 1.17)
    Z.Bench=3.17  Z.LEI=5.28  Z.LES=3.17  Nivel Sigma=3.17  DPMO=754
```

### Pareto

Tabla de frecuencias acumuladas y su gráfico.

```python
counts = pp.pareto(["Scratch", "Dent", "Scratch", "Stain", "Scratch", "Dent", "Other"])
print(counts)
pp.plot_pareto(counts)
```

```text
  categoría  conteo  porcentaje   acumulado
0   Scratch       3   42.857143   42.857143
1      Dent       2   28.571429   71.428571
2     Stain       1   14.285714   85.714286
3     Other       1   14.285714  100.000000
```

![Diagrama de Pareto](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/pareto.png)

### Corridas cortas (Z-MR)

Tres partes con medias y variaciones distintas en una sola carta.

```python
parts = ["A"] * 12 + ["B"] * 10 + ["A"] * 12 + ["C"] * 8
means = {"A": (50, 1.0), "B": (80, 2.0), "C": (20, 0.5)}
x = np.array([rng.normal(*means[p]) for p in parts])
x[15] += 10                                    # una pieza B fuera de lo normal
zmr = pp.zmr_chart(x, parts, mu={p: m for p, (m, _) in means.items()},
                   sigma={p: s for p, (_, s) in means.items()}, tests=(1, 2, 3, 4, 5, 6))
print(zmr.summary())
```

```text
Carta de control Z-MR
  Parámetros: método=histórica, partes=3, corridas=4, n=42, sigma_mín=0.5, sigma_máx=2
  Pruebas solicitadas: 1, 2, 3, 4, 5, 6
  Puntos marcados: 4
    [MR] punto 16: prueba 1 (valor 4.22507) - 1 punto a más de 3 desviaciones estándar de la línea central
    [MR] punto 17: prueba 1 (valor 4.78973) - 1 punto a más de 3 desviaciones estándar de la línea central
    [Z] punto 16: prueba 1 (valor 4.38598) - 1 punto a más de 3 desviaciones estándar de la línea central
    [Z] punto 38: prueba 4 (valor -0.457385) - 14 puntos consecutivos alternando arriba y abajo
```

![Carta Z-MR](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/zmr.png)

### Variación entre y dentro de subgrupos (I-MR-R)

Con variación entre lotes, Xbar-R alarma de más y I-MR-R no.

```python
lots = rng.normal(20, 1, (30, 5)) + rng.normal(0, 2, (30, 1))
print(len(pp.xbar_r_chart(lots).violations()))   # puntos marcados por Xbar-R
ch = pp.imr_rs_chart(lots)
print(len(ch.violations()))                      # puntos marcados por I-MR-R
```

```text
12
1
```

![Carta I-MR-R](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/imr_r.png)

### Eventos raros (G y T)

Carta G con los conteos entre eventos y carta T con los tiempos entre eventos.

```python
between = rng.geometric(0.01, 40) - 1
between[25] = 600
pp.g_chart(between).plot()
times = rng.weibull(1.4, 40) * 30
times[12] = 250
print(pp.t_chart(times).summary())
```

```text
Carta de control T
  Parámetros: distribución=weibull, forma=1.16087, escala=36.2814, n=40
  Pruebas solicitadas: 1
  Puntos marcados: 1
    [T] punto 13: prueba 1 (valor 250) - 1 punto fuera de los percentiles de la distribución weibull
```

![Carta G](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/g.png)

### Carta de zona

Puntaje acumulado ante un desplazamiento sostenido.

```python
drift = rng.normal(0, 1, 50)
drift[30:] += 1.2                              # desplazamiento sostenido de 1,2 sigmas
zone = pp.zone_chart(drift, mu=0.0, sigma=1.0, reset=True)
print(zone.summary())
```

```text
Carta de control Zona
  Parámetros: media=0, sigma=1, pesos=(0.0, 2.0, 4.0, 8.0), reinicio=True, n=50
  Pruebas solicitadas: 1
  Puntos marcados: 2
    [Zona] punto 43: prueba 1 (valor 2.03228) - puntaje acumulado de zona >= 8
    [Zona] punto 48: prueba 1 (valor 2.57529) - puntaje acumulado de zona >= 8
```

![Carta de zona](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/zona.png)

### Multivariadas: T², MEWMA y MCUSUM

Fase I con 100 observaciones y Fase II con 50 nuevas; la variable 3 se desplaza desde el punto 31.

```python
Sigma = [[1, .6, .3], [.6, 1, .2], [.3, .2, 1]]
hist = rng.multivariate_normal([0, 0, 0], Sigma, 100)
new = rng.multivariate_normal([0, 0, 0], Sigma, 50)
new[30:, 2] += 4                               # la variable 3 se desplaza
mu, cov = hist.mean(axis=0), np.cov(hist, rowvar=False)
t2 = pp.t2_chart(new, mu=mu, cov=cov, n_hist=100)
first = int(t2["T2"].flagged[0]) + 1
print(t2.contributions(first).round(2))        # contribución de cada variable a la señal
me = pp.mewma_chart(new, mu=mu, cov=cov)
print(int(me["MEWMA"].flagged[0]) + 1)         # primera señal de la MEWMA
mc = pp.mcusum_chart(new, mu=mu, cov=cov)
print(int(mc["MCUSUM"].flagged[0]) + 1, round(mc.params[0]["LCS"], 2))   # primera señal de la MCUSUM y su límite
```

```text
X1     6.81
X2     1.32
X3    16.09
Name: contribución (punto 31), dtype: float64
  …
33
33 6.88
```

![Carta T² de Hotelling](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/t2.png)

![Carta MEWMA](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/mewma.png)

![Carta MCUSUM](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/mcusum.png)

### Varianza generalizada

Subgrupos de 6 observaciones trivariadas cuya dispersión aumenta 2,5 veces en la segunda mitad.

```python
subs = rng.multivariate_normal([0, 0, 0], Sigma, 120)
subs[60:] *= 2.5                               # la dispersión aumenta
pp.generalized_variance_chart(subs, subgroup_size=6).plot()
```

![Carta de varianza generalizada |S|](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/es/gv.png)

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

Con **tamaños de subgrupo desiguales**, `'rbar'` y `'sbar'` promedian las estimaciones de cada subgrupo con pesos de varianza
inversa: `Σ wᵢ·Rᵢ/d2(nᵢ) / Σ wᵢ` con `wᵢ = d2(nᵢ)²/d3(nᵢ)²`, y `Σ hᵢ·sᵢ/c4(nᵢ) / Σ hᵢ` con `hᵢ = c4(nᵢ)²/(1 − c4(nᵢ)²)`. Con tamaño
constante los pesos son iguales y el resultado es el promedio simple de siempre.

---

### Formatos de entrada de datos

Las cartas de subgrupos (`xbar_r_chart`, `xbar_s_chart`, `ewma_chart`, `cusum_chart`,
`ma_chart`, `imr_rs_chart`, `zone_chart`, `capability_analysis`, `capability_sixpack`)
aceptan **cinco formatos equivalentes**:

```python
import pandas as pd

# 1. Matriz 2-D: cada fila es un subgrupo (formato clásico)
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
df = pd.DataFrame({"medida": vector, "subgrupo": ids})
pp.xbar_r_chart(df["medida"], subgroup=df["subgrupo"])

# 4. DataFrame en formato largo + nombres de columna
#    (subgroup: columna de identificadores, value: columna de valores)
df_largo = pd.DataFrame({
    "lote":   [1, 1, 1, 2, 2, 2, 3, 3, 3],
    "medida": [20.1, 20.3, 20.0, 20.4, 20.1, 20.5, 19.9, 20.2, 20.1],
})
pp.xbar_r_chart(df_largo, subgroup="lote", value="medida")

# Si solo hay una columna numérica, 'value' se detecta automáticamente
pp.xbar_r_chart(df_largo, subgroup="lote")

# 5. Vector 1-D con subgroup_size cuando el total no es divisible exactamente
#    El último subgrupo incompleto se grafica con sus propios límites
#    pero NO entra en el cálculo de sigma ni de la media global
import warnings
datos_11 = np.array([20.1, 20.3, 20.0, 20.4, 20.1, 20.5, 19.9, 20.2, 20.1, 20.3, 20.4])
with warnings.catch_warnings(record=True):
    carta = pp.xbar_r_chart(datos_11, subgroup_size=4)
# UserWarning: 11 observaciones no forman un número exacto de subgrupos de tamaño 4.
# El último subgrupo tiene 3 de 4 observaciones: se incluye en la gráfica
# pero NO en el cálculo de los límites de control.
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

### Fase I iterativa

`phase_one()` calcula la carta, **excluye los puntos con señal, recalcula los límites y repite** hasta que no
queda ninguna; `phase2()` aplica esos límites congelados a datos nuevos. Funciona con `imr_chart`,
`xbar_r_chart`, `xbar_s_chart`, `p_chart`, `np_chart`, `c_chart` y `u_chart`.

```python
rng = np.random.default_rng(3)
x_historico = rng.normal(100, 2, 60)
x_historico[[10, 33]] += 15           # dos puntos con causa especial
x_nuevo = rng.normal(100, 2, 20)

fase1 = pp.phase_one(pp.imr_chart, x_historico, tests=(1, 2, 3))
print(fase1.summary())     # puntos excluidos, límites congelados y cada pasada
fase1.excluded             # posiciones (base 0) de los puntos excluidos
fase1.chart.plot()         # carta con los límites definitivos (en I-MR los excluidos quedan como huecos)

carta_ii = fase1.phase2(x_nuevo, tests=(1, 2))   # Fase II con los límites de la Fase I
```

**¿Ya tienes la Fase I de otra sesión?** Guárdala y cárgala sin repetir `phase_one`, o crea el resultado desde límites que
ya conoces:

```python
fase1.to_json("fase1.json")                          # guarda lo que necesita phase2() (sin los datos)
fase1 = pp.PhaseOneResult.from_json("fase1.json")    # en otra sesión; también acepta el texto JSON
carta_ii = fase1.phase2(x_nuevo, tests=(1, 2))

# o con parámetros calculados en otra parte (en cartas con transform=, una Transformation ya ajustada)
externo = pp.PhaseOneResult.from_limits(pp.imr_chart, mu=100.0, sigma=2.0, tests=(1, 2))
carta_ii = externo.phase2(x_nuevo)
```

Salvaguardas: `max_iterations` (10), `min_points` (20) y `max_excluded` (25 % de los puntos). Si saltan,
el resultado no converge y se avisa: un proceso que necesita descartar tantos puntos no es estable.
**Excluye puntos solo si has encontrado y corregido su causa especial.** En `imr_chart` solo cuentan las
señales del panel I (un valor atípico dispara también el rango móvil de su vecino); cámbialo con `exclude_panels=`.

---

### Fechas en el eje x

Con una serie de pandas con **índice de fechas** (o de texto, p. ej. números de lote) la carta conserva las
etiquetas: el gráfico rotula el eje x con ellas, `to_frame()` y `violations()` añaden la columna `etiqueta` y
`summary()` muestra la fecha junto al punto. Los puntos se grafican por orden de muestreo, como en Minitab.

```python
import pandas as pd

x = np.random.default_rng(1).normal(10, 1, 30)
serie = pd.Series(x, index=pd.date_range("2026-03-01", periods=len(x), freq="D"))
carta = pp.imr_chart(serie, tests=(1, 2))
carta.plot()                     # eje «Fecha»
carta.violations()               # con la fecha de cada señal
carta.with_labels([f"L{i}" for i in range(30)])   # etiquetas propias (una por punto graficado)
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
)
# EWMA aplica solo la prueba 1 (no tiene parámetro tests)
```

Con subgrupos, `sigma_method` elige el estimador (`'rbar'` por defecto, `'sbar'` o `'pooled'`; con individuales
`'mr'`, `'median_mr'` o `'mssd'`). `stages=` calcula el objetivo y sigma por etapa y **reinicia** la EWMA al empezar
cada una. ARL en control con σ conocida y λ = 0,2, L = 3: ≈ 560 con límites asintóticos y ≈ 555 con exactos (`pp.arl_ewma`, contrastado con una simulación de 200 000 corridas).

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
    headstart=0.0,  # arranque rápido (FIR) en unidades de sigma; 0 ≤ headstart < H (p. ej. H/2)
    # Con H=4, K=0.5 el ARL en control de la CUSUM bilateral es ≈ 168 (Hawkins y Olwell)
)
```

El gráfico nombra sus dos series con una leyenda: «C+ (suma superior)» y «C- (suma inferior)». Se muestra por defecto y se quita con `carta.plot(legend=False)`.

> **Regla práctica:** `H = 4σ` y `K = 0.5σ` equilibran la detección de un desplazamiento
> de 1σ (ARL fuera de control ≈ 8) con un ARL en control ≈ 168 (bilateral). Para un ARL en
> control mayor sube `H` (con `H = 5`, ≈ 470). `sigma_method=` y `stages=` funcionan como en la EWMA
> (las sumas se reinician en `headstart` al empezar cada etapa).

---

### Media móvil

La carta **MA** promedia los últimos `length` puntos para suavizar el ruido.
Los primeros `length - 1` puntos usan el promedio de los datos disponibles,
por lo que sus límites son más amplios.

```python
pp.ma_chart(
    x,
    length=5,   # ventana de la media móvil; defecto: 3
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
pp.g_chart(entre_eventos, p=0.02, benneyan=True)   # añade la prueba de Benneyan (rachas de ceros)

# T: tiempo entre eventos (distribución Weibull o exponencial)
tiempos = rng.weibull(1.5, 40) * 30
pp.t_chart(tiempos)          # Weibull (defecto)
pp.t_chart(tiempos, distribution="exponential")  # exponencial
pp.t_chart(tiempos, zeros="drop")  # excluye con aviso las duraciones iguales a 0 (por defecto da error)
```

Los límites de la carta G se basan en percentiles exactos de la distribución
geométrica; los de la carta T en los de la Weibull o exponencial ajustada por
máxima verosimilitud.

La prueba de Benneyan (`benneyan=True`) señala `c` o más conteos consecutivos
iguales a 0, con `c` el menor entero tal que `p^c ≤ 1 − Φ(k)`; sirve para detectar
que los eventos se vuelven más frecuentes, algo que el límite inferior 0 de la carta
G no puede mostrar. Diferencias posibles con Minitab: Minitab la activa por defecto
y pccpy no; la fórmula de `c` es una definición propia de pccpy, no contrastada con
Minitab (no se pudo consultar su fórmula).

### ARL (longitud media de racha)

Para comparar o diseñar cartas, `pccpy` calcula el ARL (número esperado de puntos hasta la primera señal) de las cartas Shewhart,
CUSUM y EWMA, de las cartas S y R, de las de atributos (NP/P y C/U con tamaño constante) y de las de eventos raros (G y T):

```python
pp.arl_shewhart(k=3)                       # 370.4 en control
pp.arl_shewhart(k=3, shift=1.0)            # 43.9 con la media desplazada 1σ del estadístico
pp.arl_cusum(h=4, k=0.5, shift=1.0)        # 8.4
pp.arl_ewma(weight=0.2, L=3, shift=1.0)    # 10.8
pp.arl_cusum(h=4, k=0.5, shift=1.0, method="simulation", n_runs=20_000, seed=1)  # Monte Carlo, reproducible
```

`method` elige `"numeric"` (por defecto), `"markov"` o `"simulation"`. Se suponen parámetros conocidos, observaciones
independientes y solo la regla «un punto fuera de los límites» (sin las pruebas 2 a 8). Con atributos y eventos raros el ARL en
control no es 370,4, y las cartas G y T detectan mucho mejor que los eventos se espacien que que se acorten. Véase la
[guía del ARL](https://github.com/LeoSanta15/pccpy/blob/main/docs/source/arl.md). No se ha comparado con el ARL de Minitab.

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
    cov=np.cov(hist, rowvar=False),   # Sigma histórica (sin media: solo mide dispersión)
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
- **Básicas (1-4):** carta R, S, G, T, atributos (P, NP, C, U, Laney). En R y S son aproximadas: los rangos y las
  desviaciones no son normales
- **Solo prueba 1:** carta MR (los rangos móviles están autocorrelacionados y son asimétricos: con `tests="all"` la
  prueba 2 saltaba en el 45 % de las series estables), EWMA, CUSUM, MA, T², MEWMA, MCUSUM

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

### Probabilidad de un valor

```python
res = pp.capability_analysis(x, lsl=44, usl=56, subgroup_size=1)
p = res.probability(below=47)         # P(X < 47): probability, ppm, dpmo y dpu
res.probability(between=(48, 52))     # entre dos valores (dpmo y dpu: None)
res.probability().ppm                 # sin argumentos: fuera de LEI/LES (= PPM esperado)
res.probability(below=[45, 46, 47]).to_frame()   # arreglos: una fila por valor
```

Los valores van en las unidades originales (también con Box-Cox o Johnson); `sigma="within"` usa la sigma dentro de los
subgrupos y `opportunities=` fija las oportunidades por unidad del DPU. Con `capability_nonnormal` usa la distribución
ajustada. Supone la media y la sigma estimadas como conocidas y no se ha comparado con Minitab.

---

### Pruebas de atípicos (Grubbs y ESD generalizada)

```python
r = pp.outlier_test(x)                    # Grubbs: un atípico
r = pp.outlier_test(x, method="esd")      # ESD de Rosner: varios, sin enmascaramiento
r.outlier_indices, r.outlier_values, r.summary()
```

Suponen datos normales (sin los atípicos) y **no justifican eliminar un dato**: investiga su origen. Con datos de proceso en el tiempo usa las cartas de control. Verificadas contra la tabla publicada de Grubbs y el ejemplo de Rosner del manual del NIST.

---

### Datos asimétricos: guía rápida

| Quiero… | Usa |
|---|---|
| Saber por qué no son normales | `pp.diagnose(x)` → `non_normal_reason`, recomendación lista para ejecutar |
| Capacidad con datos asimétricos | `capability_analysis(x, lsl, usl, transform="yeo-johnson")`, `capability_boxcox` o `capability_nonnormal(distribution=…)` |
| Una carta I-MR o Xbar fiable | `imr_chart(x, transform="yeo-johnson")` (límites asimétricos en unidades originales) |
| Intervalos sin suponer normalidad | `ci_method="bootstrap"`, `pp.bootstrap_summary(x)`, `pp.bootstrap_ci(x, función)` |

Guía completa, con los límites y los resultados de simulación: [`docs/source/datos_asimetricos.md`](https://github.com/LeoSanta15/pccpy/blob/main/docs/source/datos_asimetricos.md).

---

### Intervalos bootstrap (datos asimétricos)

Con datos asimétricos los intervalos normales (`x̄ ± t·s/√n`, chi-cuadrado para sigma, Bissell para Ppk) pierden cobertura. `bootstrap_ci` remuestrea tus datos y no supone ninguna forma: percentil o **BCa** (corrige sesgo y asimetría). Sirve para cualquier estadístico, escalar o vector, con los mismos remuestreos.

```python
import numpy as np

r = pp.bootstrap_ci(datos, np.mean, method="bca", n_boot=2000, seed=1)
r.estimate, r.ci            # estimación e intervalo (inferior, superior)
print(r.summary())

# varios estadísticos a la vez; vectorized=True (np.mean, np.std…) es mucho más rápido
sd = lambda v, axis=-1: np.std(v, axis=axis, ddof=1)
pp.bootstrap_ci(datos, sd, vectorized=True, seed=1).ci
```

Con `pp.bootstrap_summary(datos, seed=1)` obtienes de una vez la media, la mediana y la desviación estándar con su intervalo bootstrap y, como referencia, el intervalo clásico (`t` de Student, chi-cuadrado y estadísticos de orden).

En simulación (gamma(2), n = 60) el intervalo BCa de la desviación estándar cubre ≈ 92 % frente a ≈ 83 % del intervalo chi-cuadrado; para la media el intervalo t ya aguanta bien. Con n < 20 avisa: el bootstrap también pierde cobertura.

---

### Capacidad para atributos (binomial y Poisson)

Cuando el dato es «defectuoso / bueno» o un conteo de defectos, no hay Cp ni Cpk: la capacidad es la **tasa de
defectos** con su intervalo exacto. `capability_binomial` da el % defectivo (Clopper-Pearson), el PPM y el nivel Z;
`capability_poisson` da los defectos por unidad (Garwood) y, con `opportunities=`, el DPMO y el Z. Ambas incluyen la
prueba chi-cuadrado de que la tasa es constante entre muestras: si falla, el proceso no es estable y la capacidad no es
fiable (revise la carta P o U).

```python
defectuosas = [3, 5, 2, 4, 6, 1, 3, 5]
defectos = [3, 5, 2, 4, 6, 1, 3, 5]
r = pp.capability_binomial(defectuosas, n=200)        # n constante o uno por muestra
print(r.summary())
r.p_ci, r.ppm, r.z, r.homogeneous
r.plot()                                               # tasa por muestra y estimación acumulada

q = pp.capability_poisson(defectos, units=10, opportunities=20)
q.dpu, q.dpu_ci, q.dpmo, q.z
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
    method="anderson",      # 'anderson' (defecto), 'shapiro', 'dagostino'
)
print(result)
# Anderson-Darling: estadístico = 0.5302, valor p = 0.165 (n = 40)

result.statistic    # valor del estadístico
result.p_value      # valor p
result.reject       # True si se rechaza normalidad a α = 0.05

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

## Carta de corridas y pre-control

### Carta de corridas

Detecta patrones no aleatorios en los datos mediante **cuatro pruebas de hipótesis**
(agrupamiento, mezclas, tendencias, oscilación) usando la distribución de rachas.

```python
rc = pp.run_chart(x)
print(rc.summary())
# Mediana: 100.12
# p agrupamiento: 0.23  p mezclas: 0.77  p tendencias: 0.04  p oscilación: 0.96
# → Tendencia detectada (p < 0.05)

rc.to_frame()   # punto, valor, lado (arriba/abajo), racha
rc.plot()       # carta con la mediana y puntos coloreados por lado
```

| Prueba | Detecta |
|--------|---------|
| Agrupamiento | demasiado pocas rachas → patrón por ciclos o mezcla de distribuciones |
| Mezclas | demasiadas rachas → dos distribuciones alternando |
| Tendencias | rachas largas consecutivas → deriva del proceso |
| Oscilación | alternancia excesiva arriba/abajo → sobrecontrol |

---

### Pre-control (Shainin)

Semáforo de cuatro zonas basado en el ancho de tolerancia. No requiere estimación
de sigma: usa solo LSL/USL y marca cada observación con el color de su zona.

```python
pc = pp.precontrol(x, lsl=94, usl=106)
print(pc.summary())
# Verde (G): 45   Amarillo bajo (Y-): 3   Amarillo alto (Y+): 2   Rojo: 0
# Señales de ajuste: 0

pc.zones          # lista de etiquetas: 'G', 'Y-', 'Y+', 'R-', 'R+'
pc.signals        # lista de índices donde se detectó señal de ajuste
pc.to_frame()     # DataFrame con punto, valor y zona
pc.plot()
```

**Zonas pre-control:**

| Zona | Rango | Acción |
|------|-------|--------|
| Verde (G) | USL/4 alrededor del centro (50% de la tolerancia) | Continuar |
| Amarilla baja (Y−) | [LSL, LSL + 25% tol] | Precaución |
| Amarilla alta (Y+) | [USL − 25% tol, USL] | Precaución |
| Roja (R−/R+) | Por debajo de LSL o por encima de USL | Detener |

---

## EWMA y CUSUM para atributos

Versiones de cartas de tiempo ponderado para **datos discretos** (fracciones
defectuosas, tasas de defectos). Los límites transitorios son exactos y se
ensanchan en las primeras muestras hasta estabilizarse.

```python
defectuosos = [3, 5, 2, 4, 6, 1, 3, 5, 2, 4]
n_muestral  = 200   # escalar o array de longitud igual

# EWMA-P: fracción defectuosa
carta = pp.ewma_p_chart(defectuosos, n=n_muestral, weight=0.2)

# EWMA-U: tasa de defectos por unidad
defectos   = [2, 1, 3, 0, 4, 2, 1, 3, 2, 1]
n_unidades = [1, 1, 2, 1, 2, 1, 1, 2, 1, 2]
carta_u = pp.ewma_u_chart(defectos, n=n_unidades)

# CUSUM-P: suma acumulada para fracción defectuosa
carta_cp = pp.cusum_p_chart(defectuosos, n=n_muestral, h=4, k=0.5)

# CUSUM-C: suma acumulada para número de defectos
carta_cc = pp.cusum_c_chart(defectos, h=4, k=0.5)
```

Con `n` variable (array), los límites se ajustan punto a punto al tamaño de muestra.

---

## Intervalos de tolerancia

Un **intervalo de tolerancia** (α, p) garantiza —con confianza 1−α— que al menos
una fracción `p` de la población cae dentro de los límites calculados.

### Normal bilateral y unilateral

```python
rng = np.random.default_rng(1)
x50 = rng.normal(100, 2, 50)

# Bilateral: con 95% de confianza, ≥95% de la población en (LI, LS)
res = pp.tolerance_interval(x50, coverage=0.95, confidence=0.95)
print(res.summary())
# LI = 93.7, LS = 106.3, k = 2.382 (normal bilateral, n=50, 95/95)

res.lower          # límite inferior
res.upper          # límite superior
res.k_factor       # factor k
res.achieved_confidence  # confianza lograda (si el método es no paramétrico)
res.to_frame()
res.plot()

# Unilateral superior: P(X ≤ LS) ≥ 0.95 con 95% de confianza
res_u = pp.tolerance_interval(x50, sides="upper")

# Unilateral inferior: P(X ≥ LI) ≥ 0.95 con 95% de confianza
res_l = pp.tolerance_interval(x50, sides="lower")
```

### No paramétrico

```python
x300 = rng.normal(100, 2, 300)
res_np = pp.tolerance_interval(x300, method="nonparametric", coverage=0.95)
# Los límites son estadísticos de orden; n≈300 para 95/95 bilateral
```

### Desde estadísticos resumen

Cuando solo se tienen la media, desviación típica y n (sin datos individuales):

```python
res_s = pp.tolerance_interval_summary(
    mean=100.0, std=2.0, n=50,
    coverage=0.95, confidence=0.95,
    sides="two",
)
print(res_s.summary())   # Mismos índices que tolerance_interval
```

---

## Muestreo de aceptación

### Z1.4 — Atributos (ANSI/ASQ Z1.4)

Selecciona el plan de muestreo de la norma Z1.4 a partir del tamaño de lote y el AQL:

```python
# Lote N=1000, AQL=1%
plan = pp.acceptance_sampling_attributes(N=1000, aql=1.0)
print(plan.summary())
# n=80, Ac=2, Re=3, LTPD=6.5%, AOQL=0.87%

plan.n          # tamaño de muestra
plan.c          # número de aceptación (Ac)
plan.ltpd       # LTPD (fracción que da Pa ≈ 0.10)
plan.aoq_max    # AOQL

plan.pa(0.01)   # P(aceptar | p=1%) — curva OC
plan.oc_curve() # DataFrame con columnas p_defectivo, P(aceptar) (stable=True: defective_fraction, p_accept)
plan.aoq_curve()# DataFrame con columnas p_defectivo, AOQ (stable=True: defective_fraction, aoq)
plan.plot()     # curva OC + curva AOQ en una figura
```

### Z1.9 — Variables (ANSI/ASQ Z1.9)

> ⚠️ La tabla Z1.9 incluida **no reproduce la norma** y la función avisa con un `UserWarning`. Para decidir con Z1.9, pase `n=` y `k=` tomados de su ejemplar de la norma.

Requiere que la característica se distribuya normalmente; usa la media y la desviación
para estimar la fracción defectuosa mediante el estadístico de calidad Q:

```python
plan_v = pp.acceptance_sampling_variables(N=1000, aql=1.0, spec_type="one")
# spec_type='one'  → especificación unilateral (solo USL o solo LSL)
# spec_type='two'  → especificación bilateral

muestra = rng.normal(10.5, 0.2, plan_v.n)
dec = plan_v.evaluate(muestra, usl=11.0)
print(dec)
# {'xbar': 10.49, 's': 0.19, 'Q_usl': 2.68, 'accept': True}

plan_v.oc_curve()   # curva OC del plan
```

### Dodge-Romig

Planes que minimizan la inspección total media (ATI):

```python
# Plan LTPD: diseñado para LTPD=5% con proceso promedio p̄=1%
plan_ltpd = pp.dodge_romig(N=1000, ltpd=0.05, process_avg=0.01)
print(plan_ltpd.summary())   # n, Ac, AOQL

# Plan AOQL: diseñado para AOQL=1%
plan_aoql = pp.dodge_romig(N=1000, aoql=0.01, process_avg=0.005)
print(plan_aoql.summary())   # n, Ac, LTPD

plan_ltpd.n        # tamaño de muestra
plan_ltpd.c        # número de aceptación
plan_ltpd.aoql     # AOQL
plan_ltpd.ltpd     # LTPD
plan_ltpd.to_frame()
```

---

## MSA / Gage R&R

### Cruzado (ANOVA y Xbar-R)

El diseño cruzado mide cada **parte** con todos los **operadores**. Es el más común
cuando la medición no destruye la pieza.

```python
# 10 partes × 3 operadores × 2 réplicas (orden del array: parte0-op0, parte0-op1, ...)
data = rng.normal(0, 1, 10 * 3 * 2)

# Método ANOVA (más preciso)
grr = pp.gage_rr(data, parts=10, operators=3, replicates=2, tolerance=20.0)
print(grr.summary())
# Repetibilidad: 14.3%  Reproducibilidad: 3.1%  %R&R: 14.6%  NDC: 9

grr.pct_gage            # % Estudio de variación total del sistema de medición
grr.var_repeatability   # varianza de repetibilidad
grr.var_reproducibility # varianza de reproducibilidad
grr.var_part            # varianza de partes
grr.var_total           # total (suma de los tres anteriores)
grr.ndc                 # número de categorías distintas
grr.anova_table         # DataFrame con GL, SC, CM, F, p-valor (siempre en español)
grr.anova_frame()       # la misma tabla en el idioma activo (stable=True: df, ss, ms, f, p_value)
grr.to_frame()
grr.plot()

# Si la interacción partes×operadores no es significativa (p > alpha_interaction, 0.25 por defecto) se quita del
# modelo: los componentes salen del modelo reducido (grr.anova_reduced); alpha_interaction=1.0 la conserva siempre.
# Hacen falta al menos 2 réplicas.

# Método Xbar-R (clásico AIAG: constantes d2*; K2 = 0,5231 con 3 operadores, K3 = 0,3146 con 10 partes)
grr_xr = pp.gage_rr(data, parts=10, operators=3, replicates=2,
                    method="xbar_r", tolerance=20.0)
# grr_xr.anova_table es None (el método Xbar-R no produce tabla ANOVA)
```

### Anidado

Cuando los operadores miden **partes distintas** (la medición destruye la muestra
o las partes no son intercambiables entre operadores):

```python
grr_n = pp.gage_rr_nested(data, parts=10, operators=3, replicates=2)
print(grr_n.summary())
```

### Estudio Tipo 1 — sesgo y repetibilidad

Mide una **pieza de referencia** varias veces con un solo operador para estimar
el sesgo y la repetibilidad:

```python
ref_meas = rng.normal(10.02, 0.05, 25)   # 25 mediciones de referencia = 10.0
t1 = pp.gage_type1(ref_meas, reference=10.0, tolerance=0.5)
print(t1.summary())
# Sesgo: 0.02 mm  t = 2.0  p = 0.057  Cg = 1.67  Cgk = 1.33

t1.bias      # sesgo = media - referencia
t1.t_stat    # estadístico t para H₀: sesgo = 0
t1.p_value   # valor p de la prueba bilateral
t1.cg        # capacidad del instrumento (0.2×tolerancia / 6s)
t1.cgk       # capacidad considerando sesgo

# Desde estadísticos resumen (sin datos individuales)
ts = pp.gage_type1_summary(
    mean=10.02, std=0.05, n=25,
    reference=10.0, tolerance=0.5,
)
```

### Linealidad y sesgo

Evalúa si el sesgo es constante en todo el rango de operación del instrumento:

```python
refs       = np.repeat([2, 4, 6, 8, 10], 5)    # 5 referentes × 5 réplicas
mediciones = refs + rng.normal(0.05, 0.1, 25)

lin = pp.gage_linearity(mediciones, refs, tolerance=10.0)
print(lin.summary())
# Pendiente: 0.001  Intercepto: 0.048  R²: 0.002  Linealidad: 0.01%

lin.slope      # pendiente de la regresión sesgo ~ referencia
lin.intercept
lin.r_squared
lin.to_frame()
lin.plot()
```

### Concordancia por atributos (Kappa)

Cuando la característica es categórica (conforme/no conforme, grados, colores):

```python
import pandas as pd

clasificaciones = pd.DataFrame({
    "Op1": ["G", "D", "G", "G", "D"] * 4,
    "Op2": ["G", "D", "G", "D", "D"] * 4,
    "Op3": ["G", "G", "G", "G", "D"] * 4,
})
referencia = np.array(["G", "D", "G", "G", "D"] * 2)

atr = pp.attribute_agreement(clasificaciones, reference=referencia, replicates=2)
print(atr.summary())
# Kappa Fleiss: 0.84
# Op1 vs ref: κ=0.90  Op2 vs ref: κ=0.80  Op3 vs ref: κ=0.82

atr.fleiss_kappa           # Kappa de Fleiss (acuerdo entre todos los operadores)
atr.kappa_vs_reference     # DataFrame con kappa, EE y p-valor por operador
atr.to_frame()
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

Más de 1 800 pruebas automatizadas. Las referencias son independientes de pccpy:

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

Ver [`CHANGELOG.md`](https://github.com/LeoSanta15/pccpy/blob/main/CHANGELOG.md) para el historial de versiones y
[`CONTRIBUTING.md`](https://github.com/LeoSanta15/pccpy/blob/main/CONTRIBUTING.md) para las normas de contribución.

---

## Licencia

MIT — ver [LICENSE](https://github.com/LeoSanta15/pccpy/blob/main/LICENSE).
