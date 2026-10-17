# Tareas — 009 ARL de las cartas de control

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan (núcleo: RF-01 a RF-05)

- [ ] Test de S009-RF-01 (falla hoy: no existe `arl_shewhart`).
- [ ] Test de S009-RF-02 (falla hoy: no existe `arl_cusum`).
- [ ] Test de S009-RF-03 (falla hoy: no existe `arl_ewma`).
- [ ] Test de S009-RF-04 (elección de método, semilla, métodos no admitidos).
- [ ] Test de S009-RF-05 (parámetros inválidos, simetría, monotonía, `shift` como arreglo).

## Fase 1 — Implementación del núcleo

- [ ] S009-RF-01: `arl_shewhart`.
- [ ] S009-RF-04: simulación común y cadena de Markov.
- [ ] S009-RF-03: `arl_ewma`.
- [ ] S009-RF-02: `arl_cusum` (decidir la combinación de lados con los datos).
- [ ] S009-RF-05: validación de entrada y casos borde.

## Fase 2 — Dispersión, atributos y eventos raros (RF-06 a RF-08)

- [ ] Tests de S009-RF-06, S009-RF-07 y S009-RF-08 (fallan hoy: las funciones no existen).
- [ ] S009-RF-06: `arl_sd` y `arl_range`.
- [ ] S009-RF-07: `arl_binomial` y `arl_poisson`.
- [ ] S009-RF-08: `arl_g` y `arl_t`.

## Fase 3 — Verificación y cierre

- [ ] Comprobaciones en `run_validation()` (S009-RF-09).
- [ ] Documentación, guía con ejemplo, traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
