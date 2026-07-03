# Development Plan

This document is the public source of truth for Dailytrades plugin development planning, daily task planning, and progress. It is used by the weekday development brief and end-of-day progress review automations.

Do not include private trade records, credentials, account details, unpublished research excerpts, or internal agent prompts. Keep this focused on project execution.

## Current Development Phase

Phase: local trading research workflow MVP.

Goal: make the plugin usable for the core trading research loop before adding heavier external integrations: maintain an overwriteable Active Market Plan, append update notes, scan setup-level plans, read broker facts live when authorized, generate position daily reports, capture review context, and compute risk/statistics snapshots.

## Planning North Star

Daily development planning should prioritize product capability, not process work.

The current product sequence is:

1. AI-native synthesis contract: agent reads broadly and returns concise decision-useful notes, not raw research dumps;
2. Active Market Plan schema, trading profile, update trail, and local report/review artifacts;
3. KVN momentum leaderboard: a daily local script writes all liquid universe KVN scores into SQLite, while the skill displays Top10 and ticker lookups;
4. trade plan preparation: macro, financial conditions, policy/event risk, KVN momentum, industry strength, and company thesis checks produce input reads and a Cross-Section Candidate Pool before setup rows are created;
5. research report intake: `research-report-intake` finds public/authorized reports, digests user-provided PDFs/links/text, creates a claim ledger, and maps verified report impact into Trade Plan Preparation;
6. fixture data covering KVN leaderboard snapshots, `market-plan.md`, private-style `trading-profile.md` fixture, append-only update notes, event previews, Trade Plan Preparation, setup pool, broker-live runtime views, position daily report output, and two-stage review context;
7. premarket/intraday market parsing, level updates, and dynamic tracking against the Active Market Plan;
8. setup-scoped intraday scan;
9. broker-live position daily report automation and visualization snapshots;
10. post-order review to capture user context from read-only broker facts;
11. post-exit review to capture results, lessons, and optional statistics snapshots;
12. broker-agnostic portfolio reconciliation and risk view;
13. basic stats and system review;
14. user-confirmed Active Market Plan automations;
15. OHLCV-backed chart artifacts;
16. option-flow anomaly research.

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
   - whether Claude Code should be assigned work;
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
| P0 | done | Define AI-native synthesis contract | Keeps the plugin focused on agent-heavy reading and concise user-facing decision notes instead of verbose report generation. | Apply this rule to every skill output and fixture expectation. |
| P0 | done | Define basic plugin content plan | Makes the minimum useful skill, reference, template, script, and fixture content explicit before implementation work continues. | Use `docs/PLUGIN_CONTENT_PLAN.md` as the checklist for the fixture package and next scripts. |
| P0 | review | Split plugin into focused skills | Keeps the plugin usable as an agent toolbox instead of one oversized workflow prompt. | Forward-test the router and priority skills on realistic weekly review, daily tracking, and trade review prompts. |
| P1 | in_progress | Define Trade Plan Preparation contract | Keeps macro, financial conditions, policy/event risk, industry strength, and company thesis checks from turning into loose reports or premature intraday setup calls. | Update skills, references, templates, and fixtures so research first produces input reads and a Cross-Section Candidate Pool. |
| P1 | ready | Define KVN momentum leaderboard contract | Makes the user's daily momentum-stock ranking a first-class analysis module instead of a vague watchlist score or manual table. | Add `momentum-leaderboard` skill contract, KVN field schema, SQLite storage contract, fixture output, and verifier. |
| P1 | done | Define research report intake contract | Gives `research-report-intake` a first-class workflow for report discovery, user-provided report digestion, Claim Ledger creation, verification queues, and Trade Plan Preparation impact. | Forward-test on one user-provided report and one public-source discovery prompt, then add realistic fixtures. |
| P1 | in_progress | Add Active Market Plan fixture data | Gives scripts stable inputs for tests and demos without using live broker or Google data. | Cover Trade Plan Preparation first, then setup pool, intraday watchlist, broker-live runtime views, position daily report output, review context, and expected scan outputs. |
| P1 | done | Add Active Market Plan and broker-live contracts | Aligns the workflow around one living market plan, setup-level tracking, and read-only broker sources. | Use these contracts in the fixture package and later script flows. |
| P1 | review | Re-scope canonical record schema registry | Existing CSV schemas are useful for fixtures and compatibility, but broker-live reads are now the default source for objective broker facts. | Decide which schemas stay as fixture/debug artifacts and which scripts should be deprecated or converted to snapshot tools. |
| P1 | done | Add trading profile template | Lets setup selection account for personal trading style and instrument preferences without storing account allocation in the public repo. | Use it as a private input for Active Market Plan fixtures and setup translation tests. |
| P1 | deferred | Implement local intraday scan script | Turns documented setup states into executable status and attention-priority summaries. | Resume after Trade Plan Preparation and setup pool promotion fields are stable. |
| P1 | review | Re-scope two-stage interactive review output | The review flow should capture user context while objective facts come from broker-live sources. | Convert record-writing guidance into optional snapshot/review-artifact guidance. |
| P1 | deferred | Legacy active Sheet CSV importer | Kept only as migration/compatibility tooling after Google Sheets trade records left the main path. | Do not prioritize unless the user asks to import old records again. |
| P1 | done | Add lightweight test harness | Gives product implementation tasks a local acceptance gate before CI exists. | Extend the shared contract verifier as new product contracts gain executable checks. |
| P1 | ready | Add broker-live position daily report | Gives the user a scheduled holdings/risk summary similar to broker-native reminders while preserving the no-trade-record-spreadsheet boundary. | Define fixture output, visualization fields, and automation prompt; create the real Codex automation after cadence confirmation. |
| P2 | deferred | Google Sheets summary display | Sheets is no longer a trade-record layer; only non-sensitive summaries or report indexes may be mirrored later. | Reconsider after position daily reports and visualization snapshots are stable. |
| P2 | planned | Add Active Market Plan automations | Turns deep update, quick update, intraday monitor, post-market review, and position daily report into recurring Codex prompts after the user confirms cadence and broker data permissions. | Define automation prompts from `automation-contract.md`; create or update actual Codex automations only after cadence confirmation. |
| P2 | in_progress | Add OHLCV chart artifact generator | Supports price action and multi-timeframe setup review from authorized market data. | Forward-test `chart_artifact.py` with fixture and real authorized OHLCV exports; add screenshot/export workflow later. |
| P2 | planned | Research option-flow data vendor | Needed before implementing abnormal options signal analysis. | Define minimum anomaly schema and candidate vendor requirements. |

