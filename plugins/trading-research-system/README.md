# Trading Research System Plugin

This plugin packages a trading research workflow for Codex.

It is designed for research, screening, risk review, and decision support. It does not provide guaranteed returns, personalized financial advice, or trading instructions that ignore user constraints.

It is AI-native: the agent should read broadly, verify current facts, compare conflicting signals, and tell the user only the compressed decision-useful result. User-facing output should prioritize conclusions, changed variables, invalidations, setup status, portfolio constraints, and next checks over raw article summaries or long narrative.

## Capabilities

- Macro and policy filtering focused on market-moving variables.
- Trump policy, Treasury policy, rates, yields, and liquidity monitoring.
- Longbridge `macrodata` as an optional macro and financial-conditions source when installed and authorized.
- Equity screening with thesis verification against primary sources.
- Research report discovery from public or authorized sources, with source priority and access status.
- User-provided report intake for PDFs, links, excerpts, screenshots, or copied text, producing a digest, claim ledger, verification queue, and plan impact.
- Seeking Alpha and similar research-note synthesis when accessible or provided by the user.
- High-level Al Brooks price action timing framework.
- KVN snapshot import, Top10 display, ticker lookup, and Top10 change summary from local SQLite.
- Active Market Plan maintenance with an overwriteable current state and append-only update trail.
- Trading profile template for personal strategy scoring, pool definitions, ETF groups, instrument preference, timeframe rules, crowding model, and setup-to-instrument translation.
- Automation-ready deep update, quick update, intraday monitor, post-market review, and position daily report workflows.
- Deep updates for weekend/weekly review, including prior trades, future events, momentum, and setup discovery.
- Quick updates for weekday premarket and intraday level/status changes.
- Setup-scoped intraday scanning for prepared setup plans.
- Broker-live position daily reports with concise risk summaries and visualization-ready outputs.
- Interactive post-order and post-exit review context intake from read-only broker facts and user context.
- Broker-agnostic portfolio risk exposure checks.
- Broker-live runtime view templates for read-only Longbridge skill/plugin and IBKR connector sources, with manual CSV as a reduced one-off fallback.
- Local planning, report snapshot, and review-context templates.
- Daily folder initialization, portfolio exposure, watchlist ranking, and trade statistics scripts.
- On-demand TradingView `lightweight-charts` HTML artifacts for price-action review from local OHLCV JSON.

## User Interaction

Use natural-language trading research tasks in Codex. The agent should route the
task to the right internal workflow.

```text
帮我做下周交易计划，先看宏观、利率、政策、新闻和当前持仓影响。
```

```text
盘前更新一下今天需要盯的 setup，告诉我哪些接近触发。
```

```text
现在检查今天计划里的 QQQ 和 MU setup，哪些接近触发，哪些失效？
```

```text
读这篇 NVDA 研报，提炼 thesis 和 counter-thesis，并告诉我是否影响 Active Market Plan。
```

```text
生成今天的持仓日报，只告诉我风险暴露和需要决策的事项。
```

```text
这笔 QQQ 0DTE 已经结束了，帮我做出场复盘和系统标签。
```

## Advanced Skill Surface

The conceptual router is `trading-research`. Focused skills such as
`weekly-trading-plan`, `daily-market-tracking`, `intraday-setup-scan`,
`trade-review`, `research-report-intake`, `macro-equity-research`,
`portfolio-risk`, and `trading-stats` remain available as internal agent
workflows, power-user shortcuts, and development/test boundaries. They should
not be presented as the default user-facing menu.

## Data Boundaries

For current policy, market prices, rates, yields, financial statements, or news, Codex must verify against current sources. Paywalled sources such as Seeking Alpha can only be analyzed from publicly accessible content or user-provided excerpts.

For large source sets, the plugin should not show every source detail by default. It should store or cite enough evidence to support confidence, then surface the few facts that change the plan.

## Capability Boundaries

This plugin does not:

