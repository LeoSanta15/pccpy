"""Pruebas de la especificación 012: los datos con clave de los resultados de las cartas están en inglés.

Las equivalencias están escritas aquí aparte (referencia independiente), no leídas del código. Con el idioma español, lo que
muestra ``summary()`` no cambia (``tests/golden/i18n_es.json``).
"""
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pytest

import pccpy

RAIZ = Path(__file__).resolve().parents[1]

# Claves en español de 0.15.4 y su equivalente en inglés (tabla de la especificación 012).
ES_EN = {
    "media": "mean", "centro": "center", "objetivo": "target", "distribución": "distribution", "forma": "shape",
    "escala": "scale", "longitud": "length", "peso": "weight", "pesos": "weights", "reinicio": "reset",
    "subgrupos": "subgroups", "tamaño": "size", "n_subgrupo": "subgroup_size", "MR_prom": "mr_mean", "alfa": "alpha",
    "corridas": "runs", "fase": "phase", "método": "method", "n_puntos": "n_points", "puntos": "points",
    "partes": "parts", "sigma_conocida": "sigma_known", "sigma_dentro": "sigma_within", "sigma_entre": "sigma_between",
    "sigma_entre_dentro": "sigma_between_within", "sigma_mín": "sigma_min", "sigma_máx": "sigma_max", "LCS": "ucl",
}


def _datos():
    rng = np.random.default_rng(0)
    return {
        "x": rng.normal(10, 1, 60), "g": rng.normal(10, 1, (20, 5)), "c": rng.poisson(5, 30), "n": np.full(30, 100),
        "d": rng.binomial(100, 0.05, 30), "mv": rng.multivariate_normal([0, 0, 0], np.eye(3), 60),
        "pos": rng.lognormal(0, 0.3, (60, 3)), "gv": rng.normal(size=(60, 3)),
        "geom": rng.geometric(0.05, 30) - 1, "weib": rng.weibull(1.5, 30) * 10,
    }


def _cartas():
    """Una carta de cada tipo con las claves que debe tener su ``params[0]`` (en inglés) y su ``kind``."""
    d = _datos()
    x, g, c, n, dd, mv = d["x"], d["g"], d["c"], d["n"], d["d"], d["mv"]
    partes = ["A"] * 30 + ["B"] * 30
    ceros, uno = np.zeros(3), np.eye(3)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        casos = {
            "imr": (pccpy.imr_chart(x), {"mean", "sigma", "mr_mean", "n"}),
            "xbar_r": (pccpy.xbar_r_chart(g), {"mean", "sigma", "subgroups", "size"}),
            "xbar_s": (pccpy.xbar_s_chart(g), {"mean", "sigma", "subgroups", "size"}),
            "p": (pccpy.p_chart(dd, n), {"center", "n_points"}),
            "np": (pccpy.np_chart(dd, n), {"center", "n_points"}),
            "c": (pccpy.c_chart(c), {"center", "n_points"}),
            "u": (pccpy.u_chart(c, n), {"center", "n_points"}),
            "laney_p": (pccpy.laney_p_chart(dd, n), {"center", "n_points", "sigma_z"}),
            "laney_u": (pccpy.laney_u_chart(c, n), {"center", "n_points", "sigma_z"}),
            "ewma": (pccpy.ewma_chart(x), {"k", "subgroup_size", "target", "weight", "sigma"}),
            "cusum": (pccpy.cusum_chart(x), {"h", "headstart", "k", "subgroup_size", "target", "sigma"}),
            "ma": (pccpy.ma_chart(x), {"k", "length", "mean", "subgroup_size", "sigma"}),
            "zmr": (pccpy.zmr_chart(x, partes), {"method", "parts", "runs", "n", "sigma"}),
            "imr_rs": (pccpy.imr_rs_chart(g), {"mean", "sigma_within", "sigma_between", "sigma_between_within", "subgroups"}),
            "zone": (pccpy.zone_chart(x, mu=10.0, sigma=1.0), {"mean", "n", "weights", "reset", "sigma"}),
            "g": (pccpy.g_chart(d["geom"]), {"mean", "n", "p"}),
            "t": (pccpy.t_chart(d["weib"]), {"distribution", "scale", "shape", "n"}),
            "t2": (pccpy.t2_chart(mv), {"alpha", "phase", "points", "size", "variables"}),
            "t2_bc": (pccpy.t2_chart(d["pos"], boxcox=True), {"alpha", "phase", "points", "size", "variables", "lambda_boxcox"}),
            "gv": (pccpy.generalized_variance_chart(d["gv"], subgroup_size=6),
                   {"sigma_known", "subgroups", "size", "variables", "|S|"}),
            "mewma": (pccpy.mewma_chart(mv, mu=ceros, cov=uno), {"ARL", "ucl", "weight", "points", "size", "variables"}),
            "mcusum": (pccpy.mcusum_chart(mv, mu=ceros, cov=uno), {"ARL", "ucl", "k", "points", "size", "variables"}),
            "ewma_p": (pccpy.ewma_p_chart(dd, n), {"center", "k", "weight"}),
            "ewma_c": (pccpy.ewma_c_chart(c), {"center", "k", "weight"}),
            "ewma_u": (pccpy.ewma_u_chart(c, n), {"center", "k", "weight"}),
            "cusum_p": (pccpy.cusum_p_chart(dd, n), {"center", "h", "k"}),
            "cusum_c": (pccpy.cusum_c_chart(c), {"center", "h", "k"}),
            "cusum_u": (pccpy.cusum_u_chart(c, n), {"center", "h", "k"}),
        }
    return casos


