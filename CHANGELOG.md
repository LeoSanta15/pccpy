# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).
spyc usa versionado semántico mientras esté en desarrollo (0.x): un incremento en
el segundo número puede incluir cambios que no son compatibles hacia atrás.

## [0.4.3] - contexto para Claude Code

### Añadido
- `CLAUDE.md`: contexto de arranque para continuar el desarrollo desde Claude
  Code (reglas de trabajo, mapa del código, cómo verificar cambios, pendientes
  conocidos y pasos para subir el repositorio a GitHub).

### Corregido
- Faltaba la etiqueta de git `v0.1.0` en el primer commit; se agregó.

## [0.4.2] - documentación con Sphinx

### Añadido
- Documentación en `docs/`, construida con Sphinx (tema `sphinx-rtd-theme`,
  `napoleon` para los docstrings estilo NumPy, `myst-parser` para las páginas en
  Markdown): portada, instalación, inicio rápido, una página de referencia por
  grupo de cartas (generada con `autofunction`/`autoclass` a partir del código,
  no copiada a mano) y el changelog embebido.
- `docs = [...]` en `pyproject.toml` con las dependencias para construirla.
- `.readthedocs.yaml`, listo para conectar el repositorio en readthedocs.org una
  vez esté en GitHub.
- Job `documentacion` en el CI: construye la documentación con `-W` (cualquier
  advertencia de Sphinx hace fallar el build).

### Corregido
- Docstring de `generalized_variance_chart` (usaba `|S|` sin escapar, que RST
  interpreta como una referencia de sustitución y rompía la documentación).

## [0.4.1] - herramientas de calidad y changelog

### Añadido
- `CHANGELOG.md` (este archivo).
- `ruff` y `mypy` como dependencias de desarrollo, con configuración en
  `pyproject.toml`, y un job de "calidad" en el workflow de CI que los ejecuta.
- `pytest-cov` como dependencia de desarrollo; el CI ahora corre las pruebas con
  reporte de cobertura (97% de líneas al momento de esta versión).

### Corregido
- Import sin usar en `multivariate.py`.
- Varias anotaciones de tipo incompletas señaladas por mypy (`run_sigma` en
  `zmr_chart`, `tests_at` en el graficador); sin cambios de comportamiento.
- `MultivariateChart.contributions()` ahora valida explícitamente que la media y
  la covarianza de la etapa existan antes de usarlas, en vez de fallar más abajo
  con un error de numpy menos claro.

## [0.4.0] - etapas y Box-Cox en cartas multivariadas

### Añadido
- `stages` en `t2_chart`, `generalized_variance_chart`, `mewma_chart` y
  `mcusum_chart`: sin parámetros históricos, cada etapa reestima su media y
  covarianza; con parámetros históricos se usan los mismos en todas. MEWMA y
  MCUSUM reinician su acumulador al empezar cada etapa.
- `boxcox` en las mismas 4 cartas: transforma cada variable con su propio lambda
  (estimado por máxima verosimilitud) antes de calcular la carta.
- `MultivariateChart.stage_mean`, `.stage_cov`, `.stage_scale`: para que
  `contributions()` use la media/covarianza de la etapa del punto consultado.

## [0.3.0] - carta de zona y MCUSUM

### Añadido
- `zone_chart`: carta de zona (Davis, Homer y Woodall, 1990), puntaje acumulado
  con pesos 0-2-4-8 en vez de las pruebas de causas especiales.
- `mcusum_chart` y `mcusum_limit`: CUSUM multivariada de Crosier (1988), con el
  límite calculado por ARL mediante una cadena de Markov.

## [0.2.0] - cartas avanzadas y multivariadas

### Añadido
- Univariadas: `ma_chart` (media móvil), `zmr_chart` (Z-MR, corridas cortas),
  `imr_rs_chart` (I-MR-R/S, variación entre/dentro), `g_chart` y `t_chart`
  (eventos raros).
- Multivariadas: `t2_chart` (T² de Hotelling, Fase I/II, con
  `.contributions()`), `generalized_variance_chart` (|S|), `mewma_chart` y
  `mewma_limit` (límite por ARL vía cadena de Markov).

## [0.1.0] - primera versión

### Añadido
- Cartas de variables: I-MR, Xbar-R, Xbar-S.
- Cartas de atributos: P, NP, C, U, Laney P′, Laney U′.
- Cartas de tiempo ponderado: EWMA, CUSUM.
- Las 8 pruebas de causas especiales de Minitab, con parámetros ajustables.
- Capacidad del proceso: normal, no normal (9 distribuciones) y Box-Cox;
  `capability_sixpack`.
- `normality_test` (Anderson-Darling, Shapiro, D'Agostino), `probability_plot`.
- `pareto` / `plot_pareto`.
- Constantes SPC (`d2`, `d3`, `c4`, `c5`, `control_chart_constants`) calculadas
  por integración numérica para cualquier n ≥ 2, no solo tablas finitas.
