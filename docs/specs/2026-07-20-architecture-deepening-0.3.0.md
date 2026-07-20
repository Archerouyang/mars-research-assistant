# Trading Research System 0.3.0 Architecture Deepening Spec

Status: implementation complete; final Standards/Spec review pending.

Baseline: `dev@ab07e2a81aed13132734d06ad6a4797688589db6`

## Objective

Deepen four existing modules without changing the product's accepted research
behavior:

1. centralize Broker-Live Data View product knowledge;
2. make the four chat visual adapters real purpose-specific modules;
3. centralize Private Runtime layout, preparation, and health expectations;
4. narrow the Artifact Packet facade to the supported 0.3.0 interface.

The release candidate version is `0.3.0`. This is an internal architecture
release, not a public `master` cutover.

## Product Invariants

- The system remains Bayesian decision support, not a prediction engine.
- Broker and runtime operations remain read-only unless the user gives separate
  explicit authorization; this work adds no order capability.
- Private runtime state, broker data, credentials, and user-generated artifacts
  remain outside the public repository.
- The accepted Macro, Price Action, and Portfolio inline structures remain
  visually and behaviorally stable. Architecture work must not redesign them.
- ResearchResult and Artifact Packet remain independent seams under ADR 0009.
- Artifact Packet retains ADR 0008 ownership of canonical immutable Boards.
- Unknown or incomplete product metadata fails closed and is visibly disclosed;
  no underlying, leverage, theme, or exposure is invented.
- Private runtime databases and user files are never automatically deleted.

## Workstream 1: Broker-Live Data View Product Knowledge

### Problem

Symbol normalization, product type, underlying mapping, leverage multiple,
direction, and theme derivation are repeated across Longbridge, IBKR, snapshot
repair, Portfolio Panel, and position reporting. Lists have already drifted.

### Target depth

One domain module owns product knowledge and normalized row invariants. Source
adapters own only source translation. Portfolio and reporting callers consume
the normalized view rather than carrying private product lists.

### Acceptance

- One module is the canonical owner of product mapping and derived metadata.
- Longbridge, IBKR, snapshot repair, Portfolio Panel, and position reporting do
  not maintain conflicting product lists.
- Ordinary equity, leveraged ETF, inverse ETF, unknown symbol, and the current
  KORU/TSMX/MVLL cases have focused behavior checks.
- Unknown metadata remains explicit and does not receive invented look-through.
- No broker write or account mutation path is added.

## Workstream 2: Purpose-Specific Chat Visual Adapters

### Problem

ResearchResult currently knows multiple visual payload shapes while one large
inline rendering module owns Macro, Instrument, Portfolio, and Price Action
implementation details.

### Target depth

Each purpose-specific visual adapter owns its validation, normalization, and
rendering implementation. ResearchResult knows only the shared chat visual
interface and DeliveryPacket invariants.

### Acceptance

- Macro, Instrument, Portfolio, and Price Action are separate adapter modules.
- ResearchResult no longer branches on their internal payload representations.
- Accepted fixture outputs preserve structure, interactions, disclosure, and
  compact native-fragment behavior.
- Inline output remains iframe-free, deterministic, and within the existing
  size limits.
- A change to one visual adapter does not require editing another adapter.

## Workstream 3: Private Runtime Layout And Preparation

### Problem

Bootstrap, daily initialization, preparation, and health checks independently
encode directory and template inventories. This leaves overlapping commands and
stale expectations, including obsolete database paths.

### Target depth

One Private Runtime module owns layout inventory, preparation planning, health
expectations, and controlled write semantics. CLI files are thin adapters.

### Acceptance

- Runtime layout and required-file knowledge have one canonical owner.
- Bootstrap, daily preparation, and health derive from that owner.
- Overlapping CLI entrypoints are either reduced to distinct adapters or
  removed when they have no supported caller.
- Obsolete public cache/database expectations are removed.
- Existing private runtime data is never deleted automatically.
- A temporary-runtime smoke proves idempotent preparation and honest health.

## Workstream 4: Artifact Packet Facade

### Problem

The facade mixes supported generic operations, Board aliases, and 0.1.x
pass-throughs; Canonical Gallery also reaches into core implementation.

### Target depth

Supported callers cross one narrow facade. Static registry and neutral core
remain private implementation. Unused compatibility aliases are deleted only
after repository caller evidence confirms no current obligation.

### Acceptance

- Canonical Gallery depends on the facade, not neutral core implementation.
- Unsupported and uncalled 0.1.x pass-throughs are removed.
- The supported Artifact Packet CLI and three registered Boards remain stable.
- Reference Artifact Packet bytes, content identity, manifests, privacy checks,
  and immutable-write behavior do not change.
- ADR 0008 is reinforced rather than reopened.

## Sequence And Integration

1. Record baseline behavior and caller inventory.
2. Implement Broker-Live Data View product knowledge.
3. Implement purpose-specific chat visual adapters.
4. Implement Private Runtime layout and preparation.
5. Narrow Artifact Packet facade.
6. Update version/docs, run aggregate focused verification, and perform final
   Standards and Spec review.

Each workstream lands as a bounded commit. Later workstreams rebase on the
accepted prior workstream; overlapping files are not edited in parallel.

## Verification Scope

Use the minimum useful automated checks:

- one focused behavior check per changed module interface;
- one narrow openability or temporary-runtime smoke where applicable;
- `git diff --check` for every bounded commit;
- one final `scripts/verify-skill.sh` run after integration;
- final `/code-review` against this spec and the pinned baseline.

Do not run broad screenshot matrices, exhaustive browser suites, obsolete 0.1.x
compatibility suites, or repeated full-repository verification. User-facing
visual acceptance remains manual if any rendered output changes unexpectedly.

## Version And Delivery

- Candidate version: `0.3.0`.
- Development branch: `codex/skill-v2-0.2.0` until the bounded refactor is
  complete; branch naming is historical and does not define release version.
- Integration target: remote `dev` only after final review and user approval.
- Public `master` release remains a separate explicit decision.

## Out Of Scope

- New trading strategies, forecasting logic, quant models, or order actions.
- Redesign of frozen Macro, Price Action, or Portfolio panels.
- Native Plugin wrappers, plugin caches, marketplaces, or optional plugins.
- A universal source adapter spanning broker, macrodata, and news.
- Automatic migration or deletion of private runtime state.
