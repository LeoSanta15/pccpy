"""Pre-control (semáforo): zonas verde/amarillo/rojo y reglas de Shainin/Montgomery."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class PreControlResult:
    """Resultado de :func:`precontrol`.

    Atributos
    ---------
    values : np.ndarray
        Datos originales.
    lsl, usl : float
        Límites de especificación inferior y superior.
    center : float
        Centro de la tolerancia (objetivo o punto medio).
    green_lo, green_hi : float
        Fronteras de la zona verde (centro ± tolerancia/4).
    zones : list[str]
        Zona de cada observación: ``'G'`` verde, ``'Y-'`` amarilla baja,
        ``'Y+'`` amarilla alta, ``'R-'`` roja baja, ``'R+'`` roja alta.
    signals : list[tuple[int, str]]
        Índices y códigos de las señales detectadas.
    """

    values: np.ndarray = field(repr=False)
    lsl: float
    usl: float
    center: float
    green_lo: float
    green_hi: float
    zones: list[str]
    signals: list[tuple[int, str]]

    # ------------------------------------------------------------------ helpers
    @property
    def n_green(self) -> int:
        return sum(z == "G" for z in self.zones)

    @property
    def n_yellow(self) -> int:
        return sum(z.startswith("Y") for z in self.zones)

    @property
    def n_red(self) -> int:
        return sum(z.startswith("R") for z in self.zones)

    # ------------------------------------------------------------------ output
    _SIGNAL_LABELS: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    _LABELS: dict[str, str] = field(
        default_factory=lambda: {
            "red": "Punto rojo — detener y corregir",
            "two_yellow_same": "Dos amarillas consecutivas en el mismo lado — ajustar",
            "two_yellow_opp": "Dos amarillas consecutivas en lados opuestos — detener (problema de varianza)",
        },
        init=False, repr=False,
    )

    def to_frame(self) -> pd.DataFrame:
        """DataFrame con zona y señal para cada observación."""
        rows = []
        sig_idx = {i: code for i, code in self.signals}
        for i, (v, z) in enumerate(zip(self.values, self.zones)):
            rows.append({
                "observación": i + 1,
                "valor": v,
                "zona": z,
                "señal": sig_idx.get(i, ""),
            })
        return pd.DataFrame(rows).set_index("observación")

    def summary(self) -> str:
        L = [
            (
                f"Pre-control  N={len(self.values)}  LEI={self.lsl:.5g}  LES={self.usl:.5g}"
                f"  Centro={self.center:.5g}"
            ),
            f"  Zona verde: [{self.green_lo:.5g}, {self.green_hi:.5g}]",
            f"  Verde={self.n_green}  Amarillo={self.n_yellow}  Rojo={self.n_red}",
        ]
        if self.signals:
            L.append("  Señales:")
            for i, code in self.signals:
                label = {
                    "red": "Punto rojo — detener y corregir",
                    "two_yellow_same": "Dos amarillas consecutivas en el mismo lado — ajustar",
                    "two_yellow_opp": "Dos amarillas consecutivas en lados opuestos — varianza",
                }.get(code, code)
                L.append(f"    Obs {i + 1}: {label}")
        else:
            L.append("  Sin señales detectadas.")
        return "\n".join(L)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()

    def plot(self, **kwargs):
        """Gráfico de pre-control. Ver :func:`pccpy.plotting.plot_precontrol`."""
        from .plotting import plot_precontrol

        return plot_precontrol(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …)."""
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def precontrol(
    data,
    lsl: float,
    usl: float,
    target: float | None = None,
) -> PreControlResult:
    """Análisis de pre-control (semáforo de Shainin).

    Divide la tolerancia (LES − LEI) en tres zonas:

    * **Verde** — centro ± tolerancia/4 (la mitad central de la banda).
    * **Amarillo** — entre el borde verde y el límite de especificación.
    * **Rojo** — fuera de especificaciones.

    Señales detectadas
    ------------------
    * **red**: cualquier punto fuera de especificaciones.
    * **two_yellow_same**: dos amarillas consecutivas en el mismo lado (posible deriva).
    * **two_yellow_opp**: dos amarillas consecutivas en lados opuestos (posible
      aumento de varianza).

    Parameters
    ----------
    data : array-like
        Vector 1-D de observaciones individuales en orden de producción.
    lsl, usl : float
        Límites de especificación inferior y superior.
    target : float, opcional
        Valor objetivo (centro de la zona verde). Si no se indica, se usa el
        punto medio (lsl + usl) / 2.

    Returns
    -------
    PreControlResult
    """
    if lsl >= usl:
        raise ValueError("lsl debe ser menor que usl.")
    x = np.asarray(data, dtype=float).ravel()
    if x.size < 1:
        raise ValueError("Se necesita al menos una observación.")
    center = float(target) if target is not None else (lsl + usl) / 2.0
    tol = usl - lsl
    green_lo = center - tol / 4.0
    green_hi = center + tol / 4.0

    zones: list[str] = []
    for v in x:
        if v < lsl:
            zones.append("R-")
        elif v > usl:
            zones.append("R+")
        elif v < green_lo:
            zones.append("Y-")
        elif v > green_hi:
            zones.append("Y+")
        else:
            zones.append("G")

    signals: list[tuple[int, str]] = []
    for i, z in enumerate(zones):
        if z.startswith("R"):
            signals.append((i, "red"))
        if i > 0:
            prev = zones[i - 1]
            if prev.startswith("Y") and z.startswith("Y"):
                code = "two_yellow_same" if prev == z else "two_yellow_opp"
                signals.append((i, code))

    return PreControlResult(
        values=x, lsl=float(lsl), usl=float(usl), center=center,
        green_lo=green_lo, green_hi=green_hi,
        zones=zones, signals=signals,
    )
