# BUG CATALOG — pccpy

> Fichas de todos los bugs verificados en el historial git + taxonomía de clases de error.
> Fuente: `git log --all --oneline` (102 commits), mensajes de commit, diffs.

---

## FICHAS DE BUGS

---

### BUG-01 · Zonas sigma no visibles en cartas asimétricas

| Campo | Detalle |
|---|---|
| **ID** | BUG-01 |
| **Síntoma** | Las cartas MR, R y S no mostraban las bandas ±1σ/±2σ aunque `zones=True` |
| **Causa raíz** | Condición `if zones and panel.symmetric` en `plotting.py` — las cartas asimétricas tienen `symmetric=False` y quedaban excluidas |
| **Cómo se detectó** | Revisión visual de salida de gráficos; commit de fix en v0.4.8 |
| **Solución aplicada** | Eliminada la condición `panel.symmetric`; matplotlib recorta naturalmente líneas por debajo del rango visible |
| **Archivo/línea** | `src/pccpy/plotting.py` (commit `314cb86`) |
| **Test de regresión** | SÍ — `tests/test_regresiones_catalogo.py::test_bug01_*` (cuenta las líneas de zona de los paneles R, S y MR). Probado por mutación: restituir la condición `panel.symmetric` los hace fallar |
| **¿Puede ocurrir en otras libs?** | Sí — cualquier librería de visualización que añada condiciones de "simetría" para controlar trazado. |

---

### BUG-02 · `as_1d()` lanzaba `ValueError` opaco ante NaN/inf en datos

| Campo | Detalle |
|---|---|
| **ID** | BUG-02 |
| **Síntoma** | Usuarios con datos reales (ficheros CSV con celdas vacías) recibían `ValueError` sin contexto |
| **Causa raíz** | `as_1d()` llamaba `np.asarray(..., dtype=float)` que silenciosamente convierte NaN pero luego operaciones de scipy fallaban; no había filtrado previo |
| **Cómo se detectó** | Uso en producción / datos reales; commit `39bd66a` lo documenta como mejora de compatibilidad |
| **Solución aplicada** | Filtrado de valores no finitos con `UserWarning`; si no quedan valores válidos, `ValueError` con mensaje descriptivo |
| **Archivo/línea** | `src/pccpy/_data.py`, función `as_1d()` (commit `39bd66a`) |
| **Test de regresión** | SÍ — `test_charts.py` actualizado en `39bd66a` |
| **¿Puede ocurrir en otras libs?** | Sí — es el error más común en librerías científicas que reciben datos de usuarios finales. |

---

### BUG-03 · `to_subgroups()` fallaba con DataFrame con columnas de texto

| Campo | Detalle |
|---|---|
| **ID** | BUG-03 |
| **Síntoma** | Error `"could not convert string to float"` al pasar un DataFrame con columna de fecha o etiqueta |
| **Causa raíz** | `np.asarray(df)` sin filtrar columnas no numéricas |
| **Cómo se detectó** | Uso con datos industriales reales; commit `39bd66a` |
| **Solución aplicada** | Filtrado automático de columnas no numéricas con `UserWarning` que sugiere `subgroup='nombre_columna'` |
| **Archivo/línea** | `src/pccpy/_data.py`, función `to_subgroups()` (commit `39bd66a`) |
| **Test de regresión** | SÍ — `test_charts.py` actualizado |
| **¿Puede ocurrir en otras libs?** | Sí — cualquier librería que acepte DataFrames como entrada de subgrupos. |

---

### BUG-04 · `capability_analysis()` lanzaba `ValueError` sin límites de especificación

| Campo | Detalle |
|---|---|
| **ID** | BUG-04 |
| **Síntoma** | `capability_analysis(x)` sin `lsl`/`usl` lanzaba `ValueError("Se requiere al menos lsl o usl")` |
| **Causa raíz** | Diseño de API que asumía que los límites son siempre necesarios; no consideró el caso exploratorio |
| **Cómo se detectó** | Uso real; commit `39bd66a` |
| **Solución aplicada** | `lsl` y `usl` son ahora opcionales; sin ellos los índices Cp/Cpk/Pp/Ppk se devuelven como `NaN` |
| **Archivo/línea** | `src/pccpy/capability.py` (commit `39bd66a`) |
| **Test de regresión** | SÍ — `test_capability.py` actualizado |
| **¿Puede ocurrir en otras libs?** | Sí — patrón frecuente en APIs estadísticas con parámetros que "siempre" se necesitan en producción. |

