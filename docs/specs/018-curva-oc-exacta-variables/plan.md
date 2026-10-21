# Plan — 018 Curva OC exacta de los planes por variables

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: cambia resultados existentes (principio 3), porque la `Pa` unilateral actual es una aproximación; se avisa en «Cambios que alteran resultados».

## Diseño

| RF | Dónde | Cambio |
|---|---|---|
| 01 | `acceptance.py`, `_pa_variables` | La rama `spec_type == "one"` pasa de `Φ[(z_p − k)√n/√(1 + k²/2)]` a la integral `∫ Φ(√n(z_p − k·s)) f_s(s) ds` por cuadratura de Gauss-Legendre (`_nodos_s`, 400 nodos, en caché por `n`); `z_p = norm.isf(p)` (no `ppf(1 − p)`, que pierde precisión con `p` ≈ 1e-12). `scipy.stats.nct.sf` se probó primero y se descartó: en scipy 1.9 se desvía hasta ~3·10⁻⁶. Se actualizan la docstring de `_pa_variables` y la de `SamplingPlanVariables.pa` («aproximación normal») |
| 02 | `acceptance.py` | `alpha` y `ltpd` ya salen de `_pa_variables`: no cambia código, solo valores |
| 03 | `acceptance.py` | Se conservan las guardas `p ≤ 0 → 1` y `p ≥ 1 → 0`; se comprueba que `nct.sf` no avisa con `δ` grande ni `n` grande (si lo hiciera, se envuelve en `np.errstate`) |
| 04 | `acceptance.py` | Sin cambios en la rama bilateral |

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Cuadratura de Gauss-Legendre vectorizada | `scipy.stats.nct.sf` (se probó y falló en scipy 1.9); `quad` en cada punto (10 s por `oc_curve`) | Exacta a ~1e-13 en todas las versiones y 200 veces más rápida que `quad`; `nct.sf` queda como tercera referencia en los tests |
| Referencia independiente = integral escrita aparte + simulación ≥ 20 semillas | Compararla con la fórmula de Montgomery | R-02: nunca contra la salida de pccpy ni contra la aproximación que se reemplaza |
| No tocar la OC bilateral | Rehacerla con `shift=` | Fuera de alcance (decidido en la especificación) |

## Validación independiente

Comprobación nueva en `run_validation()` (`variables-oc-exacta`): `Pa` de varios planes `(n, k)` de la tabla de MIL-STD-414 y de la malla de la especificación contra la integral numérica escrita aparte (tolerancia relativa 1e-9) y `alpha` del plan de `N=1000, aql=1,0` (valor de la integral).

## Riesgos

- **Exactitud de `nct` en scipy 1.9** (versiones mínimas): el CI lo mostraría; si falla, se usa la integral para esos casos.
- **Cambia valores** de `alpha`, `ltpd` y la curva de todos los planes unilaterales: se regeneran los goldens y se revisan línea a línea.
- **Falsa precisión:** la curva exacta supone datos normales e independientes; la documentación lo dice.

## Documentación y traducciones

Docstrings (`pa`, `_pa_variables`), `docs/source/acceptance.md` (sección MIL-STD-414: la OC es exacta bajo normalidad), README (es/en) si menciona la aproximación, CHANGELOG, `make i18n-update` y `make docs-update` con los catálogos `.po`; se quita «curva OC exacta» de los pendientes de `CLAUDE.md`.
