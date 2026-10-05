"""Corpus determinista de resultados para comprobar los textos de ``summary()`` y ``to_frame()`` en varios idiomas.

Cada entrada es una función sin argumentos que devuelve un objeto con ``summary()`` y/o ``to_frame()`` (o un ``str``).
Las semillas son fijas: la misma entrada produce siempre el mismo resultado.
"""
from __future__ import annotations

import re
import warnings

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import pccpy as pp


def _rng(semilla: int = 7) -> np.random.Generator:
    return np.random.default_rng(semilla)


def _normales(n=60, mu=50.0, sd=2.0, semilla=7):
    return _rng(semilla).normal(mu, sd, n)


def _con_atipico(n=40, semilla=3):
    x = _rng(semilla).normal(10, 1, n)
    x[7] = 17.0
    x[25] = 3.5
    return x


def _subgrupos(filas=25, columnas=5, semilla=11):
    m = _rng(semilla).normal(10, 1, (filas, columnas))
    m[4] += 2.5
    return m


def _msa_datos(semilla=0, partes=10, operadores=3, replicas=2):
    r = _rng(semilla)
    pe, oe = r.normal(0, 2.0, partes), r.normal(0, 0.3, operadores)
    datos = np.array([pe[p] + oe[o] + r.normal(0, 0.5, replicas) for p in range(partes) for o in range(operadores)]).ravel()
    return datos, partes, operadores, replicas


def _atributos(semilla=5):
    r = _rng(semilla)
    n = np.full(25, 100)
    d = r.binomial(100, 0.05, 25)
    d[10] = 20
    return d, n


def _conteos(semilla=5):
    c = _rng(semilla).poisson(4, 30)
    c[12] = 15
    return c


def _desde_df_atributos():
    r = _rng(2)
    verdad = r.integers(0, 2, 30)
    cols = {}
    for op in ("A", "B", "C"):
        for rep in (1, 2):
            ruido = r.random(30) < 0.1
            cols[f"{op}{rep}"] = np.where(ruido, 1 - verdad, verdad)
    return pd.DataFrame(cols), pd.Series(verdad)


