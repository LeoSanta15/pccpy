"""Fase I iterativa: excluir los puntos fuera de control, recalcular los límites y repetir hasta que el proceso quede estable."""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd

from ._data import to_subgroups
from ._frames import etiquetas
from ._i18n import N_, tr
from ._labels import detectar
from .charts import c_chart, imr_chart, np_chart, p_chart, u_chart, xbar_r_chart, xbar_s_chart
from .results import ControlChart, _texto_etiqueta
from .transforms import Transformation, fit_transformation

_COLUMNAS_HISTORIAL = {
    "iteration": N_("iteración"), "n_points": N_("puntos"), "n_flagged": N_("señales"), "center": N_("centro"),
    "sigma": N_("sigma"),
}
_COLUMNAS_TRANSFORMACION = {"transformation": N_("transformación"), "lambda": N_("lambda")}
# argumentos que describen los datos de la Fase I (no se reutilizan con los datos nuevos de la Fase II)
_ARGUMENTOS_DE_DATOS = ("subgroup_size", "subgroup", "value", "n")
MOTIVOS = ("in_control", "max_iterations", "min_points", "too_many_excluded", "transform_failed")
_CARTAS_CON_TRANSFORMACION = ("imr_chart", "xbar_r_chart", "xbar_s_chart")
_CAMBIO_LAMBDA_AVISO = 0.5  # cambio de lambda entre la primera y la última pasada que se considera inestable


@dataclass(frozen=True)
class _Tipo:
    """Cómo se prepara una carta para la Fase I y qué parámetros se congelan para la Fase II."""

    entrada: str  # 'individuos' | 'subgrupos' | 'conteos'
    congelar: Callable[[dict, float], dict]  # (parámetros de la carta, n constante) -> argumentos de la función
    paneles: tuple[str, ...] | None = None  # paneles cuyas señales excluyen puntos (None: todos)


_TIPOS: dict[Callable, _Tipo] = {
    # en I-MR el rango móvil de un valor atípico y el de su vecino siguiente avisan los dos: se excluye según el panel I
    imr_chart: _Tipo("individuos", lambda p, n: {"mu": p["media"], "sigma": p["sigma"]}, paneles=("I",)),
    xbar_r_chart: _Tipo("subgrupos", lambda p, n: {"mu": p["media"], "sigma": p["sigma"]}),
    xbar_s_chart: _Tipo("subgrupos", lambda p, n: {"mu": p["media"], "sigma": p["sigma"]}),
    p_chart: _Tipo("conteos", lambda p, n: {"p": p["centro"]}),
    np_chart: _Tipo("conteos", lambda p, n: {"p": p["centro"] / n}),
    c_chart: _Tipo("conteos", lambda p, n: {"c": p["centro"]}),
    u_chart: _Tipo("conteos", lambda p, n: {"u": p["centro"]}),
}


@dataclass
class PhaseOneIteration:
    """Una pasada de la Fase I: la carta calculada con los puntos que seguían incluidos."""

    iteration: int
    n_points: int
    flagged: np.ndarray  # posiciones (base 0, en los datos originales) de los puntos con señal
    center: float
    sigma: float
    transformation: Transformation | None = None  # la usada en esta pasada (solo con ``transform=``)


