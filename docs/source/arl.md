# ARL: comparar y diseñar cartas

El **ARL** (longitud media de racha, *average run length*) es el número esperado de puntos que se grafican hasta la primera
señal; la señal cuenta como un punto, así que el mínimo es 1. Con el proceso en control es el **ARL₀** (cuántos puntos pasan en
promedio antes de una falsa alarma: cuanto mayor, mejor); con la media desplazada es el **ARL₁** (cuántos puntos tarda en
detectarse el cambio: cuanto menor, mejor). Sirve para comparar cartas (Shewhart frente a EWMA frente a CUSUM) y para elegir
sus parámetros.

| Carta | Función |
|---|---|
| Shewhart de la media (un punto fuera de los límites) | {func}`pccpy.arl_shewhart` |
| CUSUM tabular bilateral | {func}`pccpy.arl_cusum` |
| EWMA bilateral | {func}`pccpy.arl_ewma` |
| S y R (dispersión) | {func}`pccpy.arl_sd`, {func}`pccpy.arl_range` |
| NP/P y C/U (atributos, tamaño constante) | {func}`pccpy.arl_binomial`, {func}`pccpy.arl_poisson` |
| G y T (eventos raros) | {func}`pccpy.arl_g`, {func}`pccpy.arl_t` |

## Supuestos

- Las observaciones son independientes en el tiempo y los parámetros del proceso (μ y σ) se **suponen conocidos**: el ARL no
  incluye el efecto de haberlos estimado en una Fase I.
- Solo cuenta la regla «un punto fuera de los límites»: **no** se aplican las pruebas suplementarias de rachas (pruebas 2 a 8).
- Las cartas de variables suponen un estadístico normal. `shift` es el desplazamiento de la media **en unidades de σ del
  estadístico graficado**: con subgrupos de tamaño `n` esa σ es σ/√n, así que un cambio de 1σ en la variable individual es
  `shift = √n`.
- Las de atributos y eventos raros usan su distribución exacta (binomial, Poisson, geométrica, Weibull).

## Comparar cartas frente a un desplazamiento de la media

```python
import numpy as np
import pandas as pd
import pccpy as pp

desp = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0])
tabla = pd.DataFrame({
    "desplazamiento (σ)": desp,
    "Shewhart (k=3)": pp.arl_shewhart(k=3, shift=desp),
    "EWMA (λ=0.2, L=2.9)": pp.arl_ewma(weight=0.2, L=2.9, shift=desp),
    "CUSUM (h=4, k=0.5)": pp.arl_cusum(h=4, k=0.5, shift=desp),
}).round(1)
print(tabla.to_string(index=False))
```

```text
 desplazamiento (σ)  Shewhart (k=3)  EWMA (λ=0.2, L=2.9)  CUSUM (h=4, k=0.5)
                0.0           370.4                416.5               167.7
                0.5           155.2                 38.3                26.6
                1.0            43.9                 10.1                  8.4
                1.5            15.0                  5.3                  4.7
                2.0             6.3                  3.7                  3.3
                3.0             2.0                  2.3                  2.2
```

Las tres cartas tienen ARL₀ distintos (370, 417 y 168), así que la comparación justa exige igualarlos: ajusta `L`, `h` o `k`
hasta que coincidan. La EWMA y la CUSUM detectan los desplazamientos pequeños (0,5σ a 1σ) mucho antes que la Shewhart; con
desplazamientos grandes (3σ o más) la Shewhart es igual de rápida.

## Elegir el método

Todas las funciones aceptan `method`:

- `"numeric"` (por defecto): fórmula cerrada o, en la CUSUM y la EWMA, ecuación integral con cuadratura de Gauss-Legendre.
- `"markov"`: cadena de Markov con celdas (solo CUSUM y EWMA).
- `"simulation"`: Monte Carlo, con `n_runs` (10 000 por defecto) y `seed` para reproducir el resultado. Su error es
  del orden de ARL/√`n_runs`.

```python
pp.arl_cusum(h=4, k=0.5, shift=1.0)                                   # 8.383 (numérico)
pp.arl_cusum(h=4, k=0.5, shift=1.0, method="markov")                  # 8.383
pp.arl_cusum(h=4, k=0.5, shift=1.0, method="simulation", n_runs=20_000, seed=1)   # ≈ 8.4
```

La EWMA usa límites asintóticos por defecto; con `exact_limits=True` los límites son más estrechos al principio y el ARL₀
baja: con λ = 0,2 y L = 3, de ≈ 560 a ≈ 555.

La CUSUM bilateral con `headstart = 0` combina los dos lados con `1/ARL = 1/ARL⁺ + 1/ARL⁻`, una aproximación que difiere
menos de 0,3 % de la simulación con h = 4 y k = 0,5. Con `headstart > 0` esa combinación falla (≈ 6 % con `headstart = h/2`),
porque las dos sumas pueden ser positivas a la vez; entonces se resuelve la cadena de Markov bidimensional, más lenta (del orden de
un segundo por llamada) y con un error de ≈ 0,1 %:

```python
pp.arl_cusum(h=4, k=0.5)                  # 167.7
pp.arl_cusum(h=4, k=0.5, headstart=2)     # 148.6 (arranque rápido)
```

