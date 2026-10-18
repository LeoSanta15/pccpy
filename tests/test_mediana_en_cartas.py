"""Pruebas de la especificación 013: mediana en las cartas de variables (``center="median"`` y ``median_r_chart``).

Referencias independientes: ``numpy.median``, la integración numérica de la densidad del estadístico de orden (``scipy.integrate``),
la distribución beta de la mediana (``scipy.special.betainc``), la tabla de Ã2 de Montgomery (valores recordados de memoria, no
verificados contra el libro) y simulación con 20 semillas.
"""
import re
import warnings
from math import factorial
from pathlib import Path

import numpy as np
import pytest
from scipy import integrate, special, stats

import pccpy

RAIZ = Path(__file__).resolve().parents[1]
D2_2 = 2 / np.sqrt(np.pi)
D2 = {3: 1.693, 5: 2.326, 7: 2.704, 9: 2.970}  # Montgomery, tabla de factores
A2_TILDE = {3: 1.187, 5: 0.691, 7: 0.509, 9: 0.412}  # Montgomery (de memoria)


def _asimetricos(seed=0, n=90):
    return np.random.default_rng(seed).lognormal(1.0, 0.6, n)


def _g(seed=1, filas=25, n=5):
    return np.random.default_rng(seed).normal(50, 2, (filas, n))


def _con_salida():
    g = _g()
    g[3] += 12.0  # un subgrupo cuya mediana sale de los límites
    return g


def _cmed_integral(n):
    """Desviación estándar de la mediana de ``n`` (impar) normales estándar por integración de la densidad del estadístico de orden."""
    m = (n - 1) // 2
    c = factorial(n) / factorial(m) ** 2
    f = lambda x: c * stats.norm.cdf(x) ** m * stats.norm.sf(x) ** m * stats.norm.pdf(x)  # noqa: E731
    return float(np.sqrt(integrate.quad(lambda x: x * x * f(x), -12, 12, epsabs=1e-13, epsrel=1e-13)[0]))


# ── S013-RF-01: center="median" en I-MR ──────────────────────────────────────────────────────────────────────────────

def test_s013_rf_01_imr_centro_en_la_mediana_con_la_misma_sigma():
    x = _asimetricos()
    s = np.mean(np.abs(np.diff(x))) / D2_2
    c = pccpy.imr_chart(x, center="median")
    i = c["I"]
    assert i.center[0] == pytest.approx(np.median(x))
    assert i.ucl[0] == pytest.approx(np.median(x) + 3 * s, rel=1e-9)
    assert i.lcl[0] == pytest.approx(np.median(x) - 3 * s, rel=1e-9)
    assert c.params[0]["center"] == "median"
    assert c.params[0]["mean"] == pytest.approx(np.median(x))
    assert c.params[0]["sigma"] == pytest.approx(s, rel=1e-9)


def test_s013_rf_01_por_defecto_es_la_media_e_identico_al_de_antes():
    x = _asimetricos()
    a, b = pccpy.imr_chart(x), pccpy.imr_chart(x, center="mean")
    assert a.params[0]["center"] == b.params[0]["center"] == "mean"
    for pa, pb in zip(a.panels, b.panels):
        np.testing.assert_array_equal(pa.center, pb.center)
        np.testing.assert_array_equal(pa.ucl, pb.ucl)
    assert a["I"].center[0] == pytest.approx(x.mean())


def test_s013_rf_01_etapas_y_huecos_y_una_observacion():
    x = np.r_[_asimetricos(1, 30), 5 * _asimetricos(2, 30)]
    c = pccpy.imr_chart(x, center="median", stages=[1] * 30 + [2] * 30)
    assert c["I"].center[0] == pytest.approx(np.median(x[:30]))
    assert c["I"].center[-1] == pytest.approx(np.median(x[30:]))
    xh = x.copy()
    xh[10] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ch = pccpy.imr_chart(xh, center="median")
    assert ch["I"].center[0] == pytest.approx(np.nanmedian(xh))
    solo = pccpy.imr_chart(np.r_[x[:20], 7.5], center="median", stages=[1] * 20 + [2], sigma=1.0)
    assert solo["I"].center[-1] == pytest.approx(7.5)


