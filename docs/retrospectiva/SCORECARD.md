# SCORECARD — pccpy v0.10.8

> Evaluación por dimensión basada en evidencia verificable.
> Escala 0–5: 0=ausente, 1=rudimentario, 2=funcional, 3=sólido, 4=maduro, 5=excelente.
> Fecha de evaluación: 2026-10-02.

---

## Tabla de puntuaciones

| # | Dimensión | Puntuación | Nivel |
|---|---|---|---|
| 1 | Estructura del repositorio | **4** | Maduro |
| 2 | Diseño de API pública | **4** | Maduro |
| 3 | Validación de entradas | **3** | Sólido |
| 4 | Corrección numérica | **4** | Maduro |
| 5 | Suite de pruebas | **3** *(antes 4)* | Sólido |
| 6 | Tipado estático | **4** | Maduro |
| 7 | Gestión de dependencias | **3** | Sólido |
| 8 | CI/CD | **4** | Maduro |
| 9 | Documentación | **4** | Maduro |
| 10 | Rendimiento | **2** | Funcional |
| 11 | Seguridad | **2** | Funcional |
| 12 | Versionado y releases | **2** *(antes 3)* | Funcional |
| 13 | Comunidad y contribución | **2** | Funcional |
| 14 | Developer Experience (DX) | **3** | Sólido |
| **GLOBAL** | | **3.1** *(44/14 = 3.14; antes 3.4)* | **Sólido** |

### Qué cambió en la segunda pasada (2026-10-02) y por qué

- **Aritmética corregida:** las puntuaciones originales sumaban 46/14 = 3.29, no 3.4.
- **Criterio explícito para un 4:** "ningún bug cerrado sin test de regresión y ningún módulo público < 70 % de cobertura". Hoy se incumple (BUG-01/07/12 sin test; `timeweighted_attr.py` 19 %, `_wizard.py` 62 %) → Suite de pruebas baja a 3.
- **Versionado y releases 3 → 2:** el release v0.10.8 falló en producción (BUG-13) por falta de guarda y versión duplicada.
- **DX 3 → 2 → 3:** bajó a 2 porque `examples/*.py` no ejecutaban (BUG-14); volvió a 3 tras corregirlos y verificar que ambos corren. CLAUDE.md también se actualizó.
- **Afirmación falsa retirada:** "`actions/checkout@v6` no existe". Evidencia en contra: `publish.yml` en el tag `v0.10.7` ya usaba `checkout@v6` y ese release publicó con éxito; el CI de `819ca11` pasó con v6 en los 7 jobs.

---

## Justificación por dimensión

### 1. Estructura del repositorio — 4/5

**HECHOS:**
- `src/` layout correcto (`src/pccpy/`).
- `pyproject.toml` completo: `name`, `version`, `requires-python`, `dependencies`, `optional-dependencies`, `authors`, `classifiers`, URLs.
- `LICENSE` (MIT) presente.
- `.github/workflows/` con tests y publish.
- `benchmarks/`, `examples/`, `docs/` organizados.

**DÉFICITS (-1):** Sin `.github/ISSUE_TEMPLATE/` ni `.github/PULL_REQUEST_TEMPLATE.md`. (CLAUDE.md estaba desactualizado con `src/nombre_anterior`; corregido en la segunda pasada.) `LICENSE` aún dice "Autores de nombre_anterior".

---

### 2. Diseño de API pública — 4/5

**HECHOS:**
- `__all__` completo en `__init__.py` (180 líneas).
- Objetos resultado con `.summary()` y `.plot()` consistentes en todas las áreas.
- Nombres de funciones en snake_case; clases en PascalCase.
- `wizard()` con tres modos (`auto`, `cli`, `widget`) bien diferenciados.
- Funciones `to_excel()` disponibles en todos los objetos resultado.

**DÉFICITS (-1):** EWMA/CUSUM univariados no soportan `stages` (documentado como pendiente en CLAUDE.md). Inconsistencia menor: `WidgetSession.result` es `None` hasta navegación completa (documentado pero puede sorprender).

---

### 3. Validación de entradas — 3/5

**HECHOS:**
- `as_1d()` centralizada con filtrado de NaN/inf y UserWarning (commit `39bd66a`).
- `to_subgroups()` filtra columnas no numéricas automáticamente.
- `capability_analysis()` acepta sin LSL/USL.
- Datos constantes (std=0) → NaN + UserWarning en lugar de ZeroDivisionError.
- `_excel_writer()` centraliza manejo de openpyxl ausente.

