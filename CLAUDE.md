# pccpy — contexto para Claude Code

Léelo completo antes de tocar código: resume convenciones, estado verificado y
deuda conocida para no repetir decisiones ni romper algo que ya funciona.
Las lecciones y el catálogo de bugs viven en `docs/retrospectiva/`.

## Qué es pccpy

Librería Python de Control Estadístico de Procesos (SPC) que replica la
funcionalidad de Minitab: cartas de control (univariadas y multivariadas),
capacidad, normalidad, Pareto, MSA/Gage R&R, muestreo de aceptación,
intervalos de tolerancia, `diagnose()` y `wizard()`. Todo el código visible al
usuario (docstrings, errores, salidas) está **en español**.

## Estado actual (verificado el 2026-10-02)

- Versión **0.12.1** (`pyproject.toml` y `src/pccpy/__init__.py`; ver R-05).
- **344 pruebas** pasando, **90 %** de cobertura global, Python `>=3.9`.
- Repo: `LeoSanta15/pccpy`. Publicado en PyPI vía Trusted Publisher (OIDC).
- CI: `.github/workflows/tests.yml` (tests 3.9–3.13, calidad = ruff + mypy,
  documentación = `sphinx-build -W`) y `publish.yml` (se dispara con
  **release publicada**, no con un push de tag).
- Detalle versión por versión: `CHANGELOG.md` (no lo dupliques aquí).

## Comandos estándar (los mismos que corre CI)

Atajo: `make check` corre todo lo de abajo (lint, tipos, tests, build, docs, ejemplos);
`make check-fast` = lint + tipos + tests + catálogos de traducción; `make release-check TAG=vX.Y.Z` verifica tag == versión del wheel.

```bash
pip install -e ".[dev,docs,excel]"
python -m pytest tests/ -q
python -m ruff check src/                      # usa la config de pyproject (= CI)
python -m mypy src/pccpy --ignore-missing-imports
python -m build --wheel                        # build aislado, como CI
sphinx-build -b html -W docs/source docs/build # si tocaste código público, docstrings o docs/
for f in examples/*.py; do MPLBACKEND=Agg python "$f" >/dev/null || echo "FALLA $f"; done
```

## Definición de "terminado"

1. `pytest -q` → 0 fallos. 2. `ruff check src/` → `All checks passed!`.
3. `mypy` → `Success`. 4. `python -m build --wheel` → `Successfully built`.
5. Cobertura global >= 85 %; módulo nuevo o modificado >= 70 %; ningún módulo
   puede bajar su cobertura actual (deuda: ver "Deuda técnica").
6. `sphinx-build -W` sin warnings si se tocó código público o docs.
7. Todo bug corregido trae test de regresión y ficha en `BUG_CATALOG.md`.
8. `CHANGELOG.md` y este archivo actualizados si cambió funcionalidad o un comando.

## Reglas de trabajo (no negociables)

- **R-01 Cambios quirúrgicos.** Sigue `/mnt/skills/user/karpathy-guidelines/SKILL.md`
  si existe. No reescribas módulos para añadir una función; imita a los vecinos.
- **R-02 Validar contra referencia independiente.** Todo resultado numérico se
  contrasta con una fuente externa (Montgomery, Minitab publicado, cálculo
  manual, `scipy`/`statsmodels`, Monte Carlo con **>= ~20 semillas**). Nunca
  contra la salida de pccpy. No inventes comparaciones con Minitab real: anota
  la decisión en el README ("Notas sobre diferencias posibles con Minitab").
- **R-03 Español** en docstrings, `ValueError`/`UserWarning`, columnas de
  DataFrame y texto de gráficos. Nombres de funciones: snake_case inglés.
- **R-04 Checkpoint incremental:** construir, probar (suite + wheel), commit.
  **El tag y el release los crea el usuario a mano** (decisión explícita suya);
  Claude no crea tags ni releases.
- **R-05 Versión: una sola fuente.** Hoy está duplicada (`pyproject.toml` +
  `__init__.py`): al subir versión edita **ambos** y verifica con
  `grep -n '^version\|^__version__' pyproject.toml src/pccpy/__init__.py`.
  Destino probado en copia: quitar `version` de `[project]`, añadir
  `dynamic = ["version"]` y `[tool.setuptools.dynamic] version = {attr = "pccpy.__version__"}`.
  No uses `importlib.metadata.version()` para `__version__`: la metadata se
  congela al instalar y queda obsoleta en instalaciones editables.