---

### BUG-05 · `ZeroDivisionError` en `capability_analysis()` con datos constantes

| Campo | Detalle |
|---|---|
| **ID** | BUG-05 |
| **Síntoma** | `capability_analysis(np.ones(30))` lanzaba `ZeroDivisionError` o `ValueError` |
| **Causa raíz** | `_indices()`, `_expected_ppm()` y `_z_bench()` no manejaban `sigma=0` |
| **Cómo se detectó** | Commit `39bd66a`; caso límite de datos de proceso en calibración |
| **Solución aplicada** | Retorno de `NaN` con `UserWarning` al detectar desviación estándar = 0 |
| **Archivo/línea** | `src/pccpy/capability.py` funciones privadas (commit `39bd66a`) |
| **Test de regresión** | SÍ — `test_capability.py` actualizado |
| **¿Puede ocurrir en otras libs?** | Sí — división por cero con sigma en cualquier análisis estadístico. |

---

### BUG-06 · `zone_chart` fallaba con nuevo error de `subgroup_size=1`

| Campo | Detalle |
|---|---|
| **ID** | BUG-06 |
| **Síntoma** | `zone_chart(data)` con datos individuales fallaba internamente con el nuevo error de validación de `to_subgroups()` |
| **Causa raíz** | `to_subgroups(arr, 1)` fue modificado para rechazar `subgroup_size=1` con mensaje que apunta a `imr_chart()`. `zone_chart` usa internamente `to_subgroups` con tamaño 1. |
| **Cómo se detectó** | Commit `39bd66a` — detectado al aplicar la validación general de `subgroup_size=1` |
| **Solución aplicada** | Añadido parámetro `_allow_size_1=True` para llamadas internas legítimas |
| **Archivo/línea** | `src/pccpy/_data.py`, `src/pccpy/charts/advanced.py` (commit `39bd66a`) |
| **Test de regresión** | SÍ — `test_advanced_charts.py` existente cubre `zone_chart` |
| **¿Puede ocurrir en otras libs?** | Sí — añadir validación de entrada puede romper llamadas internas que usan el mismo camino. |

---

### BUG-07 · Import de openpyxl daba error opaco sin orientación al usuario

| Campo | Detalle |
|---|---|
| **ID** | BUG-07 |
| **Síntoma** | `result.to_excel("salida.xlsx")` lanzaba `ImportError: No module named 'openpyxl'` sin mensaje de qué instalar |
| **Causa raíz** | El `ImportError` de `pd.ExcelWriter(engine="openpyxl")` se propagaba sin capturar |
| **Cómo se detectó** | Commit `39bd66a` / v0.10.7; openpyxl es dependencia opcional |
| **Solución aplicada** | Helper `_excel_writer()` en `_data.py` que captura `ImportError` y da instrucción explícita `pip install pccpy[excel]` |
| **Archivo/línea** | `src/pccpy/_data.py`, función `_excel_writer()` (commit `39bd66a`) |
| **Test de regresión** | SÍ — `tests/test_regresiones_catalogo.py::test_bug07_*` (`monkeypatch.setitem(sys.modules, "openpyxl", None)`). Probado por mutación: quitar el mensaje accionable de `_excel_writer()` los hace fallar |
| **¿Puede ocurrir en otras libs?** | Sí — patrón universal para dependencias opcionales. |

---

### BUG-08 · CI tests.yml tenía referencias a `nombre_anterior` tras el renombre

| Campo | Detalle |
|---|---|
| **ID** | BUG-08 |
| **Síntoma** | CI corría `pytest --cov=nombre_anterior` y `mypy src/nombre_anterior` — el módulo ya no existía |
| **Causa raíz** | El renombre de módulo no actualizó los workflows de GitHub Actions |
| **Cómo se detectó** | Primer run de CI tras el renombre; commit `3de6dc5` |
| **Solución aplicada** | Sed en los workflows: `--cov=nombre_anterior → --cov=pccpy`, `src/nombre_anterior → src/pccpy` |
| **Archivo/línea** | `.github/workflows/tests.yml`, `.github/workflows/publish.yml` (commit `3de6dc5`) |
| **Test de regresión** | N/A — es un bug de infraestructura CI |
| **¿Puede ocurrir en otras libs?** | Sí — renombres de paquete deben incluir todos los artefactos de CI. |

