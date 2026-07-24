# Technical Debt Register

This register records accepted design and maintenance costs that are not merely
open bugs. It makes the accumulated cost visible and defines when architecture
optimization becomes a planned delivery task.

Do not include private data, credentials, broker/account details, or hidden
runtime contents. Each item must point to public-safe evidence such as a test,
contract, debug item, or source file.

## What Belongs Here

A technical-debt item has a known or strongly evidenced future cost: duplicated
logic, unclear ownership, fragile interfaces, missing test seams, obsolete
compatibility layers, or a recurring root cause. A new feature belongs in the
development plan. An observed defect belongs in the debug plan until diagnosis
shows that it is technical debt.

## Entry Schema

| Field | Required content |
| --- | --- |
| ID | Stable `TD-YYYYMMDD-NN` identifier |
| Status | `candidate`, `accepted`, `planned`, `in_progress`, `removed`, `declined`, or `watching` |
| Scope | Owning module or bounded subsystem |
| Evidence | Debug IDs, test/contract, or source pointers |
| Cost | Concrete maintenance, reliability, or delivery cost |
| Score | Impact + recurrence + change cost, as defined below |
| Next action | Smallest evidence, decision, or refactor slice |
| Exit | Observable condition that removes the debt |

## Debt Score

Each accepted item has a score from 1 through 7:

- Impact: 1 low, 2 material, 3 high effect on correctness, safety, or delivery.
- Recurrence: 0 isolated, 1 likely to recur, 2 already recurring across work.
- Change cost: 0 local, 1 crosses one boundary, 2 crosses multiple modules or
  requires a new test seam.

The score prioritizes review; it does not replace engineering judgement. A
safety or data-boundary concern is always handled at its actual severity even
when its numeric score is low.

## Architecture Optimization Triggers

Create an architecture-optimization planning task before scheduling further
feature work in the affected subsystem when any of these is true:

1. one bounded subsystem has open accepted debt with a combined score of 12 or
   more for two consecutive weekly reviews;
2. three or more open debt items point to the same module boundary or ownership
   ambiguity;
3. the same diagnosed root cause causes two defects or corrective patches within
   30 days;
4. a planned P0/P1 change would require copying behavior across modules,
   bypassing a missing test seam, or extending an interface with no clear owner;
   or
5. a P0 safety, data-boundary, or decision-correctness issue identifies a
   systemic architecture failure.

On a trigger, add a bounded `Architecture Optimization` task to
`docs/DEVELOPMENT_PLAN.md`. First map ownership and dependencies, define the
target invariant and regression baseline, record any hard-to-reverse decision
in an ADR, and split the work into independently verifiable slices. Do not
start a broad rewrite or remove a compatibility path without this plan and
verification baseline.

## Active Register

| ID | Status | Scope | Evidence | Cost | Score | Next action | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TD-20260711-01 | accepted | Canonical record schemas | `docs/DEVELOPMENT_PLAN.md` task "Re-scope canonical record schema registry" | Fixture and compatibility schemas have unclear long-term ownership, making future adapters and migrations harder to change safely. | 6 | Define canonical, compatibility, and deprecated schema ownership before new record adapters are added. | One registry names each schema owner, compatibility policy, and test boundary. |
| TD-20260711-02 | removed | Runtime capability/state taxonomy | `DBG-20260711-01`, `DBG-20260711-02`; final accepted Prompt 7 UAT session `019f5ed4-9994-7832-bcef-82f6681a34fd` | The shared taxonomy cost was retired after branch coverage, direct-entry propagation, and accepted fresh UAT preserved the runtime and startup axes. | 5 | None; monitor through the retained runtime-health and Daily Ops contracts. | Shared taxonomy has full branch coverage, affected consumers preserve it, and accepted UAT passes. |
| TD-20260711-03 | removed | Behavioral contract depth | `DBG-20260711-04` to `DBG-20260711-06`; repo-level Behavior Contract Matrix modules and final two-axis review on `codex/behavior-contract-matrix` | The shallow-contract cost was retired by replacing duplicated subprocess scenarios with reconciliation, startup-surface, and setup-key/OHLCV matrices that preflight harness state and aggregate behavior mismatches. | 6 | None; retain the focused matrices in the Skill and MVP gates. | Focused, compile, Skill, and MVP gates pass; direct activation, state/input combinations, validation precedence, cwd, and forbidden side effects are covered; final review has no findings. |
| TD-20260714-01 | accepted | Behavior ownership across routing surfaces | Router and weekly entry duplication; Prompt 7 failures across `70b5787`, `f739019`, and final `19ca4ae` | One behavior is still distributed across router, focused workflow, reference, fixture, and verifier, so a change can remain internally inconsistent even though the repository now has only one portable distribution surface. | 4 | Map the authoritative behavior owner and injected entry surfaces before adding another cross-workflow rule. | Each exact behavior has one named owner and all direct activation surfaces derive from or validate against it. |

`TD-20260711-03` previously met Architecture Optimization Trigger 3. The
bounded test-seam task recorded in `docs/DEVELOPMENT_PLAN.md` is complete, so
the debt is removed and no longer contributes to the open-score threshold.

The native wrapper release-propagation part of `TD-20260714-01` was retired on
2026-07-20 when the wrappers, marketplace manifests, synchronization code, and
wrapper-only checks were removed. The debt remains `accepted` only for behavior
ownership across router and direct-activation surfaces.

## Review Cadence

Review this register during the weekly planning review and after every P0/P1
debug closure. Update score and evidence, remove resolved items, and record any
triggered optimization task in the development plan. Do not silently bury debt
inside a feature ticket or a debug fix.
