#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
OFFLINE=false

usage() {
  echo "usage: $0 [--offline]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline)
      OFFLINE=true
      shift
      ;;
    *)
      usage
      exit 64
      ;;
  esac
done

if [[ ! -f "$PACKAGE_ROOT/pyproject.toml" || ! -f "$PACKAGE_ROOT/uv.lock" ]]; then
  echo "technical analysis requires the complete Mars Skill package with pyproject.toml and uv.lock" >&2
  echo "install the repository package before running this Skill" >&2
  exit 65
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "technical analysis requires uv; no pip fallback is supported" >&2
  exit 69
fi

TRUSTED_PYTHON=""
if [[ -n "${UV_PYTHON:-}" && -x "${UV_PYTHON}" ]]; then
  TRUSTED_PYTHON="$UV_PYTHON"
elif ! TRUSTED_PYTHON="$(uv python find --no-project '>=3.12,<3.13' 2>/dev/null)"; then
  if [[ "$OFFLINE" == true ]]; then
    echo "offline setup requires an existing Python 3.12 interpreter" >&2
    exit 69
  fi
  uv python install 3.12
  TRUSTED_PYTHON="$(
    uv python find --managed-python --no-project '>=3.12,<3.13'
  )"
fi

if [[ -z "$TRUSTED_PYTHON" || ! -x "$TRUSTED_PYTHON" ]]; then
  echo "uv could not provide a trusted Python 3.12 interpreter" >&2
  exit 69
fi

SYNC_ARGUMENTS=(
  sync
  --project "$PACKAGE_ROOT"
  --locked
  --python "$TRUSTED_PYTHON"
)
if [[ "$OFFLINE" == true ]]; then
  SYNC_ARGUMENTS+=(--offline --no-python-downloads)
fi

env -u VIRTUAL_ENV -u UV_PROJECT -u UV_WORKING_DIR \
  UV_PROJECT_ENVIRONMENT="$PACKAGE_ROOT/.venv" \
  uv "${SYNC_ARGUMENTS[@]}"

if [[ ! -x "$PACKAGE_ROOT/.venv/bin/python" ]]; then
  echo "uv did not create the package-local technical-analysis environment" >&2
  exit 70
fi

"$PACKAGE_ROOT/.venv/bin/python" -c \
  'import yfinance; assert yfinance.__version__ == "1.5.2", yfinance.__version__'

echo "technical-analysis yfinance environment is ready at $PACKAGE_ROOT/.venv"
