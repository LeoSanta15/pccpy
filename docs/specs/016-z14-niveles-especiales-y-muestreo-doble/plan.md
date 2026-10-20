# Plan — 016 Z1.4: niveles especiales, muestreo doble y plan que no cabe en el lote

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (añade opciones sin cambiar lo existente) con una excepción justificada: el RF-04 corrige un
  resultado erróneo (principio 3), y el RF-02 puede hacerlo si encuentra celdas mal transcritas; ambos se avisan en
  «Cambios que alteran resultados».

## Diseño

| RF | Dónde | Cambio |
|---|---|---|
| 01 | `acceptance.py` | `_TABLA_I` pasa a 7 columnas (S-1 a S-4, I, II, III); `_letra_codigo(N, nivel)` acepta `1, 2, 3, "S-1"…"S-4"`; `ValueError` en español para otro valor |
| 02 | `acceptance.py`, `tests/` | La regla por diagonales de `_plan_z14` se sustituye por (o se comprueba contra) la tabla II-A completa si la regla difiere; los 16 AQL × 16 letras |
| 03 | `acceptance.py` | Nueva tabla `_TABLA_III_A` y `DoublePlanAttributes` (`n1`, `n2`, `ac1`, `re1`, `ac2`, `re2`); `pa(p)` con la binomial; `acceptance_sampling_attributes(..., sampling="double")` |
| 04 | `acceptance.py` | Si `n ≥ N` (o `2·n1 ≥ N`): `n = N` con aviso `UserWarning` (texto con `tr`), sin AOQ negativo |
| 05 | `acceptance.py`, `plotting.py` | `oc_curve`, `aoq_curve`, `asn_curve`, `to_frame(stable)`, `summary`, `plot`; claves estables en inglés (`tests/golden/i18n_stable.json`) |

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Tablas transcritas de las capturas, con tests que repiten la transcripción por separado | Reproducirlas con una regla (diagonales) sin comprobar | La regla ya falló una vez con Z1.4 (la validación encontró la tabla anterior mal); una transcripción revisada celda a celda es contrastable |
| Probabilidad de aceptación del plan doble por convolución binomial | Aproximación normal | Es exacta y sencilla; se contrasta con simulación |
| Un solo `acceptance_sampling_attributes` con `sampling=` (decidido) | Función nueva | Misma firma, menos superficie de API |
| Inspección rigurosa y reducida fuera de esta especificación | Hacerlas con la regla «normal» | No hay tablas; no se inventan |

## Validación independiente

- Comprobación `z14-niveles-doble` en `run_validation()`: letra de código de una malla de lotes y niveles contra la tabla I
  transcrita aparte, y `pa(p)` del plan doble contra la convolución binomial escrita a mano (tolerancia 1e-12) y contra una
  simulación de semilla fija.
- Tests de simulación con 20 semillas para `pa` y `asn`.

## Riesgos

- **Transcripción de las flechas de la tabla III-A:** las capturas son pequeñas; un error en una celda no se detecta con
  tests construidos de la misma transcripción. Mitigación: la persona responsable revisa las matrices de los tests antes
  de la Fase 1, y un test de coherencia estructural (acumulado = 2·n1, `re2 = ac2 + 1`, `re1 > ac1`, planes crecientes con el AQL).
- **El RF-02 puede encontrar errores** en planes que hoy se devuelven: cambia resultados (se avisa).
- `tests/golden/i18n_*.json` cambian si se añade el plan doble a los corpus (se regeneran y se revisan).

## Documentación y traducciones

`docs/source/acceptance.md`, README (es/en) con la nueva sección, docstrings, CHANGELOG, `make i18n-update` y catálogos `.po` de
la biblioteca y de la documentación; ficha en `BUG_CATALOG.md` para el RF-04 (y para el RF-02 si hay diferencias).
