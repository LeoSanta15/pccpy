# Tareas — 016 Z1.4: niveles especiales, muestreo doble y plan que no cabe en el lote

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Transcribir las tablas I, II-A y III-A en `tests/` y que la persona responsable las revise celda a celda (S016-RF-01, RF-02, RF-03).
- [ ] Test de S016-RF-01 (falla hoy: `inspection_level="S-3"` lanza `ValueError`).
- [ ] Test de S016-RF-02 (la tabla II-A completa; falla solo si hay celdas distintas: se anota el resultado).
- [ ] Test de S016-RF-03 (falla hoy: no existe `sampling="double"`).
- [ ] Test de S016-RF-04 (falla hoy: `N = 10` da `n = 1250`).
- [ ] Test de S016-RF-05 (falla hoy: no existe la curva ASN).

## Fase 1 — Implementación

- [ ] S016-RF-01: tabla I con S-1 a S-4.
- [ ] S016-RF-02: corregir `_plan_z14` donde difiera de la tabla.
- [ ] S016-RF-03: tabla III-A y `DoublePlanAttributes`.
- [ ] S016-RF-04: guarda del 100 % con aviso.
- [ ] S016-RF-05: curvas OC, AOQ y ASN, `to_frame`, `summary` y `plot`.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S016-RF-01 a RF-03).
- [ ] Regenerar `tests/golden/` y revisar el diff línea a línea.
- [ ] Fichas en `BUG_CATALOG.md` (RF-04 y, si procede, RF-02).
- [ ] Documentación, README (es/en), traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
