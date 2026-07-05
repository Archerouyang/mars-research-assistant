# Project Log

This file records the public trajectory of the Trading Research System plugin. It complements Git commit history, ADRs, and `docs/ROADMAP.md`.

Keep this log focused on user-visible plugin progress. Do not include private trade records, credentials, internal agent coordination, or non-public research material.

This project is not using public release versioning yet. Until the initial complete workflow, production chain, and interaction model are settled, treat this log as a planning and implementation trajectory, not a changelog for shipped versions.

## How To Update

Add an entry when one of these changes:

- capability boundary;
- roadmap milestone;
- plugin skill behavior;
- local record schema;
- external integration decision;
- important deferred decision.

Use this shape:

```text
## YYYY-MM-DD

- Commit: <short-sha> <commit subject>
- Scope: <planning | skill | script | template | sync | data | decision>
- What changed:
- Why it matters:
- Next step:
```

## 2026-07-05

- Commit: pending
- Scope: fixture, test, docs
- What changed: added safe realistic `research-report-intake` fixtures for a user-provided AI infrastructure report and a public-source discovery/access-boundary prompt. The verifier now requires source priority, access status, inaccessible S3 handling, Claim Ledger, Verification Queue, and Trade Plan Preparation impact.
- Why it matters: report intake can be forward-tested without storing paywalled or copyrighted research text, and report opinions still cannot directly become setups.
- Next step: use the same fixture-backed contract when integrating report intake into trade plan preparation and setup-pool promotion.

- Commit: pending
- Scope: automation, template, test
- What changed: added `automation-position-daily-report.md` and extended the position daily report contract so Daily Ops automations follow the same read-only broker-source order, standard `portfolio_snapshot.csv` mapping, and `position_daily_report.py` rendering path.
- Why it matters: the scheduled holdings report now has a concrete prompt contract before any real Longbridge or IBKR adapter work starts.
- Next step: connect real read-only broker source adapters to the standard snapshot view when authorized.

- Commit: pending
- Scope: script, fixture, test
- What changed: added `position_daily_report.py` and `verify_position_daily_report_selftest.py`. The first slice renders a concise Chinese broker-live style holdings/risk report from the standard `portfolio_snapshot.csv` fixture and updates the fixture expected report.
- Why it matters: this starts the broker-live position daily report path without touching real broker connectors, raw exports, or order actions.
- Next step: add broker-source adapter guidance and trading-operation automation prompts after the fixture-backed report shape is stable.

- Commit: pending
- Scope: planning, decision
- What changed: added `docs/KVN_MODEL_PLAN.md` and `docs/adr/0006-kvn-model-module-boundary.md` to define the future KVN Model module. The model module owns universe selection, market-data ingestion, factor computation, score ranking, validation, versioning, and daily snapshots; the plugin remains a snapshot consumer.
- Why it matters: KVN scores need to come from a reproducible model, not an agent-authored narrative or plugin-side shortcut. This gives future implementation a detailed contract without implementing the model now.
- Next step: continue the MVP sequence with broker-live position daily report planning and fixture/script work.

- Commit: pending
- Scope: skill, script, template, docs, test
- What changed: tightened KVN leaderboard semantics across the script output, focused skill, daily/weekly/market templates, shared references, and contract verifier. KVN rows are now explicitly ticker-only, preserve the script-computed order from the scheduled/upstream model output, and cannot be re-ranked, re-scored, or replaced with sector/theme/narrative buckets by the agent. Sector/theme rotation must live in separate market breadth or theme sections.
- Why it matters: KVN is a quantitative leaderboard artifact, not an agent-authored market narrative. This prevents daily tracking from turning broad rotation notes into fake KVN rankings.
- Next step: validate the refreshed plugin in a new chat against both missing-KVN runtime state and fixture-backed Top10 output.

