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
