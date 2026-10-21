# Tareas — 017 Planes por variables: MIL-STD-414

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Transcribir las tablas A-2 y B-1 del anexo en `tests/` y que la persona responsable las revise celda a celda (S017-RF-01, S017-RF-02, S017-RF-03).
- [x] Test de S017-RF-01 (falla hoy: la letra sale de la tabla I de Z1.4).
- [x] Test de S017-RF-02 (falla hoy: los planes de `_Z19_TABLE` no son los de la norma).
- [x] Test de S017-RF-03 (falla hoy: no existe `inspection="tightened"`).
- [x] Test de S017-RF-04 (la Forma 1: pasa antes del código porque protege lo que no cambia).
- [x] Test de S017-RF-05 (falla hoy: `n` mayor que el lote).
- [x] Test de S017-RF-06 (falla hoy: no existe `standard`; incluye los `ValueError` de `"z1.9"`, del AQL fuera de la tabla y de `spec_type="two"`).

## Fase 1 — Implementación

- [x] S017-RF-01: tabla A-2 y letra de código.
- [x] S017-RF-02: tabla B-1 y resolución de flechas.
- [x] S017-RF-03: inspección rigurosa.
- [x] S017-RF-04: Forma 1 de `evaluate`.
- [x] S017-RF-05: guarda del 100 %.
- [x] S017-RF-06: parámetro `standard` y retirada de la tabla aproximada.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S017-RF-01, S017-RF-02 y S017-RF-03).
- [ ] Regenerar `tests/golden/` y revisar el diff línea a línea.
- [ ] Fichas en `BUG_CATALOG.md` (la tabla aproximada y, si procede, el 100 %).
- [ ] Documentación, README (es/en), traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
