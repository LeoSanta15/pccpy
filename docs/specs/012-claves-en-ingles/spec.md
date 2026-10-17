# 012 — Claves en inglés en los resultados de las cartas (`params` y nombres de panel)

- **Estado:** borrador
- **Identificador:** S012
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.16.0 (cambia lo que devuelve `chart.params`: versión menor y aviso en «Cambios que alteran resultados»)

## Problema

Principio de la persona responsable: **el código está en inglés, en cualquier idioma, y las salidas dependen del idioma**. Hoy
el código de pccpy ya es inglés (funciones, parámetros, `to_frame(stable=True)`), pero los resultados de las cartas guardan
parte de sus datos con claves en español:

- `ControlChart.params` (una lista de diccionarios, uno por etapa) usa claves como `media`, `sigma_dentro`, `tamaño`, `centro`,
  `subgrupos`, `forma`, `escala`, `fase`, `método`… y valores como `"histórica"`. Un usuario que escribe `carta.params[0]["media"]`
  tiene que saber español, sea cual sea el idioma de pccpy.
- Los nombres de la carta de zona (`chart.kind == "Zona"`, `chart["Zona"]`, el panel `"Puntaje"`) también son palabras en español.

La 0.15.5 traduce lo que se **muestra** (`summary()`, títulos de gráfico), pero las claves siguen siendo español porque cambiarlas
rompe el código existente. Esta especificación las pasa al inglés con una transición que no rompe a nadie de golpe.

Las claves en español que hoy declara `results._PARAMETROS` son: `centro`, `distribución`, `escala`, `forma`, `longitud`, `media`,
`objetivo`, `peso`, `pesos`, `reinicio`, `subgrupos`, `tamaño`, `n_subgrupo`, `MR_prom`, `alfa`, `corridas`, `fase`, `método`,
`n_puntos`, `partes`, `puntos`, `sigma_conocida`, `sigma_dentro`, `sigma_entre`, `sigma_entre_dentro`, `variables`, `LCS`,
`sigma_mín`, `sigma_máx`.

## Fuera de alcance

- Los textos que se muestran (`summary()`, gráficos, tablas): ya dependen del idioma y no cambian.
- Las columnas de `to_frame()` sin `stable`: son presentación.
- Los argumentos y nombres de funciones: ya están en inglés.
- El código de `README.md` fuera de la sección de ejemplos: está pensado para quien habla español y la persona responsable decidió
  no cambiarlo.

## Requisitos

### S012-RF-01 — Claves canónicas en inglés

Cada carta guarda su `params` con claves en inglés (`snake_case`), según una tabla fija (propuesta abajo). Los valores que son
palabras del idioma fuente (`"histórica"`) pasan a su forma en inglés (`"historical"`).

**Aceptación:**
- **Dado** una carta I-MR **cuando** se lee `chart.params[0]` **entonces** tiene `mean`, `sigma`, `mr_mean` y `n` (y no `media`
  como clave real).
- **Dado** una Z-MR con `sigma` histórica **entonces** `params[0]["method"] == "historical"` y `sigma_min`/`sigma_max`.
- **Referencia independiente:** la tabla de equivalencias escrita en el test; los valores numéricos son los mismos que antes
  (los de `tests/golden/` y los de los tests actuales, leídos con la clave nueva).

### S012-RF-02 — Alias en español durante una transición

`chart.params[i]` acepta también las claves en español: `params[0]["media"]` devuelve el mismo valor que `params[0]["mean"]` y emite
`DeprecationWarning` (en español) que nombra la clave nueva. Lo mismo con `.get(...)` y `in`. Las claves en español no aparecen en
`keys()`, `items()` ni en la iteración (solo las canónicas). La transición dura hasta la versión que decida la persona responsable
[NECESITA ACLARACIÓN: ¿cuántas versiones? propongo mantener los alias hasta 0.18.0 y quitarlos en 0.19.0].

**Aceptación:**
- **Dado** código antiguo `chart.params[0]["media"]` **cuando** se ejecuta **entonces** devuelve el valor y emite `DeprecationWarning`
  que menciona `mean`; con `warnings.simplefilter("error")` falla.
- `list(chart.params[0])` no contiene ninguna clave en español.

### S012-RF-03 — Resultados guardados de la Fase I

Los archivos que guardan `PhaseOneResult` / `phase_one(...).to_json()` con claves en español siguen leyéndose (`from_limits`,
`PhaseOneResult.load`); los archivos nuevos se escriben con claves en inglés y su `schema_version` sube.

**Aceptación:**
- **Dado** un archivo de Fase I escrito con 0.15.x (guardado como fixture en `tests/`) **cuando** se lee **entonces** da los
  mismos límites que antes.
- Un archivo escrito con la versión nueva se lee con la nueva; con la antigua se documenta que no se garantiza.

### S012-RF-04 — Nombres de carta y de panel

