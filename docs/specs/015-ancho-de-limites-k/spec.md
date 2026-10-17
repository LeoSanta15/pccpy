# 015 — Ancho de los límites de control (`k`) en las cartas de Shewhart

- **Estado:** borrador
- **Identificador:** S015
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** [NECESITA ACLARACIÓN: parche (sigue a las specs 013 y 014; no cambia ningún resultado existente) o la siguiente menor]

## Problema

Las cartas I-MR, Xbar-R, Xbar-S, P, NP, C, U, Laney P'/U', Z-MR e I-MR-R/S trazan siempre los límites a ±3σ. Otras cartas de la biblioteca
sí tienen el multiplicador: EWMA, MA, G, T y la varianza generalizada (`k`) y T² de Hotelling (`alpha`). Quien quiere límites más estrechos
(más sensibles, más falsas alarmas) o más anchos no puede pedirlo.

Hay además una incoherencia que existe hoy. `test_params={1: 2.0}` hace que la prueba 1 marque los puntos a más de 2σ, pero **los límites
dibujados siguen en 3σ**: con 200 datos normales, la UCL de `imr_chart` es 2,778 con o sin el parámetro y las violaciones pasan de 5 a 22. La
carta marca puntos que parecen estar dentro de los límites.

## Fuera de alcance

- **Límites asimétricos** (`k` distinto arriba y abajo) y límites por percentiles en las cartas de Shewhart.
- Convertir `k` en un «nivel de confianza» exacto: solo es exacto en los paneles normales (I, Xbar, Z); en R, S, MR y atributos la
  probabilidad depende de la distribución del estadístico y de `n`. `chart.probability()` da la probabilidad real.
- Zonas de 1σ y 2σ y pruebas 2 a 8: no cambian con `k`.
- La carta de zona (sus pesos están definidos sobre 3σ), EWMA, CUSUM, MA, G, T y multivariadas, que ya tienen su parámetro.
- `phase_one()` (se estudia aparte si se pide).
- Afirmar equivalencia con Minitab: no se pudo comprobar si ofrece un ancho distinto de 3σ en cada carta.

## Requisitos

### S015-RF-01 — `k` en I-MR, Xbar-R y Xbar-S

`imr_chart`, `xbar_r_chart` y `xbar_s_chart` ganan `k: float = 3.0`. Los límites del panel de medias (I o Xbar) son `centro ± k·σ` (`σ/√nᵢ` en Xbar).
En los paneles de dispersión (MR, R, S): `UCL = centro + k·sd` y `LCL = max(0, centro − k·sd)`, con `sd` la desviación del estadístico (`d3·σ` o `c5·σ`).

**Aceptación:**
- **Dado** `k=2` **cuando** se construye la carta **entonces** `ucl − center == 2·σ` en I y `UCL(R) − center == 2·d3·σ`.
- **Dado** `k=3` (o sin `k`) **entonces** todos los valores coinciden con los de hoy (golden y tests existentes sin cambios).
- **Referencia independiente:** cálculo manual con `d2`, `d3`, `c4`, `c5` de Montgomery.

### S015-RF-02 — `k` en las cartas de atributos

`p_chart`, `np_chart`, `c_chart`, `u_chart`, `laney_p_chart` y `laney_u_chart` ganan `k: float = 3.0`: `centro ± k·σᵢ`, con el LCL recortado a 0 y el
UCL de P y Laney P' recortado a 1 como hoy.

**Aceptación:** con `k=2` los límites de una carta P con n variable son `p̄ ± 2·√(p̄(1−p̄)/nᵢ)` punto a punto; con `k=3` iguales a los actuales.
- **Referencia independiente:** fórmula de Montgomery (cap. 7).

### S015-RF-03 — `k` en Z-MR e I-MR-R/S

`zmr_chart` e `imr_r_chart`/`imr_s_chart` ganan `k: float = 3.0` con la misma regla en sus paneles I y MR (y R/S). El resto de cartas de `advanced.py` no cambia.

**Aceptación:** igual que RF-01 sobre los paneles de cada carta.

### S015-RF-04 — La prueba 1 sigue a los límites

La prueba 1 marca los puntos a más de `k` sigmas del centro: su umbral es `test_params[1]` si se da y, si no, `k`. Así lo marcado coincide con lo dibujado. Las pruebas
2 a 8 conservan sus umbrales y sus zonas de 1σ y 2σ (en unidades de σ, no de `k`). Con `k` y `test_params[1]` distintos gana `test_params[1]` y se avisa con `UserWarning`.

