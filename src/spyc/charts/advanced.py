"""Cartas avanzadas para una variable: media móvil, Z-MR, I-MR-R/S, zona, G y T.

Las fórmulas siguen la documentación de métodos de Minitab.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from scipy import optimize, stats

from .. import rules
from .._constants import c4, c5, d2, d3
from .._data import as_1d, to_subgroups
from .._sigma import moving_range, sigma_individuals, sigma_subgroups, subgroup_stats, vec
from ..results import ControlChart
from ._engine import StagePanel, build_chart, check_method, full
from .timeweighted import _series


# ------------------------------------------------------------------ media móvil
def ma_chart(
    data,
    *,
    length: int = 3,
    subgroup_size: Optional[int] = None,
    subgroup=None,
    mu: Optional[float] = None,
    sigma: Optional[float] = None,
    k: float = 3.0,
) -> ControlChart:
    """Carta de media móvil (Stat > Control Charts > Time-Weighted > Moving Average).

    El punto *i* es el promedio de las últimas ``length`` observaciones (o
    subgrupos); en los primeros ``length - 1`` puntos se promedian las que haya y
    los límites son más anchos, como en Minitab. Después los límites son constantes.

    ``mu`` y ``sigma`` se estiman de los datos si no se dan. Solo aplica la prueba 1.
    """
    if int(length) != length or length < 2:
        raise ValueError("'length' debe ser un entero >= 2.")
    length = int(length)
    means, n, sigma_est, grand = _series(data, subgroup_size, subgroup)
    s = float(sigma) if sigma is not None else sigma_est
    t0 = float(mu) if mu is not None else grand
    s_x = s / np.sqrt(n)

    def stage_fn(idx):
        N = len(means)
        ma = np.array([means[max(0, i - length + 1) : i + 1].mean() for i in range(N)])
        w = np.minimum(np.arange(1, N + 1), length)
        sig_t = s_x / np.sqrt(w)
        ucl, lcl = t0 + k * sig_t, t0 - k * sig_t
        flagged = np.flatnonzero((ma > ucl) | (ma < lcl))
        panel = StagePanel("MA", ma, full(t0, N), ucl, lcl, sig_t, "Media móvil", "only1",
                           violations={1: flagged})
        return [panel], {"media": t0, "sigma": s, "longitud": length, "k": k, "n_subgrupo": n}

    return build_chart("MA", len(means), None, stage_fn, (1,), {1: k})


# ------------------------------------------------------------------------- Z-MR
def _runs(parts: np.ndarray):
    """Bloques consecutivos con la misma etiqueta: lista de (etiqueta, inicio, fin)."""
    out, start = [], 0
    for i in range(1, parts.size + 1):
        if i == parts.size or parts[i] != parts[start]:
            out.append((parts[start].item() if hasattr(parts[start], "item") else parts[start],
                        start, i))
            start = i
    return out


def _mr_values(y: np.ndarray) -> np.ndarray:
    mr = moving_range(y, 2)
    return mr[~np.isnan(mr)]


def zmr_chart(
    x,
    parts,
    *,
    sigma_method: str = "constant",
    mu: Optional[Dict] = None,
    sigma=None,
    tests=(1,),
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Carta Z-MR para producción de corridas cortas (Variables Charts for Individuals > Z-MR).

    Cada observación se estandariza con la media de su parte/producto y una sigma,
    de modo que partes con medias o variaciones distintas se grafican juntas:
    ``z = (x - mu_parte) / sigma``. Se grafica z (LC = 0, límites en ±3) y el rango
    móvil de los z (LC = d2(2) = 1.128, LCS = 3.686).

    Parameters
    ----------
    x : array-like
        Observaciones en orden temporal.
    parts : array-like
        Parte o producto de cada observación. Una *corrida* es un bloque de
        observaciones consecutivas de la misma parte.
    sigma_method : {'constant', 'relative', 'by_part', 'by_run'}
        * ``'constant'``: una sigma común para todas las partes (rango móvil
          promedio dentro de las corridas / d2).
        * ``'relative'``: igual, pero sobre ln(x); útil si la variación crece con el
          tamaño de la medición.
        * ``'by_part'``: una sigma por parte (junta todas sus corridas).
        * ``'by_run'``: una sigma por corrida (cada corrida necesita >= 2 observaciones).
    mu : dict, opcional
        Media (o valor nominal) por parte, ``{parte: valor}``. Con
        ``'relative'`` debe estar en escala logarítmica. Si no se da, se estima.
    sigma : float o dict, opcional
        Sigma histórica: un número para todas las partes o ``{parte: valor}``.
    """
    y_raw = as_1d(x)
    parts = np.asarray(parts)
    if parts.shape != y_raw.shape:
        raise ValueError("'parts' debe tener una etiqueta por observación.")
    check_method(sigma_method, ("constant", "relative", "by_part", "by_run"))
    if sigma_method == "relative":
        if np.any(y_raw <= 0):
            raise ValueError("El método 'relative' requiere datos positivos (usa ln).")
        y = np.log(y_raw)
    else:
        y = y_raw

    runs = _runs(parts)
    labels = list(dict.fromkeys(r[0] for r in runs))
    mu_of = {}
    for lab in labels:
        if mu is not None:
            if lab not in mu:
                raise ValueError(f"Falta la media histórica de la parte {lab!r} en 'mu'.")
            mu_of[lab] = float(mu[lab])
        else:
            mu_of[lab] = float(y[parts == lab].mean())

    def est(mr: np.ndarray, what: str) -> float:
        if mr.size == 0:
            raise ValueError(f"No hay rangos móviles para estimar sigma ({what}); "
                             "se necesitan al menos 2 observaciones consecutivas de la misma parte.")
        return float(mr.mean() / d2(2))

    run_sigma: List[Optional[float]] = [None] * len(runs)
    part_sigma: Dict = {}
    if sigma is not None:
        for j, (lab, _, _) in enumerate(runs):
            run_sigma[j] = float(sigma[lab]) if isinstance(sigma, dict) else float(sigma)
    elif sigma_method in ("constant", "relative"):
        s = est(np.concatenate([_mr_values(y[a:b]) for _, a, b in runs]), "todas las partes")
        run_sigma = [s] * len(runs)
    elif sigma_method == "by_part":
        for lab in labels:
            mr = np.concatenate([_mr_values(y[a:b]) for l, a, b in runs if l == lab])
            part_sigma[lab] = est(mr, f"parte {lab!r}")
        run_sigma = [part_sigma[lab] for lab, _, _ in runs]
    else:  # by_run
        for j, (lab, a, b) in enumerate(runs):
            run_sigma[j] = est(_mr_values(y[a:b]), f"corrida {j + 1} (parte {lab!r})")

    if any(s is None or s <= 0 for s in run_sigma):
        raise ValueError("Se obtuvo una sigma igual a cero (datos sin variación).")
    sigmas: List[float] = run_sigma  # type: ignore[assignment]  # ya se validó que no queda ningún None
    z = np.empty(y.size)
    for (lab, a, b), s in zip(runs, sigmas):
        z[a:b] = (y[a:b] - mu_of[lab]) / s

    dd2, dd3 = d2(2), d3(2)

    def stage_fn(idx):
        n = z.size
        z_panel = StagePanel("Z", z, full(0.0, n), full(3.0, n), full(-3.0, n), full(1.0, n),
                             "Valor Z", "full")
        mr_panel = StagePanel(
            "MR", moving_range(z, 2), full(dd2, n), full(dd2 + 3 * dd3, n),
            full(max(0.0, dd2 - 3 * dd3), n), full(dd3, n),
            "Rango móvil de Z", "basic", symmetric=False,
        )
        params = {"método": "histórica" if sigma is not None else sigma_method, "partes": len(labels), "corridas": len(runs), "n": n}
        if len(set(run_sigma)) == 1:
            params["sigma"] = float(run_sigma[0])
        else:
            params["sigma_mín"], params["sigma_máx"] = float(min(run_sigma)), float(max(run_sigma))
        return [z_panel, mr_panel], params

    return build_chart("Z-MR", z.size, None, stage_fn, tests, test_params)


