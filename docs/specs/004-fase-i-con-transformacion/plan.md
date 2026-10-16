# Plan — 004 Fase I con transformación y ajuste robusto

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (principios 1, 3, 4 y 5).
- **Plan original:** docs/planes/PLAN_FASE1_TRANSFORMACION.md (fases T1, T2 y T3)

> Plan retroactivo: resume el diseño que quedó en el código, no un diseño previo.

## Diseño

`phase_one` (`src/pccpy/phase_one.py`) llama a `fit_transformation` (`src/pccpy/transformations.py`) en cada pasada con los puntos que se conservan y congela la última. El recorte robusto usa el medcouple y el diagrama de cajas ajustado.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Reajustar en cada pasada | Ajustar una sola vez con todos los datos | Un atípico no debe influir en el ajuste, y se disimula si se usa |
| Recorte robusto por defecto | Opt-in | Sin él el atípico muy grande se disimulaba (12 % frente a 100 %); `robust_fit=False` lo recupera |
| Parámetros `mu`/`sigma` en la escala transformada | Guardarlos en la original | Los límites simétricos viven en la escala transformada |

## Validación independiente

Comprobaciones de `run_validation()`: «Fase I con transformación Box-Cox» (cálculo manual con `scipy.stats.boxcox`) y «Fase I con ajuste robusto» (medcouple y diagrama de cajas escritos con bucles).

## Riesgos

Una Fase I inestable (lambda que cambia mucho) se avisa; un ajuste imposible detiene la Fase I en lugar de seguir con datos erróneos.

## Documentación y traducciones

Guía «Datos asimétricos y no normales», inicio rápido, README (es/en), catálogos `.po`.
