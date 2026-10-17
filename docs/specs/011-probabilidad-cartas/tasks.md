# Tareas — 011 Probabilidad de un valor en las cartas de control

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S011-RF-01 (falla hoy: los paneles no guardan la distribución; y los valores de las cartas no cambian).
- [x] Test de S011-RF-02 (variables: Xbar, I, EWMA, R, S, MR).
- [x] Test de S011-RF-03 (atributos: NP, P, C, U).
- [x] Test de S011-RF-04 (G y T).
- [x] Test de S011-RF-05 (sin argumentos y consistencia con `arl_*`).
- [x] Test de S011-RF-06 (`point=`, etapas, `n` variable).
- [x] Test de S011-RF-07 (transformación).
- [x] Test de S011-RF-08 (resultado: `ProbabilityResult` con `panel` y `point`; los resultados de capacidad no cambian).
- [x] Test de S011-RF-09 (entrada y casos borde).
- [x] Test de S011-RF-10 (docstrings; la comprobación de validación y el ejemplo ejecutable de la guía se prueban en la Fase 2).

## Fase 1 — Implementación

- [x] S011-RF-01: campo `dist` en `StagePanel`/`Panel` y su relleno en cada carta admitida.
- [x] S011-RF-02 y RF-03: familias de distribución y `ControlChart.probability`.
- [x] S011-RF-04: familias geométrica (G) y Weibull (T).
- [x] S011-RF-05 y RF-06: sin argumentos, `point=` y etapas.
- [x] S011-RF-07: transformación.
- [x] S011-RF-08 y RF-09: resultado y validación de entrada.

## Fase 2 — Verificación y cierre

- [x] Comprobación en `run_validation()` (S011-RF-10).
- [x] Documentación, exportación, traducciones y CHANGELOG (S011-RF-09).
- [x] `make check` en verde.
- [x] Estado de la especificación → `implementada`.
