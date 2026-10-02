# PLAYBOOK — Madurez de librería Python (niveles 0→5)

> Checklist portable e independiente del dominio.
> Para cada nivel: criterios medibles y comandos de verificación.

---

## Niveles de madurez

| Nivel | Nombre | Descripción |
|---|---|---|
| **0** | Prototipo | Código que funciona localmente, sin estructura |
| **1** | Librería básica** | Empaquetable, instalable, con tests mínimos |
| **2** | Calidad verificable | CI activo, linter, tipos, cobertura razonada |
| **3** | Lista para producción | API estable, docs completas, casos borde cubiertos |
| **4** | Publicada y mantenida | PyPI, versiones semánticas, changelog, comunidad |
| **5** | Excelencia sostenida | Benchmarks, seguridad, soporte multi-versión verificado |

---

## NIVEL 0 → 1: Estructura básica

### Dimensión: Estructura del repositorio

- [ ] `src/` layout (no flat)
- [ ] `pyproject.toml` con `name`, `version`, `requires-python`, `dependencies`
- [ ] `LICENSE` presente
- [ ] `.gitignore` configurado (excluye `__pycache__`, `dist/`, `.egg-info/`)
- [ ] `src/<paquete>/__init__.py` con `__version__` y `__all__`

**Verificación:**
```bash
python -c "import <paquete>; print(<paquete>.__version__)"
pip install -e . && python -c "import <paquete>"
```

**Criterio "hecho":** la instalación en venv limpio no da error.

---

### Dimensión: Tests mínimos

- [ ] `tests/` con al menos un archivo por módulo público
- [ ] `pytest` configurado en `pyproject.toml` (`testpaths`, `addopts`)
- [ ] Fixture de semilla aleatoria (`rng = np.random.default_rng(seed)`) en `conftest.py`
- [ ] Tests pasan en venv limpio

**Verificación:**
```bash
python -m pytest tests/ -q
```

**Criterio "hecho":** 0 fallos, 0 errores.

---

## NIVEL 1 → 2: Calidad verificable

### Dimensión: Linter

- [ ] `ruff` configurado en `pyproject.toml` con `line-length` y `target-version`
- [ ] `ruff check src/` pasa sin errores
- [ ] Reglas mínimas activadas: `F` (pyflakes), `E9` (errores de sintaxis), `B` (bugbear), `I` (isort)

**Verificación:**
```bash
python -m ruff check src/
```

**Criterio "hecho":** `All checks passed!`

---

### Dimensión: Tipado estático

- [ ] Anotaciones de tipo en todas las funciones públicas (parámetros y retorno)
- [ ] `mypy src/<paquete> --ignore-missing-imports` sin errores
- [ ] `from __future__ import annotations` en archivos con tipos forward-reference

**Verificación:**
```bash
python -m mypy src/<paquete> --ignore-missing-imports
```

**Criterio "hecho":** `Success: no issues found in N source files`

---

### Dimensión: Cobertura

- [ ] `pytest-cov` en dependencias de dev
- [ ] Cobertura global >= 85%
- [ ] Sin módulos públicos con cobertura < 70%
- [ ] `--cov-report=term-missing` en CI para identificar líneas no cubiertas

**Verificación:**
```bash
python -m pytest --cov=<paquete> --cov-report=json:/tmp/cov.json -q
python - <<'EOF'
import json
d = json.load(open("/tmp/cov.json"))["files"]
print({k: round(v["summary"]["percent_covered"]) for k, v in d.items() if v["summary"]["percent_covered"] < 70} or "OK")
EOF
```

**Criterio "hecho":** `TOTAL` >= 85% y el script imprime `OK` (ningún módulo público < 70%). `--cov-fail-under` solo controla el total: un 90% global puede esconder un módulo al 19%.
**Adopción en un repo existente:** si ya hay módulos < 70%, trátalos como trinquete (no pueden bajar) y regístralos como deuda; no declares una regla que el repo ya incumple.
**Un bug cerrado sin test de regresión no cuenta como cerrado.** Prueba que el test falla si el bug vuelve (mutación manual de una línea).