`chart.kind` y los nombres de panel de la carta de zona pasan a `"Zone"` y `"Score"`; `chart["Zona"]` y `chart["Puntaje"]` siguen
funcionando durante la transición con `DeprecationWarning`. `chart.kind == "Zona"` no se puede avisar (es una comparación de
`str`): se anuncia en el CHANGELOG como cambio.
[NECESITA ACLARACIÓN: ¿se renombran también `kind` y los paneles (cambio visible en `chart.kind`) o solo las claves de `params`?
Recomiendo renombrarlos: es lo mismo que el resto del principio.]

**Aceptación:**
- **Dado** una carta de zona **entonces** `chart.kind == "Zone"` y `chart["Zone"]` existe; `chart["Zona"]` devuelve el mismo
  panel con `DeprecationWarning`.
- `summary()` y los gráficos siguen mostrando «Zona» en español y «Zone» en inglés.

### S012-RF-05 — Todo lo que lee `params` por dentro

El código de pccpy que hoy lee `params` con claves en español (`phase1.py`, las cartas de tiempo ponderado, la validación)
usa las canónicas.

**Aceptación:**
- La suite completa pasa sin ningún `DeprecationWarning` de las claves antiguas (los tests configuran `-W error::DeprecationWarning`
  solo para ese mensaje).
- `grep` de las claves antiguas en `src/` solo las encuentra en la tabla de alias.

### S012-RF-06 — Documentación, CHANGELOG y traducciones

**Aceptación:**
- «Cambios que alteran resultados» del CHANGELOG lista la tabla completa de claves y el plazo de los alias.
- Los README, las guías y los ejemplos usan las claves nuevas (la sección de ejemplos de `README.md` y `README_en.md`
  incluida); el CHANGELOG conserva las antiguas porque es historial.
- Mensajes con `tr()` y traducción al inglés (pendiente de revisión experta en SPC).

## Tabla de equivalencias propuesta

| Español (hoy) | Inglés (propuesta) | Español (hoy) | Inglés (propuesta) |
|---|---|---|---|
| `media` | `mean` | `fase` | `phase` |
| `centro` | `center` | `método` | `method` |
| `objetivo` | `target` | `n_puntos` | `n_points` |
| `distribución` | `distribution` | `puntos` | `points` |
| `forma` | `shape` | `partes` | `parts` |
| `escala` | `scale` | `corridas` | `runs` |
| `longitud` | `length` | `variables` | `variables` |
| `peso` / `pesos` | `weight` / `weights` | `sigma_conocida` | `sigma_known` |
| `reinicio` | `reset` | `sigma_dentro` | `sigma_within` |
| `subgrupos` | `subgroups` | `sigma_entre` | `sigma_between` |
| `tamaño` | `size` | `sigma_entre_dentro` | `sigma_between_within` |
| `n_subgrupo` | `subgroup_size` | `sigma_mín` / `sigma_máx` | `sigma_min` / `sigma_max` |
| `MR_prom` | `mr_mean` | `alfa` | `alpha` |
| `LCS` (MCUSUM) | `limit` | valor `"histórica"` | valor `"historical"` |

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Clave en español que no existe en esa carta | `KeyError` como hoy (sin aviso de alias) |
| `params[0].get("media", 0)` | Valor con `DeprecationWarning` |
| `"media" in params[0]` | `True` con `DeprecationWarning` |
| Copiar `params[0]` (`dict(...)`, `copy`) | Solo claves canónicas |
| Etapas (varios diccionarios) | Todas con claves canónicas; `stage` ya es inglés |
| Cartas multivariadas | Mismas claves canónicas (`phase`, `variables`, `points`, `size`, `alpha`…) |

## Resultados existentes que cambian

`chart.params[i].keys()` deja de contener las claves en español (siguen leyéndose como alias, con aviso). Para `kind` y los
nombres de panel de la carta de zona, la comparación directa con `"Zona"` deja de ser cierta. Ningún valor numérico cambia.

## No verificable sin la fuente

No sé cuánto código de terceros usa `params["media"]` y compañía: la transición con alias es para eso. Que Minitab use estos
nombres no es relevante (son datos internos de pccpy).

## Decisiones de la persona responsable

1. Aprobado redactar esta especificación: el código en inglés en cualquier idioma y las salidas según el idioma.

## Preguntas abiertas

- [NECESITA ACLARACIÓN: **Plazo de los alias.** ¿Hasta qué versión se aceptan las claves en español con aviso?]
- [NECESITA ACLARACIÓN: **`kind` y paneles de la carta de zona.** ¿Se renombran a «Zone» y «Score» (RF-04) o se dejan?]
- [NECESITA ACLARACIÓN: **Tabla de claves.** ¿Estás de acuerdo con los nombres en inglés propuestos (por ejemplo `mr_mean` para
  `MR_prom` y `limit` para el `LCS` de la MCUSUM)?]
