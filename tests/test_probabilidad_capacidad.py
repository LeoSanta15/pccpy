"""Pruebas de la especificación 010: ``probability()`` en los resultados de capacidad.

Las referencias se escriben aparte con ``scipy.stats`` y fórmulas manuales, no con la salida de pccpy.
"""
import numpy as np
import pytest
from scipy import stats

import pccpy


@pytest.fixture(scope="module")
def datos():
    return np.random.default_rng(1).lognormal(1, 0.3, 100)


@pytest.fixture(scope="module")
def normal():
    x = np.random.default_rng(7).normal(50, 2, 120)
    return pccpy.capability_analysis(x, lsl=44, usl=56, subgroup_size=1)


def _norm(r, sigma="overall"):
    s = r.sigma_overall if sigma == "overall" else r.sigma_within
    return stats.norm(r.mean, s)


# ---------------------------------------------------------------- RF-01
def test_s010_rf_01_below_above_between(normal):
    """S010-RF-01: P(X<a), P(X>b) y P(a<=X<=b) con la normal del resultado."""
    d = _norm(normal)
    assert normal.probability(below=47).probability == pytest.approx(d.cdf(47), rel=1e-12)
    assert normal.probability(above=53).probability == pytest.approx(d.sf(53), rel=1e-12)
    assert normal.probability(between=(48, 52)).probability == pytest.approx(d.cdf(52) - d.cdf(48), rel=1e-12)


def test_s010_rf_01_cola_sin_cancelacion(normal):
    """S010-RF-01: la cola superior lejana usa sf (no 1 - cdf)."""
    x = normal.mean + 10 * normal.sigma_overall
    assert normal.probability(above=x).probability == pytest.approx(stats.norm.sf(10), rel=1e-9)


def test_s010_rf_01_sigma_within(normal):
    """S010-RF-01: sigma='within' usa sigma_within."""
    d = _norm(normal, "within")
    p = normal.probability(below=47, sigma="within")
    assert p.probability == pytest.approx(d.cdf(47), rel=1e-12)
    assert p.sigma == "within"


# ---------------------------------------------------------------- RF-02
def test_s010_rf_02_fuera_de_intervalo(normal):
    """S010-RF-02: below y above juntos dan la probabilidad de quedar fuera, con sus partes."""
    d = _norm(normal)
    p = normal.probability(below=47, above=53)
    assert p.event == "outside"
    assert p.p_below == pytest.approx(d.cdf(47), rel=1e-12)
    assert p.p_above == pytest.approx(d.sf(53), rel=1e-12)
    assert p.probability == pytest.approx(d.cdf(47) + d.sf(53), rel=1e-12)


def test_s010_rf_02_hereda_limites(normal):
    """S010-RF-02: sin argumentos hereda lsl y usl."""
    d = _norm(normal)
    p = normal.probability()
    assert p.event == "outside"
    assert p.probability == pytest.approx(d.cdf(44) + d.sf(56), rel=1e-12)


def test_s010_rf_02_un_solo_limite():
    """S010-RF-02: con un solo límite hereda el que exista."""
    x = np.random.default_rng(3).normal(10, 1, 80)
    r = pccpy.capability_analysis(x, usl=13, subgroup_size=1)
    p = r.probability()
    assert p.event == "above"
    assert p.probability == pytest.approx(stats.norm(r.mean, r.sigma_overall).sf(13), rel=1e-12)


def test_s010_rf_02_sin_limites_error():
    """S010-RF-02: sin límites ni argumentos, ValueError."""
    x = np.random.default_rng(3).normal(10, 1, 80)
    r = pccpy.capability_analysis(x, lsl=8, subgroup_size=1)
    r.lsl = None
    with pytest.raises(ValueError, match="below"):
        r.probability()


def test_s010_rf_02_between_no_se_combina(normal):
    """S010-RF-02: between con below o above es un error."""
    with pytest.raises(ValueError):
        normal.probability(between=(48, 52), below=47)
    with pytest.raises(ValueError):
        normal.probability(between=(48, 52), above=53)


