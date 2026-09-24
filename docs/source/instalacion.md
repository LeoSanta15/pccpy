# Instalación

Desde PyPI (recomendado):

```bash
pip install pccpy
```

Desde GitHub:

```bash
pip install git+https://github.com/LeoSanta15/pccpy.git
```

Desarrollo local (incluye las pruebas y las herramientas de calidad):

```bash
git clone https://github.com/LeoSanta15/pccpy.git
cd pccpy
pip install -e ".[dev]"
pytest --cov=spyc
ruff check src/
mypy src/spyc
```

Para generar esta documentación en tu máquina:

```bash
pip install -e ".[docs]"
sphinx-build -b html docs/source docs/build
```

Abre `docs/build/index.html` en el navegador.

## Requisitos

Python ≥ 3.9, con `numpy`, `scipy`, `pandas` y `matplotlib` (se instalan solos
como dependencias del paquete).
