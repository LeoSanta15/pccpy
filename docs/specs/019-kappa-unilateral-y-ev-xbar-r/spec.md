# 019 — Kappa: p-valor unilateral y caso degenerado; EV del Gage R&R Xbar-R con `d2`

- **Estado:** borrador
- **Identificador:** S019
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** por decidir (cambia resultados existentes: p-valores de kappa y EV del Xbar-R; la regla de `CLAUDE.md` dice versión menor; ver pregunta 4)

## Problema

Una segunda auditoría (sobre la 0.16.1) dejó dos hallazgos que cambian resultados. Se verificaron en el código; lo que no se pudo verificar se dice más abajo.

**1. Kappa de Cohen y Fleiss con acuerdo degenerado.** `_cohen_kappa` (`msa.py`) devuelve `κ = 1.0` y `p = 0.0` cuando `pₑ = 1` (los dos evaluadores usan una única categoría).
En ese caso `κ = (pₒ − pₑ)/(1 − pₑ)` es `0/0`: no está definido. Medido:
`_cohen_kappa(np.zeros(10), np.zeros(10), [0, 1])` → `(1.0, 0.0, 100.0)`. `_fleiss_kappa` hace lo mismo (`return … if Pe < 1 else 1.0`).
Un operador que da siempre «bueno» frente a una referencia siempre «bueno» sale con acuerdo perfecto y significación máxima, cuando no hay información para estimar nada.

**2. El p-valor del kappa es bilateral.** `p = 2·sf(|z|)` con `z = κ/SE₀`. Minitab, en su análisis de concordancia por atributos, informa `P(vs > 0)` (hipótesis alternativa `κ > 0`), unilateral; esto se recuerda de memoria y no se pudo verificar. De ser así, los p-valores de `pccpy` salen el doble que los de Minitab
cuando `κ > 0`. Medido: 3 operadores con 60 piezas: `κ = 0,700`, `p = 5,05·10⁻⁸` hoy (unilateral: `2,53·10⁻⁸`).

**3. EV del Xbar-R con `d2*` en vez de `d2`.** `_gage_rr_xbar_r` usa `EV = R̄/d2*(r, p·o)` (spec 006). Con `p·o = 30` combinaciones (10 partes × 3 operadores), `K1 = 1/d2*` es 0,8779 (2 ensayos) y 0,5881 (3 ensayos), mientras que el manual MSA de AIAG
tabula `K1 = 0,8862` y `0,5908`, es decir `1/d2(r)`, al suponer más de 15 combinaciones parte×operador (también de memoria, no verificado).
La diferencia es del **−0,9 %** (2 ensayos) y **−0,5 %** (3 ensayos) en la EV: hoy la EV sale **menor** que con `d2` (con pocas combinaciones, p. ej. 6, la diferencia llega a −4,4 %).
El AV y el PV usan `d2*(o, 1)` y `d2*(p, 1)`, que reproducen los K2 y K3 del manual a ~1e-3 (spec 006) y no cambian.

La auditoría que originó la spec 006 había recomendado `d2*` para la EV; la nueva auditoría reconoce que esa recomendación era errónea para este caso (y que habla de «inflar» la EV, cuando el signo medido es el contrario: la EV sale menor).

## Fuera de alcance

- **Documentar que la OC por atributos usa la binomial** (y no la hipergeométrica, que sería la exacta para un lote finito aislado): cambio de docstring, sin especificación (PR aparte).
- **Kappa de Fleiss entre evaluadores**: solo se arregla el caso degenerado; no se le añade p-valor.
- **Cambiar K2 y K3** del Xbar-R, el método ANOVA o `d2_star` (se mantiene).
- Afirmar equivalencia con Minitab: no se midió (ver «No verificable»).

## Requisitos

### S019-RF-01 — Kappa indefinido si `pₑ = 1`

`_cohen_kappa` y `_fleiss_kappa` devuelven `κ = nan` (y p-valor `nan`) cuando `pₑ = 1`; el porcentaje de acuerdo se conserva.

**Aceptación:**
- **Dado** dos evaluadores que usan una sola categoría (todos «bueno») **entonces** `κ` y `p` son `nan` y `% acuerdo = 100`.
- **Dado** el mismo caso en `attribute_agreement` **entonces** `summary()`, `to_frame()` y `to_excel()` no lanzan y muestran `nan` en esa fila; las demás filas no cambian.
- **Dado** `pₑ < 1` **entonces** el resultado es el de hoy (guarda: pasa antes del código).
- **Referencia independiente:** la definición `κ = (pₒ − pₑ)/(1 − pₑ)` (indefinida para `pₑ = 1`); para `pₑ < 1`, `sklearn`/`statsmodels` no son dependencias: se compara con el cálculo manual de la matriz de confusión.

### S019-RF-02 — p-valor del kappa de Cohen unilateral

`p = P(Z ≥ z) = sf(z)` con `z = κ/SE₀` (H₀: κ = 0; H₁: κ > 0), con el mismo `SE₀` de Fleiss, Cohen y Everitt (1969). El valor de `κ` no cambia.

