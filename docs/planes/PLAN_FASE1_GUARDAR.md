# Plan — guardar y reutilizar los resultados de una Fase I

> **Estado:** propuesto el 2026-10-08, pendiente de aprobación. Una rama y un PR por fase; la versión va en un PR de versión aparte.
> **Objetivo:** que quien ya tiene una Fase I (de otra sesión, otro script o calculada por otra vía) pueda pasar a la Fase II sin repetir `phase_one`, y que ese camino esté documentado y probado.
> **Fuera de alcance:** guardar los datos de la Fase I (solo lo que `phase2()` necesita); formatos distintos de un diccionario serializable en JSON.

## Situación actual

- En la misma sesión: `fase1.phase2(datos_nuevos)`.
- Con parámetros históricos: `imr_chart(datos, mu=…, sigma=…)` (y Xbar-R/S); `p_chart(p=…)`, `c_chart(c=…)`, `u_chart(u=…)`; con transformación, además `transform=Transformation.from_info(…)`.
- No hay forma de guardar un `PhaseOneResult` completo: hay que conservar a mano `limits` y `transformation.info()` y recordar con qué carta y argumentos se calcularon. Nada de esto está en una sola página de la documentación.

## Decisiones propuestas

| Pregunta | Propuesta |
|---|---|
| Qué se guarda | Lo que `phase2()` necesita: función de la carta (por nombre), argumentos (`tests`, `sigma_method`, …), `limits`, `transformation.info()`, y como información: pasadas, puntos excluidos, `converged`, `reason`, `n_original`, versión de `pccpy` |
| Formato | `to_dict()` con tipos de Python y NumPy convertidos a tipos nativos, y `to_json(path=None)`; no se usa pickle (inseguro y frágil entre versiones) |
| Carga | `PhaseOneResult.from_dict()` / `from_json()` devuelve un objeto con `phase2()` operativo; `chart` (la carta final) no se guarda: sin los datos no se puede reconstruir, y queda `None` |
| Alternativa sin `phase_one` | Función `frozen_limits(chart, **límites)` o constructor `PhaseOneResult.from_limits(chart, mu=…, sigma=…, transform=…)` para quien ya tiene los números de otra fuente |
| Validación al cargar | Versión del esquema, carta soportada, claves de `limits` coherentes con la carta (`mu`/`sigma`, `p`, `c`, `u`), `Transformation` válida; error claro si no |
| Argumentos no serializables | Los que no sean JSON (callables, arreglos grandes) se rechazan al guardar con un mensaje que dice cuál es, en vez de guardarlos mal |

## Fases

| Fase | Contenido | Rama |
|---|---|---|
| G1 | `to_dict()` / `from_dict()` con esquema versionado y validación; `phase2()` funciona tras cargar | `feat/fase1-guardar` |
| G2 | `to_json()` / `from_json()` y `PhaseOneResult.from_limits(...)` para parámetros que vienen de fuera | `feat/fase1-guardar-json` |
| G3 | Documentación (sección «De la Fase I a la Fase II» en la guía y en el inicio rápido), traducciones, CHANGELOG y una comprobación en `run_validation()` | `feat/fase1-guardar-docs` |

## Puntos a comprobar

- Que `phase2()` tras `from_dict(to_dict(r))` dé exactamente la misma carta que antes de guardar, en las siete cartas soportadas, con y sin `transform`.
- Que los límites se guarden sin pérdida de precisión (repr completo de `float`; JSON no admite `NaN` ni `inf`: decidir cómo representarlos o rechazarlos).
- Las etiquetas (`labels`) de los datos de la Fase I no se guardan: `phase2()` toma las de los datos nuevos.
- Compatibilidad hacia atrás: un diccionario con una versión de esquema más nueva debe fallar con un mensaje que lo diga.
- Atributos con tamaños de muestra variables (`n=` como arreglo en `p_chart`/`u_chart`): se descartan en `phase2()` (describen los datos de la Fase I); comprobar que no se guardan.

## Validación

- Ida y vuelta: para cada carta, `from_json(to_json(r)).phase2(nuevos)` coincide con `r.phase2(nuevos)` (puntos, límites y señales).
- Un caso con transformación Johnson para comprobar que `from_info` reconstruye la familia y los parámetros.
- Una comprobación en `run_validation()` con la ida y vuelta de I-MR con Box-Cox.

## Riesgos

- Cambios futuros en los argumentos de las cartas pueden dejar JSON antiguos incompatibles: el esquema versionado y el error claro lo cubren.
- Un `from_limits` mal usado (límites de una carta aplicados a otra) da resultados sin sentido: la validación de claves lo evita en parte; el resto se documenta.
