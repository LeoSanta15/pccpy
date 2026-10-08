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
3. [Variables charts](#variables-charts)
   - [I-MR](#i-mr-chart)
   - [Xbar-R and Xbar-S](#xbar-r-and-xbar-s-charts)
   - [Data input formats](#data-input-formats)
   - [Historical parameters and stages](#historical-parameters-and-stages)
   - [Iterative Phase I](#iterative-phase-i)
   - [Dates on the x axis](#dates-on-the-x-axis)
4. [Attribute charts](#attribute-charts)
5. [Time-weighted charts](#time-weighted-charts)
   - [EWMA](#ewma)
   - [CUSUM](#cusum)
   - [Moving average](#moving-average)
6. [Advanced charts](#advanced-charts)
   - [Z-MR (short runs)](#z-mr-short-runs)
   - [I-MR-R/S (between/within variation)](#i-mr-rs-betweenwithin-variation)
   - [Rare events (G and T)](#rare-events-g-and-t)
7. [Multivariate charts](#multivariate-charts)
   - [Hotelling's T²](#hotellings-t²)
   - [Generalized variance](#generalized-variance)
   - [MEWMA](#mewma)
   - [MCUSUM](#mcusum)
   - [Stages and Box-Cox in multivariate charts](#stages-and-box-cox-in-multivariate-charts)
8. [Special-cause tests](#special-cause-tests)
9. [Chart plotting](#chart-plotting)
10. [Process capability](#process-capability)
11. [Normality, Pareto and SPC constants](#normality-pareto-and-spc-constants)
12. [Run chart and pre-control](#run-chart-and-pre-control)
13. [EWMA and CUSUM for attributes](#ewma-and-cusum-for-attributes)
14. [Tolerance intervals](#tolerance-intervals)
15. [Acceptance sampling](#acceptance-sampling)
16. [MSA / Gage R&R](#msa--gage-rr)
17. [Accessing the result data](#accessing-the-result-data)
18. [Validation](#validation)
19. [Development](#development)
20. [License](#license)

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
chart.params[0]     # {'stage': 'Before', 'media': ..., 'sigma': ..., ...}
chart.params[1]     # {'stage': 'After', 'media': ..., 'sigma': ..., ...}

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
phase1.chart.plot()        # chart with the final limits

chart_ii = phase1.phase2(x_new, tests=(1, 2))   # Phase II with the Phase I limits
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

**Guide for choosing λ:**

| λ | Detects best | Memory |
|---|--------------|--------|
| 0.05 – 0.10 | very small shifts (¼σ) | long |
| 0.20 | moderate shifts (½σ – 1σ) | moderate (Minitab recommended) |
| 0.40+ | similar to a Shewhart chart | short |

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
    # With H=4, K=0.5 the in-control ARL is ≈370 (industry standard)
)
```

> **Rule of thumb:** `H = 4σ` and `K = 0.5σ` balance the detection of a 1σ shift
> with an out-of-control ARL ≈ 10 and an in-control ARL ≈ 370.

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
# {'sigma_dentro': 0.97, 'sigma_entre': 1.48, 'sigma_entre_dentro': 1.79, ...}
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

# T: time between events (Weibull or exponential distribution)
times = rng.weibull(1.5, 40) * 30
pp.t_chart(times)          # Weibull (default)
pp.t_chart(times, distribution="exponential")  # exponential
```

The limits of the G chart are based on exact percentiles of the geometric
distribution; those of the T chart on the Weibull or exponential distribution fitted by
maximum likelihood.

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
- **Basic (1-4):** MR, R, S, G, T charts, attributes (P, NP, C, U, Laney)
- **Test 1 only:** EWMA, CUSUM, MA, T², MEWMA, MCUSUM

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

# Xbar-R method (classic AIAG)
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
chart.params[0]     # {'stage': 1, 'media': 10.2, 'sigma': 0.31, 'MR_prom': 0.35, 'n': 30}

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
