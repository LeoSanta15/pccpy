# Registro de cambios

## [Sin publicar] - idioma de los mensajes (fases 0 a 3b de 5)

### Añadido
- Mecanismo de idioma basado en `gettext`: `set_language()`, `get_language()`, `language()` (contexto) y `available_languages()`; variable de entorno `PCCPY_LANG`. El idioma fuente es el español y `en` es el primer idioma adicional.
- Infraestructura de traducción: `make i18n-extract/update/compile/check`, `scripts/i18n_check.py` (catálogos al día, sin textos sin traducir ni marcadores distintos) y catálogos `.mo` empaquetados.
- `babel` en el extra `dev` (solo desarrollo; en ejecución se usa `gettext` de la biblioteca estándar).
- Plan completo en `docs/planes/PLAN_MULTILENGUAJE.md`.

- Fase 1: los **151 mensajes de error y aviso** (134 textos únicos) pasan por `tr()` y tienen traducción al inglés; los 34 f-strings se convierten en plantillas con `.format()`. Tests estáticos (AST) comprueban que todo `raise`/`warnings.warn` usa `tr()`, que los marcadores `{…}` coinciden con los argumentos de `.format()` y que nadie ocupa los nombres `tr`/`N_`; otro test detecta palabras españolas en las traducciones.

- Fase 2: los `summary()` de todos los resultados (14 clases), las cabeceras de `to_frame()` (15 métodos) y de `violations()`, las descripciones de las pruebas de causas especiales y las hojas de `to_excel()` pasan por `tr()` con traducción al inglés (428 → 444 textos).
- `to_frame(stable=True)` y `violations(stable=True)`: claves canónicas en inglés que no cambian con el idioma.
- Referencia en español **sin cambios**: 64 resultados de referencia (generados antes de migrar) coinciden byte a byte; tests de invariantes es/en (mismas líneas y números, sin palabras españolas, columnas alineadas) y de claves estables.

- Fase 3: los **textos de todos los gráficos** (títulos, ejes, leyendas, anotaciones, etiquetas de los paneles de las cartas) y el **asistente `wizard()`** completo (árbol de preguntas, justificaciones, fragmentos de código, modos CLI y widget) pasan por `tr()`/`N_()` con traducción al inglés (444 → 742 textos). Los fragmentos de código de ejemplo se muestran con nombres de variable en inglés.
- Referencia en español **sin cambios**: figuras (textos de cada gráfico del corpus) y asistente (árbol, CLI, resultados, widget) coinciden con las referencias generadas antes de migrar; tests es/en de gráficos y asistente (sin palabras españolas, misma estructura, código de ejemplo válido, marco del CLI con el mismo ancho).

- Fase 3b: `pareto()` (`stable=`; el grupo «Otros» usa el idioma activo), `oc_curve()`/`aoq_curve()` (`stable=`), las tablas ANOVA y de kappa mediante los métodos nuevos `anova_frame()`, `kappa_within_frame()` y `kappa_vs_reference_frame()` (los atributos `anova_table`, `kappa_within` y `kappa_vs_reference` no cambian: siguen en español), y las hojas de `to_excel()` (`KappaVsReferencia` → `KappaVsReference` en inglés). 742 → 767 textos. Español sin cambios (20 tablas de referencia generadas antes de migrar).
- `plot_pareto()` acepta tablas de cualquier idioma o con `stable=True` (usa las columnas por posición).

### Nota
- Quedan por traducir, si se decide: `pareto`, curvas OC/AOQ, tablas ANOVA y `kappa_vs_reference`: fases siguientes. El comportamiento por defecto (español) no cambia.

## [0.10.8] - documentación de referencia completa

### Añadido
- Páginas de referencia API para `diagnose()` / `DiagnoseResult` y `wizard()` / `WizardResult` / `WidgetSession`.
- Nota en la documentación de `capability_analysis()` sobre uso sin límites de especificación (LSL/USL opcionales).

### Corregido
- 18 advertencias de Sphinx tratadas como errores en CI (descripciones duplicadas y referencia cruzada ambigua).

---

