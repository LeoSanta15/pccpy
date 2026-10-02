# Tutorial: de Excel a carta de control

Este tutorial muestra el flujo completo de trabajo con datos reales: leer un
archivo CSV, diagnosticar el proceso, hacer la carta de control y exportar los
resultados, todo con pccpy.

Puedes descargar el archivo de datos de ejemplo: {download}`diametros_moldeo.csv <_static/diametros_moldeo.csv>`

---

## El escenario

Una planta de moldeo por inyección mide el diámetro (mm) de una pieza en 4
cavidades por lote durante 30 lotes consecutivos (120 mediciones en total). Las
especificaciones son LSL = 49.75 mm, USL = 50.25 mm, objetivo = 50.00 mm.

Se sospecha que el proceso se desplazó a partir del lote 21.

---

## Paso 1 — Leer los datos

```python
import pandas as pd
import numpy as np
import pccpy as pp

df = pd.read_csv("diametros_moldeo.csv", parse_dates=["fecha"])
print(df.head(8))
print(f"\nRegistros: {len(df)}  •  Lotes: {df['lote'].nunique()}")
```

```
        fecha  lote  cavidad operador  diametro_mm
0  2024-01-02     1        1        A      50.0244
1  2024-01-03     1        2        B      49.9168
2  2024-01-04     1        3        C      50.0600
3  2024-01-05     1        4        D      50.0752
...
Registros: 120  •  Lotes: 30
```

---

## Paso 2 — Diagnóstico rápido

Antes de elegir la carta, deja que `diagnose()` evalúe los datos:

```python
x = df["diametro_mm"].values

d = pp.diagnose(x, lsl=49.75, usl=50.25)
print(d.summary())
d.plot()
```

```
════════════════════════════════════════════════════════════
  DIAGNÓSTICO RÁPIDO DEL PROCESO
════════════════════════════════════════════════════════════
  N               : 120
  Media           : 50.0352
  Desv. estándar  : 0.0778
  CV              : 0.16 %
  Mínimo / Máximo : 49.8105  /  50.2489
  Asimetría       : 0.2441
  Curtosis        : -0.1823

  ── Normalidad ──
  Distribución    : Normal (p > 0.05)

  ── Alertas ──
  ⚠  Se detectó tendencia creciente. Verifica causas asignables.
  ⚠  Cp = 1.07 < 1.33: el proceso no supera el estándar automotriz.

  ── Análisis recomendado ──
  Función : run_chart → capability_analysis
════════════════════════════════════════════════════════════
```

El diagnóstico detecta la tendencia. Pasamos a la carta por subgrupos porque
tenemos 4 mediciones por lote.

---

## Paso 3 — Carta Xbar-R por subgrupos

Los datos están en formato largo (una medición por fila). pccpy acepta este
formato directamente:

```python
carta = pp.xbar_r_chart(
    df,
    subgroup="lote",
    value="diametro_mm",
    tests=(1, 2, 3, 4, 5, 6, 7, 8),
)
carta.plot()
```

También puedes convertir a matriz 2-D:

```python
g = df.pivot_table(index="lote", columns="cavidad", values="diametro_mm").values
carta = pp.xbar_r_chart(g, tests="all")
```

Ver las señales detectadas:

```python
print(carta.summary())
v = carta.violations()
print(v[["panel", "punto", "prueba", "descripcion"]])
```

Guardar el gráfico:

```python
carta.save_plot("carta_xbar_r.png", dpi=200)
carta.save_plot("carta_xbar_r.pdf")      # vectorial para reportes
carta.to_excel("carta_xbar_r.xlsx")       # datos + violaciones
```

---

## Paso 4 — Análisis de capacidad

Una vez que verificamos el estado del proceso (idealmente en control), calculamos
los índices de capacidad:

```python
cap = pp.capability_analysis(x, lsl=49.75, usl=50.25, target=50.0)
print(cap.summary())
cap.plot()
cap.save_plot("capacidad.png")
cap.to_excel("capacidad.xlsx")
```

```
  Cp   : 1.07    Cpk  : 1.01
  Pp   : 1.07    Ppk  : 1.00
  Z.Bench : 3.02
  PPM total esperado: 2580
```

Para ver la carta y la capacidad juntas (Sixpack):

```python
fig, res, chart = pp.capability_sixpack(x, lsl=49.75, usl=50.25, target=50.0)
fig.savefig("sixpack.png", dpi=150, bbox_inches="tight")
print(res.summary())
```

---

## Paso 5 — Análisis de Fase I y Fase II

La señal detectada en el lote 21 sugiere un cambio de proceso. El flujo estándar
es calcular los límites con los datos "estables" (Fase I) y aplicarlos a los datos
nuevos (Fase II):

```python
# Fase I: lotes 1-20 (primeras 80 observaciones)
x_fase1 = df.loc[df["lote"] <= 20, "diametro_mm"].values
g_fase1 = x_fase1.reshape(-1, 4)

carta_fase1 = pp.xbar_r_chart(g_fase1, tests="all")
params = carta_fase1.params[0]  # parámetros de la etapa 1

# Extraer mu y sigma estimados
mu_est      = params["mu"]
sigma_est   = params["sigma"]
print(f"Fase I:  μ = {mu_est:.4f},  σ = {sigma_est:.4f}")

# Fase II: aplicar esos límites a los lotes 21-30
g_fase2 = df.loc[df["lote"] > 20, "diametro_mm"].values.reshape(-1, 4)

carta_fase2 = pp.xbar_r_chart(
    g_fase2,
    mu=mu_est,
    sigma_within=sigma_est,
    tests=(1, 2),
)
carta_fase2.plot()
carta_fase2.save_plot("carta_fase2.png")
```

> Los parámetros `mu` y `sigma_within` fijan los límites de control usando las
> estimaciones de Fase I, en lugar de recalcularlos con los datos de Fase II.

---

## Paso 6 — Intervalo de tolerancia

¿Qué rango cubre el 99 % de la producción con 95 % de confianza?

```python
tol = pp.tolerance_interval(x_fase1, coverage=0.99, confidence=0.95)
print(tol.summary())
tol.plot()
tol.save_plot("tolerancia.png")
tol.to_excel("tolerancia.xlsx")
```

```
Intervalo de tolerancia (normal, two)
  N=80  Cobertura≥99.0%  Confianza=95.0%
  LI = 49.698   LS = 50.352
```

---

## Paso 7 — Exportar todo a un solo Excel

```python
with pd.ExcelWriter("reporte_completo.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Datos", index=False)
    cap.to_frame().to_excel(writer, sheet_name="Capacidad")
    carta.violations().to_excel(writer, sheet_name="Violaciones", index=False)
    tol.to_frame().to_excel(writer, sheet_name="Tolerancia")
    d.to_frame().to_excel(writer, sheet_name="Diagnóstico")

print("Reporte exportado a reporte_completo.xlsx")
```

---

## Resumen del flujo

```
datos.csv / datos.xlsx
      ↓
pd.read_csv / pd.read_excel
      ↓
pp.diagnose()             → ¿hay tendencia o normalidad?
      ↓
pp.xbar_r_chart() / pp.imr_chart()   → detectar señales
      ↓
pp.capability_analysis()  → Cp, Cpk, PPM
      ↓
.save_plot()  .to_excel()  ExcelWriter → entregar resultados
```

---

## Ver también

- {doc}`guia_seleccion` — elegir la carta correcta
- {doc}`capacidad_indices` — interpretar Cp, Cpk, Pp, Ppk
- {doc}`inicio_rapido` — más ejemplos rápidos
- {doc}`minitab` — equivalencias con Minitab
