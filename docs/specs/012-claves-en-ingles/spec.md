# 012 — Claves en inglés en los resultados de las cartas (`params` y nombres de panel)

- **Estado:** aprobada
- **Identificador:** S012
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.5 (decisión de la persona responsable; aunque rompe `chart.params` y los nombres de la carta de zona,
  que según la regla del proyecto pedirían versión menor, se publica como 0.15.5 con aviso en «Cambios que alteran resultados»)

## Problema

Principio de la persona responsable: **todo el código se maneja en inglés, también los datos con clave; solo las salidas y las
respuestas dependen del idioma**. Hoy el código de pccpy ya es inglés (funciones, parámetros, atributos, `to_frame(stable=True)`),
pero los resultados de las cartas guardan parte de sus datos con claves en español:

- `ControlChart.params` (una lista de diccionarios, uno por etapa) usa claves como `media`, `sigma_dentro`, `tamaño`, `centro`,
  `subgrupos`, `forma`, `escala`, `fase`, `método`… y valores como `"histórica"`. Un usuario que escribe
  `carta.params[0]["media"]` tiene que saber español, sea cual sea el idioma de pccpy.
- Los nombres de la carta de zona (`chart.kind == "Zona"`, `chart["Zona"]`, el panel `"Puntaje"`) y el `kind` de la carta de varianza
  generalizada (`"Varianza generalizada"`) también son palabras en español.

La 0.15.5 traduce lo que se **muestra** (`summary()`, títulos de gráfico), pero las claves siguen siendo español. Esta especificación
las pasa al inglés **de golpe, sin alias** (decisión de la persona responsable): `carta.params[0]["mean"]`.

Las claves en español que hoy declara `results._PARAMETROS` son: `centro`, `distribución`, `escala`, `forma`, `longitud`, `media`,
`objetivo`, `peso`, `pesos`, `reinicio`, `subgrupos`, `tamaño`, `n_subgrupo`, `MR_prom`, `alfa`, `corridas`, `fase`, `método`,
`n_puntos`, `partes`, `puntos`, `sigma_conocida`, `sigma_dentro`, `sigma_entre`, `sigma_entre_dentro`, `variables`, `LCS`,
`sigma_mín`, `sigma_máx`.

## Fuera de alcance

- Los textos que se muestran (`summary()`, gráficos, tablas): ya dependen del idioma y no cambian. Los **nombres** de los datos con
  clave son código y no dependen del idioma; lo que `summary()` muestra de ellos sí (`media=101,3` en español, `mean=101.3` en inglés).
- Las columnas de `to_frame()` sin `stable`: son presentación.
- Los argumentos y nombres de funciones: ya están en inglés.
- Alias en español de las claves viejas: no los hay (decisión de la persona responsable).

## Requisitos

### S012-RF-01 — Claves canónicas en inglés

Cada carta guarda su `params` con claves en inglés (`snake_case`), según la tabla de abajo, iguales en cualquier idioma. Los valores
que son palabras del idioma fuente (`"histórica"`) pasan a su forma en inglés (`"historical"`).

**Aceptación:**
- **Dado** una carta I-MR **cuando** se lee `chart.params[0]` **entonces** tiene `mean`, `sigma`, `mr_mean` y `n`.
- **Dado** una Z-MR con `sigma` histórica **entonces** `params[0]["method"] == "historical"` y trae `sigma_min` y `sigma_max`.
- **Dado** cualquier idioma activo (`es` o `en`) **entonces** las claves son las mismas.
- **Referencia independiente:** la tabla de equivalencias escrita en el test; los valores numéricos son los mismos que antes
  (los de `tests/golden/` y los de los tests actuales, leídos con la clave nueva).

### S012-RF-02 — Las claves en español dejan de existir (sin alias)

No hay alias ni aviso de transición: `params[0]["media"]` lanza `KeyError`, igual que con cualquier clave que no existe.

**Aceptación:**
- **Dado** una carta cualquiera **cuando** se lee `params[0]["media"]` (o cualquier clave de la tabla en español) **entonces**
  `KeyError`.
- Ninguna clave de `params`, de ninguna carta, contiene letras con acento ni es una de las españolas de la tabla (test sobre todas
  las cartas del repositorio).

### S012-RF-03 — Nombres de carta y de panel

`chart.kind` y los nombres de panel de la carta de zona pasan a `"Zone"` y `"Score"`, y el `kind` de la carta de varianza
generalizada a `"Generalized variance"`; `chart["Zona"]` y `chart["Puntaje"]` lanzan `KeyError`.

**Aceptación:**
- **Dado** una carta de zona **entonces** `chart.kind == "Zone"`, `chart["Zone"]` existe y `chart["Zona"]` lanza `KeyError`.
- **Dado** una carta de varianza generalizada **entonces** `chart.kind == "Generalized variance"`.
- `summary()` y los gráficos siguen mostrando «Zona» en español y «Zone» en inglés.

### S012-RF-04 — Lo que muestra `summary()` no cambia