## [0.10.7] - compatibilidad con datos reales y dependencias externas

### Añadido
- `_excel_writer(path)`: helper interno centralizado para abrir `pd.ExcelWriter`
  con openpyxl. Todos los métodos `to_excel()` (en `results.py`, `capability.py`,
  `tolerance.py`, `msa.py`, `acceptance.py` y `_diagnose.py`) usan este helper y
  ahora dan el mensaje `pip install pccpy[excel]` si openpyxl no está instalado.

### Mejorado
- `as_1d()`: ya **no** lanza `ValueError` cuando los datos contienen `NaN` o
  `inf`. En su lugar emite un `UserWarning` indicando cuántos valores no finitos
  se encontraron y en qué posiciones, y los excluye del análisis. El error solo
  se lanza si no quedan valores válidos.
- `to_subgroups()`: filtra automáticamente las columnas no numéricas de un
  DataFrame ancho emitiendo un `UserWarning`. Antes, `np.asarray()` fallaba con
  un error de tipo opaco al encontrar texto en el DataFrame.
- `to_subgroups()`: el error `subgroup_size=1` ahora describe la situación y
  apunta explícitamente a `imr_chart()` como alternativa correcta. Parámetro
  interno `_allow_size_1` para el uso legítimo de `zone_chart`.
- `capability_analysis()`: ya no requiere `lsl` o `usl`. Sin límites de
  especificación los índices Cp/Cpk/Pp/Ppk/… se devuelven como `NaN` y
  `summary()` los marca con `*`; los estadísticos descriptivos y las sigmas
  se calculan con normalidad.
- `capability_analysis()`: con datos de variación cero (desviación estándar = 0)
  emite un `UserWarning` y devuelve `NaN` en todos los índices, en vez de lanzar
  `ZeroDivisionError`.
- Todas las funciones `plot_*`, `DiagnoseResult.plot()` y `plot_pareto()` están
  ahora envueltas en `plt.rc_context({})`, aislando los estilos internos de pccpy
  de cambios globales de matplotlib introducidos por seaborn u otras librerías.

### Corregido
- `zone_chart` fallaba internamente con el nuevo error `subgroup_size=1` al
  llamar a `to_subgroups(arr, 1)` para datos individuales. Corregido con el
  parámetro `_allow_size_1=True`.
- `_expected_ppm()`, `_z_bench()` y el cálculo del intervalo de confianza de Ppk
  manejaban incorrectamente el caso `sigma=0`, produciendo `ZeroDivisionError`
  o resultados sin sentido.
- `instalacion.md`: corregidas las referencias al nombre anterior en los comandos de
  desarrollo (`pytest --cov`, `mypy src/...` → `pccpy`).

## [0.10.6] - diagnose(), WidgetSession y docs del wizard

### Añadido
- `diagnose(x, lsl=None, usl=None, target=None)` — diagnóstico rápido de proceso:
  estadísticos básicos, prueba de normalidad, detección de tendencia (Mann-Kendall
  simplificado), valores atípicos (IQR × 1.5), Cp/Cpk estimados y función recomendada.
  `DiagnoseResult` incluye `.summary()` (texto al estilo Minitab) y `.plot()` (histograma
  + gráfico de secuencia con matplotlib).
- `WidgetSession` — objeto retornado por `wizard(mode='widget')`. El atributo `.result`
  es `None` mientras la sesión está abierta y se llena con el `WizardResult` al navegar
  hasta una hoja. Reemplaza la lista mutable anterior; la API es ahora consistente con
  los otros modos.
- Página de documentación `wizard.md` en Sphinx (incluida en el TOC de `index.md`).
- 54 tests nuevos en `tests/test_diagnose.py`; 306 pruebas en total.

### Mejorado
- `wizard(mode='widget')` ahora muestra números de opción en cada botón (`1. …`, `2. …`)
  y breadcrumbs con el texto de la pregunta en lugar del ID del nodo.
- Tipo de retorno de `wizard()` en la firma y docstring alineado con la implementación.

## [0.10.5] - correcciones de CI y bump de versión

