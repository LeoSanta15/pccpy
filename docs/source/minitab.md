# Para usuarios de Minitab

¿Conoces Minitab y quieres usar pccpy? Esta página mapea cada menú y
procedimiento de Minitab a la función equivalente en pccpy.

---

## Stat → Control Charts

### Variables Charts for Individuals

| Minitab | pccpy | Notas |
|---------|-------|-------|
| I-MR | `imr_chart(x)` | Carta de individuos y rango móvil |
| I-MR-R/S (Between/Within) | `imr_rs_chart(g)` | Requiere subgrupos como matriz 2-D |
| Z-MR | `zmr_chart(x)` | Para distribuciones no normales |
| Moving Average | `ma_chart(x, length=3)` | |

### Variables Charts for Subgroups

| Minitab | pccpy | Notas |
|---------|-------|-------|
| Xbar-R | `xbar_r_chart(g)` | Subgrupos 2–9 |
| Xbar-S | `xbar_s_chart(g)` | Subgrupos ≥10 o n variable |

### Attributes Charts

| Minitab | pccpy | Notas |
|---------|-------|-------|
| P | `p_chart(d, n)` | n puede ser array para tamaño variable |
| NP | `np_chart(d, n)` | n debe ser escalar (tamaño fijo) |
| C | `c_chart(d)` | |
| U | `u_chart(d, n)` | n puede ser array |
| Laney P′ | `laney_p_chart(d, n)` | Ajustado por sobredispersión |
| Laney U′ | `laney_u_chart(d, n)` | Ajustado por sobredispersión |

### Time-Weighted Charts

| Minitab | pccpy | Notas |
|---------|-------|-------|
| EWMA | `ewma_chart(x)` | Parámetros: `lam`, `L` |
| CUSUM | `cusum_chart(x)` | Parámetros: `k`, `h` |
| EWMA Attributes (P) | `ewma_p_chart(d, n)` | |
| EWMA Attributes (U) | `ewma_u_chart(d, n)` | |
| CUSUM Attributes (P) | `cusum_p_chart(d, n)` | |
| CUSUM Attributes (U) | `cusum_u_chart(d, n)` | |
| CUSUM Attributes (C) | `cusum_c_chart(d)` | |

### Other Charts

| Minitab | pccpy | Notas |
|---------|-------|-------|
| Zone | `zone_chart(x)` | Pesos 0-2-4-8 |
| G Chart | `g_chart(counts)` | Entre eventos raros |
| T Chart | `t_chart(times)` | Tiempo entre eventos |
| Run Chart | `run_chart(x)` | Pruebas de aleatoriedad |

---

## Stat → Quality Tools

| Minitab | pccpy | Notas |
|---------|-------|-------|
| Run Chart | `run_chart(x)` | 4 pruebas de aleatoriedad |
| Pareto Chart | `plot_pareto(pareto(categorias))` | |
| Probability Plot | `probability_plot(x)` | Anderson-Darling incluido |
| Normality Test | `normality_test(x)` | Devuelve `NormalityResult` |
| Pre-Control Chart | `precontrol(x, lsl, usl)` | Semáforo Shainin |

---

## Stat → Capability Analysis

| Minitab | pccpy | Notas |
|---------|-------|-------|
| Normal | `capability_analysis(x, lsl, usl)` | Cp, Cpk, Pp, Ppk, DPMO |
| Nonnormal | `capability_nonnormal(x, lsl, usl, dist="weibull")` | Varias distribuciones |
| Between/Within | `capability_analysis(x, lsl, usl, subgroup_size=n)` | |
| Capability Sixpack | `capability_sixpack(x, lsl, usl)` | 6 gráficos en uno |
| Box-Cox Transformation | `capability_boxcox(x, lsl, usl)` | Transforma y calcula |
| desde estadísticos | `capability_analysis_summary(mean, std_overall, n, lsl, usl)` | |

---

## Stat → Multivariate

| Minitab | pccpy | Notas |
|---------|-------|-------|
| T² Hotelling (individual) | `t2_chart(data)` | |
| MEWMA | `mewma_chart(data)` | |
| MCUSUM | `mcusum_chart(data)` | |
| Generalized Variance | `generalized_variance_chart(data)` | |

---

## Stat → Quality Tools → Gage Study

| Minitab | pccpy | Notas |
|---------|-------|-------|
| Gage R&R Study (Crossed) | `gage_rr(data, parts, operators, replicates, method='anova')` | |
| Gage R&R Study (Nested) | `gage_rr_nested(data, parts, operators, replicates)` | |
| Gage R&R Study (Xbar-R) | `gage_rr(data, ..., method='xbar_r')` | |
| Type 1 Gage Study | `gage_type1(data, reference)` | Cg, Cgk |
| Gage Linearity and Bias | `gage_linearity(measurements, references)` | |
| Attribute Agreement Analysis | `attribute_agreement(df)` | Kappa |

---

## Stat → Reliability → Acceptance Sampling

| Minitab | pccpy | Notas |
|---------|-------|-------|
| By Attributes (Z1.4) | `acceptance_sampling_attributes(N, aql)` | |
| By Variables (Z1.9) | `acceptance_sampling_variables(N, aql)` | |
| Dodge-Romig | `dodge_romig(N, ltpd=…)` o `dodge_romig(N, aoql=…)` | |

---

## Stat → Basic Statistics

| Minitab | pccpy | Notas |
|---------|-------|-------|
| Normality Test | `normality_test(x)` | Anderson-Darling |
| (sin equivalente directo) | `diagnose(x, lsl, usl)` | Diagnóstico completo de proceso |

---

## Diferencias de convención

| Concepto | Minitab | pccpy |
|----------|---------|-------|
| Límite superior de control | UCL | `ucl` / LCS |
| Límite inferior de control | LCL | `lcl` / LCI |
| Límite superior de especificación | USL | `usl` / LES |
| Límite inferior de especificación | LSL | `lsl` / LEI |
| Número de pruebas de Nelson | 8 | 8 (tests 1–8) |
| Sigma dentro de subgrupos | Within σ | `sigma_within` |
| Sigma global | Overall σ | `sigma_overall` |

---

## Flujo típico de trabajo comparado

### En Minitab

1. Stat → Control Charts → Variables Charts for Individuals → I-MR
2. Stat → Quality Tools → Capability Analysis → Normal
3. Copiar tabla de resultados a Word/Excel manualmente

### En pccpy

```python
import pccpy as pp, pandas as pd

df = pd.read_excel("datos.xlsx")
x  = df["diametro_mm"].values

# 1. Carta I-MR
carta = pp.imr_chart(x, tests="all")
carta.plot()
carta.save_plot("carta_imr.png")          # guardar gráfico
carta.to_excel("carta_imr.xlsx")          # exportar datos a Excel

# 2. Capacidad
cap = pp.capability_analysis(x, lsl=49.5, usl=50.5)
cap.plot()
cap.save_plot("capacidad.png")
cap.to_excel("capacidad.xlsx")

# 3. Todo en uno
fig, res, chart = pp.capability_sixpack(x, lsl=49.5, usl=50.5)
fig.savefig("sixpack.png", dpi=150, bbox_inches="tight")
```

---

## Ver también

- {doc}`guia_seleccion` — árbol de decisión para elegir la carta correcta
- {doc}`inicio_rapido` — ejemplos con código listo para copiar
- {doc}`tutorial_real` — tutorial completo con datos reales en CSV
