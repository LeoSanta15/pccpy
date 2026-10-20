# Plan — 017 Z1.9: planes de muestreo por variables con las tablas de la norma

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: cambia resultados existentes (principio 3), porque los actuales no reproducen la norma; se avisa en
  «Cambios que alteran resultados». **No empieza hasta tener las tablas.**

## Diseño

| RF | Dónde | Cambio |
|---|---|---|
| 01 | `acceptance.py` | Tabla A-2 de Z1.9 (`_TABLA_A2`) y `_letra_codigo_z19(N, nivel)`; se quita el desplazamiento ±2 y el uso de la tabla I de Z1.4 |
| 02 | `acceptance.py` | `_Z19_TABLE` se sustituye por la tabla B-1 completa (todas las letras y AQL), con la resolución de flechas como en Z1.4 (`_plan_z19`); desaparece el aviso de aproximación para la tabla de la norma |
| 03 | `acceptance.py` | `SamplingPlanVariables.evaluate` conserva la Forma 1; test con la fórmula de la norma |
| 04 | `acceptance.py` | Guarda del 100 % igual que Z1.4 |
| 05 | `acceptance.py` | `_pa_variables` unilateral con `scipy.stats.nct`; el bilateral queda como está (integral exacta con proceso centrado) |
| 06, 07 | por decidir | Según las tablas que se aporten |

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| No programar nada sin las tablas | Reconstruirlas de memoria | La norma no se puede verificar; la tabla anterior (aproximada) ya falló una vez |
| Transcribir de capturas con tests que repiten la transcripción por separado, y la persona responsable las revisa celda a celda | Reproducirlas con una fórmula | Las tablas de Z1.9 no se derivan de una fórmula cerrada simple; Z1.4 se hizo así |
| Estimación de `p̂` de la Forma 2 por la beta (fórmula de la norma) y `M` de la tabla | Tabular `p̂` | `p̂` sale exacta con `scipy.stats.beta`; `M` sí necesita la tabla |

## Validación independiente

Comprobación nueva en `run_validation()` (`z19-tablas`): letra de código y `(n, k)` de una malla de lotes y AQL contra las tablas transcritas aparte, y `pa(p)` unilateral
contra `scipy.stats.nct` (tolerancia 1e-9) y una simulación de semilla fija.

## Riesgos

- **Transcripción de las tablas:** una celda mal leída no la detectaría ningún test que parta de la misma lectura. Mitigación: revisión celda a celda por la persona
  responsable antes de la Fase 1 y tests de coherencia estructural (k decrece al subir el AQL, `n` crece con la letra).
- **Cambia resultados** de todos los planes por tabla y, con RF-05, de todos los unilaterales; se regeneran y se revisan los golden `tests/golden/` línea a línea.

## Documentación y traducciones

`docs/source/acceptance.md`, README (es/en) con la sección y la nota de Minitab, docstrings, CHANGELOG, `make i18n-update` y `make docs-update` con los catálogos `.po`; se actualiza la deuda técnica
de `CLAUDE.md`.
