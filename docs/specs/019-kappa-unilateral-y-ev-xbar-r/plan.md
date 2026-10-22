# Plan — 019 Kappa unilateral y EV del Xbar-R con `d2`

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí con una excepción justificada: cambia resultados existentes (principio 3); se avisa en «Cambios que alteran resultados».

## Diseño

| RF | Dónde | Cambio |
|---|---|---|
| 01 | `msa.py`, `_cohen_kappa` y `_fleiss_kappa` | Con `pₑ ≥ 1` (tolerancia 1e-12) devuelven `κ = nan` y `p = nan`; el `% acuerdo` se conserva; se revisan los usos (`attribute_agreement`, `summary`, `to_frame`, `to_excel`) para que `nan` no rompa el formateo |
| 02 | `msa.py`, `_cohen_kappa` | `p_val = norm.sf(z)` en lugar de `2·sf(|z|)`; docstring y README: hipótesis alternativa `κ > 0` |
| 03 | `msa.py`, `_gage_rr_xbar_r` | `EV = R̄/d2(r)` si `p·o > 15`, `d2*(r, p·o)` si no (opción C, decidida); docstring con la regla |

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| `nan` para el kappa indefinido | Lanzar `ValueError` | Un operador degenerado no debe impedir el análisis de los demás; los `nan` son visibles |
| Unilateral | Parámetro `alternative=` | Menos superficie; Minitab (recordado) usa `P(vs > 0)` |
| `d2` con `p·o > 15`, `d2*` si no (decidido) | Siempre `d2` | Conserva la corrección de muestra pequeña; opción C decidida |

## Validación independiente

Comprobaciones nuevas en `run_validation()`: `kappa-unilateral` (p-valor = `norm.sf(κ/SE₀)` con `SE₀` escrito aparte, kappa `nan` con `pₑ = 1`) y `k1-xbar-r` (`K1 = 1/d2(r)` con `d2(2) = 2/√π` y `d2(3)` por integración aparte).

## Riesgos

- **El signo de la diferencia de EV** que dijo la auditoría («infla») es el contrario del medido (la EV sale menor); la especificación lo corrige con números.
- **Un salto en la EV** entre 15 y 16 combinaciones (≈ 0,9 %) con la opción C (decidida).
- **Cambia valores** de kappa y EV: se regeneran los goldens (`kappa_*`, Gage R&R Xbar-R) y se revisan línea a línea.

## Documentación y traducciones

Docstrings de `attribute_agreement`, `_gage_rr_xbar_r`, `docs/source` de MSA, «Notas sobre diferencias posibles con Minitab» en el README (es/en), CHANGELOG, `make i18n-update` y `make docs-update` con los catálogos `.po`.
