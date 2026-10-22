# Tareas — 019 Kappa unilateral y EV del Xbar-R con `d2`

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S019-RF-01: `κ`/`p` = `nan` con `pₑ = 1` en Cohen y en Fleiss, y en `attribute_agreement` (summary, `to_frame`, `to_excel` sin lanzar); guarda: `pₑ < 1` no cambia (pasa antes del código).
- [x] Test de S019-RF-02: `p` unilateral contra `norm.sf` con el `SE₀` de `statsmodels` (`std_kappa0`), `κ < 0` → `p > 0,5` y tasa de rechazo bajo H₀ (20 semillas × 300).
- [x] Test de S019-RF-03: `K1` de 10 × 3 con 2 y 3 ensayos contra `1/d2(r)` calculado aparte; 3 × 2 conserva `d2*`; `K2`, `K3` sin cambios (guarda).

## Fase 1 — Implementación

- [ ] Actualizar los tests antiguos que fijan el comportamiento anterior: `test_s015_rf05_*` (p-valor bilateral) en `tests/test_auditoria_015.py` y `test_gage_rr_xbar_r_sigue_aiag` (EV con `d2*` y 30 combinaciones) en `tests/test_auditoria_regresion.py`.
- [ ] S019-RF-01: kappa indefinido.
- [ ] S019-RF-02: p-valor unilateral.
- [ ] S019-RF-03: EV con `d2` (opción C).

## Fase 2 — Verificación y cierre

- [ ] Comprobaciones `kappa-unilateral` y `k1-xbar-r` en `run_validation()` (S019-RF-01, S019-RF-02 y S019-RF-03).
- [ ] Regenerar `tests/golden/` (kappa y Gage R&R Xbar-R) y revisar el diff línea a línea.
- [ ] Documentación, README (es/en, nota de Minitab), traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
