# Canonical research artifact packets

The research-Board visual system will use immutable snapshot-driven artifact
packets. This ADR supersedes only the renderer, artifact-identity, and fallback
clauses of [ADR 0002](0002-chart-artifacts-not-dashboard.md).

## Decision

- One versioned snapshot represents exactly one Board and one canonical HTML
  artifact.
- The shared envelope and Board payload version independently. Unknown major
  versions, Board/payload mismatch, invalid content identity, and public-fixture
  privacy violations fail closed.
- Builders own normalization, source registration, freshness evaluation,
  evidence state, and privacy-safe diagnostics. Renderers consume the validated
  snapshot and perform no reads.
- Canonical JSON uses stable serialization and a content hash. Exact HTML bytes
  have a separate SHA-256 hash. An immutable manifest records the chain,
  Board identity, decision cutoff, privacy, Views, and presentation state.
- The HTML is directly openable and semantically useful without executable code.
  It contains no external request or state-changing action surface.
- Evidence state and presentation state are independent. A presentation failure
  cannot relabel missing, stale, partial, or complete evidence.

## Consequences

- The first implementation is a synthetic Instrument Research Overview tracer.
  It runs beside existing visual artifacts and does not cut over public
  documentation, Gallery assets, or legacy SVG behavior.
- Public fixtures remain synthetic and privacy-scanned. Private state and user
  history remain outside this repository.
- Artifact opening remains passive. This preserves ADR 0002's artifact-not-
  dashboard, transient-by-default, and no-live-read decisions.
- Additional Board renderers may share the envelope and brief shell, but they
  keep payload schema and analytical content independently versioned.
