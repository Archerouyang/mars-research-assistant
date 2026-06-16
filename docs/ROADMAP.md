# Trading Research System Roadmap

## Project Goal

Trading Research System is a plugin-first trading research and risk decision-support system for Codex. It turns market information into an overwriteable Active Market Plan, append-only update notes, setup-level trade plans, intraday setup scans, actual trade records, review notes, broker-aware portfolio snapshots, and statistics for improving a discretionary trading system.

The first product surface is a Codex plugin with skills, references, scripts, templates, and local records. A standalone frontend is deferred.

The product is AI-native. Its core value is not producing long reports; it is making the agent read broadly, verify facts, filter noise, and return concise decision-useful notes to the user.

## Capability Boundaries

The system supports:

- agent-heavy research synthesis that compresses large source sets into conclusions, changed variables, invalidations, setup status, and next checks;
- macro policy and rates filtering focused on market-moving variables;
- research-note and market-view validation against primary/current sources;
- equity and ETF screening with momentum, thesis, catalyst, and risk context;
- Al Brooks-style high-level price action timing with 20 EMA, 50 EMA, and multi-timeframe context;
- Active Market Plan maintenance with overwriteable current state and append-only update history;
- trading profile support for personal style, instrument preferences, and setup-to-instrument translation without storing account allocation in the public repo;
- automation-ready Active Market Plan deep updates, quick updates, intraday monitor prompts, and post-market review prompts;
- deep updates that include prior-week trade review, current market tape, macro/rates context, policy/news filtering, major event preview, momentum leaderboard rebuild, and setup discovery;
- quick updates for weekday premarket/intraday changes in tape, macro/rates, policy/news, events, momentum, setup status, and key levels;
- setup-scoped intraday scanning for `candidate`, `active`, `approaching`, `triggered`, `invalidated`, `needs_review`, and `completed` states;
- local trade planning, read-only broker fact capture when available, two-stage interactive trade review, and statistics;
- portfolio risk exposure checks before and after trades, using canonical broker data when available;
- broker-agnostic read-only adapter contract for IBKR, Longbridge, and manual CSV sources;
- one-way local-to-Google-Sheets sync as a later mirror/review layer.

The system does not support in the initial scope:

- auto-order placement, order modification, or fully automated trading;
- guaranteed buy/sell instructions;
- unbounded whole-market real-time intraday scanning without an Active Market Plan theme, watchlist, or prepared setup;
- two-way Google Sheets sync;
- a persistent dashboard/frontend;
- unverified paywalled research extraction;
- tax, legal, or regulated investment advice.

## Execution Method

The default workflow is:

