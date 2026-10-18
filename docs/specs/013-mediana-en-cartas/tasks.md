# Tareas — 013 Mediana en las cartas de variables

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S013-RF-01 (falla hoy: `imr_chart` no tiene `center`).
- [x] Test de S013-RF-02 (Xbar-R y Xbar-S).
- [x] Test de S013-RF-03 (`mu` con `center="median"` y valor inválido).
- [x] Test de S013-RF-04 (`median_r_chart` no existe; `Ã2` contra integración y Monte Carlo).
- [x] Test de S013-RF-05 (tamaños de subgrupo).
- [x] Test de S013-RF-06 (`probability()` de la carta X̃).
- [x] Test de S013-RF-07 (claves y traducción).

## Fase 1 — Implementación

- [x] S013-RF-01 y RF-02: `center=` en las tres cartas.
- [x] S013-RF-03: validaciones.
- [x] S013-RF-04 y RF-05: `cmed(n)` y `median_r_chart`.
- [x] S013-RF-06: familia `"median"` en `Panel.dist`.
- [x] S013-RF-07: claves, `_PARAMETROS` y textos traducidos.

## Fase 2 — Verificación y cierre

- [x] Comprobaciones en `run_validation()` (RF-01, RF-04, RF-06).
- [x] Documentación, README (es/en) con figura, traducciones y CHANGELOG (S013-RF-08).
- [x] `make check` en verde.
- [x] Estado de la especificación → `implementada`.
