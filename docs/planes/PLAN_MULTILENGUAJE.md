# Plan por fases — pccpy multilenguaje (i18n)

> **Estado:** aprobado el 2026-10-04; en ejecución, **una rama y un PR por fase** (los PR se apilan: cada uno parte de la rama de la fase anterior hasta que ésta se fusiona).
> **Alcance:** idiomas humanos (español + inglés). **Fuera de alcance:** bindings para otros lenguajes de programación (R, Julia…).
> **Convención:** ✅ probado · ‼️ falló en el prototipo y se corrigió · ❔ NO VERIFICADO · *(inferencia)* estimación a partir de conteos.

## Decisiones aprobadas

| Pregunta | Decisión |
|---|---|
| Idioma por defecto | **`es`** (sin cambio de comportamiento) |
| Idiomas | `es` + **`en`** (máximo dos hasta que haya quien los mantenga) |
| Columnas de `to_frame()` | cabeceras en el idioma activo + `to_frame(stable=True)` con claves canónicas (D-7) |
| Documentación (Fase 4) | **diferida**: se decide al terminar la Fase 3 |
| Revisión del glosario SPC (Fase 5) | **pendiente de designar** a la persona responsable; el borrador de glosario lo prepara el agente |
| Entrega | una rama y PR por fase; el merge lo decide la persona responsable |

## Seguimiento por fases

