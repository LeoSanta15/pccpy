"""Pruebas formales de valores atípicos: Grubbs (uno) y ESD generalizada de Rosner (varios).

Ambas suponen que los datos *sin* los atípicos vienen de una distribución normal. No son una regla para eliminar datos:
señalan puntos que no encajan con esa normal. En datos de proceso ordenados en el tiempo, las cartas de control y sus
pruebas de causas especiales son la herramienta adecuada.

* **Grubbs** (1969): ``G = max |xᵢ − x̄| / s`` frente a
  ``(n − 1)/√n · √(t² / (n − 2 + t²))`` con ``t`` = cuantil ``1 − α/(2n)`` de la t de Student con ``n − 2`` grados
  (``α/n`` si es unilateral). Contrasta un solo atípico; con dos atípicos del mismo lado puede enmascararse.
* **ESD generalizada** (Rosner, 1983): quita de uno en uno el punto más alejado hasta ``max_outliers`` veces, calcula
  ``Rᵢ`` y el valor crítico ``λᵢ`` y declara atípicos los ``k`` primeros, donde ``k`` es el mayor ``i`` con ``Rᵢ > λᵢ``.
  Evita el enmascaramiento; conviene con ``n ≥ 25``.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from ._frames import etiquetas
from ._i18n import N_, tr

METODOS = ("grubbs", "esd")
LADOS = ("two", "upper", "lower")
MAX_ATIPICOS_POR_DEFECTO = 10

_COLUMNAS = {"step": N_("paso"), "index": N_("índice"), "value": N_("valor"), "statistic": N_("estadístico"),
             "critical": N_("valor crítico"), "outlier": N_("atípico")}


def _critico(n: int, alpha: float, lados: str, metodo: str, paso: int = 1) -> float:
    """Valor crítico con ``n`` datos en la muestra actual (``paso`` = 1 en Grubbs; i-ésimo paso en ESD)."""
    k = n - 2  # grados de libertad de la t
    p = 1 - (alpha / (2 * n) if lados == "two" else alpha / n)
    t = float(stats.t.ppf(p, k))
    if metodo == "grubbs":
        return (n - 1) / np.sqrt(n) * np.sqrt(t * t / (k + t * t))
    return (n - 1) * t / np.sqrt((k + t * t) * n)  # λᵢ de Rosner con n = tamaño de la muestra restante


def _estadistico(x: np.ndarray, lados: str) -> tuple[int, float]:
    """Posición del punto más extremo y su estadístico, con la media y s de ``x``."""
    m, s = float(x.mean()), float(x.std(ddof=1))
    if lados == "two":
        d = np.abs(x - m)
    elif lados == "upper":
        d = x - m
    else:
        d = m - x
    j = int(np.argmax(d))
    return j, float(d[j] / s)


@dataclass
class OutlierTestResult:
    """Resultado de ``outlier_test``: pasos de la prueba y puntos declarados atípicos."""

    method: str
    alpha: float
    sides: str
    n: int
    steps: pd.DataFrame
    outlier_indices: np.ndarray
    outlier_values: np.ndarray
    normality_p: float = float("nan")  # Shapiro-Wilk de los datos sin los atípicos (nan si quedan menos de 3)
    dropped: int = 0  # valores no finitos ignorados
    data: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def has_outliers(self) -> bool:
        """``True`` si se declaró al menos un atípico."""
        return self.outlier_indices.size > 0

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Un paso por fila: índice (base 0 en los datos originales), valor, estadístico, crítico y si es atípico."""
        col = etiquetas(_COLUMNAS, stable)
        s = self.steps
        return pd.DataFrame({col["step"]: s["step"], col["index"]: s["index"], col["value"]: s["value"],
                             col["statistic"]: s["statistic"], col["critical"]: s["critical"],
                             col["outlier"]: s["outlier"]})

    def summary(self) -> str:
        nombre = tr("Grubbs") if self.method == "grubbs" else tr("ESD generalizada (Rosner)")
        lados = {"two": tr("bilateral"), "upper": tr("unilateral superior"), "lower": tr("unilateral inferior")}[self.sides]
        lines = [tr("Prueba de atípicos: {metodo}, {lados}, α = {alpha:g}  (n = {n})").format(
            metodo=nombre, lados=lados, alpha=self.alpha, n=self.n)]
        for _, f in self.steps.iterrows():
            lines.append(tr("  Paso {paso}: valor {valor:.6g} (índice {indice}), estadístico {est:.4f} {cmp} crítico {crit:.4f}"
                            ).format(paso=int(f["step"]), valor=f["value"], indice=int(f["index"]), est=f["statistic"],
                                     cmp=">" if f["statistic"] > f["critical"] else "≤", crit=f["critical"]))
        if self.has_outliers:
            lines.append(tr("  Atípicos declarados: {valores} (índices {indices})").format(
                valores=", ".join(f"{v:.6g}" for v in self.outlier_values),
                indices=", ".join(str(int(i)) for i in self.outlier_indices)))
        else:
            lines.append(tr("  Ningún atípico declarado."))
        lines.append(tr("  La prueba supone datos normales. No es una regla para eliminar datos: investiga el origen."))
        if self.normality_p < 0.05:
            lines.append(tr("  Aviso: los datos restantes no parecen normales (Shapiro-Wilk p = {p:.4f}); la prueba puede "
                            "marcar puntos que no son atípicos.").format(p=self.normality_p))
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover
        return self.summary()


