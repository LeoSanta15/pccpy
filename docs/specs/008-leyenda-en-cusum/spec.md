# 008 — Leyenda de las dos sumas en el gráfico de la CUSUM

- **Estado:** borrador
- **Identificador:** S008
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.4 (cambia solo el dibujo, no los resultados; parche según CLAUDE.md)

## Problema

El gráfico de la CUSUM dibuja dos series en el mismo panel: la suma superior (azul) y la suma inferior (naranja, en
negativo). Ninguna lleva nombre, así que quien mira el gráfico no puede saber cuál es cuál sin leer el código (se
descubrió al preguntar qué representaban). Las demás líneas sí se identifican: `plot_control_chart` ya anota al borde
derecho `LCS=…`, `LC=…` y `LCI=…` con su valor (`plotting.py`, `_draw_panel`); los puntos que fallan una prueba llevan el
número de la prueba. Las dos series de la CUSUM son lo único del panel que no se explica.

Afecta a las dos cartas con una segunda serie: `cusum_chart` y la CUSUM de atributos (`charts/timeweighted_attr.py`).

## Fuera de alcance

- Etiquetas con valor al borde derecho de LCS, LC y LCI: ya existen.
- Una leyenda para las líneas de zonas (±1σ, ±2σ) y para los cuadros rojos de las pruebas.
- Cambiar los colores, los marcadores, los valores o las columnas de `to_frame()`.

## Requisitos

### S008-RF-01 — Leyenda en los paneles con segunda serie

El sistema debe mostrar, en todo panel que dibuje una segunda serie, una leyenda con un nombre para cada serie: «Suma
superior» para la primera y «Suma inferior» para la segunda.

**Aceptación:**
- **Dado** `cusum_chart(...)` (y la CUSUM de atributos) **cuando** se dibuja con `plot()` **entonces** el eje del panel
  tiene una leyenda con dos entradas, «Suma superior» y «Suma inferior», asociadas a las líneas azul y naranja.
- **Dado** una carta sin segunda serie (I-MR, Xbar-R, EWMA, G, T…) **cuando** se dibuja **entonces** ningún panel tiene
  leyenda.
- **Referencia independiente:** no es un resultado numérico; se comprueba inspeccionando los objetos de matplotlib (las
  etiquetas de las líneas y el texto de la leyenda).

### S008-RF-02 — No cambia nada más

El sistema no debe cambiar los datos ni el resto del dibujo.

**Aceptación:**
- **Dado** una CUSUM **cuando** se dibuja **entonces** los valores de las dos series, los límites, las anotaciones al
  borde y los puntos marcados son los mismos que antes; `to_frame()`, `violations()` y `summary()` no cambian.
- **Dado** que se dibuja una carta **cuando** termina `plot()` **entonces** `matplotlib.rcParams` queda igual que antes
  (R-08).

### S008-RF-03 — Texto traducible

El texto de la leyenda debe estar en español y en inglés con el mecanismo de `tr()` (R-17).

**Aceptación:**
- **Dado** `pp.language("en")` **cuando** se dibuja la CUSUM **entonces** las entradas de la leyenda están en inglés y son
  distintas de las españolas.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| CUSUM con varias etapas | Una sola leyenda por panel, sin entradas repetidas por etapa |
| CUSUM sin ninguna señal | Leyenda igual |
| Gráfico con `zones=False` | Leyenda igual |
| Leyenda sobre los datos | Se coloca donde estorbe menos (`loc="best"`) y no tapa las anotaciones del borde derecho |
| Panel con una sola serie | Sin leyenda |

## Resultados existentes que cambian

Ningún resultado numérico. Cambia el dibujo de `cusum_chart` y de la CUSUM de atributos: ahora llevan leyenda. Se lista en
el CHANGELOG como cambio visual.

## No verificable sin la fuente

No se ha comparado con el gráfico de Minitab (no se puede ejecutar aquí); no se afirma que Minitab dibuje esa leyenda.

## Decisiones de la persona responsable

(pendiente)

## Preguntas abiertas

- [NECESITA ACLARACIÓN: ¿La leyenda se muestra siempre en estos paneles, o solo con un parámetro (`plot(legend=True)`)?
  Propuesta: siempre, porque sin ella el gráfico es ambiguo, con `legend=False` para quitarla. La alternativa opt-in es
  más conservadora (principio 3 de la constitución) pero deja el gráfico ambiguo por defecto.]
- [NECESITA ACLARACIÓN: nombres de las entradas. Propuesta: «Suma superior» y «Suma inferior». Alternativa: «C⁺ (suma
  superior)» y «C⁻ (suma inferior)», más cercana a la notación de los libros pero menos legible para quien no la conoce.]
