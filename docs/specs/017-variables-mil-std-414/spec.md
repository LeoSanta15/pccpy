# 017 — Planes de muestreo por variables: MIL-STD-414 (la «Z1.9 real» queda pendiente)

- **Estado:** borrador
- **Identificador:** S017
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** por decidir (cambia resultados existentes: los planes de la tabla aproximada actual; versión menor salvo decisión contraria)

## Problema

`acceptance_sampling_variables` presenta sus planes como ANSI/ASQ Z1.9, pero la tabla incluida es una aproximación que **no reproduce la norma**, y la
propia función avisa: *«La tabla Z1.9 incluida es una aproximación que no reproduce la norma (los planes que da pueden aceptar casi cualquier lote)»*.
Hoy tiene solo 6 AQL (0,10 a 4,0 %) y las letras B a K con pares `(n, k)` «simplificados», usa la tabla I de **Z1.4** para la letra de código (con un
desplazamiento de ±2 para los niveles 1 y 3), no tiene inspección rigurosa y calcula la curva OC con una aproximación normal.

La persona responsable aportó las tablas **A-2 y B-1 de MIL-STD-414 (11 de junio de 1957)**, el predecesor de Z1.9, **no las de Z1.9**. MIL-STD-414 es un documento del
gobierno de EE. UU. (una base limpia para implementar), pero no es Z1.9: la tabla A-2 tiene los niveles de inspección I a V y otros tramos de lote (Z1.9 usa S3, S4, I, II
y III con los tramos reagrupados), y los AQL disponibles difieren. No se afirma que los valores de `k` coincidan con los de Z1.9 (no se pudo verificar).

**Decisión de la persona responsable (opción A):** implementar **MIL-STD-414 con nombre propio** y no llamarlo Z1.9. La Z1.9 real queda pendiente de sus tablas.

## Fuera de alcance

- **ANSI/ASQ Z1.9:** sin sus tablas; se hará en otra especificación cuando se aporten.
- **Curva OC exacta** (distribución t no central) en lugar de la aproximación normal: se hace aparte, para que el cambio por las tablas se revise solo (decidido).
- **Forma 2** (estimar el porcentaje no conforme y compararlo con un máximo `M`), inspección **reducida**, método del **rango**, variabilidad **conocida** y las reglas de cambio:
  sin sus tablas.
- Afirmar equivalencia con Minitab o con Z1.9: no se midió.

## Requisitos

Todos parten de las tablas transcritas del anexo (capturas de la norma, no de su texto).

### S017-RF-01 — Letra de código de MIL-STD-414 (tabla A-2)

La letra sale de la tabla A-2 (17 tramos de lote × niveles de inspección I a V; el anexo la transcribe) y no de la tabla I de Z1.4. Se eliminan el desplazamiento ±2 y la
dependencia de `_letra_codigo` de Z1.4.

**Aceptación:**
- **Dado** cada tramo de lote y nivel (enteros 1 a 5, con `4` por defecto) **entonces** la letra coincide con la tabla A-2 del anexo (los dos extremos de cada tramo y un punto interior).
- **Dado** un nivel inexistente (0, 6, `"IV"`, `None`) **entonces** `ValueError` en español.
- **Referencia independiente:** la tabla A-2 de la captura, transcrita en un test aparte del código y revisada por la persona responsable.

### S017-RF-02 — Planes `(n, k)` de la tabla B-1, inspección normal

`acceptance_sampling_variables(..., standard="mil-std-414")` devuelve, para cada letra (B a Q) y cada AQL de la tabla (0,04 a 15,00 %), el `n` y el `k` de la tabla,
resolviendo las flechas como indica la norma («usar el primer plan por debajo de la flecha, es decir, tanto el tamaño de muestra como el valor de `k`»).

**Aceptación:**
- **Dado** cada celda (letra × AQL) de la tabla B-1 **entonces** `(n, k)` coincide con el anexo, incluidas las celdas con flecha (que apuntan al primer plan numerado por debajo en la misma columna).
- **Dado** `n=` y `k=` explícitos **entonces** el plan se usa tal cual (plan a medida), sin cambios y sin aviso.
- **Dado** el plan de la tabla de MIL-STD-414 **entonces** no se emite el aviso de «aproximación».
- **Referencia independiente:** la tabla B-1 de la captura (transcripción en un test aparte; la persona responsable la revisa celda a celda).

### S017-RF-03 — Inspección rigurosa

Con `inspection="tightened"` se usa la misma tabla B-1 con la columna **desplazada una posición**: el plan de un AQL rigurosa es el de la columna del AQL inmediatamente inferior (la fila inferior de la
tabla rotula las columnas con los AQL de la inspección rigurosa: 0,065 a 15,00 %; no hay rigurosa con AQL 0,04).

**Aceptación:**
- **Dado** `inspection="tightened"` y un AQL de la fila inferior de la tabla **entonces** `(n, k)` es el de la columna normal desplazada (p. ej. rigurosa 1,00 % usa la columna normal 0,65 %).
- **Dado** un AQL sin plan riguroso (0,04 %) **entonces** `ValueError` en español.