def test_s013_rf_01_datos_constantes_avisan_y_centran_en_el_valor():
    with pytest.warns(UserWarning):
        c = pccpy.imr_chart(np.full(12, 5.0), center="median")
    assert c["I"].center[0] == 5.0


def test_s013_rf_01_con_transform_y_con_k():
    x = _asimetricos()
    c = pccpy.imr_chart(x, center="median", transform="boxcox")
    t = c.transformation
    assert c.params[0]["mean"] == pytest.approx(np.median(t.forward(x)))
    d = pccpy.imr_chart(x, center="median", k=(3, 2))
    s = np.mean(np.abs(np.diff(x))) / D2_2
    assert d["I"].ucl[0] - np.median(x) == pytest.approx(3 * s, rel=1e-9)
    assert np.median(x) - d["I"].lcl[0] == pytest.approx(2 * s, rel=1e-9)


# ── S013-RF-02: center="median" en Xbar-R y Xbar-S ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("f, disp", [(pccpy.xbar_r_chart, "R"), (pccpy.xbar_s_chart, "S")])
def test_s013_rf_02_xbar_centro_en_la_mediana_de_las_medias_de_subgrupo(f, disp):
    g = _g()
    medias = g.mean(axis=1)
    mean_chart, med = f(g), f(g, center="median")
    xb = med["Xbar"]
    assert xb.center[0] == pytest.approx(np.median(medias))
    sigma = mean_chart.params[0]["sigma"]
    assert med.params[0]["sigma"] == pytest.approx(sigma)
    assert xb.ucl[0] - xb.center[0] == pytest.approx(3 * sigma / np.sqrt(5), rel=1e-9)
    assert med.params[0]["center"] == "median" and mean_chart.params[0]["center"] == "mean"
    np.testing.assert_array_equal(med[disp].ucl, mean_chart[disp].ucl)


def test_s013_rf_02_el_ultimo_subgrupo_incompleto_no_entra_en_el_centro():
    x = _asimetricos(3, 23)  # 4 subgrupos completos de 5 y uno de 3
    c = pccpy.xbar_r_chart(x, subgroup_size=5, center="median")
    completos = x[:20].reshape(4, 5).mean(axis=1)
    assert c["Xbar"].center[0] == pytest.approx(np.median(completos))


# ── S013-RF-03: combinación con mu y valores inválidos ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("f, args", [(pccpy.imr_chart, (_asimetricos(),)), (pccpy.xbar_r_chart, (_g(),)), (pccpy.xbar_s_chart, (_g(),))])
@pytest.mark.parametrize("kw", [{"center": "median", "mu": 5.0}, {"center": "moda"}, {"center": "Mean"}, {"center": 1}, {"center": None}])
def test_s013_rf_03_errores_traducibles(f, args, kw):
    with pccpy.language("es"), pytest.raises(ValueError) as es:
        f(*args, **kw)
    with pccpy.language("en"), pytest.raises(ValueError) as en:
        f(*args, **kw)
    assert str(es.value) != str(en.value)


def test_s013_rf_03_center_mean_con_mu_sigue_valiendo():
    c = pccpy.imr_chart(_asimetricos(), center="mean", mu=3.0)
    assert c["I"].center[0] == 3.0


# ── S013-RF-04: carta de medianas de subgrupo ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", [3, 5, 7, 9])
def test_s013_rf_04_cmed_y_a2_tilde_contra_integracion_y_montgomery(n):
    from pccpy._constants import cmed

    assert cmed(n) == pytest.approx(_cmed_integral(n), rel=1e-7)
    assert 3 * cmed(n) / pccpy.d2(n) == pytest.approx(A2_TILDE[n], abs=6e-4)


@pytest.mark.parametrize("n", [3, 4, 5, 6])
def test_s013_rf_04_cmed_contra_simulacion_de_20_semillas(n):
    from pccpy._constants import cmed

    sd = [np.median(np.random.default_rng(s).normal(size=(200_000, n)), axis=1).std(ddof=1) for s in range(20)]
    assert cmed(n) == pytest.approx(np.mean(sd), rel=0.01)


