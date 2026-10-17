# pccpy

[![PyPI version](https://img.shields.io/pypi/v/pccpy.svg)](https://pypi.org/project/pccpy/)
[![Python](https://img.shields.io/pypi/pyversions/pccpy.svg)](https://pypi.org/project/pccpy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/LeoSanta15/pccpy/blob/main/LICENSE)

**Statistical Process Control (SPC) in Python, Minitab-style.**

> 🇪🇸 [Versión en español](https://github.com/LeoSanta15/pccpy/blob/main/README.md)

`pccpy` is an SPC library designed for engineers and technicians who know
Minitab and want to run the same analyses from Python. All the naming
conventions (UCL/LCL, LSL/USL, Cp/Cpk/Pp/Ppk, Z.Bench, PPM, Anderson-Darling),
the sigma estimation methods and the 8 special-cause tests follow what
Minitab documents. Messages, tables and plots are in Spanish by default; English is
available with `pp.set_language("en")` (see [Message language](#message-language)); the
examples in this README assume English is active.

---

## Table of contents

1. [Installation](#installation)
   - [Message language](#message-language)
2. [Quick start](#quick-start)
3. [Worked examples with results](#worked-examples-with-results)
4. [Variables charts](#variables-charts)
   - [I-MR](#i-mr-chart)
   - [Xbar-R and Xbar-S](#xbar-r-and-xbar-s-charts)
   - [Data input formats](#data-input-formats)
   - [Historical parameters and stages](#historical-parameters-and-stages)
   - [Iterative Phase I](#iterative-phase-i)
   - [Dates on the x axis](#dates-on-the-x-axis)
5. [Attribute charts](#attribute-charts)
6. [Time-weighted charts](#time-weighted-charts)
   - [EWMA](#ewma)
   - [CUSUM](#cusum)
   - [Moving average](#moving-average)
7. [Advanced charts](#advanced-charts)
   - [Z-MR (short runs)](#z-mr-short-runs)
   - [I-MR-R/S (between/within variation)](#i-mr-rs-betweenwithin-variation)
   - [Rare events (G and T)](#rare-events-g-and-t)
   - [ARL (average run length)](#arl-average-run-length)
8. [Multivariate charts](#multivariate-charts)
   - [Hotelling's T²](#hotellings-t²)
   - [Generalized variance](#generalized-variance)
   - [MEWMA](#mewma)
   - [MCUSUM](#mcusum)
   - [Stages and Box-Cox in multivariate charts](#stages-and-box-cox-in-multivariate-charts)
9. [Special-cause tests](#special-cause-tests)
10. [Chart plotting](#chart-plotting)
11. [Process capability](#process-capability)
12. [Normality, Pareto and SPC constants](#normality-pareto-and-spc-constants)
13. [Run chart and pre-control](#run-chart-and-pre-control)
14. [EWMA and CUSUM for attributes](#ewma-and-cusum-for-attributes)
15. [Tolerance intervals](#tolerance-intervals)
16. [Acceptance sampling](#acceptance-sampling)
17. [MSA / Gage R&R](#msa--gage-rr)
18. [Accessing the result data](#accessing-the-result-data)
19. [Validation](#validation)
20. [Development](#development)
21. [License](#license)

---

## Installation

```bash
pip install pccpy
```

From GitHub (development version):

```bash
pip install git+https://github.com/LeoSanta15/pccpy.git
```

Requires Python ≥ 3.9 with NumPy, SciPy, pandas and matplotlib.

### Message language

The texts of pccpy are in Spanish by default. The language can be changed (since 0.11.0 the error and warning messages, the `summary()` output, the `to_frame()` headers —with `stable=True` for fixed keys—, the plots, the `wizard()` assistant and the remaining tables are translated; the English text is awaiting review by a person with domain knowledge):

```python
import pccpy as pp

pp.available_languages()   # ['en', 'es']
pp.set_language("en")      # or PCCPY_LANG=en; also: with pp.language("en"): ...
```

---

## Quick start

```python
import numpy as np
import pccpy as pp

rng = np.random.default_rng(1)
x = rng.normal(100, 2, 60)
x[40:] += 3           # the process shifts at observation 41

# Compute an I-MR chart with the 8 special-cause tests
chart = pp.imr_chart(x, tests=(1, 2, 3, 4, 5, 6, 7, 8))

print(chart.summary())        # Minitab session-style summary
chart.violations()            # DataFrame: panel, point, test, description
chart.to_frame()              # all the values, limits and failed tests
chart.plot()                  # matplotlib figure (shown with plt.show())
```

---

## Worked examples with results

Real figures and outputs of the examples [`examples/basic_example.py`](https://github.com/LeoSanta15/pccpy/blob/main/examples/basic_example.py) and
[`examples/advanced_example.py`](https://github.com/LeoSanta15/pccpy/blob/main/examples/advanced_example.py), with seed `default_rng(2026)`. The code is the same in every
language; the outputs, labels and plots follow the pccpy language (here, English, `PCCPY_LANG=en`). The snippets are excerpts that
run in sequence (the data come from the same `rng`); the outputs are shortened with "…" and the complete ones are in
[`output_basic_example.txt`](https://github.com/LeoSanta15/pccpy/blob/main/docs/imagenes/en/output_basic_example.txt) and
[`output_advanced_example.txt`](https://github.com/LeoSanta15/pccpy/blob/main/docs/imagenes/en/output_advanced_example.txt). They are regenerated with
`python scripts/generar_figuras_readme.py`. With `import numpy as np` and `import pccpy as pp`.

### Individual values (I-MR)

A process that shifts from 100 to 103 at observation 41, with tests 1 to 6.

```python
rng = np.random.default_rng(2026)
x = np.r_[rng.normal(100, 1.5, 40), rng.normal(103, 1.5, 20)]   # the process shifts from 100 to 103
chart = pp.imr_chart(x, tests=[1, 2, 3, 4, 5, 6])
print(chart.summary())
chart.plot()
```

```text
Control chart I-MR
  Parameters: mean=101.347, sigma=1.45895, MR_avg=1.64624, n=60
  Tests requested: 1, 2, 3, 4, 5, 6
  Flagged points: 44
    [I] point 10: test 6 (value 99.6611) - 4 out of 5 points more than 1 standard deviation (same side)
    [I] point 13: test 2 (value 99.9038) - 9 consecutive points on the same side of the center line
```

![I-MR chart with the shift and the failed tests marked](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/imr.png)

### Subgroups (Xbar-R)

25 subgroups of 5 parts, no signals.

```python
subgroups = rng.normal(50, 0.8, (25, 5))
xr = pp.xbar_r_chart(subgroups, tests="all")
print(xr.summary())
xr.plot(zones=True)
```

```text
Control chart Xbar-R
  Parameters: mean=50.0238, sigma=0.876888, subgroups=25, size=5
  Tests requested: 1, 2, 3, 4, 5, 6, 7, 8
  Result: no out-of-control points
```

![Xbar-R chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/xbar_r.png)

### Attributes (P chart with variable n)

30 samples of 150 to 250 parts, with 4 % defective.

```python
n = rng.integers(150, 250, 30)
defectives = rng.binomial(n, 0.04)
pp.p_chart(defectives, n, tests=[1, 2, 3, 4]).plot()
```

![P chart with variable limits](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/p.png)

### Process capability and Sixpack

Normal capability with limits 95 and 105, and the six views of the Capability Sixpack.

```python
data = rng.normal(100.4, 1.5, 150)
cap = pp.capability_analysis(data, lsl=95, usl=105, target=100)
print(cap.summary())
print(round(cap.cpk, 3), round(cap.ppk, 3))
fig, _, _ = pp.capability_sixpack(subgroups, lsl=48, usl=52, target=50)
```

```text
Process capability analysis (normal distribution)
  LSL=95.0000  Target=100.0000  USL=105.0000
  N=150  Mean=100.44554  Std.Dev.(within)=1.37977 [mr]  Std.Dev.(overall)=1.52887
  Potential (within) capability:
    Cp=1.21  CPL=1.32  CPU=1.10  Cpk=1.10
    Z.Bench=3.28
  Overall performance:
    Pp=1.09  PPL=1.19  PPU=0.99  Ppk=0.99  Cpm=1.05
    95% CI Pp: (0.97, 1.21)   95% CI Ppk: (0.87, 1.12)
    Z.Bench=2.94  Z.LSL=3.56  Z.USL=2.98  Sigma Level=2.94  DPMO=1,630
  Performance (PPM):          < LSL       > USL      Total
    Observed                0.00        0.00       0.00
    Expected within        39.62      481.91     521.53
    Expected overall      184.16     1446.09    1630.25
  …
1.1 0.993
```

![Capability Sixpack](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/sixpack.png)

### Non-normal data (Weibull and Box-Cox)

Normality test and capability with the fitted distribution and with Box-Cox.

```python
w = rng.weibull(1.8, 200) * 3 + 0.5
print(pp.normality_test(w))
print(pp.capability_nonnormal(w, lsl=0.1, usl=12, distribution="weibull").summary())
print(pp.capability_boxcox(w, lsl=0.1, usl=12).summary())
```

```text
Anderson-Darling: statistic = 3.3147, p-value < 0.005 (n = 200)
Capability analysis (nonnormal) - weibull distribution
  LSL=0.1000  USL=12.0000  N=200  logL=-363.872  AIC=731.745
  Percentiles: 0.135% = 0.17925   50% = 3.13714   99.865% = 8.82399
  Pp=1.38  PPL=1.03  PPU=1.56  Ppk=1.03
  Performance (PPM):          < LSL       > USL      Total
    Observed                0.00        0.00       0.00
    Expected              378.35        2.46     380.81
  …
Process capability analysis (normal distribution)
  LSL=0.1000  Target=*  USL=12.0000
  N=200  Mean=1.18909  Std.Dev.(within)=0.58063 [mr]  Std.Dev.(overall)=0.58889
  Box-Cox transformation with lambda = 0.1615 (Mean, Std.Dev. and Z.* are on the transformed scale; LSL/USL/target and observed PPM, in original units)
  Potential (within) capability:
    Cp=1.43  CPL=1.79  CPU=1.07  Cpk=1.07
    Z.Bench=3.22
  Overall performance:
    Pp=1.41  PPL=1.76  PPU=1.06  Ppk=1.06  Cpm=*
    95% CI Pp: (1.27, 1.55)   95% CI Ppk: (0.94, 1.17)
    Z.Bench=3.17  Z.LSL=5.28  Z.USL=3.17  Sigma Level=3.17  DPMO=754
```

### Pareto

Cumulative frequency table and its chart.

```python
counts = pp.pareto(["Scratch", "Dent", "Scratch", "Stain", "Scratch", "Dent", "Other"])
print(counts)
pp.plot_pareto(counts)
```

```text
  category  count    percent  cumulative
0  Scratch      3  42.857143   42.857143
1     Dent      2  28.571429   71.428571
2    Stain      1  14.285714   85.714286
3    Other      1  14.285714  100.000000
```

![Pareto diagram](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/pareto.png)

### Short runs (Z-MR)

Three parts with different means and variations on one chart.

```python
rng = np.random.default_rng(2026)              # the advanced script restarts the seed
parts = ["A"] * 12 + ["B"] * 10 + ["A"] * 12 + ["C"] * 8
means = {"A": (50, 1.0), "B": (80, 2.0), "C": (20, 0.5)}
x = np.array([rng.normal(*means[p]) for p in parts])
x[15] += 10                                    # one B part out of the ordinary
zmr = pp.zmr_chart(x, parts, mu={p: m for p, (m, _) in means.items()},
                   sigma={p: s for p, (_, s) in means.items()}, tests=(1, 2, 3, 4, 5, 6))
print(zmr.summary())
```

```text
Control chart Z-MR
  Parameters: method=historical, parts=3, runs=4, n=42, sigma_min=0.5, sigma_max=2
  Tests requested: 1, 2, 3, 4, 5, 6
  Flagged points: 4
    [MR] point 16: test 1 (value 4.22507) - 1 point more than 3 standard deviations from the center line
    [MR] point 17: test 1 (value 4.78973) - 1 point more than 3 standard deviations from the center line
    [Z] point 16: test 1 (value 4.38598) - 1 point more than 3 standard deviations from the center line
    [Z] point 38: test 4 (value -0.457385) - 14 consecutive points alternating up and down
```

![Z-MR chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/zmr.png)

### Variation between and within subgroups (I-MR-R)

With variation between lots, Xbar-R over-alarms and I-MR-R does not.

```python
lots = rng.normal(20, 1, (30, 5)) + rng.normal(0, 2, (30, 1))
print(len(pp.xbar_r_chart(lots).violations()))   # points flagged by Xbar-R
ch = pp.imr_rs_chart(lots)
print(len(ch.violations()))                      # points flagged by I-MR-R
```

```text
12
1
```

![I-MR-R chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/imr_r.png)

### Rare events (G and T)

G chart with the counts between events and T chart with the times between events.

```python
between = rng.geometric(0.01, 40) - 1
between[25] = 600
pp.g_chart(between).plot()
times = rng.weibull(1.4, 40) * 30
times[12] = 250
print(pp.t_chart(times).summary())
```

```text
Control chart T
  Parameters: distribution=weibull, shape=1.16087, scale=36.2814, n=40
  Tests requested: 1
  Flagged points: 1
    [T] point 13: test 1 (value 250) - 1 point outside the percentiles of the weibull distribution
```

![G chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/g.png)

### Zone chart

Cumulative score for a sustained shift.

```python
drift = rng.normal(0, 1, 50)
drift[30:] += 1.2                              # sustained 1.2-sigma shift
zone = pp.zone_chart(drift, mu=0.0, sigma=1.0, reset=True)
print(zone.summary())
```

```text
Control chart Zone
  Parameters: mean=0, sigma=1, weights=(0.0, 2.0, 4.0, 8.0), reset=True, n=50
  Tests requested: 1
  Flagged points: 2
    [Zone] point 43: test 1 (value 2.03228) - cumulative zone score >= 8
    [Zone] point 48: test 1 (value 2.57529) - cumulative zone score >= 8
```

![Zone chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/zona.png)

### Multivariate: T², MEWMA and MCUSUM

Phase I with 100 observations and Phase II with 50 new ones; variable 3 shifts from point 31.

```python
Sigma = [[1, .6, .3], [.6, 1, .2], [.3, .2, 1]]
hist = rng.multivariate_normal([0, 0, 0], Sigma, 100)
new = rng.multivariate_normal([0, 0, 0], Sigma, 50)
new[30:, 2] += 4                               # variable 3 shifts
mu, cov = hist.mean(axis=0), np.cov(hist, rowvar=False)
t2 = pp.t2_chart(new, mu=mu, cov=cov, n_hist=100)
first = int(t2["T2"].flagged[0]) + 1
print(t2.contributions(first).round(2))        # contribution of each variable to the signal
me = pp.mewma_chart(new, mu=mu, cov=cov)
print(int(me["MEWMA"].flagged[0]) + 1)         # first MEWMA signal
mc = pp.mcusum_chart(new, mu=mu, cov=cov)
print(int(mc["MCUSUM"].flagged[0]) + 1, round(mc.params[0]["ucl"], 2))   # first MCUSUM signal and its limit
```

```text
X1     6.81
X2     1.32
X3    16.09
Name: contribution (point 31), dtype: float64
  …
33
33 6.88
```

![Hotelling T² chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/t2.png)

![MEWMA chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/mewma.png)

![MCUSUM chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/mcusum.png)

### Stages and multivariate Box-Cox

Each stage re-estimates its own limits; with skewed data, Box-Cox per variable.

```python
two_stages = np.vstack([new[:40], new[:40] + [0, 0, 3]])      # two periods with different means: each stage estimates its own limits
labels = [1] * 40 + [2] * 40
t2_st = pp.t2_chart(two_stages, stages=labels)
print(t2_st.stage_mean[1].round(2), t2_st.stage_mean[2].round(2))
skewed = rng.lognormal(0, 0.4, (60, 3))                        # positive, skewed data
t2_bc = pp.t2_chart(skewed, boxcox=True)
print(t2_bc.params[0]["lambda_boxcox"])
```

```text
[-0.   -0.03  1.17] [-0.   -0.03  4.17]
  …
{'X1': 0.1041, 'X2': 0.114, 'X3': 0.2551}
```

### Generalized variance

Subgroups of 6 trivariate observations whose dispersion grows 2.5 times in the second half.

```python
subs = rng.multivariate_normal([0, 0, 0], Sigma, 120)
subs[60:] *= 2.5                               # dispersion grows
pp.generalized_variance_chart(subs, subgroup_size=6).plot()
```

![Generalized variance |S| chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/gv.png)

---

## Variables charts

### I-MR chart

The **Individuals and Moving Range** chart is the standard choice when each observation
is a single measurement (no subgroups). It produces two panels:
- **I panel:** individual values with ±3σ limits around the mean.
- **MR panel:** successive moving ranges with their upper limit.

```python
import numpy as np
import pccpy as pp

x = np.array([10.2, 10.5, 9.8, 10.1, 10.4, 9.9, 10.3, 10.6,
               9.7, 10.0, 10.2, 10.8, 9.6, 10.1, 10.3])

chart = pp.imr_chart(
    x,
    span=2,                # moving range length (default: 2, same as Minitab)
    sigma_method="mr",     # sigma estimator: 'mr' (default), 'median_mr', 'mssd'
    tests=(1, 2, 3),       # which special-cause tests to activate
)
print(chart.summary())
```

**`sigma_method` options:**

| Method | Calculation | When to use it |
|--------|-------------|----------------|
| `'mr'` | `MR_avg / d2` | default; same as Minitab |
| `'median_mr'` | `median(MR) / 0.9540` | more robust to outliers (span=2 only) |
| `'mssd'` | `√(MSSD / 2)` | when there are no correlated consecutive observations |

---

### Xbar-R and Xbar-S charts

When data are collected in **subgroups** (several measurements per sample), the
**Xbar-R** (small subgroups, n ≤ 8) and **Xbar-S** (large subgroups, n > 8) charts
estimate sigma using the variation **within** each subgroup, which makes them more
sensitive to shifts in the mean than the I-MR chart.

```python
data = np.array([
    [20.1, 20.3, 20.0, 20.2, 19.9],
    [20.4, 20.1, 20.5, 20.2, 20.3],
    # ... one row per subgroup
])

chart_r = pp.xbar_r_chart(
    data,
    sigma_method="rbar",  # 'rbar' (default) or 'pooled'
    tests=(1, 2, 3, 4, 5, 6, 7, 8),
)

chart_s = pp.xbar_s_chart(
    data,
    sigma_method="sbar",  # 'sbar' (default) or 'pooled'
)
```

**`sigma_method` options for Xbar:**

| Method | Calculation | When to use it |
|--------|-------------|----------------|
| `'rbar'` | `R_avg / d2(n)` | Xbar-R, fixed-size subgroups (same as Minitab) |
| `'pooled'` | `S_pooled / c4(n_total)` | Xbar-R or Xbar-S, better estimate with many subgroups |
| `'sbar'` | `S_avg / c4(n)` | Xbar-S, fixed-size subgroups (same as Minitab) |

With **unequal subgroup sizes**, `'rbar'` and `'sbar'` average the per-subgroup estimates with inverse-variance weights:
`Σ wᵢ·Rᵢ/d2(nᵢ) / Σ wᵢ` with `wᵢ = d2(nᵢ)²/d3(nᵢ)²`, and `Σ hᵢ·sᵢ/c4(nᵢ) / Σ hᵢ` with `hᵢ = c4(nᵢ)²/(1 − c4(nᵢ)²)`. With a
constant size the weights are equal and the result is the usual simple average.

![Xbar-S chart with subgroups of 10 observations](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/xbar_s.png)

---

### Data input formats

The subgroup charts (`xbar_r_chart`, `xbar_s_chart`, `ewma_chart`, `cusum_chart`,
`ma_chart`, `imr_rs_chart`, `zone_chart`, `capability_analysis`, `capability_sixpack`)
accept **five equivalent formats**:

```python
import pandas as pd

# 1. 2-D matrix: each row is a subgroup (classic format)
data_2d = np.array([[20.1, 20.3, 20.0],
                     [20.4, 20.1, 20.5],
                     [19.9, 20.2, 20.1]])
pp.xbar_r_chart(data_2d)

# 2. 1-D vector + fixed subgroup size
vector = data_2d.ravel()            # [20.1, 20.3, 20.0, 20.4, 20.1, 20.5, ...]
pp.xbar_r_chart(vector, subgroup_size=3)

# 3. 1-D vector + subgroup identifier (allows unequal sizes)
ids = np.repeat(["S1", "S2", "S3"], 3)
pp.xbar_r_chart(vector, subgroup=ids)

# Also accepts pandas Series and DataFrame directly
df = pd.DataFrame({"measure": vector, "subgroup": ids})
pp.xbar_r_chart(df["measure"], subgroup=df["subgroup"])

# 4. DataFrame in long format + column names
#    (subgroup: column of identifiers, value: column of values)
df_long = pd.DataFrame({
    "lot":   [1, 1, 1, 2, 2, 2, 3, 3, 3],
    "measure": [20.1, 20.3, 20.0, 20.4, 20.1, 20.5, 19.9, 20.2, 20.1],
})
pp.xbar_r_chart(df_long, subgroup="lot", value="measure")

# If there is only one numeric column, 'value' is detected automatically
pp.xbar_r_chart(df_long, subgroup="lot")

# 5. 1-D vector with subgroup_size when the total is not exactly divisible
#    The last incomplete subgroup is plotted with its own limits
#    but it does NOT enter the computation of sigma or the overall mean
import warnings
data_11 = np.array([20.1, 20.3, 20.0, 20.4, 20.1, 20.5, 19.9, 20.2, 20.1, 20.3, 20.4])
with warnings.catch_warnings(record=True):
    chart = pp.xbar_r_chart(data_11, subgroup_size=4)
# UserWarning: 11 observations do not form an exact number of subgroups of size 4.
# The last subgroup has 3 of 4 observations: it is included in the plot
# but NOT in the computation of the control limits.
```

---

### Historical parameters and stages

Equivalent to *Estimation options* and *Stages* in Minitab:

```python
# Known parameters (not estimated from the data)
pp.imr_chart(x, mu=100.0, sigma=2.0)

# Stages: the limits are computed independently per stage
stage_labels = ["Before"] * 30 + ["After"] * 30
chart = pp.imr_chart(x, stages=stage_labels)
chart.params        # list of dicts, one per stage
chart.params[0]     # {'stage': 'Before', 'mean': ..., 'sigma': ..., ...}
chart.params[1]     # {'stage': 'After', 'mean': ..., 'sigma': ..., ...}

# Combination: historical parameters + stages (the same parameters for all of them)
pp.imr_chart(x, mu=100, sigma=2, stages=stage_labels)
```

---

### Iterative Phase I

`phase_one()` computes the chart, **excludes the points with signals, recomputes the limits and repeats**
until none is left; `phase2()` applies those frozen limits to new data. It works with `imr_chart`,
`xbar_r_chart`, `xbar_s_chart`, `p_chart`, `np_chart`, `c_chart` and `u_chart`.

```python
rng = np.random.default_rng(3)
x_historical = rng.normal(100, 2, 60)
x_historical[[10, 33]] += 15          # two points with a special cause
x_new = rng.normal(100, 2, 20)

phase1 = pp.phase_one(pp.imr_chart, x_historical, tests=(1, 2, 3))
print(phase1.summary())    # excluded points, frozen limits and every pass
phase1.excluded            # positions (0-based) of the excluded points
phase1.chart.plot()        # chart with the final limits (in I-MR the excluded points stay as gaps)

chart_ii = phase1.phase2(x_new, tests=(1, 2))   # Phase II with the Phase I limits
```

**Already have the Phase I from another session?** Save it and load it without repeating `phase_one`, or build
the result from limits you already know:

```python
phase1.to_json("phase1.json")                        # saves what phase2() needs (not the data)
phase1 = pp.PhaseOneResult.from_json("phase1.json")  # in another session; it also accepts the JSON text
chart_ii = phase1.phase2(x_new, tests=(1, 2))

# or with parameters computed elsewhere (with transform=, an already fitted Transformation)
external = pp.PhaseOneResult.from_limits(pp.imr_chart, mu=100.0, sigma=2.0, tests=(1, 2))
chart_ii = external.phase2(x_new)
```

Safeguards: `max_iterations` (10), `min_points` (20) and `max_excluded` (25 % of the points). If one
trips, the result does not converge and a warning is issued: a process that needs to discard that many points
is not stable. **Exclude points only if you have found and corrected their special cause.** In `imr_chart`
only the signals of the I panel count (an outlier also triggers the moving range of its neighbor); change
this with `exclude_panels=`.

---

### Dates on the x axis

With a pandas Series with a **date index** (or a text index, e.g. lot numbers) the chart keeps the
labels: the plot labels the x axis with them, `to_frame()` and `violations()` add the `label` column and
`summary()` shows the date next to the point. Points are plotted in sampling order, as in Minitab.

```python
import pandas as pd

x = np.random.default_rng(1).normal(10, 1, 30)
series = pd.Series(x, index=pd.date_range("2026-03-01", periods=len(x), freq="D"))
chart = pp.imr_chart(series, tests=(1, 2))
chart.plot()                     # "Date" axis
chart.violations()               # with the date of each signal
chart.with_labels([f"L{i}" for i in range(30)])   # your own labels (one per plotted point)
```

---

## Attribute charts

When the quality characteristic is **discrete** (defective parts, number of
defects), attribute charts are used. The Laney charts correct
**overdispersion** (variability greater than expected from the theoretical model), a
frequent problem with large sample sizes.

```python
# P: fraction defective (n can vary between samples)
defectives = np.array([3, 5, 2, 4, 6, 1, 3, 5, 2, 4])
n_sample  = np.full(10, 200)    # size of each sample
pp.p_chart(defectives, n=n_sample)

# NP: number of defectives (requires constant n)
pp.np_chart(defectives, n=200)

# C: number of defects per unit (fixed n = 1 unit per sample)
defects = np.array([2, 1, 3, 0, 4, 2, 1, 3, 2, 1])
pp.c_chart(defects)

# U: defect rate per unit (n can vary)
n_units = np.array([1, 1, 2, 1, 2, 1, 1, 2, 1, 2])
pp.u_chart(defects, n=n_units)

# Laney P': same as P but corrects overdispersion (phi != 1)
pp.laney_p_chart(defectives, n=n_sample)

# Laney U': same as U but corrects overdispersion
pp.laney_u_chart(defects, n=n_units)
```

When `n` is a scalar, the same size is applied to all the samples. With a variable
`n` the limits are computed individually for each point.

![C chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/c.png)

![Laney P' chart with overdispersed proportions](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/laney_p.png)

---

## Time-weighted charts

### EWMA

The **Exponentially Weighted Moving Average** chart is more sensitive than I-MR to
small shifts in the mean (typically ≤ 1.5σ). The exact limits are
wider in the first points until they stabilize, just like Minitab.

```python
chart = pp.ewma_chart(
    x,
    weight=0.2,    # λ: smoothing factor (0 < λ ≤ 1); smaller = more memory
    k=3.0,         # sigma multiplier for the limits (default: 3)
)
# EWMA applies only test 1 (it has no tests parameter)
```

With subgroups, `sigma_method` picks the estimator (`'rbar'` by default, `'sbar'` or `'pooled'`; with individuals
`'mr'`, `'median_mr'` or `'mssd'`). `stages=` computes the target and sigma per stage and **restarts** the EWMA at the
start of each one. In-control ARL with known σ, λ = 0.2 and L = 3: ≈ 560 with asymptotic limits and ≈ 555 with exact ones (`pp.arl_ewma`, checked against a 200,000-run simulation).

**Guide for choosing λ:**

| λ | Detects best | Memory |
|---|--------------|--------|
| 0.05 – 0.10 | very small shifts (¼σ) | long |
| 0.20 | moderate shifts (½σ – 1σ) | moderate (Minitab recommended) |
| 0.40+ | similar to a Shewhart chart | short |

![EWMA chart on a small shift](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/ewma.png)

---

### CUSUM

The **Cumulative Sum** chart also detects small shifts. It uses Hawkins' tabular
scheme: two accumulators (upper `C⁺` and lower `C⁻`) that start at 0
and are compared with the decision limit `H`.

```python
chart = pp.cusum_chart(
    x,
    h=4.0,    # decision limit H (in sigma units); default: 4 (= 4σ)
    k=0.5,    # reference zone K (in sigma units); default: 0.5
    headstart=0.0,  # fast initial response (FIR) in sigma units; 0 <= headstart < H (e.g. H/2)
    # With H=4, K=0.5 the in-control ARL of the two-sided CUSUM is ≈ 168 (Hawkins and Olwell)
)
```

The plot names its two series in a legend: "C+ (upper sum)" and "C- (lower sum)". It is shown by default and removed with `chart.plot(legend=False)`.

> **Rule of thumb:** `H = 4σ` and `K = 0.5σ` balance the detection of a 1σ shift
> (out-of-control ARL ≈ 8) with an in-control ARL ≈ 168 (two-sided). For a larger in-control ARL
> raise `H` (with `H = 5`, ≈ 470). `sigma_method=` and `stages=` work as in the EWMA (the sums
> restart at `headstart` at the beginning of each stage).

![CUSUM chart: C+ and C- accumulators](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/cusum.png)

---

### Moving average

The **MA** chart averages the last `length` points to smooth out noise.
The first `length - 1` points use the average of the available data,
so their limits are wider.

```python
pp.ma_chart(
    x,
    length=5,   # moving average window; default: 3
)
```

![Moving average chart](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/ma.png)

---

## Advanced charts

### Z-MR (short runs)

When **parts with different specifications** are manufactured (different nominal means or
variabilities), they cannot be plotted on the same standard I-MR chart.
The **Z-MR** chart standardizes each observation with the parameters of its part,
making it possible to display all of them on a single chart with ±3 limits.

```python
parts   = ["A"] * 10 + ["B"] * 10 + ["A"] * 10
measures  = np.r_[
    rng.normal(50, 1, 10),   # part A: mean 50, sigma 1
    rng.normal(80, 2, 10),   # part B: mean 80, sigma 2
    rng.normal(50, 1, 10),   # part A again
]

chart = pp.zmr_chart(
    measures,
    parts,
    sigma_method="by_part",  # 'constant', 'relative', 'by_part', 'by_run'
    # mu and sigma: dict {part: value} for historical or nominal parameters
    # mu={"A": 50, "B": 80}, sigma={"A": 1, "B": 2}
)
```

**`sigma_method` options for Z-MR:**

| Method | Description |
|--------|-------------|
| `'constant'` | same sigma for all the parts |
| `'relative'` | sigma proportional to the mean of the part |
| `'by_part'` | sigma estimated by moving range within each part (default) |
| `'by_run'` | sigma estimated by moving range within each run (consecutive block) |

---

### I-MR-R/S (between/within variation)

When the subgroups have a large variation **between subgroups** (differences
between operators, shifts, lots), the Xbar-R chart generates false alarms because its control
limit only reflects the variation **within**. The **I-MR-R/S** chart separates the
two sources and treats them separately.

```python
# sub: matrix (n_subgroups x subgroup_size)
sub = rng.normal(20, 1, (25, 5)) + rng.normal(0, 1.5, (25, 1))  # between-group variation

chart = pp.imr_rs_chart(
    sub,
    within="r",   # 'r' (range, default) or 's' (standard deviation)
)
chart.params[0]
# {'sigma_within': 0.97, 'sigma_between': 1.48, 'sigma_between_within': 1.79, ...}
```

---

### Rare events (G and T)

When events are so infrequent that P or C charts would show many
zero points, the G (number of cases/parts between events) and
T (time between events) charts are used.

```python
# G: number of cases between events (geometric distribution)
between_events = rng.geometric(0.02, 40) - 1   # p = event probability
pp.g_chart(between_events)
pp.g_chart(between_events, p=0.02, benneyan=True)   # adds the Benneyan test (runs of zeros)

# T: time between events (Weibull or exponential distribution)
times = rng.weibull(1.5, 40) * 30
pp.t_chart(times)          # Weibull (default)
pp.t_chart(times, distribution="exponential")  # exponential
```

The limits of the G chart are based on exact percentiles of the geometric
distribution; those of the T chart on the Weibull or exponential distribution fitted by
maximum likelihood.

The Benneyan test (`benneyan=True`) signals `c` or more consecutive counts equal to 0,
with `c` the smallest integer such that `p^c ≤ 1 − Φ(k)`; it detects events becoming
more frequent, which the lower limit of 0 of the G chart cannot show. Possible differences
from Minitab: Minitab enables it by default and pccpy does not; the formula for `c` is
pccpy's own definition, not checked against Minitab (its formula could not be consulted).

![T chart (time between events)](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/t.png)

### ARL (average run length)

To compare or design charts, `pccpy` computes the ARL (expected number of points until the first signal) of the Shewhart, CUSUM
and EWMA charts, of the S and R charts, of the attribute charts (NP/P and C/U with constant size) and of the rare-event charts
(G and T):

```python
pp.arl_shewhart(k=3)                       # 370.4 in control
pp.arl_shewhart(k=3, shift=1.0)            # 43.9 with the mean shifted 1σ of the statistic
pp.arl_cusum(h=4, k=0.5, shift=1.0)        # 8.4
pp.arl_ewma(weight=0.2, L=3, shift=1.0)    # 10.8
pp.arl_cusum(h=4, k=0.5, shift=1.0, method="simulation", n_runs=20_000, seed=1)  # Monte Carlo, reproducible
```

`method` chooses `"numeric"` (default), `"markov"` or `"simulation"`. Known parameters, independent observations and only the
"one point outside the limits" rule are assumed (no tests 2 to 8). With attributes and rare events the in-control ARL is not
370.4, and the G and T charts detect events spreading out much better than events getting closer together. See the
[ARL guide](https://github.com/LeoSanta15/pccpy/blob/main/docs/source/arl.md). It has not been compared with Minitab's ARL.

With a chart already built, `chart.probability()` gives the probability of a value of the statistic it plots (with the process in
control and the chart parameters treated as known); with no arguments it is the probability that one point falls outside the limits,
and its inverse is the in-control ARL:

```python
chart = pp.xbar_r_chart(subgroups, mu=50, sigma=2)
p = chart.probability()                          # one point outside the limits: 0.0027
1 / p.probability                                # 370.4, the in-control ARL
chart.probability(above=51).probability          # P(subgroup mean > 51)
chart.probability(panel="R", above=6).probability    # P(range > 6), on the R panel
chart_p.probability(above=0.08, point=[1, 3])    # with variable n, give the point (1-based)
```

The I-MR, Xbar-R, Xbar-S, P, NP, C, U, EWMA, G and T charts support the query; it returns the same `ProbabilityResult` as capability
(with `dpmo`, `dpu` and `sigma` as `None`, and the `panel` and `point` fields). It has not been compared with Minitab.

---

## Multivariate charts

### Hotelling's T²

Multivariate equivalent of the I-MR or Xbar chart. It detects simultaneous
shifts in several correlated variables. The `contributions()` method
identifies which variable(s) caused the signal.

```python
Sigma = [[1, .6, .3], [.6, 1, .2], [.3, .2, 1]]
hist  = rng.multivariate_normal([0, 0, 0], Sigma, 100)   # Phase I data
new_data  = rng.multivariate_normal([0, 0, 0], Sigma, 50)
new_data[35:, 2] += 4     # variable 3 shifts at point 36

# --- Phase I: parameters estimated from the same data ---
chart1 = pp.t2_chart(hist)
print(chart1.summary())

# --- Phase II: parameters taken from the historical period ---
chart2 = pp.t2_chart(
    new_data,
    mu=hist.mean(axis=0),
    cov=np.cov(hist, rowvar=False),
    n_hist=100,     # n of the historical estimation (affects the limit)
)

# Diagnose: which variable caused the signal at point 36?
chart2.contributions(36)     # pandas Series with the contribution of each variable

# With subgroups (one row = one observation; subgroup_size groups n rows at a time)
pp.t2_chart(new_data, subgroup_size=5)

# With a DataFrame: the column names appear in contributions()
import pandas as pd
df = pd.DataFrame(new_data, columns=["Temperature", "Pressure", "Flow"])
pp.t2_chart(df)
```

**Type of limit depending on what is provided:**

| `mu` / `cov` | `n_hist` | Distribution | Phase |
|---|---|---|---|
| Not given | — | Beta (individuals) / F (subgroups) | I |
| Given | Given | F adjusted to n_hist | II |
| Given | Not given | χ² | known parameters |

---

### Generalized variance

Complementary panel to T² for **subgrouped data**: it monitors the multivariate
dispersion through the determinant of the sample covariance matrix `|S|`.

```python
pp.generalized_variance_chart(
    new_data,
    subgroup_size=5,
    cov=np.cov(hist, rowvar=False),   # Historical Sigma (no mean: it only measures dispersion)
)
```

---

### MEWMA

Multivariate version of the EWMA chart. Very sensitive to small,
sustained shifts in the mean vector.

```python
chart = pp.mewma_chart(
    new_data,
    mu=hist.mean(axis=0),
    cov=np.cov(hist, rowvar=False),
    weight=0.1,    # λ (default: 0.1)
    arl=200,       # target in-control ARL (the H limit is computed automatically)
)

# Compute the H limit separately
H = pp.mewma_limit(p=3, weight=0.1, arl=200)
print(f"H = {H:.3f}")   # p: number of variables
```

---

### MCUSUM

Multivariate version of the CUSUM chart (Crosier's scheme). It also detects
small sustained shifts.

```python
chart = pp.mcusum_chart(
    new_data,
    mu=hist.mean(axis=0),
    cov=np.cov(hist, rowvar=False),
    k=0.5,     # reference zone (default: 0.5)
    arl=200,   # the H limit is computed automatically
)

H = pp.mcusum_limit(p=3, k=0.5, arl=200)
```

---

### Stages and Box-Cox in multivariate charts

The 4 multivariate charts (T², generalized variance, MEWMA and MCUSUM) accept
`stages` and `boxcox`, just like the univariate charts:

```python
stage_labels = [1] * 40 + [2] * 40

# Without mu/cov: each stage re-estimates its parameters
c = pp.t2_chart(data, stages=stage_labels)
c.stage_mean[1]     # mean vector of stage 1
c.stage_mean[2]     # mean vector of stage 2
c.contributions(45) # uses the mean/covariance of the stage of point 45

# With mu/cov: the same parameters in all the stages
pp.t2_chart(data, mu=mu, cov=cov, n_hist=100, stages=stage_labels)

# MEWMA and MCUSUM reset the accumulator at the start of each stage
pp.mewma_chart(data, stages=stage_labels)
pp.mcusum_chart(data, stages=stage_labels)

# Box-Cox: estimates one lambda per variable (not compatible with historical mu/cov)
c = pp.t2_chart(positive_data, boxcox=True)
c.params[0]["lambda_boxcox"]    # {'Var1': 0.42, 'Var2': 1.13, ...}
pp.mewma_chart(positive_data, boxcox=True)
pp.mcusum_chart(positive_data, boxcox=True)
```

---

## Special-cause tests

`pccpy` implements the **8 Western Electric / Nelson tests** as
Minitab documents them, with their default K parameters:

| No. | Description | Default K | Minitab equivalent |
|----|-------------|-----------|--------------------|
| 1 | 1 point beyond Kσ | 3 | Test 1 |
| 2 | K consecutive points on the same side of the CL | 9 | Test 2 |
| 3 | K consecutive points trending (rising or falling) | 6 | Test 3 |
| 4 | K points alternating up/down | 14 | Test 4 |
| 5 | 2 out of 3 points beyond 2σ on the same side | 2 | Test 5 |
| 6 | 4 out of 5 points beyond 1σ on the same side | 4 | Test 6 |
| 7 | K consecutive points within ±1σ | 15 | Test 7 |
| 8 | K consecutive points on alternating sides of the CL beyond 1σ | 8 | Test 8 |

```python
# Select tests and adjust parameters
chart = pp.imr_chart(
    x,
    tests=(1, 2, 5),            # activate only tests 1, 2 and 5
    test_params={2: 7, 5: 3},   # change the K of test 2 to 7 and that of test 5 to 3
)

# Activate all the tests
chart = pp.imr_chart(x, tests="all")

# No tests (only compute the limits)
chart = pp.imr_chart(x, tests=None)

# See the out-of-control points
chart.violations()          # DataFrame: panel, point, test, value, description
chart.in_control            # True if no test failed
chart.panels[0].flagged     # indices (0-based) of points flagged on the I panel
```

Each type of chart applies the corresponding subset:
- **Full (1-8):** I, Xbar, Z charts
- **Basic (1-4):** R, S, G, T charts, attributes (P, NP, C, U, Laney). On R and S they are approximate: ranges and
  standard deviations are not normal
- **Test 1 only:** MR chart (moving ranges are autocorrelated and skewed: with `tests="all"` test 2 fired in 45 % of
  stable series), EWMA, CUSUM, MA, T², MEWMA, MCUSUM

---

## Chart plotting

All the charts are plotted with `plot_control_chart()`. The plots include
by default the **±1σ and ±2σ zone lines** (dotted gray), just like
Minitab, and mark in red the points that fail any test with the
test number.

```python
import matplotlib.pyplot as plt

chart = pp.imr_chart(x, tests=(1, 2, 3))

# With σ zones visible (default)
fig = pp.plot_control_chart(chart)
plt.show()

# No zones (only UCL, CL, LCL)
fig = pp.plot_control_chart(chart, zones=False)

# With a custom title and figure size
fig = pp.plot_control_chart(chart, title="Shaft diameter (mm)", figsize=(14, 7))

# Direct access from the chart object
chart.plot(title="Mi chart")
```

The **sigma zones** on the chart make it possible to apply tests 5, 6, 7 and 8 visually:
- **Zone A** (±2σ to ±3σ): e.g. test 5 — 2 out of 3 points in zone A
- **Zone B** (±1σ to ±2σ): e.g. test 6 — 4 out of 5 points in zone B or beyond
- **Zone C** (0 to ±1σ): e.g. test 7 — 15 consecutive points in zone C

---

## Process capability

### Normal capability

```python
data = rng.normal(10, 0.1, 100)

res = pp.capability_analysis(
    data,
    lsl=9.7,           # Lower Specification Limit
    usl=10.3,          # Upper Specification Limit
    target=10.0,       # target (for Cpm; optional)
    subgroup_size=5,   # with subgroups: sigma_within ≠ sigma_overall
)
print(res.summary())
# Cp, CPL, CPU, Cpk, Pp, PPL, PPU, Ppk, Cpm, upper/lower Z.Bench, total PPM

res.to_frame()   # all the indices as a DataFrame
res.plot()       # histogram with within / overall curves and specifications
```

**Difference between Cp/Cpk and Pp/Ppk:**

| Index | σ used | Interprets |
|-------|--------|------------|
| Cp, Cpk | **within**-subgroup sigma | potential capability of the stable process |
| Pp, Ppk | **overall** sigma (all the data) | actual performance including between-subgroup variation |

If the process is in control, Cpk ≈ Ppk. A large difference indicates instability
or between-subgroup variation.

![Normal capability histogram](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/capability.png)

---

### Non-normal capability

When the data do not follow a normal distribution (confirmed with `normality_test`)
9 alternative distributions can be used:

```python
res_nn = pp.capability_nonnormal(
    data,
    lsl=1.0,
    usl=20.0,
    distribution="weibull",   # see list below
)
print(res_nn.summary())
```

**Available distributions:**
`"normal"`, `"lognormal"`, `"weibull"`, `"gamma"`, `"exponential"`,
`"loglogistic"`, `"logistic"`, `"largest_extreme"`, `"smallest_extreme"`

The parameters are fitted by maximum likelihood. The Pp/Ppk indices are computed
with the **percentile method** (ISO 22514-2), which is compatible with Minitab.

![Capability with a Weibull fit](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/capability_nonnormal.png)

---

### Capability with Box-Cox transformation

```python
res_bc = pp.capability_boxcox(
    data,
    lsl=1.0,
    usl=20.0,
    # lam=None  # if None, it is estimated by maximum likelihood
)
print(res_bc.summary())
res_bc.transform     # {'lambda': 0.42}
```

![Capability with a Box-Cox transformation](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/capability_boxcox.png)

---

### Probability of a value

```python
res = pp.capability_analysis(x, lsl=44, usl=56, subgroup_size=1)
p = res.probability(below=47)         # P(X < 47): probability, ppm, dpmo and dpu
res.probability(between=(48, 52))     # between two values (dpmo and dpu: None)
res.probability().ppm                 # no arguments: outside LSL/USL (= expected PPM)
res.probability(below=[45, 46, 47]).to_frame()   # arrays: one row per value
```

Values are in the original units (also with Box-Cox or Johnson); `sigma="within"` uses the within-subgroup sigma and
`opportunities=` sets the opportunities per unit for the DPU. With `capability_nonnormal` it uses the fitted
distribution. It assumes the estimated mean and sigma are known and has not been compared with Minitab.

---

### Outlier tests (Grubbs and generalized ESD)

```python
r = pp.outlier_test(x)                    # Grubbs: one outlier
r = pp.outlier_test(x, method="esd")      # Rosner's ESD: several, without masking
r.outlier_indices, r.outlier_values, r.summary()
```

They assume normal data (without the outliers) and **do not justify deleting a data point**: investigate its origin. With process data over time use control charts. Verified against the published Grubbs table and Rosner's example from the NIST handbook.

---

### Skewed data: quick guide

| I want to… | Use |
|---|---|
| Know why the data are not normal | `pp.diagnose(x)` → `non_normal_reason`, ready-to-run recommendation |
| Capability with skewed data | `capability_analysis(x, lsl, usl, transform="yeo-johnson")`, `capability_boxcox` or `capability_nonnormal(distribution=…)` |
| A reliable I-MR or Xbar chart | `imr_chart(x, transform="yeo-johnson")` (asymmetric limits in original units) |
| Intervals without assuming normality | `ci_method="bootstrap"`, `pp.bootstrap_summary(x)`, `pp.bootstrap_ci(x, function)` |

Full guide, with the limits and the simulation results: [`docs/source/datos_asimetricos.md`](https://github.com/LeoSanta15/pccpy/blob/main/docs/source/datos_asimetricos.md) (in Spanish; the documentation site has the English version).

---

### Bootstrap intervals (skewed data)

With skewed data the normal intervals (`x̄ ± t·s/√n`, chi-square for sigma, Bissell for Ppk) lose coverage. `bootstrap_ci` resamples your data and assumes no shape: percentile or **BCa** (corrects bias and skewness). It works for any statistic, scalar or vector, with the same resamples.

```python
import numpy as np

r = pp.bootstrap_ci(data, np.mean, method="bca", n_boot=2000, seed=1)
r.estimate, r.ci            # estimate and (lower, upper) interval
print(r.summary())

# several statistics at once; vectorized=True (np.mean, np.std…) is much faster
sd = lambda v, axis=-1: np.std(v, axis=axis, ddof=1)
pp.bootstrap_ci(data, sd, vectorized=True, seed=1).ci
```

With `pp.bootstrap_summary(data, seed=1)` you get the mean, the median and the standard deviation at once with their bootstrap interval and, as a reference, the classic interval (Student's `t`, chi-square and order statistics).

In simulation (gamma(2), n = 60) the BCa interval for the standard deviation covers ≈ 92 % versus ≈ 83 % for the chi-square interval; for the mean the t interval already holds up well. With n < 20 it warns: the bootstrap also loses coverage.

---

### Capability for attribute data (binomial and Poisson)

When the data are "defective / good" or a count of defects there is no Cp or Cpk: capability is the **defect rate**
with its exact interval. `capability_binomial` gives the % defective (Clopper-Pearson), the PPM and the Z level;
`capability_poisson` gives the defects per unit (Garwood) and, with `opportunities=`, the DPMO and Z. Both include the
chi-square test that the rate is constant across samples: if it fails, the process is not stable and the capability is
not reliable (check the P or U chart).

```python
defectives = [3, 5, 2, 4, 6, 1, 3, 5]
defects = [3, 5, 2, 4, 6, 1, 3, 5]
r = pp.capability_binomial(defectives, n=200)         # constant n, or one per sample
print(r.summary())
r.p_ci, r.ppm, r.z, r.homogeneous
r.plot()                                               # rate by sample and cumulative estimate

q = pp.capability_poisson(defects, units=10, opportunities=20)
q.dpu, q.dpu_ci, q.dpmo, q.z
```

![Binomial capability by sample](https://raw.githubusercontent.com/LeoSanta15/pccpy/main/docs/imagenes/en/capability_binomial.png)

---

### Capability Sixpack

Generates the **6 views** of Minitab's Capability Sixpack in a single figure:
control chart (within), range/standard deviation (within), last 25 obs/subgroups,
capability histogram, normal probability plot and capability plot.

```python
fig, res, chart = pp.capability_sixpack(
    data,
    lsl=9.7,
    usl=10.3,
    subgroup_size=5,
    tests=(1,),
)
plt.show()
# fig: matplotlib figure
# res: CapabilityResult with all the indices
# chart: ControlChart (Xbar-R, Xbar-S or I-MR depending on the subgroup size)
```

---

## Normality, Pareto and SPC constants

### Normality test

```python
result = pp.normality_test(
    data,
    method="anderson",      # 'anderson' (default), 'shapiro', 'dagostino'
)
print(result)
# Anderson-Darling: statistic = 0.5302, p-value = 0.165 (n = 40)

result.statistic    # value of the statistic
result.p_value      # p-value
result.reject       # True if normality is rejected at α = 0.05

# Normal probability plot with Anderson-Darling
pp.probability_plot(data)
```

---

### Pareto

```python
defects = ["Scratch", "Dent", "Scratch", "Paint", "Scratch",
             "Dent", "Other", "Scratch", "Paint", "Dent"]

table = pp.pareto(defects)
print(table)
#       category  frequency  percent  cumulative
# 0       Scratch          4        40.0       40.0
# 1  Dent              3        30.0       70.0
# 2      Paint            2        20.0       90.0
# 3         Other          1        10.0      100.0

pp.plot_pareto(table)   # Pareto chart with cumulative curve
```

---

### SPC constants

Computed by **numerical integration** for any `n ≥ 2` —not only for the
tabulated values up to n = 25 usually published in books.

```python
pp.d2(5)   # 2.3259  (factor for estimating sigma from R; n=5)
pp.d3(5)   # 0.8641  (for the moving range limit)
pp.c4(5)   # 0.9400  (factor for estimating sigma from s)
pp.c5(5)   # 0.3412  (for the standard deviation limit)

# Full table of constants for n=5
pp.control_chart_constants(5)
# {'n': 5, 'd2': 2.326, 'd3': 0.864, 'c4': 0.940, 'c5': 0.341,
#  'A2': 0.577, 'A3': 1.342, 'D3': 0.0, 'D4': 2.115, 'B3': 0.0, 'B4': 2.089}
```

---

## Run chart and pre-control

### Run chart

Detects non-random patterns in the data through **four hypothesis tests**
(clustering, mixtures, trends, oscillation) using the distribution of runs.

```python
rc = pp.run_chart(x)
print(rc.summary())
# Median: 100.12
# p clustering: 0.23  p mixtures: 0.77  p trends: 0.04  p oscillation: 0.96
# → Trend detected (p < 0.05)

rc.to_frame()   # point, value, side (above/below), run
rc.plot()       # chart with the median and points colored by side
```

| Test | Detects |
|------|---------|
| Clustering | too few runs → pattern by cycles or mixture of distributions |
| Mixtures | too many runs → two distributions alternating |
| Trends | long consecutive runs → process drift |
| Oscillation | excessive up/down alternation → overcontrol |

---

### Pre-control (Shainin)

Four-zone traffic light based on the tolerance width. It does not require sigma
estimation: it only uses LSL/USL and marks each observation with the color of its zone.

```python
pc = pp.precontrol(x, lsl=94, usl=106)
print(pc.summary())
# Green (G): 45   Low yellow (Y-): 3   High yellow (Y+): 2   Red: 0
# Adjustment signals: 0

pc.zones          # list of labels: 'G', 'Y-', 'Y+', 'R-', 'R+'
pc.signals        # list of indices where an adjustment signal was detected
pc.to_frame()     # DataFrame with point, value and zone
pc.plot()
```

**Pre-control zones:**

| Zone | Range | Action |
|------|-------|--------|
| Green (G) | USL/4 around the center (50% of the tolerance) | Continue |
| Low yellow (Y−) | [LSL, LSL + 25% tol] | Caution |
| High yellow (Y+) | [USL − 25% tol, USL] | Caution |
| Red (R−/R+) | Below LSL or above USL | Stop |

---

## EWMA and CUSUM for attributes

Versions of the time-weighted charts for **discrete data** (fractions
defective, defect rates). The transient limits are exact and
widen in the first samples until they stabilize.

```python
defectives = [3, 5, 2, 4, 6, 1, 3, 5, 2, 4]
n_sample  = 200   # scalar or array of equal length

# EWMA-P: fraction defective
chart = pp.ewma_p_chart(defectives, n=n_sample, weight=0.2)

# EWMA-U: defect rate per unit
defects   = [2, 1, 3, 0, 4, 2, 1, 3, 2, 1]
n_units = [1, 1, 2, 1, 2, 1, 1, 2, 1, 2]
chart_u = pp.ewma_u_chart(defects, n=n_units)

# CUSUM-P: cumulative sum for fraction defective
chart_cp = pp.cusum_p_chart(defectives, n=n_sample, h=4, k=0.5)

# CUSUM-C: cumulative sum for number of defects
chart_cc = pp.cusum_c_chart(defects, h=4, k=0.5)
```

With a variable `n` (array), the limits are adjusted point by point to the sample size.

---

## Tolerance intervals

A **tolerance interval** (α, p) guarantees —with confidence 1−α— that at least
a fraction `p` of the population falls within the computed limits.

### Normal two-sided and one-sided

```python
rng = np.random.default_rng(1)
x50 = rng.normal(100, 2, 50)

# Two-sided: with 95% confidence, ≥95% of the population in (LL, UL)
res = pp.tolerance_interval(x50, coverage=0.95, confidence=0.95)
print(res.summary())
# LL = 93.7, UL = 106.3, k = 2.382 (normal two-sided, n=50, 95/95)

res.lower          # lower limit
res.upper          # upper limit
res.k_factor       # k factor
res.achieved_confidence  # achieved confidence (if the method is nonparametric)
res.to_frame()
res.plot()

# One-sided upper: P(X ≤ UL) ≥ 0.95 with 95% confidence
res_u = pp.tolerance_interval(x50, sides="upper")

# One-sided lower: P(X ≥ LL) ≥ 0.95 with 95% confidence
res_l = pp.tolerance_interval(x50, sides="lower")
```

### Nonparametric

```python
x300 = rng.normal(100, 2, 300)
res_np = pp.tolerance_interval(x300, method="nonparametric", coverage=0.95)
# The limits are order statistics; n≈300 for 95/95 two-sided
```

### From summary statistics

When only the mean, standard deviation and n are available (no individual data):

```python
res_s = pp.tolerance_interval_summary(
    mean=100.0, std=2.0, n=50,
    coverage=0.95, confidence=0.95,
    sides="two",
)
print(res_s.summary())   # Same indices as tolerance_interval
```

---

## Acceptance sampling

### Z1.4 — Attributes (ANSI/ASQ Z1.4)

Selects the sampling plan from the Z1.4 standard based on the lot size and the AQL:

```python
# Lot N=1000, AQL=1%
plan = pp.acceptance_sampling_attributes(N=1000, aql=1.0)
print(plan.summary())
# n=80, Ac=2, Re=3, LTPD=6.5%, AOQL=0.87%

plan.n          # sample size
plan.c          # acceptance number (Ac)
plan.ltpd       # LTPD (fraction that gives Pa ≈ 0.10)
plan.aoq_max    # AOQL

plan.pa(0.01)   # P(accept | p=1%) — OC curve
plan.oc_curve() # DataFrame with columns p_defectivo, P(aceptar) (stable=True: defective_fraction, p_accept)
plan.aoq_curve()# DataFrame with columns p_defectivo, AOQ (stable=True: defective_fraction, aoq)
plan.plot()     # OC curve + AOQ curve in one figure
```

### Z1.9 — Variables (ANSI/ASQ Z1.9)

> ⚠️ The built-in Z1.9 table **does not reproduce the standard** and the function emits a `UserWarning`. To decide with Z1.9, pass `n=` and `k=` taken from your copy of the standard.

Requires the characteristic to be normally distributed; it uses the mean and standard deviation
to estimate the fraction defective through the quality statistic Q:

```python
plan_v = pp.acceptance_sampling_variables(N=1000, aql=1.0, spec_type="one")
# spec_type='one'  → one-sided specification (only USL or only LSL)
# spec_type='two'  → two-sided specification

sample = rng.normal(10.5, 0.2, plan_v.n)
dec = plan_v.evaluate(sample, usl=11.0)
print(dec)
# {'xbar': 10.49, 's': 0.19, 'Q_usl': 2.68, 'accept': True}

plan_v.oc_curve()   # OC curve of the plan
```

### Dodge-Romig

Plans that minimize the average total inspection (ATI):

```python
# LTPD plan: designed for LTPD=5% with process average p̄=1%
plan_ltpd = pp.dodge_romig(N=1000, ltpd=0.05, process_avg=0.01)
print(plan_ltpd.summary())   # n, Ac, AOQL

# AOQL plan: designed for AOQL=1%
plan_aoql = pp.dodge_romig(N=1000, aoql=0.01, process_avg=0.005)
print(plan_aoql.summary())   # n, Ac, LTPD

plan_ltpd.n        # sample size
plan_ltpd.c        # acceptance number
plan_ltpd.aoql     # AOQL
plan_ltpd.ltpd     # LTPD
plan_ltpd.to_frame()
```

---

## MSA / Gage R&R

### Crossed (ANOVA and Xbar-R)

The crossed design measures each **part** with all the **operators**. It is the most common
when the measurement does not destroy the part.

```python
# 10 parts × 3 operators × 2 replicates (array order: part0-op0, part0-op1, ...)
data = rng.normal(0, 1, 10 * 3 * 2)

# ANOVA method (more precise)
grr = pp.gage_rr(data, parts=10, operators=3, replicates=2, tolerance=20.0)
print(grr.summary())
# Repeatability: 14.3%  Reproducibility: 3.1%  %R&R: 14.6%  NDC: 9

grr.pct_gage            # % study variation of the total measurement system
grr.var_repeatability   # repeatability variance
grr.var_reproducibility # reproducibility variance
grr.var_part            # part variance
grr.var_total           # total (sum of the previous three)
grr.ndc                 # number of distinct categories
grr.anova_table         # DataFrame with DF, SS, MS, F, p-value (always in Spanish)
grr.anova_frame()       # the same table in the active language (stable=True: df, ss, ms, f, p_value)
grr.to_frame()
grr.plot()

# If the part×operator interaction is not significant (p > alpha_interaction, 0.25 by default) it is removed from
# the model: the components come from the reduced model (grr.anova_reduced); alpha_interaction=1.0 always keeps it.
# At least 2 replicates are required.

# Xbar-R method (classic AIAG: d2* constants; K2 = 0.5231 with 3 operators, K3 = 0.3146 with 10 parts)
grr_xr = pp.gage_rr(data, parts=10, operators=3, replicates=2,
                    method="xbar_r", tolerance=20.0)
# grr_xr.anova_table is None (the Xbar-R method does not produce an ANOVA table)
```

### Nested

When the operators measure **different parts** (the measurement destroys the sample
or the parts are not interchangeable between operators):

```python
grr_n = pp.gage_rr_nested(data, parts=10, operators=3, replicates=2)
print(grr_n.summary())
```

### Type 1 study — bias and repeatability

Measures a **reference part** several times with a single operator to estimate
the bias and the repeatability:

```python
ref_meas = rng.normal(10.02, 0.05, 25)   # 25 reference measurements = 10.0
t1 = pp.gage_type1(ref_meas, reference=10.0, tolerance=0.5)
print(t1.summary())
# Bias: 0.02 mm  t = 2.0  p = 0.057  Cg = 1.67  Cgk = 1.33

t1.bias      # bias = mean - reference
t1.t_stat    # t statistic for H₀: bias = 0
t1.p_value   # p-value of the two-sided test
t1.cg        # instrument capability (0.2×tolerance / 6s)
t1.cgk       # capability considering bias

# From summary statistics (no individual data)
ts = pp.gage_type1_summary(
    mean=10.02, std=0.05, n=25,
    reference=10.0, tolerance=0.5,
)
```

### Linearity and bias

Evaluates whether the bias is constant across the whole operating range of the instrument:

```python
refs       = np.repeat([2, 4, 6, 8, 10], 5)    # 5 references × 5 replicates
measurements = refs + rng.normal(0.05, 0.1, 25)

lin = pp.gage_linearity(measurements, refs, tolerance=10.0)
print(lin.summary())
# Slope: 0.001  Intercept: 0.048  R²: 0.002  Linearity: 0.01%

lin.slope      # slope of the bias ~ reference regression
lin.intercept
lin.r_squared
lin.to_frame()
lin.plot()
```

### Attribute agreement (Kappa)

When the characteristic is categorical (conforming/nonconforming, grades, colors):

```python
import pandas as pd

ratings = pd.DataFrame({
    "Op1": ["G", "D", "G", "G", "D"] * 4,
    "Op2": ["G", "D", "G", "D", "D"] * 4,
    "Op3": ["G", "G", "G", "G", "D"] * 4,
})
reference = np.array(["G", "D", "G", "G", "D"] * 2)

atr = pp.attribute_agreement(ratings, reference=reference, replicates=2)
print(atr.summary())
# Fleiss kappa: 0.84
# Op1 vs ref: κ=0.90  Op2 vs ref: κ=0.80  Op3 vs ref: κ=0.82

atr.fleiss_kappa           # Fleiss' kappa (agreement among all operators)
atr.kappa_vs_reference     # DataFrame with kappa, SE and p-value per operator
atr.to_frame()
```

---

## Accessing the result data

All the control charts return a `ControlChart` object (the multivariate ones
return `MultivariateChart`). All the computed data can be accessed:

```python
chart = pp.imr_chart(x, tests=(1, 2, 3))

# --- Access by panel name ---
panel_i  = chart["I"]    # individuals panel
panel_mr = chart["MR"]   # moving range panel

# Direct NumPy arrays
panel_i.values    # plotted values
panel_i.center    # center line (CL)
panel_i.ucl       # upper control limit (UCL)
panel_i.lcl       # lower control limit (LCL)
panel_i.sigma     # sigma estimated point by point
panel_i.stage     # stage label of each point
panel_i.flagged   # 0-based indices of flagged points

# --- DataFrame of one panel ---
panel_i.to_frame()
# columns: point, stage, value, CL, UCL, LCL, failed_tests

# --- Wide DataFrame (all the panels) ---
chart.to_frame()
# columns: point, stage, I_value, I_CL, I_UCL, I_LCL, I_failed_tests,
#            MR_value, MR_CL, MR_UCL, MR_LCL, MR_failed_tests

# --- Out-of-control points ---
chart.violations()
# columns: panel, point, test, value, description

# --- Estimated parameters ---
chart.params        # list of dicts, one per stage
chart.params[0]     # {'stage': 1, 'mean': 10.2, 'sigma': 0.31, 'mr_mean': 0.35, 'n': 30}

# --- Process status ---
chart.in_control    # True if there are no out-of-control points
chart.summary()     # text summary

# --- Programmatic access to violations per test ---
chart.panels[0].violations   # dict {test: array of indices}
```

---

## Validation

More than 1,800 automated tests. The references are independent of pccpy:

- Constants d2, d3, c4 against published tables (Montgomery).
- I-MR, Xbar-R and Xbar-S limits against manual computation with A2, D3, D4, A3, B3, B4.
- Anderson-Darling against `statsmodels` (matches to 9 decimals).
- EWMA and CUSUM against the manual recursion.
- The 8 special-cause tests against hand-built cases, including
  the edge cases.
- T²: values against `scipy.spatial.distance.mahalanobis`; Phase I and II limits
  by Monte Carlo simulation.
- Generalized variance: constants b1 and b2 by simulation of covariance matrices.
- MEWMA: the limit for p=2, λ=0.1, ARL=200 gives 8.63 (published: 8.64, Prabhu and Runger 1997).
- G and T: quantiles against `scipy.stats`, and Weibull maximum likelihood through
  its score equation.

> **Note:** pccpy follows the formulas and conventions that Minitab documents, but
> it has not been compared run by run against the Minitab software for lack of a
> license. If you find a difference, open an
> [issue](https://github.com/LeoSanta15/pccpy/issues).

---

## Development

```bash
git clone https://github.com/LeoSanta15/pccpy.git
cd pccpy
pip install -e ".[dev]"

pytest --cov=pccpy          # tests + coverage
ruff check src/              # style and common errors
mypy src/pccpy               # type checking
```

To build the documentation locally (Spanish and English):

```bash
pip install -e ".[docs]"
sphinx-build -b html docs/source docs/build
# Open docs/build/index.html
```

See [`CHANGELOG.md`](https://github.com/LeoSanta15/pccpy/blob/main/CHANGELOG.md) for the version history and
[`CONTRIBUTING.md`](https://github.com/LeoSanta15/pccpy/blob/main/CONTRIBUTING.md) for the contribution guidelines.

---

## License

MIT — see [LICENSE](https://github.com/LeoSanta15/pccpy/blob/main/LICENSE).
