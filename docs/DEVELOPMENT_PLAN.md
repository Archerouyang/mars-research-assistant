# Development Plan

This document is the public source of truth for Dailytrades plugin development planning and progress. It is used by the weekday development brief and end-of-day progress review automations.

Do not include private trade records, credentials, account details, unpublished research excerpts, or internal agent prompts. Keep this focused on project execution.

## Current Development Phase

Phase: local trading research workflow MVP.

Goal: make the plugin usable for the core local trading research loop before adding heavier external integrations: build weekly trading plans, parse the current market against those plans, scan planned setups, record actual trades, run two-stage trade reviews, and compute basic statistics.

## Planning North Star

Daily development planning should prioritize product capability, not process work.

The current product sequence is:

1. weekly trading plan and local daily records;
2. fixture data covering weekly plans, daily market tracking, prepared plans, IBKR-like trade facts, and two-stage reviews;
3. daily market parsing and dynamic tracking against the weekly plan;
4. plan-scoped intraday setup scan;
5. post-order review to create or update open `trades.csv` rows;
6. post-exit review to complete results, lessons, and `reviews.md`;
7. basic stats and system review;
8. one-way Google Sheets sync;
9. OHLCV-backed chart artifacts;
10. option-flow anomaly research.

Development workflow, TDD, CI, worktree policy, and Claude/Codex handoff rules are support rails. They should be mentioned when relevant, but should not become the recommended main task unless they are directly blocking a product capability.

## Daily Development Loop

Weekday morning brief:

1. Inspect `docs/DEVELOPMENT_PLAN.md`, `docs/ROADMAP.md`, `docs/PROJECT_LOG.md`, `CONTEXT.md`, and current git status.
2. Report current development tasks with priority.
3. Recommend one product-capability main task for today.
4. Ask the user how to arrange the day:
   - available time;
   - chosen main task;
   - optional secondary task;
   - definition of done;
   - expected verification;
   - whether progress should update this document, public roadmap/log, or both.

End-of-day progress review:

1. Ask what was planned, completed, verified, committed, pushed, blocked, or deferred.
2. Update the task board and progress log after confirmation.
3. Update `docs/PROJECT_LOG.md` only when the change affects public project trajectory.
4. Do not invent progress.

## Priority Rules

Use these priority levels:

- `P0`: needed to make the plugin workflow coherent, safe, or usable.
- `P1`: needed for the local MVP workflow.
- `P2`: needed for analysis depth or automation, but not a blocker for local MVP.
- `P3`: later optimization or expansion.

Use these statuses:

- `planned`
- `ready`
- `in_progress`
- `blocked`
- `review`
- `done`
- `deferred`

## Active Task Board

| Priority | Status | Task | Why It Matters | Next Action |
| --- | --- | --- | --- | --- |
| P0 | done | Establish public planning baseline | Gives the project capability boundaries, execution method, task breakdown, and progress tracking. | Keep roadmap and project log updated as decisions change. |
| P0 | done | Define branch strategy | Keeps Codex/Claude task work isolated and gives GitHub a clear trajectory. | Use `codex/<task> -> dev -> master`. |
| P0 | done | Establish daily development automation loop | Gives each weekday a repeatable brief, task-priority review, planning interaction, and end-of-day progress update. | Use the weekday brief and end-of-day review to keep this document current. |
| P0 | done | Define development workflow and test scope | Keeps Claude/Codex work bounded while avoiding live external service tests. | Use it as the acceptance gate for implementation tasks. |
| P1 | in_progress | Add sample weekly/daily fixture data | Gives scripts stable inputs for tests and demos without using live broker or Google data. | Define the fixture package for weekly plans, daily market tracking, plans, intraday watchlist, holdings, IBKR-like trade facts, two-stage reviews, and expected scan outputs. |
| P1 | done | Add weekly plan and daily market tracking templates | Supports the user's current hard need: build initial trade ideas and plans, then track them dynamically as the market changes. | Use these templates in the fixture package and later script flows. |
| P1 | ready | Implement local intraday scan script | Turns documented scan states into executable status and attention-priority summaries. | Build with TDD from fixture CSVs. |
| P1 | ready | Connect two-stage interactive review output to local trade records | Makes post-order and post-exit reviews produce structured `trades.csv` updates plus `reviews.md` sections. | Extend current review append flow with CSV row create/update support. |
| P1 | ready | Add lightweight test harness | Gives product implementation tasks a local acceptance gate before CI exists. | Add only the tests needed for the next product task. |
| P2 | planned | Add one-way Google Sheets sync | Mirrors local records to Sheets without making Sheets the source of truth. | Define row mapping and fixture-driven tests first. |
| P2 | planned | Add OHLCV chart artifact generator | Supports price action and multi-timeframe setup review from authorized market data. | Start with a pure data-to-chart artifact layer and fixture OHLCV; do not test live connector behavior in this repo. |
| P2 | planned | Research option-flow data vendor | Needed before implementing abnormal options signal analysis. | Define minimum anomaly schema and candidate vendor requirements. |

## Today

Date: 2026-06-14

- Morning main task: define the fixture package as the next implementation slice for the weekly plan, daily tracking, intraday scan, and two-stage review workflow.
- Secondary task: none until the fixture package shape is accepted.
- Definition of done: document or create fixture expectations for weekly plan notes, daily market tracking notes, `trade-plans.csv`, `intraday-watchlist.csv`, `holdings.csv`, IBKR-like trade facts, `trades.csv`, `reviews.md`, and expected scan outputs covering LEAP call/put, 2x ETF, ETF swing, and 0DTE QQQ option plans.
- Verification: fixture package should be usable by later TDD work for weekly planning, daily tracking, `intraday_scan.py`, post-order review writing, post-exit review updates, stats, Google Sheets sync, and chart artifact generation without live IBKR or Google data.
- End-of-day result:

## Progress Log

### 2026-06-14

- Planned: create a dedicated development planning/progress document and align weekday automations to it.
- Completed: created `docs/DEVELOPMENT_PLAN.md`, registered it in `docs/ROADMAP.md`, and updated both weekday development automations to use it as the progress source of truth.
- Completed: added `docs/DEVELOPMENT.md` as the lightweight development workflow, TDD, CI, worktree, and Codex/Claude handoff standard. Clarified that live IBKR connector behavior is outside this repo's test scope.
- Verification: read both automation configs after update; confirmed they reference `docs/DEVELOPMENT_PLAN.md`; plugin validation passed after development workflow review.
- Blockers: none.
- Decision: confirmed the user's hard need is weekly trade-plan construction, daily market tracking, opportunity discovery within the plan/watchlist, and two-stage trade review based on actual trade facts.
- Completed: added weekly plan and daily market tracking templates to the plugin and aligned review references around post-order and post-exit stages.
- Decision: confirmed fixture data as the next product-capability implementation slice before `intraday_scan.py`.
- Next: define the fixture package using the new weekly/daily templates, then implement `intraday_scan.py`, and connect post-order/post-exit review CSV writing.

## Automation Contract

Automations should use this document as the development progress source of truth:

- `dailytrades-weekday-development-brief`: weekday morning brief and planning interaction.
- `dailytrades-end-of-day-progress-review`: weekday end-of-day progress review and update prompt.

Automation outputs should be concise Chinese Markdown notes. They should ask before editing files and should not touch broker write actions, private trade data, or live external services.
