"""diagnose: por qué no es normal (atípicos, asimetría, forma) y recomendación según la causa."""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

import pccpy as pp

RNG = np.random.default_rng(0)
NORMAL = RNG.normal(50, 2, 80)
LOGNORMAL = np.random.default_rng(2).lognormal(1, 0.8, 80)
NEGATIVA = -np.random.default_rng(3).gamma(2, 1, 80) + 1  # asimétrica y con valores ≤ 0
CON_ATIPICOS = np.append(np.random.default_rng(5).normal(50, 2, 80), [75.0, 78.0, 80.0])
UNIFORME = np.random.default_rng(6).uniform(0, 1, 80)


def _specs(x):
    """Límites holgados; positivos si los datos lo son (Box-Cox transforma también los límites)."""
    lsl = float(x.min()) - 1
    return dict(lsl=max(lsl, 0.01) if x.min() > 0 else lsl, usl=float(x.max()) + 1)


def _ejecuta(d, x):
    """Ejecuta el fragmento recomendado y comprueba que devuelve un resultado."""
    entorno = {"datos": x}
    exec(d.recommended_snippet, entorno)  # noqa: S102 - el fragmento lo genera la propia biblioteca
    return entorno["resultado"]


def test_datos_normales_no_cambian():
    d = pp.diagnose(NORMAL, **_specs(NORMAL))
    assert d.non_normal_reason == "" and d.transform_normalizes is None and d.best_distribution is None
    assert d.recommended_function == "capability_analysis"
    assert "Por qué no es normal" not in d.summary()
    assert "non_normal_reason" not in d.to_frame(stable=True).index


def test_asimetria_con_datos_positivos_boxcox_normaliza():
    d = pp.diagnose(LOGNORMAL, **_specs(LOGNORMAL))
    assert not d.is_normal and d.non_normal_reason == "skewed" and d.transform_normalizes is True
    # referencia independiente: Box-Cox con lambda de máxima verosimilitud y prueba de normalidad
    y, _ = stats.boxcox(LOGNORMAL)
    assert stats.normaltest(y)[1] > 0.05
    assert d.recommended_function == "capability_boxcox"
    assert type(_ejecuta(d, LOGNORMAL)).__name__ == "CapabilityResult"


def test_mejor_distribucion_coincide_con_el_aic_calculado_aparte():
    d = pp.diagnose(LOGNORMAL)
    aic = {}
    for nombre, dist in (("normal", stats.norm), ("lognormal", stats.lognorm), ("weibull", stats.weibull_min),
                         ("gamma", stats.gamma), ("loglogistic", stats.fisk)):
        p = dist.fit(LOGNORMAL) if nombre == "normal" else dist.fit(LOGNORMAL, floc=0)
        k = len(p) - (0 if nombre == "normal" else 1)
        aic[nombre] = 2 * k - 2 * np.sum(dist(*p).logpdf(LOGNORMAL))
    mejor = min((k for k in aic if k != "normal"), key=aic.get)
    assert d.best_distribution == (mejor if aic[mejor] < aic["normal"] - 2 else None)


def test_asimetria_con_valores_no_positivos_recomienda_distribucion_sin_boxcox():
    d = pp.diagnose(NEGATIVA, **_specs(NEGATIVA))
    assert d.non_normal_reason == "skewed" and d.transform_normalizes is None  # Box-Cox no aplica
    assert d.recommended_function == "capability_nonnormal"
    assert d.best_distribution in ("logistic", "largest_extreme", "smallest_extreme")
    assert f"distribution={d.best_distribution!r}" in d.recommended_snippet
    assert type(_ejecuta(d, NEGATIVA)).__name__ == "NonNormalCapabilityResult"


def test_atipicos_explican_la_no_normalidad():
    d = pp.diagnose(CON_ATIPICOS, **_specs(CON_ATIPICOS))
    sin = CON_ATIPICOS[[i for i in range(len(CON_ATIPICOS)) if i not in d.outlier_indices]]
    assert stats.normaltest(sin)[1] > 0.05  # referencia: sin los atípicos los datos son normales
    assert d.non_normal_reason == "outliers" and d.recommended_function == "capability_analysis"
    assert any("valores atípicos" in i and "investiga" in i for i in d.issues)


def test_forma_sin_modelo_claramente_mejor_avisa_con_cautela():
    d = pp.diagnose(UNIFORME, **_specs(UNIFORME))
    assert d.non_normal_reason == "shape" and d.best_distribution is None
    assert d.recommended_function == "capability_analysis"
    assert any("cautela" in i for i in d.issues)


def test_sin_especificaciones_avisa_de_los_limites_de_imr():
    d = pp.diagnose(LOGNORMAL)
    assert d.recommended_function == "imr_chart"
    assert any("I-MR" in i and "asimetría" in i for i in d.issues)
    assert not any("I-MR" in i for i in pp.diagnose(NORMAL).issues)


