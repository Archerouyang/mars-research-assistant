# Canonical Instrument Research Artifact Packet

The Instrument Research renderer consumes one validated snapshot and produces
exactly three immutable files: canonical JSON, directly openable offline HTML,
and a manifest that links their identities. The same snapshot drives Overview,
Price & Setup, Industry & Peers, and Catalysts & Flows.

Run the public synthetic fixture with:

```bash
uv run python plugins/trading-research-system/scripts/instrument_research_artifact.py \
  plugins/trading-research-system/assets/fixtures/input/instrument-research-complete.json \
  --output-dir /tmp/dailytrades-instrument-research
```

Run the same command again with the same input and output directory. It accepts
only byte-identical files; a changed artifact under the same names fails closed.

The output directory contains:

- `snapshot.canonical.json`: sorted-key canonical JSON whose `content_hash`
  identifies the snapshot excluding that field.
- `research-brief.html`: self-contained four-View Board. Its semantic Overview
  remains useful without JavaScript. Price & Setup progressively enhances with
  the bundled local TradingView Lightweight Charts 5.2.0 asset and performs no
  artifact-time network request.
- `artifact.manifest.json`: immutable hash chain for the exact JSON and HTML
  bytes, Board identity, `snapshot_contract_version`, payload and manifest
  versions, decision cutoff, privacy, Views, and presentation state.

The fixture corpus is synthetic and sanitized. Public fixtures are recursively
privacy-scanned across every field, including unknown extra fields. Opening the
HTML does not initiate an external request or state-changing action. The
artifact is decision support, not investment advice and not an action approval.

The public corpus covers all evidence states:

- `instrument-research-complete.json`
- `instrument-research-partial.json`
- `instrument-research-stale.json`
- `instrument-research-source-error.json`

Instrument evidence requires industry, fundamentals, events/catalysts, and
market/instrument data. A partial Board still requires complete industry and
fundamentals plus at least one usable event or market gate. Flows are
supporting-only and never increase required coverage. Price & Setup is `ready`
only when all four required gates are complete; otherwise its cross-module
research gate is `blocked`.

The subject carries an explicit `identity_status`; an unresolved identity is a
visible `source_error`, not a fabricated symbol. Every Claim Ledger row names
its `evidence_gate`, and its evidence references must come from that gate.
Flow-backed claims are limited to market-reaction evidence and cannot verify an
industry or fundamental claim. Peer, candle, and overlay observations may not
postdate the decision cutoff.

The renderer accepts only the Instrument payload version `1.0`. Invalid schema or
version, Board/payload mismatch, invalid content hash, unsafe diagnostics, and
public-fixture privacy sentinels fail closed with stable safe error codes.

The public hard limits are 1.5 MiB for canonical JSON, 4 MiB for HTML, and
64 KiB for the manifest. These limits are contract values, not renderer hints.

Local browser acceptance is reproducible with
`scripts/verify_instrument_research_browser.cjs`. It checks all four views at
1200, 700, and 320 pixels, keyboard view changes, horizontal overflow, nonblank
K-line canvases, script errors, and artifact-initiated external requests. The
script requires local Playwright and a caller-supplied generated HTML artifact;
screenshots go only to the caller's temporary output path.
