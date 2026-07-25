#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT/.scratch/uv-cache}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$ROOT/.scratch/uv-venv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$ROOT/.scratch/uv-python}"
export PYTHONDONTWRITEBYTECODE=1

test ! -e "$ROOT/skills/mars-research-assistant/scripts/__pycache__"
bash "$ROOT/scripts/verify-skill-compile.sh"
uv run --no-sync python "$ROOT/scripts/verify_portable_distribution_contract.py"
uv run --no-sync python "$ROOT/skills/mars-research-assistant/scripts/verify_stateless_research_run_selftest.py"
uv run --no-sync python "$ROOT/skills/mars-research-assistant/scripts/verify_macro_research_run_selftest.py"
echo "stateless Skill verification passed"