def entradas() -> dict:
    """nombre → función que construye el objeto."""
    d: dict = {}

    # diagnose
    d["diagnose_normal_con_especificaciones"] = lambda: pp.diagnose(_normales(), lsl=44, usl=56, target=50)
    d["diagnose_tendencia"] = lambda: pp.diagnose(np.arange(40.0) + _rng(1).normal(0, 0.5, 40), lsl=0, usl=60)
    d["diagnose_atipicos_no_normal"] = lambda: pp.diagnose(np.append(_rng(4).exponential(2.0, 50), [30.0, 35.0]), lsl=0)
    d["diagnose_n5"] = lambda: pp.diagnose([1.0, 2.0, 3.5, 4.0, 5.0])

    # capacidad
    d["capability_con_especificaciones"] = lambda: pp.capability_analysis(_normales(), lsl=44, usl=56, target=50)
    d["capability_sin_especificaciones"] = lambda: pp.capability_analysis(_normales())
    d["capability_solo_lsl"] = lambda: pp.capability_analysis(_normales(), lsl=44)
    d["capability_solo_usl"] = lambda: pp.capability_analysis(_normales(), usl=56)
    d["capability_subgrupos"] = lambda: pp.capability_analysis(_subgrupos(), lsl=6, usl=14, target=10)
    d["capability_resumen"] = lambda: pp.capability_analysis_summary(50.0, 2.0, 60, lsl=44, usl=56, target=50, std_within=1.8)
    d["capability_nonnormal_weibull"] = lambda: pp.capability_nonnormal(_rng(8).weibull(2.0, 80) * 5 + 0.1, lsl=0.05, usl=12, distribution="weibull")
    d["capability_boxcox"] = lambda: pp.capability_boxcox(_rng(8).lognormal(1.0, 0.4, 80), lsl=0.5, usl=15)

    # cartas de control (summary() y to_frame() de ControlChart)
    d["imr_con_atipicos"] = lambda: pp.imr_chart(_con_atipico(), tests=[1, 2, 3, 4, 5, 6])
    d["imr_con_etapas"] = lambda: pp.imr_chart(np.r_[_normales(30), _normales(30, 55.0)], stages=["a"] * 30 + ["b"] * 30)
    d["xbar_r"] = lambda: pp.xbar_r_chart(_subgrupos(), tests="all")
    d["xbar_s"] = lambda: pp.xbar_s_chart(_subgrupos())
    d["p_chart"] = lambda: pp.p_chart(*_atributos())
    d["np_chart"] = lambda: pp.np_chart(*_atributos())
    d["c_chart"] = lambda: pp.c_chart(_conteos())
    d["u_chart"] = lambda: pp.u_chart(_conteos(), np.full(30, 2.0))
    d["laney_p"] = lambda: pp.laney_p_chart(*_atributos())
    d["laney_u"] = lambda: pp.laney_u_chart(_conteos(), np.full(30, 2.0))
    d["ewma"] = lambda: pp.ewma_chart(_con_atipico(), k=2.5, target=10.0, sigma=1.0)
    d["cusum"] = lambda: pp.cusum_chart(_con_atipico(), target=10, sigma=1, h=4, k=0.5)
    d["ma"] = lambda: pp.ma_chart(_con_atipico(), length=4)
    d["imr_rs"] = lambda: pp.imr_rs_chart(_subgrupos())
    d["zmr"] = lambda: pp.zmr_chart(_con_atipico(), ["P1"] * 20 + ["P2"] * 20)
    d["zona"] = lambda: pp.zone_chart(_con_atipico())
    d["g_chart"] = lambda: pp.g_chart(np.r_[_rng(6).geometric(0.05, 30)])
    d["t_chart"] = lambda: pp.t_chart(_rng(6).weibull(1.5, 30) * 10 + 0.1)
    d["t2"] = lambda: pp.t2_chart(_rng(9).normal(0, 1, (40, 3)))
    d["mewma"] = lambda: pp.mewma_chart(_rng(9).normal(0, 1, (40, 3)))
    d["mcusum"] = lambda: pp.mcusum_chart(_rng(9).normal(0, 1, (40, 3)))
    d["varianza_generalizada"] = lambda: pp.generalized_variance_chart(_rng(9).normal(0, 1, (20, 6, 3)))

    # corridas y precontrol
    d["run_chart_aleatorio"] = lambda: pp.run_chart(_normales(40))
    d["run_chart_tendencia"] = lambda: pp.run_chart(np.arange(30.0) + _rng(2).normal(0, 0.3, 30))
    d["precontrol"] = lambda: pp.precontrol(_normales(40), 44, 56, 50)
    d["precontrol_con_senales"] = lambda: pp.precontrol(np.array([50.0, 54.0, 54.5, 46.0, 54.0, 58.0, 50.0, 45.9, 46.2, 50.0]), 44, 56, 50)
    d["imr_sin_pruebas"] = lambda: pp.imr_chart(_con_atipico(), tests=[])

    # normalidad
    d["normalidad_anderson"] = lambda: pp.normality_test(_normales(50), method="anderson")
    d["normalidad_shapiro"] = lambda: pp.normality_test(_normales(50), method="shapiro")
    d["normalidad_dagostino"] = lambda: pp.normality_test(_normales(50), method="dagostino")

    # MSA
    def _gage(**kw):
        datos, p, o, r = _msa_datos()
        return pp.gage_rr(datos, parts=p, operators=o, replicates=r, **kw)
    d["gage_rr_anova"] = lambda: _gage(tolerance=20.0)
    d["gage_rr_xbar_r"] = lambda: _gage(method="xbar_r", tolerance=20.0)
    d["gage_rr_sin_tolerancia"] = lambda: _gage()
    d["gage_rr_anidado"] = lambda: pp.gage_rr_nested(_msa_datos()[0], parts=10, operators=3, replicates=2)
    d["gage_tipo1"] = lambda: pp.gage_type1(_rng(1).normal(10.02, 0.05, 40), reference=10.0, tolerance=0.5)
    d["gage_tipo1_resumen"] = lambda: pp.gage_type1_summary(10.02, 0.05, 40, reference=10.0, tolerance=0.5)
    d["gage_tipo1_resumen_sin_tolerancia"] = lambda: pp.gage_type1_summary(10.02, 0.05, 40, reference=10.0)
    d["gage_linealidad"] = lambda: pp.gage_linearity(
        np.repeat([2.0, 4.0, 6.0, 8.0, 10.0], 12) + _rng(3).normal(0, 0.1, 60) + 0.02 * np.repeat([2.0, 4.0, 6.0, 8.0, 10.0], 12),
        np.repeat([2.0, 4.0, 6.0, 8.0, 10.0], 12), tolerance=14.0)
    d["acuerdo_por_atributos"] = lambda: pp.attribute_agreement(_desde_df_atributos()[0], reference=_desde_df_atributos()[1], replicates=2)

    # muestreo de aceptación
    d["muestreo_atributos"] = lambda: pp.acceptance_sampling_attributes(N=1000, aql=1.0)
    d["muestreo_variables"] = lambda: pp.acceptance_sampling_variables(N=1000, aql=1.0)
    d["dodge_romig_ltpd"] = lambda: pp.dodge_romig(N=1000, ltpd=0.05, process_avg=0.01)
    d["dodge_romig_aoql"] = lambda: pp.dodge_romig(N=1000, aoql=0.02, process_avg=0.01)

    # tolerancia
    d["tolerancia_normal"] = lambda: pp.tolerance_interval(_normales(40), coverage=0.95, confidence=0.95)
    d["tolerancia_no_parametrica"] = lambda: pp.tolerance_interval(_normales(120), coverage=0.9, confidence=0.9, method="nonparametric")
    d["tolerancia_un_lado"] = lambda: pp.tolerance_interval(_normales(40), sides="upper")
    d["tolerancia_resumen"] = lambda: pp.tolerance_interval_summary(50.0, 2.0, 40, coverage=0.95, confidence=0.95)
    d["tolerancia_resumen_inferior"] = lambda: pp.tolerance_interval_summary(50.0, 2.0, 40, sides="lower")
    d["tolerancia_resumen_superior"] = lambda: pp.tolerance_interval_summary(50.0, 2.0, 40, sides="upper")

    # asistente
    d["wizard_auto"] = lambda: pp.wizard(_normales(60), mode="auto")
    d["wizard_subgrupos"] = lambda: pp.wizard(_subgrupos(), mode="auto")
    d["wizard_tendencia"] = lambda: pp.wizard(np.arange(40.0) + _rng(1).normal(0, 0.4, 40), mode="auto")
    return d