---

### Dimensión: CI básico

- [ ] GitHub Actions (o equivalente) activo en `push` y `pull_request`
- [ ] Jobs: tests, linter, tipos
- [ ] Matrix multi-versión Python (mínimo versión mínima declarada + versión actual)
- [ ] `fail-fast: false` en la matrix para ver todos los fallos

**Verificación:**
```bash
cat .github/workflows/tests.yml | grep "python-version"
```

**Criterio "hecho":** CI pasa en verde en la versión mínima declarada en `requires-python`.

---

## NIVEL 2 → 3: Lista para producción

### Dimensión: Validación de entradas

- [ ] Capa de ingesta centralizada (ej. función `_validate()` o `as_1d()`)
- [ ] Manejo explícito de: NaN/inf, arrays vacíos, tipos incorrectos, casos degenerados (n=0, sigma=0)
- [ ] Dependencias opcionales: `ImportError` capturado con mensaje `pip install X`
- [ ] Estado global (matplotlib rcParams, warnings): usar context managers

**Verificación:**
```bash
python -c "import <paquete>; <paquete>.funcion_publica([])"  # debe dar ValueError claro
python -c "import numpy as np; import <paquete>; <paquete>.funcion_publica(np.array([np.nan]))"
```

**Criterio "hecho":** errores con mensajes accionables; no `ValueError` ni `TypeError` de numpy.

---

### Dimensión: Casos borde documentados

- [ ] Docstring de cada función pública incluye sección `Raises` con condiciones
- [ ] Tests parametrizados que cubren: vacío, NaN, n=1, n=2, valores extremos
- [ ] Comportamiento con datos constantes (std=0) definido y testeado

**Verificación:**
```bash
python -m pytest tests/ -k "nan or edge or empty or zero" -v
```

**Criterio "hecho":** al menos 1 test de caso borde por función pública.

---

### Dimensión: Documentación

- [ ] README con: descripción, instalación, ejemplo mínimo funcional, referencia a docs completas
- [ ] Docstrings completos en todas las funciones públicas (parámetros, retorno, raises, ejemplo)
- [ ] CHANGELOG.md con entradas por versión
- [ ] Sphinx (o equivalente) construye sin warnings con `-W`

- [ ] Cada símbolo público tiene UNA directiva autodoc canónica; si hay dos páginas, la procesada primero lleva `:no-index:`
- [ ] Docstrings numpy sin `shape (n,)` cuando existe un atributo `n` documentado (usa `array-like`)

**Verificación:**
```bash
sphinx-build -b html -W docs/source docs/build
grep -r "TU_USUARIO\|PLACEHOLDER\|TODO" README.md docs/ --exclude-dir=retrospectiva --exclude-dir=_build --exclude-dir=build
```

**Criterio "hecho":** build de docs sin errores ni warnings; README sin placeholders.
**Caso real:** añadir dos páginas de referencia produjo 18 warnings ("duplicate object description" + una referencia ambigua `n`); `-W` en CI los detuvo antes del release.

---

### Dimensión: Consistencia de API

- [ ] Un único archivo de ingesta de datos (no lógica duplicada)
- [ ] Todos los errores de usuario son `ValueError` o `TypeError` con mensaje en español (o el idioma del proyecto)
- [ ] Nombres consistentes: snake_case para funciones, PascalCase para clases
- [ ] `__all__` completo en `__init__.py`

---

## NIVEL 3 → 4: Publicada y mantenida

### Dimensión: Versioning y releases

- [ ] Versionado semántico (MAJOR.MINOR.PATCH)
- [ ] Una sola fuente de verdad para la versión: literal en `__init__.py` +
      `[tool.setuptools.dynamic] version = {attr = "<paquete>.__version__"}` (probado: una
      edición → wheel con la versión nueva). Evita `importlib.metadata` dentro de
      `__init__.py`: la metadata se congela al instalar y diverge del código.
