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
2. accepted plugin design contract: natural-language task UX, router contract, runtime write boundary, broker source configuration, KVN snapshot boundary, and chart artifact boundary;
3. README and plugin docs aligned to natural-language task UX instead of user-facing focused-skill menus;
4. router intent fixtures and a router contract verifier;
5. runtime health contract and script for available/missing/stale/unauthorized state;
6. Active Market Plan schema, trading profile, update trail, and local report/review artifacts;
7. KVN model planning: define the future model module boundary, output contract, factor groups, universe rules, validation plan, and daily-job handoff without implementing the model inside this plugin;
8. KVN momentum leaderboard: import/read upstream or user-provided snapshots into SQLite, while the workflow displays Top10 and ticker lookups;
9. trade plan preparation: macro, financial conditions, policy/event risk, KVN snapshot, industry strength, and company thesis checks produce input reads and a Cross-Section Candidate Pool before setup rows are created;
10. research report intake: `research-report-intake` finds public/authorized reports, digests user-provided PDFs/links/text, creates a claim ledger, and maps verified report impact into Trade Plan Preparation;
11. fixture data covering KVN leaderboard snapshots, `market-plan.md`, private-style `trading-profile.md` fixture, append-only update notes, event previews, Trade Plan Preparation, setup pool, broker-live runtime views, position daily report output, and two-stage review context;
12. premarket/intraday market parsing, level updates, and dynamic tracking against the Active Market Plan;
13. setup-scoped intraday scan;
14. broker-live position daily report automation and visualization snapshots;
15. post-order review to capture user context from read-only broker facts;
16. post-exit review to capture results, lessons, and optional statistics snapshots;
17. broker-agnostic portfolio reconciliation and risk view;
18. basic stats and system review;
19. user-confirmed Active Market Plan automations;
20. OHLCV-backed chart artifacts;
21. option-flow anomaly research.

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
| P0 | done | Accept plugin design contract | Locks the product shape around natural-language task UX, internal focused skills, private runtime boundaries, draft-mode automations, broker source configuration, KVN snapshot consumption, and chart artifact behavior. | Use `docs/PLUGIN_DESIGN.md` as the source for the next implementation issues. |
| P0 | done | Align README with AI-native task UX | Keeps user docs from presenting focused skills as the default user interface. | Maintain root/plugin README examples around natural-language tasks as the default UX. |
| P0 | done | Add router intent fixtures | Makes agent autonomous routing testable before adding more scripts. | Extend fixture prompts as new user task types are added. |
| P0 | done | Add router contract verifier | Gives the router a local acceptance gate. | Run `verify_router_contract.py` with the existing contract checks. |
| P1 | done | Define Trade Plan Preparation contract | Keeps macro, financial conditions, policy/event risk, industry strength, company thesis checks, and imported KVN snapshots from turning into loose reports or premature intraday setup calls. | Use `verify_trade_plan_preparation_contract.py` as the acceptance gate before adding setup-pool or intraday-scan behavior. |
| P1 | done | Define runtime health contract | Lets the agent know which private runtime state is available before planning or automation work. | Run `runtime_health.py`, `verify_runtime_health_selftest.py`, and `verify_runtime_health_contract.py` as the local acceptance gate before runtime-dependent work. |
| P1 | done | Define KVN Model module planning contract | Keeps future KVN score construction separate from the plugin while specifying output schema, universe rules, factor groups, validation gates, and daily-job handoff. | Use `docs/KVN_MODEL_PLAN.md` before implementing any KVN model prototype outside this plugin. |
| P1 | done | Define KVN snapshot leaderboard contract | Makes externally generated KVN rankings a first-class analysis input without making this plugin own the quantitative model. | Use `momentum-leaderboard` for user-facing KVN tasks and run `kvn_leaderboard.py`, `verify_kvn_leaderboard_selftest.py`, and `verify_kvn_leaderboard_contract.py` as the local acceptance gate. |
| P1 | done | Define research report intake contract | Gives `research-report-intake` a first-class workflow for report discovery, user-provided report digestion, Claim Ledger creation, verification queues, and Trade Plan Preparation impact. | Forward-test on one user-provided report and one public-source discovery prompt, then add realistic fixtures. |
| P1 | done | Add Active Market Plan fixture data | Gives scripts stable inputs for tests and demos without using live broker or Google data. | Use `verify_active_market_plan_fixture_contract.py` before building position daily report or intraday scan scripts. |
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

Date: 2026-07-05

- Main task: execute the local MVP sequence in small verified stages.
- Current stage: define the KVN Model module planning contract without implementing model code inside this plugin.
- Secondary task: prepare the next stage around broker-live position daily report fixture/script work.
- Definition of done: `docs/KVN_MODEL_PLAN.md`, ADR, roadmap, development plan, and project log clearly separate KVN model construction from plugin snapshot consumption.
- Verification: markdown references resolve through `rg`; `git diff --check` passes.
- End-of-day result: pending.

