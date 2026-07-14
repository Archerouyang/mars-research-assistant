# Trading Research System Roadmap

## Project Goal

Trading Research System is a plugin-first trading research and risk decision-support system for Codex. It turns market information into a daily KVN momentum leaderboard, an overwriteable Active Market Plan, append-only update notes, setup-level trade plans, intraday setup scans, broker-live position daily reports, review context, visualization snapshots, and statistics for improving a discretionary trading system.

Daily Ops Orchestrator is the active process guide on top of those modules. It
uses `ops-state.md`, runtime health, Active Market Plan, and Trading Profile to
recommend the next workflow, ask for missing confirmations, and prevent users
from manually calling out every part of the system.

The first product surface is a Codex plugin with skills, references, scripts, templates, and local records. A standalone frontend is deferred.

The product is AI-native. Its core value is not producing long reports; it is making the agent read broadly, verify facts, filter noise, and return concise decision-useful notes to the user.

## Capability Boundaries

The system supports:

- agent-heavy research synthesis that compresses large source sets into conclusions, changed variables, invalidations, setup status, and next checks;
- Daily Ops Orchestrator guidance that detects the current stage, reads runtime status, asks for missing confirmations, and groups ideas by `ticker + trade_horizon + instrument`;
- macro policy and rates filtering focused on market-moving variables, with Longbridge `macrodata` available as an optional macro/financial-conditions source;
- Source Routing Boundary that scopes Longbridge `macrodata`, broker/account facts, market data, news, official policy facts, and research theses by source purpose so one selected connector does not become the default source for news;
- research report discovery from public/authorized sources plus user-provided report intake for PDFs, links, excerpts, screenshots, and copied text;
- research-note and market-view validation against primary/current sources;
- a daily KVN momentum leaderboard that imports or reads user-provided/upstream KVN snapshots, displays Top10 by default, and keeps all symbols searchable from a local SQLite store;
- equity and ETF screening with momentum, thesis, catalyst, and risk context;
- Al Brooks-style high-level price action timing with 20 EMA, 50 EMA, and multi-timeframe context;
- chat-first visual artifacts for concise inline price action and macro/regime views, with optional durable save only after confirmation;
- Active Market Plan maintenance with overwriteable current state and append-only update history;
- trading profile support for personal strategy models, instrument preferences, pool definitions, scoring thresholds, timeframe rules, and setup-to-instrument translation without storing account allocation in the public repo;
- automation-ready Active Market Plan deep updates, quick updates, intraday monitor prompts, post-market review prompts, and position daily reports;
- deep updates that include prior-week trade review, current market tape, macro/rates context, policy/news filtering, major event preview, KVN snapshot read/change summary, and setup discovery;
- quick updates for weekday premarket/intraday changes in tape, macro/rates, policy/news, events, momentum, setup status, and key levels;
- setup-scoped intraday scanning for `candidate`, `active`, `approaching`, `triggered`, `invalidated`, `needs_review`, and `completed` states;
- local trade planning, broker-live fact reads when available, two-stage interactive review-context capture, and statistics snapshots;
- portfolio risk exposure checks before and after trades, using live read-only broker sources when available;
- broker-source configuration for Longbridge skill/plugin and IBKR connector as the first supported read-only sources, with manual CSV kept as a reduced fallback for one-off runs or fixtures;
- optional non-sensitive summary or visualization mirrors when explicitly requested.

The system does not support in the initial scope:

- auto-order placement, order modification, or fully automated trading;
- guaranteed buy/sell instructions;
- unbounded whole-market real-time intraday scanning without an Active Market Plan theme, watchlist, or prepared setup;
- two-way Google Sheets sync;
- Google Sheets as a trade-record layer;
- durable local storage of full broker trade facts as the default source of truth;
- a persistent dashboard/frontend;
- unverified paywalled research extraction;
- tax, legal, or regulated investment advice.
- hard-coded personal strategy models as public defaults.
- KVN quantitative model construction, vendor selection, signal research, and backtesting.

## Execution Method

The default workflow is:

