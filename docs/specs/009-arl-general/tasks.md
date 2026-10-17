# Tareas — 009 ARL de las cartas Shewhart, EWMA y CUSUM

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S009-RF-01 (falla hoy: no existe `arl_shewhart`).
- [ ] Test de S009-RF-02 (falla hoy: no existe `arl_cusum`).
- [ ] Test de S009-RF-03 (falla hoy: no existe `arl_ewma`).
- [ ] Test de S009-RF-04 (parámetros inválidos, simetría, monotonía, `shift` como arreglo).

## Fase 1 — Implementación

- [ ] S009-RF-01: `arl_shewhart`.
- [ ] S009-RF-03: `arl_ewma`.
- [ ] S009-RF-02: `arl_cusum`.
- [ ] S009-RF-04: validación de entrada y casos borde.

## Fase 2 — Verificación y cierre

- [ ] Comprobaciones en `run_validation()` (S009-RF-05).
- [ ] Documentación, guía con ejemplo, traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
