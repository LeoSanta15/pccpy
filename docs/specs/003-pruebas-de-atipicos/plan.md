# Plan — 003 Pruebas formales de atípicos (Grubbs, ESD y Dixon)

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (principios 1, 3, 4 y 5).
- **Plan original:** docs/planes/PLAN_NO_NORMALIDAD.md

> Plan retroactivo: resume el diseño que quedó en el código, no un diseño previo.

## Diseño

`src/pccpy/outliers.py` con `outlier_test()` y `OutlierTestResult` (índices, valores, `to_frame(stable=)`, `summary()`, `ratio` para Dixon). Grubbs y ESD usan los cuantiles t de `scipy.stats`; Dixon calcula el crítico por cuadratura.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Calcular los críticos de Dixon | Tabular los valores publicados | No se tenía acceso a la fuente; el cálculo es verificable |
| Bilateral de Dixon con `α/2` por cola | Ajuste exacto de la cola doble | Conservador y simple de explicar |
| No eliminar datos | Devolver los datos limpios | Eliminar atípicos es una decisión de proceso, no estadística |

## Validación independiente

Comprobaciones de `run_validation()`: «Pruebas de atípicos (Grubbs y ESD generalizada)» (tabla de Grubbs y ejemplo de Rosner) y «Prueba de Dixon (valores críticos calculados)» (tabla de r10).

## Riesgos

Que alguien use la prueba como regla de descarte (la guía lo desaconseja) y la dependencia de la normalidad (el aviso de Shapiro-Wilk).

## Documentación y traducciones

Guía «Datos asimétricos y no normales», README (es/en), catálogos `.po`.