# ---------------------------------------------------------------- RF-03
def test_s010_rf_03_boxcox(datos):
    """S010-RF-03: Box-Cox con T(a) = (a^lam - 1)/lam escrita aparte."""
    r = pccpy.capability_boxcox(datos, lsl=1, usl=6)
    lam = r.transform["lambda"]

    def T(a):
        return np.log(a) if lam == 0 else (a ** lam - 1) / lam

    d = stats.norm(r.mean, r.sigma_overall)
    assert r.probability(below=2.5).probability == pytest.approx(d.cdf(T(2.5)), rel=1e-12)
    assert r.probability(above=5).probability == pytest.approx(d.sf(T(5)), rel=1e-12)
    assert r.probability(between=(2, 4)).probability == pytest.approx(d.cdf(T(4)) - d.cdf(T(2)), rel=1e-12)


def test_s010_rf_03_boxcox_lambda_cero():
    """S010-RF-03: con lambda = 0 se usa el logaritmo."""
    x = np.random.default_rng(2).lognormal(0, 0.5, 200)
    r = pccpy.capability_analysis(x, lsl=0.2, usl=5, transform="boxcox")
    r.transform = {"lambda": 0.0}
    d = stats.norm(r.mean, r.sigma_overall)
    assert r.probability(below=0.7).probability == pytest.approx(d.cdf(np.log(0.7)), rel=1e-12)


def test_s010_rf_03_yeo_johnson(datos):
    """S010-RF-03: Yeo-Johnson (x >= 0) con (( x+1)^lam - 1)/lam escrita aparte."""
    r = pccpy.capability_analysis(datos, lsl=1, usl=6, transform="yeo-johnson")
    lam = r.transform["lambda"]
    d = stats.norm(r.mean, r.sigma_overall)
    t = ((3.0 + 1) ** lam - 1) / lam
    assert r.probability(below=3.0).probability == pytest.approx(d.cdf(t), rel=1e-12)


def test_s010_rf_03_johnson_coherente(datos):
    """S010-RF-03: con Johnson, creciente y coherente con el PPM esperado en los límites."""
    r = pccpy.capability_analysis(datos, lsl=1, usl=6, transform="johnson")
    p = r.probability()
    assert p.p_below * 1e6 == pytest.approx(r.ppm_overall[0], rel=1e-9)
    assert p.p_above * 1e6 == pytest.approx(r.ppm_overall[1], rel=1e-9)
    ps = r.probability(below=[1.5, 2.5, 4.0, 7.0]).probability
    assert np.all(np.diff(ps) > 0)


def test_s010_rf_03_transformacion_con_within(datos):
    """S010-RF-03: sigma='within' es válido con transformación."""
    r = pccpy.capability_boxcox(datos, lsl=1, usl=6)
    p = r.probability(below=2.5, sigma="within")
    assert p.probability == pytest.approx(stats.norm(r.mean, r.sigma_within).cdf(
        (2.5 ** r.transform["lambda"] - 1) / r.transform["lambda"]), rel=1e-12)


# ---------------------------------------------------------------- RF-04
def test_s010_rf_04_no_normal_lognormal(datos):
    """S010-RF-04: coincide con el re-ajuste lognormal de scipy (rel 1e-3)."""
    r = pccpy.capability_nonnormal(datos, lsl=1, usl=6, distribution="lognormal")
    s, loc, scale = stats.lognorm.fit(datos, floc=0)
    ref = stats.lognorm(s, loc, scale)
    assert r.probability(below=2.5).probability == pytest.approx(ref.cdf(2.5), rel=1e-3)
    assert r.probability(above=5).probability == pytest.approx(ref.sf(5), rel=1e-3)
    assert r.probability(between=(2, 4)).probability == pytest.approx(ref.cdf(4) - ref.cdf(2), rel=1e-3)


def test_s010_rf_04_usa_frozen_y_hereda(datos):
    """S010-RF-04: usa la distribución ajustada y hereda lsl/usl."""
    r = pccpy.capability_nonnormal(datos, lsl=1, usl=6, distribution="weibull")
    f = r.frozen
    assert r.probability(below=2.5).probability == pytest.approx(f.cdf(2.5), rel=1e-12)
    assert r.probability().probability == pytest.approx(f.cdf(1) + f.sf(6), rel=1e-12)


