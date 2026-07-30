#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$ROOT/skills/mars-research-assistant"
VERIFY_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/mars-skills-verify.XXXXXX")"
VENV_SEED="${MARS_SKILLS_VENV_SEED:-$ROOT/.scratch/uv-venv}"
CACHE_SEED="${MARS_SKILLS_UV_CACHE_SEED:-$ROOT/.scratch/uv-cache}"
trap 'rm -rf "$VERIFY_ROOT"' EXIT

if [[ ! -d "$VENV_SEED" || ! -d "$CACHE_SEED" ]]; then
  echo "Mars Skills verification requires offline uv environment and cache seeds." >&2
  exit 1
fi

cp -R "$VENV_SEED" "$VERIFY_ROOT/uv-venv"
cp -R "$CACHE_SEED" "$VERIFY_ROOT/uv-cache"
export UV_CACHE_DIR="$VERIFY_ROOT/uv-cache"
export UV_PROJECT_ENVIRONMENT="$VERIFY_ROOT/uv-venv"
export UV_PYTHON_INSTALL_DIR="$VERIFY_ROOT/uv-python"
export npm_config_cache="$VERIFY_ROOT/npm-cache"
export PYTHONDONTWRITEBYTECODE=1

uv run --project "$RUNTIME" --offline --no-python-downloads --no-sync python "$ROOT/scripts/verify_mars_skills.py"
LOCKED_ENV="$VERIFY_ROOT/locked-sync-venv"
"$UV_PROJECT_ENVIRONMENT/bin/python" -m venv "$LOCKED_ENV"
UV_PROJECT_ENVIRONMENT="$LOCKED_ENV" uv sync --project "$RUNTIME" --locked --offline --no-python-downloads
"$LOCKED_ENV/bin/python" -c 'import yfinance; print(f"locked yfinance sync ok: {yfinance.__version__}")'
uv run --project "$RUNTIME" --offline --no-python-downloads --no-sync python -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
echo "Mars Skills verification passed"
