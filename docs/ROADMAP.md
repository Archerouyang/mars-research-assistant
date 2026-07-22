# DailyTrades Roadmap

This roadmap describes the active product direction. Historical 0.1.x delivery
details remain in `docs/PROJECT_LOG.md` and the 1.0 acceptance records.

## Product Direction

DailyTrades is a high-freedom trading-research Skill with one stable
delivery boundary:

`Validated ResearchResult -> DeliveryPacket`

The model owns research judgment. Deterministic code owns safety, provenance,
privacy, data-gap handling, concise Markdown, and an optional self-contained
standalone Board.
Macro, Instrument, Portfolio, and Price Action keep purpose-specific visual
adapters behind that shared boundary.

The only distributed behavior source is `skills/trading-research-system/`.

## 0.2.0 Release Contract

- small, natural-language Skill entrypoint with progressive references;
- current primary or explicitly authorized read-only sources;
- no invented data and visible `partial`, `stale`, conflict, and source-error
  states;
- no broker write or order action;
- concise Markdown plus one self-contained standalone Board when a visual
  changes the decision;
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

## 0.3.0 Architecture Contract

Version 0.3.0 preserves the accepted 0.2.0 product behavior while assigning
four deep module owners:

- Broker-Live Data View owns known product mapping and fails closed for unknown
  look-through metadata;
- four purpose-specific Board visual adapters own their payload and rendering
  implementation behind the shared delivery seam;
- Private Runtime owns layout, preparation, health expectations, and controlled
  writes;
- Artifact Packet exposes one supported facade while registry and neutral core
  remain private implementation.

The decision is recorded in
[`ADR 0010`](adr/0010-deep-module-ownership-for-0.3.0.md). Frozen panel
structures, read-only broker behavior, private-runtime safety, ADR 0008, and ADR
0009 remained unchanged in 0.3.0. ADR 0011 later superseded the inline-delivery
portion for 0.4.0.

## 0.4.0 Standalone Delivery Contract

Version 0.4.0 removes the parallel Codex-inline delivery surface. A visual
`ResearchResult` produces one `standalone_board` packet containing canonical
snapshot bytes, self-contained HTML, and a hash-linked manifest. Macro,
Instrument, Portfolio, and Price Action preserve their accepted view structures
behind purpose-specific Board adapters. The decision is recorded in
[`ADR 0011`](adr/0011-standalone-board-only-delivery.md).

## Current Status

| Area | Status | Acceptance |
| --- | --- | --- |
| Broker-Live product knowledge | implemented | focused known/unknown and leveraged-product self-test |
| Purpose-specific Board visual adapters | implemented | four frozen view structures render in standalone HTML |
| Private Runtime ownership | implemented | temporary-runtime idempotence, health, and data-preservation self-test |
| Artifact Packet facade | implemented | three Board reference packets and immutable writes remain stable |
| ResearchResult delivery seam | implemented | focused self-test and deterministic output |
| ArtifactPacket compatibility | retained | focused compatibility self-test |
| Bayesian decision support | implemented | Skill and ResearchResult contract name prior, evidence update, posterior decision, and next check |
| Macro standalone Board | user accepted structure | direct-open inspection with real data |
| Price Action standalone Board | user accepted structure | direct-open inspection with real data |
| Portfolio Risk standalone Board | user accepted structure | direct-open inspection with authorized read-only data |
| Optional PNG export | user accepted | explicit export and visual inspection |
| Legacy code, cache, database, fixture, and test cleanup | verified candidate | cleanup ledger and repository scan passed |
| Portable Skill distribution | verified candidate | Skill gate and isolated install smoke passed |
| Public cutover | blocked on user approval | no silent publish, install, or private-state migration |

## Next Release Steps

1. Present the verified release candidate and actual standalone Boards for user
   acceptance.
2. Apply only acceptance feedback or focused safety fixes.
3. Integrate or publish only after explicit approval.

## Deferred

- automatic PNG export or artifact persistence;
- static frontend, dashboard, or hosted panel gallery;
- order execution or broker write actions;
- private runtime migration or database deletion;
- public quantitative-model ownership or agent-generated KVN reconstruction.
