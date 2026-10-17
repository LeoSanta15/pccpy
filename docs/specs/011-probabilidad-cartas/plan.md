# Plan — 011 Probabilidad de un valor en las cartas de control

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (método nuevo, principio 3; referencias independientes con `scipy.stats`, principios 1 y 13).

## Diseño

- `charts/_engine.py`: `StagePanel` y `results.Panel` ganan un campo opcional `dist` (familia y parámetros por punto). `build_chart`
  lo concatena por etapas como ya hace con `sigma`. Cada cartero rellena su familia: `variables.py` (normal en I y Xbar; `range`
  con `span` o `n` y `σ` en MR y R; `sd` con `n` y `σ` en S), `attributes.py` (binomial y Poisson), `timeweighted.py` (normal
  con la σ por punto de la EWMA). CUSUM, G, T, Laney, MA, Zona y multivariadas dejan `dist = None`.
- Archivo nuevo `_probabilidad_cartas.py` (o ampliar `_probabilidad.py` de la 010): para cada familia, `cdf`/`sf` en el punto
  (normal con `ndtr`, rango con `studentized_range`, `sd` con `chi2`, discretas con `binom`/`poisson` y la regla estricta).
  Reutiliza el núcleo de la 010 (validación, difusión de arreglos, `between`).
- `results.py`: método `ControlChart.probability(...)` delgado; la transformación usa `chart.transformation.forward`.
- Resultado: según la decisión de la pregunta abierta (reutilizar `ProbabilityResult` o clase propia con `arl`).
- Mensajes con `tr()` (R-17) y traducciones en `pccpy.po`.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Guardar la distribución en el panel (`dist`) | Reconstruirla desde `center`/`sigma` | `n` por punto no está en el panel; reconstruir sería frágil |
| Método de `ControlChart` | Función suelta (`chart_probability`) | Coherencia con la 010 |
| Límites tal como los traza la carta; probabilidad exacta | Aproximación normal en atributos | Es lo que dice la carta; `arl_binomial`/`arl_poisson` hacen lo mismo |
| Sin CUSUM | Cadena de Markov para la marginal | No tiene forma cerrada; es el ARL |

## Validación independiente

`scipy.stats.norm`, `studentized_range`, `chi2`, `binom` y `poisson` escritos en los tests; simulación del rango de `n` normales
(≥ 20 semillas); consistencia `1/probability()` con `arl_*`. Una comprobación en `run_validation()` (63 en total).

## Riesgos

- Tocar `Panel`/`StagePanel` afecta a todas las cartas: la regresión se cubre con la suite y `tests/golden/`. Los resultados
  guardados de la Fase I (`to_dict`/`from_limits`) no deben cambiar de formato: se comprueba.
- Las cartas de atributos con LCI recortado a 0: `below=LCL` da 0, se prueba.
- `studentized_range` es lento con muchos puntos: se evalúa una vez por combinación `(n, σ)` distinta.
- Alcance grande: si crece, se divide en dos entregas (variables, atributos).

## Documentación y traducciones

Docstrings, guía de cartas de control y `arl.md`, README (es/en), CHANGELOG, `validacion.md` y catálogos `.po` (biblioteca y
documentación).