- Commit: pending
- Scope: skill, template, test
- What changed: hardened KVN source discipline for `daily-market-tracking`. Daily updates now must use imported KVN snapshots through runtime health and `kvn_leaderboard.py`; if the KVN store is missing or stale, they report the gap and ask whether to import a snapshot or continue without KVN. Public market data can still support tape and sector breadth, but must not be labeled as KVN or used to rebuild a KVN-like leaderboard.
- Why it matters: local validation showed the agent could invent a KVN-like ranking when no official local KVN snapshot existed. This fix preserves the plugin boundary that KVN is consumed from imported/user-provided snapshots only.
- Next step: rerun local fixture validation in a fresh chat after refreshing the plugin cache.

- Commit: pending
- Scope: fixture, test, docs
- What changed: added the synthetic Active Market Plan fixture package under `assets/fixtures/runtime/active-market-plan-2026-06-24/`. The package includes `market-plan.md`, `trading-profile.md`, an update note, setup-level trade plans, intraday watchlist, broker-live fixture views, a position daily report output, review context, and expected intraday scan output. Added `verify_active_market_plan_fixture_contract.py` to keep the package complete and schema-aligned.
- Why it matters: upcoming position daily report and intraday scan scripts now have stable non-private inputs and expected outputs. This keeps development offline and reproducible without live broker data.
- Next step: define the position daily report contract/script or implement the first `intraday_scan.py` against the fixture package.

- Commit: pending
- Scope: skill, router, docs, test
- What changed: added the focused `momentum-leaderboard` skill wrapper. The general router now delegates KVN import, Top10 display, ticker lookup, and Top10 changes to this skill, which uses runtime health, `momentum-leaderboard.md`, and `kvn_leaderboard.py` while preserving the rule that KVN is research priority only.
- Why it matters: users can ask natural-language momentum leaderboard questions without invoking scripts or knowing internal references, while the implementation stays AI-native and model-agnostic.
- Next step: build the fuller Active Market Plan fixture package or position daily report fixture.

- Commit: pending
- Scope: skill, template, fixture, test
- What changed: wired imported KVN snapshots into Trade Plan Preparation. Weekly planning, macro/equity research, Active Market Plan, output templates, and market/weekly templates now treat `KVN Momentum Leaderboard` as an input read. Added `trade-plan-preparation-with-kvn-2026-06-24.md` showing how KVN names enter the Cross-Section Candidate Pool while still requiring macro/financial support, thesis checks, price structure, and portfolio risk before `candidate setup` promotion.
- Why it matters: KVN is no longer just a standalone leaderboard. It now participates in the actual planning contract without becoming a buy list or bypassing setup discipline.
- Next step: add the focused `momentum-leaderboard` skill wrapper or build the fuller Active Market Plan fixture package.

## 2026-07-04

- Commit: pending
- Scope: script, fixture, reference, test
- What changed: added `kvn_leaderboard.py` for importing externally generated KVN snapshot CSV files into `{runtime_dir}/momentum/kvn.sqlite`, showing Top10 by `KVN 分数`, querying any imported ticker, and summarizing Top10 changes. Added fixture snapshots, expected Top10 output, `momentum-leaderboard.md`, selftest, contract verifier, and router fixture coverage for natural-language KVN lookup.
- Why it matters: the plugin can now consume the user's KVN momentum leaderboard as a first-class research input without owning the quantitative model or treating the leaderboard as a buy list.
- Next step: wire imported KVN candidates into Trade Plan Preparation fixture output and Cross-Section Candidate Pool rules.

- Commit: pending
- Scope: script, skill, reference, test
- What changed: added a private-safe runtime health contract and `runtime_health.py` script. The script reports runtime files, daily directories, KVN storage, and broker-source authorization as `available`, `missing`, `stale`, or `unauthorized` without reading private file contents. Added selftest and contract verifier coverage, plus router and automation guidance to run runtime health before runtime-dependent work.
- Why it matters: daily planning, automations, and broker-aware workflows can now check whether required private runtime state exists without leaking market plans, trade plans, or account context into public plugin files.
- Next step: define the KVN snapshot import/storage contract, fixture data, and verifier.

