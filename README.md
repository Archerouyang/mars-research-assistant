[English](README.md) | [简体中文](README.zh-CN.md)

# DailyTrades: Trading Research System

An AI-native research Skill that compresses market, macro, policy, company,
price-action, and portfolio evidence into an updateable decision process.

Version: `0.1.1`

## Install in 30 Seconds

Install the complete portable Agent Skill. The installer detects supported
coding agents and adapts the target directory.

```bash
npx skills@latest add Archerouyang/dailytrades --skill trading-research-system -g
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

## Synthetic Output Gallery

Every image below is generated from an explicitly labeled synthetic fixture.
No screenshot uses a broker account, private runtime, or real user data.

### Macro Regime Panel

![Synthetic Macro Regime Panel](docs/assets/readme/macro-regime-panel.svg)

### Price Action Panel

![Synthetic TradingView Lightweight Charts price-action panel](docs/assets/readme/price-action-panel.png)

The static image is a browser capture of the same
[interactive HTML](docs/assets/readme/price-action-panel.html), rendered with
TradingView Lightweight Charts 5.2.0. The handcrafted SVG remains only as a
no-browser fallback and is not the README component image.

### Position Risk Panel

![Synthetic Position Risk Panel](docs/assets/readme/position-risk-panel.svg)

Regenerate all gallery assets with `python3 scripts/generate_readme_gallery.py`.
See [third-party notices](THIRD_PARTY_NOTICES.md) for TradingView attribution
and Apache-2.0 licensing.

## Workflow

```mermaid
flowchart TD
  subgraph PUBLIC["Public Skill"]
    A["Market, macro, policy, research, charts"] --> B["Evidence filtering and verification"]
    B --> C["Active Market Plan"]
    C --> D["Daily tracking and setup review"]
    D --> E["Portfolio risk and trade review"]
    E --> C
  end
  subgraph PRIVATE["Private Runtime"]
    R["Profile, watchlist, positions, plans, history"]
  end
  R --> C
  PUBLIC -. "never packages private state" .- PRIVATE
```

The user describes the research goal in natural language. The Skill selects
the appropriate internal workflow; newcomers do not need to memorize focused
workflow names.

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
| One installable `trading-research-system` package with workflows, references, scripts, blank templates, and synthetic fixtures | User-owned profile, watchlist, positions, Active Market Plan, setups, reviews, credentials, and connector grants |
| Safe to publish and upgrade | Stays outside the repository and every distribution package |
| Starts with no personal defaults | Created only after explicit local write confirmation |

Installation and upgrades never copy, infer, synchronize, or recover private
state. Broker and market integrations are optional, separately authorized, and
read-only. **No order actions:** the Skill never creates, modifies, cancels, or
submits real orders.

## Optional Native Plugins

The portable Agent Skill above is the primary distribution. Codex and Claude
Code native plugins are optional managed wrappers over the same public Skill;
they do not contain a second behavior source or synchronize private state.

**Codex**

```bash
codex plugin marketplace add Archerouyang/dailytrades --ref master
```

Then install `trading-research-system` from `/plugins` or the Codex Plugins UI.

**Claude Code**

```text
/plugin marketplace add Archerouyang/dailytrades
/plugin install trading-research-system@dailytrades
```

Reload or open a new task after installing or upgrading a native wrapper.

## Troubleshooting and Detailed Docs

| Symptom | Check |
| --- | --- |
| Skill is not discovered | Confirm the repository is reachable and the install output names exactly `trading-research-system`. |
| A new task starts without personal data | Expected: first run is blank until the user explicitly initializes a private runtime. |
| Broker or macro data is unavailable | Authorize the optional read-only source separately; installation does not grant connector access. |
| A chart cannot be captured | Use Chrome/Chromium for the canonical PNG; the generated SVG is a no-browser fallback only. |

Detailed documents: [Plugin usage](plugins/trading-research-system/README.md),
[workflow design](docs/PLUGIN_DESIGN.md), [MVP runbook](docs/MVP_RUNBOOK.md),
and [distribution decision](docs/adr/0007-command-first-agent-skill-distribution.md).

DailyTrades is MIT licensed. Third-party components retain their own licenses.
