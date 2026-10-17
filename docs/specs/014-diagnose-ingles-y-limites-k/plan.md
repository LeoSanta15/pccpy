# Plan — 014 Valores en inglés de `diagnose()` y ancho de los límites de control

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada en la parte A: cambia un valor devuelto (principio 3, «lo existente no cambia sin avisar»); se avisa en el CHANGELOG, sin alias, igual que la spec 012.

## Parte A — `diagnose()`

- `_diagnose.py`: la línea que calcula la tendencia produce `"increasing"`/`"decreasing"`; `_tendencia()` mapea esas claves a `tr("creciente")`/`tr("decreciente")`; el comentario del campo lista los valores nuevos.
- `tests/test_diagnose.py` y los golden estables: valores nuevos; `tests/golden/i18n_es.json` sin cambios. Catálogos `.po`: los `msgid` en español no cambian.
- Decisión: valores `'increasing'`/`'decreasing'` (paralelos a `non_normal_reason`) en lugar de `'up'`/`'down'` o `±1`; sin alias (decisión de la spec 012).
- Validación independiente: signo de `scipy.stats.linregress` sobre los datos de los tests.

## Parte B — `k` y `alpha`

- `charts/variables.py`, `attributes.py`, `advanced.py` (Z-MR, I-MR-R/S): parámetros `k=3.0`, `alpha=None` y `rescale_zones=False` (en las cartas con zonas); las constantes `3 *` de los límites pasan a `k_sup *` arriba y `k_inf *` abajo.
  Un auxiliar `resolve_k(k, alpha)` en `charts/_engine.py` valida (finito, > 0, no `bool`; un valor o una pareja; `alpha` en (0,1); no ambos) con `tr()` y devuelve `(k_sup, k_inf)`: un valor `alpha` bilateral, `Φ⁻¹(1 − α/2)`; una pareja, `Φ⁻¹(1 − αᵢ)` por lado.
  `k_from_confidence` vive en `_constants.py` y se exporta desde `__init__.py`.
- `build_chart`: el umbral de la prueba 1 es `test_params.get(1, k_sup)` arriba y `test_params.get(1, k_inf)` abajo; si `k`/`alpha` se dio y `test_params[1]` difiere, `UserWarning`. `params` guarda `k_upper` y `k_lower`.
  Con `rescale_zones`, el `sigma` que recibe `rules.apply_tests` se escala por `k_lado/3` para las pruebas 2 a 8, lado a lado.
- `results.py`: `_PARAMETROS["k_upper"]`, `["k_lower"]`; `transform`: límites con `k` en la escala transformada y `aplicar_escala` como hoy.
- `_probabilidad_cartas.py`: no cambia (usa los límites guardados).

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| `k` y `alpha`, excluyentes; valor = bilateral, pareja = unilateral por lado | Solo `k` simétrico | Decisión de la persona responsable |
| Zonas en σ por defecto, `rescale_zones` opcional | Reescalar siempre | Decisión de la persona responsable |
| La prueba 1 sigue a `k` | Umbral fijo 3 | Lo marcado debe coincidir con lo dibujado |
| `test_params[1]` explícito gana | Error | Compatibilidad con código existente |

## Validación independiente

`run_validation()`: límites con `k=2`, `k=2,576` y `k=(3, 2)` de I, Xbar, R y P contra la fórmula de Montgomery; probabilidad de falsa alarma de I, R y P con `k=2` y `k=(3, 2)` contra simulación (≥ 20 semillas).

## Riesgos

- Código de usuario que compare `trend_direction` con `'creciente'`: se anuncia en el CHANGELOG.
- Que se lea `k` como confianza exacta en R/S/atributos: la documentación lo aclara.
- Muchos sitios con `3 *` literal: `grep` en `charts/` y test de que `k=3` da resultados idénticos (golden, `tests/golden/`) sin regenerar.

## Documentación y traducciones

CHANGELOG, README (es/en), `docs/source`, docstrings, `docs/locales/en`, `.po` (aviso y errores nuevos) y CLAUDE.md.
