# Tareas — 012 Claves en inglés en los resultados de las cartas

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S012-RF-01 (falla hoy: `params[0]` tiene `media`, no `mean`).
- [ ] Test de S012-RF-02 (alias con `DeprecationWarning`; las claves en español no salen en `keys()`).
- [ ] Test de S012-RF-03 (archivo de Fase I de 0.15.x se lee; el nuevo escribe el esquema nuevo).
- [ ] Test de S012-RF-04 (carta de zona: `kind`, paneles y alias).
- [ ] Test de S012-RF-05 (la suite sin avisos de las claves antiguas; `grep` de `src/`).
- [ ] Test de S012-RF-06 (README y guías sin las claves antiguas).

## Fase 1 — Implementación

- [ ] S012-RF-01 y RF-02: tabla de equivalencias y diccionario con alias.
- [ ] S012-RF-01: claves en inglés en cada carta (variables, atributos, tiempo ponderado, avanzadas, multivariadas).
- [ ] S012-RF-03: Fase I (lectura de ambos esquemas, escritura del nuevo).
- [ ] S012-RF-04: carta de zona.
- [ ] S012-RF-05: lecturas internas de `params`.

## Fase 2 — Verificación y cierre

- [ ] Documentación, README, guías, ejemplos, traducciones y CHANGELOG (S012-RF-06).
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