### Corregido
- CI `publish.yml`: job `publish-pypi` faltaban `checkout` y `setup-python`;
  la acción `pypa/gh-action-pypi-publish` los requiere en el mismo job.
- CI: todas las acciones actualizadas a v6 (`checkout`, `setup-python`,
  `upload-artifact`, `download-artifact`) para eliminar advertencias de Node 20.
- Bump de versión `0.10.4` → `0.10.5`.

## [0.10.4] - wizard de selección de análisis SPC

### Añadido
- `wizard(x=None, mode='cli'|'auto'|'widget')` — asistente de selección de análisis con tres modos:
  - **`'auto'`**: inspecciona el array de datos (dimensiones, normalidad, tendencia) y
    devuelve automáticamente un `WizardResult` con la función recomendada.
  - **`'cli'`**: menú interactivo de preguntas con opciones numeradas en la terminal.
    El árbol de decisión cubre cartas de control, capacidad, MSA, muestreo de aceptación,
    intervalos de tolerancia, normalidad, Pareto y pre-control.
  - **`'widget'`**: interfaz gráfica para Jupyter con botones de selección (requiere
    `ipywidgets`; degrada automáticamente a `cli` si no está instalado).
- `WizardResult` — objeto retornado con `.function`, `.params`, `.rationale`,
  `.alternatives`, `.snippet()`, `.summary()` y `.run(data)`.
- 32 tests en `tests/test_wizard.py`.

## [0.10.3] - cobertura de tests completa y README actualizado

### Añadido
- 4 nuevos módulos de tests (252 pruebas en total, +66 respecto a v0.10.2):
  - `tests/test_tolerance.py`: intervalos de tolerancia normal, unilateral y no paramétrico,
    y `tolerance_interval_summary`.
  - `tests/test_acceptance.py`: Z1.4, Z1.9 y Dodge-Romig.
  - `tests/test_msa.py`: Crossed Gage R&R (ANOVA y Xbar-R), Nested, Tipo 1,
    `gage_type1_summary`, linealidad y concordancia por atributos.
  - `tests/test_run_precontrol.py`: carta de corridas y pre-control.

### Corregido
- `gage_rr_nested`: `MS_ops` se computaba solo dentro de la rama `crossed`, pero se usaba
  en la rama `nested`, causando `UnboundLocalError`.

### Documentación
- README: secciones completas para carta de corridas y pre-control, EWMA/CUSUM para
  atributos, intervalos de tolerancia, muestreo de aceptación y MSA/Gage R&R.
- `inicio_rapido.md`: ejemplos de `tolerance_interval_summary`, `gage_type1_summary`
  y `capability_analysis_summary`.
- Contador de pruebas actualizado: 186 → 252.

## [0.10.2] - documentación completa de referencia Sphinx

### Documentación
- Referencia Sphinx cubre ahora el 100 % de los símbolos públicos (`__all__`).
  Se agregan `plot_capability`, `plot_control_chart`, `capability_analysis_summary`,
  `tolerance_interval_summary` y `gage_type1_summary` a sus páginas RST.

## [0.10.1] - funciones de entrada por estadísticos resumen y documentación completa

### Añadido
- `tolerance_interval_summary(mean, std, n, ...)`: intervalo de tolerancia
  normal a partir de estadísticos resumen, sin necesidad de datos crudos.
- `gage_type1_summary(mean, std, n, reference, ...)`: estudio Tipo 1 (sesgo,
  Cg, Cgk) a partir de estadísticos resumen.

### Documentación
- Referencia Sphinx ahora cubre el 100 % de los símbolos públicos (`__all__`).
  Se agregan `plot_capability`, `plot_control_chart`, `capability_analysis_summary`,
  `tolerance_interval_summary` y `gage_type1_summary` a sus páginas RST.

## [0.10.0] - MSA / Gage R&R

### Añadido
- `gage_rr`: Crossed Gage R&R completo. Soporta `method='anova'` (con tabla
  ANOVA, prueba de interacción parte×operador y agrupación automática cuando
  p-valor>0.25) y `method='xbar_r'` (método clásico AIAG). Devuelve
  `GageRRResult` con %Contribución, %Variación de estudio, NDC, tabla ANOVA,
  `.summary()`, `.to_frame()` y `.plot()`.