### S017-RF-04 — Criterio de aceptación de la Forma 1

`SamplingPlanVariables.evaluate` acepta con especificación unilateral si `Q = (U − x̄)/s ≥ k` (o `(x̄ − L)/s ≥ k`); no cambia respecto de hoy.

**Aceptación:** `evaluate` con datos construidos a mano coincide con la fórmula (cálculo aparte). Pasa antes del código (protege algo que no cambia).

### S017-RF-05 — Guarda del 100 % de inspección

Si el `n` de la tabla es igual o mayor que `N`, el plan lleva `n = N` y un `UserWarning` en español (la norma: «cuando el tamaño de muestra es igual o mayor que el del lote, todas las unidades del lote
deben inspeccionarse»; como Z1.4, S016-RF-04).

**Aceptación:** `N` pequeño con un `n` de la tabla ≥ `N` devuelve `n = N` con aviso; con planes que caben no cambia nada.

### S017-RF-06 — Parámetro `standard` y retirada de la tabla aproximada

`standard` acepta `"mil-std-414"`. `"z1.9"` lanza `ValueError` en español que explica que las tablas de Z1.9 no están disponibles y propone `standard="mil-std-414"` o `n=` y `k=`. Se elimina la tabla
aproximada `_Z19_TABLE` y su aviso.

**Aceptación:**
- **Dado** `standard="z1.9"` **entonces** `ValueError` con ese mensaje.
- **Dado** cualquier llamada sin `n=` y `k=` **entonces** el resultado sale de las tablas de MIL-STD-414 (el nombre del método del resultado es `"mil-std-414"`).
- **Dado** un AQL que no está en la tabla (o `spec_type="two"`) **entonces** `ValueError` en español.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| AQL que no está en la tabla | `ValueError` en español (los AQL son valores preferidos; decidido) |
| Celda con flecha | Primer plan numerado por debajo, misma columna |
| `n` de la tabla ≥ `N` | Inspección al 100 % con aviso (RF-05) |
| `spec_type="two"` | `ValueError` en español que explica que la Forma 1 no cubre la doble especificación (sin tablas de la Forma 2; decidido) |
| `n=` sin `k=` (o al revés) | `ValueError` en español |
| Letra B a Q, nivel I a V | Todas las combinaciones de A-2 tienen plan |

## Resultados existentes que cambian

Cambian **todos los planes de `acceptance_sampling_variables` que salen de la tabla** (no los que se dan con `n=` y `k=`): `n`, `k`, `alpha` y `ltpd` serán distintos, el nivel por defecto y el
significado de `inspection_level` cambian (hoy 1, 2 y 3 con un desplazamiento de la letra de Z1.4) y desaparece el aviso de aproximación. Se listan en «Cambios que alteran resultados» del CHANGELOG con el valor anterior y el nuevo.

## No verificable sin la fuente

- Todo se contrasta con **capturas** de las tablas A-2 y B-1 de MIL-STD-414, no con el texto del documento: una lectura errónea de una celda pasaría desapercibida. Dos celdas dudosas de la copia se confirmaron con
  la persona responsable (B-1, letra I con AQL 0,25: **2,26**, no 3,26; A-2, último nivel de «550 001 o más»: **Q**).
- No se midió si Minitab devuelve los mismos planes, ni si los valores de MIL-STD-414 coinciden con los de ANSI/ASQ Z1.9.
- Que el nivel de inspección por defecto sea el IV se recuerda de memoria; debe confirmarse con el texto de la norma.

## Preguntas abiertas

Ninguna. Decididas por la persona responsable (con las recomendaciones de la propuesta):

1. **Niveles:** enteros 1 a 5 (los niveles I a V de la norma), con `4` por defecto. Que el IV sea el nivel normal se recuerda de memoria y debe confirmarse con el texto de MIL-STD-414.
2. **Doble especificación:** `spec_type="two"` lanza `ValueError` que explica que la Forma 1 no la cubre (la Forma 2 no tiene tablas). Alternativa descartada: aplicar la Forma 1 a cada lado con aviso.
3. **AQL fuera de la tabla:** `ValueError` (son valores preferidos). Alternativa descartada: el más cercano.
4. **Curva OC exacta:** fuera de esta especificación (se hace aparte). Alternativa descartada: incluirla como RF-07.
5. **`standard="z1.9"`:** `ValueError` honesto (no hay tablas de Z1.9). Alternativa descartada: alias de MIL-STD-414 con aviso.

## Anexo — tablas transcritas (para revisar celda a celda)

### Tabla A-2 de MIL-STD-414: letras de código por tamaño de lote y nivel de inspección

