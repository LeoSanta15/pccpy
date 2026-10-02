#!/bin/bash
# Instala el proyecto con extras de desarrollo en sesiones web (idempotente, no interactivo).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"
python -m pip install --quiet --disable-pip-version-check -e ".[dev,docs,excel]"
