# ADR 0010: Deep module ownership for 0.3.0

> Superseded by ADR 0012 through ADR 0015 for the stateless Skill direction.

## Status

Accepted for Mars Research Assistant 0.3.0.

## Context

The 0.2.0 delivery contract stabilized user-facing research output, but several
implementations still exposed more knowledge than their interfaces justified:

- broker adapters and portfolio callers repeated product knowledge;
- ResearchResult knew purpose-specific visual payload shapes;
- runtime commands independently encoded layout and health expectations;
- the Artifact Packet facade retained uncalled compatibility entries while
  Canonical Gallery imported neutral core implementation directly.

These are locality and ownership problems, not requests for new product
behavior. The accepted Macro, Price Action, and Portfolio inline structures
must remain stable.

## Decision

Mars Research Assistant 0.3.0 assigns four deep module owners:

1. Broker-Live Data View product knowledge owns known product identity,
   underlying, direction, leverage, and theme facts. Source adapters only map
   source records. Unknown products fail closed.
2. The chat visual seam dispatches to separate Macro, Instrument, Portfolio,
   and Price Action adapters. Each adapter owns its validation, normalization,
   and rendering implementation. ResearchResult owns only delivery invariants.
3. Private Runtime owns layout inventory, preparation plans, health
   expectations, and controlled write policy. Runtime commands remain thin
   adapters and never delete private data automatically.
4. Artifact Packet exposes one supported facade. Static registry and neutral
   core remain private implementation, while uncalled 0.1.x pass-throughs are
   removed.

ResearchResult and Artifact Packet remain independent seams under ADR 0009.
Artifact Packet canonical bytes and immutable behavior remain governed by ADR
0008.

## Consequences

- Product mapping changes have one locality and one focused test surface.
- A purpose-specific visual can change without exposing its payload to
  ResearchResult or another visual adapter.
- Runtime inventory cannot drift independently between preparation and health.
- Canonical Gallery no longer bypasses the Artifact Packet facade.
- New products must be added explicitly; unknown products do not receive
  inferred look-through metadata.
- The release advances to 0.3.0 while preserving the accepted visual product
  experience and read-only safety boundary.