- **R-06 "Listo para release" solo si:** (a) la versión de `pyproject.toml` y
  `__init__.py` == entrada superior de `CHANGELOG.md`; (b) `python -m build --wheel`
  produce `pccpy-<esa versión>-*.whl`. El release v0.10.8 falló (PyPI `400 File
  already exists`) porque se etiquetó con la versión sin subir (BUG-13).
- **R-07 Dependencias opcionales** con mensaje accionable (`pip install pccpy[excel]`):
  patrón en `_excel_writer()` (`src/pccpy/_data.py`). Test: `monkeypatch.setitem(sys.modules, "openpyxl", None)`.
- **R-08 No contaminar estado global:** gráficos dentro de `plt.rc_context({})`,
  warnings temporales dentro de `warnings.catch_warnings()`. Test: comparar
  `dict(matplotlib.rcParams)` antes y después de `.plot()`.
- **R-09 Ingesta centralizada:** datos de usuario pasan por `as_1d()` /
  `to_subgroups()` (`_data.py`). Antes de endurecer una validación base, `grep`
  las llamadas internas; usa escape-hatch explícito (`_allow_size_1=True`).
- **R-10 Referencias obsoletas:** tras un renombre o antes de un release corre
  `grep -rIln "<nombre_viejo>\|TU_USUARIO\|PLACEHOLDER" . --exclude-dir=.git --exclude-dir=build --exclude-dir=_build --exclude-dir=retrospectiva --exclude=CHANGELOG.md --exclude=CLAUDE.md`
  (cubre `examples/`, CI y `LICENSE`). Debe salir vacío. Sustituye `<nombre_viejo>` por el nombre anterior tras un renombre.
- **R-11 Tests obligatorios:** cada función pública nueva tiene test de caso
  borde (vacío, NaN/inf, n mínimo, parámetros opcionales ausentes, std=0) y
  todo bug corregido tiene test de regresión que **falla** si el bug vuelve.
- **R-12 Sphinx:** un símbolo = una directiva autodoc canónica. Si dos páginas
  documentan el mismo símbolo, la procesada primero lleva `:no-index:`; verifica
  con `sphinx-build -W`. En docstrings numpy no escribas `shape (n,)` si existe
  un atributo `n` (referencia ambigua): usa `array-like`.
- **R-13 Ejemplos ejecutables** (corregidos y verificados el 2026-10-02): `examples/*.py` deben correr sin error antes de
  cada release (comando en "Comandos estándar").
- **R-14 CI en versión mínima:** la matrix de `tests.yml` incluye 3.9; un PR no
  se mergea con CI en rojo.
- **R-15 No repetir bugs:** antes de tocar validación de entrada, casos borde,
  imports opcionales, autodoc o releases, lee `docs/retrospectiva/BUG_CATALOG.md`.
  Si un bug reaparece: test de regresión, actualizar catálogo, reforzar la regla.
- **R-17 Texto visible traducible `[test]`.** Todo mensaje de `raise`/`warnings.warn` es `tr("texto literal")` o `tr("… {x} …").format(x=x)` (marcadores con nombre, iguales en todos los idiomas; nunca un f-string dentro de `tr()`); nadie asigna `tr`/`N_`. Tras cambiar un texto: `make i18n-update`, traducir en `locale/en/…/pccpy.po`, `make i18n-compile` (`make i18n-check` lo exige el CI). Comprobado por `tests/test_i18n_errores.py`. Los tests no pueden depender de extras opcionales (`openpyxl`): el CI no instala `excel`; usa `pytest.importorskip` o `find_spec` (la fase 3b lo rompió en CI porque local sí tenía `openpyxl`; verifica con `pip install -e .` sin extras).
- **R-16 Reglas probadas:** antes de añadir una regla a este archivo, ejecuta su
  comando contra este repo y registra el resultado (una regla propuesta con
  `ruff --select F,E9,B,I,S` falló: `S101` en `acceptance.py:692`).

