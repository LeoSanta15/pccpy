# Tareas — 012 Claves en inglés en los resultados de las cartas

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S012-RF-01 (falla hoy: `params[0]` tiene `media`, no `mean`; iguales en `es` y `en`).
- [x] Test de S012-RF-02 (`KeyError` con las claves españolas; ninguna carta tiene claves en español).
- [x] Test de S012-RF-03 (carta de zona: `kind`, paneles y `KeyError` con los nombres viejos).
- [x] Test de S012-RF-04 (`summary()` en español idéntico al golden; `mean=`/`size=` en inglés).
- [x] Test de S012-RF-05 (la suite y el `grep` de `src/`).
- [x] Test de S012-RF-06 (los archivos de Fase I escritos con 0.15.4 se leen y dan los mismos límites; el formato guardado no cambia).
- [x] Test de S012-RF-07 (README, guías y ejemplos sin las claves antiguas).

## Fase 1 — Implementación

- [x] S012-RF-01: tabla de equivalencias y claves en inglés en cada carta (variables, atributos, tiempo ponderado, avanzadas,
  multivariadas).
- [x] S012-RF-04: `summary()` traduce desde las claves canónicas.
- [x] S012-RF-03: carta de zona.
- [x] S012-RF-05: lecturas internas de `params`.
- [x] S012-RF-06: Fase I (`phase_one` lee las claves nuevas; el formato guardado no cambia).

## Fase 2 — Verificación y cierre

- [x] Documentación, README, guías, ejemplos, traducciones y CHANGELOG (S012-RF-07).
- [x] `make check` en verde.
- [x] Estado de la especificación → `implementada`.
