# Plan — 009 ARL de las cartas Shewhart, EWMA y CUSUM

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (función nueva, principio 3; referencias independientes y lo recordado declarado,
  principios 1 y 12).

## Diseño

Módulo nuevo `src/pccpy/arl.py` (ARL de las cartas univariadas; el ARL de MEWMA y MCUSUM sigue en `multivariate.py`, sin
tocarlo). Las funciones públicas se exportan en `__init__.py` y `__all__`, con docstring en español y mensajes con `tr()`.

- `arl_shewhart`: fórmula cerrada con `scipy.stats.norm`.
- `arl_cusum`: ecuación integral o cadena de Markov (según la pregunta 5) para cada lado; el ARL bilateral combina los dos
  lados con `1/ARL = 1/ARL⁺ + 1/ARL⁻` (aproximación estándar), o con la cadena de dos sumas si se exige exactitud.
  [Se concretará al resolver la pregunta 5; la combinación aproximada de lados es una decisión a justificar.]
- `arl_ewma`: ecuación integral de Crowder (1987) con cuadratura de Gauss-Legendre, límites asintóticos o exactos.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Funciones paramétricas por carta | `arl(chart)` único | No depende de lo que guarde cada objeto de carta (provisional) |
| `shift` en σ del estadístico | Parámetro `n` | Menos parámetros (provisional) |
| Solo métodos exactos o numéricos | Simulación general | Reproducible y sin semillas (provisional) |

## Validación independiente

- Shewhart: fórmula cerrada aparte (tolerancia 1e-12).
- CUSUM y EWMA: Monte Carlo con ≥ 20 semillas y los valores de la literatura recordados de memoria, declarados como tales;
  la tolerancia refleja el error de la simulación (≈ 1–2 % con 20 × 2 000 corridas) y la precisión del método numérico.
- Consistencia interna: EWMA con `weight = 1` igual a la Shewhart; simetría en `shift`.
- Una comprobación por función en `run_validation()` (55 en total).

## Riesgos

- La combinación de los dos lados de la CUSUM como `1/ARL⁺ + 1/ARL⁻` es una aproximación (buena para ARL grandes); hay
  que medir su error frente a la simulación y declararlo.
- Las cifras de la literatura están recordadas de memoria: pueden estar mal; por eso cada una lleva un cálculo
  independiente.
- Precisión numérica con `h` grande o `weight` pequeño: elegir el número de nodos y comprobarlo con el contraste.

## Documentación y traducciones

Docstrings, página de referencia y guía con ejemplo ejecutable, README (es/en), CHANGELOG, catálogos `.po` y de la
documentación.
