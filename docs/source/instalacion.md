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

Python ≥ 3.9. Las dependencias `numpy`, `scipy`, `pandas` y `matplotlib` se
instalan automáticamente al hacer `pip install pccpy` — no es necesario
instalarlas por separado ni importarlas antes de usar la librería.

### Dependencia opcional: `ipywidgets`

`ipywidgets` es necesaria **solo** si quieres usar `pp.wizard(mode='widget')`
en Jupyter Notebook o JupyterLab. Si no está instalada, el modo degrada
automáticamente a `'cli'` (preguntas en la terminal) sin lanzar ningún error.

Para habilitarlo:

```bash
pip install ipywidgets
```

En JupyterLab < 3 puede requerir además:

```bash
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```
