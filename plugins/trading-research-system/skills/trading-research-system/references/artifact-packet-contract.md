# Canonical Artifact Packet Tracer

This tracer defines the public artifact-packet boundary for one synthetic
Instrument Research Overview. A validated one-Board snapshot produces exactly
three immutable files: canonical JSON, directly openable offline HTML, and a
manifest that links their identities.

Run the public synthetic fixture with:

```bash
uv run python plugins/trading-research-system/scripts/instrument_overview_artifact.py \
  plugins/trading-research-system/assets/fixtures/input/instrument-overview-tracer.json \
  --output-dir /tmp/dailytrades-instrument-overview
```

Run the same command again with the same input and output directory. It accepts
only byte-identical files; a changed artifact under the same names fails closed.

The output directory contains:

- `snapshot.canonical.json`: sorted-key canonical JSON whose `content_hash`
  identifies the snapshot excluding that field.
- `research-brief.html`: self-contained semantic Overview with no executable
  code or external reference.
- `artifact.manifest.json`: immutable hash chain for the exact JSON and HTML
  bytes, Board identity, `snapshot_contract_version`, payload and manifest
  versions, decision cutoff, privacy, Views, and presentation state.

The fixture is synthetic and sanitized. Opening the HTML does not initiate an
external request or state-changing action. The artifact is decision support,
not investment advice and not an action approval.

The tracer accepts only the Instrument payload version `1.0`. Invalid schema or
version, Board/payload mismatch, invalid content hash, unsafe diagnostics, and
public-fixture privacy sentinels fail closed with stable safe error codes.

The public hard limits are 1.5 MiB for canonical JSON, 4 MiB for HTML, and
64 KiB for the manifest. These limits are contract values, not renderer hints.
