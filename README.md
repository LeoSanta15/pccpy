# spyc

**Control Estadístico de Procesos (SPC) en Python, al estilo Minitab.**

Cartas de control, pruebas de causas especiales, análisis de capacidad, prueba de
normalidad y Pareto, con salidas y convenciones (LCS/LCI, LEI/LES, Cp/Cpk/Pp/Ppk,
Z.Bench, PPM, Anderson-Darling) pensadas para quien viene de Minitab.

Todo en español: nombres de columnas, mensajes, descripciones de pruebas y gráficos.

## Instalación

Desde GitHub:

```bash
pip install git+https://github.com/TU_USUARIO/spyc.git
```

Desarrollo local:

```bash
git clone https://github.com/TU_USUARIO/spyc.git
cd spyc
pip install -e ".[dev]"
pytest --cov=spyc              # pruebas + cobertura (97% al momento de escribir esto)
ruff check src/                # estilo y errores comunes
mypy src/spyc                  # tipos
```

Ver [`CHANGELOG.md`](CHANGELOG.md) para el historial de versiones.

Requiere Python ≥ 3.9 (numpy, scipy, pandas, matplotlib).

## Inicio rápido

```python
import numpy as np
import spyc

rng = np.random.default_rng(1)
x = rng.normal(100, 2, 60)
x[40:] += 3                                   # el proceso se desplaza

carta = spyc.imr_chart(x, tests=(1, 2, 3, 4, 5, 6, 7, 8))
print(carta.summary())                        # resumen tipo sesión de Minitab
carta.violations()                            # DataFrame: panel, punto, prueba, descripción
carta.to_frame()                              # todos los valores, límites y pruebas fallidas
carta.plot()                                  # figura de matplotlib
```

## Cartas de control

| Minitab | Función | Notas |
|---|---|---|
| I-MR | `imr_chart(x)` | `sigma_method`: `'mr'`, `'median_mr'`, `'mssd'`; `span` configurable |
| Xbar-R | `xbar_r_chart(datos)` | `sigma_method`: `'rbar'`, `'pooled'` |
| Xbar-S | `xbar_s_chart(datos)` | `sigma_method`: `'sbar'`, `'pooled'` |
| P | `p_chart(defectuosos, n)` | límites variables con `n` variable |
| NP | `np_chart(defectuosos, n)` | |
| C | `c_chart(defectos)` | |
| U | `u_chart(defectos, n)` | |
| Laney P' / U' | `laney_p_chart`, `laney_u_chart` | corrige sobredispersión |
| EWMA | `ewma_chart(datos, weight=0.2, k=3)` | límites exactos (se ensanchan al inicio) |
| CUSUM | `cusum_chart(datos, h=4, k=0.5)` | tabular, sumas superior e inferior |
| Media móvil | `ma_chart(datos, length=3)` | límites más anchos en los primeros `length-1` puntos |
| Z-MR | `zmr_chart(x, partes)` | corridas cortas; ver más abajo |
| I-MR-R/S (entre/dentro) | `imr_rs_chart(datos, within='r')` | variación entre y dentro de subgrupos |
| G | `g_chart(entre_eventos)` | eventos raros, geométrica |
| T | `t_chart(tiempos)` | eventos raros, Weibull o exponencial |
| T² de Hotelling | `t2_chart(matriz)` | Fase I / Fase II, con diagnóstico por variable |
| Varianza generalizada | `generalized_variance_chart(matriz, subgroup_size=n)` | dispersión multivariada, `\|S\|` |
| MEWMA | `mewma_chart(matriz)` | límite por ARL (por defecto 200) |

Los datos de variables aceptan una matriz 2D (filas = subgrupos), un vector con
`subgroup_size=5`, o un vector con `subgroup=identificadores` (subgrupos de tamaño desigual).

```python
datos = rng.normal(50, 1, size=(25, 5))
spyc.xbar_r_chart(datos, tests=(1, 2, 3, 4)).summary()

vector = datos.ravel()                         # mismos datos en un solo vector
ids = np.repeat(np.arange(25), 5)              # identificador de subgrupo de cada dato
spyc.xbar_r_chart(vector, subgroup_size=5)
spyc.xbar_s_chart(vector, subgroup=ids)
```

**Parámetros históricos y etapas** (equivalentes a *Opciones de estimación* y *Etapas* de Minitab):

```python
spyc.imr_chart(x, mu=100, sigma=2)                      # parámetros conocidos
spyc.imr_chart(x, stages=["antes"] * 40 + ["después"] * 20)   # límites por etapa
```

**Atributos:**

