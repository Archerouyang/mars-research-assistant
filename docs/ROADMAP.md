# Trading Research System Roadmap

## Project Goal

Trading Research System is a plugin-first trading research and risk decision-support system for Codex. It turns market information into verified research notes, planned trades, intraday setup scans, actual trade records, review notes, and statistics for improving a discretionary trading system.

The first product surface is a Codex plugin with skills, references, scripts, templates, and local records. A standalone frontend is deferred.

## Capability Boundaries

The system supports:

- macro policy and rates filtering focused on market-moving variables;
- research-note and market-view validation against primary/current sources;
- equity and ETF screening with momentum, thesis, catalyst, and risk context;
- Al Brooks-style high-level price action timing with 20 EMA, 50 EMA, and multi-timeframe context;
- plan-scoped intraday setup scanning for prepared trade plans;
- local trade planning, actual-trade recording, interactive trade review, and statistics;
- portfolio risk exposure checks before and after trades;
- one-way local-to-Google-Sheets sync as a later mirror/review layer.

The system does not support in the initial scope:

- auto-order placement or fully automated trading;
- guaranteed buy/sell instructions;
- whole-market real-time intraday opportunity discovery;
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
5. **Setup analysis**: classify market state, trade type, higher-timeframe background, 20/50 EMA context, trigger, stop, and targets.
6. **Plan creation**: write structured `trade-plans.csv` rows and, when needed, `intraday-watchlist.csv` rows.
7. **Intraday scan**: monitor only prepared plans and classify them as `waiting`, `approaching`, `triggered`, `invalidated`, or `needs_review`.
8. **Actual trade review**: collect execution facts through interactive review intake and append structured records to `trades.csv` plus narrative notes to `reviews.md`.
9. **Statistics and optimization**: measure win rate, R-multiple, expectancy, drawdown, setup performance, instrument performance, timeframe performance, mistake tags, and confidence calibration.

## Public Repo Boundary

This repository keeps only distributable plugin artifacts and user-readable documentation:

- `plugins/`
- `CONTEXT.md`
- `docs/adr/`
- `docs/ROADMAP.md`
- `docs/PROJECT_LOG.md`
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
| Core skill routing | Started | `plugins/trading-research-system/skills/trading-research/SKILL.md` |
| Local templates | Started | `plugins/trading-research-system/assets/templates/` |
| Local utility scripts | Started | `plugins/trading-research-system/scripts/` |
| Intraday status model | Started | `references/intraday-setup-scan.md` |
| Google Sheets sync implementation | Planned | no script yet |
| IBKR-driven chart/scan artifacts | Planned | no artifact generator yet |
| Option-flow anomaly module | Planned | data vendor not selected |

## Task Breakdown

### P0: Domain Language And Note Templates

Status: in progress.

Deliverables:

- Maintain canonical glossary in `CONTEXT.md`.
- Maintain research memo and trade plan output templates.
- Keep macro, equity screening, price action, intraday scan, risk, journal, and output references inside the plugin skill.
- Keep the plugin installable from the personal marketplace.

Exit criteria:

- A new agent can understand the core language from `CONTEXT.md`.
- The skill can route research, planning, intraday scan, review, and statistics tasks to the right reference files.

### P1: Local Data Structure

Status: started.

Deliverables:

- Daily directory convention: `data/daily/YYYY-MM-DD/`.
- Templates for `watchlist.csv`, `trade-plans.csv`, `intraday-watchlist.csv`, `trades.csv`, `holdings.csv`, `reviews.md`, `research-note-log.csv`, and `daily-macro-checklist.md`.
- `init_daily.py` to create a daily folder from templates.
- Local records remain the first source of truth.

Exit criteria:

- A trading day can be initialized locally.
- Planned trades, intraday watch state, actual trades, and review notes can be stored without Google Sheets.

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

- The plugin can produce a complete research note from structured inputs and current-source verification.
- The plugin can rank watchlist candidates from CSV input.
- The plugin can evaluate whether a prepared intraday plan is waiting, approaching, triggered, invalidated, or needs review.

### P3: Review Statistics And System Optimization

Status: planned.

Deliverables:

- Win rate, average R, expectancy, and drawdown.
- Setup, instrument, timeframe, and confidence performance.
- Mistake-tag frequency.
- Review workflow that distinguishes trade quality from outcome.
- System optimization notes based on statistically meaningful samples.

Exit criteria:

- Closed trades can be grouped by setup, instrument type, timeframe, and mistake tag.
- Review notes can explain whether losses came from setup quality, execution quality, sizing, event risk, or normal variance.

### P4: External Connections And Automation

Status: planned.

Deliverables:

- One-way Google Sheets sync from local daily records.
- Google Drive research archive support.
- IBKR price/account data use for market state, holdings, and chart artifacts.
- Option data API integration after vendor research.
- Daily market brief.
- Intraday plan monitor.
- Post-market review prompt.

Exit criteria:

- Local daily records can mirror to Google Sheets without treating Sheets as source of truth.
- Intraday scans can use current market data instead of manual chart descriptions.
- Daily and post-market workflows can be scheduled or triggered reliably.

## Milestone Plan

### M1: Planning Baseline

Target result:

- Public roadmap, capability boundaries, execution method, task breakdown, and progress status are documented.
- Plugin validates and installs after documentation/reference updates.

### M2: Local Workflow MVP

Target result:

- User can initialize a trading day, create trade plans, track intraday state manually, record actual trades, append reviews, and run basic stats locally.

### M3: Data-Assisted Research MVP

Target result:

- User can run macro/rates, research validation, watchlist ranking, price action timing, and portfolio risk review in one repeatable note template.

### M4: Sync And Review MVP

Target result:

- Local records sync one-way to Google Sheets.
- Interactive trade review produces structured `trades.csv` rows and daily `reviews.md`.

### M5: Intraday Monitor MVP

Target result:

- Prepared trade plans can be scanned against current market data and sorted by attention priority.
- Chart artifacts can be generated for the plans needing review.

## Next Implementation Tasks

1. Add a Google Sheets one-way sync script for local `trades.csv`, `trade-plans.csv`, and holdings data.
2. Add an intraday scan script that reads `intraday-watchlist.csv` and emits status/attention summaries.
3. Add sample daily fixture data to test end-to-end local workflow scripts.
4. Add chart artifact generation from authorized OHLCV data.
5. Research option-flow data vendors and define the minimum anomaly schema.

## MVP 1 Acceptance Criteria

MVP 1 is complete when:

1. The plugin contains the research workflow skill and references.
2. Local CSV/Markdown templates exist for watchlist, trade plans, intraday plans, trades, reviews, research-note logs, and portfolio holdings.
3. Scripts can initialize a trading day, summarize portfolio exposure, rank watchlist candidates, append reviews, and compute basic trade statistics.
4. The trade journal schema can represent the current `2026交易记录` fields plus missing statistics fields.
5. Intraday scan statuses and attention priority are documented.
6. The plugin validates and can be installed from the personal marketplace.
