"""Objetos de resultado de las cartas de control."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ._data import _excel_writer
from ._frames import etiquetas
from ._i18n import N_, tr
from .rules import DEFAULT_K, describe

# Claves estables (inglés) → texto de la columna en español, marcado para traducir.
_COLUMNAS_PANEL = {
    "point": N_("punto"), "stage": N_("etapa"), "value": N_("valor"), "cl": N_("LC"), "ucl": N_("LCS"),
    "lcl": N_("LCI"), "lower_value": N_("valor_inferior"), "failed_tests": N_("pruebas_fallidas"),
}
_COLUMNAS_VIOLACIONES = {
    "panel": N_("panel"), "point": N_("punto"), "test": N_("prueba"), "value": N_("valor"),
    "description": N_("descripcion"),
}
# Algunas cartas guardan parámetros con clave en español: son datos y no se traducen; solo se muestran traducidos.
_PARAMETROS = {
    "centro": N_("centro"), "distribución": N_("distribución"), "escala": N_("escala"), "forma": N_("forma"),
    "longitud": N_("longitud"), "media": N_("media"), "objetivo": N_("objetivo"), "peso": N_("peso"),
    "pesos": N_("pesos"), "reinicio": N_("reinicio"), "subgrupos": N_("subgrupos"), "tamaño": N_("tamaño"),
    "n_subgrupo": N_("n_subgrupo"), "MR_prom": N_("MR_prom"), "alfa": N_("alfa"), "corridas": N_("corridas"),
    "fase": N_("fase"), "método": N_("método"), "n_puntos": N_("n_puntos"), "partes": N_("partes"),
    "puntos": N_("puntos"), "sigma_conocida": N_("sigma_conocida"), "sigma_dentro": N_("sigma_dentro"),
    "sigma_entre": N_("sigma_entre"), "sigma_entre_dentro": N_("sigma_entre_dentro"), "variables": N_("variables"),
    "LCS": N_("LCS"),
}


def _nombre_parametro(clave) -> str:
    return tr(_PARAMETROS[clave]) if clave in _PARAMETROS else str(clave)


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
    violations: dict[int, np.ndarray] = field(default_factory=dict)
    secondary: np.ndarray | None = None  # 2ª serie (CUSUM inferior)
    symmetric: bool = True  # ¿tiene sentido dibujar zonas de 1 y 2 sigma?

    @property
    def flagged(self) -> np.ndarray:
        """Índices (base 0) de todos los puntos con alguna prueba fallida."""
        if not self.violations:
            return np.array([], dtype=int)
        return np.unique(np.concatenate(list(self.violations.values())).astype(int))

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla del panel: una fila por punto.

        Con ``stable=True`` las columnas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        col = etiquetas(_COLUMNAS_PANEL, stable)
        data = {
            col["point"]: np.arange(1, len(self.values) + 1),
            col["stage"]: self.stage,
            col["value"]: self.values,
            col["cl"]: self.center,
            col["ucl"]: self.ucl,
            col["lcl"]: self.lcl,
        }
        if self.secondary is not None:
            data[col["lower_value"]] = self.secondary
        df = pd.DataFrame(data)
        tests_at: dict[int, list[str]] = {}
        for t, idx in self.violations.items():
            for i in idx:
                tests_at.setdefault(int(i), []).append(str(t))
        df[col["failed_tests"]] = [
            ",".join(tests_at.get(i, [])) for i in range(len(self.values))
        ]
        return df


@dataclass
class ControlChart:
    """Resultado de una carta de control: paneles, parámetros por etapa y pruebas."""

    kind: str
    panels: list[Panel]
    params: list[dict]
    tests: tuple = ()
    test_params: dict[int, float] = field(default_factory=dict)
    test1_text: str | None = None  # plantilla (msgid) de la descripción propia de la prueba 1; se traduce al mostrarla
    test1_params: dict = field(default_factory=dict)  # valores de los marcadores de test1_text

    def __getitem__(self, name: str) -> Panel:
        for p in self.panels:
            if p.name == name:
                return p
        raise KeyError(tr(
            "No existe el panel {name!r}. Disponibles: {available}"
        ).format(name=name, available=[p.name for p in self.panels]))

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla ancha: una fila por punto, columnas por panel.

        Con ``stable=True`` las columnas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        col = etiquetas(_COLUMNAS_PANEL, stable)
        frames = []
        for p in self.panels:
            f = p.to_frame(stable=stable).drop(columns=[col["point"], col["stage"]]).add_prefix(f"{p.name}_")
            frames.append(f)
        base = pd.DataFrame(
            {col["point"]: np.arange(1, len(self.panels[0].values) + 1), col["stage"]: self.panels[0].stage}
        )
        return pd.concat([base] + frames, axis=1)

    def _violations(self) -> pd.DataFrame:
        """Puntos que fallan pruebas, con claves estables (``panel``, ``point``, ``test``, ``value``, ``description``)."""
        rows = []
        for p in self.panels:
            for t, idx in sorted(p.violations.items()):
                desc = (tr(self.test1_text).format(**self.test1_params) if t == 1 and self.test1_text
                        else describe(t, self.test_params.get(t, DEFAULT_K[t])))
                for i in idx:
                    rows.append(
                        {"panel": p.name, "point": int(i) + 1, "test": t,
                         "value": float(p.values[i]), "description": desc}
                    )
        cols = ["panel", "point", "test", "value", "description"]
        return pd.DataFrame(rows, columns=cols).sort_values(["panel", "point", "test"]).reset_index(drop=True)

    def violations(self, stable: bool = False) -> pd.DataFrame:
        """Tabla de puntos que fallan pruebas: panel, punto (base 1), prueba, valor y descripción.

        Con ``stable=True`` las columnas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        v = self._violations()
        return v if stable else v.rename(columns=etiquetas(_COLUMNAS_VIOLACIONES, False))

    @property
    def in_control(self) -> bool:
        """True si ninguna prueba solicitada falló en ningún panel."""
        return all(p.flagged.size == 0 for p in self.panels)

    def summary(self) -> str:
        lines = [tr("Carta de control {kind}").format(kind=self.kind)]
        for prm in self.params:
            head = tr("  Etapa {stage}").format(stage=prm["stage"]) if len(self.params) > 1 else tr("  Parámetros")
            body = ", ".join(
                f"{_nombre_parametro(k)}={v:.6g}" if isinstance(v, (float, np.floating)) else f"{_nombre_parametro(k)}={v}"
                for k, v in prm.items() if k != "stage"
            )
            lines.append(f"{head}: {body}")
        if not self.tests:
            lines.append(tr("  Pruebas de causas especiales: ninguna solicitada"))
        else:
            lines.append(tr("  Pruebas solicitadas: {tests}").format(tests=", ".join(map(str, self.tests))))
            v = self._violations()
            if v.empty:
                lines.append(tr("  Resultado: sin puntos fuera de control"))
            else:
                lines.append(tr("  Puntos marcados: {count}").format(count=len(v)))
                for _, r in v.iterrows():
                    lines.append(
                        tr("    [{panel}] punto {point}: prueba {test} (valor {value:.6g}) - {description}").format(
                            panel=r["panel"], point=r["point"], test=r["test"], value=r["value"],
                            description=r["description"])
                    )
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()

    def to_excel(self, path) -> None:
        """Exporta la carta a un archivo Excel (.xlsx).

        Requiere ``openpyxl`` (``pip install openpyxl``).
        Cada panel ocupa una hoja; las violaciones van en una hoja adicional.
        """
        with _excel_writer(path) as writer:
            for p in self.panels:
                p.to_frame().to_excel(writer, sheet_name=p.name[:31], index=False)
            v = self.violations()
            if not v.empty:
                v.to_excel(writer, sheet_name="Violaciones", index=False)

    def plot(self, **kwargs):
        """Dibuja la carta con matplotlib. Ver :func:`pccpy.plotting.plot_control_chart`."""
        from .plotting import plot_control_chart

        return plot_control_chart(self, **kwargs)

    def save_plot(self, path: str, *, dpi: int = 150, **kwargs) -> None:
        """Guarda el gráfico en un archivo (PNG, SVG, PDF, …).

        Parameters
        ----------
        path : str
            Ruta de destino, p. ej. ``"carta_imr.png"`` o ``"carta.pdf"``.
        dpi : int
            Resolución en puntos por pulgada (solo relevante para formatos
            de mapa de bits). Por defecto 150.
        **kwargs
            Argumentos adicionales para :meth:`plot`.
        """
        import matplotlib.pyplot as plt

        fig = self.plot(**kwargs)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)


