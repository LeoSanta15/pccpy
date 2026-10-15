# Tareas — 001 Tolerancia no paramétrica unilateral

Especificación aprobada el 2026-10-15 (sin parámetro de compatibilidad; el cambio se avisa en el CHANGELOG).

## Fase 0 — Tests que fallan

- [x] Test de S001-RF-01: `n = 300`, cota inferior y superior con `r = 9` y confianza 0,96593.
- [x] Test de S001-RF-02: simulación con semilla fija, ±1 punto.
- [x] Test de S001-RF-03: `n = 58` falla y `n = 59` acepta con `r = 1`.

## Fase 1 — Implementación

- [x] S001-RF-01: elegir el mayor `r` que cumple en la rama unilateral de `_nonparam_indices`.
- [x] S001-RF-02: sin cambios de código; lo cubre el test de simulación (pasaba antes y después: es una garantía).
- [x] S001-RF-03: sin cambios de código; lo cubre el test del tamaño mínimo (pasaba antes y después: es una garantía).

## Fase 2 — Verificación y cierre

- [x] Comprobación en `run_validation()` (S001-RF-01, S001-RF-03).
- [x] Regenerar `tests/golden/` y revisar el diff línea a línea.
- [x] Documentación, traducciones y CHANGELOG («Cambios que alteran resultados»).
- [x] `make check` en verde.
- [x] Estado de la especificación → `implementada`.
