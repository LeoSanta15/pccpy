# Plan por fases — datos asimétricos (incertidumbre y transformaciones)

> **Estado:** aprobado el 2026-10-08; las siete fases están en revisión, **una rama y un PR por fase** (los PR se apilan). Falta el PR de versión 0.13.0.
> **Objetivo:** que `pccpy` dé intervalos de confianza fiables cuando los datos no son normales y ofrezca más caminos que Box-Cox.
> **Fuera de alcance:** comparaciones con Minitab; cualquier valor que dependa de una norma que no se pueda consultar.

## Decisiones aprobadas

| Pregunta | Decisión |
|---|---|
| Bootstrap por defecto | **Opt-in**: nada cambia si no se pide (`ci_method="bootstrap"`) |
| Forma de la API | **Parámetro** en las funciones existentes (`ci_method=`, `transform=`), sin multiplicar funciones |
| Familia de Johnson | **Incluida** (SU, SB, SL con selección automática) |
| Cartas con transformación | Se dibuja en la **escala original** por defecto, con parámetro para elegir la escala |

## Principios

- Los resultados actuales no cambian (goldens y tests existentes intactos).
- Todo lo aleatorio recibe `seed=` y es reproducible.
- Cada fase se valida con referencias independientes (`scipy.stats.bootstrap`, simulaciones de cobertura con datos lognormales y Weibull) y suma comprobaciones a `run_validation()`.
- Textos con `tr()` y traducción al inglés; documentación en es/en.

## Seguimiento por fases

| Fase | Contenido | Rama | PR | Estado |
|---|---|---|---|---|
| F1 | Núcleo de bootstrap (`bootstrap_ci`, percentil y BCa) | `feat/bootstrap-nucleo` | _(ver PR de la rama)_ | en revisión |
| F2 | Intervalos de capacidad por bootstrap (`capability_analysis`, `capability_boxcox`, `capability_nonnormal`) | `feat/bootstrap-capacidad` | _(ver PR de la rama)_ | en revisión |
| F5 | `diagnose()` con asimetría, curtosis y positividad; arreglar la condición redundante | `feat/diagnose-asimetria` | _(ver PR de la rama)_ | en revisión |
| F3 | Transformaciones: Yeo-Johnson y familia de Johnson (`transform=` en `capability_analysis`, `fit_transformation`) | `feat/transformaciones` | _(ver PR de la rama)_ | en revisión |
| F4 | `transform=` en cartas de variables (escala original por defecto) | `feat/cartas-transformacion` | _(ver PR de la rama)_ | en revisión |
| F6 | Bootstrap para media, mediana y desviación estándar (`bootstrap_summary`) | `feat/bootstrap-resumen` | _(ver PR de la rama)_ | en revisión |
| F7 | Guía «datos asimétricos», README, `wizard()`, `diagnose` con Yeo-Johnson (la versión 0.13.0 va en un PR de versión aparte) | `feat/guia-asimetricos` | _(ver PR de la rama)_ | en revisión |

Orden de ejecución: F1 → F2 → F5 → F3 → F4 → F6 → F7.

## Detalle

- **F1.** `bootstrap_ci(data, statistic, method="bca"|"percentile", n_boot, confidence, seed)`; la estadística puede devolver un escalar o un vector (varios índices con los mismos remuestreos). BCa con corrección de sesgo y aceleración por jackknife; degrada con aviso si la distribución bootstrap es degenerada.
- **F2.** `ci_method="normal"|"bootstrap"`. En `capability_nonnormal` se re-ajusta la distribución en cada remuestreo (percentil por defecto por coste). Con subgrupos: decidir si se remuestrean observaciones o subgrupos.
- **F3.** Yeo-Johnson admite ceros y negativos (Box-Cox no). Johnson SU/SB/SL con selección automática: la parte más frágil, con tests propios y recortable sin afectar al resto.
- **F4.** Límites calculados en la escala transformada y destransformados para el gráfico; compatible con `phase_one()` y con las etiquetas de fecha.
- **F5.** Recomendar entre Box-Cox, Yeo-Johnson o `capability_nonnormal` (menor AIC); distinguir cola pesada o atípicos de asimetría corregible; comprobar positividad antes de recomendar Box-Cox.

## Riesgos

- Tiempo de cómputo del bootstrap con re-ajuste por máxima verosimilitud: `n_boot` configurable.
- El bootstrap también falla con n muy pequeño: aviso por debajo de un mínimo.
- El ajuste automático de Johnson es frágil.
