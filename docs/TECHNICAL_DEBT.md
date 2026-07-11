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
| TD-20260711-02 | in_progress | Runtime capability/state taxonomy | `DBG-20260711-01`, `DBG-20260711-02`; final local review against `b752b78` | Shared runtime-selection and source-state semantics now have locally reviewed field-name and branch coverage, but fresh UAT has not confirmed every affected consumer. | 5 | Integrate the reviewed files, re-pin UAT, and run fresh startup/source-state acceptance before deciding whether the debt can exit. | Shared taxonomy has full branch coverage, all affected consumers preserve it, and accepted UAT passes. |
| TD-20260711-03 | accepted | Behavioral contract depth | `DBG-20260711-04` to `DBG-20260711-06`; four corrective review rounds and final dual-axis PASS against `b752b78` | Phrase-presence or incomplete condition/input matrices repeatedly missed broker-agnostic reconciliation, first-start state, exact metadata grammar, state-field taxonomy, and validation-order paths while the full suite remained green. | 5 | After UAT closure, implement the bounded behavior-contract matrix task in `docs/DEVELOPMENT_PLAN.md` before adding capability in the affected workflow. | High-risk behavior fixtures assert required structure, content, state/input matrices, and failure ordering rather than only keyword presence. |

`TD-20260711-03` now meets Architecture Optimization Trigger 3: the same
contract-depth cause has required multiple corrective patches within 30 days.
The planned response is a bounded test-seam improvement, not a product rewrite;
the current P1 defect and UAT remain the immediate priority.

## Review Cadence

Review this register during the weekly planning review and after every P0/P1
debug closure. Update score and evidence, remove resolved items, and record any
triggered optimization task in the development plan. Do not silently bury debt
inside a feature ticket or a debug fix.
