#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_ROOT="${PLUGIN_ROOT:-$ROOT/plugins/trading-research-system}"
VALIDATE_PLUGIN="${VALIDATE_PLUGIN:-$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py}"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required. Install it with: brew install uv" >&2
  exit 127
fi

if [[ ! -f "$VALIDATE_PLUGIN" ]]; then
  echo "error: plugin validator not found: $VALIDATE_PLUGIN" >&2
  exit 1
fi

if [[ -z "${PYTHON_BIN:-}" ]]; then
  CODEX_PYTHON="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  if [[ -x "$CODEX_PYTHON" ]]; then
    PYTHON_BIN="$CODEX_PYTHON"
  elif command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3.12)"
  else
    PYTHON_BIN="python3"
  fi
fi

export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT/.scratch/uv-cache}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$ROOT/.scratch/uv-venv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$ROOT/.scratch/uv-python}"
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"

cd "$ROOT"

uv_run() {
  uv run --python "$PYTHON_BIN" "$@"
}

uv_run python scripts/verify_plugin_compile_gate_selftest.py
PYTHON_BIN="$PYTHON_BIN" bash scripts/verify-plugin-compile.sh
uv_run python scripts/verify_plugin_distribution_selftest.py
uv_run python scripts/verify_plugin_distribution.py
uv_run python scripts/verify_behavior_contract_matrix_selftest.py
uv_run python scripts/verify_behavior_contract_matrices_contract.py
uv_run python scripts/verify_readme_gallery_contract_selftest.py
uv_run python scripts/verify_readme_gallery_contract.py
uv_run python scripts/verify_canonical_gallery_selftest.py
uv_run python scripts/stage_canonical_gallery.py \
  --verify-only \
  --output-dir docs/staging/canonical-gallery-v1
uv_run python plugins/trading-research-system/scripts/verify_position_risk_artifact_selftest.py
uv_run --group dev python "$VALIDATE_PLUGIN" "$PLUGIN_ROOT"
uv_run python plugins/trading-research-system/scripts/verify_contract_suite.py core
