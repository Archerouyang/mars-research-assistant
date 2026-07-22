# ADR 0011: Standalone Board Only Delivery

## Status

Accepted on 2026-07-22 for Trading Research System 0.4.0.

## Context

ResearchResult supported a Codex-native fragment while Artifact Packet also
supported standalone HTML. The two paths could render different view sets and
the fragment depended on host component styles. A manually wrapped Portfolio
fragment therefore opened with browser-default controls and no longer matched
the accepted panel. Temporary paths also made useful event panels hard to find
again.

## Decision

`Validated ResearchResult -> DeliveryPacket` has one optional visual output:
`DeliveryPacket.standalone_board`.

The packet contains exactly:

- `snapshot.canonical.json`;
- `research-brief.html`;
- `artifact.manifest.json`.

The HTML is a complete, direct-open document with embedded design tokens and
component styles. Macro, Instrument, Portfolio, and Price Action keep their
purpose-specific adapters and accepted view order. The system does not emit
`inline.html`, iframe wrappers, or a second host-dependent visual.

ResearchResult adapters continue to own purpose-specific validation and
rendering. The Artifact Packet public facade owns final HTML safety, size
limits, deterministic serialization, manifest construction, and hashes.

## Consequences

- Event panels can be retained and reopened from one stable artifact path.
- Browser and Codex surfaces consume the same HTML bytes.
- `DeliveryPacket.inline_html` is removed, so this is a breaking 0.4.0 change.
- ADR 0009 remains historical but its inline delivery decision is superseded.
- PNG export remains explicit and derives from the standalone Board.