# ------------------------------------------------------------- I-MR-R/S (entre/dentro)
def imr_rs_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    subgroup=None,
    within: str = "r",
    sigma_method: Optional[str] = None,
    mu: Optional[float] = None,
    sigma_within: Optional[float] = None,
    sigma_between: Optional[float] = None,
    stages=None,
    tests=(1,),
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Carta I-MR-R/S (Between/Within): variación entre y dentro de subgrupos.

    Grafica las medias de subgrupo como valores individuales (I) con su rango móvil
    (MR), más el rango (R) o la desviación estándar (S) dentro de los subgrupos.
    Los límites de I y MR usan la variación **total** de las medias (rango móvil de
    las medias), de modo que la variación entre subgrupos no genera falsas alarmas
    como en una Xbar-R.

    ``within``: ``'r'`` o ``'s'``. ``sigma_method`` (sigma dentro): ``'rbar'`` o
    ``'pooled'`` para R; ``'sbar'`` o ``'pooled'`` para S (por defecto rbar / sbar).

    Los parámetros ``params`` incluyen las desviaciones estándar *dentro*, *entre* y
    *entre/dentro* (sigma_entre = sqrt(max(0, sigma_med² - sigma_dentro²/n)), con n el
    tamaño de subgrupo más frecuente, que debe darse en más de la mitad de los
    subgrupos; si no, se reportan como NaN). Con ``sigma_between`` histórica, la sigma
    de las medias es sqrt(sigma_entre² + sigma_dentro²/n).
    """
    within = within.lower()
    if within not in ("r", "s"):
        raise ValueError("'within' debe ser 'r' o 's'.")
    default = "rbar" if within == "r" else "sbar"
    sigma_method = sigma_method or default
    check_method(sigma_method, (default, "pooled"))
    g = to_subgroups(data, subgroup_size, subgroup)

    def stage_fn(idx):
        gs = g[idx]
        n_i, means, rng, s_i = subgroup_stats(gs)
        k = len(idx)
        if k < 2:
            raise ValueError("Cada etapa necesita al menos 2 subgrupos.")
        m = float(np.mean(means)) if mu is None else float(mu)
        sw = float(sigma_within) if sigma_within is not None else sigma_subgroups(gs, sigma_method)

        sizes, counts = np.unique(n_i, return_counts=True)
        n_mode = int(sizes[np.argmax(counts)])
        mode_ok = counts.max() > k / 2
        sx_mr = sigma_individuals(means, "mr", 2)
        if sigma_between is not None:
            sb = float(sigma_between)
            sx = float(np.sqrt(sb**2 + sw**2 / n_mode))
        else:
            sb = float(np.sqrt(max(0.0, sx_mr**2 - sw**2 / n_mode))) if mode_ok else float("nan")
            sx = sx_mr
        sbw = float(np.sqrt(sb**2 + sw**2)) if np.isfinite(sb) else float("nan")

        i_panel = StagePanel("I", means, full(m, k), full(m + 3 * sx, k), full(m - 3 * sx, k),
                             full(sx, k), "Media de la muestra", "full")
        c = d2(2) * sx
        mr_panel = StagePanel(
            "MR", moving_range(means, 2), full(c, k), full(c + 3 * d3(2) * sx, k),
            full(max(0.0, c - 3 * d3(2) * sx), k), full(d3(2) * sx, k),
            "Rango móvil de las medias", "basic", symmetric=False,
        )
        if within == "r":
            cc, sd = sw * vec(d2, n_i), sw * vec(d3, n_i)
            w_panel = StagePanel("R", rng, cc, cc + 3 * sd, np.maximum(0.0, cc - 3 * sd), sd,
                                 "Rango dentro del subgrupo", "basic", symmetric=False)
        else:
            cc, sd = sw * vec(c4, n_i), sw * vec(c5, n_i)
            w_panel = StagePanel("S", s_i, cc, cc + 3 * sd, np.maximum(0.0, cc - 3 * sd), sd,
                                 "Desv. est. dentro del subgrupo", "basic", symmetric=False)
        params = {"media": m, "sigma_dentro": sw, "sigma_entre": sb, "sigma_entre_dentro": sbw,
                  "subgrupos": k}
        return [i_panel, mr_panel, w_panel], params

    return build_chart(f"I-MR-{within.upper()}", g.shape[0], stages, stage_fn, tests, test_params)


# ------------------------------------------------------------- eventos raros: G y T
def _rare_violations(values, center, lcl, ucl, tests, test_params):
    """Prueba 1 con los límites propios de la carta; pruebas 2-4 estándar."""
    wanted = [t for t in tests if t in rules.FAMILIES["basic"]]
    found = {}
    if 1 in wanted:
        found[1] = np.flatnonzero((values > ucl) | (values < lcl))
    rest = [t for t in wanted if t != 1]
    if rest:  # con sigma=1 las pruebas 2-4 solo usan el lado y el orden de los puntos
        found.update(rules.apply_tests(values, center, np.ones_like(values), rest, test_params))
    return found


def _geom_quantile(p: float, q: float) -> float:
    """Cuantil q de la geométrica "número hasta el evento" (k >= 1), con la
    interpolación lineal entre los dos enteros vecinos que usa Minitab."""
    kb = max(1, int(np.ceil(np.log1p(-q) / np.log1p(-p))))
    ka = kb - 1
    pa, pb = 1 - (1 - p) ** ka, 1 - (1 - p) ** kb
    return ka + (q - pa) / (pb - pa)


def g_chart(
    x,
    *,
    p: Optional[float] = None,
    k: float = 3.0,
    stages=None,
    tests=(1,),
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Carta G para eventos raros: número de casos (u oportunidades) entre eventos.

    Se basa en la distribución geométrica. ``p`` es la probabilidad de evento; si no
    se da, se estima como 1 / (1 + media). La línea central es la mediana, el LCS es el
    percentil que corresponde a ``k`` sigmas de una normal (0.99865 con k=3) y el LCI
    es 0. La prueba 1 marca los puntos sobre el LCS; las pruebas 2-4 son las usuales.
    No incluye la prueba de Benneyan.
    """
    x = as_1d(x)
    if np.any(x < 0):
        raise ValueError("Los conteos entre eventos no pueden ser negativos.")
    if p is not None and not 0 < p < 1:
        raise ValueError("'p' debe estar en (0, 1).")
    tests_n = rules.normalize_tests(tests)
    q_hi = float(stats.norm.cdf(k))

    def stage_fn(idx):
        xs = x[idx]
        mean = float(xs.mean())
        if p is None and mean <= 0:
            raise ValueError("Todos los conteos son 0; no se puede estimar la carta G.")
        pe = float(p) if p is not None else 1.0 / (1.0 + mean)
        n = xs.size
        center, ucl = _geom_quantile(pe, 0.5) - 1, _geom_quantile(pe, q_hi) - 1
        c, u, l = full(center, n), full(ucl, n), full(0.0, n)
        viol = _rare_violations(xs, c, l, u, tests_n, test_params)
        panel = StagePanel("G", xs, c, u, l, full(np.nan, n), "Cantidad entre eventos", "basic",
                           symmetric=False, violations=viol)
        return [panel], {"p": pe, "media": mean, "n": n}

    chart = build_chart("G", x.size, stages, stage_fn, tests_n, test_params)
    chart.test1_text = "1 punto fuera de los percentiles de la distribución geométrica"
    return chart