def test_s010_rf_04_sin_sigma_within(datos):
    """S010-RF-04: sigma='within' no existe en la distribución no normal."""
    r = pccpy.capability_nonnormal(datos, lsl=1, usl=6, distribution="weibull")
    with pytest.raises(ValueError, match="within"):
        r.probability(below=2, sigma="within")


# ---------------------------------------------------------------- RF-05
def test_s010_rf_05_medidas(normal):
    """S010-RF-05: ppm = 1e6·p, dpmo = ppm y dpu = oportunidades·p."""
    p = normal.probability(below=47, opportunities=3)
    assert isinstance(p, pccpy.ProbabilityResult)
    assert p.ppm == pytest.approx(1e6 * p.probability, rel=1e-12)
    assert p.dpmo == pytest.approx(p.ppm, rel=1e-12)
    assert p.dpu == pytest.approx(3 * p.probability, rel=1e-12)
    assert p.opportunities == 3
    assert normal.probability(below=47).dpu == pytest.approx(normal.probability(below=47).probability, rel=1e-12)


def test_s010_rf_05_between_sin_defecto(normal):
    """S010-RF-05: con between, dpmo y dpu no aplican."""
    p = normal.probability(between=(48, 52))
    assert p.event == "between"
    assert p.dpmo is None and p.dpu is None
    assert p.p_below is None and p.p_above is None


def test_s010_rf_05_partes_none(normal):
    """S010-RF-05: p_below/p_above son None si no hay esa parte."""
    assert normal.probability(below=47).p_above is None
    assert normal.probability(above=53).p_below is None


def test_s010_rf_05_to_frame_y_summary(normal):
    """S010-RF-05: to_frame (una fila por elemento, claves estables) y summary."""
    p = normal.probability(below=[45, 46, 47])
    df = p.to_frame(stable=True)
    assert len(df) == 3
    assert {"probability", "ppm", "dpmo", "dpu"} <= set(df.columns)
    assert len(p.to_frame()) == 3
    assert isinstance(p.summary(), str) and p.summary()
    assert "probability" not in set(p.to_frame().columns)  # cabeceras en el idioma activo


# ---------------------------------------------------------------- RF-06
def test_s010_rf_06_argumentos_invalidos(normal):
    """S010-RF-06: sigma, between y opportunities inválidos."""
    with pytest.raises(ValueError):
        normal.probability(below=47, sigma="otra")
    for malo in ((48,), (52, 48), 5, (1, 2, 3)):
        with pytest.raises(ValueError):
            normal.probability(between=malo)
    for malo in (0, -1, 1.5, "a"):
        with pytest.raises(ValueError):
            normal.probability(below=47, opportunities=malo)


def test_s010_rf_06_nan_e_inf(normal):
    """S010-RF-06: NaN es un error; ±inf es válido."""
    with pytest.raises(ValueError):
        normal.probability(below=float("nan"))
    with pytest.raises(ValueError):
        normal.probability(below=[1.0, float("nan")])
    assert normal.probability(below=np.inf).probability == 1.0
    assert normal.probability(above=np.inf).probability == 0.0
    assert normal.probability(below=-np.inf).probability == 0.0


def test_s010_rf_06_arreglos(normal):
    """S010-RF-06: elemento a elemento, difusión y errores de forma."""
    v = [44.0, 47.0, 50.0]
    p = normal.probability(below=v)
    assert np.shape(p.probability) == (3,)
    for i, a in enumerate(v):
        assert p.probability[i] == pytest.approx(normal.probability(below=a).probability, rel=1e-12)
    q = normal.probability(below=[44, 45], above=56)
    assert np.shape(q.probability) == (2,)
    assert q.probability[1] == pytest.approx(normal.probability(below=45, above=56).probability, rel=1e-12)
    b = normal.probability(between=([46, 47], 53))
    assert np.shape(b.probability) == (2,)
    assert np.ndim(normal.probability(below=47).probability) == 0
    with pytest.raises(ValueError):
        normal.probability(below=[])
    with pytest.raises(ValueError):
        normal.probability(below=[[1, 2], [3, 4]])
    with pytest.raises(ValueError):
        normal.probability(below=[1, 2, 3], above=[1, 2])
    with pytest.raises(ValueError):
        normal.probability(between=([48, 53], [52, 50]))  # a > b en un elemento


