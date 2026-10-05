# Idioma de los mensajes

```{note}
**Estado: disponible desde la versión 0.11.0; el inglés está pendiente de revisión por una persona del dominio SPC.** Se traducen al inglés los **mensajes de error y de aviso**, los
**`summary()`** y las **etiquetas de `to_frame()`** de los resultados, los **gráficos** y el asistente (`wizard`); también `pareto()`, las curvas OC/AOQ, las tablas ANOVA y de kappa (con `anova_frame()`, `kappa_within_frame()` y `kappa_vs_reference_frame()`) y las hojas de `to_excel()`: todas aceptan `stable=True` para claves fijas, salvo los atributos `anova_table`, `kappa_within` y `kappa_vs_reference`, que conservan siempre las cabeceras en español.
```

pccpy escribe sus textos en **español**, que es el idioma fuente: si un idioma no tiene traducción para un texto,
se muestra el original. La documentación y el README también están en inglés ([Cómo traducir](traducir.md)). Idiomas disponibles: `es` y `en` (cómo corregir o añadir uno: [Cómo traducir](traducir.md)).

```python
import pccpy as pp

with pp.language("en"):
    pp.diagnose([1.0, 2.0, 3.0])
# ValueError: diagnose requires at least 4 observations.
```

## Elegir el idioma

```python
import pccpy as pp

pp.available_languages()      # ['en', 'es']
pp.get_language()             # 'es'

pp.set_language("en")         # para todo el proceso (visible desde cualquier hilo)
pp.set_language("en_US")      # también valen variantes: 'en-US', 'EN', 'en.UTF-8'
pp.set_language("es")
```

Un idioma que no existe lanza `ValueError` (con la lista de idiomas disponibles).

## Solo dentro de un bloque

```python
with pp.language("en"):
    ...                       # aquí los textos salen en inglés
# fuera del bloque vuelve el idioma anterior
```

```{warning}
Un hilo creado **dentro** de `with pp.language(...)` no hereda ese idioma: usa el global.
Para que lo vea cualquier hilo, usa {func}`~pccpy.set_language`.
```

## Tablas (`to_frame`) con claves que no cambian con el idioma

Las cabeceras de `to_frame()` y `violations()` son **presentación**: salen en el idioma activo, como `summary()`.
Para código que indexa la tabla por nombre, usa `stable=True`: devuelve claves canónicas en inglés (`snake_case`)
que son iguales en cualquier idioma.

```python
r = pp.capability_analysis(datos, lsl=44, usl=56)

r.to_frame()                       # índice: 'N', 'Media', 'Desv.Est. (dentro)', … (en inglés: 'N', 'Mean', …)
r.to_frame(stable=True)["value"]["cpk"]   # igual en es y en
```

Las tablas de estadísticos tienen el índice `statistic` y la columna `value`; las de puntos
(`ControlChart.to_frame`, `violations`) usan `point`, `stage`, `value`, `cl`, `ucl`, `lcl`, `test`, `description`…

```{note}
Los valores de datos (p. ej. `DiagnoseResult.trend_direction`, `'creciente'`/`'decreciente'`, o los nombres de
parámetros como `chart.params[0]["media"]`) **no se traducen**: solo se muestran traducidos en `summary()`.
Los textos que un resultado guarda al crearse (p. ej. `DiagnoseResult.issues`) quedan en el idioma activo en ese momento.
```

## Variable de entorno

`PCCPY_LANG=en` fija el idioma inicial al importar `pccpy`. Si el valor no es un idioma disponible,
se muestra un aviso y se usa `es`; nunca impide importar la librería.

## Para quien contribuye con traducciones

El código marca los textos con `tr("…")` (se traducen al mostrarse) o `N_("…")` (constantes de módulo, que se
traducen al usarlas con `tr()`). Los f-strings **no** se pueden traducir: usa
`tr("'{name}' está vacío.").format(name=name)`. Comandos:

```bash
make i18n-update      # extrae los textos y actualiza los .po
make i18n-compile     # compila los .po a .mo (los .mo se versionan)
make i18n-check       # el CI lo exige: catálogos al día, sin textos sin traducir ni marcadores {…} distintos
```