def _weibull_mle(x: np.ndarray):
    """Máxima verosimilitud de la Weibull de 2 parámetros: (forma, escala)."""
    lx = np.log(x)
    if np.ptp(lx) == 0:
        raise ValueError("Todas las duraciones son iguales; no se puede ajustar la Weibull.")

    def score(c):
        w = np.exp(c * (lx - lx.max()))  # estable numéricamente
        return np.sum(w * lx) / np.sum(w) - 1.0 / c - lx.mean()

    c = optimize.brentq(score, 1e-3, 1e3, xtol=1e-12)
    return c, float(np.mean(x**c) ** (1.0 / c))


def t_chart(
    x,
    *,
    distribution: str = "weibull",
    shape: Optional[float] = None,
    scale: Optional[float] = None,
    k: float = 3.0,
    stages=None,
    tests=(1,),
    test_params: Optional[Dict[int, float]] = None,
) -> ControlChart:
    """Carta T para eventos raros: tiempo entre eventos (Weibull o exponencial).

    Los parámetros se estiman por máxima verosimilitud (o se dan con ``shape`` y
    ``scale``). La línea central es la mediana y los límites son los percentiles
    Phi(-k) y Phi(k) de la distribución (0.00135 y 0.99865 con k=3). Las duraciones
    deben ser > 0. ``distribution``: ``'weibull'`` o ``'exponential'``.
    """
    x = as_1d(x)
    check_method(distribution, ("weibull", "exponential"), "distribution")
    if np.any(x <= 0):
        raise ValueError("Las duraciones deben ser positivas (no se admiten duraciones iguales a 0).")
    if distribution == "weibull" and (shape is None) != (scale is None):
        raise ValueError("Para parámetros históricos Weibull indique 'shape' y 'scale' juntos.")
    tests_n = rules.normalize_tests(tests)
    q_lo, q_hi = float(stats.norm.cdf(-k)), float(stats.norm.cdf(k))

    def stage_fn(idx):
        xs = x[idx]
        if distribution == "exponential":
            c, sc = 1.0, float(scale) if scale is not None else float(xs.mean())
        elif shape is not None:
            c, sc = float(shape), float(scale)
        else:
            c, sc = _weibull_mle(xs)
        n = xs.size

        def ppf(q):
            return sc * (-np.log1p(-q)) ** (1.0 / c)

        cen, lo, hi = ppf(0.5), ppf(q_lo), ppf(q_hi)
        cc, l, u = full(cen, n), full(lo, n), full(hi, n)
        viol = _rare_violations(xs, cc, l, u, tests_n, test_params)
        panel = StagePanel("T", xs, cc, u, l, full(np.nan, n), "Tiempo entre eventos", "basic",
                           symmetric=False, violations=viol)
        return [panel], {"distribución": distribution, "forma": c, "escala": sc, "n": n}

    chart = build_chart("T", x.size, stages, stage_fn, tests_n, test_params)
    chart.test1_text = f"1 punto fuera de los percentiles de la distribución {distribution}"
    return chart


