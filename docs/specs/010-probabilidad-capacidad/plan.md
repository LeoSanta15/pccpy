# Plan — 010 Probabilidad de un valor en el análisis de capacidad

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (método nuevo, principio 3; referencias independientes con `scipy.stats`, principios 1 y 13).

## Diseño

- `capability.py`: método `probability(*, below, above, between, sigma, opportunities)` en `CapabilityResult` y en
  `NonNormalCapabilityResult`, y la clase de resultado `ProbabilityResult` (dataclass con `event`, `probability`, `ppm`, `dpmo`,
  `dpu`, `p_below`, `p_above`, los valores usados, `sigma` y `opportunities`; `summary()` y `to_frame(stable=False)`). Un auxiliar
  privado común valida la entrada, interpreta los parámetros y arma el resultado a partir de dos funciones que aporta cada clase:
  `cdf(x)` y `sf(x)` (la normal con `scipy.special.ndtr`; la no normal con `frozen`).
- Con `CapabilityResult.transform`, los valores pasan por `Transformation.from_info(self.transform).forward` antes (la misma
  clase que ya usa `summary()`).
- `above` se calcula con la cola superior, no con `1 − cdf`, para no perder precisión; `between` es `cdf(b) − cdf(a)` o
  `sf(a) − sf(b)` si ambos están en la cola superior.
- Sin argumentos se usan `lsl` y `usl` del resultado (en unidades originales también con transformación).
- Exportar `ProbabilityResult` en `__init__.py` y `__all__`; mensajes y etiquetas con `tr()` y traducción en `pccpy.po` (R-17).

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Método del resultado | Función suelta | Decisión de la persona responsable |
| `below`/`above`/`between` | `kind` + `x` | Decisión de la persona responsable: el valor va en el parámetro |
| Devuelve todas las medidas en un `ProbabilityResult` | `unit=` para elegir una | Decisión de la persona responsable |
| Sigma general por defecto | Dentro por defecto | Decisión de la persona responsable (como el DPMO) |
| Un valor por llamada | Arreglos | Simplicidad; un bucle cubre el caso |

## Validación independiente

`scipy.stats.norm` escrito en el test para la normal; Box-Cox escrito en el test para la transformación; re-ajuste con
`scipy.stats` para la no normal (tolerancia relativa 1e-3, justificada en la spec); coherencia con `ppm_overall`,
`ppm_within` y `ppm_expected`. Una comprobación en `run_validation()` (62 en total).

## Riesgos

- Con transformaciones, `probability` supone que la transformación es creciente: lo es para Box-Cox, Yeo-Johnson y Johnson;
  se comprueba con un test de las tres.
- La comparación entre el re-ajuste de SciPy y el de pccpy depende de la versión de SciPy (por eso 1e-3).
- `x` en unidades originales con una transformación puede dar `nan` si `x` no está en el dominio (p. ej. Box-Cox con `x ≤ 0`):
  se decide en la implementación (`ValueError` con mensaje claro o 0/1 según el lado).

## Documentación y traducciones

Docstrings, sección en `capacidad_indices.md`, README (es/en), CHANGELOG, validación (`validacion.md`) y catálogos de
traducción de la biblioteca y de la documentación.
