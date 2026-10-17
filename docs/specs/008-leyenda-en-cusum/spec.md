# 008 — Leyenda de las dos sumas en el gráfico de la CUSUM

- **Estado:** implementada
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
- Opciones para elegir la posición de la leyenda o sus textos.

## Requisitos

### S008-RF-01 — Leyenda en los paneles con segunda serie

El sistema debe mostrar por defecto, en todo panel que dibuje una segunda serie, una leyenda con un nombre para cada
serie: «C+ (suma superior)» para la primera y «C- (suma inferior)» para la segunda (ver S008-RF-04 para quitarla).

**Aceptación:**
- **Dado** `cusum_chart(...)` (y la CUSUM de atributos) **cuando** se dibuja con `plot()` **entonces** el eje del panel
  tiene una leyenda con dos entradas, «C+ (suma superior)» y «C- (suma inferior)», asociadas a las líneas azul y naranja.
- **Dado** una carta sin segunda serie (I-MR, Xbar-R, EWMA, G, T…) **cuando** se dibuja **entonces** ningún panel tiene
  leyenda.
- **Referencia independiente:** no es un resultado numérico; se comprueba inspeccionando los objetos de matplotlib (las
  etiquetas de las líneas y el texto de la leyenda).

### S008-RF-04 — La leyenda es opcional

El sistema debe permitir quitar la leyenda con el parámetro `legend` de `plot_control_chart` (y, por tanto, de
`ControlChart.plot()` y `save_plot()`, que le pasan sus argumentos). Por defecto `legend=True`.

**Aceptación:**
- **Dado** `chart.plot(legend=False)` **cuando** se dibuja una CUSUM **entonces** ningún panel tiene leyenda y el resto del
  dibujo (líneas, valores, límites, anotaciones) es el mismo que con `legend=True`.
- **Dado** `chart.plot(legend=True)` o sin el parámetro **entonces** la leyenda aparece como en S008-RF-01.
- **Dado** una carta sin segunda serie **cuando** se dibuja con `legend=True` **entonces** sigue sin leyenda.
- **Referencia independiente:** no es un resultado numérico; se comprueban los objetos de matplotlib.

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
| Panel con una sola serie | Sin leyenda, también con `legend=True` |
| `legend` que no es un booleano | Se interpreta como verdadero o falso (sin validación propia) |

## Resultados existentes que cambian

Ningún resultado numérico. Cambia el dibujo de `cusum_chart` y de la CUSUM de atributos: ahora llevan leyenda. Se lista en
el CHANGELOG como cambio visual.

## No verificable sin la fuente

No se ha comparado con el gráfico de Minitab (no se puede ejecutar aquí); no se afirma que Minitab dibuje esa leyenda.

## Decisiones de la persona responsable

1. **Visible por defecto:** la leyenda se muestra en los paneles con segunda serie. Descartado: dejarla opt-in.
   *(Revisada el 2026-10-17 por la persona responsable: ver la decisión 3.)*
2. **Nombres:** «C+ (suma superior)» y «C- (suma inferior)». Descartado: «Suma superior» y «Suma inferior» sin la notación.

3. **Opcional:** la persona responsable pidió que la leyenda sea opcional (después de implementarla siempre visible).
   Se añade `legend` (S008-RF-04). Interpretación del agente, a confirmar: «opcional» = se puede quitar con
   `legend=False` y por defecto sigue visible, como decidió en la decisión 1. Si prefería que por defecto esté
   oculta, basta cambiar el valor por defecto (`legend=False`) y la guarda de RF-04.

## Preguntas abiertas

Ninguna.