- [ ] Tags git para cada release (`vX.Y.Z`)
- [ ] CI de publicación a PyPI (con el trigger que uses: `release: published` o push de tag)
- [ ] Guarda en el workflow de publicación: tag/release == versión del wheel construido
- [ ] `twine check dist/*` en CI antes de publicar
- [ ] "Listo para release" se declara solo tras construir el wheel y ver su versión

**Verificación:**
```bash
python -m build --wheel && ls dist/                     # el nombre del wheel muestra la versión
grep -n '^version\|^__version__' pyproject.toml src/<paquete>/__init__.py   # no debe haber dos literales
V=$(python -c "import glob,re;print(re.search(r'-(\d[^-]*)-py', glob.glob('dist/*.whl')[0]).group(1))")
[ "${TAG#v}" = "$V" ] && echo OK || echo "tag != wheel"   # TAG = tag/release a publicar
git tag --list | grep "^v"
```

**Criterio "hecho":** el wheel construido tiene la versión del tag; existe tag por cada versión publicada; la guarda falla si no coinciden.
**Caso real:** un tag creado antes de subir la versión produjo artefactos de la versión anterior y PyPI respondió `400 File already exists`.

---

### Dimensión: Soporte multi-versión Python verificado

- [ ] CI matrix cubre todas las versiones en `classifiers` de `pyproject.toml`
- [ ] Sin uso de sintaxis/stdlib no disponible en la versión mínima
- [ ] Tests pasan en la versión más antigua soportada

**Verificación:**
```bash
python -m pytest tests/ -q  # en Python==versión_mínima
```

**Criterio "hecho":** 0 fallos en Python mínimo.

---

### Dimensión: Developer Experience

- [ ] `pip install -e ".[dev]"` instala todo lo necesario en un paso
- [ ] CLAUDE.md (o CONTRIBUTING.md) con comandos exactos para test/lint/tipos/build
- [ ] Sin placeholders activos en documentación de contribución
- [ ] Ejemplos ejecutables (`examples/`) que corren sin error