- `gage_rr_nested`: Nested Gage R&R (partes anidadas dentro de operadores),
  solo método ANOVA.
- `gage_type1`: Estudio Tipo 1 (sesgo y repetibilidad de una fuente). Calcula
  sesgo, t-test, Cg y Cgk. Devuelve `Type1Result`.
- `gage_linearity`: Estudio de linealidad y sesgo. Regresión sesgo~referencia,
  Linealidad (|pendiente|×rango), R², p-valor. Devuelve `LinearityResult`.
- `attribute_agreement`: Análisis de concordancia por atributos. Kappa de Cohen
  (dentro del operador y vs referencia) y Kappa de Fleiss. Devuelve
  `AttributeAgreementResult`.
- Funciones de graficación: `plot_gage_rr`, `plot_type1`, `plot_linearity`,
  `plot_attribute_agreement`.

## [0.9.0] - Muestreo de aceptación

### Añadido
- `acceptance_sampling_attributes`: plan de muestreo por atributos según
  ANSI/ASQ Z1.4. Devuelve `SamplingPlanAttributes` con `.pa()`, `.oc_curve()`,
  `.aoq_curve()`, `.summary()`, `.to_frame()` y `.plot()`. Calcula
  automáticamente α, β (0.10), LTPD y AOQL del plan.
- `acceptance_sampling_variables`: plan de muestreo por variables según
  ANSI/ASQ Z1.9 (método k). Devuelve `SamplingPlanVariables` con
  `.evaluate()` para decidir aceptación dado un vector de muestra.
- `dodge_romig`: plan Dodge-Romig por atributos, minimizando el ATI.
  Soporta dos modos: protección al consumidor (`ltpd=`) y calidad media
  de salida máxima (`aoql=`). Devuelve `DodgeRomigPlan`.
- `plot_sampling_attributes`: curva OC + curva AOQ para planes por atributos.
- `plot_sampling_variables`: curva OC para planes por variables.

## [0.8.0] - Intervalos de tolerancia

### Añadido
- `tolerance_interval`: calcula intervalos de tolerancia estadísticos. Con
  `method='normal'` usa la aproximación de Howe (1969) para bilateral y la
  distribución t no central exacta para unilateral. Con
  `method='nonparametric'` usa estadísticos de orden (libre de distribución).
  Soporta `sides='two'`, `'lower'` y `'upper'`.
- `ToleranceResult`: objeto de resultado con `.summary()`, `.to_frame()` y
  `.plot()` (histograma con el intervalo superpuesto).
- `plot_tolerance`: función de graficación disponible también como método
  `.plot()` del resultado.

## [0.7.0] - EWMA y CUSUM para cartas de atributos

### Añadido
- `ewma_p_chart`, `ewma_c_chart`, `ewma_u_chart`: EWMA para las cartas de
  atributos P, C y U. Límites exactos que se ensanchan al inicio de la serie
  usando el factor √(1−(1−λ)^{2i}), igual que el EWMA de variables.
- `cusum_p_chart`, `cusum_c_chart`, `cusum_u_chart`: CUSUM tabular estandarizado
  para atributos. Cada observación se convierte a z-score antes de acumular,
  lo que permite tamaños de muestra variables en P y U. ``h`` y ``k`` en
  unidades de σ (por defecto h=4, k=0.5 como en Minitab).

## [0.6.0] - run chart, pre-control y DPMO en capacidad

### Añadido
- `run_chart`: carta de corridas con las 4 pruebas de aleatoriedad de Minitab
  (agrupamiento, mezclas, tendencias y oscilación; p-valor con aproximación normal
  de Wald-Wolfowitz). Devuelve `RunChartResult` con `.summary()`, `.to_frame()` y
  `.plot()`.
- `precontrol`: análisis de pre-control (semáforo de Shainin). Divide la tolerancia
  en zonas verde/amarillo/rojo y detecta señales (punto rojo, dos amarillas en el
  mismo lado, dos amarillas en lados opuestos). Devuelve `PreControlResult` con
  `.summary()`, `.to_frame()` y `.plot()`.
