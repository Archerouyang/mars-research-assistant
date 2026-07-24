# Project Agent Instructions

This is the public 火星投研助手 (Mars Research Assistant) portable Skill
repository. Keep it limited to reusable Skill assets and user-readable project
docs.

## Repository Boundary

- The only canonical portable Skill behavior source is
  `skills/mars-research-assistant/`.
- Project docs live under `docs/`, `CONTEXT.md`, and top-level Markdown files.
- Never commit private trading records, watchlists, profiles, broker exports,
  runtime plans, credentials, account data, or private/user-specific charts.
  A dated README example may use public market data only when the user
  explicitly requests publication and the exported image passes a privacy
  review; this exception never permits account or private-runtime content.
- Private runtime state belongs outside this repository.
- The Skill is decision support only. It may use authorized read-only data,
  but must never create, modify, cancel, or imply approval of real orders.
- The system does not exist to predict market direction. It applies Bayesian
  decision support: begin with an explicit prior, update confidence as new
  observations arrive, and choose a conditional action with acceptable risk.
  Scenarios, levels, and forecasts are evidence inputs, not certainty claims.

## Coordinator Workflow

Codex is the planning, coordination, review, and integration owner. For a new
development or debug request, follow this order:

1. Align the complete requirement and acceptance boundary with the user.
2. Record the approved work in the correct planning document.
3. Decide whether the approved objective needs Goal mode using the context and
   goal hygiene rules below.
4. Dispatch bounded implementation packets to the designated development or
   debug task/subagent; do not implement substantial work in the coordinator
   task unless the user explicitly asks.
5. Review completed work against the pinned baseline and approved spec.
6. Integrate only after verification and user approval.

Default to no subagents for planning, status, and narrow verification. Use the
fewest agents that provide clear parallel value. Subagents must self-check and
must not push, reset, clean, delete shared data, expose credentials, or perform
broker/order actions.

When approved work genuinely benefits from multiple isolated temporary
branches, and handing off bounded branches will not slow the coordinator's own
active implementation, the coordinator may assign those branches to the
designated `开发1` task. Keep single-branch mainline work local by default; do
not dispatch merely to move context elsewhere.

## Context And Goal Hygiene

- Keep the coordinator context focused on requirements, decisions, review
  findings, and integration state. Return bounded summaries from workers rather
  than raw logs or full transcripts.
- For every long-running subagent, include a context checkpoint instruction in
  its task packet. When its context reaches 140k tokens, stop normal work. At a
  skill phase boundary, compact that subagent thread before continuing. If it
  is mid-phase or manual compact is unavailable, write a durable handoff and
  resume the remaining work in a fresh thread; do not keep working in degraded
  context.
- Use Goal mode only for an approved, multi-step objective that benefits from
  automatic continuation and has measurable completion criteria. A goal must
  state the outcome, constraints, and verification; put details longer than the
  goal field in the approved spec or planning document and point to it.
- Do not use Goal mode for requirement alignment, planning, status checks,
  narrow verification, formal review, one-turn edits, or work waiting on a user
  decision or external state. Use Plan mode first when the outcome or acceptance
  boundary is still unclear.
- Put the end-to-end goal in the coordinator task only when that task owns
  dispatch, review, and integration through completion. Give a worker its own
  goal only when its bounded implementation independently needs automatic
  continuation. Do not create duplicate goals with the same completion
  criteria across coordinator and worker tasks.
- Parallel goals must use separate tasks and, for overlapping repositories,
  separate worktrees. Never let two active goals write the same files.

## Matt Pocock Skills And Goal Mode

- Treat Goal mode as the execution envelope around the Matt Pocock skill flow,
  not as a replacement for any skill.
- During discovery and specification, do not create a goal. Route with
  `/ask-matt`, then use `/grill-with-docs`, an optional `/prototype`,
  `/to-spec`, and `/to-tickets` as required. Preserve one context through
  ticket approval so decisions are not lost.
- After the user approves the spec and ticket breakdown, create a coordinator
  goal only when delivery spans multiple tickets or sessions and the
  coordinator owns review and integration. The goal should reference the
  approved spec or plan and state aggregate outcome, constraints, and release
  verification instead of duplicating every ticket.