**Aceptación:**
- **Dado** `κ > 0` **entonces** `p_unilateral = p_bilateral_anterior / 2` y coincide con `norm.sf(κ/SE₀)` con `SE₀` de `statsmodels.stats.inter_rater.cohens_kappa(...).std_kappa0`.
- **Dado** `κ < 0` **entonces** `p > 0,5` (un `κ` negativo nunca es significativo a favor de la concordancia).
- **Dado** marginales 85/15, `n = 100`, 20 semillas × 300 muestras bajo H₀ **entonces** la tasa de rechazo al 5 % unilateral es 0,05 ± 0,01.
- **Referencia independiente:** `statsmodels` (`std_kappa0`) y la simulación bajo H₀.

### S019-RF-03 — EV del Xbar-R con `d2`

`EV = R̄/d2(r)` (la `K1` tabulada de AIAG) cuando `p·o > 15`; con `p·o ≤ 15` se conserva `d2*(r, p·o)` (la corrección de muestra pequeña). `K2`, `K3`, el ANOVA y `d2_star` no cambian.

**Aceptación:**
- **Dado** 10 partes × 3 operadores × 2 ensayos **entonces** `K1 = 0,8862` (`= 1/d2(2)`, con `d2(2) = 2/√π`) y con 3 ensayos `K1 = 0,5908` (`d2(3) = 1,6926`), contra los valores tabulados (cálculo aparte con la fórmula cerrada de `d2(2)` y la integración numérica de `d2(3)`).
- **Dado** 3 partes × 2 operadores (6 combinaciones) **entonces** la EV es la de hoy (`d2*`).
- **Dado** el mismo estudio **entonces** `K2`, `K3`, `PV` y las columnas del resultado conservan su forma; cambian solo EV, AV (que resta EV²/(p·r)), %R&R y `ndc`, en la fracción medida (≈ +0,5 % a +1 % en EV).
- **Referencia independiente:** `d2(2) = 2/√π` y `d2(3)` por integración numérica escrita aparte; el valor del manual de AIAG no se pudo consultar (ver «No verificable»).

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| `pₑ = 1` en Cohen o en Fleiss | `κ = nan`, `p = nan`, acuerdo 100 % |
| `κ = 0` | `p = 0,5` (unilateral) |
| `κ < 0` | `p > 0,5` |
| Una sola categoría en solo uno de los dos evaluadores | `pₑ < 1`: sin cambios |
| `p·o = 15` y `p·o = 16` | 15 → `d2*`, 16 → `d2` (la regla del manual; hay un salto de ~0,9 % en la EV, documentado) |
| Gage R&R ANOVA | sin cambios |

## Resultados existentes que cambian

- **Kappa:** los p-valores de `kappa_within` y `kappa_vs_reference` se reducen a la mitad cuando `κ > 0` (y salen `> 0,5` con `κ < 0`); con `pₑ = 1`, `κ` y `p` pasan de `1,0` y `0,0` a `nan`. Cambian los goldens `kappa_*` y la comprobación de validación.
- **Xbar-R:** con más de 15 combinaciones parte×operador, la EV sube ≈ 0,5–1 % (y con ella %Repetibilidad; el AV baja algo); con 15 o menos no cambia.

Se listan en «Cambios que alteran resultados» del CHANGELOG con el valor anterior y el nuevo.

## No verificable sin la fuente

- Que Minitab informe `P(vs > 0)` y que lo calcule con el `SE₀` de Fleiss, Cohen y Everitt: no se pudo consultar (ya constaba en la spec 015).
- Los valores `K1` y la nota de `g > 15` del manual MSA de AIAG (4.ª ed.): se recuerdan y no se pudieron consultar; la referencia numérica es `1/d2(r)` calculada aparte.
- No se midió si Minitab calcula la EV del Xbar-R con `d2` o con `d2*`.

## Preguntas abiertas

1. [NECESITA ACLARACIÓN: ¿El p-valor del kappa pasa a unilateral (`P(Z ≥ z)`, como recuerda la auditoría que hace Minitab) o se deja bilateral? **Recomendación:** unilateral, porque la hipótesis de interés es «el acuerdo es mejor que el azar» y alinea con lo que recuerdo de Minitab; se anota en «Notas sobre diferencias posibles con Minitab» que no se pudo verificar. Alternativa descartada: añadir `alternative="greater"|"two-sided"` (más superficie; si prefieres elegir, se hace en otra spec).]
2. [NECESITA ACLARACIÓN: ¿La EV del Xbar-R usa siempre `d2(r)` (A), siempre `d2*` como hoy (B) o `d2` con más de 15 combinaciones y `d2*` con 15 o menos (C, como la nota del manual, recordada)? **Recomendación:** C: reproduce `K1` del manual en los estudios normales (≥ 30 combinaciones) y conserva la corrección de muestra pequeña. Inconveniente: un salto de ~0,9 % entre 15 y 16 combinaciones. Alternativa A: sin salto, pero la EV sube hasta 4,6 % con 6 combinaciones.]
3. [NECESITA ACLARACIÓN: ¿También `κ = nan` en `_fleiss_kappa` con `Pe = 1`? **Recomendación:** sí, por la misma razón (0/0); hoy devuelve 1,0.]
4. [NECESITA ACLARACIÓN: ¿Versión menor (0.17.0) o parche (0.16.2)? **Recomendación:** 0.17.0: cambian p-valores y la EV sin corregir un error de tabla, y la regla de `CLAUDE.md` dice «cambia resultados → versión menor»; los parches 0.15.8, 0.15.9 y 0.16.1 fueron excepciones tuyas y la auditoría las señala como riesgosas para quien fija `~=0.16.0`.]