@dataclass
class PhaseOneResult:
    """Resultado de :func:`phase_one`.

    Atributos
    ---------
    chart : ControlChart
        Carta final, calculada solo con los puntos que no se excluyeron.
    history : list of PhaseOneIteration
        Una entrada por pasada (la 0 es la carta con todos los datos).
    excluded : numpy.ndarray
        Posiciones (base 0, en los datos originales) de los puntos excluidos, en orden.
    kept : numpy.ndarray
        Posiciones (base 0) de los puntos que se conservaron.
    converged : bool
        ``True`` si la última carta no tiene ninguna señal en los paneles que cuentan (``chart.in_control`` mira todos
        los paneles).
    reason : str
        ``'in_control'``, ``'max_iterations'``, ``'min_points'``, ``'too_many_excluded'`` o ``'transform_failed'``.
    limits : dict
        Argumentos de la función de la carta que congelan los límites (``mu``/``sigma``, ``p``, ``c`` o ``u``): es lo
        que :meth:`phase2` aplica a los datos nuevos.
    labels : numpy.ndarray or None
        Etiquetas (fechas, lotes…) de los puntos originales, si los datos las traían.
    transformation : Transformation or None
        Con ``transform=``: la transformación de la última pasada, que :meth:`phase2` aplica a los datos nuevos junto
        con los límites congelados (``mu`` y ``sigma`` están en la escala transformada). ``None`` sin ``transform``.
    """

    chart: ControlChart
    history: list[PhaseOneIteration]
    excluded: np.ndarray
    kept: np.ndarray
    converged: bool
    reason: str
    n_original: int
    limits: dict
    labels: np.ndarray | None = None
    transformation: Transformation | None = None
    _funcion: Callable = field(default=imr_chart, repr=False)
    _argumentos: dict = field(default_factory=dict, repr=False)

    @property
    def excluded_labels(self) -> np.ndarray | None:
        """Etiquetas de los puntos excluidos (``None`` si los datos no traían etiquetas)."""
        return None if self.labels is None else self.labels[self.excluded]

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Historial: una fila por pasada (puntos incluidos, señales, centro y sigma).

        Con ``transform=`` añade el método de la transformación de cada pasada y su ``lambda`` (``NaN`` en Johnson).
        Con ``stable=True`` las columnas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        col = etiquetas(_COLUMNAS_HISTORIAL, stable)
        datos = {
            col["iteration"]: [h.iteration for h in self.history],
            col["n_points"]: [h.n_points for h in self.history],
            col["n_flagged"]: [h.flagged.size for h in self.history],
            col["center"]: [h.center for h in self.history],
            col["sigma"]: [h.sigma for h in self.history],
        }
        if self.transformation is not None:  # con transform=: la transformación de cada pasada (lambda es NaN en Johnson)
            ct = etiquetas(_COLUMNAS_TRANSFORMACION, stable)
            ts = [h.transformation for h in self.history if h.transformation is not None]
            datos[ct["transformation"]] = [t.method for t in ts]
            datos[ct["lambda"]] = [t.params.get("lambda", np.nan) for t in ts]
        return pd.DataFrame(datos)

    def summary(self) -> str:
        """Resumen en texto: puntos excluidos, límites finales y estado de cada pasada."""
        n_excl = int(self.excluded.size)
        lines = [
            tr("Fase I: carta {kind}").format(kind=self.chart.kind),
            tr("  Puntos: {n} → {kept} (excluidos: {excluded})").format(
                n=self.n_original, kept=int(self.kept.size), excluded=n_excl),
        ]
        if self.converged:
            lines.append(tr("  Resultado: el proceso quedó bajo control tras {iters} pasada(s)").format(
                iters=len(self.history) - 1))
        else:
            lines.append(tr("  Resultado: NO convergió ({reason})").format(reason=_describir_motivo(self.reason)))
        restantes = [pnl.name for pnl in self.chart.panels if pnl.flagged.size]
        if self.converged and restantes:
            lines.append(tr("  Aviso: quedan señales en otros paneles ({panels}); no se excluyeron por no contar para la Fase I").format(
                panels=", ".join(restantes)))
        if n_excl:
            puntos = ", ".join(
                f"{i + 1}" if self.labels is None else f"{i + 1} ({_texto_etiqueta(self.labels[i])})"
                for i in self.excluded)
            lines.append(tr("  Puntos excluidos: {points}").format(points=puntos))
        lines.append(tr("  Límites congelados para la Fase II: {limits}").format(
            limits=", ".join(f"{k}={v:.6g}" for k, v in self.limits.items())))
        if self.transformation is not None:
            lines.append(tr("  Transformación congelada (los límites están en la escala transformada): {t}").format(
                t=self.transformation.describe()))
        for h in self.history:
            lines.append(tr("    Pasada {iteration}: {n} puntos, {flagged} con señal").format(
                iteration=h.iteration, n=h.n_points, flagged=int(h.flagged.size)))
        return "\n".join(lines)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()

    def phase2(self, data, **kwargs) -> ControlChart:
        """Carta de Fase II: los datos nuevos con los límites congelados de esta Fase I.

        Parameters
        ----------
        data : array-like
            Datos nuevos, en cualquiera de los formatos que acepta la carta (una serie con fechas conserva las fechas).
        **kwargs
            Argumentos de la función de la carta para los datos nuevos (por ejemplo ``n=`` en las cartas de atributos o
            ``subgroup_size=``); sustituyen a los usados en la Fase I.
        """
        argumentos = {**self._argumentos, **self.limits, **kwargs}
        if self.transformation is not None:
            argumentos["transform"] = self.transformation  # fija: no se reajusta a los datos nuevos
        return self._funcion(data, **argumentos)

    def plot(self, **kwargs):
        """Dibuja la carta final de la Fase I. Ver :func:`pccpy.plotting.plot_control_chart`."""
        return self.chart.plot(**kwargs)