---

### BUG-09 · PEP 639: `license` SPDX + classifier duplicado con setuptools>=77

| Campo | Detalle |
|---|---|
| **ID** | BUG-09 |
| **Síntoma** | `python -m build` fallaba con error de setuptools sobre license classifier duplicado |
| **Causa raíz** | PEP 639 adoptado en setuptools>=77: `license = "MIT"` y `License :: OSI Approved :: MIT License` son mutuamente excluyentes |
| **Cómo se detectó** | Al intentar publicar en PyPI; commit `e894a25` |
| **Solución aplicada** | Eliminar el classifier `License :: ...` del `pyproject.toml` |
| **Archivo/línea** | `pyproject.toml` (commit `e894a25`) |
| **Test de regresión** | N/A — build funciona. Se podría añadir `twine check dist/*` al CI |
| **¿Puede ocurrir en otras libs?** | Sí — cualquier paquete que migre a setuptools>=77 sin revisar PEP 639. |

---

### BUG-10 · Python 3.9: `stats.normaltest` lanza `ValueError` para n < 8

| Campo | Detalle |
|---|---|
| **ID** | BUG-10 |
| **Síntoma** | `diagnose(x)` con menos de 8 puntos fallaba en CI Python 3.9 (`stats.normaltest` exige n >= 8) |
| **Causa raíz** | `scipy.stats.normaltest` no admite n < 8 y `diagnose` lo llamaba sin guardia (el comportamiento exacto por versión de scipy NO VERIFICADO) |
| **Cómo se detectó** | CI multi-versión; commit `44f7f69` |
| **Solución aplicada** | Guardia `if n < 8:` → `normality_stat/p = nan`, `is_normal = True`; sin `try/except` (`src/pccpy/_diagnose.py:267-272`). *Corrección: la ficha original describía un `try/except` que no existe en el código.* |
| **Archivo/línea** | `src/pccpy/_diagnose.py:267` (commit `44f7f69`) |
| **Test de regresión** | PARCIAL — `tests/test_diagnose.py:20` ejecuta n=5 pero solo asserta estadísticos descriptivos; nada asserta `normality_p` NaN / `is_normal=True`. `test_diagnose_min_n` (línea 33) prueba n<4, otra rama |
| **¿Puede ocurrir en otras libs?** | Sí — scipy cambia comportamiento de warnings/errores entre versiones menores. |

---

### BUG-11 · Sphinx: `autoclass WidgetSession` generaba advertencia duplicada

| Campo | Detalle |
|---|---|
| **ID** | BUG-11 |
| **Síntoma** | CI `documentacion` (`sphinx-build -W`) falló con 18 warnings tras el PR #6: "duplicate object description" de `DiagnoseResult`, `WizardResult`, `WidgetSession` y sus miembros, más 1 referencia ambigua a `n` |
| **Causa raíz** | (a) Las nuevas páginas `referencia/diagnose.rst` y `referencia/wizard.rst` hacían `autoclass` de símbolos que `diagnose.md` y `wizard.md` ya documentaban; (b) `x : array-like, shape (n,)` en el docstring de `diagnose()` hacía que Sphinx resolviera `n` contra todos los atributos `n` |
| **Cómo se detectó** | CI job `documentacion` en el commit `31e9b74`; corregido en `819ca11` |
| **Solución aplicada** | `:no-index:` en la directiva de la página que Sphinx procesa primero (`diagnose.md`; `referencia/wizard.rst`), dejando la otra como canónica; docstring `shape (n,)` → `array-like` (`_diagnose.py`). *Corrección: la ficha original decía "reemplazar autoclass por tabla Markdown", lo cual no corresponde al código (`wizard.md:117-120` sigue usando `autoclass` con `:no-index:`).* |
| **Archivo/línea** | `docs/source/diagnose.md:136`, `docs/source/referencia/wizard.rst:9,14`, `docs/source/wizard.md:120`, `src/pccpy/_diagnose.py:228` |
| **Test de regresión** | SÍ — el job de CI `sphinx-build -W` (no es un test pytest); `sphinx-build -W` local sobre `main` termina con `build succeeded` |
| **¿Puede ocurrir en otras libs?** | Sí — dos páginas con autodoc del mismo símbolo siempre duplican; `shape (n,)` choca con cualquier atributo `n`. Regla R-14. |

---