- Commit: pending
- Scope: docs, fixture, test
- What changed: aligned root and plugin README with the accepted AI-native natural-language task UX. Added router intent fixtures for weekly plan, premarket update, intraday setup scan, research report intake, post-order review, post-exit review, position daily report, and portfolio risk. Added `verify_router_contract.py` to check fixture schema, allowed workflows, required output labels, and avoidance of focused-skill prompts as the default UX.
- Why it matters: the plugin now has an executable first gate for agent-autonomous routing. User docs no longer present focused skill names as the primary interface, while focused skills remain internal/power-user tools.
- Next step: define runtime health output and implement a private-safe health check before starting KVN snapshot import/storage.

- Commit: pending
- Scope: design, planning, decision
- What changed: accepted the plugin design contract in `docs/PLUGIN_DESIGN.md`. The design locks the product shape around natural-language task UX, internal/power-user focused skills, private runtime boundaries, draft-mode trading automations, read-only broker access, configurable broker source onboarding for Longbridge skill/plugin and IBKR connector, KVN snapshot consumption rather than model construction, and on-demand chart artifacts with opt-in auto-generation for high-priority setup/review contexts.
- Why it matters: the project now has a concrete AI-native plugin shape and development queue before implementation continues. Fuzzy boundaries around user interaction, runtime writes, broker data, KVN, charts, and automations are resolved enough to create implementation issues.
- Next step: implement the accepted development queue: align README with natural-language task UX, add router intent fixtures, add a router verifier, define runtime health, then add KVN snapshot import/storage.

## 2026-07-03

- Commit: pending
- Scope: decision, template, glossary
- What changed: clarified that strategy models, trading pools, ETF groups, timeframe rules, and crowding weights belong in private `trading-profile.md`, not as hard-coded public plugin defaults. Generalized the glossary language and expanded the trading profile template to capture strategy posture scoring, active trading pools, long-term ETF groups, and crowding model inputs.
- Why it matters: the plugin remains reusable for other users while still supporting the user's specific trading framework through runtime profile configuration.
- Next step: continue interviewing the user's trading system and map the confirmed rules into a private profile artifact before implementation work.

- Commit: pending
- Scope: data, skill, reference
- What changed: documented Longbridge `macrodata` as an optional macro and financial-conditions source. It can feed `Macro Regime` and `Financial Conditions`, while policy facts, official speeches, legal/regulatory status, and release status still require S0 official confirmation.
- Why it matters: Longbridge is no longer modeled only as a broker/account source; the plugin can use its macro data command for faster macro reads without weakening source-priority rules.
- Next step: when implementing macro-data adapters, keep `macrodata` separate from broker account reconciliation and add fixture coverage for one macro/rates read.

- Commit: pending
- Scope: decision, automation, data
- What changed: re-scoped broker data handling around broker-live reads instead of spreadsheet or durable local trade-record tables. Added the `position_daily_report` automation concept, documented broker-live position reporting as ADR 0005, updated the glossary, roadmap, development plan, README files, and automation/broker contracts.
- Why it matters: the plugin now matches the preferred product shape: no Google Sheets trade-record maintenance, no default local copy of full broker trade facts, and a first-class scheduled holdings/risk report that can use Longbridge or IBKR read-only data.
- Next step: define a fixture and output contract for the position daily report, then create the real Codex automation after cadence, timezone, broker source order, and snapshot policy are confirmed.

- Commit: pending
- Scope: planning, skill, data
- What changed: re-scoped the next product slice around analysis-first development. Added KVN momentum leaderboard terminology and planning: a dedicated `momentum-leaderboard` skill, KVN snapshot import/storage, `{runtime_dir}/momentum/kvn.sqlite` storage, Top10 default display, all-symbol lookup, S&P500-benchmarked rank, 60D `KVN P`, and Top10 entry-memory fields.
- Why it matters: the plugin's immediate value should be finding and validating trade candidates before perfecting records or sync details. The KVN leaderboard becomes the quantitative candidate source that macro/rates regime filters and industry/company research can consume.
- Next step: implement the KVN contract, fixture, verifier, and storage schema before returning to Google Sheets sync or deeper record-module refinement.

