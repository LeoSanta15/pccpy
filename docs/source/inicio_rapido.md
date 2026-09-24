# Inicio rápido

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

Cada tipo de carta tiene su propia página en la {doc}`referencia/index`, con
ejemplos y la descripción exacta de cada parámetro (extraída directamente de los
docstrings, así que siempre coincide con el código instalado).

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
