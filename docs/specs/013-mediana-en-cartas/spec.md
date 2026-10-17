# 013 — Mediana en las cartas de variables

- **Estado:** aprobada
- **Identificador:** S013
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.6 (no cambia ningún resultado existente: opción nueva y función nueva)

## Problema

Las cartas I-MR, Xbar-R y Xbar-S solo usan la media como línea central. Con datos asimétricos o con atípicos la media se
desplaza y la línea central deja de representar el valor típico del proceso. La persona responsable pide dos cosas (opción C):

- **A.** Poder cambiar la media por la mediana como línea central de I-MR, Xbar-R y Xbar-S.
- **B.** Una carta de **medianas de subgrupo** (X̃-R), que grafica la mediana de cada subgrupo en lugar de su media.

Qué se sabe (simulación informal, **no** incluida en `run_validation()`; hay que repetirla con ≥ 20 semillas antes de afirmarlo en la
documentación): con datos asimétricos la línea central en la mediana **no** elimina las falsas alarmas de la prueba 1, porque los
límites ±3σ siguen siendo simétricos; sí hace que la prueba 2 (9 puntos seguidos del mismo lado) sea libre de distribución, porque
la mediana deja la mitad de los puntos a cada lado. Para datos asimétricos la herramienta correcta sigue siendo `transform=`.
La varianza de la mediana de un subgrupo normal es 1,34 a 1,49 veces la de la media (n = 3 a 9): la carta X̃ es menos sensible que Xbar
con datos normales.

## Fuera de alcance

- Límites asimétricos o por percentiles (eso lo cubre `transform=`).
- Cartas de mediana con otras cartas de dispersión (X̃-S) y con tamaños de subgrupo desiguales.
- EWMA, CUSUM, cartas de atributos y multivariadas.
- Que `phase_one()` acepte `center=` (se estudia aparte si se pide).
- Afirmar equivalencia con Minitab: no se pudo comprobar si Minitab ofrece estas opciones ni su fórmula.

## Requisitos

### S013-RF-01 — `center="median"` en I-MR

`imr_chart(x, center="mean"|"median")`, por defecto `"mean"` (resultado idéntico al actual). Con `"median"` la línea central del panel I es la
mediana de las observaciones de la etapa (sin huecos); σ y los límites se calculan como hoy: `centro ± 3σ`.

**Aceptación:**
- **Dado** datos asimétricos **cuando** `center="median"` **entonces** `params[0]["center"] == "median"`, `params[0]["mean"]` es la mediana
  y los límites son `mediana ± 3σ` con la misma σ que con `center="mean"`.
- **Referencia independiente:** `numpy.median` y el cálculo manual de σ (`MR̄/d2`).

### S013-RF-02 — `center="median"` en Xbar-R y Xbar-S

Igual que RF-01: la línea central del panel X̄ es la mediana de las **medias de subgrupo** de los subgrupos completos de la etapa; σ y los
límites no cambian (`centro ± 3σ/√nᵢ`).

**Aceptación:**
- **Dado** subgrupos **cuando** `center="median"` **entonces** el centro es `numpy.median(medias de subgrupo)`.
- Decidido por la persona responsable: el centro es la mediana de las medias de subgrupo (el estimador del centro de lo que se grafica).

### S013-RF-03 — Combinación con `mu`

`mu` fija la línea central, así que `center="median"` junto con `mu` es un error (`ValueError`, texto traducible). `center` distinto de
`"mean"`/`"median"` también.

**Aceptación:** ambos casos lanzan `ValueError` en español e inglés.

### S013-RF-04 — Carta de medianas de subgrupo `median_r_chart`

`median_r_chart(data, subgroup_size=…, subgroup=…, value=…, mu=…, sigma=…, stages=…, tests=…, test_params=…)`: dos paneles, **Mediana** (X̃) y
**R**. Entrada y etapas como `xbar_r_chart`. Con `n` el tamaño del subgrupo y `σ̂ = R̄/d2(n)`:

- línea central = promedio de las medianas de subgrupo (o `mu`);
- límites = `centro ± 3·cmed(n)·σ̂` con `cmed(n)` = desviación estándar de la mediana de `n` normales estándar (el coeficiente `Ã2 = 3·cmed(n)/d2(n)`
  de Montgomery: `centro ± Ã2·R̄`);
- el panel R es el de Xbar-R.

