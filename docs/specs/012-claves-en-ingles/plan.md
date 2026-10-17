# Plan — 012 Claves en inglés en los resultados de las cartas

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: rompe lo que devuelve `chart.params` y los nombres de la carta de
  zona (principio 3, «lo existente no cambia sin avisar»); se avisa en el CHANGELOG y sube la versión menor. Sin alias, por decisión
  de la persona responsable.

## Diseño

- `results.py`: `_PARAMETROS` pasa a mapear las claves **en inglés** al texto en español que se muestra (marcado con `N_()`), y
  `_VALORES_PARAMETRO` mapea `"historical"` a su texto en español; el `summary()` los traduce como hoy.
- Las cartas (`charts/*.py`, `multivariate.py`) construyen sus diccionarios con las claves en inglés de la tabla
  (`variables.py`, `attributes.py`, `timeweighted*.py`, `advanced.py`, `multivariate.py`).
- `phase1.py` y su serialización: lee las claves nuevas; para los archivos guardados con 0.15.x, según la pregunta abierta.
- Carta de zona: `kind` y paneles `"Zone"`/`"Score"`; `_NOMBRES_VISIBLES` mapea esos nombres a «Zona»/«Puntaje» para mostrarlos.
- Ejemplos, README, guías y tests usan las claves nuevas.
- Catálogos `.po`: las entradas pasan a tener como `msgid` el texto en español que ya existe; no cambia el texto mostrado.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Sin alias | Alias con `DeprecationWarning` hasta la 0.18.0 | Decisión de la persona responsable |
| Claves en inglés, texto mostrado traducido | Claves en el idioma activo | El código no puede depender del idioma |
| Renombrar `kind` y paneles de la carta de zona | Dejarlos | Mismo principio |
| Versión menor (0.16.0) | Parche | Es un cambio incompatible |

## Validación independiente

La tabla de equivalencias escrita en los tests; los valores numéricos se comparan con los de los tests y los golden actuales
(sin cambios); `summary()` en español idéntico al de 0.15.5 (`tests/golden/i18n_es.json` sin regenerar). Sin comprobación numérica
nueva en `run_validation()`.

## Riesgos

- Código de usuario que lea `params["media"]`: falla con `KeyError`; se anuncia en el CHANGELOG con la tabla y la receta.
- Archivos de Fase I guardados: según la pregunta abierta; fixture de un archivo de 0.15.x.
- Tests, README y guías con las claves antiguas: `grep` en `tests/`, `docs/` y `README*.md`.

## Documentación y traducciones

Docstrings de las cartas, README (es/en), guías, CHANGELOG («Cambios que alteran resultados»), `.po` y catálogos de la
documentación.
