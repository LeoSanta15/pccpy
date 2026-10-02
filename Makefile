.PHONY: install test cov lint types build docs examples check-fast check release-check

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

check-fast: lint types test

check: check-fast build docs examples

# Uso: make release-check TAG=v0.10.9  (el wheel construido debe tener la versión del tag)
release-check:
	@test -n "$(TAG)" || { echo "uso: make release-check TAG=vX.Y.Z"; exit 1; }
	@rm -rf dist && python -m build --wheel >/dev/null
	@V=$$(python -c "import glob,re;print(re.search(r'-(\d[^-]*)-py', glob.glob('dist/*.whl')[0]).group(1))"); \
	if [ "$(TAG:v%=%)" = "$$V" ]; then echo "OK: tag $(TAG) == wheel $$V"; else echo "ERROR: tag $(TAG) != wheel $$V"; exit 1; fi