def test_s013_rf_04_la_carta_de_medianas():
    g = _g()
    r = np.mean(g.max(axis=1) - g.min(axis=1))
    c = pccpy.median_r_chart(g)
    assert [p.name for p in c.panels] == ["Median", "R"] and c.kind == "Median-R"
    m = c["Median"]
    assert m.values == pytest.approx(np.median(g, axis=1))
    assert m.center[0] == pytest.approx(np.median(g, axis=1).mean())
    assert m.ucl[0] - m.center[0] == pytest.approx(A2_TILDE[5] * r, rel=2e-3)
    assert m.center[0] - m.lcl[0] == pytest.approx(A2_TILDE[5] * r, rel=2e-3)
    xr = pccpy.xbar_r_chart(g)
    np.testing.assert_array_equal(c["R"].ucl, xr["R"].ucl)
    np.testing.assert_array_equal(c["R"].lcl, xr["R"].lcl)
    prm = c.params[0]
    assert prm["center"] == "mean_of_medians" and prm["size"] == 5 and prm["subgroups"] == 25


def test_s013_rf_04_formatos_de_entrada_etapas_mu_y_sigma():
    x = _asimetricos(2, 40)
    a = pccpy.median_r_chart(x, subgroup_size=5)
    b = pccpy.median_r_chart(x.reshape(8, 5))
    np.testing.assert_allclose(a["Median"].ucl, b["Median"].ucl)
    h = pccpy.median_r_chart(x.reshape(8, 5), mu=10.0, sigma=2.0)
    assert h["Median"].center[0] == 10.0
    assert h["Median"].ucl[0] - 10.0 == pytest.approx(3 * 2.0 * 0.5356, rel=2e-3)  # cmed(5) = 0.5356
    s = pccpy.median_r_chart(x.reshape(8, 5), stages=[1] * 4 + [2] * 4)
    assert s["Median"].center[0] == pytest.approx(np.median(x.reshape(8, 5)[:4], axis=1).mean())
    assert s["Median"].center[-1] == pytest.approx(np.median(x.reshape(8, 5)[4:], axis=1).mean())


def test_s013_rf_04_acepta_k_alpha_y_rescale_zones_de_la_spec_014():
    g = _g()
    a, b = pccpy.median_r_chart(g), pccpy.median_r_chart(g, k=2)
    np.testing.assert_allclose(b["Median"].ucl - b["Median"].center, (a["Median"].ucl - a["Median"].center) * 2 / 3, rtol=1e-9)
    assert pccpy.median_r_chart(g, k=(3, 2)).params[0]["k_lower"] == 2.0
    pccpy.median_r_chart(g, alpha=0.05, rescale_zones=True)


# ── S013-RF-05: tamaños de subgrupo ──────────────────────────────────────────────────────────────────────────────────

def test_s013_rf_05_n_1_y_tamanos_desiguales_lanzan_value_error():
    with pytest.raises(ValueError):
        pccpy.median_r_chart(_asimetricos(), subgroup_size=1)
    sub = np.repeat(np.arange(10), [4, 5, 5, 5, 5, 5, 5, 5, 5, 5])
    with pytest.raises(ValueError):
        pccpy.median_r_chart(np.random.default_rng(0).normal(size=sub.size), subgroup=sub)


@pytest.mark.parametrize("n", [2, 3, 4, 6, 8])
def test_s013_rf_05_cualquier_n_mayor_o_igual_que_2_construye_la_carta(n):
    c = pccpy.median_r_chart(np.random.default_rng(n).normal(size=(20, n)))
    assert np.all(np.isfinite(c["Median"].ucl))


