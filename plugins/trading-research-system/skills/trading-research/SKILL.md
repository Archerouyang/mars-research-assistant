---
name: trading-research
description: Route trading research requests to the right Trading Research System workflow. Use when the user invokes trading-research generally, asks for trading help without naming a specific sub-skill, or needs coordination across Active Market Plan updates, weekly deep updates, daily quick updates, intraday setup scanning, trade review, broker data reconciliation, automations, macro/equity research, portfolio risk, and trading statistics.
---

# Trading Research Router

Use this skill as the general entrypoint for the Trading Research System plugin. Keep it lightweight: choose the most specific sub-skill and follow that workflow.

This is decision support, not automated trading. Do not present outputs as guaranteed returns, personalized financial advice, or certainty. Always separate facts, assumptions, thesis, counter-thesis, invalidation, and risk controls.

This plugin is AI-native. The agent should absorb large volumes of market, macro, research, chart, broker, and journal information, then return a compact decision note. Do not dump raw readings, long source summaries, or every intermediate observation unless the user asks for audit detail.

## Routing

- General Daily Ops guidance, vague requests such as "start today", "begin daily ops", "开始今天的交易研究", "开始今天的交易研究日程", "现在该做什么", or any request where the user wants active process guidance:
  read `references/daily-ops-orchestrator.md` first. The Daily Ops Orchestrator detects stage, checks runtime health, asks for missing confirmations, and then routes to the focused workflow.

### Exact Generic First Start

For the exact generic first-start request `开始今天的交易研究`, return the
fixed Daily Ops startup block before analysis or `daily-market-tracking`.

#### 运行状态检查

Render `runtime_dir`, `runtime_origin`, `formal runtime`, `startup_status`,
`startup_reason` when available, `current_mode`, and status-only runtime files.

#### 券商来源健康

Render `source_capability_health` before `broker_source_health`, then show the
exact `portfolio_reconciliation` status. If it is `unavailable`, list excluded
sources, preserve fail-closed wording, and include the missing confirmation.

#### 宏观数据来源状态

Render `macro-panel.json` and its source status, with fixture/debug disclosure
and no invented macro values.

Then ask the first-start broker read-only question and route to a focused
workflow. Do not replace this structure with a generic market-update status
table.
- Active Market Plan initialization or deep update with last-week trade review, macro/policy/news/event preview, optional external momentum context, and setup discovery:
  use `weekly-trading-plan`.
- Daily quick update against `market-plan.md`: macro/policy/news/event delta, momentum change, setup status changes, and level updates:
  use `daily-market-tracking`.
- Several active setups, multiple tickers/charts, trigger checks, and attention priority:
  use `intraday-setup-scan`.
- Actual trade record, broker execution facts, post-order note, post-exit review:
  use `trade-review`.
- Research report discovery, user-provided PDF/link/text digestion, report thesis extraction, claim ledger, and verification queue:
  use `research-report-intake`.
- Macro policy, rates/yields, research-note verification, stock screening:
  use `macro-equity-research`.
- External quantitative momentum model requests:
  explain that v1 does not bundle or publicly expose model construction,
  rankings, or a standalone leaderboard. If the user provides an already
  generated snapshot, treat it as an optional internal input to Trade Plan
  Preparation after confirmation; otherwise continue without it.
- Holdings, sizing, portfolio exposure, risk budget, trade impact:
  use `portfolio-risk`.
- Win rate, R-multiple, setup performance, mistake tags, system review:
  use `trading-stats`.
- Automation design, recurring brief, scheduled Active Market Plan update, or monitor:
  read `references/automation-contract.md` and use the Codex automation tool when creating or updating actual automations.

Before workflows that depend on private runtime state, use
`references/runtime-health.md` and `../../scripts/runtime_health.py` to check
whether required state is available, missing, stale, unauthorized,
`partial_data`, `upstream_error`, `empty_positions_unverified`, or
`needs_review`. Preserve the returned status; do not translate a partial/error
result into unauthorized. Do not read private file contents just to perform the
health check.

If the current trading date is missing its daily runtime package, ask before
writing and then use `../../scripts/prepare_daily_runtime.py` to create safe
header-only daily containers such as `trade-plans.csv` and
`intraday-watchlist.csv`. This prepares files for the workflow; it does not
create setup rows, read brokers, read market data, or place orders.

After the user confirms concrete setup rows from the Active Market Plan, use
`../../scripts/prepare_setup_rows.py` with user-confirmed setup JSON to populate
`trade-plans.csv` and `intraday-watchlist.csv`. This bridges plan preparation
to formal scanning; it does not parse free-form trade ideas, read brokers, read
market data, or place orders.