## Progress Log

### 2026-07-05

- Completed: defined the KVN Model module planning contract in `docs/KVN_MODEL_PLAN.md` and `docs/adr/0006-kvn-model-module-boundary.md`. The future model owns universe, data ingestion, factor computation, validation, versioning, and daily snapshots; the plugin only consumes standardized outputs.
- Completed: extended Trade Plan Preparation from five input reads to six by adding `KVN Momentum Leaderboard` as an imported snapshot input.
- Completed: updated weekly planning, macro/equity research, Active Market Plan, output templates, and market/weekly templates so KVN feeds the Cross-Section Candidate Pool but cannot become a buy list or direct setup.
- Completed: added `trade-plan-preparation-with-kvn-2026-06-24.md` fixture showing SNDK/CRDO/GLW/SOXX style KVN candidates, thesis/risk gates, and promotion requirements for `candidate setup`.
- Completed: added the focused `momentum-leaderboard` skill wrapper around `kvn_leaderboard.py` and updated the router to use it for KVN import/show/query/change tasks.
- Completed: added the Active Market Plan fixture package under `assets/fixtures/runtime/active-market-plan-2026-06-24/`, covering plan state, trading profile, update note, setup pool, intraday watchlist, broker-live fixture views, position daily report, review context, and expected intraday scan output.
- Completed: hardened daily tracking KVN source discipline after local validation showed a `KVN-like` rebuild risk. `daily-market-tracking` now must report missing/stale KVN and ask whether to import or continue without KVN; it must not rebuild or relabel public market data as KVN.
- Completed: tightened KVN leaderboard semantics. KVN rows are ticker-only, preserve script-computed order from the scheduled/upstream model output, and must not be re-ranked, re-scored, or replaced with sector/theme/narrative buckets by the agent.
- Next: define the position daily report contract/script or implement the first `intraday_scan.py` against the fixture package.

### 2026-07-04

- Completed: accepted the plugin design contract in `docs/PLUGIN_DESIGN.md`.
- Decisions: default UX is natural-language tasks; focused skills are internal/power-user tools; trading-judgment runtime writes are draft-only; trading-operation automations default to draft mode; broker facts are read live from authorized sources; derived broker summaries may be saved privately; v1 broker sources are Longbridge skill/plugin and IBKR connector; KVN model construction is outside plugin scope; chart artifacts are on-demand with opt-in auto-generation for high-priority setup/review contexts.
- Next: implement the development queue from the design: README UX alignment, router intent fixtures, router verifier, runtime health contract/script, then KVN snapshot import/storage.
- Completed: aligned root/plugin README around natural-language task prompts and moved focused skill names into advanced/internal wording.
- Completed: added router intent fixtures for weekly plan, premarket update, intraday setup scan, research report intake, post-order review, post-exit review, position daily report, and portfolio risk.
- Completed: added `verify_router_contract.py` as a local acceptance gate for router fixture shape, allowed workflows, required output labels, and AI-native prompt wording.
- Completed: added a private-safe runtime health contract and script that reports runtime availability, stale state, and broker authorization status without copying private runtime content into the public repo.
- Completed: added runtime health selftest and contract verifier coverage, and wired the router/automation docs to run the health check before runtime-dependent work.
- Completed: added `kvn_leaderboard.py` for importing externally generated KVN snapshots into SQLite, showing Top10, querying any ticker, and summarizing Top10 changes.
- Completed: added KVN fixture snapshots, expected Top10 output, selftest, contract verifier, and router fixture coverage for natural-language KVN lookup.
- Next: update Trade Plan Preparation fixtures so macro/financial/policy reads and imported KVN candidates can feed the Cross-Section Candidate Pool.

### 2026-07-03

- Planned: use `grill-with-docs` to re-evaluate plugin scope and development priorities against current docs.
- Decision: the record module is useful but hard to perfect upfront; near-term development should prioritize analysis, especially the KVN momentum leaderboard, macro/rates regime filtering, and industry/company research flow.
- Decision: objective broker facts should be read live from Longbridge/IBKR when authorized; Google Sheets and local `trades.csv` should not be treated as the main trade-record layer.
- Decision: add a scheduled position daily report capability that summarizes broker-live holdings, risk exposure, notable changes, and visualization-ready snapshots without placing or implying orders.
- Decision: `momentum-leaderboard` should be a focused skill backed by KVN snapshot import/storage in `{runtime_dir}/momentum/kvn.sqlite`, not a sub-section of `macro-equity-research`; the quantitative model itself stays outside plugin scope.
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