| Lote | I | II | III | IV | V |
|---|---|---|---|---|---|
| 3 a 8 | B | B | B | B | C |
| 9 a 15 | B | B | B | B | D |
| 16 a 25 | B | B | B | C | E |
| 26 a 40 | B | B | B | D | F |
| 41 a 65 | B | B | C | E | G |
| 66 a 110 | B | B | D | F | H |
| 111 a 180 | B | C | E | G | I |
| 181 a 300 | B | D | F | H | J |
| 301 a 500 | C | E | G | I | K |
| 501 a 800 | D | F | H | J | L |
| 801 a 1 300 | E | G | I | K | L |
| 1 301 a 3 200 | F | H | J | L | M |
| 3 201 a 8 000 | G | I | L | M | N |
| 8 001 a 22 000 | H | J | M | N | O |
| 22 001 a 110 000 | I | K | N | O | P |
| 110 001 a 550 000 | I | K | O | P | Q |
| 550 001 o más | I | K | P | Q | Q |

### Tabla B-1 de MIL-STD-414: `k` por letra y AQL (inspección normal; método de la desviación estándar, especificación unilateral, Forma 1)

`↓` = usar el primer plan por debajo de la flecha (tanto `n` como `k`). Los AQL son % de defectuosos. Inspección rigurosa: la misma tabla con la columna desplazada una posición (AQL rigurosa .065, .10, .15, .25, .40, .65,
1.00, 1.50, 2.50, 4.00, 6.50, 10.00, 15.00 sobre las columnas normales .04 a 10.00).

| Letra | n | .04 | .065 | .10 | .15 | .25 | .40 | .65 | 1.00 | 1.50 | 2.50 | 4.00 | 6.50 | 10.00 | 15.00 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | 3 | ↓ | ↓ | ↓ | ↓ | ↓ | ↓ | ↓ | ↓ | ↓ | 1.12 | .958 | .765 | .566 | .341 |
| C | 4 | ↓ | ↓ | ↓ | ↓ | ↓ | ↓ | ↓ | 1.45 | 1.34 | 1.17 | 1.01 | .814 | .617 | .393 |
| D | 5 | ↓ | ↓ | ↓ | ↓ | ↓ | ↓ | 1.65 | 1.53 | 1.40 | 1.24 | 1.07 | .874 | .675 | .455 |
| E | 7 | ↓ | ↓ | ↓ | ↓ | 2.00 | 1.88 | 1.75 | 1.62 | 1.50 | 1.33 | 1.15 | .955 | .755 | .536 |
| F | 10 | ↓ | ↓ | ↓ | 2.24 | 2.11 | 1.98 | 1.84 | 1.72 | 1.58 | 1.41 | 1.23 | 1.03 | .828 | .611 |
| G | 15 | 2.64 | 2.53 | 2.42 | 2.32 | 2.20 | 2.06 | 1.91 | 1.79 | 1.65 | 1.47 | 1.30 | 1.09 | .886 | .664 |
| H | 20 | 2.69 | 2.58 | 2.47 | 2.36 | 2.24 | 2.11 | 1.96 | 1.82 | 1.69 | 1.51 | 1.33 | 1.12 | .917 | .695 |
| I | 25 | 2.72 | 2.61 | 2.50 | 2.40 | 2.26 | 2.14 | 1.98 | 1.85 | 1.72 | 1.53 | 1.35 | 1.14 | .936 | .712 |
| J | 30 | 2.73 | 2.61 | 2.51 | 2.41 | 2.28 | 2.15 | 2.00 | 1.86 | 1.73 | 1.55 | 1.36 | 1.15 | .946 | .723 |
| K | 35 | 2.77 | 2.65 | 2.54 | 2.45 | 2.31 | 2.18 | 2.03 | 1.89 | 1.76 | 1.57 | 1.39 | 1.18 | .969 | .745 |
| L | 40 | 2.77 | 2.66 | 2.55 | 2.44 | 2.31 | 2.18 | 2.03 | 1.89 | 1.76 | 1.58 | 1.39 | 1.18 | .971 | .746 |
| M | 50 | 2.83 | 2.71 | 2.60 | 2.50 | 2.35 | 2.22 | 2.08 | 1.93 | 1.80 | 1.61 | 1.42 | 1.21 | 1.00 | .774 |
| N | 75 | 2.90 | 2.77 | 2.66 | 2.55 | 2.41 | 2.27 | 2.12 | 1.98 | 1.84 | 1.65 | 1.46 | 1.24 | 1.03 | .804 |
| O | 100 | 2.92 | 2.80 | 2.69 | 2.58 | 2.43 | 2.29 | 2.14 | 2.00 | 1.86 | 1.67 | 1.48 | 1.26 | 1.05 | .819 |
| P | 150 | 2.96 | 2.84 | 2.73 | 2.61 | 2.47 | 2.33 | 2.18 | 2.03 | 1.89 | 1.70 | 1.51 | 1.29 | 1.07 | .841 |
| Q | 200 | 2.97 | 2.85 | 2.73 | 2.62 | 2.47 | 2.33 | 2.18 | 2.04 | 1.89 | 1.70 | 1.51 | 1.29 | 1.07 | .845 |
