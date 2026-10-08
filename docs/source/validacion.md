# Validación de la instalación

`pccpy` incluye una validación que **comprueba la biblioteca contra referencias independientes**: tablas publicadas,
fórmulas escritas aparte con NumPy y SciPy, definiciones y simulaciones con semilla fija. Sirve para documentar que la
versión instalada calcula bien (por ejemplo, en un sistema de calidad regulado) y para detectar regresiones.

```python
import pccpy as pp

informe = pp.run_validation()
print(informe.summary())      # «Validación de pccpy …: 37 de 37 comprobaciones correctas»
informe.passed                # True si todo coincide
informe.to_frame()            # una fila por comprobación (error y tolerancia)
```

Desde la línea de órdenes, con un informe en Markdown (devuelve código de salida 0 si todo es correcto):

```bash
python -m pccpy.validation --markdown validacion.md
```

## Qué se comprueba

| Área | Referencia |
|------|-----------|
| Constantes d2, d3, c4, A2, A3, D3, D4, B3, B4 | Tabla de factores de Montgomery (n = 2, 5, 10) |
| Límites de I-MR, Xbar-R, Xbar-S, P, NP, C y U | Fórmulas manuales; d2 y d3 por integración numérica |
| Pruebas de causas especiales 1 a 8 | Patrones construidos a mano; tasa de falsas alarmas por simulación |
| Cp, Cpk, Pp, Ppk, Z.Bench y PPM | Fórmulas con la distribución normal |
| Intervalos bootstrap de Pp y Ppk | Fórmulas de Pp y Ppk escritas aparte, con los mismos remuestreos |
| Yeo-Johnson y familia de Johnson | `scipy.stats.yeojohnson`; `Φ⁻¹(F(x))` con las distribuciones de scipy |
| Bootstrap (BCa y percentil) | `scipy.stats.bootstrap` (diferencia dentro del error de Monte Carlo) |
| Capacidad binomial y Poisson | Intervalos exactos de SciPy (Clopper-Pearson) y cuantiles de la gamma (Garwood) |
| Anderson-Darling | Estadístico A² calculado por separado |
| Intervalos de tolerancia | Factores k conocidos (n = 10, 95/95) |
| Muestreo de aceptación | Celdas de las tablas I y II-A de Z1.4 (niveles I, II y III); probabilidad binomial acumulada |
| Gage R&R, Tipo 1, linealidad, kappa | Cuadrados medios del ANOVA, fórmulas de Cg/Cgk, regresión exacta, definición de κ |
| T² de Hotelling y MEWMA | Fórmulas y límites conocidos |

## Qué no es

- **No es una comparación con Minitab** ni con otro programa: usa referencias independientes, no otro software.
- No sustituye la validación del proceso de quien la usa: demuestra que los cálculos de `pccpy` son correctos, no que
  los datos o su uso lo sean.
- Cada comprobación tiene una tolerancia numérica documentada en el informe.

```{eval-rst}
.. autofunction:: pccpy.run_validation

.. autoclass:: pccpy.ValidationReport
   :members: passed, failures, to_frame, summary, to_markdown
```