1. **Information collection**: gather macro policy, Treasury/rates/yield data, Longbridge `macrodata` when available, research-report leads, research-note claims, company facts, prices, watchlists, trade plans, and holdings.
2. **Information processing**: filter noise, classify source reliability, normalize inputs into analysis views, and separate facts from assumptions.
3. **Trade idea formation**: state long/short thesis, catalyst, counter-thesis, invalidation, and risk.
4. **Research Report Intake**: find public/authorized reports or digest user-provided PDFs, links, excerpts, screenshots, and text into a `Research Report Digest`, `Claim Ledger`, `Verification Queue`, and `Trade Plan Preparation Impact`.
5. **Information verification**: cross-check research claims against primary sources, current data, price behavior, and counter-evidence.
6. **KVN Momentum Leaderboard**: import or read daily, S&P500-benchmarked KVN ticker snapshots from a user-provided or upstream scheduled script/model output; show Top10 by script-computed order by default and preserve Top10 entry memory for later research triage. Agents may read, query, and explain changes, but must not re-rank or re-score KVN.
7. **Trade Plan Preparation**: compress Macro Regime, Financial Conditions, Policy/Event Risk, Industry/Sector Strength, Company Thesis Check, the latest KVN leaderboard, and profile-defined pool/scoring rules into input reads and a Cross-Section Candidate Pool before creating setup rows.
8. **Setup analysis**: classify higher-timeframe regime from 4H/1D/1W, map it to strategy bias, then use 1H and lower only for execution observation, trigger zone, invalidation, and next check.
8a. **Daily Ops Orchestrator**: when the user asks to start or continue the workflow, read `ops-state.md`, runtime health, Active Market Plan, and Trading Profile; detect stage; ask for missing `ticker + trade_horizon + instrument` confirmations; then route to the next workflow.
9. **Active Market Plan deep update**: review prior trades when relevant, analyze current tape, macro/rates, policy, news, future event risk, Trade Plan Preparation, setup pool, invalidation, trigger timeframe, and risk budget; overwrite `{runtime_dir}/market-plan.md` and append the rationale to `{runtime_dir}/updates/YYYY-MM-DD.md`.
10. **Active Market Plan quick update**: parse today's tape, macro/rates, policy, news, event preview, and setup-relevant changes against `market-plan.md`; update setup statuses, trigger zones, invalidation levels, targets, and which setups are approaching, triggered, invalidated, completed, or require review.
11. **Scheduled macro/industry/news research monitor**: after the weekly plan locks the week's P0/P1 focus variables, run user-confirmed recurring searches over public/authorized sources for macro, rates, policy, industry, company confirmation, and research leads. Apply Source Routing Boundary rules: Longbridge macrodata can support macro values, but choosing Longbridge for stock or broker data must not become the default source for news. Output only deltas, source-priority notes, verification queue, report leads, and Active Market Plan impact; do not bypass paywalls or turn reports into setups directly.
12. **Setup planning**: write structured setup-level rows to `trade-plans.csv` and, when needed, `intraday-watchlist.csv`; use `prepare_setup_rows.py` after the user confirms setup rows.
13. **Intraday scan**: monitor prepared setups and high-priority watchlist ideas; classify setups as `candidate`, `active`, `approaching`, `triggered`, `invalidated`, `needs_review`, or `completed`.
14. **Position daily report**: on a confirmed schedule, read authorized Longbridge or IBKR data, with manual CSV as a reduced fallback when needed, and generate a concise holdings/risk summary with visualization-ready exposure snapshots and user decisions needed today.
15. **Post-order review**: after an order or fill appears, use read-only broker facts when available and ask interactively for entry background, signal bar, confidence, and risk plan; save review context only after user confirmation.
16. **Post-exit review**: after the trade is closed, read objective result from broker-live sources when available and capture exit quality, mistake tags, lessons, and optional statistics snapshot.
17. **Statistics and optimization**: measure win rate, R-multiple, expectancy, drawdown, setup performance, instrument performance, timeframe performance, mistake tags, and confidence calibration when enough broker history or user-approved snapshots are available.
18. **Automation setup checklist**: before creating real Codex automations, confirm the Daily Ops thread, timezone, cadence, `runtime_dir`, allowed sources, runtime write policy, read-only broker permissions, and paywall boundaries through `automation-setup-checklist.md`.

## Public Repo Boundary

This repository keeps only distributable plugin artifacts and user-readable documentation:

- `plugins/`
- `CONTEXT.md`
- `docs/adr/`
- `docs/ROADMAP.md`
- `docs/DEVELOPMENT.md`
- `docs/PROJECT_LOG.md`
- `docs/DEVELOPMENT_PLAN.md`
- `交易研究工作流.md`
- `投资分析提示词.md`
- `.gitignore`

Internal collaboration rules, private trade-analysis material, credentials, and agent coordination docs stay outside this public plugin repository.

A separate development repository is not required at this stage. Codex/Claude collaboration rules can run as the current harness protocol; if private settings or agent coordination templates become durable later, keep them outside this public plugin repository.