def test_s010_rf_06_between_igual_es_cero(normal):
    """S010-RF-06: between=(a, a) da 0."""
    assert normal.probability(between=(50, 50)).probability == 0.0


def test_s010_rf_06_sigma_cero():
    """S010-RF-06: con sigma 0 la probabilidad es un escalón (0,5 en la media)."""
    r = pccpy.capability_analysis(np.full(30, 10.0) + np.arange(30) * 0, lsl=9, usl=11, subgroup_size=1)
    r.sigma_overall = 0.0
    r.mean = 10.0
    assert r.probability(below=9.0).probability == 0.0
    assert r.probability(below=11.0).probability == 1.0
    assert r.probability(below=10.0).probability == 0.5
    assert r.probability(above=10.0).probability == 0.5
    assert r.probability(above=9.0).probability == 1.0


# ---------------------------------------------------------------- RF-07
def test_s010_rf_07_coherencia_normal(normal):
    """S010-RF-07: reproduce ppm_overall, ppm_within y dpmo en los límites."""
    p = normal.probability()
    assert p.p_below * 1e6 == pytest.approx(normal.ppm_overall[0], rel=1e-9)
    assert p.p_above * 1e6 == pytest.approx(normal.ppm_overall[1], rel=1e-9)
    assert p.ppm == pytest.approx(normal.ppm_overall[2], rel=1e-9)
    assert p.dpmo == pytest.approx(normal.dpmo, rel=1e-9)
    w = normal.probability(sigma="within")
    assert w.p_below * 1e6 == pytest.approx(normal.ppm_within[0], rel=1e-9)
    assert w.ppm == pytest.approx(normal.ppm_within[2], rel=1e-9)


def test_s010_rf_07_coherencia_no_normal(datos):
    """S010-RF-07: en no normal reproduce ppm_expected."""
    r = pccpy.capability_nonnormal(datos, lsl=1, usl=6, distribution="lognormal")
    p = r.probability()
    assert p.p_below * 1e6 == pytest.approx(r.ppm_expected[0], rel=1e-9)
    assert p.p_above * 1e6 == pytest.approx(r.ppm_expected[1], rel=1e-9)
    assert p.ppm == pytest.approx(r.ppm_expected[2], rel=1e-9)


def test_s010_rf_07_coherencia_transformacion(datos):
    """S010-RF-07: con transformación reproduce ppm_overall con lsl y usl originales."""
    r = pccpy.capability_boxcox(datos, lsl=1, usl=6)
    p = r.probability()
    assert p.ppm == pytest.approx(r.ppm_overall[2], rel=1e-9)
    assert p.p_below * 1e6 == pytest.approx(r.ppm_overall[0], rel=1e-9)


# ---------------------------------------------------------------- RF-08
def test_s010_rf_08_exportacion_y_validacion():
    """S010-RF-08: ProbabilityResult exportado y la comprobación de validación pasa (62 en total)."""
    from pccpy.validation import run_validation

    assert "ProbabilityResult" in pccpy.__all__
    assert pccpy.ProbabilityResult.__doc__
    informe = run_validation()
    assert len(informe.checks) == 62
    assert all(c.passed for c in informe.checks if c.id == "probabilidad-capacidad")
    assert any(c.id == "probabilidad-capacidad" for c in informe.checks)


def test_s010_rf_08_ejemplo_de_la_guia():
    """S010-RF-08: el ejemplo de la guía de capacidad se ejecuta tal como está escrito."""
    import re
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[1] / "docs" / "source" / "capacidad_indices.md").read_text(encoding="utf-8")
    bloques = [b for b in re.findall(r"```python\n(.*?)```", texto, re.S) if "res.probability(" in b]
    assert bloques
    for b in bloques:
        exec(b, {})


def test_s010_rf_08_textos_en_ingles():
    """S010-RF-08: los mensajes y las cabeceras se traducen."""
    with pccpy.language("en"):
        r = pccpy.capability_analysis(np.random.default_rng(1).normal(50, 2, 60), lsl=44, usl=56, subgroup_size=1)
        with pytest.raises(ValueError, match="sigma"):
            r.probability(below=1, sigma="x")
        assert "Probability" in r.probability(below=47).to_frame().columns