```python
defectuosos = rng.binomial(200, 0.05, 30)
spyc.p_chart(defectuosos, n=200)
spyc.laney_p_chart(defectuosos, n=200)
```

## Cartas avanzadas

```python
# Z-MR: partes con medias y variaciones distintas en una sola carta (corridas cortas)
partes = ["A"] * 10 + ["B"] * 10 + ["A"] * 10
medidas = np.r_[rng.normal(50, 1, 10), rng.normal(80, 2, 10), rng.normal(50, 1, 10)]
spyc.zmr_chart(medidas, partes, sigma_method="by_part")   # 'constant', 'relative', 'by_part', 'by_run'

# I-MR-R/S: la variación entre subgrupos no genera falsas alarmas como en Xbar-R
sub = rng.normal(20, 1, (25, 5)) + rng.normal(0, 1.5, (25, 1))
c = spyc.imr_rs_chart(sub, within="s")
c.params[0]     # sigma_dentro, sigma_entre, sigma_entre_dentro

# Eventos raros
spyc.g_chart(rng.geometric(0.02, 40) - 1)                 # casos entre eventos
spyc.t_chart(rng.weibull(1.5, 40) * 30)                   # tiempo entre eventos

# Media móvil
spyc.ma_chart(x, length=5)
```

`zmr_chart` estandariza cada observación con la media de su parte y una sigma estimada
con el rango móvil *dentro de cada corrida* (bloque consecutivo de la misma parte);
`mu={parte: valor}` y `sigma=` aceptan valores históricos o nominales.

## Cartas multivariadas

```python
Sigma = [[1, .6, .3], [.6, 1, .2], [.3, .2, 1]]
historico = rng.multivariate_normal([0, 0, 0], Sigma, 100)
nuevos = rng.multivariate_normal([0, 0, 0], Sigma, 40)
nuevos[25:, 2] += 4                                       # la variable 3 se desplaza

# Fase I: parámetros estimados de los mismos datos
spyc.t2_chart(historico).summary()

# Fase II: parámetros históricos (n_hist = observaciones con que se estimaron)
c = spyc.t2_chart(nuevos, mu=historico.mean(axis=0), cov=np.cov(historico, rowvar=False),
                  n_hist=100)
c.violations()
c.contributions(31)                                       # ¿qué variable explica la señal?

# Subgrupos: matriz N x p con subgroup_size, o array 3-D (subgrupos x n x p)
spyc.t2_chart(nuevos[:40], subgroup_size=4)
spyc.generalized_variance_chart(nuevos[:40], subgroup_size=8)

# MEWMA: cambios pequeños y sostenidos
spyc.mewma_chart(nuevos, mu=historico.mean(axis=0), cov=np.cov(historico, rowvar=False))
spyc.mewma_limit(p=2, weight=0.1, arl=200)                # límite H para un ARL dado (≈ 8.64)
```

Los datos pueden ser un `DataFrame` (los nombres de columna se usan en `contributions`).
El límite de T² usa por defecto α = 0.00135 (cola de 3 sigmas, como Minitab). Sin `mu`/`cov`
se usan límites de **Fase I** (Beta para individuales, F para subgrupos); con `mu`/`cov` y
`n_hist`, de **Fase II**; con `mu`/`cov` sin `n_hist` los parámetros se toman como conocidos (χ²).

### Etapas y Box-Cox

Las 4 cartas multivariadas (T², varianza generalizada, MEWMA y MCUSUM) aceptan `stages`
y `boxcox`, igual que las cartas univariadas:

```python
etapas = [1] * 40 + [2] * 40                              # p. ej. antes/después de un ajuste

# Sin mu/cov: la media y la covarianza se vuelven a estimar dentro de cada etapa
c = spyc.t2_chart(nuevos_con_dos_etapas, stages=etapas)
c.stage_mean[1], c.stage_mean[2]                          # medias distintas por etapa
c.contributions(45)                                       # usa la media/cov de la etapa del punto 45

# Con mu/cov históricos: los mismos parámetros en todas las etapas
spyc.t2_chart(nuevos_con_dos_etapas, mu=mu, cov=cov, n_hist=100, stages=etapas)

# MEWMA y MCUSUM: el acumulador reinicia al empezar cada etapa
spyc.mewma_chart(nuevos_con_dos_etapas, stages=etapas)
spyc.mcusum_chart(nuevos_con_dos_etapas, stages=etapas)

# Box-Cox: una lambda por variable (no se puede combinar con mu/cov históricos)
c = spyc.t2_chart(datos_positivos, boxcox=True)
c.params[0]["lambda_boxcox"]                              # {'X1': ..., 'X2': ..., 'X3': ...}
spyc.generalized_variance_chart(datos_positivos, subgroup_size=6, boxcox=True)
spyc.mewma_chart(datos_positivos, boxcox=True)
spyc.mcusum_chart(datos_positivos, boxcox=True)
```