**Aceptación:**
- **Dado** `n` = 3, 5, 7 y 9 **cuando** se construye la carta **entonces** `Ã2` coincide con la integración numérica de la densidad de la
  mediana (estadístico de orden) y con una simulación Monte Carlo de ≥ 20 semillas (tolerancia 1 %).
- **Referencia independiente:** integración numérica de la densidad del estadístico de orden con `scipy.integrate`, y la tabla de Ã2 de
  Montgomery (valores recordados de memoria: 1,187 / 0,691 / 0,509 / 0,412; **no verificados contra el libro**).

### S013-RF-05 — Tamaños de subgrupo de la carta X̃

**Aceptación:** con `n = 1` o con tamaños de subgrupo desiguales lanza `ValueError`; con cualquier `n ≥ 2` constante construye la carta.

Decidido por la persona responsable: se acepta cualquier `n ≥ 2` constante y `cmed(n)` se calcula por integración; solo los tamaños impares se contrastan con la tabla de Montgomery, y la documentación lo dice.

### S013-RF-06 — `ControlChart.probability()` en la carta X̃

La mediana de `n` normales (con `n` impar) tiene distribución exacta `F⁻¹(Beta(k, k))` con `k = (n+1)/2`, así que `P(X̃ ≤ x) = I_{Φ(z)}(k, k)`.
`Panel.dist` de la carta X̃ usa la familia `"median"`; con `n` par se usa la integración numérica.

**Aceptación:** `probability()` sin argumentos coincide con la probabilidad de caer fuera de los límites calculada por simulación
(≥ 20 semillas) y, para `n` = 1, con la de I.

### S013-RF-07 — Claves y textos

`chart.params` gana la clave `center` (`"mean"` o `"median"`); en la carta X̃ `center` es `"mean_of_medians"`. Claves y valores en inglés (spec 012);
`summary()` los traduce (`results._PARAMETROS`, `_VALORES_PARAMETRO`). Nombre del panel: `"Median"`. Todo texto nuevo con `tr()`.

**Aceptación:** `tests/test_claves_ingles.py` y `tests/test_i18n_nombres_y_parametros.py` cubren las claves nuevas.

### S013-RF-08 — Documentación

README (es/en), `docs/source`, docstrings y una advertencia: la mediana como centro no corrige las falsas alarmas de la prueba 1 con datos
asimétricos (usar `transform=`); la carta X̃ es menos sensible que Xbar con datos normales.

**Aceptación:** `sphinx-build -W` sin avisos y un test que ejecuta el fragmento del README.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Etapa con una sola observación | Igual que la media: mediana = el valor |
| Huecos (NaN) en I-MR | La mediana ignora los huecos |
| Subgrupos incompletos | El último subgrupo incompleto no entra en el centro ni en σ (como en Xbar) |
| Datos constantes | σ = 0 con el aviso actual; centro = valor |
| `center="median"` con `transform=` | Funciona: la mediana de los datos transformados |
| `median_r_chart` con `n = 1` | `ValueError` |
| `median_r_chart` con `mu` histórica | Centro = `mu`, igual que Xbar-R |

## Resultados existentes que cambian

Ninguno: `center` por defecto es `"mean"` y `chart.params` solo gana la clave `center`.

## No verificable sin la fuente

- Si Minitab ofrece mediana como línea central o una carta X̃, y su fórmula: no se pudo consultar; no se afirma equivalencia.
- La tabla de Ã2 de Montgomery está recordada de memoria; la verificación es la integración numérica y la simulación.
- Qué dice la literatura sobre el centro de la carta (búsqueda web del 2026-10-17, **no se pudo abrir ni verificar ningún texto**): para la carta de medianas (X̃) el centro habitual es el promedio de las medianas
  de subgrupo; no hallé una fuente que fije el centro de una carta Xbar con mediana. Rocke (1989) encontró que las cartas cuyo estadístico de subgrupo ya es resistente (las de medianas) tienen el peor
  desempeño y recomienda estadísticos como la media recortada; Schoonhoven et al. (2011) comparan estimadores robustos de localización para la carta Xbar. Hay que leer esos artículos antes de afirmar nada en la documentación.

## Preguntas abiertas

Cerradas por la persona responsable: RF-02 (por defecto, la mediana de las medias de subgrupo), RF-05 (cualquier `n ≥ 2` constante, con `cmed(n)` por integración; solo los impares se contrastan con la tabla) y el nombre `median_r_chart`.
