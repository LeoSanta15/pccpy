# Plan — 010 Probabilidad de un valor x en el análisis de capacidad

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (método nuevo, principio 3; referencias independientes con `scipy.stats`, principios 1 y 13).

## Diseño

- `capability.py`: método `probability` en `CapabilityResult` y en `NonNormalCapabilityResult`, con un auxiliar privado común
  (`_probabilidad(cdf, sf, x, x2, kind, unit, opportunities)`) que valida la entrada y convierte la unidad. Cada clase aporta
  su `cdf` y su `sf`: la normal con `scipy.special.ndtr` (media y sigma elegida) y la no normal con `frozen`.
- Con `CapabilityResult.transform`, `x` y `x2` pasan por `Transformation.from_info(self.transform).forward` antes (la misma
  clase que ya usa `summary()`).
- `above` se calcula con la cola superior (`sf`), no con `1 − cdf`, para no perder precisión en las colas.
- `between` es `cdf(x2) − cdf(x)`; si ambos extremos caen en la misma cola, se usa `sf(x) − sf(x2)` para no restar dos números
  casi iguales a 1.
- Mensajes con `tr()` y traducción en `pccpy.po` (R-17).

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Método del resultado | Función suelta | Decisión de la persona responsable |
| Sigma general por defecto, `sigma="within"` opcional | Dentro por defecto | Decisión de la persona responsable (como el DPMO) |
| `kind` + `x2` | `below=`/`above=`/`between=` | Provisional: una sola firma (pregunta 2) |
| `dpu = opportunities·p` | Otra definición | Provisional (pregunta 1) |

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