def test_con_tendencia_manda_la_tendencia():
    x = np.arange(60.0) ** 1.3 + 1
    assert pp.diagnose(x, **_specs(x)).recommended_function == "run_chart"


def test_pocos_datos_no_estudian_la_forma():
    d = pp.diagnose([1.0, 2.0, 3.5, 4.0, 5.0])
    assert d.non_normal_reason == "" and d.is_normal


def test_frame_resumen_y_traduccion():
    d = pp.diagnose(LOGNORMAL, **_specs(LOGNORMAL))
    estable = d.to_frame(stable=True)
    assert estable.loc["non_normal_reason", "value"] == "skewed"
    assert "Por qué no es normal" in d.summary() and "asimetría" in d.summary()
    with pp.language("en"):
        assert "Why it is not normal" in d.summary() and "skewness" in d.summary().lower()


@pytest.mark.parametrize("x", [NORMAL, LOGNORMAL, NEGATIVA, CON_ATIPICOS, UNIFORME])
def test_el_fragmento_recomendado_siempre_se_ejecuta(x):
    d = pp.diagnose(x, **_specs(x))
    exec(d.recommended_snippet, {"datos": x})  # noqa: S102


def test_clasificacion_de_la_causa_es_fiable_en_simulacion():
    """La causa es una heurística: se mide su acierto con semillas fijas (≥ 90 % en cada caso)."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        asimetricos = sum(
            pp.diagnose(np.random.default_rng(s).lognormal(1, 0.8, 80)).non_normal_reason == "skewed" for s in range(100))
        contaminados = sum(
            pp.diagnose(np.append(np.random.default_rng(s).normal(50, 2, 80), [75.0, 78.0, 80.0])).non_normal_reason
            == "outliers" for s in range(100))
    assert asimetricos >= 90 and contaminados >= 90


def test_boxcox_no_se_recomienda_si_los_limites_no_son_positivos():
    """Los datos son positivos y Box-Cox los normaliza, pero con LEI ≤ 0 capability_boxcox fallaría."""
    d = pp.diagnose(LOGNORMAL, lsl=-1.0, usl=float(LOGNORMAL.max()) + 1)
    assert d.transform_normalizes is True and d.recommended_function != "capability_boxcox"
    assert any("Box-Cox" in i and "positivos" in i for i in d.issues)
    assert d.recommended_function == ("capability_nonnormal" if d.best_distribution else "capability_analysis")
    exec(d.recommended_snippet, {"datos": LOGNORMAL})  # noqa: S102


# ── Yeo-Johnson y cartas ──────────────────────────────────────────────────────

def _mixta(semilla):
    r = np.random.default_rng(semilla)
    return np.concatenate([-r.gamma(2, 1, 30), r.gamma(2, 1, 70)])


def test_yeo_johnson_se_recomienda_si_box_cox_no_aplica_y_no_hay_mejor_distribucion():
    x = _mixta(28)  # valores negativos: Box-Cox no aplica; ninguna distribución gana a la normal por AIC
    d = pp.diagnose(x, **_specs(x))
    assert d.transform_normalizes is None and d.best_distribution is None and d.yeo_johnson_normalizes is True
    assert d.recommended_function == "capability_analysis" and "transform='yeo-johnson'" in d.recommended_snippet
    y, _ = stats.yeojohnson(x)
    assert stats.normaltest(y)[1] > 0.05  # referencia independiente
    r = _ejecuta(d, x)
    assert r.transform["method"] == "yeo-johnson"
    assert not any("cautela" in i for i in d.issues)  # ya hay una transformación que normaliza


@pytest.mark.parametrize("x, metodo", [(LOGNORMAL, "boxcox"), (NEGATIVA, "yeo-johnson")])
def test_sin_especificaciones_recomienda_imr_con_transformacion(x, metodo):
    d = pp.diagnose(x)
    assert d.recommended_function == "imr_chart" and f"transform={metodo!r}" in d.recommended_snippet
    assert type(_ejecuta(d, x)).__name__ == "ControlChart"


def test_datos_normales_siguen_recomendando_imr_sin_transformacion():
    d = pp.diagnose(NORMAL)
    assert "transform" not in d.recommended_snippet and d.yeo_johnson_normalizes is None


def test_frame_y_resumen_incluyen_yeo_johnson():
    d = pp.diagnose(NEGATIVA, **_specs(NEGATIVA))
    assert bool(d.to_frame(stable=True).loc["yeo_johnson_normalizes", "value"]) is True
    assert "Yeo-Johnson normaliza: sí" in d.summary()
    with pp.language("en"):
        assert "Yeo-Johnson normalizes: yes" in d.summary()
