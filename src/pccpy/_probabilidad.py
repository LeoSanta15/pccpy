"""Probabilidad de un valor en el análisis de capacidad (``CapabilityResult.probability``)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import ndtr

from ._i18n import N_, tr

SIGMAS = ("overall", "within")

# clave estable -> etiqueta en español
_COLUMNAS = (
    ("event", N_("Evento")), ("below", N_("Por debajo de")), ("above", N_("Por encima de")),
    ("between_lower", N_("Entre (inferior)")), ("between_upper", N_("Entre (superior)")),
    ("probability", N_("Probabilidad")), ("ppm", N_("PPM")), ("dpmo", N_("DPMO")), ("dpu", N_("DPU")),
)


def _normal(media: float, sigma: float):
    """``(cdf, sf)`` de una normal; con ``sigma == 0`` es un escalón (0,5 en la media)."""
    if sigma > 0:
        return (lambda v: ndtr((v - media) / sigma)), (lambda v: ndtr(-(v - media) / sigma))

    def cdf(v):
        return np.where(v < media, 0.0, np.where(v > media, 1.0, 0.5))

    return cdf, (lambda v: 1.0 - cdf(v))


def _a_arreglo(valor, nombre: str):
    v = np.asarray(valor, dtype=float) if not isinstance(valor, str) else None
    if v is None:
        raise ValueError(tr("'{nombre}' debe ser un número o un arreglo de una dimensión.").format(nombre=nombre))
    if v.ndim > 1 or (v.ndim == 1 and v.size == 0):
        raise ValueError(
            tr("'{nombre}' debe ser un número o un arreglo no vacío de una dimensión.").format(nombre=nombre))
    if np.isnan(v).any():
        raise ValueError(tr("'{nombre}' no puede contener NaN.").format(nombre=nombre))
    return v


def _par(between):
    try:
        a, b = between
    except (TypeError, ValueError):
        raise ValueError(tr("'between' debe ser un par (inferior, superior).")) from None
    return a, b


@dataclass
class ProbabilityResult:
    """Probabilidad de un evento sobre el proceso y sus medidas derivadas.

    Con un número en la entrada, las medidas son números; con arreglos, arreglos de la forma resultante.

    Attributes
    ----------
    event : {'below', 'above', 'outside', 'between'}
        Evento: por debajo de un valor, por encima, fuera de un intervalo (ambos) o entre dos valores.
    probability : float | ndarray
        Probabilidad del evento, entre 0 y 1.
    ppm : float | ndarray
        ``1e6 · probability`` (partes por millón).
    dpmo : float | ndarray | None
        Defectos por millón de oportunidades (``1e6 · probability``); ``None`` con ``between`` (no es un defecto).
    dpu : float | ndarray | None
        Defectos por unidad: ``opportunities · probability``; ``None`` con ``between``.
    p_below, p_above : float | ndarray | None
        Las dos partes del evento (``None`` si no hay esa parte).
    below, above : float | ndarray | None
        Valores usados, en unidades originales (los límites de especificación si se heredaron).
    between : tuple | None
        Par ``(inferior, superior)`` usado con ``between``.
    sigma : str
        ``'overall'`` o ``'within'``.
    opportunities : int
        Oportunidades de defecto por unidad (para ``dpu``).
    """

    event: str
    probability: object
    ppm: object
    dpmo: object
    dpu: object
    p_below: object
    p_above: object
    below: object
    above: object
    between: tuple | None
    sigma: str
    opportunities: int

    def to_frame(self, stable: bool = False) -> pd.DataFrame:
        """Tabla con una fila por elemento.

        Con ``stable=True`` las columnas llevan claves canónicas en inglés que no cambian con el idioma.
        """
        n = max(np.size(self.probability), 1)  # type: ignore[arg-type]

        def col(v):
            return np.broadcast_to(np.nan if v is None else np.asarray(v, dtype=float), (n,)).copy()

        lo, hi = self.between if self.between is not None else (None, None)
        datos = {
            "event": [self.event] * n, "below": col(self.below), "above": col(self.above),
            "between_lower": col(lo), "between_upper": col(hi), "probability": col(self.probability),
            "ppm": col(self.ppm), "dpmo": col(self.dpmo), "dpu": col(self.dpu),
        }
        frame = pd.DataFrame(datos)
        if not stable:
            frame.columns = [tr(etiqueta) for _clave, etiqueta in _COLUMNAS]
        return frame

    def summary(self) -> str:
        """Texto con el evento y la tabla de medidas."""
        return "\n".join([
            tr("Probabilidad de un valor (sigma {sigma}, oportunidades por unidad: {oportunidades})").format(
                sigma=self.sigma, oportunidades=self.opportunities),
            self.to_frame().to_string(index=False),
        ])

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.summary()


def _salida(v):
    v = np.asarray(v, dtype=float)
    return float(v) if v.ndim == 0 else v


def _combinar(*valores):
    try:
        return np.broadcast_arrays(*valores)
    except ValueError:
        raise ValueError(tr("Los valores indicados tienen formas incompatibles.")) from None


def _armar(evento, p, p_below, p_above, below, above, between, sigma, opportunities) -> ProbabilityResult:
    ppm = 1e6 * np.asarray(p) if np.ndim(p) else 1e6 * p
    defecto = evento != "between"
    return ProbabilityResult(
        event=evento, probability=p, ppm=ppm, dpmo=ppm if defecto else None,
        dpu=opportunities * p if defecto else None, p_below=p_below, p_above=p_above,
        below=below, above=above, between=between, sigma=sigma, opportunities=int(opportunities))


def calcular_probabilidad(cdf, sf, *, lsl, usl, below, above, between, sigma, opportunities,
                          escala=None) -> ProbabilityResult:
    """Núcleo común: valida, combina los arreglos y evalúa ``cdf``/``sf`` de la escala del modelo.

    ``escala`` lleva los valores originales a la escala del modelo (transformación creciente); ``sigma`` ya viene
    validado por quien llama.
    """
    entero = isinstance(opportunities, (int, np.integer)) and not isinstance(opportunities, bool)
    if not entero or opportunities < 1:
        raise ValueError(tr("'opportunities' debe ser un entero >= 1."))
    if between is not None and (below is not None or above is not None):
        raise ValueError(tr("'between' no se puede combinar con 'below' ni con 'above'."))
    if between is None and below is None and above is None:
        below, above = lsl, usl
        if below is None and above is None:
            raise ValueError(tr("Indica 'below', 'above' o 'between': el resultado no tiene límites de especificación."))

    def a_modelo(v):
        if escala is None:
            return v
        with np.errstate(invalid="ignore"):
            t = np.asarray(escala(v), dtype=float)
        # fuera del dominio (p. ej. <= 0 en Box-Cox) no hay masa por debajo; los infinitos se conservan
        return np.where(np.isinf(v), v, np.where(np.isnan(t), -np.inf, t))

    if between is not None:
        a, b = _par(between)
        a, b = _combinar(_a_arreglo(a, "between"), _a_arreglo(b, "between"))
        if np.any(a > b):
            raise ValueError(tr("En 'between' el valor inferior no puede ser mayor que el superior."))
        ta, tb = a_modelo(a), a_modelo(b)
        # la resta de colas más pequeñas evita la cancelación lejos de la media
        p = np.where(cdf(ta) > 0.5, sf(ta) - sf(tb), cdf(tb) - cdf(ta))
        return _armar("between", _salida(p), None, None, None, None, (_salida(a), _salida(b)), sigma, opportunities)

    lo = None if below is None else _a_arreglo(below, "below")
    hi = None if above is None else _a_arreglo(above, "above")
    if lo is not None and hi is not None:
        lo, hi = _combinar(lo, hi)  # type: ignore[assignment]
    pl = None if lo is None else _salida(cdf(a_modelo(lo)))
    ph = None if hi is None else _salida(sf(a_modelo(hi)))
    if pl is not None and ph is not None:
        evento, p = "outside", _salida(np.asarray(pl) + np.asarray(ph))
    else:
        evento, p = ("below", pl) if pl is not None else ("above", ph)
    return _armar(evento, p, pl, ph, None if lo is None else _salida(lo), None if hi is None else _salida(hi),
                  None, sigma, opportunities)