CARTAS = _cartas()


# ---------------------------------------------------------------- RF-01
@pytest.mark.parametrize("nombre", sorted(CARTAS))
def test_s012_rf_01_las_claves_de_params_estan_en_ingles(nombre):
    """S012-RF-01: ``params[0]`` tiene exactamente las claves canónicas en inglés (más ``stage``)."""
    carta, esperadas = CARTAS[nombre]
    assert set(carta.params[0]) == esperadas | {"stage"}


def test_s012_rf_01_las_claves_no_dependen_del_idioma():
    """S012-RF-01: con el idioma inglés o el español, las claves son las mismas."""
    d = _datos()
    with pccpy.language("en"):
        en = set(pccpy.xbar_r_chart(d["g"]).params[0])
    with pccpy.language("es"):
        es = set(pccpy.xbar_r_chart(d["g"]).params[0])
    assert en == es == {"mean", "sigma", "subgroups", "size", "stage"}


def test_s012_rf_01_zmr_con_sigma_historica():
    """S012-RF-01: método ``historical`` y rango de sigmas con ``sigma_min`` y ``sigma_max``."""
    x = _datos()["x"]
    carta = pccpy.zmr_chart(x, ["A"] * 30 + ["B"] * 30, mu={"A": 10.0, "B": 10.0}, sigma={"A": 1.0, "B": 2.0})
    prm = carta.params[0]
    assert prm["method"] == "historical"
    assert prm["sigma_min"] == 1.0 and prm["sigma_max"] == 2.0


def test_s012_rf_01_los_valores_numericos_no_cambian():
    """S012-RF-01: mismos valores que antes, ahora con la clave nueva."""
    x = _datos()["x"]
    prm = pccpy.imr_chart(x).params[0]
    assert prm["mean"] == pytest.approx(float(np.mean(x)), rel=1e-12)
    mr = np.abs(np.diff(x))
    assert prm["mr_mean"] == pytest.approx(float(mr.mean()), rel=1e-12)
    assert prm["sigma"] == pytest.approx(float(mr.mean()) / 1.1283791670955126, rel=1e-9)


# ---------------------------------------------------------------- RF-02
@pytest.mark.parametrize("nombre", sorted(CARTAS))
def test_s012_rf_02_ninguna_clave_en_espanol(nombre):
    """S012-RF-02: ninguna carta guarda claves de la tabla española ni con acentos."""
    carta, _ = CARTAS[nombre]
    for prm in carta.params:
        assert not set(prm) & set(ES_EN), sorted(set(prm) & set(ES_EN))
        assert all(k.isascii() for k in prm)


def test_s012_rf_02_las_claves_espanolas_dan_keyerror():
    """S012-RF-02: sin alias, la clave española no existe."""
    carta = pccpy.imr_chart(_datos()["x"])
    assert carta.params[0]["mean"]
    for vieja in ("media", "MR_prom"):
        with pytest.raises(KeyError):
            carta.params[0][vieja]
    assert "media" not in carta.params[0] and carta.params[0].get("media") is None


# ---------------------------------------------------------------- RF-03
def test_s012_rf_03_la_carta_de_zona_y_la_de_varianza_generalizada():
    """S012-RF-03: ``kind`` y paneles en inglés; los nombres viejos dan ``KeyError``."""
    d = _datos()
    zona = pccpy.zone_chart(d["x"], mu=10.0, sigma=1.0)
    assert zona.kind == "Zone" and [p.name for p in zona.panels] == ["Zone", "Score"]
    assert zona["Zone"] is zona.panels[0] and zona["Score"] is zona.panels[1]
    for viejo in ("Zona", "Puntaje"):
        with pytest.raises(KeyError):
            zona[viejo]
    gv = pccpy.generalized_variance_chart(d["gv"], subgroup_size=6)
    assert gv.kind == "Generalized variance"


def test_s012_rf_03_el_resumen_y_el_grafico_siguen_traducidos():
    """S012-RF-03: «Zona» en español y «Zone» en inglés al mostrarse, aunque el ``kind`` sea el mismo."""
    zona = pccpy.zone_chart(_datos()["x"], mu=10.0, sigma=1.0)
    with pccpy.language("es"):
        assert zona.summary().splitlines()[0] == "Carta de control Zona"
    with pccpy.language("en"):
        assert zona.summary().splitlines()[0] == "Control chart Zone"
    gv = pccpy.generalized_variance_chart(_datos()["gv"], subgroup_size=6)
    with pccpy.language("es"):
        assert gv.summary().splitlines()[0] == "Carta de control Varianza generalizada"
    with pccpy.language("en"):
        assert gv.summary().splitlines()[0] == "Control chart Generalized variance"


