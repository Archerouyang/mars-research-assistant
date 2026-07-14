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
| TD-20260711-03 | accepted | Behavioral contract depth | `DBG-20260711-04` to `DBG-20260711-06`; repeated corrective reviews through `19ca4ae` | Phrase-presence, expected-response fixtures, and incomplete entry/input matrices repeatedly missed broker-agnostic reconciliation, startup-state propagation, direct skill activation, validation ordering, and actual command cwd while green suites continued to pass. | 6 | Implement the bounded behavior-contract matrix task in `docs/DEVELOPMENT_PLAN.md` before adding capability in the affected workflow. | High-risk contracts exercise required structure, state/input matrices, direct activation surfaces, command cwd, and failure ordering rather than only keyword presence. |
| TD-20260714-01 | accepted | Behavior ownership and plugin release propagation | Router and weekly entry duplication; Prompt 7 failures across `70b5787`, `f739019`, and final `19ca4ae`; personal source/cache refresh required for each UAT | One behavior is distributed across router, focused skill, reference, fixture, verifier, personal plugin source, and installed cache. Changes can be locally green yet absent from the model-selected entry or installed runtime. | 6 | Map the authoritative owner and injected entry surfaces, then design one bounded source-of-truth or generation seam plus a source/cache release check. | Each exact behavior has one named owner, all direct activation surfaces derive or validate against it, and the release check proves the installed cache matches the accepted source. |

`TD-20260711-03` now meets Architecture Optimization Trigger 3: the same
contract-depth cause has required multiple corrective patches within 30 days.
The planned response is a bounded test-seam improvement, not a product rewrite;
the UAT gate is closed, so this bounded task is now the next subsystem priority.

`TD-20260711-03` and `TD-20260714-01` have a combined open score of 12 in this
review. Architecture Optimization Trigger 1 requires the threshold for two
consecutive weekly reviews, so it is not yet independently satisfied; Trigger 3
already requires the bounded architecture task recorded in
`docs/DEVELOPMENT_PLAN.md`.

## Review Cadence

Review this register during the weekly planning review and after every P0/P1
debug closure. Update score and evidence, remove resolved items, and record any
triggered optimization task in the development plan. Do not silently bury debt
inside a feature ticket or a debug fix.
