# Local MVP Runbook

This runbook defines the fixture-backed local MVP for the Trading Research
System plugin. It is a local smoke path for development confidence, not a live
trading execution flow.

## MVP Definition Of Done

The fixture-backed local MVP is done when this command passes on a clean
checkout after installing `uv`:

```bash
bash scripts/verify-mvp.sh
```

## Quick Run

```bash
brew install uv
bash scripts/verify-mvp.sh
```

## What This MVP Covers

- plugin validation through `scripts/verify-plugin.sh`;
- runtime health against a fixture runtime;
- KVN snapshot import, show, query, and changes from fixture CSV snapshots;
- Active Market Plan fixture completeness;
- plan-scoped intraday scan from fixture `intraday-watchlist.csv`;
- broker-live style position daily report from fixture `portfolio_snapshot.csv`;
- core contracts for Daily Ops Orchestrator, Source Routing Boundary,
  macro/industry monitor, Trade Plan Preparation, automation setup, and router
  behavior.

## What This MVP Does Not Cover

- No live broker reads;
- No real Codex automations;
- No live market data;
- No KVN quantitative model construction;
- No option-flow vendor integration;
- No order placement, modification, cancellation, closing, or approval;
- No private runtime or real trade-record validation.

## Smoke Output

`bash scripts/verify-mvp.sh` creates a new `.scratch/mvp-smoke-runtime.*`
directory on each run and writes generated smoke artifacts to:

```text
.scratch/mvp-smoke-runtime.XXXXXX/smoke-output/
```

## New Chat Validation

After plugin reinstall, start a fresh Codex thread and ask in Chinese:

```text
开始今天的交易研究日程。先只做 dry-run，不读 broker，不 web search，不写 runtime。
请说明当前阶段、缺失确认、下一步建议，并确认每个 ticker 都需要
ticker + trade_horizon + instrument。
```

Expected behavior: the agent routes through Daily Ops Orchestrator, reports
runtime/source limitations, enters `券商只读来源设置` when broker source is
missing or unauthorized, gives a concrete `下一步指引` with a copyable reply
format, and refuses concrete trigger levels for tickers without trade horizon
and instrument confirmation.

For the complete user-workflow gate, use `docs/1.0_ACCEPTANCE.md`. The 1.0 acceptance
path extends this smoke prompt into fresh-chat acceptance prompts for
daily startup, weekly plan, intraday setup tracking, position daily report,
rolling price action analysis, and two-stage trade review.

## Safety Boundary

The MVP is decision support only. It uses public repo fixtures and does not
touch broker write APIs, real accounts, real automations, or private trading
records.

## Next After MVP

1. Use Runtime bootstrap with `bootstrap_runtime.py` to create the private
   `~/Documents/dailytrades-runtime` skeleton from blank templates.
2. Use Daily runtime package preparation with `prepare_daily_runtime.py` to
   create today's `trade-plans.csv`, `intraday-watchlist.csv`, update note, and
   missing `ops-state.md` before formal intraday scans.
3. Use `prepare_setup_rows.py` with confirmed setup JSON to populate prepared
   setup rows before running `intraday_scan.py`.
4. Connect read-only broker adapters for Longbridge and IBKR.
5. Add user-confirmed Codex automations that wake Daily Ops Orchestrator.
6. Add chart screenshot/export workflow for price-action review.