NUMERO = re.compile(r"[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?")


def enmascarar(texto: str) -> str:
    """Sustituye cada número por ``#``: compara texto y estructura sin depender de decimales entre versiones de numpy/scipy."""
    return NUMERO.sub("#", texto)


def _py(valor):
    """Valor de una celda como tipo básico de Python (comparable y serializable en JSON)."""
    if isinstance(valor, np.generic):
        valor = valor.item()
    if isinstance(valor, float) and np.isnan(valor):
        return None
    return valor if isinstance(valor, (bool, int, float, str)) or valor is None else str(valor)


def tabla(df: pd.DataFrame) -> dict:
    """Etiquetas exactas (índice, columnas) y valores de una tabla."""
    return {
        "index_name": df.index.name,
        "columns": [str(c) for c in df.columns],
        "index": [_py(i) for i in df.index],
        "data": [[_py(v) for v in fila] for fila in df.to_numpy(dtype=object)],
    }


def textos(obj) -> dict:
    """Los textos observables de un objeto: ``summary()`` / ``str()`` y la tabla de ``to_frame()``."""
    salida: dict = {}
    if isinstance(obj, str):
        salida["texto"] = obj
        return salida
    if hasattr(obj, "summary"):
        salida["summary"] = obj.summary()
    elif hasattr(obj, "__str__"):
        salida["str"] = str(obj)
    if hasattr(obj, "to_frame"):
        salida["frame"] = tabla(obj.to_frame())
    return salida


