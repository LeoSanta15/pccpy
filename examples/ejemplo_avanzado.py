"""Cartas avanzadas y multivariadas de spyc. Las figuras se guardan en ./salida."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import spyc

salida = Path("salida")
salida.mkdir(exist_ok=True)
rng = np.random.default_rng(2026)

# 1) Corridas cortas: tres partes con medias y variaciones distintas en una sola carta
partes = ["A"] * 12 + ["B"] * 10 + ["A"] * 12 + ["C"] * 8
medias = {"A": (50, 1.0), "B": (80, 2.0), "C": (20, 0.5)}
x = np.array([rng.normal(*medias[p]) for p in partes])
x[15] += 10                                    # una pieza B fuera de lo normal
# medias y sigmas históricas por parte (con solo 10 datos, un valor atípico inflaría la sigma estimada)
zmr = spyc.zmr_chart(x, partes, mu={p: m for p, (m, _) in medias.items()},
                     sigma={p: s for p, (_, s) in medias.items()}, tests=(1, 2, 3, 4, 5, 6))
print(zmr.summary(), "\n")
zmr.plot().savefig(salida / "zmr.png")

# 2) Variación entre y dentro de subgrupos: Xbar-R alarma de más, I-MR-R no
lotes = rng.normal(20, 1, (30, 5)) + rng.normal(0, 2, (30, 1))
print("Xbar-R  puntos marcados:", len(spyc.xbar_r_chart(lotes).violations()))
ch = spyc.imr_rs_chart(lotes)
print("I-MR-R  puntos marcados:", len(ch.violations()))
print({k: round(v, 3) for k, v in ch.params[0].items()}, "\n")
ch.plot().savefig(salida / "imr_r.png")

# 3) Eventos raros
entre = rng.geometric(0.01, 40) - 1
entre[25] = 600
spyc.g_chart(entre).plot().savefig(salida / "g.png")
tiempos = rng.weibull(1.4, 40) * 30
tiempos[12] = 250
print(spyc.t_chart(tiempos).summary(), "\n")

# 3b) Carta de zona: puntaje acumulado en lugar de pruebas de causas especiales
deriva = rng.normal(0, 1, 50)
deriva[30:] += 1.2                             # desplazamiento sostenido de 1.2 sigmas
zona = spyc.zone_chart(deriva, mu=0.0, sigma=1.0, reset=True)
print(zona.summary(), "\n")
zona.plot(zones=True).savefig(salida / "zona.png")

# 4) Multivariadas: Fase I con el histórico y Fase II con datos nuevos
Sigma = [[1, .6, .3], [.6, 1, .2], [.3, .2, 1]]
hist = rng.multivariate_normal([0, 0, 0], Sigma, 100)
nuevos = rng.multivariate_normal([0, 0, 0], Sigma, 50)
nuevos[30:, 2] += 4                            # la variable 3 se desplaza
print(spyc.t2_chart(hist).summary(), "\n")
mu, cov = hist.mean(axis=0), np.cov(hist, rowvar=False)
t2 = spyc.t2_chart(nuevos, mu=mu, cov=cov, n_hist=100)
print(t2.summary().splitlines()[0:3])
primero = int(t2["T2"].flagged[0]) + 1
print(f"Contribuciones en el punto {primero}:\n{t2.contributions(primero).round(2)}\n")
t2.plot().savefig(salida / "t2.png")
me = spyc.mewma_chart(nuevos, mu=mu, cov=cov)
print("MEWMA primera señal en el punto", int(me["MEWMA"].flagged[0]) + 1)
me.plot().savefig(salida / "mewma.png")
mc = spyc.mcusum_chart(nuevos, mu=mu, cov=cov)
print("MCUSUM primera señal en el punto", int(mc["MCUSUM"].flagged[0]) + 1, f"(h = {mc.params[0]['LCS']:.2f})")
mc.plot().savefig(salida / "mcusum.png")
subs = rng.multivariate_normal([0, 0, 0], Sigma, 120)
subs[60:] *= 2.5                               # aumenta la dispersión
spyc.generalized_variance_chart(subs, subgroup_size=6).plot().savefig(salida / "gv.png")
print("Figuras en", salida.resolve())
