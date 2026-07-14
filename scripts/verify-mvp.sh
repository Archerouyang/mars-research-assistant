#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_ROOT="$ROOT/plugins/trading-research-system"
FIXTURE_RUNTIME="$PLUGIN_ROOT/assets/fixtures/runtime/active-market-plan-2026-06-24"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required. Install it with: brew install uv" >&2
  exit 127
fi

if [[ ! -d "$FIXTURE_RUNTIME" ]]; then
  echo "error: fixture runtime missing: $FIXTURE_RUNTIME" >&2
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

mkdir -p "$ROOT/.scratch"
MVP_RUNTIME_DIR="${MVP_RUNTIME_DIR:-$(mktemp -d "$ROOT/.scratch/mvp-smoke-runtime.XXXXXX")}"
mkdir -p "$MVP_RUNTIME_DIR"
cp -R "$FIXTURE_RUNTIME/." "$MVP_RUNTIME_DIR/"
mkdir -p "$MVP_RUNTIME_DIR/momentum" "$MVP_RUNTIME_DIR/smoke-output"

echo "Fixture-backed local MVP smoke"
echo "Runtime: $MVP_RUNTIME_DIR"
echo "No live broker reads; no real Codex automations; no live market data."

./scripts/verify-plugin.sh

uv_run python plugins/trading-research-system/scripts/bootstrap_runtime.py \
  --runtime-dir "$MVP_RUNTIME_DIR/bootstrap-check" \
  --date 2026-06-24 \
  > "$MVP_RUNTIME_DIR/smoke-output/runtime-bootstrap.txt"

uv_run python plugins/trading-research-system/scripts/runtime_health.py \
  --runtime-dir "$MVP_RUNTIME_DIR" \
  --date 2026-06-24 \
  --format json \
  --broker-source manual=available \
  > "$MVP_RUNTIME_DIR/smoke-output/runtime-health.json"

uv_run python plugins/trading-research-system/scripts/kvn_leaderboard.py import \
  plugins/trading-research-system/assets/fixtures/input/kvn-snapshot-2026-06-21.csv \
  --db "$MVP_RUNTIME_DIR/momentum/kvn.sqlite" \
  --source fixture \
  > "$MVP_RUNTIME_DIR/smoke-output/kvn-import-2026-06-21.txt"

uv_run python plugins/trading-research-system/scripts/kvn_leaderboard.py import \
  plugins/trading-research-system/assets/fixtures/input/kvn-snapshot-2026-06-24.csv \
  --db "$MVP_RUNTIME_DIR/momentum/kvn.sqlite" \
  --source fixture \
  > "$MVP_RUNTIME_DIR/smoke-output/kvn-import-2026-06-24.txt"

uv_run python plugins/trading-research-system/scripts/kvn_leaderboard.py show \
  --db "$MVP_RUNTIME_DIR/momentum/kvn.sqlite" \
  --date 2026-06-24 \
  --top 10 \
  > "$MVP_RUNTIME_DIR/smoke-output/kvn-show.md"

uv_run python plugins/trading-research-system/scripts/kvn_leaderboard.py query SOXX \
  --db "$MVP_RUNTIME_DIR/momentum/kvn.sqlite" \
  --date 2026-06-24 \
  > "$MVP_RUNTIME_DIR/smoke-output/kvn-query-soxx.md"

uv_run python plugins/trading-research-system/scripts/kvn_leaderboard.py changes \
  --db "$MVP_RUNTIME_DIR/momentum/kvn.sqlite" \
  --date 2026-06-24 \
  > "$MVP_RUNTIME_DIR/smoke-output/kvn-changes.md"

uv_run python plugins/trading-research-system/scripts/broker_snapshot_ingest.py \
  --input "IBKR:plugins/trading-research-system/assets/fixtures/input/broker-positions-ibkr-2026-06-24.csv" \
  --input "Longbridge:plugins/trading-research-system/assets/fixtures/input/broker-positions-longbridge-2026-06-24.csv" \
  --output "$MVP_RUNTIME_DIR/smoke-output/portfolio_snapshot_from_brokers.csv" \
  --as-of 2026-06-24T20:00:00Z \
  > "$MVP_RUNTIME_DIR/smoke-output/broker-snapshot-ingest.txt"

uv_run python plugins/trading-research-system/scripts/intraday_scan.py \
  "$MVP_RUNTIME_DIR/daily/2026-06-24/intraday-watchlist.csv" \
  --date 2026-06-24 \
  --output "$MVP_RUNTIME_DIR/smoke-output/intraday-scan.md"

uv_run python plugins/trading-research-system/scripts/position_daily_report.py \
  "$MVP_RUNTIME_DIR/daily/2026-06-24/portfolio_snapshot.csv" \
  --date 2026-06-24 \
  --source "fixture broker-live snapshot" \
  --data-status fixture \
  --snapshot-saved fixture \
  > "$MVP_RUNTIME_DIR/smoke-output/position-daily-report.md"

uv_run python plugins/trading-research-system/scripts/verify_position_daily_report_selftest.py
uv_run python plugins/trading-research-system/scripts/verify_intraday_scan_selftest.py
uv_run python plugins/trading-research-system/scripts/verify_active_market_plan_fixture_contract.py
uv_run python plugins/trading-research-system/scripts/verify_mvp_smoke_contract.py

echo "MVP smoke ok"
echo "Smoke output: $MVP_RUNTIME_DIR/smoke-output"
