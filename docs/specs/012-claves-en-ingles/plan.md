# Plan — 012 Claves en inglés en los resultados de las cartas

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: cambia lo que devuelve `chart.params` (principio 3, «lo existente
  no cambia sin avisar»); se avisa en el CHANGELOG, sube la versión menor y los alias mantienen funcionando el código antiguo.

## Diseño

- `results.py`: tabla `_CLAVES_ES_EN` (la de la especificación) y una subclase de `dict`, `_Parametros`, con `__missing__`,
  `get` y `__contains__` que aceptan la clave en español, emiten `DeprecationWarning` y devuelven el valor de la canónica. Es lo
  único que se guarda en `ControlChart.params`.
- Las cartas (`charts/*.py`, `multivariate.py`) construyen sus diccionarios con claves en inglés (`variables.py`, `attributes.py`,
  `timeweighted*.py`, `advanced.py`, `multivariate.py`); `_PARAMETROS` pasa a mapear `inglés → texto en español` para el
  `summary()` (se mantiene la traducción de lo que se muestra).
- `phase1.py` y su serialización: leer ambos esquemas; escribir el nuevo con `schema_version` mayor.
- Carta de zona: `kind` y paneles `"Zone"`/`"Score"`; `ControlChart.__getitem__` acepta `"Zona"`/`"Puntaje"` con aviso.
- Ejemplos, README y guías con las claves nuevas.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Alias con `DeprecationWarning` en `params` | Romper de golpe | El código de terceros puede leer `params["media"]` |
| `dict` con `__missing__` | Un `Mapping` completo | Basta para lectura; mantiene `dict` para `copy` y `json` |
| Claves en español fuera de `keys()` | Mostrar ambas | Evitar duplicados al iterar o serializar |
| Escribir solo el esquema nuevo en archivos de Fase I | Escribir ambos | Un solo formato; los antiguos siguen legibles |

## Validación independiente

La tabla de equivalencias escrita en los tests; los valores numéricos se comparan con los de los tests y los golden actuales
(sin cambios). Fixture de un archivo de Fase I escrito con 0.15.x. Sin comprobación numérica nueva en `run_validation()`.

## Riesgos

- Código de usuario que itere `params` esperando claves en español: se anuncia en el CHANGELOG.
- `chart.kind == "Zona"` no puede avisar: documentado.
- Archivos de Fase I guardados por el usuario: se cubre con la fixture.
- Sphinx/doctests que muestren `params`: se revisan las guías.

## Documentación y traducciones

Docstrings de las cartas, README (es/en), guías, CHANGELOG («Cambios que alteran resultados»), `.po` y catálogos de la documentación.
