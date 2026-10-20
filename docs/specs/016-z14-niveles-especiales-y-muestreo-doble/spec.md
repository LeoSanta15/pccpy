# 016 — Z1.4: niveles especiales S-1 a S-4, muestreo doble y plan que no cabe en el lote

- **Estado:** aprobada
- **Identificador:** S016
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** por decidir (añade opciones y funciones; solo cambia resultados existentes el RF-04, que corrige un error)

## Problema

`acceptance_sampling_attributes` implementa ANSI/ASQ Z1.4 solo en parte: niveles generales de inspección I, II y III
(tabla I), muestreo **simple** e inspección **normal** (tabla II-A). Faltan los **niveles especiales S-1 a S-4**, el
**muestreo doble** (tabla III-A) y la inspección rigurosa y reducida. La persona responsable aportó capturas de las
tablas I, II-A y III-A de la norma (hasta ahora «no se pudieron obtener»), con lo que S-1 a S-4 y el muestreo doble
normal se pueden hacer; la inspección rigurosa y reducida necesita sus tablas (II-B, II-C, III-B, III-C) y la Z1.9
sigue sin las suyas (A-2 y B-1).

Además, al repasar el código para esta especificación se encontró un error hoy sin ficha: cuando el plan de la tabla
tiene un tamaño de muestra mayor o igual que el lote, la norma manda **inspeccionar el 100 %** («If sample size
equals, or exceeds, lot size, carry out 100 percent inspection»), pero `pccpy` devuelve la muestra de la tabla aunque
no quepa en el lote:

```python
pp.acceptance_sampling_attributes(10, 0.01)   # n = 1250 con N = 10 (AOQL = -0.0)
pp.acceptance_sampling_attributes(200, 0.01)  # n = 1250 con N = 200
```

## Fuera de alcance

- **Inspección rigurosa y reducida** y las reglas de cambio entre ellas (tablas II-B, II-C, III-B, III-C y la tabla de
  cambios): no se tienen. Se hará con otra especificación cuando haya capturas.
- **Muestreo múltiple** (tabla IV) y los planes de doble muestreo para inspección rigurosa o reducida.
- **Z1.9** (variables): sigue sin sus tablas A-2 y B-1; el aviso de `acceptance_sampling_variables` se mantiene.
- Afirmar equivalencia con Minitab o con software de la norma: no se midió.

## Requisitos

### S016-RF-01 — Niveles especiales de inspección S-1 a S-4

`inspection_level` acepta `"S-1"`, `"S-2"`, `"S-3"` y `"S-4"` además de 1, 2 y 3 (que no cambian). La letra de código sale
de la tabla I de la norma; el plan, de la tabla II-A (o III-A) con esa letra.

**Aceptación:**
- **Dado** un lote de 1 000 **cuando** se pide el nivel `"S-3"` **entonces** la letra es `E` (con `"S-4"`, `F`; con `"S-1"` y
  `"S-2"`, `C`).
- **Dado** cualquier tamaño de lote y nivel **entonces** la letra coincide con las 60 celdas de la tabla I (15 tramos de
  lote × S-1 a S-4) y las 45 de los niveles I a III no cambian respecto de 0.15.8.
- **Dado** un valor de `inspection_level` que no existe (`"S-5"`, `4`) **entonces** `ValueError` en español.
- **Referencia independiente:** la tabla I de la captura aportada, transcrita en el test aparte del código (la persona
  responsable la revisa celda a celda); los niveles I a III ya se contrastaron con esa captura al redactar esta
  especificación y coinciden con la tabla incluida.

### S016-RF-02 — La tabla II-A incluida coincide con la norma

Hoy `_plan_z14` resuelve las flechas de la tabla II-A con una regla por diagonales. Debe coincidir con las 16 letras ×
16 AQL de la tabla maestra (tamaño de muestra, `Ac` y `Re`).

**Aceptación:**
- **Dado** cada par (letra A a R, AQL de 0,010 a 10 %) **entonces** `(n, Ac, Re)` coincide con la captura de la tabla II-A; si
  alguna celda difiere, se corrige y se documenta como error (ficha en `BUG_CATALOG.md`).
- **Referencia independiente:** la tabla II-A de la captura, transcrita en el test aparte del código. Alcance de los
  AQL: los que ya acepta la función (0,010 a 10 %); los AQL mayores (15 a 1000) de la tabla no se exponen hoy y quedan
  fuera salvo decisión contraria.

### S016-RF-03 — Muestreo doble para inspección normal (tabla III-A)

`acceptance_sampling_attributes(..., sampling="double")` devuelve un plan de doble muestreo de la tabla III-A: dos
tamaños de muestra (`n1`, `n2`; el acumulado es `2·n1`), números de aceptación y rechazo de la primera muestra
(`ac1`, `re1`) y de la acumulada (`ac2`, `re2`, con `re2 = ac2 + 1`). Se acepta si `d1 ≤ ac1`, se rechaza si `d1 ≥ re1` y,
entre ambos, se toma la segunda muestra y se acepta si `d1 + d2 ≤ ac2`.

