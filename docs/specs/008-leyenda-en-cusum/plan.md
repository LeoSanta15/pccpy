# Plan — 008 Leyenda de las dos sumas en el gráfico de la CUSUM

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (principios 3, 5 y 7; ver las preguntas abiertas sobre opt-in).

## Diseño

- `plotting.py`, `_draw_panel`: poner `label=` a las dos líneas del panel con `secondary` y llamar a `ax.legend()` solo
  en ese caso. El panel azul pasa a llamarse «Suma superior» y la naranja «Suma inferior». Las demás líneas del panel
  no llevan etiqueta, para que la leyenda tenga solo dos entradas.
- `charts/timeweighted.py` y `charts/timeweighted_attr.py` no cambian: el dibujo ya recibe `secondary`. Hoy `secondary`
  solo lo usan esas dos cartas; si otra carta lo usara con otro significado, habría que añadir un campo al panel con el
  nombre de cada serie.
- Textos con `tr()` y traducción en `pccpy.po` (R-17).

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Leyenda con `ax.legend()` en el panel | Etiquetas al borde como LCS/LC/LCI | Las dos series se solapan en el eje; un nombre junto al borde no dice cuál es cuál |
| Nombre derivado del hecho de que haya `secondary` | Campo nuevo en `Panel` | Cambio mínimo; el campo solo se necesita si aparece otro uso |

(Provisional hasta resolver las preguntas abiertas de la spec.)

## Validación independiente

Sin comprobación en `run_validation()`: no hay resultado numérico. Los tests inspeccionan los objetos de matplotlib
(`ax.get_legend()`, `line.get_label()`) con backend `Agg`.

## Riesgos

- La leyenda puede tapar datos o las anotaciones del borde derecho (`loc="best"` y revisar un gráfico real).
- Una leyenda por etapa duplicaría las entradas: se crea una sola vez por panel, fuera del bucle de etapas.

## Documentación y traducciones

CHANGELOG (cambio visual), catálogo `.po` (`make i18n-update`, traducir, `make i18n-compile`) y, si alguna página muestra
la imagen del gráfico CUSUM, revisar su descripción.
