"""Ejes con fechas (y etiquetas en general): las cartas conservan el índice de fechas/texto de la entrada."""
from __future__ import annotations

import inspect

import matplotlib
import numpy as np
import pandas as pd
import pytest

import pccpy as pp

matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def _cerrar_figuras():
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


def _serie(n=40, desplazar=True, inicio="2026-03-01", freq="D", semilla=1):
    rng = np.random.default_rng(semilla)
    x = rng.normal(10, 1, n)
    if desplazar:
        x[n - 10:] += 3
    return pd.Series(x, index=pd.date_range(inicio, periods=n, freq=freq))


# ── detección y adjuntado ────────────────────────────────────────────────────

def test_una_serie_con_fechas_conserva_las_fechas():
    s = _serie()
    c = pp.imr_chart(s, tests=(1, 2))
    assert c.labels is not None and len(c.labels) == 40
    assert pd.Timestamp(c.labels[0]) == pd.Timestamp("2026-03-01") and pd.Timestamp(c.labels[-1]) == pd.Timestamp("2026-04-09")


def test_los_numeros_de_la_carta_no_cambian_con_etiquetas():
    s = _serie()
    con, sin = pp.imr_chart(s, tests=(1, 2)), pp.imr_chart(s.to_numpy(), tests=(1, 2))
    for a, b in zip(con.panels, sin.panels):
        np.testing.assert_array_equal(a.values, b.values)
        np.testing.assert_array_equal(a.ucl, b.ucl)
        assert {t: v.tolist() for t, v in a.violations.items()} == {t: v.tolist() for t, v in b.violations.items()}


@pytest.mark.parametrize("entrada", [
    np.arange(30.0) % 7, pd.Series(np.arange(30.0) % 7), pd.Series(np.arange(30.0) % 7, index=np.arange(30) + 5),
])
def test_sin_fechas_ni_texto_no_hay_etiquetas_y_la_tabla_no_cambia(entrada):
    c = pp.imr_chart(entrada)
    assert c.labels is None
    assert list(c.to_frame(stable=True).columns[:2]) == ["point", "stage"]
    assert "label" not in c.violations(stable=True).columns


def test_un_indice_de_texto_tambien_sirve_de_etiqueta():
    s = pd.Series(np.random.default_rng(3).normal(size=12), index=[f"lote{i:02d}" for i in range(12)])
    assert list(pp.imr_chart(s).labels) == [f"lote{i:02d}" for i in range(12)]


def test_con_subgroup_size_la_etiqueta_es_la_de_la_primera_observacion_del_subgrupo():
    s = _serie(60, freq="h")
    c = pp.xbar_r_chart(s, subgroup_size=5)
    assert len(c.labels) == 12 and pd.Timestamp(c.labels[1]) == s.index[5]


def test_un_dataframe_ancho_usa_su_indice_como_etiqueta_de_subgrupo():
    rng = np.random.default_rng(4)
    df = pd.DataFrame(rng.normal(10, 1, (25, 4)), index=pd.date_range("2026-01-01", periods=25, freq="D"))
    c = pp.xbar_s_chart(df)
    assert len(c.labels) == 25 and pd.Timestamp(c.labels[3]) == pd.Timestamp("2026-01-04")


def test_en_formato_largo_las_etiquetas_son_los_subgrupos_en_orden_de_aparicion():
    rng = np.random.default_rng(5)
    dias = np.repeat(pd.date_range("2026-02-01", periods=10), 4)
    df = pd.DataFrame({"dia": dias, "medida": rng.normal(size=40)})
    c = pp.xbar_r_chart(df, subgroup="dia", value="medida")
    assert len(c.labels) == 10 and pd.Timestamp(c.labels[0]) == pd.Timestamp("2026-02-01")


def test_los_identificadores_de_subgrupo_de_texto_o_fecha_son_etiquetas():
    rng = np.random.default_rng(6)
    ids = np.repeat(["A", "B", "C", "D", "E", "F"], 5)
    c = pp.xbar_r_chart(rng.normal(size=30), subgroup=ids)
    assert list(c.labels) == list("ABCDEF")


def test_las_cartas_de_atributos_y_las_multivariadas_tambien_las_conservan():
    idx = pd.date_range("2026-01-01", periods=30, freq="D")
    d = pd.Series(np.random.default_rng(7).binomial(100, 0.05, 30), index=idx)
    assert len(pp.p_chart(d, n=100).labels) == 30
    assert len(pp.c_chart(d).labels) == 30
    assert len(pp.ewma_chart(_serie()).labels) == 40
    m = pd.DataFrame(np.random.default_rng(8).normal(size=(30, 3)), index=idx, columns=list("abc"))
    assert len(pp.t2_chart(m).labels) == 30


