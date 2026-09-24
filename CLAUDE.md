# pccpy — contexto para Claude Code

Este archivo es el punto de partida para retomar el trabajo en spyc desde Claude
Code. Léelo completo antes de tocar código: resume las convenciones, el estado
actual y lo que falta, para no repetir decisiones ya tomadas ni romper algo que
ya funciona.

## Qué es pccpy

Librería Python de Control Estadístico de Procesos (SPC) que replica la
funcionalidad de Minitab: cartas de control (univariadas y multivariadas),
análisis de capacidad, prueba de normalidad y Pareto. Todo el código,
docstrings, mensajes de error y salidas están **en español**.

## Estado actual

- Versión **0.4.5**, en `src/spyc/__init__.py` (`__version__`) y `pyproject.toml`.
- **186 pruebas**, todas pasando, ~97% de cobertura.
- 6 commits en `main`, etiquetados `v0.1.0` a `v0.4.2` (uno por versión).
- **No está en GitHub todavía** — el repositorio solo existe en este `.tar.gz`.
  El `pyproject.toml` y el `README.md` tienen `TU_USUARIO` como marcador de
  posición en las URLs; hay que reemplazarlo antes de subirlo (ver "Pendientes").
- Documentación con Sphinx en `docs/`, sin publicar (no hay Read the Docs
  conectado todavía, pero `.readthedocs.yaml` ya está listo para eso).

Para el detalle versión por versión, lee `CHANGELOG.md` — no lo dupliques aquí.

## Reglas de trabajo (no negociables)

1. **Sigue `/mnt/skills/user/karpathy-guidelines/SKILL.md` si existe en tu
   entorno** (o los mismos principios si no): simplicidad, cambios quirúrgicos,
   criterios de éxito verificables. No reescribas módulos enteros para agregar
   una función; sigue el patrón que ya usan los módulos vecinos.
2. **Todo resultado numérico se valida contra una referencia independiente** —
   nunca contra la propia salida de spyc. Referencias usadas hasta ahora:
   tablas publicadas (Montgomery, Minitab), cálculo manual, `scipy`/`statsmodels`,
   o simulación Monte Carlo con **al menos ~20 semillas distintas** antes de dar
   por buena una tolerancia (varias pruebas de este proyecto fallaron con la
   primera semilla que se probó y hubo que ajustar la tolerancia o el enunciado).
3. **Español en todo lo que ve el usuario**: nombres de funciones en snake_case
   inglés está bien (`imr_chart`), pero docstrings, mensajes de `ValueError`,
   columnas de DataFrame, texto de gráficos y de `summary()` van en español.
4. **Avances incrementales con checkpoint**: cada versión nueva se construye,
   se prueba (pruebas propias + wheel en un venv limpio), se hace commit, se
   etiqueta `vX.Y.Z`, y solo entonces se sigue. No dejes trabajo a medio hacer
   entre un commit y otro.
5. **Antes de un commit de versión**, corre siempre, en este orden:
   ```bash
   pytest -q                                    # deben pasar todas
   ruff check src/ --select F,E9,B,S            # bugs reales, no solo estilo
   mypy src/spyc --ignore-missing-imports        # debe salir limpio
   python -m build --wheel                       # construir
   # instalar el wheel en un venv limpio y correr pytest ahí también
   sphinx-build -b html -W docs/source docs/build # si tocaste código público, docstrings o docs/
   ```
6. **No inventes comparaciones con Minitab real** — nunca hubo licencia
   disponible durante el desarrollo. Cuando una fórmula no está clara en la
   documentación pública de Minitab, se usa la referencia estadística estándar
   (Montgomery, el paper original del método) y se anota como decisión propia
   en el README, sección "Notas sobre diferencias posibles con Minitab".

## Mapa del código

