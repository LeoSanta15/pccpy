# Plan — 013 Mediana en las cartas de variables

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí.

## Diseño

- `charts/variables.py`: parámetro `center="mean"` en `imr_chart`, `xbar_r_chart`, `xbar_s_chart` (y `_xbar_chart`); `stage_fn` usa `np.nanmedian` (I-MR) o la
  mediana de las medias de subgrupo completos (Xbar) cuando `center="median"`; error si va con `mu` o es otro valor.
- `charts/variables.py`: `median_r_chart` con `_xbar_chart`-like: panel `"Median"` con límites `centro ± 3·cmed(n)·σ̂/…` y panel R reutilizado.
- `_constants.py`: `cmed(n)` = desviación estándar de la mediana de `n` normales estándar por integración numérica de la densidad del estadístico de
  orden (`scipy.integrate.quad`), con caché como `d2`, `d3`; `Ã2 = 3·cmed(n)/d2(n)`.
- `_probabilidad_cartas.py`: familia `"median"` (impar: Beta exacta; par: integración numérica).
- `results.py`: `_PARAMETROS["center"]`, `_VALORES_PARAMETRO` (`"median"`, `"mean_of_medians"`), `_NOMBRES_VISIBLES["Median"]`.
- `__init__.py`: exporta `median_r_chart`; `plotting.py`/`_labels.py`: `@con_etiquetas` en la carta nueva.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| `center=` como parámetro | Función aparte `imr_median_chart` | Una opción con valor por defecto compatible; imita a `sigma_method` |
| σ y límites no cambian con `center="median"` | Estimar σ también con la mediana | El estimador de σ ya se elige con `sigma_method` |
| `cmed(n)` por integración | Tabla de Ã2 de memoria | R-02: referencia independiente, no memoria |

## Validación independiente

`run_validation()`: `cmed(n)` y `Ã2` para n = 3, 5, 7, 9 contra una integración independiente (cuadratura con otro método) y Monte Carlo ≥ 20 semillas;
centro con `center="median"` contra `numpy.median`; probabilidad de fuera de límites de la carta X̃ contra simulación.

## Riesgos

- Que se interprete `center="median"` como robustez de σ: la documentación lo aclara.
- `Panel.dist` con familia nueva obliga a tocar `_probabilidad_cartas.py`; los tests de ARL/probabilidad existentes deben seguir pasando sin cambios.

## Documentación y traducciones

README (es/en) con el ejemplo y su figura, `docs/source` (cartas de variables), docstrings, `docs/locales/en`, `.po`, CHANGELOG y CLAUDE.md.
