"""Comprueba las especificaciones de ``docs/specs``: estructura, estados, dudas abiertas y trazabilidad a los tests.

No juzga si una especificación es buena (eso lo hace la revisión); comprueba lo que se puede comprobar a máquina:

* cada carpeta ``NNN-nombre`` tiene ``spec.md``, ``plan.md`` y ``tasks.md`` (y existe ``_plantilla`` completa);
* ``spec.md`` declara un estado válido y un identificador ``SNNN`` que coincide con la carpeta;
* tiene al menos un requisito ``SNNN-RF-nn`` y cada uno lleva su ``**Aceptación:**``;
* una especificación ``aprobada`` o ``implementada`` no tiene ``[NECESITA ACLARACIÓN`` abiertas;
* todo requisito aparece en ``tasks.md``;
* una especificación ``implementada`` tiene todas las tareas marcadas y cada requisito citado por algún test;
* una ``descartada`` explica el motivo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ESTADOS = ("borrador", "aprobada", "implementada", "descartada")
ARCHIVOS = ("spec.md", "plan.md", "tasks.md")
DUDA = "[NECESITA ACLARACIÓN"


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _requisitos(texto: str, sid: str) -> list[tuple[str, str]]:
    """(identificador, cuerpo) de cada ``### SNNN-RF-nn — título``."""
    partes = re.split(r"^### (?=" + re.escape(sid) + r"-RF-\d+)", texto, flags=re.M)[1:]
    out = []
    for p in partes:
        ident = re.match(re.escape(sid) + r"-RF-\d+", p)
        if ident:
            out.append((ident.group(0), re.split(r"^## ", p, maxsplit=1, flags=re.M)[0]))
    return out


def comprobar(specs: Path = RAIZ / "docs" / "specs", tests: Path = RAIZ / "tests") -> list[str]:
    """Lista de problemas encontrados (vacía si todo está en orden)."""
    problemas: list[str] = []
    plantilla = specs / "_plantilla"
    for a in ARCHIVOS:
        if not (plantilla / a).is_file():
            problemas.append(f"_plantilla: falta {a}")
    for nombre in ("README.md", "CONSTITUCION.md"):
        if not (specs / nombre).is_file():
            problemas.append(f"falta docs/specs/{nombre}")
    textos_tests = "\n".join(_leer(p) for p in sorted(tests.glob("**/*.py"))) if tests.is_dir() else ""

    for carpeta in sorted(p for p in specs.iterdir() if p.is_dir() and not p.name.startswith("_")):
        m = re.match(r"^(\d{3})-[a-z0-9-]+$", carpeta.name)
        if not m:
            problemas.append(f"{carpeta.name}: el nombre debe ser NNN-nombre-corto (minúsculas, cifras y guiones)")
            continue
        sid = "S" + m.group(1)
        faltan = [a for a in ARCHIVOS if not (carpeta / a).is_file()]
        if faltan:
            problemas.append(f"{carpeta.name}: faltan {', '.join(faltan)}")
            continue
        spec, tareas = _leer(carpeta / "spec.md"), _leer(carpeta / "tasks.md")

        e = re.search(r"^- \*\*Estado:\*\* (\S+)", spec, flags=re.M)
        estado = e.group(1) if e else ""
        if estado not in ESTADOS:
            problemas.append(f"{carpeta.name}: estado {estado!r} no válido (usa {', '.join(ESTADOS)})")
        i = re.search(r"^- \*\*Identificador:\*\* (\S+)", spec, flags=re.M)
        if not i or i.group(1) != sid:
            problemas.append(f"{carpeta.name}: el identificador debe ser {sid}")

        reqs = _requisitos(spec, sid)
        if not reqs:
            problemas.append(f"{carpeta.name}: no hay ningún requisito {sid}-RF-nn")
        ids = [r[0] for r in reqs]
        if len(set(ids)) != len(ids):
            problemas.append(f"{carpeta.name}: hay requisitos repetidos")
        for ident, cuerpo in reqs:
            if "**Aceptación:**" not in cuerpo:
                problemas.append(f"{carpeta.name}: {ident} no tiene '**Aceptación:**'")
            if ident not in tareas:
                problemas.append(f"{carpeta.name}: {ident} no aparece en tasks.md")

        if estado in ("aprobada", "implementada") and DUDA in spec:
            problemas.append(f"{carpeta.name}: estado {estado} con '{DUDA}…' abiertas")
        if estado == "descartada" and not re.search(r"^- \*\*Motivo:\*\* \S", spec, flags=re.M):
            problemas.append(f"{carpeta.name}: una especificación descartada necesita '- **Motivo:** …'")
        if estado == "implementada":
            if re.search(r"^- \[ \]", tareas, flags=re.M):
                problemas.append(f"{carpeta.name}: implementada pero quedan tareas sin marcar")
            for ident in ids:
                if ident not in textos_tests:
                    problemas.append(f"{carpeta.name}: {ident} no está citado por ningún test")
    return problemas


def main() -> int:
    problemas = comprobar()
    for p in problemas:
        print(f"[specs] {p}")
    if problemas:
        print(f"\nERROR: {len(problemas)} problema(s) en docs/specs")
        return 1
    n = sum(1 for p in (RAIZ / "docs" / "specs").iterdir() if p.is_dir() and not p.name.startswith("_"))
    print(f"OK: {n} especificación(es) en orden")
    return 0


if __name__ == "__main__":
    sys.exit(main())
