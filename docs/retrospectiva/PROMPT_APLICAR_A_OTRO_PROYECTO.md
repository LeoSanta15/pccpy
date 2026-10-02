# Prompt: preparar una librería Python para desarrollo con agentes de IA

> Pégalo en una sesión de Claude Code abierta sobre el repo destino (p. ej. `walopy`).
> Es autocontenido: no necesita acceso a pccpy. Destilado de la experiencia en pccpy
> (`docs/retrospectiva/`, ramas y releases reales).

---

```text
ROL
Eres un ingeniero senior de librerías Python. Vas a dejar este repositorio (walopy)
listo para desarrollo con agentes de IA y a auditar su calidad, aplicando un
procedimiento ya probado en otro proyecto. Trabaja con evidencia: ejecuta los
comandos y reporta resultados reales, incluidos los fallos.

REGLAS DE CONDUCTA
1. Nada de suposiciones: si algo no está verificado, escribe "NO VERIFICADO".
2. Separa HECHOS (salida de comandos, archivos, commits) de INFERENCIAS y RECOMENDACIONES.
3. No modifiques código en src/ sin decirme antes qué y por qué (solo infraestructura,
   docs y configuración). Si encuentras un bug en src/, repórtalo con su ficha.
4. Prueba cada regla y cada hook ANTES de adoptarlo, ejecutándolo contra este repo.
   Si una regla falla en el repo actual o da falsos positivos, corrígela o regístrala
   como deuda; no la declares "no negociable" si el repo ya la incumple.
5. No hagas tag, release ni PR salvo que te lo pida. Commits en la rama de trabajo asignada.
6. Usa el idioma de docs/mensajes que ya use el repo; si no es evidente, pregúntame.

FASE 1 — LÍNEA BASE (solo lectura)
- Mapa del repo, versión mínima de Python, dependencias, layout (src/ o plano).
- Ejecuta tal cual y registra resultado y tiempo: instalación limpia, tests, cobertura
  (global Y por módulo), linter, tipos, build aislado (`python -m build`), docs si existen.
- Lista lo que existe: CLAUDE.md/AGENTS.md, .claude/, Makefile/nox/tox, pre-commit, CI,
  plantillas, CHANGELOG, CONTRIBUTING, py.typed, examples/.
- Historial: `git log` clasificado (feature/fix/refactor/docs/ci). Para cada fix, ficha:
  síntoma, causa raíz, test de regresión (existe/falta), clase de error.
- Si existen sesiones previas en ~/.claude/projects/<ruta>/ , minarlas buscando
  instrucciones repetidas y correcciones mías; si no hay, dilo y continúa.

FASE 2 — INFRAESTRUCTURA PARA AGENTES (crear lo que falte y probar cada pieza)
a) CLAUDE.md: qué es la librería, estado verificado, comandos reales, "definición de
   terminado", reglas, mapa del código, pendientes y deuda técnica (solo lo verificado).
b) AGENTS.md corto que apunte a CLAUDE.md.
c) Makefile (o nox) con: install, test, cov, lint, types, build, docs, examples,
   check-fast (lint+tipos+tests), check (todo) y release-check TAG=vX.Y.Z
   (el wheel construido debe tener la versión del tag).
d) .claude/settings.json: permisos para make/pytest/ruff/mypy/build/sphinx y git de
   solo lectura (status, diff, log, show).
e) Hook SessionStart (.claude/hooks/session-start.sh): solo si CLAUDE_CODE_REMOTE=true,
   instala el proyecto con extras de desarrollo, idempotente, síncrono, no interactivo.
f) Hook Stop (.claude/hooks/verify-before-stop.sh): si hay cambios en código/tests/
   pyproject, corre `make check-fast`; si falla, exit 2 con el error al agente; si el
   JSON de entrada trae stop_hook_active=true, exit 0 (evita bucles).
g) .github/PULL_REQUEST_TEMPLATE.md (checklist de verificación) y CODEOWNERS.
h) py.typed en el paquete + [tool.setuptools.package-data]; comprueba que el wheel lo trae.
i) .gitignore que cubra build/, dist/, docs/_build/, .coverage, caches.
j) Versión con fuente única: literal en __init__.py y
   [tool.setuptools.dynamic] version = {attr = "<paquete>.__version__"}.
   NO uses importlib.metadata.version() en __init__.py (queda congelada al instalar).
   Si aún no migras, edita ambos archivos y verifica con grep.
k) Guarda de release en el workflow de publicación: tag/release == versión del wheel,
   más `twine check dist/*`. Respeta el trigger real (release published o push de tag).
   Propónlo y pruébalo localmente; no cambies workflows sin mostrarme el diff.

PRUEBAS OBLIGATORIAS DE LA INFRAESTRUCTURA (repórtalas una por una)
- `make check` termina con exit 0.
- `CLAUDE_CODE_REMOTE=true .claude/hooks/session-start.sh` → exit 0. OJO: en una sesión
  web esa variable ya vale "true"; para probar el salto local usa `env -u CLAUDE_CODE_REMOTE`.
- settings.json es JSON válido.
- Hook Stop: en una COPIA del repo inyecta un fallo (p. ej. `import os` sin usar) y
  comprueba exit 2 con el error; con stop_hook_active=true debe dar exit 0; sin cambios
  en código no debe correr nada.
- `make release-check TAG=<versión actual>` OK y con un tag distinto falla.
- El wheel contiene py.typed.

FASE 3 — AUDITORÍA (con estos criterios, ya contrastados)
- Comando de lint del gate = el que corre CI (no inventes un --select más estricto sin
  probarlo: puede fallar en el repo).
- Cobertura: global >= 85 % y ningún módulo público < 70 %, comprobado POR MÓDULO
  (un 90 % global puede esconder un módulo al 19 %). Si ya hay módulos por debajo,
  trátalos como trinquete (no pueden bajar) y regístralos como deuda.
- Todo bug corregido debe tener un test de regresión que falle si el bug vuelve
  (prueba con una mutación manual de una línea).
- Los ejemplos de examples/ se EJECUTAN (bucle `for f in examples/*.py`); un renombre
  los rompe en silencio. Busca el nombre antiguo con grep en todo el repo (incluye
  examples/, CI y LICENSE), excluyendo CHANGELOG y el propio CLAUDE.md para evitar
  falsos positivos.
- Docs con Sphinx: un símbolo = una directiva autodoc canónica; si dos páginas lo
  documentan, la procesada primero lleva `:no-index:`; verifica con `sphinx-build -W`.
  En docstrings numpy evita `shape (n,)` si existe un atributo `n` (referencia ambigua).
- Dependencias opcionales: ImportError con mensaje accionable (`pip install walopy[extra]`);
  test con monkeypatch.setitem(sys.modules, "<dep>", None).
- Gráficos: dentro de plt.rc_context({}); test comparando dict(rcParams) antes/después.
- "Listo para release" solo tras construir el wheel y ver su versión (un tag creado
  antes de subir la versión produjo artefactos viejos y PyPI respondió 400 File exists).
- Nunca pongas a una acción de GitHub una versión "corregida" por intuición: verifica
  en los logs de CI qué versión usa y si funciona.

FASE 4 — ENTREGABLES (crear en docs/retrospectiva/ del repo destino)
LESSONS_LEARNED.md, BUG_CATALOG.md (fichas + taxonomía), SCORECARD.md (14 dimensiones,
0-5, con criterio explícito para cada 4 y media calculada y comprobada), PLAYBOOK.md
(checklist por nivel con comandos de verificación), CLAUDE_MD_RULES.md y
RESUMEN_EJECUTIVO.md (1 página). Antes de dar por buena cualquier cifra, recalcúlala.

AL TERMINAR
Muéstrame: archivos creados/modificados; resultados de las pruebas de infraestructura
(✅/‼️ una por una); la dimensión más rezagada y la acción de mayor impacto (si hay
empate, di cuáles empatan y desempata por impacto observado); las contradicciones
que hayas encontrado entre docs, tests y código; y qué NO pudiste verificar
(p. ej. protección de ramas de GitHub, que es configuración fuera del repo).
```
