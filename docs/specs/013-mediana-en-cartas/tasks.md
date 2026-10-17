# Tareas — 013 Mediana en las cartas de variables

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S013-RF-01 (falla hoy: `imr_chart` no tiene `center`).
- [ ] Test de S013-RF-02 (Xbar-R y Xbar-S).
- [ ] Test de S013-RF-03 (`mu` con `center="median"` y valor inválido).
- [ ] Test de S013-RF-04 (`median_r_chart` no existe; `Ã2` contra integración y Monte Carlo).
- [ ] Test de S013-RF-05 (tamaños de subgrupo).
- [ ] Test de S013-RF-06 (`probability()` de la carta X̃).
- [ ] Test de S013-RF-07 (claves y traducción).

## Fase 1 — Implementación

- [ ] S013-RF-01 y RF-02: `center=` en las tres cartas.
- [ ] S013-RF-03: validaciones.
- [ ] S013-RF-04 y RF-05: `cmed(n)` y `median_r_chart`.
- [ ] S013-RF-06: familia `"median"` en `Panel.dist`.
- [ ] S013-RF-07: claves, `_PARAMETROS` y textos traducidos.

## Fase 2 — Verificación y cierre

- [ ] Comprobaciones en `run_validation()` (RF-01, RF-04, RF-06).
- [ ] Documentación, README (es/en) con figura, traducciones y CHANGELOG (S013-RF-08).
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