## Infraestructura para agentes (verificada el 2026-10-02)

- `.claude/settings.json`: permisos para `make`, `pytest`, `ruff`, `mypy`, `build`, `sphinx` y `git` de solo lectura.
- `.claude/hooks/session-start.sh`: en sesiones web instala `.[dev,docs,excel]` (síncrono, idempotente).
- `.claude/hooks/verify-before-stop.sh` (hook `Stop`): si hay cambios en `src/`, `tests/` o `pyproject.toml`, corre `make check-fast`; si falla, bloquea el cierre (exit 2) y devuelve el error. Respeta `stop_hook_active` para no entrar en bucle.
- `AGENTS.md` apunta a este archivo; `.github/PULL_REQUEST_TEMPLATE.md` y `CODEOWNERS`; `py.typed` incluido en el wheel.

## Internacionalización (en curso; plan en `docs/planes/PLAN_MULTILENGUAJE.md`)

- Idioma fuente: **español**; adicional: `en`. Mecanismo: `gettext` de la biblioteca estándar (`src/pccpy/_i18n.py`); `babel` solo en desarrollo.
- API: `pccpy.set_language()`, `get_language()`, `language()` (contexto) y `available_languages()`; variable `PCCPY_LANG`. Un idioma inexistente lanza `ValueError`.
- Textos: `tr("…")` se traduce al mostrar; `N_("…")` marca constantes de módulo (se traducen con `tr()` al usarlas). Los f-strings **no** se pueden traducir: usa `tr("… {x} …").format(x=x)`.
- Comandos: `make i18n-update` (extraer + actualizar `.po`), `make i18n-compile` (los `.mo` se versionan) y `make i18n-check` (lo exige el CI).
- Estado por fases (una rama y PR por fase): ver la tabla de `docs/planes/PLAN_MULTILENGUAJE.md`. Fases 0 a 3b hechas (mecanismo, errores/avisos, `summary()` y `to_frame()`, gráficos y `wizard`, otras tablas); fases 4 y 5 hechas (documentación y README en inglés, glosario, guía `docs/source/traducir.md`, versión 0.11.0); falta la revisión humana del inglés y el tag.
- Fase I y fechas: `phase_one()` (`src/pccpy/phase1.py`) y las etiquetas de eje (`src/pccpy/_labels.py`, decorador `@con_etiquetas` en las funciones de cartas: toda carta nueva con datos de entrada debe llevarlo; `tests/test_fase1.py`, `tests/test_fechas.py`).
- Validación: `src/pccpy/validation.py` (`run_validation()`, `python -m pccpy.validation`) contrasta la biblioteca con referencias independientes (no con Minitab). Toda función numérica nueva debería sumar una comprobación con su referencia; cualquier cambio de un valor esperado se justifica en el CHANGELOG. La validación ya encontró dos errores reales (Cg del Tipo 1 y tabla Z1.4).
- Documentación en inglés: catálogos en `docs/locales/en` (uno por página, incluida la API); tras cambiar un `.md`/`.rst` o un docstring, `make docs-update`, traduce los `msgstr` nuevos y `make docs-check docs-en`. En páginas Markdown, los roles de Sphinx traducidos van con sintaxis MyST (`{func}`x``). `README_en.md` se mantiene a mano junto a `README.md` (`tests/test_docs_i18n.py` comprueba su estructura).
- `to_frame(stable=True)` da claves canónicas en inglés (no cambian con el idioma); sin `stable`, cabeceras en el idioma activo. Lo mismo vale para `pareto`, `oc_curve`, `aoq_curve`, `anova_frame` y `kappa_*_frame` (golden `tests/golden/i18n_tablas_es.json`). Al añadir filas o columnas, define su clave estable (los tests comparan con `tests/golden/i18n_stable.json`).
- Los textos de `summary()` se comprueban contra `tests/golden/i18n_es.json` (generado con el código previo a la migración; **no se regenera** salvo cambio deliberado del español) y con invariantes es/en (`tests/test_i18n_resumenes.py`).
- No pongas `tr()` dentro de un f-string: Babel solo lo extrae en Python >= 3.12 (el catálogo cambiaría según la versión).
- El marcador se llama `tr`, no `_`: 8 funciones usan `_` como variable y lanzan errores (un `_("…")` ahí fallaría solo en la ruta de error).

