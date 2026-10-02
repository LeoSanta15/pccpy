# RESUMEN EJECUTIVO — pccpy v0.10.8

**Fecha:** 2026-10-02 (revisado en segunda pasada) | **Versión evaluada:** 0.10.8 | **Madurez:** Nivel 3 — Sólido (3.1/5.0)

> **Correcciones de la segunda pasada:** (1) la media anterior 3.4 estaba mal calculada (las puntuaciones sumaban 46/14 = 3.29); (2) se retiró la recomendación de bajar `checkout@v6` a `v4`: v6 funciona (CI verde en `819ca11`; el release v0.10.7 publicó con él); (3) CLAUDE.md ya está actualizado; (4) se añadieron BUG-13 (release fallido) y BUG-14 (ejemplos rotos).

---

## Estado actual

pccpy es una librería Python de Control Estadístico de Procesos (SPC) con 6.636 líneas de código fuente, 344 tests pasando al 100%, 90% de cobertura global y un CI funcional en GitHub Actions con matrix Python 3.9–3.13. El proyecto pasó de prototipo local (`spyc`) a paquete publicado en PyPI en ~100 commits a lo largo de varios meses.

**CI ejecutado en esta revisión:**
- `pytest -q`: **344 passed in 33.97s** (0 fallos)
- `ruff check src/`: **All checks passed!**
- `mypy src/pccpy`: **Success: no issues found in 25 source files**
- `python -m build --wheel`: **Successfully built pccpy-0.10.8-py3-none-any.whl**

---

## 5 mayores aciertos

**A-01: Suite de tests robusta y reproducible.**
344 pruebas, fixture de semilla aleatoria en conftest.py, cobertura del 90%, un archivo de test por área temática. Es la base de confianza del proyecto.

**A-02: API consistente con objetos resultado unificados.**
Todos los análisis devuelven objetos con `.summary()`, `.plot()` y `.to_excel()`. La consistencia reduce la curva de aprendizaje del usuario.

**A-03: Validación numérica por referencia independiente.**
Las constantes de carta de control se calculan por integración numérica (no tablas). Los tests usan Monte Carlo con ≥20 semillas. Esta política está escrita en CLAUDE.md y se cumple.

**A-04: Documentación Sphinx completa con CI.**
Sphinx construye con `-W` (warnings como errores) en CI. Tutorial con datos reales, FAQ, guía de selección, comparativa con Minitab. Representa un esfuerzo sostenido de documentación.

**A-05: Manejo de casos borde en datos reales.**
La versión 0.10.7 corrigió NaN/inf, DataFrames con columnas mixtas, capability sin especificaciones y datos constantes — los errores más frecuentes en uso industrial real.

---

## 5 mayores riesgos

**R-01: El pipeline de release no verifica lo que publica (ya falló una vez).**
`publish.yml` (trigger `release: published`) no compara el release con la versión del wheel ni corre `twine check`; la versión vive en dos archivos. El release v0.10.8 falló por esto (BUG-13).

**R-02: `examples/*.py` están rotos.**
Ambos scripts hacen `import spyc` y fallan con `AttributeError` (BUG-14). Ningún test ni CI los ejecuta. *No estaba en la primera versión de este informe.*

**R-03: Bugs cerrados sin test de regresión y módulos casi sin cobertura.**
BUG-01, BUG-07 y BUG-12 sin test (recetas probadas en el catálogo); BUG-10 solo parcial. `charts/timeweighted_attr.py` al 19 % (6 funciones públicas EWMA/CUSUM de atributos) y `_wizard.py` al 62 %.

**R-04: Sin auditoría de seguridad de dependencias.**
No hay `pip audit` en CI ni `SECURITY.md`; rangos sin límite superior (`numpy>=1.22` sin `<3`).

**R-05: Reglas de calidad sin trinquete.**
El criterio "ningún módulo < 70 %" no se cumple hoy (2 módulos) y un `ruff --select ...,S` propuesto falla (`S101`, `acceptance.py:692`). Hasta que se adopten como trinquete, son deuda declarada, no gate.

---

## Siguientes pasos (ordenados por impacto/esfuerzo)

1. ~~Actualizar CLAUDE.md~~ — **hecho** (segunda pasada).

2. **Blindar el release** — guarda tag/release == versión del wheel + `twine check` en `publish.yml`, y versión única con `[tool.setuptools.dynamic]` (ambos probados localmente; el step de YAML aún no se ha ejecutado en Actions). ~30 min. Es la acción de mayor impacto: evita repetir BUG-13.

3. **Arreglar `examples/`** — `spyc` → `pccpy` en los dos scripts, ejecutarlos y añadir el bucle de ejemplos a CI. ~15 min.

4. **Tests de regresión faltantes** — BUG-01, BUG-07, BUG-12 (recetas ya probadas en `BUG_CATALOG.md`) y el `assert` de n<8 en `_diagnose` (BUG-10). ~30 min.

5. **Tests para `timeweighted_attr.py` y el modo widget de `_wizard.py`** (mock de `ipywidgets`). Meta: >= 70 % por módulo. 2–4 horas.

6. **`pip audit` en CI + `SECURITY.md`**. ~15 min.

~~Corregir `checkout@v6` → `v4`~~ — **descartado**: la versión v6 funciona (evidencia arriba); bajarla causaría una regresión.
