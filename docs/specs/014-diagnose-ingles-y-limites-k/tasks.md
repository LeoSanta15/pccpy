# Tareas — 014 Valores en inglés de `diagnose()` y ancho de los límites de control

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S014-RF-01 (falla hoy: `trend_direction` devuelve `'creciente'`).
- [ ] Test de S014-RF-02 (`summary()` en español igual al golden; en inglés, «increasing»).
- [ ] Test de S014-RF-03 (el `grep` de `src/`, tests y documentación).
- [ ] Test de S014-RF-04 (falla hoy: `imr_chart` no acepta `k`; valor y pareja).
- [ ] Test de S014-RF-05 (atributos).
- [ ] Test de S014-RF-06 (Z-MR e I-MR-R/S).
- [ ] Test de S014-RF-07 (la prueba 1 coincide con los límites; aviso con `test_params`).
- [ ] Test de S014-RF-08 (`k` y `alpha` inválidos, parejas de longitud incorrecta).
- [ ] Test de S014-RF-09 (`transform`, `stages`, `mu`/`sigma`).
- [ ] Test de S014-RF-10 (`k_upper`/`k_lower` en `params`, `probability()` y ARL).
- [ ] Test de S014-RF-11 (`alpha` valor y pareja, `k_from_confidence`).
- [ ] Test de S014-RF-12 (`rescale_zones`).
- [ ] Test de S014-RF-13 (fragmento del README).

## Fase 1 — Implementación

- [ ] S014-RF-01: valores en inglés en `_diagnose.py`.
- [ ] S014-RF-02: `_tendencia()` traduce desde las claves inglesas.
- [ ] S014-RF-03: literales en tests y documentación.
- [ ] S014-RF-08 y RF-11: `resolve_k`, `alpha` y `k_from_confidence`.
- [ ] S014-RF-04 a RF-06: `k` en las cartas (arriba y abajo).
- [ ] S014-RF-07: umbral de la prueba 1 y aviso.
- [ ] S014-RF-12: `rescale_zones`.
- [ ] S014-RF-09 y RF-10: transformación, etapas y `params`.

## Fase 2 — Verificación y cierre

- [ ] Comprobaciones en `run_validation()` (RF-04, RF-05, RF-10).
- [ ] Documentación, README (es/en), traducciones y CHANGELOG (S014-RF-13).
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
