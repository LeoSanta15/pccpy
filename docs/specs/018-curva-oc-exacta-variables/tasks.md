# Tareas — 018 Curva OC exacta de los planes por variables

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Integral numérica independiente (`quad` sobre la densidad de `s`) como referencia en `tests/` (S018-RF-01).
- [ ] Test de S018-RF-01 contra la integral y la simulación con ≥ 20 semillas (falla hoy: la aproximación normal difiere hasta 0,02).
- [ ] Test de S018-RF-02: `alpha` y `ltpd` del plan de `N=1000, aql=1,0`; `ltpd = nan` si `Pa(AQL) < 0,10`; `oc_curve` monótona.
- [ ] Test de S018-RF-03: extremos (`p` = 0, 1, 1e-12; `n` = 2 y 2 000; `k` ≤ 0) sin avisos (varios pasan hoy; el de `n = 2` y el valor exacto fallan).
- [ ] Test de S018-RF-04 (la OC bilateral: pasa antes del código porque protege lo que no cambia).

## Fase 1 — Implementación

- [ ] S018-RF-01: `_pa_variables` unilateral con `nct.sf` y docstrings.
- [ ] S018-RF-02: verificar `alpha` y `ltpd` (sin cambio de código).
- [ ] S018-RF-03: extremos sin avisos.
- [ ] S018-RF-04: verificar que la rama bilateral no cambió.

## Fase 2 — Verificación y cierre

- [ ] Comprobación `variables-oc-exacta` en `run_validation()` (S018-RF-01 y S018-RF-02).
- [ ] Regenerar `tests/golden/` (solo `oc_variables`, `muestreo_variables`) y revisar el diff línea a línea.
- [ ] Documentación, README (es/en), traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
