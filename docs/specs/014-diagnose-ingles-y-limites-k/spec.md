# 014 — Valores en inglés de `diagnose()` y ancho de los límites de control

- **Estado:** aprobada
- **Identificador:** S014
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.6 (decisión de la persona responsable; la parte A es incompatible y se anuncia en el CHANGELOG, sin alias; la parte B no cambia ningún resultado con `k=3`).

Fusiona las antiguas especificaciones 014 (dirección de la tendencia) y 015 (ancho de los límites), por decisión de la persona responsable.

## Problema

**A. Un valor de código en español.** `DiagnoseResult.trend_direction` devuelve `'creciente'` o `'decreciente'` (o `''`): un valor de código en español que no depende del idioma
elegido. Mismo principio de la spec 012: el código y los datos con clave van en inglés; solo lo que se muestra depende del idioma.

**B. Límites siempre a ±3σ.** Las cartas I-MR, Xbar-R, Xbar-S, P, NP, C, U, Laney P'/U', Z-MR e I-MR-R/S trazan siempre los límites a ±3σ. Otras cartas (EWMA, MA, G, T y la varianza
generalizada con `k`; T² con `alpha`) sí tienen el parámetro. Quien quiere límites más estrechos o más anchos, o distintos arriba y abajo, no puede pedirlos.
Hay además una incoherencia que existe hoy: `test_params={1: 2.0}` hace que la prueba 1 marque los puntos a más de 2σ, pero **los límites dibujados siguen en 3σ** (con 200 datos normales la UCL de
`imr_chart` es 2,778 con o sin el parámetro y las violaciones pasan de 5 a 22).

## Fuera de alcance

- De la parte A: `issues`, `recommended_snippet` y demás textos que se muestran (siguen traduciéndose); otros valores de `DiagnoseResult` (`non_normal_reason` ya devuelve `'outliers'`, `'skewed'`, `'shape'`); revisar otros módulos (si se encuentra otro valor de código en español, se anota aparte).
- De la parte B: límites por percentiles en las cartas de Shewhart (para datos asimétricos está `transform=`); la carta de zona (sus pesos están definidos sobre 3σ), EWMA, CUSUM, MA, G, T y multivariadas, que ya tienen su parámetro;
  `phase_one()` (se estudia aparte si se pide); convertir `k` en un nivel de confianza exacto fuera de los paneles normales (la probabilidad real la da `chart.probability()`); afirmar equivalencia con Minitab (no se pudo comprobar si ofrece un ancho distinto de 3σ en cada carta).

## Requisitos

## Parte A — `diagnose()`

### S014-RF-01 — Valores en inglés

`trend_direction` devuelve `'increasing'`, `'decreasing'` o `''`, iguales en cualquier idioma. Sin alias: `'creciente'`/`'decreciente'` dejan de existir
(consistente con la decisión de la spec 012).

**Aceptación:**
- **Dado** datos con tendencia creciente/decreciente **cuando** se llama a `diagnose()` **entonces** `trend_direction` es `'increasing'`/`'decreasing'`
  con el idioma `es` y con `en`.
- **Referencia independiente:** el signo de la pendiente de una recta de mínimos cuadrados (`scipy.stats.linregress`) sobre los datos del test.

### S014-RF-02 — Lo que se muestra sigue traducido

`summary()` y el texto «Se detectó tendencia …» muestran «creciente»/«decreciente» en español y «increasing»/«decreasing» en inglés
(`_tendencia()` traduce desde las claves inglesas). `to_frame()` conserva su regla (los golden `i18n_es.json` e `i18n_stable.json` cambian solo en esas celdas, de forma deliberada): las etiquetas se traducen y los valores son iguales en cualquier idioma, así que muestra
el valor canónico `increasing`/`decreasing`.

**Aceptación:** el texto de `summary()` en español queda **idéntico** al de `tests/golden/i18n_es.json` (que no se regenera); en inglés se
muestra la traducción. `to_frame()` (con y sin `stable`) da el valor canónico en inglés en cualquier idioma.

### S014-RF-03 — Código y documentación

Los literales de `src/`, tests, README, guías y catálogos usan los valores nuevos; una sola lista de equivalencias se escribe en el CHANGELOG para que quien
compare con `'creciente'` sepa qué cambiar.

**Aceptación:** `grep -rn "'creciente'\|\"creciente\"\|'decreciente'\|\"decreciente\"" src tests docs README*.md` solo encuentra la tabla de
traducción de `_tendencia()`, los golden y el CHANGELOG.

## Parte B — ancho de los límites (`k` y `alpha`)

### S014-RF-04 — `k` en I-MR, Xbar-R y Xbar-S

`imr_chart`, `xbar_r_chart` y `xbar_s_chart` ganan `k: float | tuple[float, float] = 3.0` y `alpha: float | tuple[float, float] | None = None` (S014-RF-11: son excluyentes
y `alpha` se convierte en `k`). **Un valor** `k`: límites simétricos `centro ± k·σ` (`σ/√nᵢ` en Xbar). **Un par** `(k_sup, k_inf)`: `UCL = centro + k_sup·σ` y `LCL = centro − k_inf·σ`.
En los paneles de dispersión (MR, R, S): `UCL = centro + k_sup·sd` y `LCL = max(0, centro − k_inf·sd)`, con `sd` la desviación del estadístico (`d3·σ` o `c5·σ`).

