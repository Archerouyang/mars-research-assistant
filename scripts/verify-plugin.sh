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

cd "$ROOT"

uv_run() {
  uv run --python "$PYTHON_BIN" "$@"
}

uv_run python scripts/verify_plugin_distribution_selftest.py
uv_run python scripts/verify_plugin_distribution.py
uv_run --group dev python "$VALIDATE_PLUGIN" "$PLUGIN_ROOT"
uv_run python plugins/trading-research-system/scripts/verify_contract_suite.py core
