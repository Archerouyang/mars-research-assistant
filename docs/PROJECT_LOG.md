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

## 2026-06-14

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