## 2026-06-18

- Commit: pending
- Scope: script, test
- What changed: added a shared `contract_verifier.py` module and a small self-test, then rewired weekly outlook, Trade Plan Preparation, and research report intake contract checks to use it. Added `record_schemas.py` as the canonical local CSV schema registry, wired daily initialization to it, added record template verification for exact headers and row widths, and fixed a misaligned `trades.csv` sample row.
- Why it matters: future product contracts can add acceptance checks without copying verifier loops, and local records now have a single schema source before broker adapters, trade review updates, statistics, and Google Sheets sync start writing rows.
- Next step: use the shared verifier and record schema registry for the next fixture-backed contract slice, then consider wiring these local checks into CI after the public workflow stabilizes.

- Commit: pending
- Scope: script, skill, reference, test
- What changed: added the Actual trade record module with `trade_records.py` and `update_trade_record.py`. Post-order review can create or update an `open` `trades.csv` row and append `reviews.md`; post-exit review updates the same trade with outcome, PnL/R, exit review, mistake tag, and lesson. Added a CLI self-test and contract check, and wired `$trade-review` guidance to use the script after user confirmation.
- Why it matters: interactive trade review now has a repo-owned write path for local records, so the workflow can preserve fresh entry rationale and later complete closed-trade statistics without hand-editing CSV.
- Next step: forward-test with one real confirmed post-order review and one post-exit review, then reuse the same schema path for one-way Google Sheets sync.

- Commit: pending
- Scope: script, reference, test
- What changed: fixed legacy `active` Sheet imports for older rows that do not contain `quantity`, `fees`, or `risk_amount`. The `update_trade_record.py` CLI now supports an explicit `--allow-unknown-execution-fields` flag that writes only those missing execution fields as `unknown`, while normal post-order review still requires resolved execution fields.
- Why it matters: existing Google Sheet trade history can be migrated and forward-tested without weakening the quality gate for fresh trade reviews.
- Next step: use the same explicit legacy mode when importing older sheet rows, and keep real-time trade review strict by default.

- Commit: pending
- Scope: script, fixture, reference, test
- What changed: added `import_legacy_active_csv.py` plus a fixture-backed self-test for legacy `active` tab CSV exports. The importer maps old Sheet columns into canonical `trades.csv`, writes staged `review_raw`, appends `reviews.md`, preserves rows with review text but blank `盈亏` as `not_counted`, and uses the explicit legacy unknown-execution-field mode for missing `quantity`, `fees`, or `risk_amount`.
- Why it matters: old Google Sheet trade history can now be moved into local canonical records before stats, setup review, or one-way Sheet sync work continues.
- Next step: run the importer on a broader private `active` export, inspect the local stats output, and then build one-way Google Sheets sync from local records.

## 2026-06-17

- Commit: pending
- Scope: skill, reference, template
- What changed: added a first-class `research-report-intake` capability for public/authorized report discovery and user-provided report digestion. The contract produces a `Research Report Digest`, `Claim Ledger`, `Verification Queue`, and `Trade Plan Preparation Impact`, and wires the new skill into the router, macro/equity research, local templates, and contract verification.
- Why it matters: the plugin can now treat research reports as structured, verifiable evidence instead of dumping long summaries or letting analyst opinions directly become trade setups.
- Next step: add realistic report-digestion fixtures and forward-test the skill on a user-provided report plus a public-source discovery prompt.

## 2026-06-16

- Commit: pending
- Scope: planning, skill, template, fixture
- What changed: introduced Trade Plan Preparation as the bridge from macro/financial/policy/industry/company research into Active Market Plan. Added the five v1 input reads, Cross-Section Candidate Pool, promotion guidance into `candidate setup`, and a contract verifier. Reordered the roadmap so `intraday_scan.py` waits until setup pool fields are stable.
- Why it matters: weekly and macro/equity research now serve plan preparation first, instead of producing generic macro notes or jumping directly into intraday scan logic.
- Next step: forward-test weekly and macro/equity outputs against the new Trade Plan Preparation contract, then build fixture files for setup promotion.

