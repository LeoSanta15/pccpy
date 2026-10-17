# Plan — 014 Dirección de la tendencia en inglés

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: cambia un valor devuelto (principio 3, «lo existente no cambia sin avisar»); se avisa en el
  CHANGELOG, sin alias, igual que la spec 012.

## Diseño

- `_diagnose.py`: línea 367 produce `"increasing"`/`"decreasing"`; `_tendencia()` mapea esas claves a `tr("creciente")`/`tr("decreciente")`; el
  comentario del campo lista los valores nuevos.
- `tests/test_diagnose.py`, golden estables: valores nuevos; `tests/golden/i18n_es.json` sin cambios.
- Catálogos `.po`: los `msgid` en español no cambian.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Sin alias | Aceptar ambos valores | Decisión tomada en la spec 012 |
| Valores `'increasing'`/`'decreasing'` | `'up'`/`'down'`, `+1`/`-1` | Legibles y paralelos a `non_normal_reason` (palabras inglesas) |

## Validación independiente

Signo de `scipy.stats.linregress` sobre los datos de los tests. Sin comprobación nueva en `run_validation()`.

## Riesgos

- Código de usuario que compare con `'creciente'`: se anuncia en el CHANGELOG.

## Documentación y traducciones

CHANGELOG, README y guías que citen el valor, docstring de `DiagnoseResult`.
