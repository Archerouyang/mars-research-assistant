# DailyTrades Roadmap

This roadmap describes the active product direction. Historical 0.1.x delivery
details remain in `docs/PROJECT_LOG.md` and the 1.0 acceptance records.

## Product Direction

DailyTrades is a high-freedom trading-research Skill with one stable chat
delivery boundary:

`Validated ResearchResult -> DeliveryPacket`

The model owns research judgment. Deterministic code owns safety, provenance,
privacy, data-gap handling, concise Markdown, and optional chat-inline HTML.
Macro, Instrument, Portfolio, and Price Action keep purpose-specific visual
adapters behind that shared boundary.

The canonical behavior source is `skills/trading-research-system/`. Native
plugin wrappers are generated with `scripts/sync_native_plugin.py`.

## 0.2.0 Release Contract

- small, natural-language Skill entrypoint with progressive references;
- current primary or explicitly authorized read-only sources;
- no invented data and visible `partial`, `stale`, conflict, and source-error
  states;
- no broker write or order action;
- concise Markdown plus real chat-inline HTML when a visual changes the
  decision;
- Bayesian decision support that updates a prior with current evidence instead
  of presenting market research as prediction;
- frozen Macro, Portfolio Risk, and Price Action panel structures accepted
  through manual inspection;
- user-selected PNG export only, with no automatic save, frontend, or hosting;
- retained immutable ArtifactPacket behavior for canonical public artifacts;
- no mutable legacy KVN store, legacy trade importer, generated cache, or
  prompt-wording regression suite in the public package.

The architectural source of truth is
[`ADR 0009`](adr/0009-research-result-delivery-contract.md). The smallest
release check is documented in [`MVP_RUNBOOK.md`](MVP_RUNBOOK.md).

## Current Status

| Area | Status | Acceptance |
| --- | --- | --- |
| ResearchResult delivery seam | implemented | focused self-test and deterministic output |
| ArtifactPacket compatibility | retained | focused compatibility self-test |
| Bayesian decision support | implemented | Skill and ResearchResult contract name prior, evidence update, posterior decision, and next check |
| Macro inline panel | user accepted | manual inline inspection with real data |
| Price Action inline panel | user accepted | manual inline inspection with real data |
| Portfolio Risk inline panel | user accepted | manual inline inspection with authorized read-only data |
| Optional PNG export | user accepted | explicit export and visual inspection |
| Legacy code, cache, database, fixture, and test cleanup | verified candidate | cleanup ledger and repository scan passed |
| Portable/native distribution | verified candidate | sync, plugin gate, isolated install smoke passed |
| Public cutover | blocked on user approval | no silent publish, install, or private-state migration |

## Next Release Steps

1. Present the verified release candidate and actual inline artifacts for user
   acceptance.
2. Apply only acceptance feedback or focused safety fixes.
3. Integrate or publish only after explicit approval.

## Deferred

- automatic PNG export or artifact persistence;
- static frontend, dashboard, or hosted panel gallery;
- order execution or broker write actions;
- private runtime migration or database deletion;
- public quantitative-model ownership or agent-generated KVN reconstruction.