@dataclass
class MultivariateChart(ControlChart):
    """Carta multivariada: agrega los datos necesarios para diagnosticar una señal."""

    variables: list[str] = field(default_factory=list)
    points: np.ndarray | None = None  # vector graficado en cada punto (m x p)
    mean: np.ndarray | None = None  # media usada (la de la 1ª etapa si hay varias)
    cov: np.ndarray | None = None  # covarianza usada (la de la 1ª etapa si hay varias)
    scale: float = 1.0  # tamaño de subgrupo n (T2 = n * d' S^-1 d)
    stage_mean: dict = field(default_factory=dict)  # media por etapa (T², con 'stages')
    stage_cov: dict = field(default_factory=dict)  # covarianza por etapa
    stage_scale: dict = field(default_factory=dict)  # tamaño de subgrupo por etapa

    def contributions(self, point: int) -> pd.Series:
        """Contribución de cada variable al T² de un punto (``point`` en base 1).

        Para cada variable j se calcula ``d_j = T² - T²_(-j)``, donde ``T²_(-j)`` es el
        T² del mismo punto sin la variable j (Runger, Alt y Montgomery, 1996). Un
        valor grande señala la variable que más aporta a la señal; las
        contribuciones no suman T². Si la carta se calculó con ``stages``, usa la
        media y la covarianza de la etapa a la que pertenece ese punto.
        """
        if self.points is None or self.kind != "T²":
            raise ValueError(tr("Las contribuciones solo están disponibles para la carta T²."))
        m = self.points.shape[0]
        if not 1 <= point <= m:
            raise ValueError(tr("'point' debe estar entre 1 y {m}.").format(m=m))
        label = self.panels[0].stage[point - 1]
        mean = self.stage_mean.get(label, self.mean)
        cov = self.stage_cov.get(label, self.cov)
        scale = self.stage_scale.get(label, self.scale)
        if mean is None or cov is None:
            raise ValueError(tr("La carta no tiene media/covarianza calculadas para este punto."))
        d = self.points[point - 1] - mean
        p = d.size
        t2 = scale * d @ np.linalg.solve(cov, d)
        out = np.empty(p)
        for j in range(p):
            keep = [i for i in range(p) if i != j]
            dj = d[keep]
            out[j] = t2 - scale * dj @ np.linalg.solve(cov[np.ix_(keep, keep)], dj)
        return pd.Series(out, index=self.variables, name=f"contribución (punto {point})")
