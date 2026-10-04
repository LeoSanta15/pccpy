.PHONY: install test cov lint types build docs examples i18n-extract i18n-update i18n-compile i18n-check check-fast check release-check

install:
	python -m pip install -e ".[dev,docs,excel]"

test:
	python -m pytest tests/ -q

cov:
	python -m pytest tests/ -q --cov=pccpy --cov-report=term-missing

lint:
	python -m ruff check src/

types:
	python -m mypy src/pccpy --ignore-missing-imports

build:
	python -m build --wheel

docs:
	sphinx-build -b html -W docs/source docs/build

examples:
	@for f in examples/*.py; do MPLBACKEND=Agg python "$$f" >/dev/null || { echo "FALLA $$f"; exit 1; }; done; echo "ejemplos OK"

i18n-extract:
	pybabel extract -F babel.cfg --no-default-keywords -k tr -k N_ --no-location --sort-output -o src/pccpy/locale/pccpy.pot --project=pccpy --msgid-bugs-address="" --copyright-holder="" src

i18n-update: i18n-extract
	pybabel update -i src/pccpy/locale/pccpy.pot -d src/pccpy/locale -D pccpy

i18n-compile:
	pybabel compile -d src/pccpy/locale -D pccpy

i18n-check:
	python scripts/i18n_check.py

check-fast: lint types test i18n-check

check: check-fast build docs examples

# Uso: make release-check TAG=v0.10.9  (el wheel construido debe tener la versión del tag)
release-check:
	@test -n "$(TAG)" || { echo "uso: make release-check TAG=vX.Y.Z"; exit 1; }
	@rm -rf dist && python -m build --wheel >/dev/null
	@V=$$(python -c "import glob,re;print(re.search(r'-(\d[^-]*)-py', glob.glob('dist/*.whl')[0]).group(1))"); \
	if [ "$(TAG:v%=%)" = "$$V" ]; then echo "OK: tag $(TAG) == wheel $$V"; else echo "ERROR: tag $(TAG) != wheel $$V"; exit 1; fi
