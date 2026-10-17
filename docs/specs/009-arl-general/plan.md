# Plan — 009 ARL de las cartas de control

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (funciones nuevas, principio 3; referencias independientes y lo recordado declarado,
  principios 1 y 12).

## Diseño

Módulo nuevo `src/pccpy/arl.py` (el ARL de MEWMA y MCUSUM sigue en `multivariate.py`, sin tocarlo). Funciones públicas
paramétricas, exportadas en `__init__.py` y `__all__`, con docstring en español y mensajes con `tr()`: `arl_shewhart`,
`arl_cusum`, `arl_ewma`, `arl_sd`, `arl_range`, `arl_binomial`, `arl_poisson`, `arl_g`, `arl_t`.

- `method="numeric"` (por defecto): Shewhart y las cartas de dispersión, atributos y eventos raros, con fórmulas cerradas de
  `scipy.stats`; CUSUM y EWMA con ecuación integral y cuadratura de Gauss-Legendre (Crowder 1987; Brook y Evans 1972).
- `method="markov"`: cadena de Markov con celdas para la CUSUM y la EWMA (el mismo método que `_mewma_arl`).
- `method="simulation"`: Monte Carlo común a todas las funciones (`n_runs`, `seed`), con una longitud máxima de racha para
  que no se cuelgue con ARL enormes.
- CUSUM bilateral: la cadena de dos sumas no es unidimensional; se combinan los dos lados con
  `1/ARL = 1/ARL⁺ + 1/ARL⁻` (aproximación estándar) y se mide su error frente a la simulación, o se resuelve la cadena
  bidimensional si el error no es aceptable. Decisión a tomar con los datos de la Fase 1.
- Se reutilizan los límites que ya calculan `g_chart`, `t_chart` y las constantes de `_constants.py` para que el ARL sea el de
  la carta que dibuja pccpy.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Funciones paramétricas por carta | `arl(chart)` único | Decisión de la persona responsable |
| `shift` en σ del estadístico | Parámetro `n` | Decisión de la persona responsable |
| Tres métodos con `method` | Solo exactos | Decisión de la persona responsable |
| Implementar por fases (núcleo, luego el resto) | Todo de golpe | Una rama y PR por fase (docs/specs/README.md) |

## Validación independiente

- Shewhart, S, R, binomial, Poisson, G y T: fórmula cerrada aparte con `scipy.stats` (tolerancia 1e-12).
- CUSUM y EWMA: Monte Carlo con ≥ 20 semillas y los valores de la literatura recordados de memoria, declarados como tales;
  la tolerancia refleja el error de la simulación (≈ 1–2 % con 20 × 2 000 corridas) y la precisión del método numérico.
- Consistencia interna: EWMA con `weight = 1` igual a la Shewhart; simetría en `shift`; `"numeric"` frente a `"markov"`.
- Una comprobación por función en `run_validation()` (61 en total).

## Riesgos

- La combinación de los dos lados de la CUSUM como `1/ARL⁺ + 1/ARL⁻` es una aproximación (buena para ARL grandes).
- Las cifras de la literatura están recordadas de memoria: pueden estar mal; por eso cada una lleva un cálculo independiente.
- Precisión numérica con `h` grande o `weight` pequeño: elegir el número de nodos y de celdas y comprobarlo con el contraste.
- `studentized_range` de SciPy puede ser lenta o imprecisa para algunos `n`: medirlo en la Fase 2.
- El alcance es amplio: si una carta no se puede validar con rigor, se saca de la especificación en vez de entregarla sin
  contraste.

## Documentación y traducciones

Docstrings, página de referencia y guía con ejemplo ejecutable, README (es/en), CHANGELOG, catálogos `.po` y de la
documentación.