def test_si_se_descartan_valores_no_finitos_no_se_adjuntan_etiquetas_en_vez_de_desalinearlas():
    s = _serie()
    s.iloc[5] = np.nan
    with pytest.warns(UserWarning):
        c = pp.imr_chart(s)
    assert c.labels is None


def test_las_funciones_decoradas_conservan_su_firma_y_su_documentacion():
    assert "span" in inspect.signature(pp.imr_chart).parameters
    assert "Carta de valores individuales" in (pp.imr_chart.__doc__ or "")


# ── tablas y resumen ─────────────────────────────────────────────────────────

def test_to_frame_y_violations_incluyen_la_etiqueta():
    c = pp.imr_chart(_serie(), tests=(1, 2))
    assert "etiqueta" in c.to_frame().columns and "etiqueta" in c.violations().columns
    f = c.to_frame(stable=True)
    assert list(f.columns[:3]) == ["point", "label", "stage"]
    assert pd.Timestamp(f["label"].iloc[0]) == pd.Timestamp("2026-03-01")
    v = c.violations(stable=True)
    assert pd.Timestamp(v["label"].iloc[0]) == c.labels[v["point"].iloc[0] - 1]


def test_el_resumen_muestra_la_fecha_junto_al_punto():
    resumen = pp.imr_chart(_serie(), tests=(1, 2)).summary()
    assert "punto 40 (2026-04-09)" in resumen
    with pp.language("en"):
        assert "point 40 (2026-04-09)" in pp.imr_chart(_serie(), tests=(1, 2)).summary()


def test_con_horas_la_etiqueta_incluye_la_hora():
    s = _serie(30, freq="90min")
    resumen = pp.imr_chart(s, tests=(1, 2, 3, 4, 5, 6, 7, 8)).summary()
    assert "(2026-03-" in resumen and ":" in resumen.split("(2026-03-")[1].split(")")[0]


# ── with_labels ──────────────────────────────────────────────────────────────

def test_with_labels_asocia_etiquetas_a_cualquier_carta_y_valida_la_longitud():
    x = np.random.default_rng(9).normal(size=15)
    c = pp.imr_chart(x).with_labels([f"turno {i}" for i in range(15)])
    assert c.labels[3] == "turno 3" and c.to_frame(stable=True)["label"].iloc[3] == "turno 3"
    with pytest.raises(ValueError, match="una etiqueta por cada punto graficado"):
        pp.imr_chart(x).with_labels(["a", "b"])
    with pp.language("en"), pytest.raises(ValueError, match="one label per plotted point"):
        pp.imr_chart(x).with_labels(["a", "b"])


# ── gráfico ──────────────────────────────────────────────────────────────────

def _marcas(fig):
    eje = fig.axes[-1]
    return [t.get_text() for t in eje.get_xticklabels()], eje.get_xlabel()


def test_el_grafico_rotula_el_eje_x_con_las_fechas():
    fig = pp.imr_chart(_serie(), tests=(1,)).plot()
    textos, xlabel = _marcas(fig)
    assert xlabel == "Fecha" and textos[0] == "2026-03-01" and textos[-1] == "2026-04-09" and len(textos) <= 8


def test_el_grafico_en_ingles_dice_date():
    with pp.language("en"):
        assert _marcas(pp.imr_chart(_serie()).plot())[1] == "Date"


def test_con_horas_las_marcas_muestran_la_hora():
    textos, _ = _marcas(pp.imr_chart(_serie(30, freq="h")).plot())
    assert textos[0] == "00:00" and all(":" in t for t in textos)


def test_con_etiquetas_de_texto_se_conserva_la_etiqueta_del_eje():
    s = pd.Series(np.random.default_rng(3).normal(size=12), index=[f"L{i:02d}" for i in range(12)])
    textos, xlabel = _marcas(pp.imr_chart(s).plot())
    assert xlabel == "Observación" and textos[0] == "L00"


def test_sin_etiquetas_el_grafico_no_cambia():
    textos, xlabel = _marcas(pp.imr_chart(_serie().to_numpy()).plot())
    assert xlabel == "Observación" and textos and not any("2026" in t for t in textos)


def test_el_sixpack_y_save_plot_siguen_funcionando_con_fechas(tmp_path):
    c = pp.imr_chart(_serie())
    c.save_plot(str(tmp_path / "x.png"))
    assert (tmp_path / "x.png").stat().st_size > 1000