## GitHub Trajectory

Project trajectory should be visible on GitHub through four public artifacts:

- commit history for exact code/document changes;
- `docs/PROJECT_LOG.md` for human-readable update records;
- `docs/ROADMAP.md` for current plan, progress, milestones, and next implementation tasks;
- `docs/DEVELOPMENT.md` for development workflow, testing, CI, and Codex/Claude handoff rules;
- `docs/DEVELOPMENT_PLAN.md` for active development priorities, daily planning, and progress review;
- `docs/PLUGIN_CONTENT_PLAN.md` for the minimum useful plugin content checklist and fixture package definition;
- `docs/adr/` for hard-to-reverse architecture decisions.

Update `docs/PROJECT_LOG.md` whenever a change materially affects capability boundaries, execution method, roadmap milestones, schemas, plugin behavior, or external integration decisions.

## Branch Strategy

Use a lightweight branch model:

- `master`: stable baseline for the public plugin repository. It represents the current reviewed canonical state, not a complete product release.
- `dev`: integration branch for reviewed work before it becomes the stable baseline.
- `codex/<task>`: task branches for implementation, documentation, experiments, or Claude Code worker tasks.

Default flow:

```text
codex/<task> -> dev -> master
```

Rules:

- Claude Code works on task branches or isolated worktrees, not directly on `master`.
- Codex reviews task output before merge or promotion.
- `master` receives only staged stable snapshots from `dev`.
- Do not create release tags or public version semantics until the initial complete workflow, production chain, and interaction model are settled.

## Current Progress

