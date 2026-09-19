"""Recorrido rápido por spyc: cartas de control, capacidad y normalidad.

Ejecutar:  python examples/ejemplo_basico.py
Las figuras se guardan en la carpeta ./salida
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # quite esta línea si quiere ventanas interactivas

import numpy as np

import spyc

salida = Path("salida")
salida.mkdir(exist_ok=True)
rng = np.random.default_rng(2026)

# --- 1. Valores individuales (I-MR) con un desplazamiento del proceso -------------------
x = np.r_[rng.normal(100, 1.5, 40), rng.normal(103, 1.5, 20)]
chart = spyc.imr_chart(x, tests=[1, 2, 3, 4, 5, 6])
print(chart.summary())
print(chart.violations().head(), "\n")
chart.plot().savefig(salida / "imr.png", dpi=110)

# --- 2. Subgrupos: X-barra y R (una fila por subgrupo) ---------------------------------
subgrupos = rng.normal(50, 0.8, (25, 5))
xr = spyc.xbar_r_chart(subgrupos, tests="all")
print(xr.summary(), "\n")
xr.plot(zones=True).savefig(salida / "xbar_r.png", dpi=110)

# --- 3. Atributos: carta P con tamaño de muestra variable ------------------------------
n = rng.integers(150, 250, 30)
defectuosos = rng.binomial(n, 0.04)
spyc.p_chart(defectuosos, n, tests=[1, 2, 3, 4]).plot().savefig(salida / "p.png", dpi=110)

# --- 4. Capacidad del proceso -----------------------------------------------------------
datos = rng.normal(100.4, 1.5, 150)
cap = spyc.capability_analysis(datos, lsl=95, usl=105, target=100)
print(cap.summary(), "\n")
print("Cpk =", round(cap.cpk, 3), "| Ppk =", round(cap.ppk, 3), "\n")

# Sixpack de capacidad (como Minitab)
fig, _, _ = spyc.capability_sixpack(subgrupos, lsl=48, usl=52, target=50)
fig.savefig(salida / "sixpack.png", dpi=100)

# --- 5. Datos no normales: ajuste Weibull y Box-Cox ------------------------------------
w = rng.weibull(1.8, 200) * 3 + 0.5
print(spyc.normality_test(w))
print(spyc.capability_nonnormal(w, lsl=0.1, usl=12, distribution="weibull").summary(), "\n")
print(spyc.capability_boxcox(w, lsl=0.1, usl=12).summary(), "\n")

# --- 6. Pareto ---------------------------------------------------------------------------
tabla = spyc.pareto(["Rayón", "Abolladura", "Rayón", "Mancha", "Rayón", "Abolladura", "Otro"])
print(tabla)
spyc.plot_pareto(tabla).savefig(salida / "pareto.png", dpi=110)

print(f"\nFiguras guardadas en {salida.resolve()}")
