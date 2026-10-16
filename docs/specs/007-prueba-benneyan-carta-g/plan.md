# Plan — 007 Prueba de Benneyan en la carta G

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (opt-in, principio 3; la fórmula no verificada se declara, principio 12).

## Diseño

- `charts/advanced.py`: función privada `_benneyan_run(p, k)` que devuelve `c`, y `_benneyan_violations(xs, c)` que
  devuelve los índices (rachas de ceros). `g_chart` gana `benneyan: bool = False`; en `stage_fn` se añade el resultado a
  `viol` por etapa (RF-03).
- La clave de la violación y su descripción en `results.py` dependen de la pregunta 3; hay que revisar `_violations`,
  `summary()` y el gráfico (marca «B») sin romper que hoy las claves son enteros.
- Actualizar el docstring de `g_chart` (quitar «No incluye…»).

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Parámetro `benneyan` aparte | Número de prueba nuevo en `tests=` | `tests` valida enteros 1–8 en `rules.normalize_tests` |
| Opt-in | Activada por defecto como Minitab | No cambiar resultados sin avisar |

(Provisional hasta resolver las preguntas 3 y 4.)

## Validación independiente

Comprobación nueva en `run_validation()`: `c` para varios `p` contra el cálculo manual de `p^c ≤ α`, y falsas alarmas por
punto con ≥ 20 semillas (geométrica simulada con `p` conocido) frente a `α`, con tolerancia por el error de Monte Carlo.

## Riesgos

- Fórmula de `c` distinta de la de Minitab (pregunta 1): se documenta y no se afirma equivalencia.
- Claves no enteras en `violations` pueden romper código que ordena o indexa por prueba.

## Documentación y traducciones

Docstring, página de cartas avanzadas, README (es/en), CHANGELOG, catálogos `.po` (`make i18n-update`, `make docs-update`).
