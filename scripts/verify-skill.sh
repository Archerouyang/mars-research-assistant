#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_ROOT="${SKILL_ROOT:-$ROOT/skills/mars-research-assistant}"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required. Install it with: brew install uv" >&2
  exit 127
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

PUBLIC_ROOTS=(
  "$ROOT/skills/mars-research-assistant"
)
GENERATED_STATE="$(find "${PUBLIC_ROOTS[@]}" \
  \( -type d -name __pycache__ \
  -o -type f \( -name '*.pyc' -o -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) \) \
  -print)"
if [[ -n "$GENERATED_STATE" ]]; then
  echo "error: generated cache or database state found under public package roots:" >&2
  printf '%s\n' "$GENERATED_STATE" >&2
  exit 1
fi

uv_run() {
  uv run --python "$PYTHON_BIN" "$@"
}

PYTHON_BIN="$PYTHON_BIN" bash scripts/verify-skill-compile.sh
uv_run python scripts/verify_portable_distribution_contract.py
uv_run python "$SKILL_ROOT/scripts/verify_product_knowledge_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_private_runtime_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_research_result_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_mars_observation_adapter_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_macro_preflight_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_ibkr_macro_adapter_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_ibkr_ohlcv_adapter_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_ibkr_only_contract.py"
uv_run python "$SKILL_ROOT/scripts/verify_mars_broker_capability_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_daily_ops_routing_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_holdings_display_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_mars_runtime_migration_selftest.py"
uv_run python "$SKILL_ROOT/scripts/verify_standalone_board_selftest.py"
node "$SKILL_ROOT/scripts/verify_board_png_contract.mjs"
uv_run python "$SKILL_ROOT/scripts/verify_artifact_packet_selftest.py"