def _describir_motivo(motivo: str) -> str:
    return {
        "max_iterations": tr("se alcanzó el máximo de pasadas"),
        "min_points": tr("quedarían menos puntos que el mínimo"),
        "too_many_excluded": tr("se excluiría una fracción excesiva de los puntos: el proceso no es estable"),
        "transform_failed": tr("no se pudo reajustar la transformación con los puntos que quedarían"),
    }.get(motivo, motivo)


def _preparar(tipo: _Tipo, data, kwargs: dict) -> tuple[np.ndarray, np.ndarray | None, dict]:
    """(datos como array, etiquetas por punto, argumentos de la carta sin los que describen los datos)."""
    argumentos = {k: v for k, v in kwargs.items() if k not in _ARGUMENTOS_DE_DATOS}
    if tipo.entrada == "subgrupos":
        mat, n_completos = to_subgroups(
            data, kwargs.get("subgroup_size"), kwargs.get("subgroup"), value=kwargs.get("value"))
        etiquetas_x = detectar(data, kwargs.get("subgroup_size"), kwargs.get("subgroup"), kwargs.get("value"))
        if n_completos < mat.shape[0]:  # el último subgrupo incompleto no entra en los límites: tampoco en la Fase I
            mat = mat[:n_completos]
            etiquetas_x = None if etiquetas_x is None else etiquetas_x[:n_completos]
        return mat, etiquetas_x, argumentos
    arr = np.asarray(data, dtype=float).ravel()
    if not np.all(np.isfinite(arr)):
        raise ValueError(tr("La Fase I no admite valores faltantes ni infinitos: elimínalos antes."))
    etiquetas_x = detectar(data)
    if tipo.entrada == "conteos" and kwargs.get("n") is not None:
        argumentos["n"] = kwargs["n"]
    return arr, etiquetas_x, argumentos


