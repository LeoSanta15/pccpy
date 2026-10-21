# Plan — 017 Planes por variables: MIL-STD-414

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: cambia resultados existentes (principio 3), porque los actuales no reproducen ninguna norma; se avisa en «Cambios que alteran resultados».

## Diseño

| RF | Dónde | Cambio |
|---|---|---|
| 01 | `acceptance.py` | Tabla A-2 de MIL-STD-414 (`_TABLA_A2_414`) y `_letra_codigo_414(N, nivel)`; se quita el desplazamiento ±2 y el uso de la tabla I de Z1.4 |
| 02 | `acceptance.py` | `_Z19_TABLE` se sustituye por `_TABLA_B1_414` (todas las letras y AQL, con las flechas como `↓`) y `_plan_414(letra, aql, inspeccion)`; sin aviso de aproximación |
| 03 | `acceptance.py` | Parámetro `inspection` (`"normal"`/`"tightened"`) con la columna desplazada |
| 04 | `acceptance.py` | `SamplingPlanVariables.evaluate` conserva la Forma 1 |
| 05 | `acceptance.py` | Guarda del 100 % igual que Z1.4 |
| 06 | `acceptance.py` | Parámetro `standard`; `"z1.9"` lanza `ValueError`; `method="mil-std-414"` en el resultado |

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Implementar MIL-STD-414 con nombre propio | Llamarlo Z1.9 | Las tablas son de MIL-STD-414; Z1.9 difiere en la A-2 y no se verificó que los `k` coincidan |
| `standard="z1.9"` lanza `ValueError` | Alias de 414 con aviso | Honesto: no hay tablas de Z1.9 |
| Transcribir las tablas de las capturas con tests aparte que la persona responsable revisa celda a celda | Reglas por diagonales | Las flechas de B-1 son explícitas; no hay fórmula simple |
| La rigurosa sale de la misma B-1 desplazando una columna | Tabla aparte | Es lo que indica la propia tabla |

## Validación independiente

Comprobación nueva en `run_validation()` (`variables-414`): letra de código y `(n, k)` de una malla de lotes, niveles y AQL contra las tablas transcritas aparte (y la rigurosa por el desplazamiento), y la coherencia
estructural de B-1 (`k` decrece al subir el AQL y crece con `n`).

## Riesgos

- **Transcripción de las tablas:** una celda mal leída no la detectaría ningún test que parta de la misma lectura; la revisión celda a celda por la persona responsable cubre ese riesgo (dos celdas ya corregidas).
- **Cambia resultados** de todos los planes por tabla; se regeneran y se revisan los golden `tests/golden/` línea a línea.
- **Confusión con Z1.9:** la documentación, el docstring y el README dicen «MIL-STD-414» y explican que no es Z1.9.

## Documentación y traducciones

`docs/source/acceptance.md` (la sección «Por variables — Z1.9» pasa a MIL-STD-414), README (es/en) y su nota de Minitab, docstrings, CHANGELOG, `make i18n-update` y `make docs-update` con los catálogos `.po`;
se actualiza la deuda técnica de `CLAUDE.md` (Z1.9 sigue pendiente de sus tablas).
