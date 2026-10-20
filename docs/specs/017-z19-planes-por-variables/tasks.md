# Tareas — 017 Z1.9: planes de muestreo por variables con las tablas de la norma

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Recibir las tablas de la norma y transcribirlas en `tests/`; la persona responsable las revisa celda a celda (S017-RF-01, RF-02 y las adicionales).
- [ ] Test de S017-RF-01 (falla hoy: la letra sale de la tabla I de Z1.4).
- [ ] Test de S017-RF-02 (falla hoy: los planes de `_Z19_TABLE` no son los de la norma).
- [ ] Test de S017-RF-03 (la Forma 1: pasa antes del código si solo protege lo que no cambia).
- [ ] Test de S017-RF-04 (falla hoy: `n` mayor que el lote).
- [ ] Test de S017-RF-05 (falla hoy: `pa` es la aproximación normal).
- [ ] Tests de S017-RF-06 y RF-07 si entran.

## Fase 1 — Implementación

- [ ] S017-RF-01: tabla A-2 y letra de código de Z1.9.
- [ ] S017-RF-02: tabla B-1 y resolución de flechas.
- [ ] S017-RF-03: Forma 1 de `evaluate`.
- [ ] S017-RF-04: guarda del 100 %.
- [ ] S017-RF-05: OC con la t no central.
- [ ] S017-RF-06 y RF-07 si entran.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S017-RF-01, RF-02 y RF-05).
- [ ] Regenerar `tests/golden/` y revisar el diff línea a línea.
- [ ] Fichas en `BUG_CATALOG.md` (la tabla aproximada y, si procede, el 100 %).
- [ ] Documentación, README (es/en), traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
