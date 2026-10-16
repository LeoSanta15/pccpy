# Constitución de `pccpy`

Principios que no se negocian. Una especificación o un plan que los contradiga se corrige antes de implementarse. Cada
uno remite a la regla de `CLAUDE.md` que lo hace cumplir y dice cómo se comprueba.

| # | Principio | Regla | Cómo se comprueba |
|---|---|---|---|
| 1 | **Ningún resultado numérico sin referencia independiente.** Se contrasta con una fuente externa (norma, libro, `scipy`, cálculo manual o simulación con ≥ 20 semillas), nunca con la salida de `pccpy`. Si no se puede consultar la fuente, se dice. | R-02 | `run_validation()` |
| 2 | **No se afirma lo que no se ha ejecutado.** Los ejemplos de la documentación se ejecutan; los números que se citan se miden; no se inventan comparaciones con Minitab. | R-02, R-13 | `tests/test_docs_ejemplos.py`, `make examples` |
| 3 | **Lo nuevo es opt-in y lo existente no cambia sin avisar.** Un cambio que altera resultados sube la versión menor y se lista en «Cambios que alteran resultados» del CHANGELOG. | R-01, R-06 | `tests/golden/`, CHANGELOG |
| 4 | **Todo fallo conocido queda fijado con un test que falla sin la corrección.** | R-11, R-15 | `tests/test_auditoria_regresion.py` y vecinos |
| 5 | **Español en lo visible, inglés traducido.** Docstrings, errores, avisos, columnas y gráficos en español con `tr()`; catálogos `.po` al día; la traducción sigue pendiente de revisión experta. | R-03, R-17 | `make i18n-check`, `make docs-check` |
| 6 | **La entrada del usuario se valida en un solo sitio.** Datos por `as_1d()` / `to_subgroups()`; los casos borde (vacío, NaN, n mínimo, std = 0) tienen test. | R-09, R-11 | tests de casos borde |
| 7 | **Sin estado global ni efectos laterales.** Gráficos dentro de `rc_context`, avisos temporales dentro de `catch_warnings`. | R-08 | tests de aislamiento |
| 8 | **Funciona en las versiones mínimas declaradas** (Python 3.9, numpy 1.22, scipy 1.9, pandas 1.4, matplotlib 3.5). | R-14 | trabajo `versiones-minimas` del CI |
| 9 | **Cambios quirúrgicos.** Se imita a los vecinos; no se reescribe un módulo para añadir una función. | R-01 | revisión |
| 10 | **El tag y el release los crea la persona responsable**, nunca el agente. | R-04 | proceso |
| 11 | **Aprobar una especificación es decisión de la persona responsable.** Quien la redacta (persona o agente) resuelve las dudas con su respuesta, pero no la pasa a `aprobada` por su cuenta. | R-04 | revisión; `make specs-check` (sin dudas abiertas) |
| 12 | **Lo que se recuerda y no se pudo consultar se declara.** Una tabla o un valor transcrito de memoria (p. ej. la tabla de Rorabacher para Dixon) se respalda con un cálculo independiente y consta en «No verificable sin la fuente»; nunca se presenta como contrastado con la fuente. | R-02 | sección «No verificable sin la fuente» de cada especificación |
| 13 | **La tolerancia de una referencia se justifica.** Si la referencia independiente es menos exacta que `pccpy` (el optimizador de SciPy se detiene en ~3·10⁻⁶), la tolerancia refleja eso y se escribe por qué, en la especificación y en el test. | R-02 | tolerancia declarada en `run_validation()` |

## Qué debe contener toda especificación de un cálculo estadístico

- La **fórmula** con su fuente, o la derivación si no hay fuente a mano.
- Al menos **un valor de referencia** calculado aparte, con su tolerancia.
- Qué ocurre en los **casos borde** (n mínimo, datos constantes, valores no finitos, subgrupos desiguales).
- Si **cambia algún resultado existente**, cuál y por cuánto.
- Qué **no** se pudo verificar sin acceso a la fuente.
