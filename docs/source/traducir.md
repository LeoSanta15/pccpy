# Cómo traducir pccpy

El idioma fuente es el **español**; cada idioma adicional es un catálogo `gettext` (`src/pccpy/locale/<código>/LC_MESSAGES/pccpy.po`).
Hoy existe `en` (inglés). Esta guía explica cómo corregir una traducción o añadir un idioma.

## Corregir una traducción

1. Busca el texto en español en `src/pccpy/locale/en/LC_MESSAGES/pccpy.po` y edita su `msgstr`.
2. Compila y comprueba:

```bash
make i18n-compile      # genera el .mo
make i18n-check        # catálogo al día, sin textos sin traducir, mismos {marcadores}
python -m pytest tests/test_i18n_glosario.py tests/test_i18n_errores.py
```

## Reglas

- **Marcadores `{nombre}`:** deben ser idénticos en el original y la traducción (`{n:.2f}` incluido). `make i18n-check` falla si no.
- **Espacios y alineación:** las tablas de `summary()` se alinean con espacios dentro del texto; conserva el ancho de las columnas
  (los tests comparan las líneas de ambos idiomas).
- **Saltos de línea y sangría** de los textos de varias líneas (por ejemplo, los fragmentos de código del asistente): se conservan.
- **Código:** `pp.función(...)`, nombres de parámetros y valores como `'weibull'` **no se traducen**.
- **Claves estables:** `to_frame(stable=True)` y similares usan claves en inglés fijas; no dependen del catálogo.
- **Glosario:** usa siempre el mismo término para el mismo concepto (tabla de abajo; lo comprueba `tests/test_i18n_glosario.py`).

## Revisar el catálogo

```bash
python scripts/i18n_revision.py > revision_en.md   # tabla español | inglés para marcar ✔ / ✎ / ?
```

## Traducir la documentación

La documentación (Sphinx) y el README también se traducen. Las páginas usan catálogos `gettext` en `docs/locales/<idioma>/LC_MESSAGES/`
(uno por página, incluidas las descripciones de la API, que salen de los docstrings); el README en inglés es `README_en.md`.

```bash
make docs-update     # extrae los textos y actualiza los catálogos (traduce después los msgstr nuevos)
make docs-en         # construye la documentación en inglés (con -W)
make docs-check      # catálogos al día, sin textos vacíos, mismas referencias de Sphinx, sin español sin traducir
```

- Conserva los roles (`{doc}`…``, `:func:`…``), las URL, los fragmentos de código y las negritas: `make docs-check` lo comprueba.
- En las páginas Markdown, escribe los roles de las descripciones de la API con la sintaxis de MyST (`{func}`nombre``), no con la de RST.
- El historial de versiones (`changelog`) se deja en español.

## Añadir un idioma

```bash
pybabel init -i src/pccpy/locale/pccpy.pot -d src/pccpy/locale -D pccpy -l fr   # crea fr/LC_MESSAGES/pccpy.po
# traducir todos los msgstr (ninguno puede quedar vacío ni «fuzzy»)
make i18n-compile && make i18n-check
```

Después, `pccpy.available_languages()` lo incluye automáticamente. Si cambian textos en el código: `make i18n-update` actualiza
los catálogos y marca lo modificado como *fuzzy* para revisarlo.

## Glosario español → inglés

La traducción al inglés sigue la terminología de Minitab y de la bibliografía SPC. **Pendiente de revisión por una persona del dominio.**

| Español | Inglés |
|---|---|
| carta de control | control chart |
| límite de control | control limit |
| línea central | center line |
| subgrupo | subgroup |
| observación | observation |
| capacidad (del proceso) | capability |
| desviación estándar | standard deviation |
| intervalo de tolerancia | tolerance interval |
| muestreo de aceptación | acceptance sampling |
| causa especial | special-cause |
| repetibilidad | repeatability |
| reproducibilidad | reproducibility |
| sesgo | bias |
| linealidad | linearity |
| concordancia | agreement |
| fracción defectuosa | fraction defective |
| p-valor / valor p | p-value |
| mediana | median |
| rango | range |
| especificación | specification |
| defectuosos | defective |
| tamaño de muestra | sample size |
| normalidad | normality |
| atípico | outlier |
| tendencia | trend |
| mezcla | mixture |
| agrupamiento | clustering |
| oscilación | oscillation |
| operador | operator |
| parte | part |
| dentro (del subgrupo) | within |
| general | overall |