**Aceptación:**
- **Dado** `k=(3, 2)` **entonces** `ucl − center == 3·σ` y `center − lcl == 2·σ`.
- **Dado** `k=2` **cuando** se construye la carta **entonces** `ucl − center == 2·σ` en I y `UCL(R) − center == 2·d3·σ`.
- **Dado** `alpha=0.0455` **entonces** el resultado coincide con `k=2`; **dado** `alpha=(0.00135, 0.025)` **entonces** `k=(3, 1.96)` (hasta la tolerancia de la conversión).
- **Dado** `k=3` (o sin `k`) **entonces** todos los valores coinciden con los de hoy (golden y tests existentes sin cambios).
- **Referencia independiente:** cálculo manual con `d2`, `d3`, `c4`, `c5` de Montgomery.

### S014-RF-05 — `k` en las cartas de atributos

`p_chart`, `np_chart`, `c_chart`, `u_chart`, `laney_p_chart` y `laney_u_chart` ganan `k` y `alpha` con el mismo formato (valor o par; S014-RF-11): `centro ± k·σᵢ`, con `k_sup` arriba y `k_inf` abajo (o `k` en los dos lados con un valor), el LCL recortado a 0 y el
UCL de P y Laney P' recortado a 1 como hoy.

**Aceptación:** con `k=2` los límites de una carta P con n variable son `p̄ ± 2·√(p̄(1−p̄)/nᵢ)` punto a punto; con `k=3` iguales a los actuales.
- **Referencia independiente:** fórmula de Montgomery (cap. 7).

### S014-RF-06 — `k` en Z-MR e I-MR-R/S

`zmr_chart` e `imr_r_chart`/`imr_s_chart` ganan `k` y `alpha` (valor o par) con la misma regla en sus paneles I y MR (y R/S). El resto de cartas de `advanced.py` no cambia.

**Aceptación:** igual que RF-01 sobre los paneles de cada carta.

### S014-RF-07 — La prueba 1 sigue a los límites

La prueba 1 marca los puntos por encima de `centro + k_sup·σ` o por debajo de `centro − k_inf·σ`: su umbral es `test_params[1]` si se da (el mismo en los dos lados, como hoy) y, si no, `k_sup`/`k_inf`. Así lo marcado coincide con lo dibujado. Por defecto
las pruebas 2 a 8 conservan sus umbrales y sus zonas de 1σ y 2σ (en unidades de σ, no de `k`); la persona usuaria puede reescalarlas (S014-RF-12). Con `k` (o `alpha`) y `test_params[1]` distintos gana `test_params[1]` y se avisa con `UserWarning`.

**Aceptación:**
- **Dado** `k=2` sin `test_params` **entonces** la prueba 1 marca exactamente los puntos fuera de `[lcl, ucl]`.
- **Dado** `k=2` y `test_params={1: 3}` **entonces** marca los de 3σ y avisa.
- **Dado** `k=2` **entonces** las violaciones de las pruebas 2 a 8 son las mismas que con `k=3`.

### S014-RF-08 — Validación de `k` y `alpha`

`k` es un número finito mayor que 0 (`bool` no vale) o una pareja de ellos (lista, tupla o arreglo de longitud 2). Si no, `ValueError` con texto traducible.

`alpha` (o cada valor de la pareja) cumple `0 < alpha < 1`. Pasar `k` y `alpha` a la vez es un `ValueError`.

**Aceptación:** `k=0`, `k=-1`, `k=nan`, `k=inf`, `k="3"`, `k=True`, `alpha=0`, `alpha=1`, `alpha=nan`, `k=(3, 3, 3)`, `k=(3,)` y `k` junto con `alpha` lanzan `ValueError` en español e inglés.

### S014-RF-09 — `k` con `transform`, `stages`, `mu` y `sigma`

`k` se aplica en la escala en que se calculan los límites: con `transform=` los límites son `centro ± k·σ` en la escala transformada y, con `scale="original"`, se
devuelven a la escala original (asimétricos, como hoy). Con `stages` el mismo `k` en todas las etapas; con `mu`/`sigma` históricos, igual.

**Aceptación:** `k=2` con `transform="boxcox"` da límites que son la inversa de la transformación aplicada a `centro ± 2σ`.

### S014-RF-10 — Resultado y coherencia con `probability()` y `arl_*`

`chart.params[i]` guarda `k_upper` y `k_lower` (claves en inglés, spec 012; `summary()` los muestra traducidos), iguales cuando el usuario dio un solo valor. `chart.probability()` sin argumentos refleja los límites con `k`.

**Aceptación:**
- **Dado** un I con `k=2` **cuando** `probability()` sin argumentos **entonces** es `2·Φ(−2) = 0,0455` y su inversa coincide con `arl_shewhart(k=2)`; con `k=(3, 2)` es `Φ(−3) + Φ(−2)` (cálculo con `scipy.stats.norm`).
- **Referencia independiente:** `scipy.stats.norm` y simulación con ≥ 20 semillas para R, S y P (tolerancia 5 % relativo).