## Mapa del código

```
src/pccpy/
  __init__.py        # API pública: todo lo exportado vive en __all__
  _constants.py      # d2, d3, c4, c5, A2..B4 por integración numérica
  _data.py           # as_1d, to_subgroups, stage_slices, _excel_writer
  _sigma.py          # estimadores de sigma
  _diagnose.py       # diagnose() y DiagnoseResult
  _i18n.py           # idioma: tr(), N_(), set_language(), language()… (catálogos en locale/)
  _wizard.py         # wizard(), WizardResult, WidgetSession
  rules.py           # las 8 pruebas de causas especiales de Minitab
  results.py         # Panel, ControlChart, MultivariateChart
  charts/
    _engine.py       # build_chart(): motor común (etapas + pruebas)
    variables.py     # I-MR, Xbar-R, Xbar-S
    attributes.py    # P, NP, C, U, Laney P'/U'
    timeweighted.py  # EWMA, CUSUM (sin 'stages')
    timeweighted_attr.py  # EWMA/CUSUM de atributos (cobertura 19 %)
    run_chart.py     # carta de corridas
    advanced.py      # MA, Z-MR, I-MR-R/S, Zona, G, T
  multivariate.py    # T², |S|, MEWMA, MCUSUM
  capability.py      # capacidad normal/no normal/Box-Cox, sixpack
  msa.py             # MSA / Gage R&R / acuerdo por atributos
  acceptance.py      # muestreo de aceptación
  tolerance.py       # intervalos de tolerancia
  precontrol.py      # pre-control
  normality.py       # Anderson-Darling, Shapiro, D'Agostino
  plotting.py        # plot_control_chart, plot_capability, ...
  quality_tools.py   # pareto, plot_pareto
tests/               # un archivo por área; fixture `rng` en conftest.py
examples/            # ejemplo_basico.py, ejemplo_avanzado.py
docs/source/         # Sphinx: referencia/*.rst usa autodoc (ver R-12)
docs/retrospectiva/  # LESSONS_LEARNED, BUG_CATALOG, PLAYBOOK, SCORECARD, ...
```

**Patrón para una carta nueva:** usa `charts/advanced.py` (`g_chart`) o
`multivariate.py` (`mcusum_chart`) como plantilla; toda carta termina en
`build_chart(kind, n_puntos, stages, stage_fn, tests, test_params)`. No
reimplementes el bucle de etapas.

## Pendientes conocidos (verificados contra el código el 2026-10-02)

1. Prueba de Benneyan en la carta G (`charts/advanced.py:317` dice que no la incluye).
2. `stages` en `ewma_chart`/`cusum_chart` (`charts/timeweighted.py` no lo soporta).
3. Transformación de Johnson (no hay código en `src/`).
4. Box-Cox en cartas univariadas y duraciones = 0 en la carta T: NO VERIFICADO.

## Deuda técnica detectada en la revisión del 2026-10-02

- Sin test de regresión: BUG-01 (zonas en cartas R/S/MR), BUG-07 (openpyxl ausente), BUG-12 (aislamiento de `rcParams`). Recetas probadas en `BUG_CATALOG.md`.
- Cobertura total 97 % (ningún módulo bajo 90 %). Lo menos cubierto: `_wizard.py` (94 %, ramas del widget), `acceptance.py` (96 %, búsquedas Dodge-Romig sin solución) y las rutas de `openpyxl` ausente en `_data.py`.
- Z1.9: la tabla incluida NO reproduce la norma (planes que aceptan casi todo; `acceptance_sampling_variables` avisa). Falta sustituirla por las tablas A-2 y B-1 de ANSI/ASQ Z1.9, que no se pudieron obtener (sin acceso a la norma). Z1.4 usa ya la tabla I (niveles I/II/III) y II-A; no incluye los niveles especiales S-1 a S-4 ni inspección rigurosa/reducida ni doble/múltiple.
- `publish.yml` no verifica que la versión del wheel coincida con el release ni corre `twine check`.
- `ruff --select ...,S` falla por `assert` en `acceptance.py:692` (S101).