### BUG-12 · Plots contaminaban estilos globales de matplotlib (incompatibilidad con seaborn)

| Campo | Detalle |
|---|---|
| **ID** | BUG-12 |
| **Síntoma** | En entornos con seaborn importado antes de pccpy, los gráficos de control aparecían con estilos de seaborn; viceversa, pccpy alteraba los gráficos del usuario |
| **Causa raíz** | Las funciones `plot_*` modificaban `rcParams` globalmente sin restaurar el estado anterior |
| **Cómo se detectó** | Uso en Jupyter con seaborn; commit `786fccb` |
| **Solución aplicada** | Envolver todas las funciones `plot_*` en `plt.rc_context({})` |
| **Archivo/línea** | `src/pccpy/plotting.py`, `src/pccpy/quality_tools.py` (commit `786fccb`) |
| **Test de regresión** | SÍ — `tests/test_regresiones_catalogo.py::test_bug12_*` (compara `dict(matplotlib.rcParams)` antes y después de `.plot()` en cartas, capacidad, Pareto y Gage R&R). Probado por mutación: tocar `rcParams` fuera de `rc_context` lo hace fallar |
| **¿Puede ocurrir en otras libs?** | Sí — cualquier librería de visualización que no use `rc_context`. |

---

### BUG-13 · Release v0.10.8 falló: tag creado antes de subir la versión

| Campo | Detalle |
|---|---|
| **ID** | BUG-13 |
| **Síntoma** | Workflow "Publicar en PyPI" (run `37060818445`) terminó en `failure`: PyPI respondió `400 File already exists ('pccpy-0.10.7-py3-none-any.whl')` |
| **Causa raíz** | El tag `v0.10.8` apuntaba a `d16df0d`, donde `pyproject.toml` y `__init__.py` seguían en `0.10.7`; el build generó artefactos 0.10.7, ya publicados. Se había declarado "listo para release" sin verificar la versión. Versión duplicada en 2 archivos (clase C-08) y sin guarda tag↔wheel en `publish.yml` |
| **Cómo se detectó** | Logs del job fallido (`mcp__github__get_job_logs`); el usuario reportó el fallo |
| **Solución aplicada** | Commit `2be31df` (bump a 0.10.8 en ambos archivos + CHANGELOG); el usuario movió el tag y el release 0.10.8 se publicó |
| **Archivo/línea** | `pyproject.toml:7`, `src/pccpy/__init__.py:89` |
| **Test de regresión** | PARCIAL — `publish.yml` ya comprueba tag == versión del wheel y corre `twine check` antes de publicar (los pasos se probaron localmente con el wheel de 0.15.8: OK con `v0.15.8`, error con `v0.15.9`; **no se han ejecutado en Actions**, solo al publicar el próximo release). `tests/test_regresiones_catalogo.py::test_bug13_*` vigila que los pasos sigan en el flujo y antes de publicar. Falta la versión única vía `dynamic` (probado en copia) |
| **¿Puede ocurrir en otras libs?** | Sí — cualquier proyecto que etiquete a mano y mantenga la versión en más de un sitio. |

---

### BUG-14 · `examples/*.py` rotos tras el renombre `nombre_anterior` → `pccpy`

| Campo | Detalle |
|---|---|
| **ID** | BUG-14 |
| **Síntoma** | `python examples/ejemplo_basico.py` → `AttributeError: module 'nombre_anterior' has no attribute 'imr_chart'`; `ejemplo_avanzado.py` → `... 'zmr_chart'` |
| **Causa raíz** | Ambos scripts conservan `import nombre_anterior` (`ejemplo_basico.py:14`, `ejemplo_avanzado.py:9`); el renombre no los tocó y ningún test ni CI los ejecuta |
| **Cómo se detectó** | Esta revisión: `grep -rIl nombre_anterior .` + ejecución de los scripts (2026-10-02). La retrospectiva inicial no lo vio |
| **Solución aplicada** | CORREGIDO: se reemplazó el nombre antiguo por `pccpy` en ambos scripts; los dos ejecutan sin error (`MPLBACKEND=Agg python examples/<f>.py`, 2026-10-02) |
| **Archivo/línea** | `examples/ejemplo_basico.py`, `examples/ejemplo_avanzado.py` |
| **Test de regresión** | NO — sigue faltando un paso de CI que ejecute `examples/*.py` |
| **¿Puede ocurrir en otras libs?** | Sí — los ejemplos fuera de `src/` y `tests/` se pudren en silencio tras cualquier renombre o cambio de API. |

