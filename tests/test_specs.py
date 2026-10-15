"""``scripts/specs_check.py``: la estructura de ``docs/specs`` y las reglas del desarrollo guiado por especificaciones."""
import importlib.util
import shutil
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("specs_check", RAIZ / "scripts" / "specs_check.py")
specs_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(specs_check)


def test_las_especificaciones_del_repositorio_estan_en_orden():
    assert specs_check.comprobar() == []


def test_main_devuelve_0_si_todo_esta_en_orden(capsys):
    assert specs_check.main() == 0
    assert "OK" in capsys.readouterr().out


# ── el comprobador detecta cada incumplimiento ───────────────────────────────

SPEC = """# 001 — Prueba

- **Estado:** {estado}
- **Identificador:** S001

## Requisitos

### S001-RF-01 — Algo

Debe hacer algo.

**Aceptación:**
- Dado… cuando… entonces…

## Preguntas abiertas

{pregunta}
"""
TAREAS = "# Tareas\n\n- [{marca}] S001-RF-01: hacerlo.\n"


@pytest.fixture
def raiz(tmp_path):
    specs = tmp_path / "docs" / "specs"
    shutil.copytree(RAIZ / "docs" / "specs" / "_plantilla", specs / "_plantilla")
    (specs / "README.md").write_text("x", encoding="utf-8")
    (specs / "CONSTITUCION.md").write_text("x", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    return tmp_path


def _crear(raiz, estado="borrador", pregunta="Ninguna.", marca=" ", nombre="001-prueba", spec=None, tareas=None):
    carpeta = raiz / "docs" / "specs" / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "spec.md").write_text(spec or SPEC.format(estado=estado, pregunta=pregunta), encoding="utf-8")
    (carpeta / "plan.md").write_text("# Plan", encoding="utf-8")
    (carpeta / "tasks.md").write_text(tareas or TAREAS.format(marca=marca), encoding="utf-8")


def _problemas(raiz):
    return specs_check.comprobar(raiz / "docs" / "specs", raiz / "tests")


def test_una_especificacion_correcta_no_da_problemas(raiz):
    _crear(raiz)
    assert _problemas(raiz) == []


def test_un_borrador_puede_tener_dudas_abiertas(raiz):
    _crear(raiz, pregunta="- [NECESITA ACLARACIÓN: ¿esto?]")
    assert _problemas(raiz) == []


@pytest.mark.parametrize("estado", ["aprobada", "implementada"])
def test_aprobada_o_implementada_no_admite_dudas_abiertas(raiz, estado):
    _crear(raiz, estado=estado, pregunta="- [NECESITA ACLARACIÓN: ¿esto?]", marca="x")
    assert any("abiertas" in p for p in _problemas(raiz))


def test_estado_no_valido(raiz):
    _crear(raiz, estado="terminada")
    assert any("no válido" in p for p in _problemas(raiz))


def test_nombre_de_carpeta_incorrecto(raiz):
    _crear(raiz, nombre="prueba-sin-numero")
    assert any("NNN-nombre-corto" in p for p in _problemas(raiz))


def test_faltan_archivos(raiz):
    _crear(raiz)
    (raiz / "docs" / "specs" / "001-prueba" / "plan.md").unlink()
    assert any("faltan plan.md" in p for p in _problemas(raiz))


def test_el_identificador_debe_coincidir_con_la_carpeta(raiz):
    _crear(raiz, spec=SPEC.format(estado="borrador", pregunta="x").replace("S001\n", "S002\n"))
    assert any("identificador" in p for p in _problemas(raiz))


def test_un_requisito_sin_aceptacion(raiz):
    _crear(raiz, spec=SPEC.format(estado="borrador", pregunta="x").replace("**Aceptación:**", "**Nada:**"))
    assert any("Aceptación" in p for p in _problemas(raiz))


def test_un_requisito_que_no_esta_en_las_tareas(raiz):
    _crear(raiz, tareas="# Tareas\n\n- [ ] otra cosa\n")
    assert any("no aparece en tasks.md" in p for p in _problemas(raiz))


def test_implementada_exige_tareas_marcadas_y_tests_que_citen_el_requisito(raiz):
    _crear(raiz, estado="implementada", marca=" ")
    msgs = _problemas(raiz)
    assert any("sin marcar" in p for p in msgs) and any("ningún test" in p for p in msgs)
    _crear(raiz, estado="implementada", marca="x")
    (raiz / "tests" / "test_algo.py").write_text('def test_a():\n    """S001-RF-01"""\n', encoding="utf-8")
    assert _problemas(raiz) == []


def test_descartada_exige_motivo(raiz):
    _crear(raiz, estado="descartada")
    assert any("Motivo" in p for p in _problemas(raiz))
    spec = SPEC.format(estado="descartada", pregunta="x").replace("- **Identificador:** S001", "- **Identificador:** S001\n- **Motivo:** ya no hace falta")
    _crear(raiz, spec=spec)
    assert _problemas(raiz) == []


def test_la_plantilla_incompleta_se_detecta(raiz):
    (raiz / "docs" / "specs" / "_plantilla" / "tasks.md").unlink()
    assert any("_plantilla" in p for p in _problemas(raiz))