def construir_todo() -> tuple[dict, dict]:
    """(resultados, errores): cada entrada se construye con los avisos silenciados."""
    resultados, errores = {}, {}
    for nombre, f in entradas().items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                resultados[nombre] = textos(f())
        except Exception as e:  # noqa: BLE001 - se informa del nombre y del error
            errores[nombre] = f"{type(e).__name__}: {str(e)[:120]}"
    return resultados, errores


def tabla_estable(obj) -> dict | None:
    """La tabla de ``to_frame(stable=True)`` (claves canónicas) o ``None`` si el objeto no tiene tabla."""
    return tabla(obj.to_frame(stable=True)) if hasattr(obj, "to_frame") else None


def construir_estables() -> dict:
    estables = {}
    for nombre, f in entradas().items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            t = tabla_estable(f())
        if t is not None:
            estables[nombre] = t
    return estables



# ── gráficos: todo el texto de una figura ────────────────────────────────────

def textos_de_figura(fig) -> list[str]:
    """Textos visibles de una figura (títulos, ejes, leyendas, anotaciones, marcas categóricas), con los números enmascarados."""
    import matplotlib.text as mtext

    salida = []
    for t in fig.findobj(mtext.Text):
        s = t.get_text().strip()
        if not s or re.fullmatch(r"[-+−0-9.,eE %]+", s):   # marcas numéricas de los ejes: no son texto traducible
            continue
        salida.append(enmascarar(s))
    return sorted(salida)


# Resultados construidos desde estadísticos (sin los datos): no se pueden dibujar.
SIN_DATOS_PARA_GRAFICAR = {"capability_resumen"}


def graficos() -> dict:
    """nombre → función que devuelve la ``Figure`` (entradas del corpus con ``.plot()`` y funciones de graficado sueltas)."""
    import matplotlib.pyplot as plt

    g: dict = {}
    for nombre, f in entradas().items():
        if nombre not in SIN_DATOS_PARA_GRAFICAR:
            g[f"plot_{nombre}"] = f
    g["plot_probabilidad"] = lambda: pp.probability_plot(_normales(40))
    g["plot_pareto"] = lambda: pp.plot_pareto(pp.pareto(["Rayón", "Abolladura", "Rayón", "Mancha", "Rayón", "Abolladura", "Otro"]))
    g["plot_sixpack"] = lambda: pp.capability_sixpack(_subgrupos(), 6, 14, 10)[0]
    g["plot_capability_funcion"] = lambda: pp.plot_capability(pp.capability_analysis(_normales(), lsl=44, usl=56, target=50))

    def construir(nombre, f):
        obj = f()
        fig = obj if isinstance(obj, plt.Figure) else (obj.plot() if hasattr(obj, "plot") else None)
        return fig
    return {n: (lambda n=n, f=f: construir(n, f)) for n, f in g.items()}


def construir_graficos() -> tuple[dict, dict]:
    import matplotlib.pyplot as plt

    res, err = {}, {}
    for nombre, f in graficos().items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fig = f()
            if fig is None:
                continue
            res[nombre] = textos_de_figura(fig)
            plt.close(fig)
        except Exception as e:  # noqa: BLE001
            err[nombre] = f"{type(e).__name__}: {str(e)[:100]}"
    return res, err