def outlier_test(data, *, method: str = "grubbs", alpha: float = 0.05, sides: str = "two",
                 max_outliers: int | None = None) -> OutlierTestResult:
    """Prueba formal de valores atípicos (Grubbs o ESD generalizada de Rosner).

    Parameters
    ----------
    data : array-like
        Muestra 1-D (los valores no finitos se ignoran con un aviso; los índices son los de la entrada original).
    method : {'grubbs', 'esd'}
        ``'grubbs'`` contrasta un solo atípico (el más extremo); ``'esd'`` busca hasta ``max_outliers`` atípicos
        sin que se enmascaren entre sí.
    alpha : float
        Nivel de significación (por defecto 0,05).
    sides : {'two', 'upper', 'lower'}
        Bilateral, o solo valores demasiado altos o demasiado bajos.
    max_outliers : int, opcional
        Solo ESD: máximo de atípicos a buscar (por defecto ``min(10, (n − 1) // 2)``).

    Returns
    -------
    OutlierTestResult
        ``outlier_indices`` y ``outlier_values`` de los atípicos declarados, y un paso por fila en ``to_frame()``.

    Notes
    -----
    Ambas pruebas suponen que los datos sin los atípicos son normales; el resultado incluye el valor p de Shapiro-Wilk
    de los datos restantes. Declarar un punto atípico no justifica eliminarlo.
    """
    if method not in METODOS:
        raise ValueError(tr("'method' debe ser uno de {opciones}.").format(opciones=", ".join(METODOS)))
    if sides not in LADOS:
        raise ValueError(tr("'sides' debe ser uno de {opciones}.").format(opciones=", ".join(LADOS)))
    if not 0 < alpha < 1:
        raise ValueError(tr("'alpha' debe estar en (0, 1)."))
    original = np.asarray(data, dtype=float).ravel()
    ok = np.isfinite(original)
    descartados = int((~ok).sum())
    if descartados:
        warnings.warn(tr("Se ignoraron {n} valor(es) no finito(s); los índices son los de la entrada original.").format(
            n=descartados), UserWarning, stacklevel=2)
    posiciones = np.flatnonzero(ok)
    x = original[ok]
    n = x.size
    minimo = 3 if method == "grubbs" else 4
    if n < minimo:
        raise ValueError(tr("Se necesitan al menos {n} observaciones para esta prueba.").format(n=minimo))
    if np.ptp(x) == 0:
        raise ValueError(tr("Los datos son constantes: no se puede calcular la prueba de atípicos."))

    if method == "grubbs":
        r = 1
    else:
        r = (min(MAX_ATIPICOS_POR_DEFECTO, (n - 1) // 2) if max_outliers is None else int(max_outliers))
        if r < 1 or r > n - 3:
            raise ValueError(tr("'max_outliers' debe estar entre 1 y n − 3 ({tope}).").format(tope=n - 3))

    restantes = np.arange(n)  # posiciones (en x) de los datos que quedan
    filas = []
    for paso in range(1, r + 1):
        y = x[restantes]
        if np.ptp(y) == 0:
            break
        j, est = _estadistico(y, sides)
        crit = _critico(y.size, alpha, sides, method)
        filas.append({"step": paso, "index": int(posiciones[restantes[j]]), "value": float(y[j]),
                      "statistic": est, "critical": float(crit), "outlier": False})
        restantes = np.delete(restantes, j)
    # Grubbs: solo el primer paso decide; ESD: atípicos = los primeros k pasos, con k el mayor i en que R_i > λ_i
    k = 0
    for i, f in enumerate(filas, start=1):
        if f["statistic"] > f["critical"]:
            k = i
    for f in filas[:k]:
        f["outlier"] = True
    pasos = pd.DataFrame(filas)
    indices = pasos.loc[pasos["outlier"], "index"].to_numpy(dtype=int)
    sin = np.delete(original, indices)
    sin = sin[np.isfinite(sin)]
    p_norm = float(stats.shapiro(sin)[1]) if sin.size >= 3 and np.ptp(sin) > 0 else float("nan")
    return OutlierTestResult(
        method=method, alpha=float(alpha), sides=sides, n=n, steps=pasos, outlier_indices=indices,
        outlier_values=original[indices], normality_p=p_norm, dropped=descartados, data=original)
