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

## Un vistazo por tema

- **Variables** (I-MR, Xbar-R, Xbar-S, media móvil, Z-MR, I-MR-R/S, Zona):
  {doc}`referencia/variables` y {doc}`referencia/avanzadas`.
- **Atributos** (P, NP, C, U, Laney P′/U′): {doc}`referencia/atributos`.
- **Tiempo ponderado** (EWMA, CUSUM): {doc}`referencia/tiempo_ponderado`.
- **Multivariadas** (T², varianza generalizada, MEWMA, MCUSUM, con etapas y
  Box-Cox): {doc}`referencia/multivariadas`.
- **Capacidad del proceso**: {doc}`referencia/capacidad`.
- **Normalidad, Pareto y constantes**: {doc}`referencia/normalidad_y_herramientas`
  y {doc}`referencia/constantes`.
- **Objetos de resultado** (`ControlChart`, `MultivariateChart`, `Panel`, y los
  resultados de capacidad y normalidad): {doc}`referencia/resultados`.
