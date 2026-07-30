#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$ROOT/skills/mars-research-assistant"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT/.scratch/uv-cache}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$ROOT/.scratch/uv-venv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$ROOT/.scratch/uv-python}"
export PYTHONDONTWRITEBYTECODE=1

uv run --project "$RUNTIME" --offline --no-python-downloads --no-sync python "$ROOT/scripts/verify_mars_skills.py"
uv run --project "$RUNTIME" --offline --no-python-downloads --no-sync python -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
echo "Mars Skills verification passed"