---

### BUG-15 · EWMA-P/EWMA-U con tamaño de muestra variable: límites demasiado estrechos

| Campo | Detalle |
|---|---|
| **ID** | BUG-15 |
| **Síntoma** | Con `n` alternando 30 y 600 (p = 0,1; λ = 0,2) la tasa de falsas alarmas por punto era 0,152 en lugar de ≈ 0,0027 |
| **Causa raíz** | `_ewma_attr` usaba `σ(nᵢ)·√(λ/(2−λ)·(1−(1−λ)^{2i}))`, fórmula cerrada válida solo con `n` constante; la varianza exacta es `Vᵢ = (1−λ)²Vᵢ₋₁ + λ²σ²(nᵢ)` |
| **Cómo se detectó** | Auditoría estadística 0.15.7 (simulación con 20 semillas contra la recursión escrita aparte) |
| **Solución aplicada** | CORREGIDO en 0.15.8: recursión de la varianza (también en `ewma_chart` para el último subgrupo incompleto) |
| **Archivo/línea** | `src/pccpy/charts/timeweighted_attr.py` |
| **Test de regresión** | SÍ — `tests/test_auditoria_015.py::test_s015_rf01_*` |
| **¿Puede ocurrir en otras libs?** | Sí — cualquier fórmula «de régimen estacionario» aplicada con entradas de tamaño variable. |

Requisitos de la especificación 015: S015-RF-01, S015-RF-08.

---

### BUG-16 · Dodge-Romig: ATI con `Pa` en lugar de `1−Pa` y AOQL aproximado con holgura del 5 %

| Campo | Detalle |
|---|---|
| **ID** | BUG-16 |
| **Síntoma** | `dodge_romig(1000, ltpd=0.05)` elegía n=45, c=0 (ATI 392) en lugar de n=132, c=3 (ATI 170,4); el plan por AOQL superaba el objetivo (0,02095 > 0,02); el AOQL de Z1.4 daba 0,000255 en lugar de 0,000287 |
| **Causa raíz** | `ATI = n + Pa·(N−n)` (debe ser `(1−Pa)`); el AOQL se tomaba como máximo de una rejilla de 400 a 500 puntos y se aceptaba hasta un 5 % por encima del objetivo |
| **Cómo se detectó** | Auditoría estadística 0.15.7 (búsqueda exhaustiva con `scipy.stats.binom`) |
| **Solución aplicada** | CORREGIDO en 0.15.8: `_ati`, `_aoql_exacto` (rejilla y `minimize_scalar`) y bisección por `c`; `_ltpd_exacto` ya no depende del AQL |
| **Archivo/línea** | `src/pccpy/acceptance.py` |
| **Test de regresión** | SÍ — `test_s015_rf02_*` y `test_s015_rf13_ltpd_de_plan_a_medida` |
| **¿Puede ocurrir en otras libs?** | Sí — optimizar con una fórmula escrita al revés pasa desapercibido si solo se comprueba que el plan «cumple». |

Requisitos de la especificación 015: S015-RF-02, S015-RF-13.

---

### BUG-17 · Carta de corridas: prueba de tendencias descalibrada con empates

| Campo | Detalle |
|---|---|
| **ID** | BUG-17 |
| **Síntoma** | Con datos redondeados (n = 30) el 38 % de las series daba `p_trends < 0,05` (con datos continuos, 3 %) |
| **Causa raíz** | Las diferencias nulas se descartaban pero `E = (2n−1)/3` y `V = (16n−29)/90` usaban la `n` original; con empates `n` debe ser `m + 1` (puntos que quedan) |
| **Cómo se detectó** | Auditoría estadística 0.15.7 (20 semillas × 500 series) |
| **Solución aplicada** | CORREGIDO en 0.15.8: `n = m + 1` en `_runs_updown`. Minitab podría tratar los empates de otro modo (no se pudo verificar) |
| **Archivo/línea** | `src/pccpy/charts/run_chart.py` |
| **Test de regresión** | SÍ — `test_s015_rf03_*` |
| **¿Puede ocurrir en otras libs?** | Sí — datos con resolución limitada (instrumentos digitales) rompen pruebas pensadas para datos continuos. |

Requisitos de la especificación 015: S015-RF-03.

---

### BUG-18 · `diagnose()` y `wizard()` casi no detectaban tendencias