# ── S013-RF-06: probability() ────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", [3, 5, 9])
def test_s013_rf_06_probabilidad_exacta_con_n_impar(n):
    g = np.random.default_rng(n).normal(0, 1, (20, n))
    c = pccpy.median_r_chart(g, mu=0.0, sigma=1.0)
    m = c["Median"]
    k = (n + 1) // 2
    esperado = special.betainc(k, k, stats.norm.cdf(m.lcl[0] / 1.0)) + special.betainc(k, k, stats.norm.sf(m.ucl[0] / 1.0))
    assert c.probability().probability == pytest.approx(esperado, rel=1e-9)


def test_s013_rf_06_probabilidad_con_n_par_contra_simulacion():
    c = pccpy.median_r_chart(np.zeros((6, 4)) + np.arange(24).reshape(6, 4) * 0.01, mu=0.0, sigma=1.0)
    m = c["Median"]
    tasas = []
    for seed in range(20):
        med = np.median(np.random.default_rng(seed).normal(size=(200_000, 4)), axis=1)
        tasas.append(np.mean((med > m.ucl[0]) | (med < m.lcl[0])))
    assert c.probability().probability == pytest.approx(np.mean(tasas), rel=0.05)


def test_s013_rf_06_en_el_panel_r_sigue_valiendo():
    c = pccpy.median_r_chart(_g(), mu=50.0, sigma=2.0)
    assert 0 < c.probability(panel="R").probability < 0.02


# ── S013-RF-07: claves y textos ──────────────────────────────────────────────────────────────────────────────────────

def test_s013_rf_07_summary_traduce_center_y_oculta_el_valor_por_defecto():
    x = _asimetricos()
    with pccpy.language("es"):
        assert "centro=mediana" in pccpy.imr_chart(x, center="median").summary()
        assert "centro=" not in pccpy.imr_chart(x).summary().split("Parámetros")[1].split("\n")[0]
        assert "Carta de control Median-R" in pccpy.median_r_chart(_g()).summary()
        assert "[Mediana]" in pccpy.median_r_chart(_con_salida()).summary()
    with pccpy.language("en"):
        assert "center=median" in pccpy.imr_chart(x, center="median").summary()
        assert "center=mean_of_medians" not in pccpy.median_r_chart(_g()).summary()
        assert "mean of medians" in pccpy.median_r_chart(_g()).summary()
        assert "[Median]" in pccpy.median_r_chart(_con_salida()).summary()


def test_s013_rf_07_claves_en_ingles_y_traducidas():
    from pccpy import results

    assert "median" in results._VALORES_PARAMETRO and "mean_of_medians" in results._VALORES_PARAMETRO
    assert "Median" in results._NOMBRES_VISIBLES
    for idioma in ("es", "en"):
        with pccpy.language(idioma):
            assert set(pccpy.median_r_chart(_g()).params[0]) == {
                "stage", "mean", "sigma", "subgroups", "size", "center", "k_upper", "k_lower"}


# ── S013-RF-08: documentación ────────────────────────────────────────────────────────────────────────────────────────

ENCABEZADO = {"README.md": r"^###? .*[Mm]ediana", "README_en.md": r"^###? .*[Mm]edian"}


@pytest.mark.parametrize("nombre", ["README.md", "README_en.md"])
def test_s013_rf_08_el_readme_documenta_la_mediana_y_su_fragmento_corre(nombre):
    texto = (RAIZ / nombre).read_text(encoding="utf-8")
    m = re.search(ENCABEZADO[nombre], texto, re.MULTILINE)
    assert m, f"{nombre}: falta la sección de la mediana"
    seccion = texto[m.start():]
    siguiente = re.search(r"^#{2,3} ", seccion[3:], re.MULTILINE)
    seccion = seccion[: siguiente.start() + 3] if siguiente else seccion
    for palabra in ('center="median"', "median_r_chart", "transform"):
        assert palabra in seccion
    bloques = re.findall(r"```python\n(.*?)```", seccion, re.DOTALL)
    assert bloques
    import matplotlib

    matplotlib.use("Agg")
    ns: dict = {}
    exec("import numpy as np\nimport pccpy as pp\nrng = np.random.default_rng(1)\nx = rng.lognormal(1.0, 0.6, 60)\n" + "\n".join(bloques), ns)
