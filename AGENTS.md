# Project Agent Instructions

This repository is the public-facing plugin repo for the Daily Trades / Trading
Research System. Keep it focused on reusable plugin assets and user-readable
project documentation.

## Scope

- Plugin source lives under `plugins/`.
- Project docs live under `docs/`, `CONTEXT.md`, and top-level user-readable
  markdown files.
- Do not commit private trading records, broker exports, runtime market plans,
  screenshots, generated chart artifacts, credentials, or personal account data.
- Runtime trading data belongs outside the plugin repo, or in ignored local
  paths such as `data/` while the runtime directory is being finalized.

## Development Workflow

- Use `dev` as the default development branch.
- Keep changes small and reviewable.
- Use git for plugin/documentation changes and preserve unrelated user work.
- Prefer TDD for code paths, scripts, and data transformations where behavior
  can be tested cheaply.
- For plugin packaging or cache updates, use the existing project scripts and
  documented workflow before inventing a new path.

## Skill Routing

- For plugin development work, prefer the Matt Pocock engineering skill set:
  `to-issues`, `to-prd`, `triage`, `tdd`, `review`, `diagnose`,
  `improve-codebase-architecture`, `zoom-out`, and related setup skills.
- Use those engineering skills for planning, issue creation, implementation
  slicing, TDD, code review, diagnosis, and architecture work.
- Do not use the Trading Research System skills as development-process
  authority while editing this plugin. Those skills are the product being built.
- Use Trading Research System skills only to run or verify trading-research
  behavior, fixture outputs, and user-facing Daily Ops workflows.
- State which skills are being used in working updates when the task depends on
  them, especially when switching between development work and product-behavior
  verification.

## Plugin Work

- Trading workflow behavior should live in the Trading Research System skills,
  references, templates, or scripts, not in this instruction file.
- Keep AI-native output concise: read and verify more than is shown to the user.
  Put detailed working memory in runtime notes, not public plugin docs.

## Claude Code Collaboration

- Codex coordinates the task and performs final review.
- Claude Code may be used as an implementation subagent for scoped code or docs
  tasks.
- Ask Claude Code to self-check its changes before Codex reviews them.
- Do not let subagents push, reset, clean, or perform destructive git operations.

## Model-tier Subagents

Use the GPT-5.6 model tiers when the current Codex or API runtime exposes
explicit subagent model selection. Check capability before dispatch. The agent
must not claim a model tier was used when it was unavailable; record the
fallback in the run metadata instead.

The default production path is `Luna -> Terra -> Sol`:

- GPT-5.6 Luna prepares inputs: source collection, normalization, deduplication,
  schema checks, document chunking, mechanical repo inspection, and other
  bounded preprocessing. Luna must not make the final trading-research or
  architecture decision.
- GPT-5.6 Terra performs the primary analysis, implementation, synthesis, and
  first self-check. Terra is the default tier for factor research, market and
  company analysis, price-action classification, code changes, and routine
  review.
- GPT-5.6 Sol escalation is reserved for material evidence conflicts, model
  promotion or rollback, unexplained backtest behavior, difficult architecture
  decisions, high-impact portfolio-risk questions, or a Terra result that
  remains low-confidence after verification.

For plugin development, Codex remains the coordinator and final reviewer. Give
each subagent a narrow work packet, require a self-check, and review the diff or
artifact before accepting it. Subagents must not push, reset, clean, delete
shared data, expose credentials, or perform broker/order actions.

For Trading Research System runs, Luna may prepare public or authorized inputs,
Terra owns the normal user-facing analysis, and Sol only reviews the escalation
case. Deterministic scripts remain the authority for rankings, model metrics,
and stored run state; model-tier routing must not silently change those values.

## Trading Safety Boundary

- The plugin is decision support only.
- It may read broker data through authorized connectors and prepare plans,
  scans, reviews, and risk notes.
- It must not create, submit, or imply approval of real orders.