| Area | Status | Evidence |
| --- | --- | --- |
| Plugin-first architecture | Done | `docs/adr/0001-plugin-first-interface.md` |
| Chart artifacts instead of dashboard | Done | `docs/adr/0002-chart-artifacts-not-dashboard.md` |
| Plan-scoped intraday scan boundary | Done | `docs/adr/0003-intraday-scan-plan-scoped.md` |
| One-way Google Sheets sync decision | Superseded for trade records | `docs/adr/0004-one-way-google-sheets-sync.md`; `docs/adr/0005-broker-live-position-reporting.md` |
| Broker-live position reporting decision | Done | `docs/adr/0005-broker-live-position-reporting.md` |
| Domain glossary | In progress | `CONTEXT.md` |
| AI-native synthesis contract | Done | `docs/PLUGIN_CONTENT_PLAN.md`; `skills/trading-research-system/references/output-templates.md` |
| Plugin design contract | Done | `docs/PLUGIN_DESIGN.md` |
| AI-native task UX and router fixtures | Done | `README.md`; `plugins/trading-research-system/README.md`; `plugins/trading-research-system/assets/fixtures/input/router-intents.json`; `plugins/trading-research-system/scripts/verify_router_contract.py` |
| Runtime health contract | Done | `skills/trading-research-system/references/runtime-health.md`; `plugins/trading-research-system/scripts/runtime_health.py`; `plugins/trading-research-system/scripts/verify_runtime_health_contract.py`; `plugins/trading-research-system/scripts/verify_runtime_health_selftest.py` |
| Daily Ops Orchestrator contract | Prompt-backed | `skills/trading-research-system/references/daily-ops-orchestrator.md`; `plugins/trading-research-system/assets/templates/daily-ops-orchestrator.md`; `plugins/trading-research-system/assets/templates/ops-state.md`; `plugins/trading-research-system/scripts/verify_daily_ops_orchestrator_contract.py`; setup keys use `ticker + trade_horizon + instrument` |
| Fresh-chat Daily Ops startup health | Done | `runtime_health.py` emits `current_mode` and per-source `broker_source_health`; Daily Ops startup output must include `运行状态检查`, `券商来源健康`, `当前模式`, and formal `runtime_dir` before analysis |
| Macro Data Source Contract | Done | `skills/trading-research-system/references/macro-data-source-contract.md`; Longbridge macrodata is preferred for macro values, IBKR market data confirms price/OHLCV transmission, and outputs must show actual macro indicator reads before claiming macro analysis |
| Longbridge macrodata adapter | Fixture-backed | `plugins/trading-research-system/scripts/longbridge_macrodata_adapter.py`; `plugins/trading-research-system/scripts/verify_longbridge_macrodata_adapter_selftest.py`; saved or tool-returned Longbridge macrodata JSON normalizes to standard `macro-panel.json` without live macrodata reads, broker account reads, or order actions |
| Macro panel runtime preparation | Fixture-backed | `plugins/trading-research-system/scripts/prepare_macro_panel.py`; `plugins/trading-research-system/scripts/verify_prepare_macro_panel_selftest.py`; saved macrodata JSON writes the dated runtime `macro-panel.json`, official fallback uses `--source-capability official_source_fallback`, and missing input produces next-step guidance instead of invented macro reads |
| Longbridge skill adapter contract | Done | `skills/trading-research-system/references/longbridge-skill-adapter.md`; `runtime_health.py` reports `source_capability_health` for Longbridge broker skill, Longbridge Terminal CLI, Longbridge `macrodata`, IBKR connector, and manual snapshot |
| Source Routing Boundary | Done | `CONTEXT.md`; `skills/trading-research-system/references/macro-policy-filter.md`; `skills/trading-research-system/references/output-templates.md`; `plugins/trading-research-system/assets/fixtures/expected/source-routing-longbridge-boundary.md`; Longbridge macrodata can support macro values but must not become the default source for news |
| Fixture-backed local MVP | Done | `docs/MVP_RUNBOOK.md`; `scripts/verify-mvp.sh`; `scripts/verify-plugin.sh`; fixture runtime health, KVN snapshot, intraday scan, position daily report, and contract checks |
| 1.0 Acceptance Plan | Accepted locally on `dev` | `docs/1.0_ACCEPTANCE.md`; `docs/1.0_ACCEPTANCE_RESULTS.md`; `plugins/trading-research-system/scripts/verify_1_0_acceptance_contract.py`; six fresh-chat `local trading research workflow` prompts passed before any public release tag |
| Runtime bootstrap | Done | `plugins/trading-research-system/scripts/bootstrap_runtime.py`; `plugins/trading-research-system/scripts/verify_runtime_bootstrap_selftest.py`; `plugins/trading-research-system/scripts/verify_runtime_bootstrap_contract.py` |
| Broker snapshot ingest | Done | `plugins/trading-research-system/scripts/broker_snapshot_ingest.py`; `plugins/trading-research-system/scripts/verify_broker_snapshot_ingest_selftest.py`; `plugins/trading-research-system/scripts/verify_broker_snapshot_ingest_contract.py`; fixture IBKR/Longbridge position exports normalize to `portfolio_snapshot.csv` |
| IBKR connector adapter | Fixture-backed | `plugins/trading-research-system/scripts/ibkr_connector_adapter.py`; `plugins/trading-research-system/scripts/verify_ibkr_connector_adapter_selftest.py`; `plugins/trading-research-system/scripts/verify_ibkr_connector_adapter_contract.py`; saved read-only `get_account_positions` / `get_account_balances` JSON normalizes to `portfolio_snapshot.csv` without live broker reads or order actions |
| Longbridge Terminal CLI adapter | Done | `plugins/trading-research-system/scripts/longbridge_cli_adapter.py`; `plugins/trading-research-system/scripts/verify_longbridge_cli_adapter_selftest.py`; `plugins/trading-research-system/scripts/verify_longbridge_cli_adapter_contract.py`; saved `longbridge portfolio --format json` snapshots normalize to `portfolio_snapshot.csv` without live broker reads or order actions |
| Portfolio snapshot repair | Fixture-backed | `plugins/trading-research-system/scripts/repair_portfolio_snapshot.py`; `plugins/trading-research-system/scripts/verify_repair_portfolio_snapshot_selftest.py`; repairs stale or unmapped product/theme fields in standard `portfolio_snapshot.csv` before position daily reports, without live broker reads or order actions |
| Longbridge OHLCV adapter | Forward-smoked / fresh-chat verified | `plugins/trading-research-system/scripts/longbridge_ohlcv_adapter.py`; `plugins/trading-research-system/scripts/verify_longbridge_ohlcv_adapter_selftest.py`; saved Longbridge kline JSON normalizes to standard OHLCV JSON for `price_action_rollforward.py` without live broker reads or order actions; prompt #5 rerun passed with saved DRAM/SOXX/QQQ OHLCV artifacts |
| KVN model planning contract | Done | `docs/adr/0006-kvn-model-module-boundary.md`; `docs/KVN_MODEL_PLAN.md` |
| External momentum snapshot compatibility | Internal / hidden | `skills/trading-research-system/references/momentum-leaderboard.md`; `plugins/trading-research-system/scripts/kvn_leaderboard.py`; `plugins/trading-research-system/scripts/verify_kvn_leaderboard_contract.py`; `plugins/trading-research-system/scripts/verify_kvn_leaderboard_selftest.py`; public focused skill is hidden for 1.0 RC |
| Trade Plan Preparation contract | Done | `CONTEXT.md`; `skills/trading-research-system/references/active-market-plan.md`; optional external momentum snapshot wording in templates; `plugins/trading-research-system/scripts/verify_trade_plan_preparation_contract.py` |
| Active Market Plan fixture package | Done | `plugins/trading-research-system/assets/fixtures/runtime/active-market-plan-2026-06-24/`; `plugins/trading-research-system/assets/fixtures/expected/intraday-scan-2026-06-24.md`; `plugins/trading-research-system/scripts/verify_active_market_plan_fixture_contract.py` |
| Broker-live position daily report script | Fixture-backed | `plugins/trading-research-system/scripts/position_daily_report.py`; `plugins/trading-research-system/scripts/verify_position_daily_report_selftest.py`; `plugins/trading-research-system/scripts/verify_position_daily_report_contract.py`; `plugins/trading-research-system/assets/templates/automation-position-daily-report.md`; fixture `position-daily-report.md`; reports concentration, instrument/product exposure, broker/account exposure, cash, and leveraged ETF path risk |
| Research report intake contract | Fixture-backed | `skills/trading-research-system/references/workflow-research-report-intake.md`; `skills/trading-research-system/references/research-report-intake.md`; `plugins/trading-research-system/assets/fixtures/input/research-report-user-provided-ai-infra.md`; `plugins/trading-research-system/assets/fixtures/input/research-report-discovery-ai-infra.md`; `plugins/trading-research-system/assets/fixtures/expected/research-report-intake-ai-infra.md`; `plugins/trading-research-system/assets/fixtures/expected/research-report-discovery-ai-infra.md`; `plugins/trading-research-system/scripts/verify_research_report_intake_contract.py` |
| Two-stage review context | Started | `skills/trading-research-system/references/workflow-trade-review.md`; `skills/trading-research-system/references/interactive-trade-review.md`; `plugins/trading-research-system/scripts/write_trade_review_context.py`; `plugins/trading-research-system/scripts/verify_trade_review_context_selftest.py`; `plugins/trading-research-system/scripts/verify_trade_review_context_contract.py` |
| Setup row preparation | Fresh-chat verified | `plugins/trading-research-system/scripts/prepare_setup_rows.py`; `plugins/trading-research-system/scripts/verify_prepare_setup_rows_selftest.py`; `plugins/trading-research-system/scripts/verify_prepare_setup_rows_contract.py`; consumes user-confirmed setup JSON and writes scanner-ready `trade-plans.csv` / `intraday-watchlist.csv` rows; prompt #3 rerun passed with monitor-only rows |
| Plan-scoped intraday scan script | Fresh-chat verified | `skills/trading-research-system/references/workflow-intraday-setup-scan.md`; `skills/trading-research-system/references/intraday-setup-scan.md`; `plugins/trading-research-system/scripts/intraday_scan.py`; `plugins/trading-research-system/scripts/verify_intraday_scan_selftest.py`; `plugins/trading-research-system/scripts/verify_intraday_scan_contract.py`; prompt #3 rerun rendered 4 `needs_review` rows plus 1 `candidate` row without broker reads or order actions |
| Contract verification modules | Done | `plugins/trading-research-system/scripts/contract_verifier.py`; `plugins/trading-research-system/scripts/verify_contract_verifier_selftest.py`; `plugins/trading-research-system/scripts/contract_suite.py`; `plugins/trading-research-system/scripts/verify_contract_suite.py`; `plugins/trading-research-system/scripts/verify_contract_suite_selftest.py`; `plugins/trading-research-system/scripts/verify_contract_suite_contract.py`; `scripts/verify-plugin.sh` delegates core checks to `verify_contract_suite.py core` |
| Release surface hidden-quant contract | Done | `plugins/trading-research-system/scripts/verify_release_surface_contract.py`; default README/router/skill/template surface does not expose external quant model modules |
| Price Action rollforward contract | Done | `plugins/trading-research-system/scripts/verify_price_action_rollforward_contract.py`; PA output must include previous-analysis comparison, timeframe roles, support/resistance levels, cost/buy-record context, proportional add/reduce sizing, and weekly event mapping |
| Content & Visualization Artifact System MVP | Review | `plugins/trading-research-system/scripts/visual_artifacts.py`; `plugins/trading-research-system/scripts/chart_artifact.py`; `plugins/trading-research-system/scripts/macro_regime_artifact.py`; PA uses canonical Lightweight Charts v5.2.0 HTML plus browser capture, handcrafted SVG is no-browser fallback, and optional manifest-backed local save requires explicit opt-in |
| Visual Trigger Policy | Prompt-backed | `skills/trading-research-system/references/visual-trigger-policy.md`; `plugins/trading-research-system/scripts/verify_visual_trigger_contract.py`; defines when Daily Ops, weekly, quick update, rolling PA, intraday scan, position report, and review outputs should show chat-first visuals |
| Canonical record schema module | Compatibility | `plugins/trading-research-system/scripts/record_schemas.py`; `plugins/trading-research-system/scripts/verify_record_templates_contract.py` |
| Actual trade record module | Compatibility | `plugins/trading-research-system/scripts/trade_records.py`; `plugins/trading-research-system/scripts/update_trade_record.py`; `plugins/trading-research-system/scripts/verify_trade_record_update_selftest.py` |
| Legacy active import module | Deferred compatibility | `plugins/trading-research-system/scripts/import_legacy_active_csv.py`; `plugins/trading-research-system/scripts/verify_legacy_active_import_selftest.py` |
| Portable Skill architecture | Done | One canonical `skills/trading-research-system/` package; focused workflows are internal references; Codex/Claude wrappers are generated and drift-checked |
| Local templates | Started | `plugins/trading-research-system/assets/templates/` |
| Local utility scripts | Started | `plugins/trading-research-system/scripts/` |
| Active Market Plan update loop | Started | `docs/ROADMAP.md`; `skills/trading-research-system/references/active-market-plan.md` |
| Broker-live data contract | Started | `skills/trading-research-system/references/broker-data-contract.md` |
| Automation contract | Prompt-backed | `skills/trading-research-system/references/automation-contract.md`; `plugins/trading-research-system/assets/templates/automation-active-plan-deep-update.md`; `plugins/trading-research-system/assets/templates/automation-active-plan-quick-update.md`; `plugins/trading-research-system/assets/templates/automation-intraday-trigger-monitor.md`; `plugins/trading-research-system/assets/templates/automation-post-market-review.md`; `plugins/trading-research-system/assets/templates/automation-position-daily-report.md`; `plugins/trading-research-system/scripts/verify_active_plan_automation_contract.py` |
| Active Plan automation prompts | Done | `plugins/trading-research-system/assets/templates/automation-active-plan-deep-update.md`; `plugins/trading-research-system/assets/templates/automation-active-plan-quick-update.md`; `plugins/trading-research-system/assets/templates/automation-intraday-trigger-monitor.md`; `plugins/trading-research-system/assets/templates/automation-post-market-review.md`; `plugins/trading-research-system/assets/templates/automation-position-daily-report.md` |
| Scheduled macro/industry research monitor | Prompt-backed | `plugins/trading-research-system/assets/templates/automation-macro-industry-research-monitor.md`; `plugins/trading-research-system/assets/fixtures/input/macro-industry-monitor-focus-2026-07-06.md`; `plugins/trading-research-system/assets/fixtures/expected/macro-industry-monitor-2026-07-06.md`; `plugins/trading-research-system/scripts/verify_macro_industry_research_monitor_contract.py` |
| Automation setup checklist | Prompt-backed | `plugins/trading-research-system/assets/templates/automation-setup-checklist.md`; `plugins/trading-research-system/assets/fixtures/input/automation-setup-request-daily-ops.md`; `plugins/trading-research-system/assets/fixtures/expected/automation-setup-checklist-daily-ops.md`; `plugins/trading-research-system/scripts/verify_automation_setup_contract.py`; real Codex automations still require setup confirmation |
| Trading profile template | Started | `plugins/trading-research-system/assets/templates/trading-profile.md` |
| Intraday status model | Script-backed | `skills/trading-research-system/references/intraday-setup-scan.md`; `plugins/trading-research-system/scripts/intraday_scan.py` |
| Development workflow norms | Done | `docs/DEVELOPMENT.md` |
| Basic plugin content plan | Done | `docs/PLUGIN_CONTENT_PLAN.md` |
| Daily development task-planning automation loop | Done | `docs/DEVELOPMENT_PLAN.md`; Codex automations `dailytrades-weekday-development-brief` and `dailytrades-end-of-day-progress-review` |
| Position daily report automation | Prompt-backed | `skills/trading-research-system/references/automation-contract.md`; `plugins/trading-research-system/assets/templates/automation-position-daily-report.md` |
| Google Sheets summary display | Deferred | no script yet |
| OHLCV-driven chart/scan artifacts | Started | `plugins/trading-research-system/scripts/chart_artifact.py`; now folded into the Content & Visualization Artifact System MVP as chat-first visual artifacts plus optional HTML inspection output |
| Option-flow anomaly module | Planned | data vendor not selected |

