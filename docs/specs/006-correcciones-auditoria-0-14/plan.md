# Plan — 006 Correcciones de la auditoría estadística de 0.13.1

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (principios 1, 3, 4 y 5).
- **Plan original:** (no hubo plan; la auditoría produjo la lista de hallazgos)

> Plan retroactivo: resume el diseño que quedó en el código, no un diseño previo.

## Diseño

Correcciones puntuales en `tolerance.py`, `capability.py`, `msa.py`, `_constants.py` (`d2_star`), `rules.py`, `charts/` y `phase_one.py`, cada una con su test en `tests/test_auditoria_regresion.py`.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Subir la versión menor | Parche | Cambian resultados numéricos existentes (principio 3) |
| `alpha_interaction` = 0,25 | Quitar siempre la interacción | Es la práctica de AIAG/Minitab |
| Panel MR solo con la prueba 1 | Dejar todas | La prueba 2 saltaba en el 45 % de las series estables |

## Validación independiente

Cinco comprobaciones nuevas en `run_validation()` (tolerancia no paramétrica, Cpm, sigma con subgrupos desiguales, Gage R&R reducido y constantes K de AIAG).

## Riesgos

Que quien dependía de los resultados anteriores no lo note: por eso se avisó en el CHANGELOG.

## Documentación y traducciones

CHANGELOG (0.14.0), guía de tolerancia, README (es/en), catálogos `.po`.
