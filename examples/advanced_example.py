"""Advanced and multivariate charts of pccpy. The figures are saved in ./output.

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

# 1) Short runs: three parts with different means and variations on a single chart
parts = ["A"] * 12 + ["B"] * 10 + ["A"] * 12 + ["C"] * 8
means = {"A": (50, 1.0), "B": (80, 2.0), "C": (20, 0.5)}
x = np.array([rng.normal(*means[p]) for p in parts])
x[15] += 10                                    # one B part out of the ordinary
# historical means and sigmas per part (with only 10 data, an outlier would inflate the estimated sigma)
zmr = pccpy.zmr_chart(x, parts, mu={p: m for p, (m, _) in means.items()},
                      sigma={p: s for p, (_, s) in means.items()}, tests=(1, 2, 3, 4, 5, 6))
print(zmr.summary(), "\n")
zmr.plot().savefig(output / "zmr.png")

# 2) Variation between and within subgroups: Xbar-R over-alarms, I-MR-R does not
lots = rng.normal(20, 1, (30, 5)) + rng.normal(0, 2, (30, 1))
print(len(pccpy.xbar_r_chart(lots).violations()))   # flagged points of Xbar-R
ch = pccpy.imr_rs_chart(lots)
print(len(ch.violations()), "\n")                   # flagged points of I-MR-R
ch.plot().savefig(output / "imr_r.png")

# 3) Rare events
between = rng.geometric(0.01, 40) - 1
between[25] = 600
pccpy.g_chart(between).plot().savefig(output / "g.png")
times = rng.weibull(1.4, 40) * 30
times[12] = 250
print(pccpy.t_chart(times).summary(), "\n")

# 3b) Zone chart: cumulative score instead of special-cause tests
drift = rng.normal(0, 1, 50)
drift[30:] += 1.2                              # sustained shift of 1.2 sigma
zone = pccpy.zone_chart(drift, mu=0.0, sigma=1.0, reset=True)
print(zone.summary(), "\n")
zone.plot(zones=True).savefig(output / "zona.png")

# 4) Multivariate: Phase I with the history and Phase II with new data
Sigma = [[1, .6, .3], [.6, 1, .2], [.3, .2, 1]]
hist = rng.multivariate_normal([0, 0, 0], Sigma, 100)
new = rng.multivariate_normal([0, 0, 0], Sigma, 50)
new[30:, 2] += 4                               # variable 3 shifts
print(pccpy.t2_chart(hist).summary(), "\n")
mu, cov = hist.mean(axis=0), np.cov(hist, rowvar=False)
t2 = pccpy.t2_chart(new, mu=mu, cov=cov, n_hist=100)
print(t2.summary().splitlines()[0:3])
first = int(t2["T2"].flagged[0]) + 1
print(t2.contributions(first).round(2), "\n")
t2.plot().savefig(output / "t2.png")
me = pccpy.mewma_chart(new, mu=mu, cov=cov)
print(int(me["MEWMA"].flagged[0]) + 1)         # first MEWMA signal
me.plot().savefig(output / "mewma.png")
mc = pccpy.mcusum_chart(new, mu=mu, cov=cov)
print(int(mc["MCUSUM"].flagged[0]) + 1, round(mc.params[0]["LCS"], 2), "\n")   # first MCUSUM signal and its limit
mc.plot().savefig(output / "mcusum.png")

# 4b) Stages: two periods with different means, each one re-estimates its own limits
two_stages = np.vstack([new[:40], new[:40] + [0, 0, 3]])
labels = [1] * 40 + [2] * 40
t2_st = pccpy.t2_chart(two_stages, stages=labels)
print(t2_st.stage_mean[1].round(2), t2_st.stage_mean[2].round(2), "\n")

# 4c) Multivariate Box-Cox (positive, skewed data)
skewed = rng.lognormal(0, 0.4, (60, 3))
t2_bc = pccpy.t2_chart(skewed, boxcox=True)
print(t2_bc.params[0]["lambda_boxcox"], "\n")
subs = rng.multivariate_normal([0, 0, 0], Sigma, 120)
subs[60:] *= 2.5                               # dispersion grows
pccpy.generalized_variance_chart(subs, subgroup_size=6).plot().savefig(output / "gv.png")
