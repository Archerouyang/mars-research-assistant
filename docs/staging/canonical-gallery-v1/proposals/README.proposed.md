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

## Proposed Canonical Research Board Gallery

Staged only. These synthetic, non-interactive captures are hash-linked to the same canonical HTML used by Codex and Claude Code.

### Instrument Research
![Synthetic instrument-research Overview; png sha256 b0b472b23ddb](docs/assets/canonical-gallery/captures/instrument-research/overview-1200x840.png)
[Open canonical HTML](docs/assets/canonical-gallery/artifacts/instrument-research/research-brief.html) · non-interactive screenshot · synthetic fixture

### Macro Regime
![Synthetic macro-regime Overview; png sha256 d009c0a070c9](docs/assets/canonical-gallery/captures/macro-regime/overview-1200x840.png)
[Open canonical HTML](docs/assets/canonical-gallery/artifacts/macro-regime/research-brief.html) · non-interactive screenshot · synthetic fixture

### Portfolio Risk
![Synthetic portfolio-risk Overview; png sha256 918b5197b5ee](docs/assets/canonical-gallery/captures/portfolio-risk/overview-1200x840.png)
[Open canonical HTML](docs/assets/canonical-gallery/artifacts/portfolio-risk/research-brief.html) · non-interactive screenshot · synthetic fixture

## Workflow

```mermaid
flowchart TB
  GOAL(["Natural-language research goal"])

  subgraph PUBLIC["PUBLIC SKILL · RESEARCH LOOP"]
    direction TB
    subgraph DISCOVER["01 · BUILD THE VIEW"]
      direction LR
      ROUTE{"Route intent"} --> RESEARCH["Research<br/>macro · equity · reports"]
      RESEARCH --> VERIFY["Verify<br/>claims · sources"]
    end
    subgraph OPERATE["02 · OPERATE THE PLAN"]
      direction LR
      PLAN(["Active Market Plan"]) --> TRACK["Track<br/>setups · levels"]
      TRACK --> REVIEW["Review<br/>risk · trades"]
    end
    VERIFY --> PLAN
    REVIEW -. "learn" .-> PLAN
  end

  subgraph PRIVATE["PRIVATE RUNTIME · USER OWNED"]
    direction LR
    RUNTIME[("Profile · watchlist · positions · history")]
  end

  GOAL --> ROUTE
  PRIVATE -. "local context only" .-> ROUTE
  REVIEW --> RESULT(["Decision brief · next check"])

  classDef terminal fill:#1f2328,stroke:#1f2328,color:#ffffff,stroke-width:1.5px
  classDef gate fill:#fff8c5,stroke:#9a6700,color:#1f2328,stroke-width:1.5px
  classDef step fill:#ffffff,stroke:#57606a,color:#1f2328,stroke-width:1.5px
  classDef plan fill:#dafbe1,stroke:#1a7f37,color:#1f2328,stroke-width:2px
  classDef runtime fill:#f6f8fa,stroke:#8c959f,color:#57606a,stroke-width:1.5px
  class GOAL,RESULT terminal
  class ROUTE gate
  class RESEARCH,VERIFY,TRACK,REVIEW step
  class PLAN plan
  class RUNTIME runtime
  style PUBLIC fill:#f6f8fa,stroke:#d0d7de,stroke-width:1.5px
  style DISCOVER fill:#ffffff,stroke:#d8dee4,stroke-width:1px
  style OPERATE fill:#ffffff,stroke:#d8dee4,stroke-width:1px
  style PRIVATE fill:#ffffff,stroke:#8c959f,stroke-width:1.5px,stroke-dasharray:5 5
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

## Troubleshooting and Detailed Docs

| Symptom | Check |
| --- | --- |
| Skill is not discovered | Confirm the repository is reachable and the install output names exactly `trading-research-system`. |
| A new task starts without personal data | Expected: first run is blank until the user explicitly initializes a private runtime. |
| Broker or macro data is unavailable | Authorize the optional read-only source separately; installation does not grant connector access. |
| A chart cannot be captured | Use Chrome/Chromium for the canonical PNG; the generated SVG is a no-browser fallback only. |

Detailed documents: [Skill contract](skills/trading-research-system/SKILL.md),
[workflow design](docs/PLUGIN_DESIGN.md), [MVP runbook](docs/MVP_RUNBOOK.md),
and [distribution decision](docs/adr/0007-command-first-agent-skill-distribution.md).

DailyTrades is MIT licensed. Third-party components retain their own licenses.
