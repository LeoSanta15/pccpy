import matplotlib

matplotlib.use("Agg")  # sin ventanas en CI

import matplotlib.pyplot as plt
import pytest


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture(autouse=True)
def _idioma_espanol():
    """La suite comprueba los textos en español (idioma fuente) aunque el entorno defina PCCPY_LANG."""
    from pccpy import _i18n

    anterior = _i18n._global
    _i18n._global = "es"
    yield
    _i18n._global = anterior


@pytest.fixture
def rng():
    """Generador aleatorio propio de cada prueba (independiente del orden de ejecución)."""
    import numpy as np

    return np.random.default_rng(123)