- place trades or automate order execution;
- modify or cancel broker orders;
- generate guaranteed buy/sell instructions;
- scan the entire market for unplanned intraday trades outside the Active Market Plan, watchlist, or prepared setups in the initial scope;
- use Google Sheets as the canonical source of truth;
- provide tax, legal, or regulated investment advice.

## Local Records

Use a private runtime directory as the first source of truth. By default:

```text
~/Documents/dailytrades-runtime/
```

This can be overridden with `TRADING_RESEARCH_RUNTIME_DIR` or script-level
`--runtime-dir`.

The runtime directory should contain:

```text
market-plan.md
trading-profile.md
updates/YYYY-MM-DD.md
daily/YYYY-MM-DD/
charts/
```

The plugin includes templates for Active Market Plans, update notes, holdings, broker-live runtime views, watchlists, trade plans, report snapshots, reviews, research-note logs, research-report logs, and macro checklists.

Use `trading-profile.md` in the runtime directory for private strategy scoring, pool definitions, ETF groups, instrument preferences, timeframe rules, crowding model, and avoid rules. The public repo only ships a blank template and does not store personal account allocation or a hard-coded personal strategy model.

Broker adapters are read-only sources. During onboarding or runtime
initialization, ask which broker sources to enable. V1 formally supports the
Longbridge skill/plugin and IBKR connector. Manual CSV remains a reduced fallback
for one-off runs or fixtures. Local files are fixtures, debug artifacts, or
user-confirmed derived snapshots, not the default broker fact source of truth.
Longbridge `macrodata` is a separate macro-data source, not an account source.

Codex automations can be used to schedule prompts around the Active Market Plan loop and position daily report, but they should ask before editing local records and must not touch broker write actions.

Google Sheets is optional summary display only. It should not be used as a trade-record layer.

## Project Plan

In the source repository, `docs/ROADMAP.md` is the public planning document for capability boundaries, execution method, task breakdown, and progress tracking.

Use `docs/PROJECT_LOG.md` for the public GitHub trajectory of milestone updates and important plugin changes.

## Scripts

```bash
python3 plugins/trading-research-system/scripts/runtime_health.py --date 2026-07-04 --format json
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py import /path/to/kvn.csv --db ~/Documents/dailytrades-runtime/momentum/kvn.sqlite --source user
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py show --date 2026-06-24 --top 10
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py query SOXX --date 2026-06-24
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py changes --date 2026-06-24
python3 plugins/trading-research-system/scripts/init_daily.py --date 2026-06-12
python3 plugins/trading-research-system/scripts/portfolio_risk.py ~/Documents/dailytrades-runtime/daily/2026-06-12/portfolio.csv
python3 plugins/trading-research-system/scripts/watchlist_score.py ~/Documents/dailytrades-runtime/daily/2026-06-12/watchlist.csv
python3 plugins/trading-research-system/scripts/trade_stats.py ~/Documents/dailytrades-runtime/daily/2026-06-12/trades.csv --group-by instrument_type
python3 plugins/trading-research-system/scripts/update_trade_record.py --date 2026-06-12 --stage post-order --trade-id 20260612-QQQ-001 --fields-json /path/to/fields.json --review-file /path/to/review.md
python3 plugins/trading-research-system/scripts/update_trade_record.py --date 2026-06-12 --stage post-order --trade-id 20260612-QQQ-LEGACY --fields-json /path/to/legacy-fields.json --review-file /path/to/review.md --allow-unknown-execution-fields
python3 plugins/trading-research-system/scripts/import_legacy_active_csv.py plugins/trading-research-system/assets/fixtures/input/legacy-active-trades.csv --runtime-dir ~/Documents/dailytrades-runtime
python3 plugins/trading-research-system/scripts/append_review.py --date 2026-06-12 --trade-id 20260612-QQQ-001 --symbol QQQ --review-file /path/to/review.md
python3 plugins/trading-research-system/scripts/chart_artifact.py plugins/trading-research-system/assets/templates/chart-ohlcv-qqq-sample.json --output ~/Documents/dailytrades-runtime/charts/qqq-plan.html
```
