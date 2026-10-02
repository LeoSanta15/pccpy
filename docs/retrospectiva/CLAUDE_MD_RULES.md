# REGLAS PARA CLAUDE.md — Bloque listo para pegar

> Copia este bloque en el CLAUDE.md de cualquier repo Python.
> Sustituye `<paquete>` por el nombre real del módulo Python (ej. `pccpy`).
> Sustituye `<nombre_pypi>` por el nombre en PyPI (puede ser distinto del módulo).

---

```markdown
## Comandos estándar

```bash
# Tests
python -m pytest tests/ -q

# Linter: el MISMO comando que CI (config en pyproject). No uses un --select
# distinto sin probarlo: F,E9,B,I,S falló en este repo (S101, acceptance.py:692).
python -m ruff check src/

# Tipos
python -m mypy src/<paquete> --ignore-missing-imports

# Build
python -m build --wheel

# Tests con cobertura
python -m pytest --cov=<paquete> --cov-report=term-missing -q

# Docs sin warnings
sphinx-build -b html -W docs/source docs/build

# Ejemplos ejecutables
for f in examples/*.py; do MPLBACKEND=Agg python "$f" >/dev/null || echo "FALLA $f"; done

# Cobertura por módulo (lista los módulos < 70 %; salida vacía = OK)
python -m pytest -q --cov=<paquete> --cov-report=json:/tmp/cov.json >/dev/null && python - <<'EOF'
import json
d = json.load(open("/tmp/cov.json"))["files"]
print({k: round(v["summary"]["percent_covered"]) for k, v in d.items() if v["summary"]["percent_covered"] < 70} or "OK")
EOF

# Referencias obsoletas (probado: sin falsos positivos con estas exclusiones)
grep -rIln "nombre_viejo\|PLACEHOLDER" . --exclude-dir=.git --exclude-dir=build --exclude-dir=_build --exclude-dir=retrospectiva --exclude=CHANGELOG.md --exclude=CLAUDE.md || echo "OK"
```

## Definición de "terminado"

Una tarea está **terminada** solo cuando:
1. `pytest -q` → 0 fallos, 0 errores.
2. `ruff check src/` → `All checks passed!`
3. `mypy src/<paquete> --ignore-missing-imports` → `Success: no issues found`
4. `python -m build --wheel` → `Successfully built`
5. Cobertura global >= 85%; módulo nuevo o modificado >= 70%; ningún módulo baja
   su cobertura actual (trinquete). Si el repo ya tiene módulos < 70%, listarlos
   como deuda en CLAUDE.md en vez de declarar una regla que el repo ya incumple.
6. Sin referencias al nombre antiguo del paquete (incluye `examples/`, CI, LICENSE).
7. `sphinx-build -W` sin warnings y `examples/*.py` ejecutan sin error.
8. Todo bug corregido tiene test de regresión y ficha en BUG_CATALOG.md.
9. CHANGELOG.md actualizado con la versión nueva.
10. CLAUDE.md actualizado si se añadió funcionalidad o se cambió un comando.

## Reglas de trabajo (no negociables)

### R-01: Cambios quirúrgicos
No reescribas módulos enteros para añadir una función. Sigue el patrón que usan
los módulos vecinos. Haz el cambio mínimo que resuelve el problema.

### R-02: Validar contra referencia independiente
Todo resultado numérico se valida contra una fuente externa a este código
(publicación, cálculo manual, otra librería, simulación Monte Carlo con ≥20 semillas).
Nunca validar la salida del código contra sí mismo.

### R-03: Español en lo que ve el usuario
Docstrings, mensajes de `ValueError`/`UserWarning`, columnas de DataFrame,
texto de gráficos → en español. Nombres de funciones y variables → snake_case inglés está bien.

### R-04: Avances incrementales con checkpoint
Cada versión: construir, probar (suite + wheel en venv limpio), commit, tag `vX.Y.Z`.
No dejar trabajo a medio hacer entre commits.

### R-05: Una sola fuente de verdad para la versión
Deja el literal solo en `__init__.py` y que el build lo lea (probado: una edición
produjo `pccpy-0.10.9-py3-none-any.whl`):
```toml
[project]
dynamic = ["version"]          # y quitar `version = "..."`

[tool.setuptools.dynamic]
version = {attr = "<paquete>.__version__"}
```
NO uses `importlib.metadata.version()` dentro de `__init__.py`: la metadata
queda congelada al instalar y diverge del código en instalaciones editables
(probado: metadata 0.10.8 vs fuente 0.10.9 tras subir versión sin reinstalar).
Si no puedes migrar aún, edita ambos archivos y verifica con
`grep -n '^version\|^__version__' pyproject.toml src/<paquete>/__init__.py`.

### R-06: Dependencias opcionales con mensaje orientativo
Cualquier `import` de dependencia opcional va dentro de `try/except ImportError`:
```python
try:
    import openpyxl  # noqa: F401
except ImportError:
    raise ImportError(
        "X es necesario. Instálalo con:\n    pip install <nombre_pypi>[extra]"
    ) from None
```

### R-07: No contaminar estado global
Las funciones de visualización van dentro de `plt.rc_context({})`.
Los warnings temporales van dentro de `warnings.catch_warnings()`.

### R-08: Validación de entrada centralizada
La conversión de datos de usuario a arrays internos pasa siempre por la misma
función de ingesta. Esa función maneja: NaN/inf (warning + filtrado), arrays vacíos
(ValueError), tipos incorrectos (TypeError), casos degenerados (std=0 → NaN + warning).

### R-09: Checklist de renombre
Si se cambia el nombre del módulo Python o del paquete PyPI, ejecutar ANTES:
```bash
grep -r "nombre_viejo" . --include="*.py" --include="*.toml" --include="*.yml" \
  --include="*.md" --include="*.rst" --include="*.yaml"
```
El resultado es la lista exacta de archivos a actualizar. Incluir este CLAUDE.md.

### R-10: No repetir bugs del catálogo
Los bugs documentados en `docs/retrospectiva/BUG_CATALOG.md` tienen solución conocida.
Antes de implementar validación de entrada, casos borde o importaciones opcionales,
leer ese catálogo y aplicar el patrón correcto directamente.

### R-11: Tests de casos borde obligatorios
Cada función pública nueva necesita al menos un test de caso borde:
- Entrada vacía
- NaN/inf en los datos
- n mínimo (1 o 2 según la función)
- Parámetros opcionales ausentes
- Caso degenerado (std=0, todos iguales, etc.)

### R-12: CI en versión mínima
Antes de abrir un PR, confirmar que los tests pasan en la versión mínima de Python
declarada en `pyproject.toml`. Si no se puede verificar localmente, el CI debe correr
esa versión y el PR no se mergea hasta que pase.

### R-13: "Listo para release" exige verificación, no opinión
Solo declara "listo" si: (a) la versión en el código == entrada superior de
CHANGELOG.md; (b) `python -m build --wheel` genera `<nombre>-<esa versión>-*.whl`.
En el workflow de publicación añade, tras el build, una guarda que compare el
tag/release con la versión del wheel (probada localmente contra el commit que
falló: devuelve exit 1 con tag 0.10.8 vs versión 0.10.7):
```bash
V=$(python -c "import glob,re;print(re.search(r'-(\d[^-]*)-py', glob.glob('dist/*.whl')[0]).group(1))")
[ "${TAG#v}" = "$V" ] || { echo "tag $TAG != wheel $V"; exit 1; }
```
(`TAG` = `github.event.release.tag_name` si el trigger es `release`, o `GITHUB_REF_NAME` si es push de tag.)

### R-14: Sphinx — un símbolo, una directiva canónica
No hagas `autoclass`/`autofunction` del mismo símbolo en dos páginas. Si es
inevitable, la que Sphinx procesa primero lleva `:no-index:`; verifícalo con
`sphinx-build -W`. En docstrings numpy no uses `shape (n,)` si existe un
atributo `n` en algún objeto documentado (referencia ambigua): usa `array-like`.

### R-15: Los ejemplos son código que se ejecuta
Cada `examples/*.py` corre sin error antes de un release y, idealmente, en CI.
Un renombre que no los toca los deja rotos sin que ningún test lo note.

### R-16: Una regla nueva se prueba antes de adoptarla
Ejecuta el comando de verificación de la regla contra el propio repo y registra
el resultado. Si la regla falla en el repo actual, o es un falso positivo (p. ej.
un `grep` que coincide con el propio CLAUDE.md), corrígela o documéntala como deuda.

## Política de no repetición

Si un bug del catálogo (`BUG_CATALOG.md`) reaparece:
1. Identificar por qué la solución anterior no fue suficiente.
2. Añadir un test de regresión si no existe.
3. Actualizar el catálogo con la nueva ocurrencia.
4. Reforzar la regla correspondiente en este archivo.
```
