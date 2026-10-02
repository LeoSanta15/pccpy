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
| 5 | Suite de pruebas | **4** | Maduro |
| 6 | Tipado estático | **4** | Maduro |
| 7 | Gestión de dependencias | **3** | Sólido |
| 8 | CI/CD | **4** | Maduro |
| 9 | Documentación | **4** | Maduro |
| 10 | Rendimiento | **2** | Funcional |
| 11 | Seguridad | **2** | Funcional |
| 12 | Versionado y releases | **3** | Sólido |
| 13 | Comunidad y contribución | **2** | Funcional |
| 14 | Developer Experience (DX) | **3** | Sólido |
| **GLOBAL** | | **3.4** | **Sólido** |

---

## Justificación por dimensión

### 1. Estructura del repositorio — 4/5

**HECHOS:**
- `src/` layout correcto (`src/pccpy/`).
- `pyproject.toml` completo: `name`, `version`, `requires-python`, `dependencies`, `optional-dependencies`, `authors`, `classifiers`, URLs.
- `LICENSE` (MIT) presente.
- `.github/workflows/` con tests y publish.
- `benchmarks/`, `examples/`, `docs/` organizados.

**DÉFICITS (-1):** CLAUDE.md desactualizado con referencias a `src/spyc` (evidencia: archivo activo). Sin `.github/ISSUE_TEMPLATE/` ni `.github/PULL_REQUEST_TEMPLATE.md`.

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

### 5. Suite de pruebas — 4/5

**HECHOS:**
- 344 tests pasando (verificado: `344 passed in 33.97s`).
- Cobertura global 90%.
- 17 archivos de test, uno por área temática.
- Fixture `rng` en `conftest.py` para reproducibilidad.
- Tests de stages, Box-Cox, multivariate en archivos dedicados.

**DÉFICITS (-1):** `timeweighted_attr.py` con 19% de cobertura (77 líneas, 62 sin cubrir). `_wizard.py` con 62% (modo widget sin tests). `_data.py` con 72%.

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

**DÉFICITS (-1):** `actions/checkout@v6` no existe actualmente (versión inválida — GitHub Actions actualmente en v4). CI puede fallar por versión de action incorrecta en un nuevo repo.

---

### 9. Documentación — 4/5

**HECHOS:**
- Sphinx con tema RTD, MyST, `.readthedocs.yaml`.
- Páginas de referencia API para todas las áreas.
- Tutorial con datos reales (`tutorial_real.md`).
- FAQ, guía de selección, comparativa con Minitab.
- CHANGELOG completo versión a versión.

**DÉFICITS (-1):** CLAUDE.md desactualizado (referencias `spyc`). Sin página de "Migración desde versión anterior".

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

### 12. Versionado y releases — 3/5

**HECHOS:**
- Versionado semántico.
- Tags git para releases.
- CHANGELOG detallado.
- CI de publicación a PyPI en push de tag.

**DÉFICITS (-2):** Versión en dos lugares (`pyproject.toml` y `__init__.py`) — desincronización histórica documentada. Sin `twine check dist/*` en CI. `pip show pccpy` reportó 0.10.6 mientras `__version__` era 0.10.8 (desincronización de instalación).

---

### 13. Comunidad y contribución — 2/5

**HECHOS:**
- `CONTRIBUTING.md` presente.
- `LICENSE` MIT.
- Repositorio público en GitHub.

**DÉFICITS (-3):** Sin issue templates. Sin PR template. Sin código de conducta. Sin `SECURITY.md`. CONTRIBUTING.md tuvo referencias obsoletas a `spyc` (commit `415f412`).

---

### 14. Developer Experience (DX) — 3/5

**HECHOS:**
- `pip install -e ".[dev]"` instala todo en un paso.
- CLAUDE.md con mapa de código y reglas de trabajo.
- Ejemplos en `examples/` documentados.
- Wizard de selección para usuarios nuevos.

**DÉFICITS (-2):** CLAUDE.md desactualizado (comandos incorrectos para el nombre actual). Sin `Makefile` ni script de conveniencia. La primera instalación en Python 3.9 puede fallar si el entorno no está configurado.

---

## Nivel de madurez global: NIVEL 3 — Sólido

**Puntuación media: 3.4 / 5.0**

El proyecto es funcional, bien testeado y tiene CI activo. Los déficits principales son:
1. CLAUDE.md desactualizado (riesgo operacional inmediato).
2. Módulo `timeweighted_attr.py` sin cobertura de tests.
3. Gestión de versión con dos fuentes de verdad.
4. Sin auditoría de seguridad en CI.
