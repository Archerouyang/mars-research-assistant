# ResearchResult Contract

Use this reference only when creating a stable research delivery packet.

The model may research and reason freely. Before delivery, express the answer as
one `ResearchResult` with:

- `result_kind`: `operations`, `macro`, `instrument`, `price_action`, or
  `report`;
- `as_of` and `decision`;
- `key_evidence`, `risks`, `scenarios`, `next_checks`, and visible `data_gaps`;
- compact `sources` with priority and timestamp;
- optional `visual` using the adapter matching the result kind.

The result is a Bayesian decision snapshot, not a prediction record. Use the
existing fields rather than adding ceremonial schema:

- `decision` states the current posterior judgment and the reasonable action;
- `key_evidence` contains observations that preserve or change the prior;
- `risks` and counter-theses contain evidence that could reverse the update;
- `scenarios` are conditional paths with observable triggers, not forecasts;
- `next_checks` identify the next evidence that would update the decision.

When the prior is material to understanding the change, state it briefly in the
decision or evidence. Do not invent numerical probabilities when the evidence
does not support calibration.

Every key-evidence row requires an `evidence_type` (`fact`, `inference`,
`thesis`, or `counter_thesis`), at least one valid `source_ref`, and its own
`as_of`. Any non-complete evidence requires a visible `data_gaps` row. The
delivery Markdown preserves this classification and provenance.

Run `scripts/research_result.py` when deterministic Markdown or a standalone
Board is needed. Macro and Instrument visuals accept their existing canonical
Board snapshot, and Price Action accepts the existing OHLCV chart payload. In
unscoped Daily Ops, Macro always requires this delivery path: `visual` cannot
be omitted or replaced with `visualize`, copied HTML, or a new renderer.

When `visual` is present, `DeliveryPacket.standalone_board` contains exactly one
self-contained packet: `snapshot.canonical.json`, `research-brief.html`, and
`artifact.manifest.json`. The HTML preserves the accepted purpose-specific view
structure and includes its own tokens and component styles. It must not depend
on Codex host CSS, wrap another page in an iframe, or emit `inline.html`.

Do not invent fields to fill the contract. Use empty lists when a section has no
decision-useful content and use `data_gaps` when required evidence is absent.

The validator rejects broker/order action keys, imperative order language,
private sentinels in public fixtures, and oversized results or rendered
artifacts. `DeliveryPacket.diagnostics` contains only safe data-gap labels and
states; it must not contain raw broker responses or credentials.
