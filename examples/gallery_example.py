"""Gallery of the remaining charts and plots of pccpy. The figures are saved in ./output.

Messages, tables and plots follow the pccpy language (``pccpy.set_language("en")`` or PCCPY_LANG).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pccpy

output = Path("output")
output.mkdir(exist_ok=True)
rng = np.random.default_rng(2026)

# 1) Subgroups with many observations: Xbar-S
subgroups = rng.normal(20, 0.5, (24, 10))
pccpy.xbar_s_chart(subgroups).plot().savefig(output / "xbar_s.png", dpi=110)

# 2) Attributes: C chart and Laney P' (overdispersed proportions)
pccpy.c_chart(rng.poisson(4, 30)).plot().savefig(output / "c.png", dpi=110)
n = rng.integers(800, 1200, 30)
p_true = np.clip(rng.normal(0.05, 0.012, 30), 0.001, None)
pccpy.laney_p_chart(rng.binomial(n, p_true), n).plot().savefig(output / "laney_p.png", dpi=110)

# 3) Time-weighted charts: EWMA, CUSUM and moving average on a small shift (historical target and sigma)
x = np.r_[rng.normal(10, 0.3, 30), rng.normal(10.35, 0.3, 20)]
pccpy.ewma_chart(x, weight=0.2, target=10, sigma=0.3).plot().savefig(output / "ewma.png", dpi=110)
pccpy.cusum_chart(x, target=10, sigma=0.3).plot().savefig(output / "cusum.png", dpi=110)
pccpy.ma_chart(x, length=5).plot().savefig(output / "ma.png", dpi=110)

# 4) Time between events: T chart
pccpy.t_chart(rng.weibull(1.5, 40) * 30).plot().savefig(output / "t.png", dpi=110)

# 5) Capability: normal, non-normal (Weibull) and Box-Cox
data = rng.normal(100.4, 1.5, 150)
pccpy.capability_analysis(data, lsl=95, usl=105, target=100).plot().savefig(output / "capability.png", dpi=110)
w = rng.weibull(1.8, 200) * 3 + 0.5
pccpy.capability_nonnormal(w, lsl=0.1, usl=12, distribution="weibull").plot().savefig(
    output / "capability_nonnormal.png", dpi=110)
pccpy.capability_boxcox(w, lsl=0.1, usl=12).plot().savefig(output / "capability_boxcox.png", dpi=110)

# 6) Capability for attributes (binomial)
n = rng.integers(180, 220, 25)
pccpy.capability_binomial(rng.binomial(n, 0.03), n=n).plot().savefig(output / "capability_binomial.png", dpi=110)

# 7) Subgroup medians: median-R chart on skewed data (drawn last so the figures above keep their data)
pccpy.median_r_chart(rng.lognormal(1.0, 0.4, (25, 5))).plot().savefig(output / "median_r.png", dpi=110)