- Work the unblocked ticket frontier in fresh worker tasks or worktrees. Each
  worker runs `/implement` for one bounded ticket; `/implement` uses `/tdd`
  where appropriate and finishes with `/code-review`. Give that worker a goal
  only if the ticket itself needs automatic continuation; its completion
  criteria stop at the ticket acceptance checks and local verification.
- For bugs, use `/diagnosing-bugs` to establish a red-capable feedback loop and
  evidence-backed closure criteria. Create a debug goal only when the approved
  diagnosis-and-fix effort is multi-step; keep the goal tied to the reproduced
  symptom, regression test, and verification command.
- A worker completion is returned as a bounded handoff. The coordinator reviews
  against the pinned baseline and spec, integrates approved tickets, runs the
  aggregate verification, and only then completes the end-to-end goal.
- Respect skill phase boundaries for context cleanup. The installed
  `/ask-matt` flow prefers a handoff before its approximately 120k smart-zone
  boundary; the project-level 140k rule is a hard checkpoint for long-running
  subagents. Do not compact in the middle of a skill phase: compact at an
  intentional boundary, or hand off to a fresh task when already mid-phase.

## Development And Git

- Use `dev` as the default development branch and `codex/<task>` for isolated
  work. Keep changes small, reviewable, and Git-managed.
- Preserve unrelated user work. Do not switch the main workspace merely to run
  acceptance or integration checks.
- Prefer TDD for scripts, transformations, and other cheaply testable behavior.
- Use existing packaging, cache, and verification scripts before adding a new
  path.
- Run non-quant 1.0 acceptance and release-readiness checks in
  `/Users/archer/Documents/交易想法-1-0-uat`, re-pinned to the accepted `dev`
  commit. A stale UAT snapshot is not release evidence.

## Planning Records

- `docs/DEVELOPMENT_PLAN.md`: features, integrations, and approved bounded
  architecture work.
- `docs/DEBUG_PLAN.md`: reproducible defects, evidence, and closure criteria.
- `docs/TECHNICAL_DEBT.md`: accepted systemic cost and architecture triggers.
- P0 debug work precedes feature work. Broad architecture changes require a
  triggered debt item, regression baseline, bounded plan, and ADR when the
  decision is hard to reverse.

## Product Prototyping And Acceptance

- Start from first principles and build the smallest viable prototype that can
  answer the product question. Preserve product quality in hierarchy,
  information density, interaction, and failure behavior; MVP does not mean a
  disposable user experience.
- Keep automated acceptance minimal and decision-relevant. Prefer focused
  checks for schema, provenance, privacy, safety, and artifact openability;
  present the real artifact or workflow for user-owned manual acceptance.
- Before replying, compare the result with every explicit requirement and
  identify missing evidence, weak assumptions, unclear copy, or unmet product
  expectations. Correct them in the current iteration when feasible.
- Record explicit dissatisfaction and improvement requests in `DEBUG_PLAN` or
  `DEVELOPMENT_PLAN` as appropriate. Do not let product feedback remain only in
  chat history.
- Once the user explicitly freezes an accepted workflow or surface, treat it
  as a release contract. Do not change its information architecture, source
  routing, interaction model, or safety boundary without renewed acceptance;
  source-backed data, timestamps, concise copy, accessibility, and compatible
  defect fixes remain allowed.

## Skill Routing

- Use Matt Pocock engineering skills for development work: requirement
  shaping, planning, issue slicing, TDD, diagnosis, review, and architecture.
- Use Mars Research Assistant skills only to verify the product's trading
  behavior, fixtures, and Daily Ops UX; they are not development-process
  authority.
- State the active skill in progress updates when skill instructions affect the
  workflow.

## Model-tier Subagents

- A worker self-check is evidence, not approval. Codex owns the final
  `accept`, `changes_requested`, or `reject` decision.
- Formal reviews use the `/code-review` skill, a pinned baseline/spec, and
  separate Standards and Spec findings. Rerun the smallest useful checks
  independently.
- Use explicit model-tier routing only when the runtime exposes it; the agent
  must not claim a model tier was used when it was unavailable.
- GPT-5.6 Luna prepares only materially large or ambiguous bounded inputs.
- GPT-5.6 Terra performs the primary analysis, implementation, and routine
  review.
- GPT-5.6 Sol escalation is reserved for coordination, material conflicts, or
  genuine high-impact review needs.
- Update debug or technical-debt records when review evidence changes status.
