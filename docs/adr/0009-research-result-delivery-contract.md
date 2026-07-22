# ADR 0009: ResearchResult delivery contract

## Status

Accepted for Trading Research System 0.2.0. The inline-delivery portion was
superseded by ADR 0011 in 0.4.0.

## Context

The 0.1.x Skill distributes behavior across routing prose, workflow references,
output templates, fixtures, and wording-based verifiers. This creates a large
model context while still failing to guarantee stable user-facing output. It
also makes obsolete compatibility code, caches, database paths, and tests hard
to remove because behavior ownership is unclear.

## Decision

Trading Research System 0.2.0 has one chat-delivery seam:

`Validated ResearchResult -> DeliveryPacket`

The model owns intent interpretation, source and tool selection, analysis, and
synthesis. A deterministic validator owns safety, provenance, data-gap, privacy,
and schema invariants. Deterministic renderers own concise Markdown and optional
chat-inline HTML.

Macro, Instrument, Portfolio, and Price Action remain purpose-specific visual
adapters behind the shared seam. The existing public Artifact Packet seam
continues to own immutable canonical Board artifacts and is not replaced by the
chat-delivery contract.

Chat-inline HTML is a native Codex fragment: compact literal markup, local
interaction, theme-aware styles, and no iframe or embedded standalone Board.
Artifact Packet HTML may be validated or reused as a data contract, but it must
not be wrapped and promoted as the conversational visualization.

The migration is replace-not-layer. Superseded prompt rules, compatibility
paths, generated caches, database-backed legacy features, fixtures, and tests
are removed when they have no supported 0.2.0 caller or public compatibility
obligation. Private runtime databases are never deleted automatically.

## Consequences

- The canonical Skill entrypoint becomes small and high freedom.
- Stable output comes from schemas and renderers, not fixed prompt wording.
- Tests concentrate at one external seam and active safety interfaces.
- Visual acceptance is primarily manual using real inline artifacts.
- 0.1.x prose output compatibility is intentionally not preserved.
- The plugin version advances to 0.2.0.