1. **Information collection**: gather macro policy, Treasury/rates/yield data, research-note claims, company facts, prices, watchlists, trade plans, and holdings.
2. **Information processing**: filter noise, classify source reliability, normalize inputs into local daily records, and separate facts from assumptions.
3. **Trade idea formation**: state long/short thesis, catalyst, counter-thesis, invalidation, and risk.
4. **Information verification**: cross-check research claims against primary sources, current data, price behavior, and counter-evidence.
5. **Trade Plan Preparation**: compress Macro Regime, Financial Conditions, Policy/Event Risk, Industry/Sector Strength, and Company Thesis Check into input reads and a Cross-Section Candidate Pool before creating setup rows. Quant momentum candidate pools are a separate future model.
6. **Setup analysis**: classify higher-timeframe regime from 4H/1D/1W, map it to strategy bias, then use 1H and lower only for execution observation, trigger zone, invalidation, and next check.
7. **Active Market Plan deep update**: review prior trades when relevant, analyze current tape, macro/rates, policy, news, future event risk, Trade Plan Preparation, setup pool, invalidation, trigger timeframe, and risk budget; overwrite `{runtime_dir}/market-plan.md` and append the rationale to `{runtime_dir}/updates/YYYY-MM-DD.md`.
8. **Active Market Plan quick update**: parse today's tape, macro/rates, policy, news, event preview, and setup-relevant changes against `market-plan.md`; update setup statuses, trigger zones, invalidation levels, targets, and which setups are approaching, triggered, invalidated, completed, or require review.
9. **Setup planning**: write structured setup-level rows to `trade-plans.csv` and, when needed, `intraday-watchlist.csv`.
10. **Intraday scan**: monitor prepared setups and high-priority watchlist ideas; classify setups as `candidate`, `active`, `approaching`, `triggered`, `invalidated`, `needs_review`, or `completed`.
11. **Post-order review**: after an order or fill appears, use read-only broker facts when available and ask interactively for entry background, signal bar, confidence, and risk plan; write or update an `open` row in `trades.csv`.
12. **Post-exit review**: after the trade is closed, update result, exit quality, realized R, mistake tags, and lessons in `trades.csv` plus narrative notes in `reviews.md`.
13. **Statistics and optimization**: measure win rate, R-multiple, expectancy, drawdown, setup performance, instrument performance, timeframe performance, mistake tags, and confidence calibration.

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
| One-way Google Sheets sync decision | Done | `docs/adr/0004-one-way-google-sheets-sync.md` |
| Domain glossary | In progress | `CONTEXT.md` |
| AI-native synthesis contract | Done | `docs/PLUGIN_CONTENT_PLAN.md`; `plugins/trading-research-system/skills/trading-research/references/output-templates.md` |
| Trade Plan Preparation contract | Started | `CONTEXT.md`; `plugins/trading-research-system/skills/trading-research/references/active-market-plan.md`; `plugins/trading-research-system/scripts/verify_trade_plan_preparation_contract.py` |
| Skill set architecture | Started | Router skill plus focused skills under `plugins/trading-research-system/skills/` |
| Local templates | Started | `plugins/trading-research-system/assets/templates/` |
| Local utility scripts | Started | `plugins/trading-research-system/scripts/` |
| Active Market Plan update loop | Started | `docs/ROADMAP.md`; `plugins/trading-research-system/skills/trading-research/references/active-market-plan.md` |
| Broker data contract | Started | `plugins/trading-research-system/skills/trading-research/references/broker-data-contract.md` |
| Automation contract | Started | `plugins/trading-research-system/skills/trading-research/references/automation-contract.md` |
| Trading profile template | Started | `plugins/trading-research-system/assets/templates/trading-profile.md` |
| Intraday status model | Started | `references/intraday-setup-scan.md` |
| Development workflow norms | Done | `docs/DEVELOPMENT.md` |
| Basic plugin content plan | Done | `docs/PLUGIN_CONTENT_PLAN.md` |
| Daily development task-planning automation loop | Done | `docs/DEVELOPMENT_PLAN.md`; Codex automations `dailytrades-weekday-development-brief` and `dailytrades-end-of-day-progress-review` |
| Google Sheets sync implementation | Planned | no script yet |
| OHLCV-driven chart/scan artifacts | Started | `plugins/trading-research-system/scripts/chart_artifact.py` |
| Option-flow anomaly module | Planned | data vendor not selected |

## Task Breakdown

### P0: Domain Language And Note Templates

Status: in progress.

Deliverables:

- Maintain canonical glossary in `CONTEXT.md`.
- Maintain Active Market Plan, update note, research memo, and trade plan output templates.
- Keep `trading-research` as the router skill.
- Maintain focused skills for Active Market Plan deep updates, quick updates, intraday scan, trade review, macro/equity research, portfolio risk, and trading statistics.
- Keep active plan, broker data, macro, equity screening, price action, intraday scan, risk, journal, and output references shared inside the plugin.
- Keep automation rules aligned with the Active Market Plan loop and broker read-only boundary.
- Keep the plugin installable from the personal marketplace.

Exit criteria:

- A new agent can understand the core language from `CONTEXT.md`.
- The router can send research, planning, intraday scan, review, risk, and statistics tasks to focused skills and shared references.

### P1: Local Data Structure

Status: started.

Deliverables:

- Runtime root convention: `{runtime_dir}`, defaulting to `~/Documents/dailytrades-runtime`.
- Active plan convention: `{runtime_dir}/market-plan.md`.
- Private trading profile convention: `{runtime_dir}/trading-profile.md`.
- Append-only update convention: `{runtime_dir}/updates/YYYY-MM-DD.md`.
- Daily directory convention: `{runtime_dir}/daily/YYYY-MM-DD/`.
- Deep update convention for last-week trade review, current market tape, macro/rates, policy/news, event preview, Trade Plan Preparation, themes, setup pool, and risk budget.
- Quick update convention for current market read, fast macro/policy/news update, event preview, momentum changes, setup status changes, level updates, and attention priority.
- Broker data convention for raw snapshots under `{runtime_dir}/broker/<source>/YYYY-MM-DD/` and canonical daily CSV files.
- Templates for `market-plan.md`, `trading-profile.md`, `weekly-plan.md`, `daily-market-tracking.md`, `watchlist.csv`, `trade-plans.csv`, `intraday-watchlist.csv`, `trades.csv`, `holdings.csv`, `portfolio_snapshot.csv`, `broker_executions.csv`, `broker_orders.csv`, `reviews.md`, `research-note-log.csv`, and `daily-macro-checklist.md`.
- `init_daily.py` to create a daily folder from templates.
- Local records remain the first source of truth.

