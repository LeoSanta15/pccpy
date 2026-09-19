import matplotlib

matplotlib.use("Agg")  # sin ventanas en CI

import matplotlib.pyplot as plt
import pytest


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def rng():
    """Generador aleatorio propio de cada prueba (independiente del orden de ejecución)."""
    import numpy as np

    return np.random.default_rng(123)
