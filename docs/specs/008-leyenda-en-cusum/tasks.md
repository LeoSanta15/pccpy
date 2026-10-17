# Tareas — 008 Leyenda de las dos sumas en el gráfico de la CUSUM

Orden de ejecución. Cada tarea cita los requisitos que cubre. Los tests de una fase se escriben antes que su código y
deben fallar por el motivo esperado.

## Fase 0 — Tests que fallan

- [x] Test de S008-RF-01 (falla hoy: el panel de la CUSUM no tiene leyenda); incluye la guarda de las cartas sin segunda serie.
- [x] Test de S008-RF-02 (guarda: pasa antes y después; compara datos y `rcParams`).
- [x] Test de S008-RF-03 (falla hoy: no hay texto que traducir).
- [x] Test de S008-RF-04 (falla hoy: `plot` no acepta `legend`); incluye la guarda de las cartas sin segunda serie.

## Fase 1 — Implementación

- [x] S008-RF-01: etiquetas y `ax.legend()` en `_draw_panel`.
- [x] S008-RF-03: textos con `tr()` y traducción al inglés.
- [x] S008-RF-04: parámetro `legend` en `plot_control_chart`, docstring y catálogo de la documentación.

## Fase 2 — Verificación y cierre

- [x] Revisar a ojo un gráfico real (CUSUM con y sin señales, con etapas).
- [x] CHANGELOG y catálogos.
- [x] `make check` en verde.
- [x] Estado de la especificación → `implementada`.
