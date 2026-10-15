# Tareas — 001 Tolerancia no paramétrica unilateral

Pendiente de aprobación de la especificación (hay una pregunta abierta).

## Fase 0 — Tests que fallan

- [ ] Test de S001-RF-01: `n = 300`, cota inferior y superior con `r = 9` y confianza 0,96593.
- [ ] Test de S001-RF-02: simulación con semilla fija, ±1 punto.
- [ ] Test de S001-RF-03: `n = 58` falla y `n = 59` acepta con `r = 1`.

## Fase 1 — Implementación

- [ ] S001-RF-01: elegir el mayor `r` que cumple en la rama unilateral de `_nonparam_indices`.
- [ ] S001-RF-02: sin cambios de código; lo cubre el test de simulación.
- [ ] S001-RF-03: sin cambios de código; lo cubre el test del tamaño mínimo.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S001-RF-01, S001-RF-03).
- [ ] Regenerar `tests/golden/` y revisar el diff línea a línea.
- [ ] Documentación, traducciones y CHANGELOG («Cambios que alteran resultados»).
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
