# Tareas — 007 Prueba de Benneyan en la carta G

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S007-RF-01 (falla hoy: `benneyan` no existe).
- [x] Test de S007-RF-02 (falla hoy: `benneyan` no existe); incluye la guarda de `benneyan=False` idéntico a 0.15.1.
- [x] Test de S007-RF-03 (rachas que cruzan etapas).

## Fase 1 — Implementación

- [x] S007-RF-01: `_benneyan_run`.
- [x] S007-RF-02: parámetros `benneyan` y `benneyan_marks`, violaciones y descripción.
- [x] S007-RF-03: conteo por etapa.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S007-RF-01).
- [ ] Documentación, traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
