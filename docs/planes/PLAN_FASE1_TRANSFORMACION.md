# Plan — `phase_one` con `transform=`

> **Estado:** propuesto el 2026-10-08, pendiente de aprobación. Una rama y un PR por fase; la versión va en un PR de versión aparte.
> **Objetivo:** que `phase_one(chart, data, transform=…)` calcule la Fase I de datos asimétricos y congele la transformación junto con los límites para la Fase II.
> **Fuera de alcance:** cartas de atributos (no usan transformación) y `stages=` (ya no se admite en Fase I).

## Por qué hoy no se admite

`phase_one` repite «calcular la carta → excluir puntos con señal → recalcular». Con `transform=` hay dos decisiones que no son triviales y que hoy evita una guarda en `src/pccpy/phase1.py`:

1. **Cuándo se ajusta la transformación.** Reajustarla en cada pasada hace que λ (o los parámetros de Johnson) cambien al quitar puntos; ajustarla una sola vez deja que los puntos con causa especial, que se van a excluir, influyan en el ajuste.
2. **Qué se congela para la Fase II.** `phase2()` aplica límites congelados (`mu`, `sigma`) a datos nuevos; habría que congelar también la `Transformation` ajustada.

## Decisiones propuestas

| Pregunta | Propuesta |
|---|---|
| Ajuste de la transformación | **En cada pasada**, solo con los puntos conservados (la Fase I estima el proceso bajo control, sin causas especiales) |
| Qué se congela | La `Transformation` de la última pasada, junto con `mu` y `sigma` en la escala transformada |
| Transformación ya ajustada (`transform=<Transformation>`) | Se respeta y **no** se reajusta (el usuario fija los parámetros) |
| Escala de salida | La de la carta: `scale="original"` por defecto, igual que en F4 |
| Historial | `PhaseOneIteration` guarda además el método y los parámetros de cada pasada, para ver cómo se mueve λ |
| Aviso | Si la transformación cambia mucho entre la primera y la última pasada (p. ej. λ varía más de 0,5), avisar: la Fase I no es estable |

## Fases

| Fase | Contenido | Rama |
|---|---|---|
| T1 | Núcleo: aceptar `transform=` en `phase_one` (cartas `imr_chart`, `xbar_r_chart`, `xbar_s_chart`), reajustar por pasada, guardar la transformación en `PhaseOneResult`, quitar la guarda | `feat/fase1-transformacion` |
| T2 | `phase2()` con la transformación congelada (`mu`, `sigma` y `transform=` fija) y escala original; `to_frame()` e historial con los parámetros | `feat/fase1-transformacion-fase2` |
| T3 | Validación (`run_validation()`), tests, documentación es/en (guía «datos asimétricos», `phase_one`), traducciones y CHANGELOG | `feat/fase1-transformacion-docs` |

## Puntos a comprobar en T1/T2

- Que las cartas admitan `mu=`/`sigma=` junto con una `Transformation` fija (límites asimétricos y zonas en escala original); si no, completar ese soporte en `charts/variables.py` antes.
- Que `sigma` congelado sea el de la escala transformada (no el original) y que `phase2()` lo documente.
- Datos con ceros o negativos y `transform="boxcox"`: la guarda de Box-Cox debe fallar con un mensaje claro desde la primera pasada, y una pasada posterior no puede introducir el fallo (los conservados son un subconjunto).
- Pasadas con pocos puntos: `MIN_OBSERVACIONES = 8` de `fit_transformation`; `min_points` ya impide bajar de 20 por defecto, pero con `min_points < 8` hay que fallar con un mensaje claro.
- Johnson es la más frágil: si el ajuste falla en una pasada intermedia, conservar la anterior y avisar, o detener con `reason="transform_failed"`.

## Validación

- Datos lognormales y Weibull con 2 puntos contaminados: la Fase I con transformación recupera los puntos contaminados y la tasa de falsas señales de la Fase II queda cerca de la nominal (simulación con semilla fija).
- Equivalencia: `phase_one(transform=t)` con `t` fija es igual a `phase_one` sobre `t.forward(datos)` en la escala transformada.
- Con datos normales y `transform=`, no excluye más puntos que sin transformar (tolerancia de simulación).

## Riesgos

- Reajustar por pasada puede oscilar con muestras pequeñas: por eso el aviso de estabilidad y la opción de pasar una `Transformation` fija.
- El coste de Johnson (tres ajustes por pasada) con hasta 10 pasadas; aceptable con los tamaños habituales, a medir en T1.
