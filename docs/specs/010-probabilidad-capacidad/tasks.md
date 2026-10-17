# Tareas — 010 Probabilidad de un valor x en el análisis de capacidad

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S010-RF-01 (falla hoy: `probability` no existe).
- [ ] Test de S010-RF-02 (con Box-Cox, Yeo-Johnson y Johnson).
- [ ] Test de S010-RF-03 (no normal).
- [ ] Test de S010-RF-04 (unidades).
- [ ] Test de S010-RF-05 (entrada y casos borde).
- [ ] Test de S010-RF-06 (coherencia con `ppm_overall`, `ppm_within` y `ppm_expected`).

## Fase 1 — Implementación

- [ ] S010-RF-01, RF-04 y RF-05: `CapabilityResult.probability`.
- [ ] S010-RF-02: transformación de `x`.
- [ ] S010-RF-03: `NonNormalCapabilityResult.probability`.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S010-RF-07).
- [ ] Documentación, traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