| Campo | Detalle |
|---|---|
| **ID** | BUG-18 |
| **Síntoma** | Una deriva total de 3σ con n = 20 o 50 se detectaba en 0 % de los casos; con n = 3 daba 33 % de falsas alarmas |
| **Causa raíz** | La regla «más del 80 % o menos del 20 % de las diferencias positivas» (llamada «Mann-Kendall simplificado») exige casi monotonía |
| **Cómo se detectó** | Auditoría estadística 0.15.7 (simulación con 20 semillas) |
| **Solución aplicada** | CORREGIDO en 0.15.8: Mann-Kendall (`scipy.stats.kendalltau` contra el índice, α = 0,05 bilateral) con mínimo de 8 observaciones; `wizard` usa la misma prueba y protege `normaltest` con n < 8 |
| **Archivo/línea** | `src/pccpy/_diagnose.py`, `src/pccpy/_wizard.py` |
| **Test de regresión** | SÍ — `test_s015_rf04_*`, `test_s015_rf15_wizard_con_n_pequeno_no_avisa` |
| **¿Puede ocurrir en otras libs?** | Sí — una prueba «simplificada» sin potencia calculada. |

Requisitos de la especificación 015: S015-RF-04, S015-RF-15.

---

### BUG-19 · p-valor del kappa de Cohen con error estándar incorrecto

| Campo | Detalle |
|---|---|
| **ID** | BUG-19 |
| **Síntoma** | Tasa de rechazo bajo H₀ al 5 % de 0,13 % (marginales 85/15, n = 100); el error estándar salía 1,15 a 1,38 veces mayor con 3 categorías |
| **Causa raíz** | Se usaba `√(pₑ/(n(1−pₑ)))`; el error estándar bajo H₀ es el de Fleiss, Cohen y Everitt (1969): `√((pₑ + pₑ² − Σ pᵢ.p.ᵢ(pᵢ. + p.ᵢ))/(n(1−pₑ)²))` |
| **Cómo se detectó** | Auditoría estadística 0.15.7 (`statsmodels.cohens_kappa(...).std_kappa0` y simulación) |
| **Solución aplicada** | CORREGIDO en 0.15.8. Minitab podría usar otro error estándar (no se pudo verificar). La repetibilidad ya no promedia p-valores de pares |
| **Archivo/línea** | `src/pccpy/msa.py` (`_cohen_kappa`) |
| **Test de regresión** | SÍ — `test_s015_rf05_*` |
| **¿Puede ocurrir en otras libs?** | Sí — mezclar el error estándar de H₀ con el de la estimación. |

Requisitos de la especificación 015: S015-RF-05, S015-RF-14.

---

### BUG-20 · Capacidad con huecos: `capability_boxcox` desplazaba subgrupos y el rango móvil cruzaba los huecos

| Campo | Detalle |
|---|---|
| **ID** | BUG-20 |
| **Síntoma** | `capability_boxcox` daba σ_within 0,3012 en lugar de 0,1897; la capacidad con individuales daba 0,9527 en lugar de 0,6077 |
| **Causa raíz** | `capability_boxcox` quitaba los NaN antes de agrupar; `capability_analysis` con individuales compactaba la serie (`as_1d`) y unía observaciones no consecutivas |
| **Cómo se detectó** | Auditoría estadística 0.15.7 |
| **Solución aplicada** | CORREGIDO en 0.15.8: los huecos se conservan (`as_1d_con_huecos`), como en `imr_chart` (decisión S006-RF-06) |
| **Archivo/línea** | `src/pccpy/capability.py` |
| **Test de regresión** | SÍ — `test_s015_rf06_*`, `test_s015_rf07_*` |
| **¿Puede ocurrir en otras libs?** | Sí — dos rutas que limpian NaN en lugares distintos. |

Requisitos de la especificación 015: S015-RF-06, S015-RF-07.

---

### BUG-21 · `phase2()` fallaba tras `phase_one(..., center="median")`

| Campo | Detalle |
|---|---|
| **ID** | BUG-21 |
| **Síntoma** | `ValueError: 'center="median"' no se combina con 'mu'` al llamar a `phase2()` |
| **Causa raíz** | `phase2()` volvía a pasar `center` junto con la `mu` congelada |
| **Cómo se detectó** | Auditoría estadística 0.15.7 |
| **Solución aplicada** | CORREGIDO en 0.15.8: `phase2()` no pasa `center` (también con archivos de Fase I guardados antes) |
| **Archivo/línea** | `src/pccpy/phase1.py` |
| **Test de regresión** | SÍ — `test_s015_rf09_*` |
| **¿Puede ocurrir en otras libs?** | Sí — una opción que genera un parámetro congelado no debe reenviarse. |

