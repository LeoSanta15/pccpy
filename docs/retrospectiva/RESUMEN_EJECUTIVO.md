# RESUMEN EJECUTIVO — pccpy v0.10.8

**Fecha:** 2026-10-02 | **Versión evaluada:** 0.10.8 | **Madurez:** Nivel 3 — Sólido (3.4/5.0)

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

**R-01: CLAUDE.md desactualizado — riesgo operacional inmediato.**
Contiene comandos activos con `src/spyc` y `mypy src/spyc`. Cualquier sesión nueva ejecutará comandos incorrectos. Acción: actualizar antes de la próxima sesión de desarrollo.

**R-02: `timeweighted_attr.py` con 19% de cobertura.**
El módulo EWMA/CUSUM para atributos tiene 62 de 77 líneas sin cubrir. Un bug en este módulo no sería detectado por la suite actual.

**R-03: `actions/checkout@v6` no existe en GitHub Actions.**
El CI usa `v6` pero GitHub Actions está en `v4`. El CI puede fallar silenciosamente en un repo nuevo o en un re-run tras expiración de caché.

**R-04: Versión gestionada en dos lugares.**
`pyproject.toml` y `src/pccpy/__init__.py` declaran la versión manualmente. La desincronización ya ocurrió (historial documentado). Riesgo de publicar con metadata incorrecta.

**R-05: Sin auditoría de seguridad de dependencias.**
No hay `pip audit` en CI. Dependencias sin límite superior de versión (`numpy>=1.22` sin `<3`). Un breaking change en una dependencia mayor podría romper el paquete sin detección automática.

---

## Siguientes pasos (ordenados por impacto/esfuerzo)

1. **Actualizar CLAUDE.md** — reemplazar `spyc` por `pccpy` en todos los comandos. 30 minutos. Impacto: inmediato.

2. **Añadir tests a `timeweighted_attr.py`** — `ewma_p_chart`, `ewma_c_chart`, `cusum_p_chart`, `cusum_u_chart` en `test_charts.py`. Meta: subir de 19% a ≥85%. 2–4 horas.

3. **Unificar versión con `importlib.metadata`** — eliminar `__version__ = "0.10.8"` de `__init__.py`; añadir `from importlib.metadata import version; __version__ = version("pccpy")`. 15 minutos.

4. **Corregir versión de GitHub Actions** — `checkout@v6` → `checkout@v4`, `setup-python@v6` → `setup-python@v5` en los dos workflows. 15 minutos.

5. **Añadir `pip audit` al CI** — nuevo step en el job `calidad`. 15 minutos.