**Aceptación:**
- **Dado** `k=2` sin `test_params` **entonces** la prueba 1 marca exactamente los puntos fuera de `[lcl, ucl]`.
- **Dado** `k=2` y `test_params={1: 3}` **entonces** marca los de 3σ y avisa.
- **Dado** `k=2` **entonces** las violaciones de las pruebas 2 a 8 son las mismas que con `k=3`.

### S015-RF-05 — Validación de `k`

`k` debe ser un número finito mayor que 0 (`bool` no vale). Si no, `ValueError` con texto traducible.

**Aceptación:** `k=0`, `k=-1`, `k=nan`, `k=inf`, `k="3"` y `k=True` lanzan `ValueError` en español e inglés.

### S015-RF-06 — `k` con `transform`, `stages`, `mu` y `sigma`

`k` se aplica en la escala en que se calculan los límites: con `transform=` los límites son `centro ± k·σ` en la escala transformada y, con `scale="original"`, se
devuelven a la escala original (asimétricos, como hoy). Con `stages` el mismo `k` en todas las etapas; con `mu`/`sigma` históricos, igual.

**Aceptación:** `k=2` con `transform="boxcox"` da límites que son la inversa de la transformación aplicada a `centro ± 2σ`.

### S015-RF-07 — Resultado y coherencia con `probability()` y `arl_*`

`chart.params[i]["k"]` guarda el valor usado (clave en inglés, spec 012; `summary()` lo muestra traducido). `chart.probability()` sin argumentos refleja los límites con `k`.

**Aceptación:**
- **Dado** un I con `k=2` **cuando** `probability()` sin argumentos **entonces** es `2·Φ(−2) = 0,0455` y su inversa coincide con `arl_shewhart(k=2)`.
- **Referencia independiente:** `scipy.stats.norm` y simulación con ≥ 20 semillas para R, S y P (tolerancia 5 % relativo).

### S015-RF-08 — Documentación

README (es/en), `docs/source`, docstrings y una advertencia: `k` no es un nivel de confianza fijo fuera de los paneles normales; tabla de equivalencias para I/Xbar
(`k = 2` ↔ 95,45 %; `2,576` ↔ 99 %; `3` ↔ 99,73 %), sin afirmar cómo lo hace Minitab.

**Aceptación:** `sphinx-build -W` sin avisos y un test que ejecuta el fragmento del README.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `k` muy grande (p. ej. 10) | Límites muy anchos; LCL de dispersión y atributos recortado a 0 |
| `k` pequeño (p. ej. 0,5) | Acepta; muchas violaciones de la prueba 1 |
| σ = 0 | Igual que hoy: aviso y límites iguales al centro |
| Etapa con una observación | Igual que hoy |
| `tests=None` con `k=2` | Los límites cambian; no hay pruebas |
| `k` con la carta de zona | No existe el parámetro (sin cambio) |

## Resultados existentes que cambian

Ninguno con `k=3`. El comportamiento de `test_params={1: x}` **sí cambia** cuando no se da `k`: hoy el umbral de la prueba 1 se mueve sin mover los límites; con la
spec se mantiene el umbral (sigue ganando `test_params[1]`) y solo se añade el aviso si `k` se da y es distinto. Sin `k` no hay aviso y todo queda igual.

## No verificable sin la fuente

- Si Minitab permite ancho distinto de 3σ en cada carta y cómo trata las zonas: no se pudo consultar; no se afirma equivalencia.

## Preguntas abiertas

- [NECESITA ACLARACIÓN: nombre y significado del parámetro. Se propone `k` (en sigmas), igual que EWMA, MA, G, T y varianza generalizada. Alternativas: `alpha`/`confidence`
  (como T²), que no tiene un significado único en R, S y atributos.]
- [NECESITA ACLARACIÓN: ¿añadir además un auxiliar `pp.k_from_confidence(0.99)` (= `norm.ppf(1 − (1−confianza)/2)`) para quien piense en confianza?]
- [NECESITA ACLARACIÓN: ¿las zonas de 1σ y 2σ y las pruebas 5 y 6 quedan en σ aunque `k` cambie (propuesto), o se reescalan con `k/3`?]
