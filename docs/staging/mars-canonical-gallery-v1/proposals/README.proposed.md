[English](README.md) | [简体中文](README.zh-CN.md)

# 火星投研助手 (Mars Research Assistant)

An AI-native, Bayesian decision-support Skill that compresses market, macro,
policy, company, price-action, and portfolio evidence into an updateable
decision process. It does not try to predict the next market move: it updates a
prior with new evidence, compares conditional scenarios, and identifies the
next observation that would change the decision.

Version: `1.0.0`

## Install in 30 Seconds

Install the complete portable Agent Skill. The installer detects supported
coding agents and adapts the target directory.

```bash
npx skills@latest add Archerouyang/mars-research-assistant --skill mars-research-assistant -g
```

## First Run

Open a new task and say:

```text
Start today's trading research.
```

The same Skill checks runtime health and, when no private runtime exists,
enters blank first-run setup. It confirms a local runtime location and offers
optional authorized read-only data sources. It does not restore or infer a
watchlist, profile, portfolio, plan, credential, connector grant, or research
history.

## Accepted Output Examples

These screenshots are user-selected PNG exports of accepted standalone Boards.
They use dated public market data and contain no broker account,
private runtime, or private portfolio information. They are research snapshots,
not live quotes or trade instructions.

### Macro Regime Panel

![Macro Regime Panel showing rates, inflation, risk breadth, and one-month trend analysis](docs/assets/readme/macro-regime-live-2026-07-19.png)

The Macro panel connects the current liquidity regime with rates, inflation,
NDX/RUT breadth, volatility, the dollar, credit, oil, and the next material
events.

### NVDA 4H Price Action Panel

![NVDA 4H Price Action entry plan with scenarios, key levels, staged entries, and company events](docs/assets/readme/nvda-4h-pa-entry-plan.png)

The Price Action panel separates observation from action: timeframe and data
provenance, current structure, conditional paths, key levels, invalidation,
staged execution, and stock-specific event checks remain visible together.

Self-contained standalone HTML is the only primary visual artifact. Each Board
is saved with its canonical snapshot and manifest so it can be reopened and
updated after an event. PNG is saved only when the user explicitly selects a
Board for export. See
[third-party notices](THIRD_PARTY_NOTICES.md) for TradingView attribution and
Apache-2.0 licensing.

## Capabilities and Sources

| Capability | What the Skill produces | Source rule |
| --- | --- | --- |
| Weekly and daily market work | Active Market Plan changes, event priorities, and next checks | Verify current facts; show only decision-relevant deltas |
| Macro, rates, and policy | Regime posture, transmission paths, and affected plans | Prefer official primary sources; use authorized macro data for values |
| Equity and report research | Thesis, counter-thesis, claim ledger, and verification queue | Public, authorized, or user-provided research only; no paywall bypass |
| Price action | Declared timeframe, trend/range context, levels, and setup conditions | Authorized OHLCV; TradingView Lightweight Charts for canonical visuals |
| Alpha Lab input | Published champion ranks, history deltas, and uncertainty for research priority | Read-only private store; preserve model ranks and continue safely when unavailable |
| Portfolio risk | Concentration, product, theme, broker exposure, and material flags | Authorized read-only broker facts or explicit user input |
| Trade review | Post-order and post-exit context, errors, and lessons | Read-only execution facts plus user confirmation |

When the private Alpha Lab is available, the Skill reads its published champion
ranking as research priority only. It never retrains or re-ranks the model.
Alpha contracts and automation details live in the
[Alpha Lab plan](docs/ALPHA_LAB_PLAN.md).

The system is decision support. It does not promise returns, replace regulated
advice, or turn a data point into an automatic trade instruction.

## Public Skill / Private Runtime

| Public Skill | Private Runtime |
| --- | --- |
| One installable `mars-research-assistant` package with research guidance, references, scripts, blank templates, and synthetic fixtures | User-owned profile, watchlist, positions, Active Market Plan, setups, reviews, credentials, and connector grants |
| Safe to publish and upgrade | Stays outside the repository and every distribution package |
| Starts with no personal defaults | Created only after explicit local write confirmation |

Installation and upgrades never copy, infer, synchronize, or recover private
state. Broker and market integrations are optional, separately authorized, and
read-only. **No order actions:** the Skill never creates, modifies, cancels, or
submits real orders.

## Troubleshooting and Detailed Docs

| Symptom | Check |
| --- | --- |
| Skill is not discovered | Confirm the repository is reachable and the install output names exactly `mars-research-assistant`. |
| A new task starts without personal data | Expected: first run is blank until the user explicitly initializes a private runtime. |
| Broker or macro data is unavailable | Authorize the optional read-only source separately; installation does not grant connector access. |
| A selected Board cannot be exported | User-selected PNG export requires Chrome/Chromium; the standalone HTML remains the primary artifact. |

Detailed documents: [Skill contract](skills/mars-research-assistant/SKILL.md),
[standalone delivery decision](docs/adr/0011-standalone-board-only-delivery.md),
[0.3.0 module ownership](docs/adr/0010-deep-module-ownership-for-0.3.0.md),
[MVP runbook](docs/MVP_RUNBOOK.md), and
[distribution plan](docs/DISTRIBUTION_AND_README_PLAN.md).

火星投研助手 (Mars Research Assistant) is MIT licensed. Third-party components retain their own licenses.

## Proposed Canonical Research Board Gallery

Staged only. These synthetic, non-interactive captures are hash-linked to the same canonical HTML used by Codex and Claude Code.

### Instrument Research
![Synthetic instrument-research Overview; png sha256 c831db88294b](docs/assets/canonical-gallery/captures/instrument-research/overview-1200x840.png)
[Open canonical HTML](docs/assets/canonical-gallery/artifacts/instrument-research/research-brief.html) · non-interactive screenshot · synthetic fixture

### Macro Regime
![Synthetic macro-regime Overview; png sha256 871aae25936b](docs/assets/canonical-gallery/captures/macro-regime/overview-1200x840.png)
[Open canonical HTML](docs/assets/canonical-gallery/artifacts/macro-regime/research-brief.html) · non-interactive screenshot · synthetic fixture

### Portfolio Risk
![Synthetic portfolio-risk Overview; png sha256 d70b9655d1f5](docs/assets/canonical-gallery/captures/portfolio-risk/overview-1200x840.png)
[Open canonical HTML](docs/assets/canonical-gallery/artifacts/portfolio-risk/research-brief.html) · non-interactive screenshot · synthetic fixture