- `plot_run_chart`, `plot_precontrol`: funciones de graficación disponibles también
  como métodos `.plot()` de los resultados correspondientes.
- `CapabilityResult.dpmo`: propiedad que devuelve el DPMO esperado (= PPM general).
- `CapabilityResult.sigma_level`: propiedad que devuelve el nivel sigma del proceso
  (= Z.bench general). Ambos aparecen ahora en `.to_frame()` y `.summary()`.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).
pccpy usa versionado semántico mientras esté en desarrollo (0.x): un incremento en
el segundo número puede incluir cambios que no son compatibles hacia atrás.

## [0.5.1] - formato largo extendido a todos los gráficos de subgrupos

### Cambiado
- `ewma_chart`, `cusum_chart`, `ma_chart`: aceptan ahora DataFrame largo con
  ``subgroup`` + ``value``, y vector 1-D con ``subgroup_size`` con resto (el
  subgrupo incompleto se grafica pero no entra en la estimación de sigma).
- `imr_rs_chart`, `zone_chart`: ídem.
- `capability_analysis`, `capability_sixpack`: ídem; la sigma dentro se estima
  solo con los subgrupos completos.

## [0.5.0] - entrada de datos en formato largo para cartas Xbar

### Añadido
- `xbar_r_chart` y `xbar_s_chart` aceptan tres formatos de entrada:
  1. **Matriz 2-D** (una fila por subgrupo) — comportamiento anterior, sin cambios.
  2. **Vector 1-D + `subgroup_size`** — si el total de observaciones no es divisible
     por el tamaño, el último subgrupo incompleto se **grafica** con sus propios
     límites (calculados con las constantes de su tamaño real) pero **no entra** en
     la estimación de sigma ni media; se emite un `UserWarning` describiendo la
     situación.
  3. **DataFrame en formato largo + `subgroup` + `value`** — `subgroup` es el nombre
     de la columna de identificadores de subgrupo y `value` el de la columna de
     valores; si hay una sola columna numérica, `value` se detecta automáticamente.

### Cambiado
- `to_subgroups` ahora devuelve `(mat, n_complete)` en vez de solo `mat`.
  `n_complete` indica cuántos subgrupos se usan para el cálculo de límites.

## [0.4.9] - README exhaustivo

### Cambiado
- `README.md`: reescrito con explicaciones detalladas de todas las cartas de
  control, parámetros, ejemplos de uso, tablas de Cp/Cpk vs Pp/Ppk, las 8
  pruebas de causas especiales, acceso a datos del resultado e instrucciones
  de desarrollo.

## [0.4.8] - zonas sigma en cartas asimétricas

### Corregido
- `_draw_panel`: se eliminó la condición `panel.symmetric` que impedía dibujar
  las líneas de ±1σ y ±2σ en cartas asimétricas (MR, R, S, atributos). Ahora
  todos los paneles muestran las zonas cuando `zones=True`, igual que Minitab.
  Las líneas que quedan por debajo de cero no son visibles (matplotlib las
  recorta al rango de los datos).

## [0.4.7] - zonas sigma visibles por defecto

### Cambiado
- `plot_control_chart` y `_draw_panel`: el parámetro `zones` ahora es `True` por
  defecto. Las líneas de ±1σ y ±2σ se muestran automáticamente en todas las cartas
  simétricas, igual que Minitab. Para ocultar las zonas usa `zones=False`.

## [0.4.4] - correcciones de documentación y empaquetado

### Corregido
- Eliminado classifier de licencia duplicado (`License :: OSI Approved :: MIT License`)
  incompatible con PEP 639 en setuptools ≥ 77.
- Corregidas todas las URLs y referencias de `TU_USUARIO/<nombre anterior>` a `LeoSanta15/pccpy`
  en README.md, docs/ y CONTRIBUTING.md.
- Nombre del proyecto actualizado del nombre anterior a `pccpy` en pyproject.toml, conf.py
  e index.md.
- Modernizadas anotaciones de tipo con ruff (UP006, UP035, UP045).

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
