# Trading Research System 0.2.0

This native wrapper is generated from the canonical portable Skill at:

```text
skills/trading-research-system/
```

Do not maintain behavior separately under `plugins/`. Run:

```bash
python3 scripts/sync_native_plugin.py
```

## Product Contract

The model may choose the shortest useful research path. Stable delivery comes
from one validated boundary:

```text
ResearchResult -> DeliveryPacket
```

The system is Bayesian decision support, not a market-prediction engine. It
starts from an explicit prior, updates that view with current evidence, and
returns a conditional decision plus the next observation that would change it.

Every delivery contains:

- canonical ResearchResult JSON;
- concise Markdown with a stable section order;
- optional Codex chat-inline interactive HTML.

Macro, Instrument, Portfolio, and Price Action use purpose-specific visual
adapters. Canonical standalone Board artifacts remain available through the
separate ArtifactPacket API.

## Hard Boundaries

- decision support only;
- no order creation, modification, cancellation, or implied approval;
- no invented evidence or silent replacement of missing data;
- public fixtures contain no private runtime, broker, account, credential, or
  user-chart data;
- opened artifacts are offline and read-only.

## Verification

```bash
bash scripts/verify-plugin.sh
```

The default gate is intentionally narrow. Visual acceptance uses one real
inline artifact reviewed by the user; screenshot matrices and legacy runtime
test suites are not part of the default workflow.
