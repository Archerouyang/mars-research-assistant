#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SCRIPTS="${SKILL_SCRIPTS:-$ROOT/skills/mars-research-assistant/scripts}"
SKILL_COMPILE_CACHE_ROOT="${SKILL_COMPILE_CACHE_ROOT:-$ROOT/.scratch/skill-compile-cache}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -d "$SKILL_SCRIPTS" ]]; then
  echo "error: Skill scripts directory missing: $SKILL_SCRIPTS" >&2
  exit 1
fi

mkdir -p "$SKILL_COMPILE_CACHE_ROOT"
PYCACHE_PREFIX="$(mktemp -d "$SKILL_COMPILE_CACHE_ROOT/run.XXXXXX")"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required" >&2
  exit 127
fi

PYTHONPYCACHEPREFIX="$PYCACHE_PREFIX" \
  uv run --no-sync --python "$PYTHON_BIN" python -m compileall -q "$SKILL_SCRIPTS"

echo "Skill compile gate ok: $SKILL_SCRIPTS"
echo "Bytecode cache: $PYCACHE_PREFIX"
