"""Benchmarks de rendimiento para las principales funciones de pccpy.

Ejecutar con:
    python benchmarks/bench_charts.py

Para una comparación más precisa con timeit:
    python -m timeit -s "import benchmarks.bench_charts as b" "b.bench_imr()"
"""
from __future__ import annotations

import time
from typing import Callable

import numpy as np

import pccpy

RNG = np.random.default_rng(0)

# Datos de prueba
X_80   = RNG.normal(100, 2, 80)
X_500  = RNG.normal(100, 2, 500)
X_5000 = RNG.normal(100, 2, 5000)
G_25x4  = RNG.normal(100, 2, (25, 4))
G_100x5 = RNG.normal(100, 2, (100, 5))
MV_100  = RNG.normal(0, 1, (100, 4))
MV_500  = RNG.normal(0, 1, (500, 4))


# ── helpers ──────────────────────────────────────────────────────────────────

def _bench(label: str, fn: Callable, n: int = 10) -> float:
    """Ejecuta `fn` `n` veces y devuelve el tiempo promedio en milisegundos."""
    # warm-up
    fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    elapsed = (time.perf_counter() - t0) / n * 1000
    print(f"  {label:<45s} {elapsed:8.2f} ms")
    return elapsed


# ── benchmarks individuales (llamables desde timeit) ─────────────────────────

def bench_imr():
    pccpy.imr_chart(X_500, tests="all")

def bench_imr_large():
    pccpy.imr_chart(X_5000, tests="all")

def bench_xbar_r():
    pccpy.xbar_r_chart(G_100x5, tests="all")

def bench_ewma():
    pccpy.ewma_chart(X_500)

def bench_cusum():
    pccpy.cusum_chart(X_500)

def bench_zone():
    pccpy.zone_chart(X_500)

def bench_ma():
    pccpy.ma_chart(X_500)

def bench_capability():
    pccpy.capability_analysis(X_500, 94, 106, 100)

def bench_capability_boxcox():
    pccpy.capability_boxcox(X_500, 94, 106)

def bench_capability_sixpack():
    import matplotlib.pyplot as plt
    pccpy.capability_sixpack(X_500, 94, 106, 100)
    plt.close("all")

def bench_diagnose():
    pccpy.diagnose(X_500, lsl=94, usl=106)

def bench_tolerance():
    pccpy.tolerance_interval(X_500)

def bench_tolerance_nonparam():
    pccpy.tolerance_interval(X_500, method="nonparametric")

def bench_t2():
    pccpy.t2_chart(MV_100)

def bench_mewma():
    pccpy.mewma_chart(MV_100)

def bench_t2_large():
    pccpy.t2_chart(MV_500)

def bench_mewma_large():
    pccpy.mewma_chart(MV_500)

def bench_gage_rr():
    data = RNG.normal(0, 1, (10, 3, 2))
    pccpy.gage_rr(data, parts=10, operators=3, replicates=2)

def bench_acceptance_attributes():
    pccpy.acceptance_sampling_attributes(5000, 1.0)

def bench_acceptance_variables():
    pccpy.acceptance_sampling_variables(1000, 1.0)


# ── suite completa ────────────────────────────────────────────────────────────

def run_all(n: int = 20) -> None:
    print("=" * 62)
    print("  pccpy — benchmarks de rendimiento")
    print("=" * 62)

    print("\n── Cartas de variables (univariadas) ─────────────────────")
    _bench("imr_chart (n=500, tests=all)",      bench_imr,       n)
    _bench("imr_chart (n=5000, tests=all)",     bench_imr_large, n)
    _bench("xbar_r_chart (100×5, tests=all)",   bench_xbar_r,    n)
    _bench("ewma_chart (n=500)",                bench_ewma,      n)
    _bench("cusum_chart (n=500)",               bench_cusum,     n)
    _bench("zone_chart (n=500)",                bench_zone,      n)
    _bench("ma_chart (n=500)",                  bench_ma,        n)

    print("\n── Capacidad del proceso ──────────────────────────────────")
    _bench("capability_analysis (n=500)",        bench_capability,        n)
    _bench("capability_boxcox (n=500)",          bench_capability_boxcox, n)
    _bench("capability_sixpack (n=500)",         bench_capability_sixpack, n)

    print("\n── Diagnóstico y tolerancia ───────────────────────────────")
    _bench("diagnose (n=500, lsl+usl)",          bench_diagnose,              n)
    _bench("tolerance_interval normal (n=500)",  bench_tolerance,             n)
    _bench("tolerance_interval nonparam (n=500)", bench_tolerance_nonparam,   n)

    print("\n── Cartas multivariadas ───────────────────────────────────")
    _bench("t2_chart (100×4)",                   bench_t2,          n)
    _bench("mewma_chart (100×4)",                bench_mewma,       n)
    _bench("t2_chart (500×4)",                   bench_t2_large,    n)
    _bench("mewma_chart (500×4)",                bench_mewma_large, n)

    print("\n── MSA y muestreo ─────────────────────────────────────────")
    _bench("gage_rr (10×3×2, ANOVA)",            bench_gage_rr,                n)
    _bench("acceptance_sampling_attributes",      bench_acceptance_attributes,  n)
    _bench("acceptance_sampling_variables",       bench_acceptance_variables,   n)

    print("=" * 62)


if __name__ == "__main__":
    run_all()