Use the formal runtime as the only active Daily Ops state root:
`runtime_dir`, defaulting to `~/Documents/dailytrades-runtime` unless
`TRADING_RESEARCH_RUNTIME_DIR` or a user-confirmed runtime path overrides it.
Repo fixtures, bundled templates, and example plans are development inputs only;
do not treat them as the current Active Market Plan in a new chat.

On every Daily Ops first start, enter `券商只读来源设置`, including when
unspecified live broker sources default to `needs_review`. On later turns,
`missing` or `unauthorized` enters `券商只读来源设置`. Ask
whether to enable Longbridge read-only, IBKR read-only, both, or continue without
broker facts for this run. `券商只读来源设置` configures read intent only; it
must not read accounts, install software, or call broker write actions.

On later turns, `needs_review` asks for matching verification/retry and does not
repeat authorization setup. `stale`, `partial_data`, `upstream_error`, and
`empty_positions_unverified` retain distinct availability or verification paths;
report the exact state instead of routing them through authorization setup.

If a ticker or setup lacks `trade_horizon`, do not generate concrete entry or
exit triggers. Ask for the intended `ticker + trade_horizon + instrument`
grouping first. If trade horizon is missing, the correct output is a compact
blocking question, not a forced setup.

Apply this gate before deep research on a specific tradable idea: confirm the complete
`ticker + trade_horizon + instrument` key. A brief watch-only or reduced-scope
research summary may still be useful while the key is missing, but do not start
expensive company/setup research or produce entry/exit levels until the user
confirms it.

For a weekend first start with a missing or partial runtime, do not make runtime
initialization or broker authorization a prerequisite for all value. First
return a current, public-source reduced-scope research summary that clearly
states what cannot be personalized; then ask for the smallest confirmations
needed for broker reads, the setup key, and optional runtime initialization.
Do not write runtime during this first response.

Before macro regime, financial-conditions, rates/liquidity, or strategy posture
claims, read `references/macro-data-source-contract.md`. Use Longbridge
macrodata as the preferred source for macro values when available, use
IBKR market data for price/OHLCV transmission, and official source fallback for
S0 facts or when Longbridge macrodata is unavailable.

If a request spans multiple workflows, run them in the natural order:

1. Daily Ops Orchestrator when the user asks to start, continue, or decide what to do next.
2. `research-report-intake` when the task starts from research reports, PDFs, links, excerpts, or report discovery.
3. `macro-equity-research` when deeper source verification, screening, or macro/policy analysis is needed.
4. `weekly-trading-plan` to initialize or deep-update the Active Market Plan.
5. `daily-market-tracking` to quick-update the same plan against today's market.
6. `intraday-setup-scan` to classify setup-level status during the session.
7. `portfolio-risk` before increasing or concentrating exposure, using canonical broker data when available.
8. `trade-review` after orders/fills and after exits.
9. `trading-stats` after enough closed-trade records exist.

## Shared Resources

Detailed domain rules remain in:

- `references/macro-policy-filter.md`
- `references/macro-data-source-contract.md`
- `references/research-report-intake.md`
- `references/equity-screening.md`
- `references/daily-ops-orchestrator.md`
- `references/active-market-plan.md`
- `references/runtime-health.md`
- `references/trading-profile.md`
- `references/broker-data-contract.md`
- `references/automation-contract.md`
- `references/price-action-timing.md`
- `references/intraday-setup-scan.md`
- `references/interactive-trade-review.md`
- `references/trade-journal.md`
- `references/portfolio-risk.md`
- `references/output-templates.md`

Shared scripts and templates remain in the plugin root:

- `../../scripts/`
- `../../assets/templates/`

Runtime health:

```bash
python3 ../../scripts/runtime_health.py --format json
```

Position daily report from a standard runtime snapshot:

```bash
python3 ../../scripts/position_daily_report.py {runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv --date YYYY-MM-DD
```

## Output Style

Use Chinese unless the user asks otherwise. Prefer Markdown notes suitable for Obsidian.

Default to compressed output:

- conclusion first;
- changed variables only;
- setup status and next check;
- invalidation and risk constraints;
- evidence only when it changes confidence;
- no long narrative source dumps.

Use clear labels when applicable:

- `事实`
- `假设`
- `多头逻辑`
- `空头逻辑`
- `失效条件`
- `择时`
- `组合风险`
- `下一步`

When a task needs current facts, use browsing or authorized connectors. Do not rely on memory for policy, market data, yields, company facts, or current prices.
