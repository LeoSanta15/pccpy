## Resumen

<!-- Qué cambia y por qué. -->

## Especificación

<!-- Si cambia el comportamiento de la biblioteca: enlace a su carpeta en `docs/specs/` (NNN-nombre) y requisitos que cubre
(SNNN-RF-nn). Si es una corrección trivial (errata, docstring, traducción): "No aplica". -->

## Verificación

- [ ] `make check` pasa (lint, tipos, tests, build, docs, ejemplos)
- [ ] Si cierra una especificación: estado `implementada`, tareas marcadas y cada requisito citado por un test (`make specs-check`)
- [ ] Si corrige un bug: test de regresión que falla sin el fix + ficha en `docs/retrospectiva/BUG_CATALOG.md`
- [ ] Si toca la API pública: docstring en español, `CHANGELOG.md` y `__all__` actualizados
- [ ] Si prepara un release: `make release-check TAG=vX.Y.Z` pasa