**Aceptación:**
- **Dado** un lote y un AQL **entonces** el plan (`n1`, `n2`, `ac1`, `re1`, `ac2`, `re2`) coincide con la tabla III-A de la
  captura, resolviendo las flechas como en la norma (por ejemplo, la letra G lleva `n1 = n2 = 20`, con acumulada 40).
- **Dado** el plan **entonces** `pa(p)` es la probabilidad exacta `P(d1 ≤ ac1) + Σ_{d1=ac1+1}^{re1−1} P(d1)·P(d2 ≤ ac2 − d1)`
  con la binomial, y coincide con una simulación de 20 semillas × 20 000 lotes (tolerancia 0,005) y con la suma escrita aparte.
- **Referencia independiente:** la tabla III-A de la captura; la probabilidad de aceptación por convolución binomial
  escrita en el test (no la salida de `pccpy`) y simulación Monte Carlo.

### S016-RF-04 — Plan que no cabe en el lote: inspección al 100 %

Si la muestra de la tabla (o la acumulada, en el doble) es ≥ el tamaño del lote, la norma manda inspeccionar el 100 %.
El plan devuelto no puede tener `n > N`.

**Aceptación:**
- **Dado** `N = 10` y AQL 0,01 **entonces** el plan indica inspección al 100 % (`n = N`, con el `Ac` de la tabla), con un aviso
  (`UserWarning`) en español, sin AOQL negativo ni `nan`.
- **Dado** un lote donde la muestra sí cabe **entonces** no cambia nada.
- **Resultado que cambia:** los planes que hoy devuelven `n > N` (error: ver «Resultados existentes que cambian»).

### S016-RF-05 — Curva OC, ASN y AOQ del plan doble

El plan doble ofrece `oc_curve()`, `aoq_curve()` y la **curva ASN** (tamaño medio de muestra
`ASN(p) = n1 + n2·P(se toma la segunda muestra)`), con `to_frame(stable=True)`, `summary()`, `plot()` y las mismas claves
estables en inglés que el plan simple.

**Aceptación:**
- **Dado** un plan doble **entonces** `asn(p)` coincide con `n1 + n2·P(ac1 < d1 < re1)` calculado aparte y es ≤ `n1 + n2`;
  con `p → 0` tiende a `n1`.
- **Dado** `to_frame(stable=True)` **entonces** las claves están en inglés y no dependen del idioma (golden).
- **Referencia independiente:** convolución binomial aparte y simulación con 20 semillas.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Lote de 2 a 8 con muestreo doble (letra A) | La tabla no trae plan doble para A: se usa el de la letra B con `UserWarning` (decidido) |
| Lote ≤ muestra de la tabla | Inspección al 100 % con aviso (RF-04) |
| `inspection_level="s-3"` (minúsculas) | `ValueError` en español: solo `"S-1"` a `"S-4"` (decidido) |
| `n` y `c` dados por la persona usuaria | Igual que hoy (plan a medida; no usa las tablas) |
| AQL entre dos valores de la tabla | El más cercano, como hoy |

## Resultados existentes que cambian

- Los planes de `acceptance_sampling_attributes` cuya muestra de la tabla supera el tamaño del lote (por ejemplo `N = 10`,
  AQL 0,01 → `n = 1250`) pasan a inspección al 100 % (`n = N`) con aviso: eran un error.
- Si la comprobación del RF-02 encuentra celdas de la tabla II-A transcritas con error, esos planes cambian y se listan en
  «Cambios que alteran resultados». Hasta ejecutarla no se sabe si hay alguna.

## No verificable sin la fuente

- Todo se contrasta con **capturas** de las tablas I, II-A y III-A, no con el texto de la norma: una lectura errónea de
  una celda (sobre todo de las flechas de la tabla III-A, que son pequeñas) pasaría desapercibida. Por eso las
  transcripciones de los tests las revisa la persona responsable celda a celda antes de aprobar la fase de código.
- No se midió si Minitab o el software de la norma devuelven los mismos planes.
- La inspección rigurosa, la reducida, las reglas de cambio, el muestreo múltiple y la Z1.9 siguen sin tablas.

## Preguntas abiertas

Ninguna. Decididas por la persona responsable (con las recomendaciones de la propuesta):

1. **Alcance:** esta especificación cubre S-1 a S-4, el muestreo doble normal, la tabla II-A comprobada y la guarda del 100 %.
   La inspección rigurosa y reducida esperan sus tablas (otra especificación). Alternativa descartada: hacerlo todo junto.
2. **API:** parámetro `sampling="single"|"double"` (por defecto `"single"`) en `acceptance_sampling_attributes`, que devuelve
   una clase nueva `DoublePlanAttributes` con `sampling="double"`. Alternativa descartada: función nueva.
3. **Letra A en doble:** se usa el plan doble de la letra B con un `UserWarning` en español (la tabla manda usar el simple
   correspondiente o el doble de la letra B). Alternativa descartada: `ValueError`.
4. **100 % de inspección:** el plan devuelto lleva `n = N` y el `Ac` de la tabla, con un `UserWarning` en español.
   Alternativa descartada: `c = 0`.
5. **Nombre del nivel:** solo `"S-1"` a `"S-4"` (guion y mayúscula, como en la norma); otras grafías (`"s-3"`, `"S3"`)
   lanzan `ValueError` en español. Alternativa descartada: normalizar las grafías.