| Fase | Rama | PR | Estado |
|---|---|---|---|
| 0 Andamiaje | `feat/i18n-fase-0-andamiaje` | [#7](https://github.com/LeoSanta15/pccpy/pull/7) | en revisión |
| 1 Errores y avisos | `feat/i18n-fase-1-errores` | [#8](https://github.com/LeoSanta15/pccpy/pull/8) | en revisión |
| 2 `summary()` y `to_frame()` | `feat/i18n-fase-2-resumenes` | [#9](https://github.com/LeoSanta15/pccpy/pull/9) | en revisión |
| 3 Gráficos y constantes de módulo (`wizard`) | `feat/i18n-fase-3-graficos` | [#10](https://github.com/LeoSanta15/pccpy/pull/10) | en revisión |
| 3b Otras tablas con columnas en español (`pareto`, curvas OC/AOQ, ANOVA, `kappa_vs_reference`) | `feat/i18n-fase-3b-tablas` | [#11](https://github.com/LeoSanta15/pccpy/pull/11) | en revisión |
| 4 Documentación multilingüe | — | — | diferida |
| 5 Glosario y release `0.11.0` | `feat/i18n-fase-5-release` | _(se completa al abrir el PR)_ | en revisión (falta la revisión humana del inglés; el tag lo crea la persona responsable) |

---

## 1. Línea base medida (código en español, sin ninguna capa de traducción)

| Qué | Cantidad | Cómo se midió |
|---|---:|---|
| Líneas de `src/` | 8 134 | `wc -l` |
| Mensajes de error y aviso (`raise …Error("…")`, `warnings.warn`) | 151 (116 constantes + 31 f-strings + 4 avisos) | análisis AST |
| Textos dentro de `summary()` | ~183 f-strings + cientos de fragmentos constantes *(el conteo de fragmentos se solapa con los f-strings; no es una cifra de mensajes únicos)* | análisis AST |
| Textos de gráficos (títulos, ejes, leyendas, anotaciones) | 62 (58 constantes + 4 f-strings) | análisis AST |
| Métodos `to_frame()` | 15, con ~165 etiquetas de columna/índice (`msa` 48, `capability` 34, `_diagnose` 23, `acceptance` 19…) | análisis AST |
| **Textos a nivel de módulo** (se evalúan al importar) | **184**: `_wizard._TREE` 175, `rules.TEST_DESCRIPTIONS` 8, `multivariate` 1 | análisis AST |
| Tests que fijan texto en español (`match=`) | 28; además ~37 aserciones sobre texto de `summary()` *(cifra aproximada: `grep` con varios patrones)* | `grep` |
| Tests que dependen de nombres de columna | 3 indexan por nombre; 15 llaman a `to_frame()` | `grep` |
| Documentación | 29 archivos `.md/.rst` en español, `language = "es"` | `find` |
| ¿Existe ya `gettext`/`locale`/`babel`? | No | `grep` |

*(inferencia)* Volumen total a extraer: **≈ 700–900 textos únicos**. Los nombres de funciones y argumentos ya están en inglés: la API no cambia.

---

## 2. Decisiones de diseño (cada una con su evidencia)

| # | Decisión | Recomendación | Alternativa descartada y por qué |
|---|---|---|---|
| D-1 | **Idioma fuente (msgid)** | El **español actual**: el diff es mínimo, el idioma por defecto no cambia y, si falta una traducción, se muestra el original ✅ (probado: `fr` sin catálogo → español) | msgid en inglés: obliga a reescribir los ~700 textos y a cambiar el comportamiento por defecto |
| D-2 | **Mecanismo** | `gettext` de la **biblioteca estándar** en ejecución; **Babel solo en desarrollo** (`pybabel extract/update/compile`) ✅ (probado: wheel instalado, sin `babel` importado en ejecución) | dependencia de ejecución nueva: innecesaria |
| D-3 | **Selección de idioma** | Global (`set_language("en")`, variable `PCCPY_LANG`) **+** sobreescritura por contexto (`with pccpy.language("en"):`) ✅ | solo `ContextVar` ‼️ (v1 del prototipo): `set_language("en")` **no llegaba a los hilos nuevos**; la v2 (global + contexto) lo corrige. Limitación documentada: un hilo nuevo creado *dentro* de `with language()` no hereda el contexto |
| D-4 | **Idioma por defecto** | **`es`** → comportamiento actual intacto; versión **0.11.0** (funcionalidad nueva, compatible) | cambiar a `en` es un cambio que rompe compatibilidad |
| D-5 | **f-strings** | Convertir a plantillas con `.format()` y marcadores con nombre: `tr("'{name}' está vacío.").format(name=name)` ✅. Los formatos numéricos (`{x:.4f}`) se quedan dentro de la plantilla | dejar el f-string dentro de `tr()` ‼️: **no se extrae** (0 mensajes) ni se puede traducir. Son 34 f-strings en errores/avisos y ~183 en `summary()` |
| D-6 | **Constantes de módulo (184)** | Marcar con `N_()` (solo para extraer) y traducir con `tr()` **al mostrar** ✅ (probado: definido al importar en `es`, mostrado en `en`, y de vuelta a `es`) | `tr()` al importar: fijaría el idioma del momento de importar |
| D-7 | **Columnas/índices de DataFrame** (decisión crítica) | `to_frame()` devuelve cabeceras **en el idioma activo** (es presentación, como `summary()`), y se añade **`to_frame(stable=True)`** con claves canónicas (inglés, `snake_case`) para código que no debe depender del idioma. Con `es` por defecto, nada cambia para los usuarios actuales | (a) traducir sin más: rompe `df["valor"]` al cambiar de idioma. (b) pasar todo a claves canónicas: rompe a todos los usuarios actuales |
| D-8 | **Docstrings y `help()`** | Se quedan en español (gettext no traduce docstrings en ejecución). La documentación se traduce con `sphinx-intl` en una fase opcional | docstrings en inglés: cambia todo el código sin beneficio |
| D-9 | **Catálogos** | Versionar `.po` y `.mo` ✅ (compilar dos veces da bytes idénticos) + `make i18n-check` en CI (hecho en la Fase 0) que recompila y falla si `.pot`/`.mo` están desactualizados | compilar en el build con un hook de setuptools: más complejo, ❔ sin probar |
| D-10 | **Idiomas** | `es` + `en`. No pasar de dos hasta que haya quien los mantenga: cada versión obliga a actualizar todos | — |
| D-11 | **Glosario SPC** | Lista cerrada revisada por una persona del dominio: `LC/LCS/LCI` → `CL/UCL/LCL`, `Desv.Est.` → `Std. Dev.`, «capacidad del proceso» → `process capability`, etc. *(inferencia: usar los términos de la interfaz en inglés de Minitab como referencia, porque pccpy replica Minitab)* | traducción libre sin revisar |
| D-12 | **Nombre del marcador** | **`tr()`** (no el habitual `_()`): 27 usos de `_` como variable en `src/`, y **8 funciones** (`mewma_chart`, `zmr_chart`, `capability_boxcox`, `mcusum_chart`…) lo asignan en su propio ámbito **y** lanzan errores; un `_("…")` ahí fallaría solo en la ruta de error, donde ningún test lo vería ✅ (medido con AST) | `_`: riesgo permanente ante cualquier `for _ in …` futuro |

---

## 3. Fases

Cada fase se entrega en **su propia rama y PR** (nunca directo a `main`), con `make check` en verde antes de pedir la fusión.

### Fase 0 — Andamiaje y decisiones *(≈ 1 día)*
- Decidir D-1…D-11 con la persona responsable.
- Añadir `src/pccpy/_i18n.py` (prototipo v2), `babel.cfg` (`[python: **.py]`, extracción con `-k N_`), extra `i18n = ["babel"]`, `package-data` `locale/*/LC_MESSAGES/*.mo`.
- Makefile: `i18n-extract`, `i18n-update`, `i18n-compile`, `i18n-check`.
- Tests del módulo: idioma global, contexto, hilos, respaldo, variable de entorno, `N_`.
- **Gate:** `make check` verde; el wheel contiene el `.mo`; `import babel` no ocurre en ejecución.

### Fase 1 — Errores y avisos *(≈ 1–2 días; 151 textos, de ellos 34 f-strings)*
- Empezar por `_data.py` (piloto) y los validadores; seguir módulo a módulo.
- Catálogo `en` completo para estos textos.
- **Gate:** un test AST (con control negativo, como `test_idioma`) falla si algún `raise`/`warn` tiene texto sin `tr()`; test de paridad: mismos marcadores `{…}` en `es` y `en` (evita un `KeyError` en `.format`); la suite actual sigue pasando con `es`.

### Fase 2 — `summary()` y etiquetas de `to_frame()` *(≈ 3–5 días; el grueso)*
- Orden por tamaño: `msa` (117 textos), `capability` (107), `_diagnose` (66), `acceptance` (56), `tolerance` (36), `results`, `run_chart`, `precontrol`.
- Definir la tabla de claves canónicas y `to_frame(stable=True)` (D-7); `to_excel()` usa las cabeceras del idioma activo.
- **Gate:** `summary()` en `en` no contiene palabras españolas (detector con control negativo); `to_frame(stable=True)` es idéntico en `es` y `en`; los 15 `to_frame()` tienen test en ambos idiomas.

### Fase 3 — Gráficos y constantes de módulo *(≈ 2–3 días)*
- 62 textos de gráficos; 184 constantes con `N_()` (el árbol de `wizard`, 175, es lo más laborioso).
- **Gate:** tests de gráficos en `en` (backend `Agg`, `rcParams` intacto); `wizard()` completo en `en`.

### Fase 4 — Documentación multilingüe *(opcional, ≈ 2–4 días, independiente)*
- `sphinx-intl` para las 29 páginas, README en inglés, Read the Docs por idioma.
- **Gate:** `sphinx-build -W` en ambos idiomas.

### Fase 5 — Calidad lingüística y release *(≈ 1–2 días)*
- Revisión del glosario por una persona del dominio SPC; guía «Cómo traducir»; CHANGELOG; `0.11.0`.
- **Gate:** `make check` y `make release-check TAG=v0.11.0`; el tag y el release los crea la persona responsable.

*(inferencia)* **Total ≈ 9–15 días-persona**, derivado de los conteos de §1; no es una medición.

---

## 4. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Un `msgid` en español se corrige (errata) y la traducción se pierde | `make i18n-check` en CI; `pybabel update` marca el cambio como *fuzzy* y el test de paridad lo detecta |
| Un marcador `{…}` distinto entre idiomas → `KeyError` al mostrar | test de paridad de marcadores (Fase 1) |
| Texto nuevo sin pasar por `tr()` | test AST con control negativo; regla en `CLAUDE.md` (§5) |
| Constantes de módulo traducidas al importar | `N_()` + test que cambia de idioma tras importar |
| Hilos y contexto | idioma global + contexto (D-3); limitación documentada |
| Los 28 tests con `match=` en español fallan al cambiar el idioma por defecto | el idioma por defecto sigue siendo `es` (D-4); un fixture fija `es` en la suite |
| Cambio de idioma que rompe código de usuarios que indexan columnas | `to_frame(stable=True)` (D-7) y documentación |
| Mantenimiento de N idiomas | límite de dos idiomas; el CI exige catálogo completo para los «oficiales» |

---

## 5. Regla propuesta para `CLAUDE.md` (no aplicada; para decidir)
**R-nn Texto visible traducible `[test]`:** todo mensaje de error, aviso, `summary()`, etiqueta de `to_frame()` o texto de gráfico pasa por `tr()` (o `N_()` si es una constante de módulo); no se usan f-strings dentro de `tr()`; los marcadores son idénticos en todos los idiomas. Comprobación: test AST con control negativo + `make i18n-check`.

---

## 6. Qué se probó y qué no

| Prueba (prototipo en una copia de `main`, Linux, Python 3.11) | Resultado |
|---|---|
| Extracción con `pybabel` (`-k N_`) y catálogo `en` | ✅ |
| Compilación determinista (dos compilaciones → bytes idénticos) | ✅ |
| Idioma por defecto, `set_language`, `PCCPY_LANG`, contexto, respaldo a español | ✅ |
| Propagación a hilos (solo `ContextVar`) | ‼️ falla → corregido con global + contexto ✅ |
| f-string dentro de `tr()` | ‼️ no se extrae (0 mensajes) → plantillas con `.format()` ✅ |
| Suite completa de pccpy con el prototipo (idioma `es`) | ✅ 344 tests, 0 fallos |
| Wheel y sdist con el `.mo`; wheel instalado sin `babel` en ejecución | ✅ |
| Constantes de módulo con `N_()` y cambio de idioma en caliente | ✅ |
| Coste: `tr()` ≈ 0,2 µs (es) / 0,5 µs (en) por llamada; primera carga 0,13 ms | ✅ medido (solo se ejecuta al mostrar texto o en rutas de error; `summary()` actual ≈ 17 µs) |

❔ **No verificado:** migración real de los módulos grandes (`msa`, `capability`, `wizard`); Python 3.9–3.10 y 3.12–3.13 (la matriz de CI lo comprobaría); Windows/macOS; `sphinx-intl`; compilación del catálogo en el build; la calidad de las traducciones al inglés (solo se tradujeron 4 textos de prueba).

---

## Desviaciones y hallazgos de la fase 2

- **Movido de la fase 3 a la 2:** `rules.TEST_DESCRIPTIONS` y los textos de la prueba 1 de las cartas (`test1_text`, ahora una plantilla `N_()` con `test1_params`): `ControlChart.summary()` los muestra, así que sin ellos el resumen en inglés quedaba mezclado.
- **Hallazgo:** 6 funciones más devuelven DataFrames con columnas en español (`violations` —hecha—, `pareto`, `oc_curve`, `aoq_curve`, tablas ANOVA de Gage R&R, `kappa_vs_reference`). No estaban en el plan; propuesta de **fase 3b** (misma solución: etiquetas traducibles + `stable=True`).
- **Hallazgo:** algunas cartas guardan parámetros con **clave en español** (`media`, `forma`, `n_puntos`, `sigma_dentro`…); son datos públicos y no se traducen: solo se muestran traducidos en `summary()`.
- **Hallazgo:** `tr()` dentro de un f-string se extrae solo en Python >= 3.12; ahora un test lo prohíbe (el catálogo no debe depender de la versión de Python).
- **Semántica a documentar:** los textos que un resultado guarda al crearse (`DiagnoseResult.issues`, `recommended_snippet`, `WizardResult.rationale`) quedan en el idioma activo en ese momento.

---

## Desviaciones y hallazgos de la fase 3

- **Etiquetas de paneles (`Panel.ylabel`):** se guardan en español (son datos públicos del resultado) marcadas con `N_()` y se traducen solo al dibujar (`plotting.py`), igual que `trend_direction` o las claves de `params`.
- **Asistente:** `WizardResult.rationale` y las preguntas/opciones del árbol siguen en español como dato; `summary()`, `snippet()`, el modo CLI y el widget los muestran traducidos al idioma activo **en el momento de mostrarlos** (no al crear el resultado).
- **Fragmentos de código en inglés:** los nombres de variable de ejemplo (`datos`, `carta`…) pasan a `data`, `chart`…; los tests exigen que sean Python válido y que llamen a la función recomendada.
- **Detector útil:** el test «sin palabras españolas» de los gráficos encontró dos etiquetas de panel (`Cantidad entre eventos`, `Puntaje acumulado`) que se habían escapado de la migración.
- **Mutaciones comprobadas:** quitar `tr()` de una etiqueta de eje, del botón «Volver» o del estado `pendiente` hace fallar los tests; quitar `N_()` lo detecta `make i18n-check` (catálogo desactualizado).

## Desviaciones y hallazgos de la fase 3b

- **Atributos vs métodos:** `anova_table`, `kappa_within` y `kappa_vs_reference` son campos guardados; convertirlos en métodos rompería la API. Se dejan **siempre en español** (datos públicos) y se añaden métodos `anova_frame()`, `kappa_within_frame()` y `kappa_vs_reference_frame()` con cabeceras traducidas y `stable=True`.
- **`pareto()`:** el grupo «Otros» es un valor de los datos; se traduce al crear la tabla (idioma activo en ese momento). `plot_pareto()` lee las columnas por posición para aceptar cualquier idioma.
- **Hojas de Excel:** `KappaVsReferencia` se traduce; la hoja `ANOVA` conserva el nombre. Los tests comparan las hojas por posición, no por nombre.
- **Mutaciones comprobadas:** no traducir columnas, filas, el nombre «Otros» o la hoja de kappa hace fallar los tests.
- **Fallo de CI corregido:** los tests de tablas generaban las hojas de Excel sin comprobar que `openpyxl` (extra opcional) estuviera instalado; en local pasaban y en CI fallaban 62 tests. Ahora las hojas se omiten sin `openpyxl`. Se verificó con una instalación `pip install -e .` sin extras (1840 pasan, 13 omitidos).
- **Segundo fallo de CI corregido:** `kappa_*` difería en el último dígito decimal entre versiones de numpy/scipy (Python 3.10/3.11 vs local); las referencias de tablas comparan ahora etiquetas exactas y números con tolerancia relativa 1e-9 (con control negativo).
