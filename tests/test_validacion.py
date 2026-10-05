"""Módulo de validación: se ejecuta solo, informa y detecta una biblioteca rota."""
from __future__ import annotations

import pccpy as pp
from pccpy import validation


def test_todo_correcto():
    informe = pp.run_validation()
    assert len(informe.checks) >= 30
    assert informe.passed, informe.summary()
    assert informe.failures == []


def test_filtra_por_id_y_ids_unicos():
    ids = [d.id for d in validation._REGISTRO]
    assert len(ids) == len(set(ids))
    informe = pp.run_validation(["limites-imr", "limites-xbar-r"])
    assert [c.id for c in informe.checks] == ["limites-imr", "limites-xbar-r"]


def test_detecta_biblioteca_rota(monkeypatch):
    """Control negativo: si la biblioteca devuelve algo distinto, la validación falla y lo dice."""
    import pccpy.msa as msa

    original = msa.gage_type1

    def rota(*a, **k):
        r = original(*a, **k)
        object.__setattr__(r, "cg", r.cg * 2)  # el error que tenía la versión 0.11.0
        return r

    monkeypatch.setattr(msa, "gage_type1", rota)
    informe = pp.run_validation()
    assert not informe.passed
    assert [c.id for c in informe.failures] == ["gage-tipo1"]


def test_comprobacion_que_lanza_se_informa_sin_detener_el_resto(monkeypatch):
    def explota():
        raise RuntimeError("boom")

    monkeypatch.setattr(validation, "_REGISTRO", [validation._Definicion("x", "Caso roto", "ref", explota, 1e-9),
                                                  *validation._REGISTRO[:2]])
    informe = pp.run_validation()
    assert [c.passed for c in informe.checks] == [False, True, True]
    assert "RuntimeError: boom" in informe.failures[0].detail
    assert "FALLA x" in informe.summary()


def test_informes():
    informe = pp.run_validation(["limites-imr"])
    md = informe.to_markdown()
    assert "limites-imr" in md and "Minitab" in md
    df = informe.to_frame()
    assert list(df["id"]) == ["limites-imr"] and bool(df["correcta"].iloc[0])
    assert "passed" in informe.to_frame(stable=True).columns


def test_ingles():
    with pp.language("en"):
        informe = pp.run_validation(["constantes-n5", "prueba-1"])
        assert "n = 5" in informe.checks[0].description and "Constants" in informe.checks[0].description
        assert "checks passed" in informe.summary()
        assert "Validación" not in informe.to_markdown()


def test_main(tmp_path, capsys):
    destino = tmp_path / "informe.md"
    assert validation.main(["--markdown", str(destino)]) == 0
    assert "comprobaciones correctas" in capsys.readouterr().out
    assert destino.read_text(encoding="utf-8").startswith("# ")