**Verificación:**
```bash
# `python examples/*.py` solo ejecutaría el primero: usa un bucle
for f in examples/*.py; do MPLBACKEND=Agg python "$f" >/dev/null || echo "FALLA $f"; done
grep -rIln "nombre_viejo\|TU_USUARIO\|PLACEHOLDER" . --exclude-dir=.git --exclude-dir=build --exclude-dir=_build --exclude-dir=retrospectiva --exclude=CHANGELOG.md --exclude=CLAUDE.md
```

**Criterio "hecho":** todos los ejemplos corren (idealmente en CI); el `grep` no devuelve nada (incluye `examples/`, CI y LICENSE, no solo la documentación).
**Caso real:** tras un renombre, los dos scripts de `examples/` conservaron `import <nombre_viejo>` y fallaron durante varias versiones sin que ningún test lo notara.

---

## NIVEL 4 → 5: Excelencia sostenida

### Dimensión: Rendimiento

- [ ] Benchmarks documentados para las operaciones críticas
- [ ] `benchmarks/` con scripts reproducibles
- [ ] Sin regresiones de rendimiento entre versiones mayores

**Verificación:**
```bash
python benchmarks/bench_charts.py  # o equivalente
```

---

### Dimensión: Seguridad

- [ ] Sin dependencias con CVEs conocidas (`pip audit`)
- [ ] Dependencias fijadas en rangos (no `>=0.1`, sino `>=1.22,<3`)
- [ ] Sin datos sensibles en el repositorio

**Verificación:**
```bash
pip audit
```

---

### Dimensión: Comunidad

- [ ] CONTRIBUTING.md con guía de contribución
- [ ] Issue templates en `.github/`
- [ ] Código de conducta
- [ ] Tiempo de respuesta a issues < 7 días (mantenimiento activo)

---

## Checklist de "terminado" para un PR

Antes de mergear cualquier PR:
```bash
# 1. Tests completos
python -m pytest tests/ -q

# 2. Sin fallos de linter (mismo comando que CI)
python -m ruff check src/

# 3. Sin fallos de tipos
python -m mypy src/<paquete> --ignore-missing-imports

# 4. Build limpio (aislado, como CI)
python -m build --wheel

# 5. Sin referencias obsoletas
grep -rIln "nombre_antiguo\|TU_USUARIO\|PLACEHOLDER" . --exclude-dir=.git --exclude-dir=build --exclude-dir=_build --exclude-dir=retrospectiva --exclude=CHANGELOG.md --exclude=CLAUDE.md

# 6. Cobertura no cayó
python -m pytest --cov=<paquete> --cov-fail-under=85 -q

# 7. Docs y ejemplos
sphinx-build -b html -W docs/source docs/build
for f in examples/*.py; do MPLBACKEND=Agg python "$f" >/dev/null || echo "FALLA $f"; done

# 8. Si el PR corrige un bug: ¿hay test de regresión y ficha en BUG_CATALOG.md?
```

## Preparación para desarrollo con agentes de IA

Checklist verificable (cada ítem se comprobó en un repo real, ver `SCORECARD.md`):

- [ ] `CLAUDE.md` actualizado: comandos reales, definición de "terminado", reglas, deuda conocida
- [ ] `AGENTS.md` mínimo que apunta a `CLAUDE.md` (otros agentes no leen `CLAUDE.md`)
- [ ] `Makefile`/`nox` con un único `check` (lint + tipos + tests + build + docs + ejemplos) y `check-fast`
- [ ] `.claude/settings.json` con permisos para los comandos de verificación y `git` de solo lectura
- [ ] Hook `SessionStart` (solo si `CLAUDE_CODE_REMOTE=true`): instala dependencias, idempotente, síncrono
- [ ] Hook `Stop`: si hay cambios en código, corre `check-fast`; exit 2 si falla; respeta `stop_hook_active`
- [ ] Plantilla de PR con el checklist de verificación y `CODEOWNERS`
- [ ] `.gitignore` cubre artefactos de build/docs/cobertura (que no aparezcan como cambios sin seguimiento)
- [ ] `py.typed` en el paquete y en `package-data` (el wheel lo contiene)
- [ ] Protección de la rama por defecto (CI obligatorio antes de mergear): se comprueba en la configuración de GitHub, no en el repo

**Verificación:**
```bash
make check                                              # exit 0
CLAUDE_CODE_REMOTE=true .claude/hooks/session-start.sh  # exit 0
python -c "import json;json.load(open('.claude/settings.json'))"
echo '{"stop_hook_active": true}' | .claude/hooks/verify-before-stop.sh   # exit 0 (no bucle)
python -c "import zipfile,glob;print([n for n in zipfile.ZipFile(glob.glob('dist/*.whl')[0]).namelist() if 'py.typed' in n])"
```
**Prueba del hook Stop:** inyecta un fallo (p. ej. `import os` sin usar) en una copia del repo y comprueba que el hook devuelve exit 2 con el error; con `stop_hook_active=true` debe devolver 0.
**Cuidado con el hook de inicio:** en una sesión web `CLAUDE_CODE_REMOTE` ya vale `true`, así que para probar el salto local hay que usar `env -u CLAUDE_CODE_REMOTE`.

## Meta-regla: las reglas también se prueban

Antes de adoptar una regla o un comando de verificación, ejecútalo contra el
propio repo. En esta revisión, tres "reglas" fallaron al probarlas: un `ruff
--select ...,S` que el repo no pasa (`S101`), un `grep` de referencias obsoletas
que coincidía con el propio CLAUDE.md, y una recomendación de versión
(`importlib.metadata`) que se queda obsoleta en instalaciones editables.
