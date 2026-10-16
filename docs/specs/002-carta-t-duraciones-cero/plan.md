# Plan — 002 Carta T: duraciones iguales a 0

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí. El valor por defecto conserva el comportamiento actual, no se inventan datos y la
  opción nueva se valida contra un ajuste hecho aparte.

## Diseño

- `t_chart` (`src/pccpy/charts/advanced.py`) gana `zeros: str = "error"` (`"error"` | `"drop"`), validado con
  `check_method`.
- Antes de ajustar: se separan ceros y negativos. Negativos siempre lanzan `ValueError` (mensaje propio, con posiciones).
  Ceros: con `"error"` lanzan `ValueError` (mensaje propio, con posiciones y pista de `zeros="drop"`); con `"drop"` se
  excluyen, se emite un `UserWarning` con el número excluido y la carta se dibuja con el resto, igual que ya se hace
  con los valores no finitos.
- Si tras excluir no quedan datos suficientes, el `ValueError` de datos insuficientes de hoy.
- Con `shape` y `scale` históricos y `zeros="error"`, los ceros se rechazan igual (la carta se dibuja sobre `x`).

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| `zeros="drop"` excluye con aviso | Sustituir por la mitad de la resolución (opción C) | Inventa un dato; la persona usuaria decidió B |
| Valor por defecto `"error"` | `"drop"` por defecto | No cambia resultados existentes (RF-03) y obliga a decidir |
| Reutilizar el mecanismo de valores no finitos | Lógica nueva de exclusión | Cambios quirúrgicos (R-01) |

## Validación independiente

Comprobación nueva en `run_validation()`: `zeros="drop"` sobre una serie con ceros reproduce los límites de un ajuste
Weibull de la serie sin ceros hecho con `scipy.stats.weibull_min.fit(floc=0)` (tolerancia 1e-4 en forma y escala) y los
percentiles Φ(±3).

## Riesgos

- Que quien excluye ceros subestime los eventos más rápidos: el aviso lo dice y la documentación lo explica.
- Posiciones: tras excluir, los índices de los puntos de la carta deben coincidir con los de la serie sin ceros; un test
  lo fija.

## Documentación y traducciones

Docstring de `t_chart`, guía de cartas de eventos raros, FAQ (ceros), CHANGELOG (versión 0.15.1), catálogos `.po`
(`make i18n-update`, `make docs-update`) y, si cambian, los valores de `tests/golden/`.