## Pruebas de causas especiales

Las 8 pruebas de Minitab (1 a 8) con sus parámetros por defecto
(`K` = 3, 9, 6, 14, 2, 4, 15, 8). Se piden con `tests=(...)` y se ajustan con `test_params`:

```python
spyc.imr_chart(x, tests=(1, 2, 5), test_params={2: 7})   # prueba 2 con 7 puntos
```

Cada tipo de carta aplica el subconjunto que corresponde (completo en I, Xbar y Z;
básicas 1-4 en MR, R, S, G, T y cartas de atributos; solo la 1 en EWMA, CUSUM, MA y las
multivariadas). En G y T la prueba 1 usa los percentiles de su distribución.
Las funciones individuales están en `spyc.rules`.

## Capacidad del proceso

```python
datos = rng.normal(10, 0.1, 100)
res = spyc.capability_analysis(datos, lsl=9.7, usl=10.3, subgroup_size=5)
print(res.summary())      # Cp, CPL, CPU, Cpk, Pp, PPL, PPU, Ppk, Cpm, Z.Bench, PPM, IC
res.to_frame()
res.plot()
```

Como en Minitab, **Cp/Cpk usan la desviación estándar dentro de subgrupos** y
**Pp/Ppk la desviación general**; por eso Cpk ≠ Ppk cuando el proceso se desplaza o hay variación entre subgrupos.

Datos no normales:

```python
spyc.capability_nonnormal(x, lsl=1, usl=20, distribution="weibull")
spyc.capability_boxcox(x, lsl=1, usl=20)
```

Distribuciones: `normal`, `lognormal`, `weibull`, `gamma`, `exponential`,
`loglogistic`, `logistic`, `largest_extreme`, `smallest_extreme` (método de percentiles).

`spyc.capability_sixpack(datos, lsl, usl, subgroup_size=5)` genera el **Capability Sixpack**.

## Normalidad, Pareto y constantes

```python
spyc.normality_test(x)                    # Anderson-Darling (por defecto), 'shapiro', 'dagostino'
spyc.probability_plot(x)

tabla = spyc.pareto(["rayón", "abolladura", "rayón", "otro"])
spyc.plot_pareto(tabla)

spyc.control_chart_constants(5)           # d2, d3, c4, c5, A2, A3, D3, D4, B3, B4
```

Las constantes se calculan por integración numérica para **cualquier** `n ≥ 2` (no solo tablas hasta 25).

## Validación

 pruebas automatizadas. Las referencias son independientes de spyc:

- Constantes d2, d3, c4 frente a las tablas publicadas (Montgomery).
- Límites I-MR, Xbar-R y Xbar-S frente al cálculo manual con A2, D3, D4, A3, B3, B4.
- Anderson-Darling frente a `statsmodels.stats.diagnostic.normal_ad` (coincide a 9 decimales).
- EWMA y CUSUM frente a la recursión manual.
- Las 8 pruebas de causas especiales frente a casos construidos a mano, incluidos los casos límite.
- T²: valores frente a `scipy.spatial.distance.mahalanobis`; los límites de Fase I y II
  (Beta y F) por simulación Monte Carlo (tasa de falsa alarma y valor esperado).
- Varianza generalizada: constantes b1 y b2 por simulación de matrices de covarianza.
- MEWMA: el límite para p=2, λ=0.1, ARL=200 da 8.63 (publicado: 8.64, Prabhu y Runger 1997)
  y el ARL se comprueba por simulación.
- G y T: cuantiles frente a `scipy.stats`, y máxima verosimilitud Weibull por su ecuación de score.
- Constantes de Z-MR (1.128 y 3.686) frente a las que documenta Minitab.

> **Importante:** spyc no se ha comparado corrida a corrida contra el software Minitab
> (no hay licencia disponible en el desarrollo). Sigue las fórmulas y convenciones que
> Minitab documenta. Si encuentras una diferencia, abre un issue (ver `CONTRIBUTING.md`).

## Fuera de alcance (por ahora)

Cartas multivariadas (T² de Hotelling), cartas de corridas cortas, Z-MR, I-MR-R/S
(entre/dentro), transformación de Johnson, MSA/Gage R&R.

## Licencia

MIT.