### S014-RF-11 — `alpha`: un valor es bilateral, un par es unilateral por lado

- **Un valor** `alpha`: probabilidad **bilateral** de falsa alarma de un punto en un panel normal, `k = Φ⁻¹(1 − alpha/2)` en los dos lados (`alpha=0.0027` ↔ `k≈3`).
- **Un par** `(alpha_sup, alpha_inf)`: cada valor es la probabilidad **unilateral** de su lado, `k_sup = Φ⁻¹(1 − alpha_sup)` y `k_inf = Φ⁻¹(1 − alpha_inf)` (`alpha_sup` para el límite superior,
  `alpha_inf` para el inferior). Es la misma convención unilateral que el `alpha` de `t2_chart`.
- En paneles no normales (R, S, MR, atributos) es una **aproximación**: se usa el mismo `k` y la probabilidad real la da `chart.probability()`.
- `pp.k_from_confidence(confidence)` devuelve `Φ⁻¹(1 − (1 − confidence)/2)` (`0.99` ↔ `2.576`; bilateral).

**Aceptación:**
- `alpha=0.0027` da `k≈3`; `alpha=(0.00135, 0.00135)` da también `k=(3, 3)` (la misma probabilidad total, 0,0027).
- `k_from_confidence(0.9973) ≈ 3`, `0.95 ≈ 1.960`, `0.99 ≈ 2.576`; valores fuera de `(0, 1)` lanzan `ValueError`.
- **Referencia independiente:** `scipy.stats.norm.ppf` y la tabla normal estándar.

### S014-RF-12 — Zonas reescalables

Las cartas con zonas ganan `rescale_zones: bool = False`. Por defecto las zonas A/B/C y las pruebas 2 a 8 quedan en 1σ y 2σ aunque cambie `k` (igual que con `k=3`). Con `rescale_zones=True`
las fronteras de las zonas pasan a `k/3` y `2k/3` sigmas de cada lado (con `k=(k_sup, k_inf)`, `k_sup/3` y `2·k_sup/3` arriba, `k_inf/3` y `2·k_inf/3` abajo; las pruebas 5 y 6 miden desde ahí) y se dibujan así; la prueba 1 no cambia.

**Aceptación:**
- **Dado** `k=2` y `rescale_zones=True` **entonces** las líneas de zona están a `2/3` y `4/3` σ del centro y la prueba 5 marca según esas fronteras.
- **Dado** `k=2` por defecto **entonces** las zonas siguen a 1σ y 2σ.
- **Dado** `k=3` **entonces** `rescale_zones` no cambia nada.

### S014-RF-13 — Documentación

README (es/en), `docs/source`, docstrings y una advertencia: `k` no es un nivel de confianza fijo fuera de los paneles normales; tabla de equivalencias para I/Xbar
(`k = 2` ↔ 95,45 %; `2,576` ↔ 99 %; `3` ↔ 99,73 %), el uso de `alpha`, `k_from_confidence` y `rescale_zones`, sin afirmar cómo lo hace Minitab.

**Aceptación:** `sphinx-build -W` sin avisos y un test que ejecuta el fragmento del README.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Sin tendencia | `trend_direction == ''` y `has_trend == False`, como hoy |
| Datos con n mínimo | Igual que hoy (el umbral de tendencia no cambia) |
| `trend_direction` impreso con `PCCPY_LANG=en` | El valor guardado es `'increasing'`; el texto mostrado también |
| `k` muy grande (p. ej. 10) | Límites muy anchos; LCL de dispersión y atributos recortado a 0 |
| `k` pequeño (p. ej. 0,5) | Acepta; muchas violaciones de la prueba 1 |
| σ = 0 | Igual que hoy: aviso y límites iguales al centro |
| Etapa con una observación | Igual que hoy |
| `tests=None` con `k=2` | Los límites cambian; no hay pruebas |
| `k` con la carta de zona | No existe el parámetro (sin cambio) |
| `k=(3, 3)` | Igual que `k=3` |
| Límites asimétricos y escala transformada | Los límites se calculan con `k_sup`/`k_inf` en la escala transformada y se devuelven a la original |

## Resultados existentes que cambian

- **A:** `DiagnoseResult.trend_direction`: de `'creciente'`/`'decreciente'` a `'increasing'`/`'decreasing'`. Incompatible para quien compare con el literal español; no cambia ningún cálculo.
- **B:** ninguno con `k=3`. `test_params={1: x}` conserva su significado (gana sobre `k`); solo se añade el aviso si `k` o `alpha` se dan y difieren.

## No verificable sin la fuente

- Si Minitab permite un ancho distinto de 3σ en cada carta, límites distintos arriba y abajo, y cómo trata las zonas: no se pudo consultar; no se afirma equivalencia.
- La regla de la tendencia (`pct_inc > 0.80` / `< 0.20`) no cambia.

## Preguntas abiertas

Ninguna.