## 2026-06-14

- Commit: pending
- Scope: skill, template, fixture
- What changed: improved the weekly macro/policy/news outlook contract so weekly plans must rank event importance, apply source-priority levels, explain market transmission, tie events to existing holdings and new-position plans, include the week's market-moving earnings, recommend an overall strategy posture, filter Trump/White House policy noise, and avoid unexplained internal setup-status language. Added an expected 2026-06-15 weekly outlook fixture and a verification script for the contract.
- Why it matters: weekly planning now answers what matters for QQQ/VOO/DRAM/SOXX, what evidence is reliable enough to affect the plan, which earnings can move index/sector beta, whether the posture should be defensive, balanced, or high-beta momentum, what should be ignored, and what confirmation is needed before adding risk, instead of producing a generic macro calendar.
- Next step: use the fixture to forward-test `$weekly-trading-plan` output in the Daily Ops thread.

- Commit: pending
- Scope: decision, script, skill, sync
- What changed: split plugin development and trading operations into separate chat/workspace boundaries. Created a fixed `交易研究 Daily Ops` thread for weekly plans, daily tracking, and reviews. Added `runtime_dir` as the private working-memory root, defaulting to `~/Documents/dailytrades-runtime`, with `TRADING_RESEARCH_RUNTIME_DIR` and `--runtime-dir` overrides. Clarified that Google Sheets remains a compact one-way mirror while detailed records live locally.
- Why it matters: keeps public plugin development, git history, and reusable skills separate from private trading plans, broker-derived records, chart artifacts, and reviews.
- Next step: wire future trading-operation automations to the Daily Ops thread and implement the planned one-way Google Sheets sync against runtime records.

- Commit: pending
- Scope: script, template, skill
- What changed: added a local TradingView `lightweight-charts` HTML artifact generator and a QQQ OHLCV fixture. Updated chart artifact and output guidance so agents can show concise annotated charts while keeping full source notes in local records.
- Why it matters: gives price-action and multi-timeframe setup review a visual artifact path without building a persistent frontend dashboard.
- Next step: forward-test the chart artifact on authorized OHLCV exports and add a screenshot/export workflow for chat display.

- Commit: pending
- Scope: planning, data
- What changed: added `docs/PLUGIN_CONTENT_PLAN.md` to define the minimum useful plugin content set, fixture package requirements, product priorities, AI-native synthesis contract, and deferred scope. Initialized `data/market-plan.md` and `data/updates/2026-06-14.md` with a 2026-06-15 to 2026-06-19 Active Market Plan outlook.
- Why it matters: turns the next development slice into a concrete checklist, clarifies that the agent should read broadly but show concise decision notes, and gives the weekly planning workflow a real local plan artifact to use as fixture seed material.
- Next step: build daily fixture files and expected intraday scan output from the new Active Market Plan, then implement `intraday_scan.py`.

- Commit: `1a40139` `Document automation planning contract`
- Scope: planning, skill, decision
- What changed: added an automation contract for development task planning and Active Market Plan operations. Updated the existing Codex weekday development brief and end-of-day progress review automations to recommend and review daily product-capability tasks from the current roadmap.
- Why it matters: the project now has two explicit automation layers: development task planning for building the plugin, and future trading-operation prompts for Active Market Plan deep updates, quick updates, intraday monitors, post-market review, and broker reconciliation.
- Next step: confirm cadence and data-source permissions before creating trading-operation automations.