**DÉFICITS (-2):** Cobertura de `_data.py` es 72% — hay caminos de validación no testeados (líneas 84-118). No hay tests que simulen openpyxl ausente. No hay tests que verifiquen el mensaje de error de subgroup_size=1 vs. el mensaje interno.

---

### 4. Corrección numérica — 4/5

**HECHOS:**
- Constantes de carta de control (`d2`, `d3`, `c4`, `c5`) calculadas por integración numérica, no tablas (CLAUDE.md regla 2 + `_constants.py`).
- Validación contra Montgomery, papers originales (CLAUDE.md documenta la política).
- Monte Carlo con ≥20 semillas antes de fijar tolerancias (CLAUDE.md regla 2).
- `_sigma.py` con múltiples estimadores documentados.

**DÉFICITS (-1):** Sin comparación formal contra Minitab real (licencia no disponible — documentado explícitamente en CLAUDE.md).

---

### 5. Suite de pruebas — 3/5

**HECHOS:**
- 344 tests pasando (verificado: `344 passed in 33.97s`).
- Cobertura global 90%.
- 17 archivos de test, uno por área temática.
- Fixture `rng` en `conftest.py` para reproducibilidad.
- Tests de stages, Box-Cox, multivariate en archivos dedicados.

**DÉFICITS (-2):** `timeweighted_attr.py` con 19% de cobertura (77 líneas, 62 sin cubrir; 6 funciones públicas EWMA/CUSUM de atributos). `_wizard.py` con 62% (modo widget sin tests). `_data.py` con 72%. Bugs cerrados sin test de regresión (verificado con `grep` en `tests/`): BUG-01, BUG-07, BUG-12; BUG-10 solo parcial. Dos de los tres tienen ya una receta de test probada en `BUG_CATALOG.md` (BUG-01 también por mutación).

---

### 6. Tipado estático — 4/5

**HECHOS:**
- `mypy src/pccpy --ignore-missing-imports` → `Success: no issues found in 25 source files` (verificado).
- `from __future__ import annotations` en módulos principales.
- Anotaciones en funciones públicas.
- 6 errores de mypy corregidos en commit `322a24e`.

**DÉFICITS (-1):** `ignore-missing-imports` oculta potenciales problemas con numpy/scipy stubs. Algunos parámetros usan `Any` en lugar de tipos más precisos.

---

### 7. Gestión de dependencias — 3/5

**HECHOS:**
- Dependencias mínimas: numpy, scipy, pandas, matplotlib con rangos de versión.
- `optional-dependencies` para `dev`, `docs`, `excel`.
- `requires-python = ">=3.9"` declarado.

**DÉFICITS (-2):** Rangos no tienen límite superior (`numpy>=1.22` sin `<3`). Sin `pip audit` en CI. Sin `requirements.txt` ni `lock file` para reproducibilidad exacta.

---

### 8. CI/CD — 4/5

**HECHOS:**
- Matrix Python 3.9–3.13 con `fail-fast: false`.
- Jobs separados: tests, calidad (ruff+mypy), documentación (sphinx-build -W), publish-pypi.
- Actions actualizadas a v6 para Node 24.
- publish.yml con job separado de build y publicación condicionada a tag.

**DÉFICITS (-1):** El pipeline de publicación no verifica lo que publica: sin guarda tag/release == versión del wheel ni `twine check` (BUG-13). `publish.yml` se dispara con `release: published`, no con push de tag. CI no ejecuta `examples/*.py` (BUG-14) ni `pip audit`. *(La afirmación original "`checkout@v6` no existe" era falsa y se retiró; ver arriba.)*

---

### 9. Documentación — 4/5

**HECHOS:**
- Sphinx con tema RTD, MyST, `.readthedocs.yaml`.
- Páginas de referencia API para todas las áreas.
- Tutorial con datos reales (`tutorial_real.md`).
- FAQ, guía de selección, comparativa con Minitab.
- CHANGELOG completo versión a versión.

**DÉFICITS (-1):** Sin página de "Migración desde versión anterior". Esta documentación tenía además errores propios (BUG-11 mal descrito, `checkout@v6`), corregidos en la segunda pasada. `sphinx-build -W` local sobre `main`: `build succeeded`.

---

### 10. Rendimiento — 2/5

