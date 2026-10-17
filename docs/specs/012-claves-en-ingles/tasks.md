# Tareas — 012 Claves en inglés en los resultados de las cartas

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S012-RF-01 (falla hoy: `params[0]` tiene `media`, no `mean`; iguales en `es` y `en`).
- [ ] Test de S012-RF-02 (`KeyError` con las claves españolas; ninguna carta tiene claves en español).
- [ ] Test de S012-RF-03 (carta de zona: `kind`, paneles y `KeyError` con los nombres viejos).
- [ ] Test de S012-RF-04 (`summary()` en español idéntico al golden; `mean=`/`size=` en inglés).
- [ ] Test de S012-RF-05 (la suite y el `grep` de `src/`).
- [ ] Test de S012-RF-06 (un archivo de Fase I escrito con 0.15.5 se lee y da los mismos límites; el nuevo lleva `schema_version` mayor).
- [ ] Test de S012-RF-07 (README, guías y ejemplos sin las claves antiguas).

## Fase 1 — Implementación

- [ ] S012-RF-01: tabla de equivalencias y claves en inglés en cada carta (variables, atributos, tiempo ponderado, avanzadas,
  multivariadas).
- [ ] S012-RF-04: `summary()` traduce desde las claves canónicas.
- [ ] S012-RF-03: carta de zona.
- [ ] S012-RF-05: lecturas internas de `params`.
- [ ] S012-RF-06: Fase I (lectura de los archivos antiguos y escritura del esquema nuevo).

## Fase 2 — Verificación y cierre

- [ ] Documentación, README, guías, ejemplos, traducciones y CHANGELOG (S012-RF-07).
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
