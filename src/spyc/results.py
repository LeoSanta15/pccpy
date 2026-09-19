"""Objetos de resultado de las cartas de control."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .rules import DEFAULT_K, describe


@dataclass
class Panel:
    """Un gráfico individual dentro de una carta (p. ej. el gráfico I o el MR)."""

    name: str
    values: np.ndarray
    center: np.ndarray
    ucl: np.ndarray
    lcl: np.ndarray
    sigma: np.ndarray
    stage: np.ndarray
    ylabel: str = ""
    violations: Dict[int, np.ndarray] = field(default_factory=dict)
    secondary: Optional[np.ndarray] = None  # 2ª serie (CUSUM inferior)
    symmetric: bool = True  # ¿tiene sentido dibujar zonas de 1 y 2 sigma?

    @property
    def flagged(self) -> np.ndarray:
        """Índices (base 0) de todos los puntos con alguna prueba fallida."""
        if not self.violations:
            return np.array([], dtype=int)
        return np.unique(np.concatenate(list(self.violations.values())).astype(int))

    def to_frame(self) -> pd.DataFrame:
        data = {
            "punto": np.arange(1, len(self.values) + 1),
            "etapa": self.stage,
            "valor": self.values,
            "LC": self.center,
            "LCS": self.ucl,
            "LCI": self.lcl,
        }
        if self.secondary is not None:
            data["valor_inferior"] = self.secondary
        df = pd.DataFrame(data)
        tests_at: Dict[int, List[str]] = {}
        for t, idx in self.violations.items():
            for i in idx:
                tests_at.setdefault(int(i), []).append(str(t))
        df["pruebas_fallidas"] = [
            ",".join(tests_at.get(i, [])) for i in range(len(self.values))
        ]
        return df


@dataclass
class ControlChart:
    """Resultado de una carta de control: paneles, parámetros por etapa y pruebas."""

    kind: str
    panels: List[Panel]
    params: List[dict]
    tests: tuple = ()
    test_params: Dict[int, float] = field(default_factory=dict)

    def __getitem__(self, name: str) -> Panel:
        for p in self.panels:
            if p.name == name:
                return p
        raise KeyError(f"No existe el panel {name!r}. Disponibles: {[p.name for p in self.panels]}")

    def to_frame(self) -> pd.DataFrame:
        """Tabla ancha: una fila por punto, columnas por panel."""
        frames = []
        for p in self.panels:
            f = p.to_frame().drop(columns=["punto", "etapa"]).add_prefix(f"{p.name}_")
            frames.append(f)
        base = pd.DataFrame(
            {"punto": np.arange(1, len(self.panels[0].values) + 1), "etapa": self.panels[0].stage}
        )
        return pd.concat([base] + frames, axis=1)

    def violations(self) -> pd.DataFrame:
        """Tabla de puntos que fallan pruebas: panel, punto (base 1), prueba, valor."""
        rows = []
        for p in self.panels:
            for t, idx in sorted(p.violations.items()):
                desc = describe(t, self.test_params.get(t, DEFAULT_K[t]))
                for i in idx:
                    rows.append(
                        {"panel": p.name, "punto": int(i) + 1, "prueba": t,
                         "valor": float(p.values[i]), "descripcion": desc}
                    )
        cols = ["panel", "punto", "prueba", "valor", "descripcion"]
        return pd.DataFrame(rows, columns=cols).sort_values(["panel", "punto", "prueba"]).reset_index(drop=True)

    @property
    def in_control(self) -> bool:
        """True si ninguna prueba solicitada falló en ningún panel."""
        return all(p.flagged.size == 0 for p in self.panels)

    def summary(self) -> str:
        lines = [f"Carta de control {self.kind}"]
        for prm in self.params:
            head = f"  Etapa {prm['stage']}" if len(self.params) > 1 else "  Parámetros"
            body = ", ".join(
                f"{k}={v:.6g}" if isinstance(v, (float, np.floating)) else f"{k}={v}"
                for k, v in prm.items() if k != "stage"
            )
            lines.append(f"{head}: {body}")
        if not self.tests:
            lines.append("  Pruebas de causas especiales: ninguna solicitada")
        else:
            lines.append(f"  Pruebas solicitadas: {', '.join(map(str, self.tests))}")
            v = self.violations()
            if v.empty:
                lines.append("  Resultado: sin puntos fuera de control")
            else:
                lines.append(f"  Puntos marcados: {len(v)}")
                for _, r in v.iterrows():
                    lines.append(
                        f"    [{r['panel']}] punto {r['punto']}: prueba {r['prueba']} "
                        f"(valor {r['valor']:.6g}) - {r['descripcion']}"
                    )
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()

    def plot(self, **kwargs):
        """Dibuja la carta con matplotlib. Ver :func:`spyc.plotting.plot_control_chart`."""
        from .plotting import plot_control_chart

        return plot_control_chart(self, **kwargs)
