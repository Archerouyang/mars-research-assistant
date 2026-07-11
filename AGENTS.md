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

## 1.0 Acceptance Workspace

- Run the current non-quant 1.0 acceptance, plugin verification, MVP smoke,
  and release-readiness checks from
  `/Users/archer/Documents/交易想法-1-0-uat`.
- Keep `/Users/archer/Documents/交易想法` on its active development branch;
  do not switch that workspace for acceptance testing.
- The acceptance workspace is currently a detached `dev@a19a5ed` snapshot.
  Recreate or re-pin it after an accepted `dev` change before treating a test
  result as release evidence.

## Planning Records

- Keep feature, integration, and approved architecture-optimization work in
  `docs/DEVELOPMENT_PLAN.md`.
- Record observed defects and their reproducible closure evidence in
  `docs/DEBUG_PLAN.md`; do not relabel an unresolved symptom as architecture
  work.
- Record accepted systemic maintenance cost in `docs/TECHNICAL_DEBT.md` and
  use its triggers before scheduling a broad architecture optimization.
- A P0 debug item takes precedence over feature work. A triggered architecture
  optimization needs a bounded plan, regression baseline, and ADR when the
  decision is hard to reverse; do not start a broad rewrite by default.

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

- Codex coordinates the task and performs final review. This includes reviewing
  completed development and debug changes from other Codex tasks/chats before
  they are accepted, merged, packaged, or treated as release evidence.
- For cross-task reviews, use the `review` skill, pin the implementation
  baseline and originating spec, isolate unrelated concurrent work, and report
  Standards and Spec findings separately before giving an acceptance decision.
- Do not load an entire development/debug chat or full diff into the Sol
  coordinator by default. When the coordinator is GPT-5.6 Sol Ultra, prefer
  direct read-only baseline/file-scope recovery and use no preparation
  subagent for small or medium reviews.
- Spawn review agents with isolated context (`fork_context: false`) and a narrow
  packet containing only the baseline, spec, owned files, untracked files,
  standards sources, and verification evidence. Limit each review result to
  concise findings with severity, file/line, reproduction, and confidence.
- Minimize subagent count in Sol Ultra mode. If the `review` skill requires
  separate Standards and Spec axes, spawn exactly two explicit Terra reviewers
  and no Luna by default. Use Luna only when scope recovery is materially large
  or ambiguous enough that Sol cannot produce the packet cheaply with a few
  read-only commands.
- Outside formal review, default to zero subagents for documentation, planning,
  status, narrow fixes, and straightforward verification. Use one bounded
  subagent when it creates clear parallel value; use more only for genuinely
  independent work streams.
- Sol owns the final `accept / changes_requested / reject` decision. It reads
  the cited hotspots and reruns the smallest useful checks, but directly reviews
  the full critical path only for P0/safety/private-data risks, architecture
  triggers, cross-module contract changes, conflicting reviewer evidence, or a
  low-confidence Terra result.
- A worker task's self-check is evidence, not final approval. Codex reruns the
  smallest useful verification and updates `docs/DEBUG_PLAN.md` and
  `docs/TECHNICAL_DEBT.md` when review findings change their status.
- Claude Code may be used as an implementation subagent for scoped code or docs
  tasks.
- Ask Claude Code to self-check its changes before Codex reviews them.
- Do not let subagents push, reset, clean, or perform destructive git operations.

## Model-tier Subagents

Use the GPT-5.6 model tiers when the current Codex or API runtime exposes
explicit subagent model selection. Check capability before dispatch. The agent
must not claim a model tier was used when it was unavailable; record the
fallback in the run metadata instead.

The available production path is `Luna -> Terra -> Sol`, but Sol Ultra uses it
selectively rather than on every task:

- GPT-5.6 Luna prepares inputs: source collection, normalization, deduplication,
  schema checks, document chunking, mechanical repo inspection, and other
  bounded preprocessing. Luna must not make the final trading-research or
  architecture decision.
- GPT-5.6 Terra performs the primary analysis, implementation, synthesis, and
  first self-check. Terra is the default tier for factor research, market and
  company analysis, price-action classification, code changes, and routine
  review. Routine review dispatch must explicitly select Terra rather than
  inheriting the Sol coordinator model.
- GPT-5.6 Sol escalation is reserved for material evidence conflicts, model
  promotion or rollback, unexplained backtest behavior, difficult architecture
  decisions, high-impact portfolio-risk questions, or a Terra result that
  remains low-confidence after verification.

For plugin development, Codex remains the coordinator and final reviewer. Give
each subagent a narrow work packet, require a self-check, and review the diff or
artifact before accepting it. Subagents must not push, reset, clean, delete
shared data, expose credentials, or perform broker/order actions.

In Sol Ultra mode, do not spawn Luna merely to list files, run `git status`, or
summarize a small thread. Reserve Luna for large source sets, ambiguous ownership
across branches/worktrees, or other bounded preprocessing that would otherwise
consume substantial coordinator context.

For Trading Research System runs, Luna may prepare public or authorized inputs,
Terra owns the normal user-facing analysis, and Sol only reviews the escalation
case. Deterministic scripts remain the authority for rankings, model metrics,
and stored run state; model-tier routing must not silently change those values.

## Trading Safety Boundary

- The plugin is decision support only.
- It may read broker data through authorized connectors and prepare plans,
  scans, reviews, and risk notes.
- It must not create, submit, or imply approval of real orders.
