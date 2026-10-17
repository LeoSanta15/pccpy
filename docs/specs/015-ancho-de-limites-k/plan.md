# Plan — 015 Ancho de los límites de control (`k`)

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí.

## Diseño

- `charts/variables.py`, `attributes.py`, `advanced.py` (Z-MR, I-MR-R/S): parámetro `k=3.0` y las constantes `3 *` de los límites pasan a `k *`; en dispersión,
  `c ± k·sd`. Un auxiliar `check_k(k)` en `charts/_engine.py` valida (finito, > 0, no `bool`) con `tr()`.
- `build_chart`: el umbral de la prueba 1 es `test_params.get(1, k)`; si `k` se dio explícito y `test_params[1]` difiere, `UserWarning`. `k` viaja en `params`.
- `results.py`: `_PARAMETROS["k"]`; `_labels`/`@con_etiquetas` sin cambios.
- `transform`: se calcula en la escala transformada con `k` y `aplicar_escala` devuelve los límites como hoy.
- `_probabilidad_cartas.py`: no cambia (usa los límites guardados).

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| `k` en sigmas | `alpha`/`confidence` | Igual que EWMA, MA, G, T; en R, S y atributos la confianza no es única |
| Zonas y pruebas 2–8 en σ | Reescalarlas con `k/3` | Las zonas A/B/C se definen sobre σ; reescalar cambiaría el significado de las pruebas |
| La prueba 1 sigue a `k` | Umbral fijo 3 | Lo marcado debe coincidir con lo dibujado |
| `test_params[1]` explícito gana | Error | Compatibilidad con código existente |

## Validación independiente

`run_validation()`: límites con `k=2` y `k=2,576` de I, Xbar, R, P contra la fórmula de Montgomery; probabilidad de falsa alarma de I, R y P con `k=2` contra
simulación (≥ 20 semillas).

## Riesgos

- Que se lea `k` como confianza exacta en R/S/atributos: la documentación lo aclara.
- Muchos sitios con `3 *` literal: `grep` en `charts/` y test de que `k=3` da resultados idénticos (golden, `tests/golden/`) sin regenerar.

## Documentación y traducciones

README (es/en), `docs/source`, docstrings, `docs/locales/en`, `.po` (aviso y errores nuevos), CHANGELOG y CLAUDE.md.
