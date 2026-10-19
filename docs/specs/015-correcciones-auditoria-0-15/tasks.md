# Tareas — 015 Correcciones de la auditoría estadística 0.15

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S015-RF-01 (falla hoy: sigma del EWMA-P con `n` variable y falsa alarma 0,152).
- [x] Test de S015-RF-02 (falla hoy: plan n=45, c=0 y ATI con `Pa`; AOQL de la rejilla).
- [x] Test de S015-RF-03 (falla hoy: 38 % de rechazos con empates).
- [x] Test de S015-RF-04 (falla hoy: `has_trend` False con deriva de 24σ).
- [x] Test de S015-RF-05 (falla hoy: tasa de rechazo 0,13 % del kappa).
- [x] Test de S015-RF-06 (falla hoy: sigma 0,3012 frente a 0,1897).
- [x] Test de S015-RF-07 (falla hoy: 0,9527 frente a 0,6077).
- [x] Test de S015-RF-08 (falla hoy: sigma 0,447 en el último subgrupo).
- [x] Test de S015-RF-09 (falla hoy: `ValueError` en `phase2`).
- [x] Test de S015-RF-10 (falla hoy: `tolerance` sin efecto).
- [x] Test de S015-RF-11 (falla hoy: 84,3 % en lugar de 11,7 %).
- [x] Test de S015-RF-12 (falla hoy: P(|S| > LCS) = 0,0197).
- [x] Test de S015-RF-13 (falla hoy: la prueba 1 con sigma 0, NaN en `precontrol`, `gage_rr` con NaN y LTPD NaN).
- [x] Test de S015-RF-14 (`mssd`, OC bilateral, repetibilidad del acuerdo, IQR).
- [x] Test de S015-RF-15 (secciones del README, comentarios y `wizard` con 3 ≤ n ≤ 7).

## Fase 1 — Implementación

- [ ] Gravedad alta: S015-RF-01 a RF-05.
- [ ] Gravedad media: S015-RF-06 a RF-12.
- [ ] Gravedad baja: S015-RF-13 y RF-14.

## Fase 2 — Verificación y cierre

- [ ] Comprobaciones en `run_validation()` (RF-01, RF-02, RF-03, RF-04, RF-05 y RF-12 si se decide).
- [ ] Fichas en `BUG_CATALOG.md` (un bug por RF de gravedad alta y media) y tests de regresión.
- [ ] Documentación, README (es/en) con la sección de diferencias con Minitab, traducciones y CHANGELOG (S015-RF-15).
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