# ---------------------------------------------------------------- RF-04
def test_s012_rf_04_lo_que_se_muestra_depende_del_idioma():
    """S012-RF-04: ``Parameters: mean=…`` en inglés y ``Parámetros: media=…`` en español, de las mismas claves."""
    carta = pccpy.xbar_r_chart(_datos()["g"])
    with pccpy.language("es"):
        linea = carta.summary().splitlines()[1]
    assert "media=" in linea and "tamaño=" in linea and "subgrupos=" in linea
    with pccpy.language("en"):
        linea = carta.summary().splitlines()[1]
    assert "mean=" in linea and "size=" in linea and "subgroups=" in linea


def test_s012_rf_04_el_metodo_historical_se_muestra_traducido():
    """S012-RF-04: el valor ``historical`` se muestra como «histórica» en español."""
    carta = pccpy.zmr_chart(_datos()["x"], ["A"] * 30 + ["B"] * 30, mu={"A": 10.0, "B": 10.0}, sigma={"A": 1.0, "B": 2.0})
    with pccpy.language("es"):
        assert "método=histórica" in carta.summary()
    with pccpy.language("en"):
        assert "method=historical" in carta.summary()


# ---------------------------------------------------------------- RF-05
_TOKENS_ES = sorted(ES_EN, key=len, reverse=True)


def test_s012_rf_05_el_codigo_no_usa_claves_espanolas():
    """S012-RF-05: ``src/`` solo nombra las claves españolas en el diccionario que traduce lo que se muestra."""
    alternativas = "|".join(re.escape(k) for k in _TOKENS_ES)
    patron = re.compile(rf"""["'](?:{alternativas})["']""")
    hallazgos = {}
    for ruta in (RAIZ / "src" / "pccpy").rglob("*.py"):
        if ruta.name == "results.py":
            continue
        for i, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            if patron.search(linea) and "N_(" not in linea and "tr(" not in linea:  # tr()/N_(): textos que se muestran
                hallazgos[f"{ruta.name}:{i}"] = linea.strip()[:90]
    assert hallazgos == {}


# ---------------------------------------------------------------- RF-06
@pytest.mark.parametrize("archivo", ["fase1_0_15_4_imr.json", "fase1_0_15_4_xbar_r.json"])
def test_s012_rf_06_los_archivos_de_fase_i_guardados_con_0_15_se_leen(archivo):
    """S012-RF-06: un archivo escrito con 0.15.x (fixture) se lee y da los mismos límites; ``phase2`` funciona."""
    ruta = RAIZ / "tests" / "data" / archivo
    guardado = json.loads(ruta.read_text(encoding="utf-8"))
    r = pccpy.PhaseOneResult.from_json(ruta)
    assert r.limits == pytest.approx(guardado["limits"], rel=1e-12)
    nuevos = np.random.default_rng(5).normal(guardado["limits"]["mu"], guardado["limits"]["sigma"], (30, 5) if "xbar" in archivo else 30)
    assert r.phase2(nuevos).kind in ("I-MR", "Xbar-R")


def test_s012_rf_06_los_archivos_nuevos_conservan_el_formato():
    """S012-RF-06: el formato guardado no cambia (claves de límites ya inglesas, mismo ``schema``)."""
    ruta = RAIZ / "tests" / "data" / "fase1_0_15_4_imr.json"
    viejo = json.loads(ruta.read_text(encoding="utf-8"))
    x = np.random.default_rng(0).normal(10, 1, 60)
    nuevo = pccpy.phase_one(pccpy.imr_chart, x).to_dict()
    assert nuevo["schema"] == viejo["schema"]
    assert set(nuevo["limits"]) == set(viejo["limits"]) == {"mu", "sigma"}
    assert nuevo["limits"] == pytest.approx(viejo["limits"], rel=1e-12)


# ---------------------------------------------------------------- RF-07
def test_s012_rf_07_la_documentacion_y_los_ejemplos_usan_las_claves_nuevas():
    """S012-RF-07: README, guías y ejemplos no leen ``params`` con claves españolas."""
    alternativas = "|".join(re.escape(k) for k in _TOKENS_ES)
    patron = re.compile(rf"""params(?:\[\d+\])?\[\s*["'](?:{alternativas})["']\s*\]""")
    archivos = [RAIZ / "README.md", RAIZ / "README_en.md", *(RAIZ / "docs" / "source").rglob("*.md"),
                *(RAIZ / "docs" / "source").rglob("*.rst"), *(RAIZ / "examples").glob("*.py")]
    como_texto = re.compile(rf"""['"](?:{alternativas})['"]\s*(?::|y\b|and\b|\))""")  # {'media': …} o «'media' y 'sigma'»
    hallazgos = {}
    for ruta in archivos:
        for i, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            if patron.search(linea) or como_texto.search(linea):
                hallazgos[f"{ruta.relative_to(RAIZ)}:{i}"] = linea.strip()[:80]
    assert hallazgos == {}