El `summary()` traduce los nombres al idioma activo a partir de las claves canónicas en inglés; con el idioma español, la salida es
**idéntica** a la de 0.15.5.

**Aceptación:**
- Los textos de `summary()` coinciden con `tests/golden/i18n_es.json` (sin regenerarlo) y con las invariantes es/en.
- **Dado** el idioma inglés **entonces** `Parameters: mean=…` y `Parameters: size=…`; en español, `media=` y `tamaño=`.

### S012-RF-05 — Todo lo que lee `params` por dentro

El código de pccpy que hoy lee `params` con claves en español (`phase1.py`, las cartas de tiempo ponderado, la validación) usa las
canónicas.

**Aceptación:**
- La suite completa pasa.
- `grep` de las claves españolas de la tabla en `src/` solo las encuentra en el diccionario que traduce lo que se muestra.

### S012-RF-06 — Los archivos de Fase I guardados con 0.15.x se siguen leyendo

Un resultado de Fase I guardado con 0.15.x se lee con la versión nueva y da los mismos límites. Al preparar la Fase 0 se comprobó
que **el formato guardado no usa las claves en español** (los límites congelados ya se guardan como `mu`, `sigma`, `p`, `c`, `u`, y
el historial como `center` y `sigma`), así que el formato no cambia y no hace falta subir el `schema`: este requisito es una
garantía de que el cambio de `params` (que `phase_one` lee por dentro) no rompe los archivos ya guardados.

**Aceptación:**
- **Dado** un archivo de Fase I escrito con 0.15.4 (fixtures en `tests/data/`, tal como lo escribía esa versión) **cuando** se lee
  **entonces** da los mismos límites que antes y `phase2()` funciona.
- **Dado** `phase_one(...).to_dict()` con la versión nueva **entonces** el `schema` y las claves de `limits` son los de antes.
- **Referencia independiente:** los límites del archivo antiguo, leídos del propio archivo guardado.

### S012-RF-07 — Documentación, CHANGELOG y traducciones

**Aceptación:**
- «Cambios que alteran resultados» del CHANGELOG lista la tabla completa de claves, dice que no hay alias y cómo actualizar el código
  (`params[0]["media"]` → `params[0]["mean"]`).
- Los README, las guías y los ejemplos usan las claves nuevas; el CHANGELOG conserva las antiguas porque es historial.
- Mensajes con `tr()` y traducción al inglés (pendiente de revisión experta en SPC).

## Tabla de equivalencias

Los nombres de la derecha son código: no cambian con el idioma. `summary()` los muestra traducidos.

| Español (hoy) | Inglés | Español (hoy) | Inglés |
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
| `LCS` (MEWMA y MCUSUM) | `ucl` | valor `"histórica"` | valor `"historical"` |

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Clave en español | `KeyError` (como cualquier clave inexistente) |
| Etapas (varios diccionarios) | Todas con claves canónicas; `stage` ya es inglés |
| Cartas multivariadas | Mismas claves canónicas (`phase`, `variables`, `points`, `size`, `alpha`…) |
| `summary()` con el idioma español | Idéntico al de 0.15.5 |
| Resultado de Fase I guardado con 0.15.x | Se lee y da los mismos límites; el formato no cambia (RF-06) |

## Resultados existentes que cambian

`chart.params[i]` deja de tener las claves en español (`KeyError` si se leen). Para la carta de zona, `chart.kind` y los nombres de
panel pasan de `"Zona"`/`"Puntaje"` a `"Zone"`/`"Score"`. Ningún valor numérico cambia. Es un cambio incompatible, anunciado en el
CHANGELOG y publicado como 0.15.5 por decisión de la persona responsable.

## No verificable sin la fuente

No sé cuánto código de terceros usa `params["media"]` y compañía: al no haber alias, ese código fallará con `KeyError` al
actualizar. Que Minitab use estos nombres no es relevante (son datos internos de pccpy).

## Decisiones de la persona responsable

1. Todo el código en inglés, también los datos con clave; solo las salidas dependen del idioma.
2. Se renombran también `kind` y los paneles de la carta de zona (a «Zone» y «Score»).
3. **Sin alias**: cambio de golpe (`carta.params[0]["mean"]`).
4. Los nombres de la tabla son código en inglés y no dependen del idioma; `summary()` los traduce al mostrarlos. (Los nombres
   concretos de la tabla se revisan al aprobar la especificación.)
5. Los archivos de Fase I guardados con 0.15.x **se siguen leyendo** (RF-06).
6. **Versión 0.15.5**, no 0.16.0.
7. Aprobada por la persona responsable. Al preparar la Fase 0 se hicieron tres ajustes de implementación, que se avisan al aprobar:
   `LCS` de la MEWMA y la MCUSUM (el límite superior de control) pasa a `ucl` y no a `limit`; el `kind` de la carta de varianza
   generalizada también pasa a inglés; y el formato de los archivos de Fase I no cambia (ya usaba claves en inglés).

## Preguntas abiertas

Ninguna.
