"""Los ejemplos corregidos en la auditoría de la documentación de 0.13.0 se ejecutan tal como están escritos."""
import re
import warnings
from pathlib import Path

import numpy as np
import pytest

import pccpy as pp

DOCS = Path(__file__).resolve().parents[1] / "docs" / "source"


def _bloques(archivo: str, contiene: str) -> list[str]:
    texto = (DOCS / archivo).read_text(encoding="utf-8")
    return [b for b in re.findall(r"```python\n(.*?)```", texto, re.S) if contiene in b]


@pytest.mark.parametrize("marca", ["res.ppm_overall", "res.z_bench_overall"])
def test_ejemplos_de_capacidad_acceden_a_atributos_que_existen(marca):
    x = np.random.default_rng(0).normal(50, 2, 60)
    res = pp.capability_analysis(x, lsl=44, usl=56)
    bloques = _bloques("capacidad_indices.md", marca)
    assert bloques
    for b in bloques:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(b, {"pp": pp, "np": np, "x": x, "res": res})


def test_ejemplo_de_ewma_de_la_guia_de_seleccion():
    bloques = _bloques("guia_seleccion.md", "ewma_chart(")
    assert bloques
    x = np.random.default_rng(0).normal(50, 1, 60)
    for b in bloques:
        exec(b, {"pp": pp, "np": np, "x": x})