# ------------------------------------------------------------------------ carta de zona
def _zone_scores(z: np.ndarray, weights, reset: bool):
    """Puntaje acumulado de zona y puntos que señalan (puntaje >= peso de la zona 4).

    Cada punto aporta el peso de su zona (0-1σ, 1-2σ, 2-3σ, más de 3σ) y los pesos
    se suman mientras los puntos permanezcan del mismo lado de la línea central; al
    cruzarla (o caer justo sobre ella) el puntaje vuelve a 0 y el punto que cruza
    inicia la nueva suma.
    """
    zone = np.digitize(np.abs(z), [1.0, 2.0, 3.0])
    side = np.sign(z)
    score = np.zeros(z.size)
    flagged, cum, prev = [], 0.0, 0.0
    for i in range(z.size):
        if side[i] == 0:
            cum = 0.0
        else:
            if side[i] != prev:
                cum = 0.0
            cum += weights[zone[i]]
        score[i] = cum
        prev = side[i]
        if cum >= weights[3]:
            flagged.append(i)
            if reset:
                cum = 0.0
    return score, np.array(flagged, dtype=int)


def zone_chart(
    data,
    *,
    subgroup_size: Optional[int] = None,
    subgroup=None,
    sigma_method: Optional[str] = None,
    mu: Optional[float] = None,
    sigma: Optional[float] = None,
    weights=(0, 2, 4, 8),
    reset: bool = False,
    stages=None,
) -> ControlChart:
    """Carta de zona (Stat > Control Charts > Variables Charts for Subgroups > Zone).

    Sustituye las pruebas de causas especiales por un puntaje acumulado (Davis, Homer
    y Woodall, 1990): la zona 1 (0-1σ) pesa 0, la 2 (1-2σ) pesa 2, la 3 (2-3σ) pesa 4
    y la 4 (más de 3σ) pesa 8. Los pesos se suman mientras los puntos sigan del mismo
    lado de la línea central y se reinician al cruzarla; hay señal cuando el puntaje
    llega al peso de la zona 4 (8 por defecto). Un punto justo en la frontera entre dos
    zonas se asigna a la zona más lejana.

    ``data``: observaciones individuales (vector) o subgrupos (matriz 2-D, o vector con
    ``subgroup_size`` / ``subgroup``). ``sigma_method``: ``'mr'`` (por defecto),
    ``'median_mr'`` o ``'mssd'`` para individuales; ``'rbar'`` (por defecto) o
    ``'pooled'`` para subgrupos. ``reset=True`` reinicia el puntaje tras cada señal.

    El resultado tiene el panel ``"Zona"`` (medias y límites) y el panel ``"Puntaje"``
    (puntaje acumulado y su umbral). Las señales se marcan en ``"Zona"``.
    """
    w = tuple(float(v) for v in weights)
    if len(w) != 4 or min(w) < 0 or any(b < a for a, b in zip(w, w[1:])) or w[3] <= 0:
        raise ValueError("'weights' debe tener 4 pesos no negativos, no decrecientes y con el último > 0.")
    arr = np.asarray(data, dtype=float)
    individuals = arr.ndim == 1 and subgroup_size is None and subgroup is None
    g = to_subgroups(arr, 1) if individuals else to_subgroups(data, subgroup_size, subgroup)
    if individuals or (g.shape[1] == 1 and not np.isnan(g).any()):
        individuals = True
        check_method(sigma_method or "mr", ("mr", "median_mr", "mssd"))
    else:
        check_method(sigma_method or "rbar", ("rbar", "pooled"))

    def stage_fn(idx):
        gs = g[idx]
        n_i, means, _, _ = subgroup_stats(gs)
        k = len(idx)
        m = float(np.nansum(gs) / n_i.sum()) if mu is None else float(mu)
        if sigma is not None:
            sg = float(sigma)
        elif individuals:
            sg = sigma_individuals(means, sigma_method or "mr", 2)
        else:
            sg = sigma_subgroups(gs, sigma_method or "rbar")
        sig_x = sg / np.sqrt(n_i)
        score, flagged = _zone_scores((means - m) / sig_x, w, reset)
        z_panel = StagePanel("Zona", means, full(m, k), m + 3 * sig_x, m - 3 * sig_x, sig_x,
                             "Media de la muestra" if not individuals else "Valor individual",
                             "only1", violations={1: flagged})
        s_panel = StagePanel("Puntaje", score, full(0.0, k), full(w[3], k), full(np.nan, k),
                             full(np.nan, k), "Puntaje acumulado", "only1", symmetric=False,
                             violations={})
        return [z_panel, s_panel], {"media": m, "sigma": sg, "pesos": w, "reinicio": reset, "n": k}

    chart = build_chart("Zona", g.shape[0], stages, stage_fn, (1,), None)
    chart.test1_text = f"puntaje acumulado de zona >= {w[3]:g}"
    return chart
