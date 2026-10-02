#!/bin/bash
# Hook Stop: si hay cambios en src/ o tests/, exige lint + tipos + tests antes de terminar.
# Exit 2 devuelve el error al agente para que lo corrija; stop_hook_active evita bucles.
set -uo pipefail

INPUT=$(cat)
if echo "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"
if [ -z "$(git status --porcelain -- src tests pyproject.toml 2>/dev/null)" ]; then
  exit 0
fi

if ! OUT=$(make check-fast 2>&1); then
  echo "Verificación fallida: corrige antes de terminar (definición de 'terminado' en CLAUDE.md)." >&2
  echo "$OUT" | tail -25 >&2
  exit 2
fi