Exit criteria:

- A trading day can be initialized locally.
- Active Market Plan, update notes, planned setups, intraday watch state, broker canonical data, actual trades, and review notes can be stored without Google Sheets.

### P2: Analysis Modules

Status: started.

Deliverables:

- `portfolio_risk.py` for portfolio exposure summaries.
- `watchlist_score.py` for candidate prioritization.
- `trade_stats.py` for closed-trade statistics.
- Macro/rates filter reference.
- Research-note verification reference.
- Price action timing reference.
- Intraday setup scan reference.
- Future option-flow anomaly reference after vendor selection.

Exit criteria:

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

- One-way Google Sheets sync from local daily records.
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
- Automations ask before editing local plan/trade records and never touch broker write actions.

## Milestone Plan

### M1: Planning Baseline

Target result:

- Public roadmap, capability boundaries, execution method, task breakdown, and progress status are documented.
- Minimum useful plugin content and fixture package requirements are documented.
- Plugin validates and installs after documentation/reference updates.

### M2: Local Workflow MVP

Target result:

- User can maintain an Active Market Plan, initialize a trading day, parse current market state against that plan, create setup-level trade plans, update levels, track intraday state manually, reconcile read-only broker facts, record actual trades, append two-stage reviews, and run basic stats locally.
- User can attach Codex automations to deep update, quick update, intraday monitor, post-market review, and development progress workflows without changing the broker read-only boundary.
- Weekday development automations can recommend and review daily project tasks from the current roadmap without duplicating trading-operation automations.

### M3: Data-Assisted Research MVP

Target result:

- User can run macro/rates, research validation, watchlist ranking, price action timing, and portfolio risk review in one repeatable note template.

### M4: Sync And Review MVP

Target result:

- Local records sync one-way to Google Sheets.
- Interactive trade review produces post-order and post-exit updates to structured `trades.csv` rows plus daily `reviews.md`.

### M5: Intraday Monitor MVP

Target result:

- Prepared trade plans can be scanned against current market data and sorted by attention priority.
- Chart artifacts can be generated for the plans needing review.

## Next Implementation Tasks

1. Forward-test router behavior and each priority skill on realistic Active Market Plan prompts.
2. Add Trade Plan Preparation fixture data that covers input reads, Cross-Section Candidate Pool, and promotion into `candidate setup`.
3. Add sample Active Market Plan fixture data that covers `market-plan.md`, update notes, event previews, setup pool, canonical broker CSV, post-order review, post-exit review, and expected scan outputs.
4. Add an intraday scan script that reads setup-level plan data and emits status/attention summaries after setup pool fields are stable.
5. Connect interactive review intake to post-order and post-exit `trades.csv` updates.
6. Add a Google Sheets one-way sync script for local `trades.csv`, `trade-plans.csv`, and holdings data.
7. Add chart artifact generation from fixture-backed authorized OHLCV data.
8. Research option-flow data vendors and define the minimum anomaly schema.
9. Create user-confirmed Codex automations for Active Market Plan deep update, quick update, intraday monitor, and post-market review after cadence and data-source permissions are confirmed.

## MVP 1 Acceptance Criteria

MVP 1 is complete when:

1. The plugin contains the research workflow skill and references.
2. Local CSV/Markdown templates exist for watchlist, trade plans, intraday plans, trades, reviews, research-note logs, and portfolio holdings.
3. Scripts can initialize a trading day, summarize portfolio exposure, rank watchlist candidates, append reviews, and compute basic trade statistics.
4. The trade journal schema can represent the current `2026交易记录` fields plus missing statistics fields.
5. Intraday scan statuses and attention priority are documented.
6. The plugin validates and can be installed from the personal marketplace.
