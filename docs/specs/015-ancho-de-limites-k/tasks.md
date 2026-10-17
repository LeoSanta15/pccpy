# Tareas — 015 Ancho de los límites de control (`k`)

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S015-RF-01 (falla hoy: `imr_chart` no acepta `k`).
- [ ] Test de S015-RF-02 (atributos).
- [ ] Test de S015-RF-03 (Z-MR e I-MR-R/S).
- [ ] Test de S015-RF-04 (la prueba 1 coincide con los límites; aviso con `test_params`).
- [ ] Test de S015-RF-05 (`k` inválido).
- [ ] Test de S015-RF-06 (`transform`, `stages`, `mu`/`sigma`).
- [ ] Test de S015-RF-07 (`params["k"]`, `probability()` y ARL).
- [ ] Test de S015-RF-09 (`alpha`, `k_from_confidence`).
- [ ] Test de S015-RF-10 (`rescale_zones`).
- [ ] Test de S015-RF-08 (fragmento del README).

## Fase 1 — Implementación

- [ ] S015-RF-05 y RF-09: `resolve_k`, `alpha` y `k_from_confidence`.
- [ ] S015-RF-01 a RF-03: `k` en las cartas.
- [ ] S015-RF-04: umbral de la prueba 1 y aviso.
- [ ] S015-RF-10: `rescale_zones`.
- [ ] S015-RF-06 y RF-07: transformación, etapas y `params`.

## Fase 2 — Verificación y cierre

- [ ] Comprobaciones en `run_validation()` (RF-01, RF-02, RF-07).
- [ ] Documentación, README (es/en), traducciones y CHANGELOG (S015-RF-08).
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
