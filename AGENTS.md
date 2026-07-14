# Project Agent Instructions

This is the public DailyTrades / Trading Research System plugin repository.
Keep it limited to reusable plugin assets and user-readable project docs.

## Repository Boundary

- The only canonical portable Skill behavior source is
  `skills/trading-research-system/`.
- `plugins/trading-research-system/` is the Codex/Claude native wrapper,
  generated deterministically from the canonical Skill by
  `scripts/sync_native_plugin.py`; do not maintain duplicate behavior there.
- Project docs live under `docs/`, `CONTEXT.md`, and top-level Markdown files.
- Never commit private trading records, watchlists, profiles, broker exports,
  runtime plans, credentials, account data, or user-generated charts.
- Private runtime state belongs outside this repository.
- The plugin is decision support only. It may use authorized read-only data,
  but must never create, modify, cancel, or imply approval of real orders.

## Coordinator Workflow

Codex is the planning, coordination, review, and integration owner. For a new
development or debug request, follow this order:

1. Align the complete requirement and acceptance boundary with the user.
2. Record the approved work in the correct planning document.
3. Create a goal for the approved objective.
4. Dispatch bounded implementation packets to the designated development or
   debug task/subagent; do not implement substantial work in the coordinator
   task unless the user explicitly asks.
5. Review completed work against the pinned baseline and approved spec.
6. Integrate only after verification and user approval.

Default to no subagents for planning, status, and narrow verification. Use the
fewest agents that provide clear parallel value. Subagents must self-check and
must not push, reset, clean, delete shared data, expose credentials, or perform
broker/order actions.

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

## Skill Routing

- Use Matt Pocock engineering skills for development work: requirement
  shaping, planning, issue slicing, TDD, diagnosis, review, and architecture.
- Use Trading Research System skills only to verify the product's trading
  behavior, fixtures, and Daily Ops UX; they are not development-process
  authority.
- State the active skill in progress updates when skill instructions affect the
  workflow.

## Review And Models

- A worker self-check is evidence, not approval. Codex owns the final
  `accept`, `changes_requested`, or `reject` decision.
- Formal reviews use the `review` skill, a pinned baseline/spec, and separate
  Standards and Spec findings. Rerun the smallest useful checks independently.
- When explicit model-tier routing is available, use Terra for implementation
  and routine review, Luna only for materially large input preparation, and Sol
  for coordination or genuine escalation. Never claim an unavailable tier.
- Update debug or technical-debt records when review evidence changes status.
