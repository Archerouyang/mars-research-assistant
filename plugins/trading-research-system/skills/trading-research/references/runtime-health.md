# Runtime Health

Use this reference before plan updates, trading-operation automations, broker
reconciliation, setup scans, KVN reads, or review flows that depend on private
runtime state.

Runtime health is a status check, not a content read. Do not read or copy private file contents into public repo files or public documentation.

## Status Values

Use only these status values:

- `available`: expected runtime path or source exists and is usable.
- `missing`: expected runtime path or source is absent.
- `stale`: expected file exists but is older than the configured freshness
  threshold.
- `unauthorized`: broker or external source is not authorized for this run.
- `not_installed`: broker source, connector, skill, or local terminal is not
  installed or visible in the current Codex session.

`not_installed` is broker-source health only. File/runtime path checks should
continue to use `missing`.

## Default Checks

The health check should cover:

- `{runtime_dir}/market-plan.md`
- `{runtime_dir}/trading-profile.md`
- `{runtime_dir}/updates/`
- `{runtime_dir}/daily/YYYY-MM-DD/`
- `{runtime_dir}/daily/YYYY-MM-DD/trade-plans.csv`
- `{runtime_dir}/daily/YYYY-MM-DD/intraday-watchlist.csv`
- `{runtime_dir}/momentum/kvn.sqlite`
- `Longbridge` broker source
- `IBKR` broker source
- `Manual snapshot` source
- `broker_sources`

The JSON payload must include:

- `current_mode`: `live read-only`, `manual snapshot`, or `dry-run`.
- `broker_source_health`: per-source status rows for Longbridge, IBKR, and
  Manual snapshot.

## Script

Use the bundled script:

```bash
python3 plugins/trading-research-system/scripts/runtime_health.py --date 2026-07-04 --format json
```

Useful options:

- `--runtime-dir`: private runtime root, defaulting to `TRADING_RESEARCH_RUNTIME_DIR`
  or `~/Documents/dailytrades-runtime`.
- `--format json`: machine-readable output for automations and verifiers.
- `--format markdown`: human-readable status note.
- `--broker-source longbridge=available`: disclose known broker-source status.
- `--broker-source ibkr=unauthorized`: disclose missing broker authorization.
- `--broker-source ibkr=not_installed`: disclose that the connector/source is
  not installed or visible in this run.
- `--broker-source manual=available`: disclose a user-approved manual snapshot.
- `--stale-after-days 3`: mark existing files stale when modified before the
  freshness window.

## Behavior

If required state is `missing`, `stale`, or `unauthorized`, report the gap and
ask whether to initialize, import, connect a source, or continue with reduced
analysis.

Use `current_mode` to explain what the current Daily Ops run can trust:

- `live read-only`: at least one authorized broker source is available.
- `manual snapshot`: no live broker source is available, but a user-approved
  derived snapshot is available.
- `dry-run`: no broker facts should be assumed.

Do not invent current plan state. Do not treat a stale local broker snapshot as
current broker truth. Return to authorized read-only broker sources when exact
holdings, executions, orders, or account facts matter.
