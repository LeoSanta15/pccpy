# Tareas — 008 Leyenda de las dos sumas en el gráfico de la CUSUM

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [ ] Test de S008-RF-01 (falla hoy: el panel de la CUSUM no tiene leyenda); incluye la guarda de las cartas sin segunda serie.
- [ ] Test de S008-RF-02 (guarda: pasa antes y después; compara datos y `rcParams`).
- [ ] Test de S008-RF-03 (falla hoy: no hay texto que traducir).

## Fase 1 — Implementación

- [ ] S008-RF-01: etiquetas y `ax.legend()` en `_draw_panel`.
- [ ] S008-RF-03: textos con `tr()` y traducción al inglés.

## Fase 2 — Verificación y cierre

- [ ] Revisar a ojo un gráfico real (CUSUM con y sin señales, con etapas).
- [ ] CHANGELOG y catálogos.
- [ ] `make check` en verde.
- [ ] Estado de la especificación → `implementada`.