## Today

Date: 2026-07-03

- Morning main task: re-scope the plugin around analysis-first development, with `momentum-leaderboard` as the next concrete product slice.
- Secondary task: keep existing record-writing, legacy import, and Google Sheets mirror work as support infrastructure, not the near-term main line.
- Definition of done: `CONTEXT.md`, `docs/ROADMAP.md`, `docs/PLUGIN_CONTENT_PLAN.md`, `docs/DEVELOPMENT_PLAN.md`, and `docs/PROJECT_LOG.md` reflect the KVN leaderboard scope, storage boundary, and next implementation task.
- Verification: documentation terms are internally consistent, roadmap next tasks put KVN before heavier intraday/record/sync work, and git diff is clean after commit.
- End-of-day result: pending.

## Progress Log

### 2026-07-03

- Planned: use `grill-with-docs` to re-evaluate plugin scope and development priorities against current docs.
- Decision: the record module is useful but hard to perfect upfront; near-term development should prioritize analysis, especially the KVN momentum leaderboard, macro/rates regime filtering, and industry/company research flow.
- Decision: objective broker facts should be read live from Longbridge/IBKR when authorized; Google Sheets and local `trades.csv` should not be treated as the main trade-record layer.
- Decision: add a scheduled position daily report capability that summarizes broker-live holdings, risk exposure, notable changes, and visualization-ready snapshots without placing or implying orders.
- Decision: `momentum-leaderboard` should be a focused skill backed by a daily local script and `{runtime_dir}/momentum/kvn.sqlite`, not a sub-section of `macro-equity-research`.
- Decision: default user-facing KVN output is Top10 with screenshot-like fields, while all liquid universe symbols remain queryable from local storage.
- Next: implement the `momentum-leaderboard` contract, fixture, verifier, and storage schema; then define the broker-live position daily report fixture and automation prompt.

### 2026-06-18

- Completed: added a shared `contract_verifier.py` module for product contract checks.
- Completed: converted weekly outlook, Trade Plan Preparation, and research report intake verifier scripts into thin adapters over the shared verifier.
- Completed: added exact CSV header validation for the research report log template.
- Completed: added `record_schemas.py` as the canonical local CSV schema registry and wired `init_daily.py` to it.
- Completed: added record template verification for headers and row widths, which caught and fixed a misaligned `trades.csv` sample row.
- Completed: added the Actual trade record module with `trade_records.py` and `update_trade_record.py` for post-order row creation and post-exit row completion.
- Completed: wired `$trade-review` documentation to use the update script after user confirmation.
- Completed: fixed legacy `active` Sheet import by adding an explicit `--allow-unknown-execution-fields` mode for older rows missing `quantity`, `fees`, or `risk_amount`.
- Completed: added `import_legacy_active_csv.py` to migrate legacy `active` tab CSV exports into canonical local `trades.csv` and append-only `reviews.md`.
- Verification: shared verifier self-test plus all existing contract checks pass locally.
- Next: import a broader legacy active CSV export into the private runtime, inspect the stats output, then use the same schema path for one-way Google Sheets sync.

### 2026-06-17