## Task Breakdown

### P0: Domain Language And Note Templates

Status: in progress.

Deliverables:

- Maintain canonical glossary in `CONTEXT.md`.
- Maintain Active Market Plan, update note, research memo, and trade plan output templates.
- Maintain Daily Ops Orchestrator and `ops-state.md` templates so users can start or continue the workflow without manually calling each focused workflow.
- Keep `trading-research-system` as the single public Skill and router.
- Maintain internal workflow references for research report intake, Active Market Plan deep updates, quick updates, intraday scan, trade review, macro/equity research, portfolio risk, and trading statistics. External quantitative momentum modules stay hidden unless the user provides a separate snapshot.
- Keep active plan, broker data, macro, equity screening, price action, intraday scan, risk, journal, and output references shared inside the plugin.
- Keep automation rules aligned with the Active Market Plan loop and broker read-only boundary.
- Keep the plugin installable from the personal marketplace.

Exit criteria:

- A new agent can understand the core language from `CONTEXT.md`.
- The router can send report intake, research, planning, intraday scan, review, risk, and statistics tasks to internal workflows and shared references, while hidden external quantitative modules remain optional inputs rather than public workflows.

### P1: Local Data Structure

Status: started.

Deliverables:

- Runtime root convention: `{runtime_dir}`, defaulting to `~/Documents/dailytrades-runtime`.
- Active plan convention: `{runtime_dir}/market-plan.md`.
- Private trading profile convention: `{runtime_dir}/trading-profile.md`.
- Profile-configured strategy posture scores, trading pools, ETF groups, crowding model, and timeframe rules.
- Append-only update convention: `{runtime_dir}/updates/YYYY-MM-DD.md`.
- Daily directory convention: `{runtime_dir}/daily/YYYY-MM-DD/`.
- Deep update convention for last-week trade review, current market tape, macro/rates, policy/news, event preview, Trade Plan Preparation, themes, setup pool, and risk budget.
- Quick update convention for current market read, fast macro/policy/news update, event preview, momentum changes, setup status changes, level updates, and attention priority.
- Broker-live data convention for authorized read-only runtime views, with optional raw snapshots only when the user asks or a fixture/debug run needs local files.
- Templates for `market-plan.md`, `trading-profile.md`, `weekly-plan.md`, `daily-market-tracking.md`, `watchlist.csv`, `trade-plans.csv`, `intraday-watchlist.csv`, `holdings.csv`, broker-live fixture views, position daily report snapshots, `reviews.md`, `research-note-log.csv`, `research-report-log.csv`, and `daily-macro-checklist.md`.
- `init_daily.py` to create a daily folder from templates.
- Local plan and review artifacts remain the source of truth for discretionary context; broker facts are read live from authorized sources.