- Commit: `414a9ca` `Define active market plan and broker data contracts`
- Scope: planning, skill, template, script, decision
- What changed: replaced the weekly/daily split with one overwriteable Active Market Plan plus append-only update notes. Added setup-level status semantics, Active Market Plan and broker data contract references, canonical broker CSV templates, broker-neutral trade review language, Longbridge/IBKR/manual CSV read-only source boundaries, and broker/account risk splits in `portfolio_risk.py`.
- Why it matters: the plugin now has a clear product core: maintain current plan state, track setup-level opportunities, reconcile read-only broker facts, and keep order execution outside plugin scope.
- Next step: build fixture data for `market-plan.md`, update notes, setup pool, canonical broker CSV, intraday scan expectations, and two-stage trade review writing.

- Commit: `cc981f9` `Refine weekly and daily trading workflows`
- Scope: planning, skill, template
- What changed: realigned the plugin around a weekly market review and next-week trading plan package, plus daily premarket/intraday tracking with quick market, macro, policy, news, event, momentum, and level updates. Updated router behavior, weekly/daily skills, templates, shared references, roadmap, development plan, README, and glossary.
- Why it matters: keeps the product focused on the user's actual workflow: weekly review and opportunity discovery first, then daily dynamic tracking of prepared plans and trade levels.
- Next step: build fixture data that represents the full weekly package and daily tracking loop, then use it for TDD on intraday scanning and two-stage trade review writing.

- Commit: `4749ff0` `Split trading research plugin into focused skills`
- Scope: skill
- What changed: split the Trading Research System plugin from one oversized `trading-research` skill into a lightweight router plus focused skills for weekly planning, daily market tracking, intraday setup scanning, trade review, macro/equity research, portfolio risk, and trading statistics.
- Why it matters: makes the plugin usable as an agent toolbox, with narrower triggers and less context bloat for each workflow.
- Next step: forward-test the router and priority skills on realistic prompts, then build fixture data for weekly plans, daily tracking, IBKR-like trade facts, two-stage reviews, and scan outputs.

- Commit: `e9870fc` `Prioritize weekly plan and two-stage trade review`
- Scope: planning, skill, template
- What changed: reprioritized the product loop around weekly trading plan construction, daily market tracking, plan-scoped opportunity discovery, IBKR-backed trade facts, and two-stage post-order/post-exit review. Added weekly plan and daily market tracking templates, updated the trading skill routing, and split interactive review guidance into entry-time and exit-time stages.
- Why it matters: aligns the plugin with the user's immediate workflow need: generate initial trade ideas and plans weekly, dynamically track the current market each day, and capture actual trades while the entry context is fresh before final outcome review.
- Next step: build fixture data for weekly plans, daily tracking, IBKR-like trade facts, post-order review, post-exit review, and expected intraday scan outputs.

- Commit: `7799a12` `Refocus daily planning on product capability`
- Scope: planning
- What changed: corrected `docs/DEVELOPMENT_PLAN.md` and weekday automation prompts so daily planning prioritizes product-capability work over process or harness work.
- Why it matters: keeps the project centered on the trading research plugin's product loop: local records, planned setup scanning, trade review, statistics, sync, and chart artifacts.
- Next step: start the next task with fixture data, then implement the local intraday scan script against those fixtures.

- Commit: `abf125a` `Define development workflow and test scope`
- Scope: decision
- What changed: added `docs/DEVELOPMENT.md` to define Codex/Claude handoff, worktree use, TDD boundaries, test scope, lightweight CI policy, and acceptance gates. Clarified that live IBKR connector behavior is outside this repo's test scope.
- Why it matters: gives implementation tasks a stable development harness without confusing external connector capabilities with repo-owned code.
- Next step: add fixture data and a lightweight local test harness before enabling GitHub Actions CI.

- Commit: `3248b5b` `Add daily development plan and automation source`
- Scope: planning
- What changed: added `docs/DEVELOPMENT_PLAN.md` as the source of truth for active development priorities, daily planning, and progress review; registered it in `docs/ROADMAP.md`; updated weekday development automations to use it.
- Why it matters: the project now has a daily operating loop that reports current tasks with priority, asks the user how to arrange the day, and records end-of-day progress without relying on a separate dev repository.
- Next step: use the next morning brief to select the next implementation task from the active task board.

