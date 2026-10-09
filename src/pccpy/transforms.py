"""Transformaciones de normalización: Box-Cox, Yeo-Johnson y familia de Johnson (SU, SB, SL).

Una ``Transformation`` se ajusta una vez a los datos (``fit_transformation``) y se aplica después con
``forward`` (a los datos, a los límites de especificación y al objetivo) o se deshace con ``inverse``.

* **Box-Cox** (``'boxcox'``): solo datos estrictamente positivos; lambda por máxima verosimilitud.
* **Yeo-Johnson** (``'yeo-johnson'``): como Box-Cox pero admite ceros y valores negativos.
* **Johnson** (``'johnson'``): ``z = a + b·g(u)`` con ``u = (x − loc)/scale`` y ``g`` = ``asinh`` (SU, sin límites),
  ``ln(u/(1−u))`` (SB, acotada en ``(loc, loc + scale)``) o ``ln(u)`` (SL, lognormal de tres parámetros). Se ajustan
  las tres familias por máxima verosimilitud y se elige la que deja los datos transformados más normales (mayor valor
  p de Anderson-Darling). Un valor fuera del soporte de SB o SL se transforma en ±∞ (p. ej. un límite de
  especificación más allá de la cota de SB no puede superarse).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
from scipy import stats
from scipy.special import boxcox as _boxcox

from ._i18n import tr
from .normality import anderson_darling_pvalue, anderson_darling_statistic

METODOS = ("boxcox", "yeo-johnson", "johnson")
MIN_OBSERVACIONES = 8


def _yj(x: np.ndarray, lam: float) -> np.ndarray:
    out = np.empty_like(x, dtype=float)
    pos = x >= 0
    xp, xn = x[pos], x[~pos]
    out[pos] = np.log1p(xp) if lam == 0 else ((xp + 1) ** lam - 1) / lam
    out[~pos] = -np.log1p(-xn) if lam == 2 else -(((-xn + 1) ** (2 - lam)) - 1) / (2 - lam)
    return out


def _yj_inversa(z: np.ndarray, lam: float) -> np.ndarray:
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    zp, zn = z[pos], z[~pos]
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        if lam == 0:
            out[pos] = np.expm1(zp)
        else:
            t = lam * zp + 1
            out[pos] = np.where(t > 0, np.power(np.where(t > 0, t, 1.0), 1 / lam) - 1, np.inf)
        if lam == 2:
            out[~pos] = 1 - np.exp(-zn)
        else:
            t = 1 - (2 - lam) * zn
            out[~pos] = np.where(t > 0, 1 - np.power(np.where(t > 0, t, 1.0), 1 / (2 - lam)), -np.inf)
    return out


@dataclass(frozen=True)
class Transformation:
    """Transformación ya ajustada. ``params`` depende del método (ver ``info()``)."""

    method: str
    params: dict = field(default_factory=dict)

    def forward(self, values):
        """Transforma valores (escalar o arreglo) a la escala normalizada; los NaN se conservan."""
        v = np.asarray(values, dtype=float)
        escalar = v.ndim == 0
        v = np.atleast_1d(v)
        p = self.params
        with np.errstate(invalid="ignore", divide="ignore"):
            if self.method == "boxcox":
                out = np.where(v > 0, _boxcox(np.where(v > 0, v, 1.0), p["lambda"]), np.nan)
            elif self.method == "yeo-johnson":
                out = _yj(v, p["lambda"])
            else:
                u = (v - p["loc"]) / p["scale"]
                if p["family"] == "SU":
                    g = np.arcsinh(u)
                elif p["family"] == "SB":
                    g = np.where(u <= 0, -np.inf, np.where(u >= 1, np.inf, np.log(u / (1 - u))))
                else:
                    g = np.where(u <= 0, -np.inf, np.log(np.where(u > 0, u, 1.0)))
                out = p["a"] + p["b"] * g
        out = np.where(np.isnan(v), np.nan, out)
        return float(out[0]) if escalar else out

    def inverse(self, values):
        """Deshace la transformación: de la escala normalizada a la original.

        Un valor fuera del rango que alcanza la transformación (p. ej. por debajo de ``−1/λ`` en Box-Cox con
        ``λ > 0``) se lleva al extremo del soporte original: ``0`` para Box-Cox por abajo, ``±∞`` en los demás casos.
        """
        z = np.asarray(values, dtype=float)
        escalar = z.ndim == 0
        z = np.atleast_1d(z)
        p = self.params
        with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
            if self.method == "boxcox":
                lam = p["lambda"]
                if lam == 0:
                    out = np.exp(z)
                else:
                    t = lam * z + 1
                    fuera = np.where(t > 0, 0.0, (0.0 if lam > 0 else np.inf))
                    out = np.where(t > 0, np.power(np.where(t > 0, t, 1.0), 1 / lam), fuera)
            elif self.method == "yeo-johnson":
                out = _yj_inversa(z, p["lambda"])
            else:
                t = (z - p["a"]) / p["b"]
                if p["family"] == "SU":
                    u = np.sinh(t)
                elif p["family"] == "SB":
                    u = 1 / (1 + np.exp(-t))
                else:
                    u = np.exp(t)
                out = p["loc"] + p["scale"] * u
        out = np.where(np.isnan(z), np.nan, out)
        return float(out[0]) if escalar else out

    def info(self) -> dict:
        """Diccionario con el método y sus parámetros (es lo que guarda ``CapabilityResult.transform``)."""
        return {"method": self.method, **self.params}

    @classmethod
    def from_info(cls, info: dict) -> Transformation:
        """Reconstruye la transformación a partir de ``info()``."""
        p = {k: v for k, v in info.items() if k != "method"}
        return cls(info.get("method", "boxcox"), p)

    def describe(self) -> str:
        """Texto corto con el método y sus parámetros."""
        p = self.params
        if self.method == "johnson":
            return tr("Johnson {family} (a={a:.4g}, b={b:.4g}, loc={loc:.4g}, scale={scale:.4g})").format(**p)
        nombre = "Box-Cox" if self.method == "boxcox" else "Yeo-Johnson"
        return tr("{nombre} con lambda = {lam:.4f}").format(nombre=nombre, lam=p["lambda"])


def _pvalor_normalidad(z: np.ndarray) -> float:
    return float(anderson_darling_pvalue(anderson_darling_statistic(z), len(z)))


def _intentar(ajustar):
    try:
        return ajustar()
    except Exception:  # noqa: BLE001 - un ajuste que falla simplemente no compite
        return None


def _ajustar_johnson(x: np.ndarray) -> Transformation:
    candidatas = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        intentos = (("SU", lambda: stats.johnsonsu.fit(x)), ("SB", lambda: stats.johnsonsb.fit(x)),
                    ("SL", lambda: stats.lognorm.fit(x)))
        for familia, ajustar in intentos:
            par = _intentar(ajustar)
            if par is None:
                continue
            if familia == "SL":  # lognorm: z = ln((x − loc)/scale)/s
                s, loc, scale = par
                p = {"family": "SL", "a": 0.0, "b": 1.0 / s, "loc": float(loc), "scale": float(scale)}
            else:
                a, b, loc, scale = par
                p = {"family": familia, "a": float(a), "b": float(b), "loc": float(loc), "scale": float(scale)}
            t = Transformation("johnson", p)
            z = t.forward(x)
            if not np.all(np.isfinite(z)) or np.ptp(z) == 0 or not (p["b"] > 0 and p["scale"] > 0):
                continue
            candidatas.append((_pvalor_normalidad(z), familia, t))
    if not candidatas:
        raise ValueError(tr("No se pudo ajustar ninguna distribución de Johnson a los datos."))
    pvalor, _, t = max(candidatas, key=lambda c: c[0])  # empate: gana la primera (SU, SB, SL)
    return Transformation("johnson", {**t.params, "p_value": pvalor})


MAX_PARES_MEDCOUPLE = 1500  # puntos por lado de la mediana a partir de los cuales se submuestrea (memoria O(n²))
MAX_FRACCION_RECORTADA = 0.25  # si el recorte quitaría más, no se confía en él y se ajusta con todos los datos


def medcouple(x) -> float:
    """Medcouple (Brys, Hubert y Struyf, 2004): medida robusta de asimetría en [−1, 1] (0 si es simétrica).

    Es la mediana de ``((x_j − m) − (m − x_i)) / (x_j − x_i)`` sobre los pares ``x_i ≤ m ≤ x_j`` (``m`` = mediana).
    Los pares con ``x_i = x_j = m`` se ignoran. Con más de ``MAX_PARES_MEDCOUPLE`` puntos por lado se toma una
    submuestra equiespaciada (determinista).
    """
    x = np.sort(np.asarray(x, dtype=float).ravel())
    m = float(np.median(x))
    abajo, arriba = x[x <= m], x[x >= m]
    for lado in (0, 1):
        v = (abajo, arriba)[lado]
        if v.size > MAX_PARES_MEDCOUPLE:
            v = v[np.linspace(0, v.size - 1, MAX_PARES_MEDCOUPLE).astype(int)]
            abajo, arriba = (v, arriba) if lado == 0 else (abajo, v)
    den = arriba[None, :] - abajo[:, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        h = ((arriba[None, :] - m) - (m - abajo[:, None])) / den
    h = h[den > 0]
    return float(np.median(h)) if h.size else 0.0


def adjusted_boxplot_mask(x, k: float = 1.5) -> np.ndarray:
    """Máscara de los puntos dentro de los límites del diagrama de cajas ajustado por asimetría.

    Hubert y Vandervieren (2008): los límites del diagrama de cajas se mueven según el medcouple ``MC`` para que una
    cola larga natural no cuente como atípica. Con ``MC ≥ 0``: ``[Q1 − k·e^(−4·MC)·IQR, Q3 + k·e^(3·MC)·IQR]``; con
    ``MC < 0``: ``[Q1 − k·e^(−3·MC)·IQR, Q3 + k·e^(4·MC)·IQR]``. Devuelve ``True`` donde el punto cae dentro.
    """
    x = np.asarray(x, dtype=float)
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    mc = medcouple(x)
    if mc >= 0:
        inf, sup = q1 - k * np.exp(-4 * mc) * iqr, q3 + k * np.exp(3 * mc) * iqr
    else:
        inf, sup = q1 - k * np.exp(-3 * mc) * iqr, q3 + k * np.exp(4 * mc) * iqr
    return (x >= inf) & (x <= sup)


def fit_transformation(data, method: str, *, robust: bool = False) -> Transformation:
    """Ajusta una transformación de normalización a ``data`` (1-D, sin NaN).

    Parameters
    ----------
    data : array-like
        Observaciones (todas, no por subgrupos).
    method : {'boxcox', 'yeo-johnson', 'johnson'}
        Método; ver el módulo.
    robust : bool
        Con ``True`` el ajuste (por máxima verosimilitud) se hace sin los puntos fuera del diagrama de cajas ajustado
        por asimetría (``adjusted_boxplot_mask``), de modo que unos pocos valores muy lejanos no deformen la
        transformación y queden disimulados. La transformación se aplica después a todos los datos. Si el recorte
        quitaría más del 25 % de los puntos o dejaría menos de 8, se ignora y se ajusta con todos.

    Returns
    -------
    Transformation
    """
    if method not in METODOS:
        raise ValueError(tr("'transform' debe ser uno de {opciones}.").format(opciones=", ".join(METODOS)))
    x = np.asarray(data, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if x.size < MIN_OBSERVACIONES:
        raise ValueError(tr("Se necesitan al menos {n} observaciones para ajustar la transformación.").format(
            n=MIN_OBSERVACIONES))
    if np.ptp(x) == 0:
        raise ValueError(tr("Los datos son constantes: no se puede ajustar una transformación."))
    if robust:
        dentro = adjusted_boxplot_mask(x)
        if dentro.sum() >= MIN_OBSERVACIONES and dentro.mean() >= 1 - MAX_FRACCION_RECORTADA and np.ptp(x[dentro]) > 0:
            x = x[dentro]
    if method == "boxcox":
        if x.min() <= 0:
            raise ValueError(tr("Box-Cox requiere datos estrictamente positivos."))
        _, lam = stats.boxcox(x)
        return Transformation("boxcox", {"lambda": float(lam)})
    if method == "yeo-johnson":
        _, lam = stats.yeojohnson(x)
        return Transformation("yeo-johnson", {"lambda": float(lam)})
    return _ajustar_johnson(x)


__all__ = ["METODOS", "Transformation", "adjusted_boxplot_mask", "fit_transformation", "medcouple"]