Exit criteria:

- A trading day can be initialized locally.
- Active Market Plan, update notes, planned setups, intraday watch state, position daily reports, visualization snapshots, and review notes can be stored without Google Sheets.

### P2: Analysis Modules

Status: started.

Deliverables:

- `momentum-leaderboard` skill and a KVN snapshot import/storage script backed by `{runtime_dir}/momentum/kvn.sqlite`.
- KVN fields: `Rank vs S&P500`, `Ticker`, `KVN 分数`, `KVN P`, `当前是否 S&P500`, `连续入选Top10天数`, `近20日入选Top10次数`, and `上次入选Top10时间`.
- `portfolio_risk.py` for portfolio exposure summaries.
- `watchlist_score.py` for candidate prioritization.
- `trade_stats.py` for closed-trade statistics.
- Macro/rates filter reference.
- Research report intake and verification reference.
- Research-note verification reference.
- Price action timing reference.
- Intraday setup scan reference.
- Future option-flow anomaly reference after vendor selection.

Exit criteria:

- The plugin can import or read the latest KVN leaderboard snapshot, display Top10, query any symbol, and summarize Top10 changes without treating the leaderboard as a buy list.
- The plugin can produce Trade Plan Preparation input reads and a Cross-Section Candidate Pool from structured inputs and current-source verification.
- The plugin can rank watchlist candidates from CSV input.
- The plugin can evaluate whether a prepared setup is candidate, active, approaching, triggered, invalidated, needs review, or completed.

