# Idioma de los mensajes

```{note}
**Estado: en desarrollo (fase 1 de 5).** Hoy se traducen al inglés los **mensajes de error y de aviso**
(las `ValueError`, `TypeError`, `ImportError` y `UserWarning` de las funciones). El resto de los textos
(`summary()`, etiquetas de `to_frame()` y gráficos) se migra por fases y sigue en español hasta entonces.
```

pccpy escribe sus textos en **español**, que es el idioma fuente: si un idioma no tiene traducción para un texto,
se muestra el original. Idiomas disponibles: `es` y `en` (`en` irá completándose por fases).

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
