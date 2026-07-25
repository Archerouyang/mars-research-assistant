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

## Product Thinking And MVP

- Start product work from first principles: identify the user's actual decision
  or job, known facts, assumptions, constraints, safety invariants, and the
  smallest outcome that can prove useful value.
- Prefer an early minimum viable prototype over a broad implementation. Make it
  narrow, usable, and inspectable enough for the user to judge the core
  workflow, interaction, information hierarchy, and output format.
- MVP means minimum scope, not low quality. Preserve the clarity, terminology,
  essential states, failure behavior, and visual hierarchy required for a
  credible product experience.
- Optimize for the user's real workflow and decision quality, not for apparent
  completeness, architectural sophistication, or the amount of generated
  output. Every element should help the user understand, decide, or act.
- Present the prototype for manual acceptance before expanding architecture,
  compatibility layers, automation, or test coverage. After acceptance, harden
  the approved behavior into a stable format or contract and broaden only where
  evidence or risk justifies it.
- Before every substantive response or artifact, perform a requirement-gap
  self-review: check what the user explicitly requested, what the response still
  omits, what may have been misinterpreted, whether prior feedback was applied,
  and whether the delivered format and interaction match the request. Correct
  discovered gaps before presenting the result.
- Explicitly disclose any unmet requirement, unresolved assumption, or deferred
  work. Passing tests is not a substitute for meeting the user's actual request.
- Treat user dissatisfaction and improvement feedback as product evidence.
  Correct the current output, record the actionable item in the appropriate
  planning record, and carry it into the next iteration instead of leaving it
  only in chat.

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
- Default to the minimum useful automated verification: focused tests for the
  changed behavior, one narrow end-to-end or openability smoke when needed, and
  `git diff --check`. Do not automatically expand into the full repository
  suite, broad acceptance matrices, repeated browser runs, or exhaustive visual
  checks.
- Broaden automated verification only when a release gate requires it, the
  change crosses a shared compatibility or safety interface, a reproduced
  defect needs wider regression evidence, or the user explicitly requests it.
- Deliver a usable artifact or workflow to the user as early as possible and
  prefer explicit human acceptance of user-facing behavior over agent-generated
  visual proof. Automated checks support that decision; they do not replace it.
- When the user asks for minimal testing, treat that as a strict scope limit.
  Report the small checks that ran and identify any intentionally deferred
  suites without running them speculatively.
- Run non-quant 1.0 acceptance and release-readiness checks in
  `/Users/archer/Documents/交易想法-1-0-uat`, re-pinned to the accepted `dev`
  commit. A stale UAT snapshot is not release evidence.

## Visual Artifact Delivery

- Give the user the real generated HTML artifact for visual acceptance before
  public cutover, packaging, or broad screenshot-matrix work. Automated visual
  checks do not replace the user's visual approval.
- Resolve every artifact path from the worktree that actually generated it.
  Before sharing a path or URL, verify that the file exists in that worktree;
  never assume the main workspace contains an isolated worktree's outputs.
- Do not hand `file://` links to the Codex in-app browser. Serve the narrowest
  artifact directory from the generating worktree on `127.0.0.1`, then verify
  the HTTP page loads with the expected title and view controls before giving
  the user the URL. Keep that local server running for the review session.
- For manual visual acceptance, first deliver the canonical Overview and all
  intended interactive views. Record concrete user feedback and do not claim
  visual acceptance until the user explicitly approves the rendered result.
- Keep routine automated visual gates limited to artifact determinism,
  manifest/hash integrity, offline and privacy safety, plugin synchronization,
  and a minimal openability/interaction smoke. Run broad viewport, pixel, or
  screenshot matrices only when the approved issue specifically requires them
  or a reproduced defect needs them.

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