### P3: Review Statistics And System Optimization

Status: planned.

Deliverables:

- Win rate, average R, expectancy, and drawdown.
- Setup, instrument, timeframe, and confidence performance.
- Mistake-tag frequency.
- Two-stage review workflow that distinguishes post-order entry review from post-exit outcome review.
- System optimization notes based on statistically meaningful samples.

Exit criteria:

- Closed trades can be grouped by setup, instrument type, timeframe, and mistake tag.
- Review notes can explain whether losses came from setup quality, execution quality, sizing, event risk, or normal variance.

### P4: External Connections And Automation

Status: planned.

Deliverables:

- Optional non-sensitive Google Sheets summary display if explicitly requested.
- Google Drive research archive support.
- External connector or broker skill-provided read-only market/account data use for market state, holdings, executions, order status, and chart artifacts.
- Option data API integration after vendor research.
- Daily market brief.
- Weekly trading plan brief.
- Intraday plan monitor.
- Post-order review prompt.
- Post-exit review prompt.

Exit criteria:

- Local daily records can mirror to Google Sheets without treating Sheets as source of truth.
- Intraday scans can use current market data instead of manual chart descriptions.
- Daily and post-market workflows can be scheduled or triggered reliably.
- Automations ask before editing local plan/review artifacts and never touch broker write actions.