# ── asistente (wizard): árbol, resultados, CLI y widget ──────────────────────

def _widget_falso():
    """Módulos ``ipywidgets`` e ``IPython.display`` mínimos: registran HTML y botones y permiten pulsarlos."""
    import types

    class Base:
        def __init__(self, *a, **k):
            self.a, self.k, self.children, self._on_click = a, k, [], None

        def on_click(self, fn):
            self._on_click = fn

    class HTML(Base):
        pass

    class Button(Base):
        pass

    w = types.SimpleNamespace(HTML=HTML, Button=Button, VBox=Base, Layout=lambda **k: dict(k))
    mod_display = types.ModuleType("IPython.display")
    mod_display.display = lambda *_a, **_k: None
    mod_ipython = types.ModuleType("IPython")
    mod_ipython.display = mod_display
    return w, {"ipywidgets": w, "IPython": mod_ipython, "IPython.display": mod_display}


def _textos_hijos(contenedor) -> list[str]:
    out = []
    for h in contenedor.children:
        out.append(h.a[0] if h.a else h.k.get("description", ""))
    return out


def textos_wizard() -> dict:
    """Todos los textos visibles del asistente en el idioma activo."""
    import builtins
    import io
    import sys
    from contextlib import redirect_stdout

    from pccpy import _wizard as W

    salida: dict = {}
    salida["arbol"] = {n: [p, [o for o, _d in ops]] for n, (p, ops) in W._TREE.items()}
    salida["resultados"] = {n: {"summary": r.summary(), "snippet": r.snippet()} for n, r in W._RESULTS.items()}

    def cli(respuestas):
        it = iter(respuestas)
        original = builtins.input
        builtins.input = lambda prompt="": (print(prompt, end=""), next(it))[1]
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                W._run_cli()
            return buf.getvalue()
        finally:
            builtins.input = original

    salida["cli"] = cli(["x", "99", "1", "1", "1"])

    w, modulos = _widget_falso()
    previos = {k: sys.modules.get(k) for k in modulos}
    sys.modules.update(modulos)
    try:
        pasos = []
        capturado = {}
        contenedor_original = w.VBox

        def vbox(*a, **k):
            capturado["c"] = contenedor_original(*a, **k)
            return capturado["c"]

        w.VBox = vbox
        sesion = W._run_widget()
        c = capturado["c"]
        pasos.append(_textos_hijos(c))
        for _ in range(3):                      # root → cartas → cartas_ind → hoja
            boton = next(h for h in c.children if h.k.get("description", "").startswith("1."))
            boton._on_click(boton)
            pasos.append(_textos_hijos(c))
        volver = next(h for h in c.children if "description" in h.k and not h.k["description"][:1].isdigit())
        volver._on_click(volver)
        pasos.append(_textos_hijos(c))
        salida["widget"] = pasos
        salida["widget_repr_inicial"] = repr(W.WidgetSession())
        assert sesion is not None
    finally:
        for k, v in previos.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return salida

if __name__ == "__main__":  # python tests/_corpus_i18n.py  → regenera tests/golden/i18n_es.json (solo con el código de referencia)
    import json
    from pathlib import Path

    resultados, errores = construir_todo()
    assert not errores, errores
    destino = Path(__file__).parent / "golden" / "i18n_es.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(resultados)} entradas → {destino}")
    estable = Path(__file__).parent / "golden" / "i18n_stable.json"
    estable.write_text(json.dumps(construir_estables(), ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"claves estables → {estable}")
    figs, errs = construir_graficos()
    assert not errs, errs
    (Path(__file__).parent / "golden" / "i18n_plots_es.json").write_text(json.dumps(figs, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(figs)} figuras → tests/golden/i18n_plots_es.json")
    (Path(__file__).parent / "golden" / "i18n_wizard_es.json").write_text(json.dumps(textos_wizard(), ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("asistente → tests/golden/i18n_wizard_es.json")
