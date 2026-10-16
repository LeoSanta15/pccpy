# Tareas — 002 Carta T: duraciones iguales a 0

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S002-RF-01 (falla hoy: el mensaje dice «iguales a 0» también para negativos y no cita posiciones).
- [ ] Test de S002-RF-02 (falla hoy: `zeros` no existe).
- [ ] Test de S002-RF-03 (guarda: pasa antes y después).

## Fase 1 — Implementación

- [ ] S002-RF-01: mensajes separados para ceros y negativos, con posiciones.
- [ ] S002-RF-02: parámetro `zeros="error"|"drop"` con aviso.
- [ ] S002-RF-03: comprobar que los datos positivos dan el mismo resultado.

## Fase 2 — Verificación y cierre

- [ ] Comprobación en `run_validation()` (S002-RF-02).
- [ ] Documentación, traducciones y CHANGELOG.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
