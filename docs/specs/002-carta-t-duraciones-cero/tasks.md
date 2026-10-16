# Tareas — 002 Carta T: duraciones iguales a 0

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S002-RF-01 (falla hoy: el mensaje dice «iguales a 0» también para negativos y no cita posiciones).
- [x] Test de S002-RF-02 (falla hoy: `zeros` no existe).
- [x] Test de S002-RF-03 (guarda: pasa antes y después).

## Fase 1 — Implementación

- [x] S002-RF-01: mensajes separados para ceros y negativos, con posiciones.
- [x] S002-RF-02: parámetro `zeros="error"|"drop"` con aviso.
- [x] S002-RF-03: comprobar que los datos positivos dan el mismo resultado.

## Fase 2 — Verificación y cierre

- [x] Comprobación en `run_validation()` (S002-RF-02).
- [x] Documentación, traducciones y CHANGELOG.
- [x] `make check` en verde.
- [x] Estado de la especificación → `implementada`.
