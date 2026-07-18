# Canonical Research Artifact Packets

The canonical Macro Regime Board uses the same immutable packet seam through
`scripts/macro_regime_board_artifact.py`: one validated `macro_regime` snapshot
produces canonical JSON, directly openable offline HTML, and a manifest. Its
purpose-specific renderer owns Overview, Rates & Liquidity, Inflation & Growth,
Cross-Asset Impact, and Event Scenarios. It requires a fresh plan context and
never supplies a generic regime label when that gate fails. The four committed
Macro fixtures are synthetic and privacy-safe: `complete`, `partial`, `stale`,
and `source_error`.

Macro has its own payload version constant (`1.0`). A complete, partial, or
stale `plan_context` structurally names the active plan identity, applicable
horizon and timestamped session, current posture, constraints, assumptions, and
decision rules; the session date must match the decision cutoff. An unavailable
plan uses empty structured plan fields plus the explicit `Plan context
unavailable` state. Its rendered Board retains views and evidence coverage, but
does not expose payload posture/consequences, plan effects, exposure plan rules
or impacts, or scenario posture consequences. The artifact-packet builder loads
the bundled ECharts source and passes it to the pure Macro renderer; the
renderer does not access the filesystem.

Every Macro cascade and family evidence row identifies its source alias and
reference, priority, freshness status, and as-of timestamp. Actual, forecast,
media, and thesis provenance therefore remains auditable at the decision row.

This canonical entrypoint deliberately coexists with
`scripts/macro_regime_artifact.py`, the legacy static SVG mini-panel generator.
The SVG path is not a fallback, is not included in a Macro packet manifest, and
is not changed by the canonical Board flow. Public SVG cutover remains separate.

For focused local browser acceptance, generate a packet from the complete Macro
fixture and run `scripts/verify_macro_regime_browser.py` with a local
Chrome/Chromium executable. It checks all five views at 1200, 700, and 320
pixels with zero external requests, selected controls, nonblank SVG chart,
responsive layout, and a semantic no-JavaScript Overview.

## Instrument Research Packet

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

Local browser acceptance uses a caller-supplied Chrome or Chromium executable:

```bash
export BROWSER_BIN=/path/to/chrome-or-chromium
OUTPUT_DIR="$(mktemp -d)"
uv run --frozen python skills/trading-research-system/scripts/instrument_research_artifact.py \
  skills/trading-research-system/assets/fixtures/input/instrument-research-complete.json \
  --output-dir "$OUTPUT_DIR"
uv run --frozen python scripts/verify_instrument_research_browser.py \
  --html "$OUTPUT_DIR/research-brief.html" \
  --browser "$BROWSER_BIN" \
  --screenshot-dir "$OUTPUT_DIR/screenshots"
```

It checks all four views at 1200, 700, and 320 pixels, keyboard view changes,
horizontal overflow, nonblank K-line canvases, script errors, and
artifact-initiated external requests. The script uses the repository-locked
Playwright dependency; screenshots go only to the caller's temporary output
path. The repository-wide mandatory browser gate is delivered separately by
the visual acceptance ticket; this command is the focused local acceptance for
the Instrument vertical slice.

## Staged Cross-Host Gallery

`scripts/stage_canonical_gallery.py` validates the exact twelve-snapshot public
corpus: three Boards times `complete`, `partial`, `stale`, and `source_error`.
Only complete snapshots are captured. The approved permanent capture matrix is:

- Instrument Research: Overview and Price & Setup;
- Macro Regime: Overview and Cross-Asset Impact;
- Portfolio Risk: Overview and Stress Tests;
- each approved View at 1200 by 840 and 700 by 840, for twelve PNGs total.

The staging manifest records the canonical JSON, artifact manifest, exact HTML,
PNG, documentation-proposal, size, and timing identities. Codex exact-byte
copy, Claude Code local-open, and GitHub static-reference records all point to
the same per-Board HTML path and SHA-256. PNG metadata also records Board, View,
and synthetic-fixture identity. A replaced PNG, edited manifest hash, stale HTML
link, invalid dimensions, missing file, or over-budget artifact fails closed.

Generation requires a caller-supplied local Chrome or Chromium and an absent
output directory. It builds in a fresh sibling temporary directory, verifies
the complete hash chain, then publishes the staging directory with one atomic
rename:

```bash
uv run --frozen python scripts/stage_canonical_gallery.py \
  --browser /path/to/chrome-or-chromium \
  --output-dir docs/staging/canonical-gallery-v1

uv run --frozen python scripts/stage_canonical_gallery.py \
  --verify-only \
  --output-dir docs/staging/canonical-gallery-v1
```

The staged English/Chinese README and detailed visual document are proposals.
This workflow does not edit the active root READMEs, `docs/assets/readme`, or
legacy SVG files and records `public_cutover=not_performed`. Public switching,
full browser/privacy/distribution matrices, and real Codex inline smoke remain
separate acceptance and cutover tickets.
