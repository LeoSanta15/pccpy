"""Quick tour of pccpy: control charts, capability and normality.

Run:  python examples/basic_example.py
The figures are saved in ./output. Messages, tables and plots follow the pccpy language
(``pccpy.set_language("en")`` or the PCCPY_LANG environment variable); the code is the same in every language.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # remove this line to get interactive windows

import numpy as np

import pccpy

output = Path("output")
output.mkdir(exist_ok=True)
rng = np.random.default_rng(2026)

# --- 1. Individual values (I-MR) with a process shift ----------------------------------
x = np.r_[rng.normal(100, 1.5, 40), rng.normal(103, 1.5, 20)]
chart = pccpy.imr_chart(x, tests=[1, 2, 3, 4, 5, 6])
print(chart.summary())
print(chart.violations().head(), "\n")
chart.plot().savefig(output / "imr.png", dpi=110)

# --- 2. Subgroups: Xbar and R (one row per subgroup) -----------------------------------
subgroups = rng.normal(50, 0.8, (25, 5))
xr = pccpy.xbar_r_chart(subgroups, tests="all")
print(xr.summary(), "\n")
xr.plot(zones=True).savefig(output / "xbar_r.png", dpi=110)

# --- 3. Attributes: P chart with variable sample size ----------------------------------
n = rng.integers(150, 250, 30)
defectives = rng.binomial(n, 0.04)
pccpy.p_chart(defectives, n, tests=[1, 2, 3, 4]).plot().savefig(output / "p.png", dpi=110)

# --- 4. Process capability -------------------------------------------------------------
data = rng.normal(100.4, 1.5, 150)
cap = pccpy.capability_analysis(data, lsl=95, usl=105, target=100)
print(cap.summary(), "\n")
print(round(cap.cpk, 3), round(cap.ppk, 3), "\n")

# Capability sixpack (as in Minitab)
fig, _, _ = pccpy.capability_sixpack(subgroups, lsl=48, usl=52, target=50)
fig.savefig(output / "sixpack.png", dpi=100)

# --- 5. Non-normal data: Weibull fit and Box-Cox ---------------------------------------
w = rng.weibull(1.8, 200) * 3 + 0.5
print(pccpy.normality_test(w))
print(pccpy.capability_nonnormal(w, lsl=0.1, usl=12, distribution="weibull").summary(), "\n")
print(pccpy.capability_boxcox(w, lsl=0.1, usl=12).summary(), "\n")

# --- 6. Pareto -------------------------------------------------------------------------
counts = pccpy.pareto(["Scratch", "Dent", "Scratch", "Stain", "Scratch", "Dent", "Other"])
print(counts)
pccpy.plot_pareto(counts).savefig(output / "pareto.png", dpi=110)
