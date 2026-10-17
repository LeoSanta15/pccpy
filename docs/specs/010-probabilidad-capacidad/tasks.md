# Tareas — 010 Probabilidad de un valor en el análisis de capacidad

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S010-RF-01 (falla hoy: `probability` no existe).
- [ ] Test de S010-RF-02 (fuera de un intervalo y límites heredados).
- [ ] Test de S010-RF-03 (con Box-Cox, Yeo-Johnson y Johnson).
- [ ] Test de S010-RF-04 (no normal).
- [ ] Test de S010-RF-05 (todas las medidas y `ProbabilityResult`).
- [ ] Test de S010-RF-06 (entrada y casos borde).
- [ ] Test de S010-RF-07 (coherencia con `ppm_overall`, `ppm_within` y `ppm_expected`).

## Fase 1 — Implementación

- [ ] S010-RF-01, RF-02, RF-05 y RF-06: `CapabilityResult.probability` y `ProbabilityResult`.
- [ ] S010-RF-03: transformación de los valores.
- [ ] S010-RF-04: `NonNormalCapabilityResult.probability`.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S010-RF-08).
- [ ] Documentación, exportación, traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