**HECHOS:**
- `benchmarks/bench_charts.py` existe (commit `cf704c9`).
- Sin regresión de rendimiento visible.

**DÉFICITS (-3):** Sin métricas de referencia documentadas (tiempo esperado por benchmark). Sin gate de rendimiento en CI. Sin perfilado de los módulos críticos (`capability.py`, `msa.py`).

---

### 11. Seguridad — 2/5

**HECHOS:**
- Sin código que ejecute input de usuario como código (no `eval`, no `exec`).
- Dependencias estándar del ecosistema científico.

**DÉFICITS (-3):** Sin `pip audit` en CI. Sin política de reporte de vulnerabilidades (`SECURITY.md`). Rangos de dependencias sin límite superior (riesgo de breaking change por upgrade automático).

---

### 12. Versionado y releases — 2/5

**HECHOS:**
- Versionado semántico.
- Tags git para releases.
- CHANGELOG detallado.
- CI de publicación a PyPI al publicar un release (`on: release: types: [published]`).
- v0.10.7 publicó correctamente; **v0.10.8 falló** (run `37060818445`, PyPI `400 File already exists`) y se resolvió con `2be31df` (BUG-13).

**DÉFICITS (-3):** Versión en dos lugares (`pyproject.toml:7` y `__init__.py:89`) — desincronización histórica (`fb8fc3d`) y causa del release fallido. Sin guarda tag/release == versión del wheel. Sin `twine check dist/*`. Se declaró "listo para release" sin construir el wheel.

---

### 13. Comunidad y contribución — 2/5

**HECHOS:**
- `CONTRIBUTING.md` presente.
- `LICENSE` MIT.
- Repositorio público en GitHub.

**DÉFICITS (-3):** Sin issue templates. Sin PR template. Sin código de conducta. Sin `SECURITY.md`. CONTRIBUTING.md tuvo referencias obsoletas a `nombre_anterior` (commit `415f412`).

---

### 14. Developer Experience (DX) — 3/5

**HECHOS:**
- `pip install -e ".[dev]"` instala todo en un paso.
- CLAUDE.md con mapa de código, comandos y reglas (reescrito y verificado en la segunda pasada).
- Wizard de selección para usuarios nuevos.

**DÉFICITS (-2):** `examples/` estaban rotos (BUG-14) y la primera pasada los daba como positivos sin ejecutarlos; ya corregidos y verificados, pero CI sigue sin ejecutarlos. Sin `Makefile` ni script de conveniencia. "La instalación en Python 3.9 puede fallar" de la primera pasada es NO VERIFICADO.

---

## Nivel de madurez global: NIVEL 3 — Sólido

**Puntuación media: 3.1 / 5.0** (44/14 = 3.14; en el límite inferior del Nivel 3)

El proyecto es funcional, bien testeado y tiene CI activo. Los déficits principales son:
1. Pipeline de release sin verificación y versión en dos fuentes (BUG-13, ya ocurrió).
2. CI no ejecuta `examples/` (BUG-14 ya corregido, pero puede repetirse).
3. Bugs sin test de regresión y módulos con cobertura < 70 % (`timeweighted_attr.py` 19 %, `_wizard.py` 62 %).
4. Sin auditoría de seguridad en CI.

---

## Dimensión más rezagada y siguiente acción de mayor impacto

**Más rezagada:** hay un empate a 2/5 entre Rendimiento, Seguridad, Versionado y releases y Comunidad. Ninguna está por debajo del resto.

**Desempate por impacto observado:** **Versionado y releases** es la única de las cuatro que ya causó un fallo en producción (release v0.10.8) y la de menor esfuerzo de corrección.

**Siguiente acción de mayor impacto (≈30 min):**
1. Añadir en `publish.yml`, tras el build, la guarda tag/release == versión del wheel y `twine check dist/*`.
2. Pasar la versión a fuente única con `[tool.setuptools.dynamic] version = {attr = "pccpy.__version__"}`.

Ambas piezas se probaron localmente (guarda: exit 1 contra el commit que falló, exit 0 contra `2be31df`; `dynamic`: una edición → wheel 0.10.9). **NO se han ejecutado todavía dentro de GitHub Actions**, así que la primera ejecución real debe revisarse con un release de prueba o un `workflow_dispatch`.

Segunda en la lista (≈10 min): añadir a CI el bucle que ejecuta `examples/*.py`.