```
src/spyc/
  __init__.py          # API pública: todo lo exportado vive en __all__ aquí
  _constants.py         # d2, d3, c4, c5, A2..B4 por integración numérica (n>=2)
  _data.py               # as_1d, to_subgroups, stage_slices (etapas contiguas)
  _sigma.py               # estimadores de sigma (individuales y subgrupos)
  rules.py                 # las 8 pruebas de causas especiales de Minitab
  results.py                # Panel, ControlChart, MultivariateChart (+ .plot(), .summary()...)
  charts/
    _engine.py               # build_chart(): motor común, itera etapas, aplica pruebas
    variables.py               # I-MR, Xbar-R, Xbar-S
    attributes.py               # P, NP, C, U, Laney P'/U'
    timeweighted.py               # EWMA, CUSUM (NO soportan 'stages' todavía)
    advanced.py                     # MA, Z-MR, I-MR-R/S, Zona, G, T
  multivariate.py                    # T², |S|, MEWMA, MCUSUM (con 'stages' y 'boxcox')
  capability.py                       # capacidad normal/no normal/Box-Cox, sixpack
  normality.py                         # Anderson-Darling, Shapiro, D'Agostino
  plotting.py                           # plot_control_chart, plot_capability, etc.
  quality_tools.py                       # pareto, plot_pareto

tests/            # un archivo por área temática, todas usan la fixture `rng` de conftest.py
examples/         # ejemplo_basico.py y ejemplo_avanzado.py, ambos se ejecutan sin error
docs/source/      # Sphinx: referencia/*.rst usa autofunction/autoclass (no dupliques docstrings ahí)
```

**Patrón para agregar una carta nueva:** mira `charts/advanced.py` (una carta
univariada simple, p. ej. `g_chart`) o `multivariate.py` (una multivariada,
p. ej. `mcusum_chart`) como plantilla. Toda carta termina llamando a
`build_chart(kind, n_puntos, stages, stage_fn, tests, test_params)`, que se
encarga de iterar etapas y aplicar las pruebas de causas especiales — no
reimplementes ese bucle.

## Cómo verificar que todo sigue sano

```bash
pip install -e ".[dev,docs]"
pytest -q                                          # 186 pruebas, deben pasar todas
ruff check src/
mypy src/spyc
sphinx-build -b html -W docs/source docs/build
python examples/ejemplo_basico.py                  # debe correr sin error
python examples/ejemplo_avanzado.py                 # ídem
```

## Pendientes conocidos (en orden aproximado de lo que se ha ido priorizando)

1. **Subir a GitHub** — sigue sin hacerse porque requiere la cuenta del
   usuario. Pasos exactos en la sección siguiente de este archivo.
2. **Publicar en PyPI** — nunca se preparó (no hay `twine`, no hay cuenta de
   PyPI configurada). Si se pide, empezar por `python -m build`, revisar con
   `twine check dist/*`, y pedir las credenciales al usuario antes de subir
   nada.
3. **Box-Cox en las cartas univariadas** (solo existe en capacidad y en las 4
   cartas multivariadas).
4. **Prueba de Benneyan** en la carta G.
5. **Duraciones = 0** en la carta T (Weibull/exponencial no las admite).
6. **Transformación de Johnson** (solo hay Box-Cox y percentiles no-normales).
7. **MSA / Gage R&R** — no implementado en absoluto.
8. **`stages` en `ewma_chart`/`cusum_chart`** — las 4 cartas multivariadas y la
   mayoría de las univariadas sí lo soportan; EWMA/CUSUM univariados no.
9. Nunca se ejecutó el CI de verdad (solo localmente) porque no hay repo
   remoto — conviene revisar el primer run en GitHub Actions en cuanto exista,
   por si hay diferencias de entorno no detectadas aquí.

## Cómo subir esto a GitHub (primera vez)

```bash
# 1. Reemplazar el marcador de usuario
sed -i 's/TU_USUARIO/tu-usuario-real/g' pyproject.toml README.md docs/source/index.md .readthedocs.yaml

# 2. Crear un repositorio vacío en github.com/new (sin README ni licencia)

# 3. Conectar y subir (ya trae 6 commits y las etiquetas v0.1.0..v0.4.2)
git remote add origin https://github.com/tu-usuario-real/spyc.git
git push -u origin main --tags
```

Después de eso, el workflow `.github/workflows/tests.yml` va a correr solo en
cada push (pruebas + cobertura, ruff + mypy, y build de la documentación). Es
la primera vez que corre de verdad — vale la pena revisar el resultado.

Para publicar la documentación: conectar el repo en readthedocs.org (detecta
`.readthedocs.yaml` solo, no requiere configuración adicional).