Requisitos de la especificación 015: S015-RF-09.

---

### BUG-22 · `gage_rr(tolerance=)` sin efecto

| Campo | Detalle |
|---|---|
| **ID** | BUG-22 |
| **Síntoma** | El docstring y el README prometían `%Tolerancia`, pero el parámetro no cambiaba ninguna salida |
| **Causa raíz** | El parámetro se aceptaba y no se usaba |
| **Cómo se detectó** | Auditoría estadística 0.15.7 |
| **Solución aplicada** | CORREGIDO en 0.15.8: `pct_tolerance_gage`, `pct_tolerance_repeatability` y `pct_tolerance_reproducibility` (`100·K·σ/T`) en `to_frame()` y `summary()` |
| **Archivo/línea** | `src/pccpy/msa.py` |
| **Test de regresión** | SÍ — `test_s015_rf10_*` |
| **¿Puede ocurrir en otras libs?** | Sí — parámetros aceptados y no usados. |

Requisitos de la especificación 015: S015-RF-10.

---

### BUG-23 · %Linealidad y %Sesgo medían el instrumento, no el proceso

| Campo | Detalle |
|---|---|
| **ID** | BUG-23 |
| **Síntoma** | Con pendiente −0,117, `%Linealidad` daba 84,3 % en lugar de 11,7 % |
| **Causa raíz** | El denominador era `6·s_residual` (variación del instrumento); AIAG usa la variación del proceso: `%Linealidad = 100·|pendiente|` y `%Sesgo = 100·|sesgo medio| / variación del proceso` |
| **Cómo se detectó** | Auditoría estadística 0.15.7 (definición de AIAG MSA 3.ª ed., recordada de memoria; no se comprobó la de Minitab) |
| **Solución aplicada** | CORREGIDO en 0.15.8: `%Linealidad = 100·|pendiente|` y `process_variation=` para el %Sesgo |
| **Archivo/línea** | `src/pccpy/msa.py` |
| **Test de regresión** | SÍ — `test_s015_rf11_*` |
| **¿Puede ocurrir en otras libs?** | Sí. |

Requisitos de la especificación 015: S015-RF-11.

---

### BUG-24 · Límites de la carta |S| con aproximación normal

| Campo | Detalle |
|---|---|
| **ID** | BUG-24 |
| **Síntoma** | `P(|S| > LCS) ≈ 0,0197` (ARL₀ ≈ 50) en lugar de 0,00135, y el LCI quedaba en 0 |
| **Causa raíz** | `b1 ± k·√b2` (Montgomery 11.3) supone una distribución simétrica de `|S|`, que es muy asimétrica |
| **Cómo se detectó** | Auditoría estadística 0.15.7 (simulación de |S|) |
| **Solución aplicada** | CORREGIDO en 0.15.8: límites por percentiles de `|S| = |Σ|·Πχ²_{n−i}/(n−1)^p` (Bartlett) por convolución numérica de las ln χ² |
| **Archivo/línea** | `src/pccpy/multivariate.py` |
| **Test de regresión** | SÍ — `test_s015_rf12_*` |
| **¿Puede ocurrir en otras libs?** | Sí — aproximaciones normales de estadísticos con cola larga. |

Requisitos de la especificación 015: S015-RF-12.

---

### BUG-25 · Z1.4: plan con muestra mayor que el lote

| Campo | Detalle |
|---|---|
| **ID** | BUG-25 |
| **Síntoma** | `acceptance_sampling_attributes(10, 0.01)` devolvía `n = 1250` con un lote de 10 (y `aoq_max = -0.0`); lo mismo con `N = 20` o `N = 200` |
| **Causa raíz** | La tabla Z1.4 manda, cuando «la muestra es igual o mayor que el lote», inspeccionar el 100 %; la función devolvía el tamaño de la tabla sin compararlo con `N` |
| **Cómo se detectó** | Al leer el código para la especificación 016 (Z1.4 con niveles especiales y muestreo doble) |
| **Solución aplicada** | CORREGIDO: con `n ≥ N` el plan lleva `n = N` (con el `Ac` de la tabla) y un `UserWarning`; el plan doble pone todo el lote en la primera muestra. El AOQL queda en 0 |
| **Archivo/línea** | `src/pccpy/acceptance.py`, `acceptance_sampling_attributes` y `_plan_doble` |
| **Test de regresión** | SÍ — `tests/test_z14_niveles_y_doble.py::test_s016_rf04_*` |
| **¿Puede ocurrir en otras libs?** | Sí — una tabla de planes aplicada sin comprobar el tamaño del lote. |