## Milestone Plan

### M1: Planning Baseline

Target result:

- Public roadmap, capability boundaries, execution method, task breakdown, and progress status are documented.
- Minimum useful plugin content and fixture package requirements are documented.
- Plugin validates and installs after documentation/reference updates.

### M2: Local Workflow MVP

Target result:

- User can maintain an Active Market Plan, initialize a trading day, parse current market state against that plan, create setup-level trade plans, update levels, track intraday state manually, generate broker-live position daily reports, capture two-stage review context, and run basic stats from broker history or approved snapshots.
- User can attach Codex automations to deep update, quick update, intraday monitor, post-market review, and development progress workflows without changing the broker read-only boundary.
- Weekday development automations can recommend and review daily project tasks from the current roadmap without duplicating trading-operation automations.

### M3: Data-Assisted Research MVP

Target result:

- User can run KVN momentum ranking, macro/rates regime filtering, research validation, price action timing, and portfolio risk review in one repeatable note template.

### M4: Sync And Review MVP

Target result:

- Google Sheets trade-record sync is out of the main path; optional summary display can be reconsidered later.
- Interactive trade review captures post-order and post-exit context, with objective facts read from broker-live sources when available.

### M5: Intraday Monitor MVP

Target result:

- Prepared trade plans can be scanned against current market data and sorted by attention priority.
- Chart artifacts can be generated for the plans needing review.

## Next Implementation Tasks

1. Ask the user before promoting the accepted local workflow from `dev` to
   `master`; do not create release tags or public version semantics yet.
2. Finalize Daily Ops Orchestrator fixtures and `ops-state.md` behavior before enabling real trading-operation automations.
3. Forward-test the `Visual Trigger Policy` in Daily Ops, weekly planning, PA
   rollforward, intraday scan, and position daily report so macro and PA charts
   appear only when the trigger matrix says they should.
4. Add richer chart artifact generation from fixture-backed authorized OHLCV data.
5. Research option-flow data vendors and define the minimum anomaly schema outside the core MVP path.
6. Create user-confirmed Codex automations for Active Market Plan deep update, quick update, intraday monitor, post-market review, position daily report, and scheduled macro/industry research monitor after cadence and data-source permissions are confirmed.
7. Connect real read-only source adapters to the standard runtime views:
   Longbridge skill/Terminal CLI adapter for read-only broker facts, IBKR connector adapter
   for read-only broker/market facts, and Longbridge `macrodata` adapter for
   macro panel values.

## MVP 1 Acceptance Criteria

MVP 1 is complete when:

1. The plugin contains the research workflow skill and references.
2. Local CSV/Markdown templates exist for watchlist, trade plans, intraday plans, trades, reviews, research-note logs, and portfolio holdings.
3. Scripts can initialize a trading day, summarize portfolio exposure, import/read KVN momentum snapshots, rank watchlist candidates, append reviews, and compute basic trade statistics.
4. The trade journal schema can represent the current `2026交易记录` fields plus missing statistics fields.
5. Intraday scan statuses and attention priority are documented.
6. The plugin validates and can be installed from the personal marketplace.
