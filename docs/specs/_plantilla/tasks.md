# Tareas — NNN Título corto

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de SNNN-RF-01 (falla hoy porque …).
- [ ] Test de SNNN-RF-02.

## Fase 1 — Implementación

- [ ] SNNN-RF-01: …
- [ ] SNNN-RF-02: …

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (SNNN-RF-01).
- [ ] Regenerar `tests/golden/` y revisar el diff línea a línea (si cambian resultados).
- [ ] Documentación, traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