Requisito de la especificación 016: S016-RF-04.

---

## TAXONOMÍA DE CLASES DE ERROR

| Clase | Descripción | Cómo prevenirla | Cómo detectarla | Bugs en este proyecto |
|---|---|---|---|---|
| **C-01 Validación de entrada faltante** | La función acepta datos inválidos (NaN, inf, tipo incorrecto, vacío) y falla con error opaco aguas abajo | Capa de validación explícita en cada función pública; tests con entradas malformadas | `pytest` con casos borde; `mypy` para tipos | BUG-02, BUG-03, BUG-05 |
| **C-02 Caso degenerado no considerado** | El diseño de API no contempló valores extremos válidos (sin límites, datos constantes, n<8) | Listar casos degenerados al diseñar la API; documentar en docstring | Tests parametrizados con valores límite | BUG-04, BUG-05, BUG-10, BUG-25 |
| **C-03 Import opcional sin mensaje orientativo** | Dependencia opcional ausente genera `ImportError` crudo sin guía al usuario | Capturar `ImportError` de opcionales; mensaje con `pip install ...` | Test que simula ausencia con `unittest.mock` | BUG-07 |
| **C-04 CI que no detecta el fallo** | El build/test local pasa pero CI falla por diferencia de entorno (versión Python, Node), o el pipeline de release no verifica lo que publica | Correr la matrix localmente con tox antes del PR; CI fail-fast desactivado; guarda tag==versión del wheel y `twine check` antes de publicar | Primera ejecución en CI; logs de CI | BUG-08, BUG-09, BUG-10, BUG-11, BUG-13 |
| **C-05 Documentación/ejemplos desactualizados** | Código, comandos o ejemplos apuntan al estado anterior (nombre viejo, API vieja) | Incluir docs y `examples/` en el checklist de cada PR; ejecutar `examples/*.py` y `grep` de términos obsoletos en CI | Grep automatizado; ejecutar los ejemplos; revisión de CLAUDE.md en cada sesión | BUG-08, BUG-14, L-01, L-07 |
| **C-06 Efecto secundario de refactor** | Validación añadida en función base rompe llamada interna válida | Al añadir validación, buscar todas las llamadas internas con `grep`; añadir parámetro escape-hatch explícito | Tests de integración de módulos que se llaman entre sí | BUG-06 |
| **C-07 Estado global de entorno** | La librería modifica estado global (rcParams) contaminando el entorno del usuario | Usar context managers (`rc_context`, `warnings.catch_warnings`) | Test que verifica estado antes/después de la llamada | BUG-12 |
| **C-08 Versión múltiple fuente** | La versión se gestiona en N>1 lugares y se desincroniza | Literal único en `__init__.py` + `[tool.setuptools.dynamic] version = {attr = ...}` (probado). **No** `importlib.metadata` en `__init__.py`: se congela al instalar (probado) | Guarda tag==versión del wheel en el workflow de publicación (R-13); en dev, `grep -n '^version\|^__version__'` | BUG-13, L-10 |
| **C-09 Autodoc duplicado/ambiguo** | Dos directivas autodoc para el mismo símbolo, o tipos en docstring (`shape (n,)`) que Sphinx resuelve como referencia | Una directiva canónica por símbolo; `:no-index:` en la procesada primero; `array-like` en vez de `shape (n,)` | `sphinx-build -W` en CI | BUG-11 |
| **C-10 Fórmula estadística fuera de su supuesto** | Una fórmula de régimen estacionario, de datos continuos o de una aproximación normal se usa donde no vale (n variable, empates, estadísticos asimétricos) | Contrastar cada resultado con una referencia independiente y una simulación con ≥ 20 semillas (R-02), incluidos los casos de entrada «incómodos» | Auditoría con Monte Carlo; `run_validation()` | BUG-15, BUG-16, BUG-17, BUG-18, BUG-19, BUG-23, BUG-24 |
