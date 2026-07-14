#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_SCRIPTS="${PLUGIN_SCRIPTS:-$ROOT/plugins/trading-research-system/scripts}"
PLUGIN_COMPILE_CACHE_ROOT="${PLUGIN_COMPILE_CACHE_ROOT:-$ROOT/.scratch/plugin-compile-cache}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -d "$PLUGIN_SCRIPTS" ]]; then
  echo "error: plugin scripts directory missing: $PLUGIN_SCRIPTS" >&2
  exit 1
fi

mkdir -p "$PLUGIN_COMPILE_CACHE_ROOT"
PYCACHE_PREFIX="$(mktemp -d "$PLUGIN_COMPILE_CACHE_ROOT/run.XXXXXX")"

PYTHONPYCACHEPREFIX="$PYCACHE_PREFIX" \
  "$PYTHON_BIN" -m compileall -q "$PLUGIN_SCRIPTS"

echo "Plugin compile gate ok: $PLUGIN_SCRIPTS"
echo "Bytecode cache: $PYCACHE_PREFIX"
