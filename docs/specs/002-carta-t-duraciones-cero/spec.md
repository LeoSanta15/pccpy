# 002 — Carta T: duraciones iguales a 0

- **Estado:** borrador
- **Identificador:** S002
- **Responsable de aprobarla:** LeoSanta15
- **Versión objetivo:** 0.15.1 (no cambia resultados numéricos existentes; solo los mensajes de error y la opción nueva `zeros`)

## Problema

`t_chart` modela el tiempo entre eventos raros con una Weibull o una exponencial, distribuciones definidas para
`t > 0`. Hoy rechaza cualquier duración `≤ 0` con un `ValueError`, pero:

1. El mensaje dice «no se admiten duraciones iguales a 0» también cuando el dato es **negativo**, que es otro error
   (probablemente fechas desordenadas).
2. En la práctica aparecen ceros legítimos: dos eventos registrados en la misma unidad de tiempo (la resolución del
   registro es de un día y ocurren dos el mismo día). Quien usa la carta se queda sin salida: o borra datos o inventa un
   valor, sin que la biblioteca le diga cuál es lo razonable.
3. Qué hace Minitab con ceros en la carta T **no está verificado** (pendiente declarado en `CLAUDE.md`), de modo que
   no hay una referencia a la que ajustarse.

Medido hoy (0.15.0): `t_chart([0, 1.2, 3.4, 2.2, 5.1, 0.8, 2.9, 1.7])` y la misma serie con `-1` en lugar de `0` lanzan
el mismo `ValueError`.

## Fuera de alcance

- Otras distribuciones para la carta T (lognormal, gamma…).
- La carta G (eventos raros discretos) y su prueba de Benneyan.
- Rellenar o imputar ceros sin que la persona usuaria lo pida.

## Requisitos

### S002-RF-01 — Mensajes distintos para cero y para negativos

`t_chart` debe distinguir en el mensaje de error entre duraciones iguales a 0 y duraciones negativas, indicando cuántas
son y en qué posiciones (como hace el aviso de valores no finitos).

**Aceptación:**
- **Dado** una serie con un 0 en la posición 0, **cuando** se llama a `t_chart`, **entonces** `ValueError` cuyo
  mensaje habla de ceros y cita la posición 0.
- **Dado** una serie con un `-1`, **entonces** `ValueError` cuyo mensaje habla de valores negativos, no de ceros.

### S002-RF-02 — Ceros: decisión explícita de la persona usuaria

`t_chart` debe aceptar un parámetro `zeros` con dos valores: `"error"` (por defecto, el comportamiento actual) y `"drop"`, que
excluye las duraciones iguales a 0 y avisa de cuántas. No se sustituyen ceros por valores inventados (decisión de
LeoSanta15: opción B; descartadas A, solo mensaje, y C, sustituir por la mitad de la resolución).

**Aceptación:**
- **Dado** `zeros="error"` (o sin indicarlo), **entonces** el comportamiento es el de RF-01.
- **Dado** `zeros="drop"`, **cuando** hay ceros, **entonces** el resultado es idéntico al de la serie sin ellos y se
  emite un `UserWarning` que dice cuántos se excluyeron.
- **Referencia independiente:** el ajuste Weibull de la serie sin ceros calculado aparte con `scipy.stats.weibull_min`
  (`floc=0`), tolerancia 1e-6 en forma y escala.

### S002-RF-03 — La opción por defecto no cambia resultados

Con datos positivos el resultado de `t_chart` es idéntico al de 0.15.0 (límites, línea central, violaciones).

**Aceptación:**
- **Dado** una serie positiva fija y los valores de `tests/golden/`, **entonces** no hay diferencias.

## Casos borde

| Caso | Comportamiento esperado |
|---|---|
| Todas las duraciones son 0 | `ValueError` (RF-01); con `zeros="drop"`, `ValueError` porque no quedan datos |
| Un solo valor positivo tras excluir ceros | `ValueError` de datos insuficientes, como hoy |
| Cero y negativo en la misma serie | El mensaje menciona ambos |
| Valores no finitos | Sin cambios: se excluyen con aviso |
| `shape` y `scale` dados (parámetros históricos) y ceros | Los ceros se rechazan igual: la carta se dibuja sobre `x` |

## Resultados existentes que cambian

Ninguno. Solo cambian los mensajes de error y se añade `zeros` con un valor por defecto igual al comportamiento actual.

## No verificable sin la fuente

El tratamiento de ceros por Minitab en la carta T no se pudo consultar. Esta especificación **no** afirma equivalencia
con Minitab: documenta el comportamiento de `pccpy` y lo marca como diferencia posible.

## Preguntas abiertas

Ninguna. (La opción B para S002-RF-02 se decidió el 2026-10-16.)