- Completed: defined the `research-report-intake` capability as the first-class path for report discovery and user-provided report digestion.
- Completed: added `Research Report Digest`, `Claim Ledger`, `Verification Queue`, and `Trade Plan Preparation Impact` as the required shape before report views can affect macro/equity research or setup promotion.
- Verification: added and ran the report-intake contract verifier; kept weekly outlook and Trade Plan Preparation contract checks passing.
- Next: forward-test on a user-provided research report and a public-source discovery prompt, then add report-digestion fixtures.

### 2026-06-16

- Planned: prioritize Trade Plan Preparation over `intraday_scan.py`.
- Decision: v1 inputs are `Macro Regime`, `Financial Conditions`, `Policy/Event Risk`, `Industry/Sector Strength`, and `Company Thesis Check`.
- Decision: quantitative momentum candidate pool is a separate TODO and should not be treated as a v1 input until its data, factors, ranking, and validation are defined.
- Decision: Active Market Plan needs a `Trade Plan Preparation` section with `Input Reads` and `Cross-Section Candidate Pool` before setup rows are promoted.
- Decision: research reports need a dedicated `research-report-intake` path before macro/equity research consumes them. Report discovery is limited to public/authorized sources, user-provided reports are reduced to `Research Report Digest`, `Claim Ledger`, `Verification Queue`, and `Trade Plan Preparation Impact`, and paywall bypass remains out of scope.

### 2026-06-14

- Planned: create a dedicated development planning/progress document and align weekday automations to it.
- Completed: created `docs/DEVELOPMENT_PLAN.md`, registered it in `docs/ROADMAP.md`, and updated both weekday development automations to use it as the progress source of truth.
- Completed: added `docs/DEVELOPMENT.md` as the lightweight development workflow, TDD, CI, worktree, and Codex/Claude handoff standard. Clarified that live IBKR connector behavior is outside this repo's test scope.
- Verification: read both automation configs after update; confirmed they reference `docs/DEVELOPMENT_PLAN.md`; plugin validation passed after development workflow review.
- Blockers: none.
- Decision: confirmed the user's hard need is a weekly market review and next-week plan package, daily premarket/intraday tracking with level updates, opportunity discovery within the plan/watchlist, and two-stage trade review based on actual trade facts.
- Completed: added weekly review and daily market tracking templates to the plugin and aligned review references around post-order and post-exit stages.
- Completed: split the plugin into a lightweight `trading-research` router plus focused skills for weekly market review/planning, daily tracking, intraday scan, trade review, macro/equity research, portfolio risk, and trading stats.
- Decision: confirmed fixture data as the next product-capability implementation slice before `intraday_scan.py`.
- Decision: refined the workflow around one overwriteable Active Market Plan plus append-only update notes. Weekly and daily work are update depths, not separate workflows. Setup is the smallest planning unit, and broker sources are read-only adapters mapped into canonical daily CSV.
- Decision: added a trading profile layer for style and instrument preferences without storing account allocation in the public repo.
- Next: forward-test focused skill routing, then define the fixture package using `market-plan.md`, `trading-profile.md`, update notes, setup pool, and canonical broker CSV, implement `intraday_scan.py`, and connect post-order/post-exit review CSV writing.
- Completed: defined the basic plugin content plan across router/focused skills, shared references, templates, scripts, fixture package, priorities, and deferred scope.
- Completed: initialized the 2026-06-15 to 2026-06-19 Active Market Plan outlook and append-only update note using current event/calendar and market sources.
- Decision: clarified the plugin is AI-native: agents should read, verify, compare, and synthesize broadly, but return concise decision notes rather than long source dumps.
- Next: convert the new market plan into fixture package files for daily records, expected intraday scan output, and review-writing tests.

## Automation Contract

Automations should use this document as the development progress source of truth:

- `dailytrades-weekday-development-brief`: weekday morning brief and daily task-planning interaction.
- `dailytrades-end-of-day-progress-review`: weekday end-of-day progress review and update prompt.

The morning automation should recommend one main product-capability task for the day, ask for available time, chosen task, optional secondary task, definition of done, expected verification, whether Claude Code should be assigned work, and which docs should be updated after completion.

Automation outputs should be concise Chinese Markdown notes. They should ask before editing files and should not touch broker write actions, private trade data, or live external services.

Trading-operation reminders and assistant prompts are separate from development automations. They belong in the fixed `交易研究 Daily Ops` chat and should use `runtime_dir` as the private working-memory root. Default `runtime_dir` is `~/Documents/dailytrades-runtime`, with `TRADING_RESEARCH_RUNTIME_DIR` or script-level `--runtime-dir` overrides.

Trading prompts should read `{runtime_dir}/market-plan.md` as current state, `{runtime_dir}/trading-profile.md` as private trading style input when available, and `{runtime_dir}/updates/YYYY-MM-DD.md` as the append-only trail. They may prompt for deep updates, quick updates, intraday trigger checks, post-market reviews, position daily reports, and read-only broker reconciliation, but should ask before editing files and should never call broker write actions. They are not automated trading systems. Google Sheets is no longer a trade-record layer.