def phase_one(
    chart: Callable[..., ControlChart],
    data,
    *,
    exclude_tests=None,
    exclude_panels=None,
    max_iterations: int = 10,
    min_points: int = 20,
    max_excluded: float = 0.25,
    **kwargs: Any,
) -> PhaseOneResult:
    """Fase I iterativa: excluye los puntos con señal, recalcula los límites y repite hasta que no quede ninguna.

    En cada pasada se calcula la carta con los puntos que siguen incluidos; todos los puntos con alguna señal (en
    los paneles que cuentan, ver ``exclude_panels``) se excluyen y se vuelve a calcular. Termina cuando una carta no tiene señales (el proceso quedó
    estable: sus límites sirven para vigilar datos nuevos con :meth:`PhaseOneResult.phase2`) o cuando seguir
    excluyendo no es razonable (ver ``max_iterations``, ``min_points`` y ``max_excluded``). **Excluir puntos solo
    tiene sentido si se ha encontrado y corregido su causa especial**; si no, los límites quedan artificialmente
    estrechos.

    Parameters
    ----------
    chart : callable
        Función de la carta: ``imr_chart``, ``xbar_r_chart``, ``xbar_s_chart``, ``p_chart``, ``np_chart``,
        ``c_chart`` o ``u_chart``.
    data : array-like
        Los datos de la Fase I, en el formato de esa carta. Con una serie de pandas con fechas, el resultado conserva
        las fechas. No debe contener valores faltantes.
    exclude_tests : int or iterable of int, optional
        Solo se excluyen los puntos con señal en estas pruebas (por defecto, todas las solicitadas en ``tests``).
    exclude_panels : str or iterable of str, optional
        Paneles cuyas señales excluyen puntos. Por defecto, en ``imr_chart`` solo el panel ``'I'`` (un valor atípico
        dispara también el rango móvil de su vecino, que no es un punto anómalo) y, en las demás cartas, todos.
    max_iterations : int
        Máximo de recálculos tras la carta inicial (por defecto 10).
    min_points : int
        No se excluyen puntos si quedarían menos de estos (por defecto 20; observaciones, subgrupos o muestras).
    max_excluded : float
        Fracción máxima de puntos que se pueden excluir en total (por defecto 0.25). Si se superara, se detiene sin
        excluir y el resultado no converge: un proceso que necesita descartar tantos puntos no está estable.
    **kwargs
        Argumentos de la función de la carta, como ``tests=(1, 2, 3)``, ``subgroup_size=5`` o ``n=…`` (en las cartas
        de atributos).

    Returns
    -------
    PhaseOneResult

    Raises
    ------
    ValueError
        Si la carta no está soportada, no se pide ninguna prueba, hay valores no finitos o hay menos de
        ``min_points`` puntos.

    Examples
    --------
    >>> import numpy as np, pccpy as pp
    >>> rng = np.random.default_rng(2)
    >>> x = rng.normal(100, 2, 60); x[[10, 33]] += 15     # dos puntos con causa especial
    >>> fase1 = pp.phase_one(pp.imr_chart, x, tests=(1,))
    >>> fase1.excluded                                    # puntos excluidos (base 0)
    array([10, 33])
    >>> nueva = fase1.phase2(rng.normal(100, 2, 20))       # datos nuevos con los límites de la Fase I
    """
    tipo = _TIPOS.get(chart)
    if tipo is None:
        raise ValueError(tr("La Fase I no está soportada para esta carta; usa {charts}.").format(
            charts=", ".join(sorted(f.__name__ for f in _TIPOS))))
    if max_iterations < 0 or not 0 < max_excluded <= 1 or min_points < 2:
        raise ValueError(tr("'max_iterations' debe ser >= 0, 'max_excluded' estar en (0, 1] y 'min_points' ser >= 2."))
    if "stages" in kwargs and kwargs["stages"] is not None:
        raise ValueError(tr("La Fase I no admite 'stages': hazla por separado en cada etapa."))
    transform = kwargs.pop("transform", None)
    if transform is not None and chart.__name__ not in _CARTAS_CON_TRANSFORMACION:
        raise ValueError(tr("'transform' solo se admite en {charts}.").format(charts=", ".join(_CARTAS_CON_TRANSFORMACION)))
    if kwargs.get("tests", (1,)) in (None, (), []):
        raise ValueError(tr("La Fase I necesita al menos una prueba de causas especiales ('tests')."))

    arr, etiquetas_x, argumentos = _preparar(tipo, data, kwargs)
    n = arr.shape[0]
    if n < min_points:
        raise ValueError(tr("La Fase I necesita al menos {min_points} puntos (hay {n}); ajusta 'min_points' si es a propósito.").format(
            min_points=min_points, n=n))
    cuantos = None if exclude_tests is None else set(np.atleast_1d(exclude_tests).astype(int).tolist())
    paneles = tipo.paneles if exclude_panels is None else tuple(np.atleast_1d(exclude_panels).astype(str))
    n_const = float(np.atleast_1d(kwargs.get("n", 1.0))[0]) if tipo.entrada == "conteos" else 1.0

    def ajustar(conservados: np.ndarray) -> Transformation | None:
        """Transformación para los puntos conservados: se reajusta en cada pasada salvo que el usuario dé una ya ajustada."""
        if transform is None or isinstance(transform, Transformation):
            return transform
        return fit_transformation(arr[conservados].ravel(), transform)

    def calcular(conservados: np.ndarray, t: Transformation | None) -> ControlChart:
        a = dict(argumentos)
        if t is not None:
            a["transform"] = t
        if kwargs.get("n") is not None and np.ndim(kwargs["n"]) > 0:
            a["n"] = np.asarray(kwargs["n"], dtype=float)[conservados]
        c = chart(arr[conservados], **a)
        if etiquetas_x is not None:
            c.with_labels(etiquetas_x[conservados])
        return c

    def con_senal(carta: ControlChart) -> np.ndarray:
        idx = [np.asarray(v, dtype=int) for p in carta.panels if paneles is None or p.name in paneles
               for t, v in p.violations.items() if cuantos is None or t in cuantos]
        return np.unique(np.concatenate(idx)) if idx else np.array([], dtype=int)

    conservados = np.arange(n)
    historial: list[PhaseOneIteration] = []
    motivo = "in_control"
    t_actual = ajustar(conservados)  # un error aquí (p. ej. Box-Cox con datos no positivos) se propaga: no hay Fase I
    while True:
        carta = calcular(conservados, t_actual)
        marcados = con_senal(carta)
        prm = carta.params[0]
        historial.append(PhaseOneIteration(
            iteration=len(historial), n_points=int(conservados.size), flagged=conservados[marcados],
            center=float(prm.get("media", prm.get("centro", np.nan))), sigma=float(prm.get("sigma", np.nan)),
            transformation=t_actual))
        if marcados.size == 0:
            break
        if len(historial) - 1 >= max_iterations:
            motivo = "max_iterations"
            break
        restantes = np.delete(conservados, marcados)
        if restantes.size < min_points:
            motivo = "min_points"
            break
        if (n - restantes.size) / n > max_excluded:
            motivo = "too_many_excluded"
            break
        try:
            t_nueva = ajustar(restantes)
        except ValueError:  # p. ej. quedan menos de 8 observaciones o Johnson no se ajusta: la carta actual es la última
            motivo = "transform_failed"
            break
        conservados, t_actual = restantes, t_nueva

    convergio = motivo == "in_control"
    resultado = PhaseOneResult(
        chart=carta, history=historial, excluded=np.setdiff1d(np.arange(n), conservados), kept=conservados,
        converged=convergio, reason=motivo, n_original=n,
        limits=tipo.congelar(carta.params[0], n_const), labels=etiquetas_x, transformation=t_actual,
        _funcion=chart, _argumentos=argumentos_fase2(argumentos))
    _avisar_cambio_de_transformacion(historial)
    if not convergio:
        warnings.warn(
            tr("La Fase I no convergió: {reason}.").format(reason=_describir_motivo(motivo)), UserWarning, stacklevel=2)
    return resultado


def _avisar_cambio_de_transformacion(historial: list[PhaseOneIteration]) -> None:
    """Avisa si la transformación reajustada cambió mucho entre la primera y la última pasada (Fase I inestable)."""
    primera, ultima = historial[0].transformation, historial[-1].transformation
    if primera is None or ultima is None or primera is ultima or primera.method != ultima.method:
        return
    cambio = None
    if "lambda" in primera.params:
        d = abs(primera.params["lambda"] - ultima.params["lambda"])
        cambio = d if d > _CAMBIO_LAMBDA_AVISO else None
    elif primera.params.get("family") != ultima.params.get("family"):
        cambio = float("nan")
    if cambio is not None:
        warnings.warn(tr("La transformación cambió mucho al excluir puntos ({primera} → {ultima}): la Fase I no es estable "
                         "y los límites dependen de qué puntos se excluyan.").format(
            primera=primera.describe(), ultima=ultima.describe()), UserWarning, stacklevel=3)


def argumentos_fase2(argumentos: dict) -> dict:
    """Argumentos de la carta que se reutilizan con los datos nuevos (sin los que describen los datos de la Fase I)."""
    return {k: v for k, v in argumentos.items() if k not in _ARGUMENTOS_DE_DATOS}