## Cartas de dispersión, atributos y eventos raros

```python
pp.arl_sd(5), pp.arl_range(5)                         # ARL₀ de las cartas S y R con n = 5: 256.5 y 217.2
pp.arl_sd(5, ratio=1.5), pp.arl_range(5, ratio=1.5)   # si σ pasa a 1,5 σ₀: ≈ 7.0 y 7.2
pp.arl_binomial(100, 0.05)                            # carta NP con n = 100, p₀ = 0,05: ≈ 234.0 (no 370: distribución discreta)
pp.arl_binomial(100, 0.05, p1=0.10)                   # si p pasa a 0,10: ≈ 3.4
pp.arl_poisson(9, 12)                                 # carta C con c₀ = 9; si c pasa a 12: ≈ 26.7
pp.arl_t(shape=1.5), pp.arl_t(shape=1.5, scale_ratio=2.0)   # carta T: 370.4 y, con tiempos el doble de largos, ≈ 10.3
```

En las cartas de atributos el ARL₀ **no** es 370,4: la distribución es discreta y asimétrica, y los límites a ±3σ no dejan
una probabilidad de señal de 0,0027. La carta P con tamaño de muestra constante es la NP, y la U con área constante es la C
(con `c0 = n·u0`); con tamaños variables no hay un ARL único.

### Las cartas G y T detectan mucho mejor que los eventos se espacien que que se acorten

La carta G tiene límite superior pero su límite inferior es 0, así que `arl_g` solo detecta que los eventos se vuelven menos
frecuentes (`p1 < p0`). Con eventos más frecuentes (`p1 > p0`) el ARL se dispara:

```python
pp.arl_g(0.02)                 # 739.7 en control
pp.arl_g(0.02, p1=0.01)        # 26.7 (la mitad de eventos)
pp.arl_g(0.02, p1=0.04)        # ≈ 627 000 (el doble de eventos: la carta casi no lo ve)
```

Para ese caso `g_chart(..., benneyan=True)` añade la prueba de Benneyan (rachas de ceros), que este ARL no incluye.

La carta T tiene el mismo problema en el extremo opuesto del tiempo: su límite inferior (el percentil Φ(−3) de la Weibull) está
muy cerca de 0. Con la escala del tiempo al doble el ARL baja de 370 a ≈ 10, pero con tiempos más cortos casi no mejora (con
`scale_ratio = 0.5`, ≈ 262; con 0,7, ≈ 432, incluso más que en control):

```python
[round(pp.arl_t(shape=1.5, scale_ratio=r), 1) for r in (0.3, 0.5, 0.7, 1.0, 1.5, 2.0)]
# [122.1, 262.2, 431.7, 370.4, 35.5, 10.3]
```

## Probabilidad de un valor desde una carta

El ARL parte de parámetros sueltos. Con una carta ya construida, `chart.probability()` da la probabilidad de un valor del
estadístico que grafica (la media del subgrupo, el rango, el conteo…) con el proceso en control y los parámetros de la carta tratados
como conocidos. Sin argumentos es la probabilidad de que **un punto** salga de los límites, cuya inversa es el ARL₀ de arriba:

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(1)
g = rng.normal(50, 2, (25, 5))
chart = pp.xbar_r_chart(g, mu=50, sigma=2)

p = chart.probability()                         # un punto fuera de los límites de la carta Xbar
p.probability, 1 / p.probability                # 0.0027 y 370.4 (= pp.arl_shewhart(k=3))
chart.probability(above=51).probability        # P(media de 5 piezas > 51) = 0.132
chart.probability(panel="R", above=6).probability   # P(rango > 6) = 0.211
1 / chart.probability(panel="R").probability   # ARL₀ de la carta R con n = 5: 217.2 (= pp.arl_range(5))
```

Con tamaños de muestra variables, etapas o una EWMA la distribución cambia de un punto a otro: indica `point=` (base 1) o recibes un
error que lo pide.

```python
n = np.array([100, 150, 200] * 10)
chart_p = pp.p_chart(rng.binomial(n, 0.05), n, p=0.05)
chart_p.probability(above=0.08, point=[1, 3]).probability   # una probabilidad por punto, con su n: [0.063, 0.024]
```

Los valores son del estadístico (en proporción o defectos por unidad en las cartas P y U; en unidades originales con `transform=`).
Admiten la consulta las cartas I-MR, Xbar-R, Xbar-S, P, NP, C, U, EWMA, G y T; no la CUSUM, la media móvil, la carta de zona, las de
Laney ni las multivariadas. El resultado es el mismo `ProbabilityResult` de la capacidad, con `dpmo`, `dpu` y `sigma` en `None` y los
campos `panel` y `point`. No se ha comparado con Minitab.

## Qué no se ha comprobado

- Las cifras de la literatura que se mencionan (ARL₀ = 168 de la CUSUM con h = 4 y k = 0,5, ≈ 500 de la EWMA con λ = 0,2 y
  L = 2,962, 370,4 de la Shewhart) las recordamos de memoria y se contrastan con simulaciones propias; no pudimos consultar
  los artículos originales. La validación ({doc}`validacion`) usa las simulaciones y las fórmulas cerradas, no esas cifras.
- No se ha comparado con el ARL de Minitab.