- Commit: `a7d4f73` `Document lightweight branch strategy`
- Scope: decision
- What changed: defined a lightweight branch model with `master` as the stable public baseline, `dev` as the integration branch, and `codex/<task>` as task branches for Codex or Claude Code work.
- Why it matters: gives the project a clear GitHub trajectory and merge path without introducing heavyweight release/version semantics before the initial complete workflow is settled.
- Next step: create and push `master` and `dev` from the current reviewed baseline, then use `dev` as the default integration base for new tasks.

- Commit: `dc83ad2` `Document no separate dev repo requirement`
- Scope: decision
- What changed: confirmed that a separate `dailytrades-dev` repository is not required for the current stage. The local clone created for exploration was removed, and Codex/Claude collaboration rules will run as harness protocol until they become durable enough to need their own private storage.
- Why it matters: reduces process overhead while preserving the public/private boundary for the plugin repository.
- Next step: use the harness protocol on the next implementation task, then decide whether any part of it needs a persistent private template.

## 2026-06-13

- Commit: `46c46fa` `Document intraday scan roadmap`
- Scope: planning, skill
- What changed: established the public planning baseline in `docs/ROADMAP.md`; added capability boundaries, execution method, task breakdown, milestone plan, progress status, and MVP acceptance criteria. Added `references/intraday-setup-scan.md` and routed intraday plan monitoring through the plugin skill.
- Why it matters: GitHub now has a readable project trajectory instead of relying only on chat context and scattered commits.
- Next step: implement a local intraday scan script that reads `intraday-watchlist.csv` and emits status plus attention-priority summaries.

- Commit: `f8e9f8b` `Define intraday trigger confirmation rules`
- Scope: skill, domain language
- What changed: documented trigger confirmation rules and instrument-specific strictness for `triggered` status.
- Why it matters: a plan can no longer become actionable from price contact alone; it must have execution-timeframe setup confirmation and acceptable risk/reward.
- Next step: convert the trigger-confirmation rules into script-readable scan logic.

- Commit: `e73597d` `Define needs review intraday status`
- Scope: domain language
- What changed: added the `needs_review` state for unclear, incomplete, conflicted, data-limited, news-affected, or risk-constrained situations.
- Why it matters: the scanner has a safe state for human review instead of forcing false precision.
- Next step: make `needs_review` an explicit output status in intraday scan artifacts.

- Commit: `a1a9d02` `Remove internal agent collaboration docs from plugin repo`
- Scope: repo boundary
- What changed: removed internal collaboration files from the public plugin repository.
- Why it matters: `dailytrades` stays focused on distributable plugin artifacts and user-readable docs; internal planning and agent coordination settings stay outside the public plugin repository.
- Next step: keep future public updates limited to plugin artifacts, roadmap, ADRs, project log, and user-facing docs.

- Commit: `fb36618` `Add daily trade review workflow`
- Scope: skill, template, script
- What changed: added interactive trade review guidance and review-appending support.
- Why it matters: actual trades can be recorded and reviewed through a structured one-question-at-a-time workflow rather than loose memory.
- Next step: connect review intake to local `trades.csv` and Google Sheets one-way sync.

- Commit: `0b3cb5b` `Add trading research system plugin`
- Scope: plugin
- What changed: introduced the Codex plugin with skill, references, scripts, templates, and personal marketplace install flow.
- Why it matters: the project became an agent-usable plugin instead of only a prompt/workflow document.
- Next step: keep expanding plugin references and scripts around the documented roadmap.

- Commit: `dbdc43d` `Set up trading research workflow`
- Scope: planning
- What changed: created the first public workflow docs for macro policy filtering, research-note validation, stock screening, price action timing, and portfolio risk review.
- Why it matters: established the initial research process that later became the plugin skill.
- Next step: keep workflow docs aligned with `CONTEXT.md` and plugin references.
