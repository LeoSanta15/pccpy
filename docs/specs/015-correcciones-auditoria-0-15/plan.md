# Plan — 015 Correcciones de la auditoría estadística 0.15

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: cambia resultados existentes (principio 3, «lo existente no cambia sin avisar»). Se avisa en «Cambios que alteran resultados» del CHANGELOG, con el valor antiguo y el nuevo de cada caso, y se publica como 0.16.0 (versión menor).

## Diseño

Cada corrección es local y sigue a su vecino; no se reescribe ningún módulo.

| RF | Dónde | Cambio |
|---|---|---|
| 01 | `charts/timeweighted_attr.py` | La sigma del EWMA de P/U pasa a la recursión `Vᵢ = (1−λ)²Vᵢ₋₁ + λ²σ²(nᵢ)` (vectorizada con `np.frompyfunc` o bucle; los tamaños son pequeños). Con `n` constante coincide con la fórmula cerrada. |
| 02 | `acceptance.py` (`_dodge_romig_ltpd`, `_dodge_romig_aoql`, rejilla del AOQL) | ATI con `(1−Pa)`; AOQL por máximo exacto (optimizador acotado sobre `p`, p. ej. `scipy.optimize.minimize_scalar` sobre `−AOQ(p)` con rejilla gruesa de arranque); sin tolerancia del 5 %; la búsqueda del LTPD parte de un punto que garantice un cruce. |
| 03 | `charts/run_chart.py` (`_runs_updown`) | `n_eff = m + 1` (puntos tras quitar diferencias nulas) en `E` y `V`. |
| 04 | `_diagnose.py`, `_wizard.py` | Una función común `_tendencia_mk(x)` con `scipy.stats.kendalltau` (en `_diagnose.py`, usada por `_wizard.py`); la regla de `trend_direction` pasa a `'increasing'`/`'decreasing'` según el signo de τ cuando `p < 0,05`; mínimo de observaciones. |
| 05 | `msa.py` (`_cohen_kappa`) | `se₀` de Fleiss, Cohen y Everitt (1969). |
| 06, 07 | `capability.py` | `capability_boxcox` usa `to_subgroups` antes de transformar; la sigma de individuales se calcula con la misma ruta que `imr_chart` (`sigma_individuals` sobre la serie con huecos). |
| 08 | `charts/timeweighted.py` (`_series_etapas`) | La sigma de cada punto usa su `nᵢ`. |
| 09 | `phase1.py` | `phase2()` y `from_limits` no reenvían `center` cuando hay `mu` congelado. |
| 10, 11 | `msa.py` | `%Tolerancia`; %Linealidad y %Sesgo con la definición de AIAG y un parámetro de variación del proceso. |
| 12 | `multivariate.py` (`generalized_variance_chart`) | Según la decisión: percentiles por simulación con semilla fija o aviso en docstring/README/`summary()`. |
| 13 | `rules.py`, `precontrol.py`, `msa.py`, `acceptance.py` | `z = ±inf` cuenta como válido para la prueba 1; `as_1d`; validaciones. |
| 14, 15 | varios + README/docs | Documentación y los ajustes decididos. |

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Una sola especificación, tres fases de implementación (alta, media, baja) | Una especificación por área | Un único cambio de versión 0.16.0 y una sola lista de «Cambios que alteran resultados»; pendiente de confirmar |
| Mann-Kendall en `diagnose`/`wizard` | Parchear los umbrales 80/20 | La regla de umbrales no tiene potencia con n grande ni controla las falsas alarmas con n pequeño |
| Dodge-Romig por búsqueda exhaustiva en lugar de la tabla de Dodge y Romig | Reproducir las tablas publicadas | No se tienen las tablas; la búsqueda con la definición exacta es contrastable |
| Sin alias ni parámetros nuevos salvo los que decida la persona responsable | Opciones para el comportamiento antiguo | Los comportamientos antiguos son errores, no una opción |

## Validación independiente

`run_validation()` suma comprobaciones con referencia escrita aparte: EWMA-P con `n` variable (recursión), Dodge-Romig (búsqueda exhaustiva con `scipy.stats.binom`), carta de corridas con empates (Monte Carlo, 20 semillas),
kappa (`statsmodels.cohens_kappa().std_kappa0`), tendencia (`scipy.stats.kendalltau`, potencia y tamaño por Monte Carlo) y, si se decide, |S|. Los tests de regresión de cada hallazgo usan las reproducciones de la auditoría (valor obtenido y esperado que constan en la especificación).

## Riesgos

- Los planes de Dodge-Romig y las recomendaciones de `diagnose`/`wizard` cambian de forma visible: se avisa en el CHANGELOG con ejemplos.
- La búsqueda exhaustiva de Dodge-Romig puede ser lenta con N grande: se acota y se mide.
- La simulación de límites de |S| (si se elige) debe ser determinista (semilla fija) y rápida; si no, se cae al aviso.
- Los goldens (`tests/golden/`) pueden cambiar en `diagnose`/`wizard` (tendencia): se actualizan solo las celdas afectadas y se justifican.

## Documentación y traducciones

CHANGELOG («Cambios que alteran resultados» y «Corregido», con las fichas de `BUG_CATALOG.md`), README (es/en) con la sección de diferencias con Minitab, `docs/source` (guías de ARL, MSA, muestreo y diagnose), docstrings, catálogos `.po` y `docs/locales/en`.
