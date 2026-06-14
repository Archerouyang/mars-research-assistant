# Development Plan

This document is the public source of truth for Dailytrades plugin development planning and progress. It is used by the weekday development brief and end-of-day progress review automations.

Do not include private trade records, credentials, account details, unpublished research excerpts, or internal agent prompts. Keep this focused on project execution.

## Current Development Phase

Phase: local workflow and automation baseline.

Goal: make the plugin usable as a repeatable Codex-assisted development and trading research workflow before adding heavier external integrations.

## Daily Development Loop

Weekday morning brief:

1. Inspect `docs/DEVELOPMENT_PLAN.md`, `docs/ROADMAP.md`, `docs/PROJECT_LOG.md`, `CONTEXT.md`, and current git status.
2. Report current development tasks with priority.
3. Recommend one main task for today.
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
| P1 | ready | Implement local intraday scan script | Turns documented scan states into executable status and attention-priority summaries. | Build with TDD from fixture CSVs. |
| P1 | ready | Add sample daily fixture data | Gives scripts stable inputs for tests and demos without using live broker or Google data. | Add fixtures for plans, intraday watchlist, holdings, and trades. |
| P1 | ready | Add lightweight test harness | Gives Claude/Codex tasks a local acceptance gate before CI exists. | Start with unittest fixtures for existing scripts and template schemas. |
| P1 | ready | Connect interactive review output to local trade records | Makes trade review produce structured `trades.csv` rows plus `reviews.md` sections. | Extend current review append flow with CSV write support. |
| P2 | planned | Add one-way Google Sheets sync | Mirrors local records to Sheets without making Sheets the source of truth. | Define row mapping and fixture-driven tests first. |
| P2 | planned | Add OHLCV chart artifact generator | Supports price action and multi-timeframe setup review from authorized market data. | Start with a pure data-to-chart artifact layer and fixture OHLCV; do not test live connector behavior in this repo. |
| P2 | planned | Research option-flow data vendor | Needed before implementing abnormal options signal analysis. | Define minimum anomaly schema and candidate vendor requirements. |

## Today

Date: 2026-06-14

- Morning main task:
- Secondary task:
- Definition of done:
- Verification:
- End-of-day result:

## Progress Log

### 2026-06-14

- Planned: create a dedicated development planning/progress document and align weekday automations to it.
- Completed: created `docs/DEVELOPMENT_PLAN.md`, registered it in `docs/ROADMAP.md`, and updated both weekday development automations to use it as the progress source of truth.
- Completed: added `docs/DEVELOPMENT.md` as the lightweight development workflow, TDD, CI, worktree, and Codex/Claude handoff standard. Clarified that live IBKR connector behavior is outside this repo's test scope.
- Verification: read both automation configs after update; confirmed they reference `docs/DEVELOPMENT_PLAN.md`; plugin validation passed after development workflow review.
- Blockers: none.
- Next: use the next morning brief to choose between `intraday_scan.py`, fixture data, or trade-review CSV writing as the next implementation task.

## Automation Contract

Automations should use this document as the development progress source of truth:

- `dailytrades-weekday-development-brief`: weekday morning brief and planning interaction.
- `dailytrades-end-of-day-progress-review`: weekday end-of-day progress review and update prompt.

Automation outputs should be concise Chinese Markdown notes. They should ask before editing files and should not touch broker write actions, private trade data, or live external services.
