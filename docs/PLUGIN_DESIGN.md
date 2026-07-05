# Trading Research Plugin Design

Status: accepted design.

This document defines the intended product shape, capability boundary, agent
interaction model, runtime state model, and development sequence for the
Dailytrades Trading Research System plugin.

The design goal is an AI-native trading research assistant: the user expresses a
trading research or operations goal in natural language, and the agent chooses
the right internal workflow, reads the necessary state and sources, verifies
current facts, and returns a concise decision-useful note.

## Design Principles

- The plugin is decision support, not an automated trading system.
- The user should not need to memorize focused skill names.
- The user should not need to manually call out every module in order; Daily Ops Orchestrator provides 主动流程引导 before focused workflows run.
- Focused skills remain as agent-internal tools, test boundaries, and development
  units.
- The public plugin must stay general. Personal strategy details belong in the
  private runtime trading profile.
- The agent should read broadly, verify aggressively, and show only what changes
  plans, risk, setup state, or user decisions.
- Broker sources are read-only. The plugin must not create, modify, cancel, or
  approve orders.
- Local runtime files are the first source of truth for discretionary context.
- Google Sheets is optional display or summary sync, not the trade-record source
  of truth.
- A persistent frontend is deferred. Generated chart artifacts are allowed when
  they help the user inspect price action.

## Current Recommended Decisions

These are recommendations for review. Accepted rows reflect decisions already
confirmed in the design discussion.

| Area | Recommended decision | Status | Why |
| --- | --- | --- | --- |
| Default UX | Natural language tasks are the default user interface | accepted | Keeps the product AI-native and avoids making users memorize skill names |
| Daily Ops Orchestrator | Add an active process guide backed by `ops-state.md` and `ticker + trade_horizon + instrument` confirmations | accepted | Lets the user say "start today" or "continue the flow" while the agent decides the next workflow |
| Focused skills | Keep as internal agent workflows, power-user shortcuts, and test boundaries | accepted | Preserves modularity without making the UX tool-menu driven |
| Public docs | README should show task prompts first and move focused skill names to an advanced section | accepted | Aligns documentation with the desired user interaction model |
| Runtime source of truth | Private runtime files own discretionary context; broker facts are read live when authorized; derived broker summaries may be saved for comparison | accepted | Avoids leaking private data and avoids stale local broker records |
| Trading profile | Public plugin ships a blank framework; concrete strategy preferences live in private `trading-profile.md` | accepted | Keeps the plugin general while supporting personal workflows |
| Automations | Trading operations automations default to draft mode and ask before runtime writes; broker access remains read-only | accepted | Keeps operations useful without becoming automated trading |
| KVN | Plugin supports KVN snapshot import, storage, query, Top10 memory, and plan usage; KVN model construction stays outside plugin scope | accepted | Lets the workflow use momentum rankings without making this plugin own the quantitative model |
| KVN model module | Future separate module owns KVN universe, factors, validation, model versions, and daily snapshots | accepted | Keeps quantitative research auditable without turning the plugin into a model lab |
| Charts | Generate chart artifacts on demand by default; allow opt-in auto-generation for high-priority setup, invalidation, or review contexts; do not build a dashboard | accepted | Keeps the plugin lightweight and Codex-native |

## Design Review Path

Review should happen in this order because later decisions depend on earlier
ones.

1. **User interaction model**: decide whether natural language tasks are the
   default UX and focused skills are internal/power-user tools.
2. **Runtime boundary**: decide what the agent may read/write locally, and what
   must remain private or external.
3. **Router contract**: decide how the agent maps user tasks into focused
   workflows and when it asks clarifying questions.
4. **Capability boundary**: confirm in-scope and out-of-scope features,
   especially broker read-only behavior and no frontend.
5. **Data-source priority**: confirm official/current/authorized source tiers and
   how low-quality leads are filtered.
6. **Automation confirmation model**: decide how much a scheduled prompt may do
   before asking the user.
7. **Development plan**: convert the accepted design into issues and
   implementation order.

The natural-language UX decision is accepted. README, router fixtures, and
future tests should be written around task intent instead of manual focused-skill
invocation.

All design gates above are accepted. Future implementation work should preserve
these decisions unless a new design review explicitly changes them.

## Product Shape

The system has four layers.

| Layer | Responsibility | Public repo? |
| --- | --- | --- |
| Codex plugin | Skills, references, scripts, templates, fixtures, docs | yes |
| Private runtime | Active Market Plan, trading profile, updates, daily artifacts, derived snapshots | no |
| External connectors | Google Drive, broker read-only sources, Longbridge macrodata, web/current sources | no |
| Automations | Recurring prompts that wake the agent and ask for confirmation before writes | config outside plugin repo |

The default interface is Codex conversation. The user asks for outcomes such as
"做下周交易计划", "盘前更新", "检查这些 setup", "读这篇研报", or "复盘这笔交易".
The agent then routes internally.

## User Interaction Model

Default UX:

- User writes a natural language task.
- Agent reads `trading-research` router guidance and private runtime state.
- Agent selects one or more focused workflows.
- Agent asks only for missing information that materially affects the output.
- Agent returns concise Chinese Markdown.

Focused skills are not the default user-facing menu. They remain available for
advanced users, debugging, tests, and direct development checks.

Example user prompts:

- "帮我做下周交易计划，先看宏观、利率、政策、新闻和当前持仓影响。"
- "盘前更新一下今天需要盯的 setup，告诉我哪些接近触发。"
- "现在 QQQ 有没有 0DTE setup，只看我计划里的场景。"
- "读这篇研报，提炼 thesis/counter-thesis，并告诉我是否影响 Active Market Plan。"
- "我刚买了 MU，带我做入场后复盘。"
- "这笔交易结束了，帮我做出场复盘和系统标签。"
- "生成今天的持仓日报，只告诉我风险暴露和需要决策的事项。"

## Agent Router Contract

The router is the main agent decision layer. It maps user intent to workflows and
keeps output concise.

| User intent | Internal workflow | Required reads | Default output |
| --- | --- | --- | --- |
| New weekly or weekend plan | Deep Active Market Plan update | runtime plan/profile, macro/rates, policy/news, event preview, momentum, portfolio risk | regime, top variables, affected holdings, setup pool, user decisions |
| Premarket or intraday update | Quick Active Market Plan update | current plan, setup pool, current tape, macro/news delta | changed variables, setup state changes, next checks |
| Multiple setup monitoring | Intraday setup scan | current setup rows, chart/price data, plan levels | attention priority, approaching/triggered/invalidated/needs_review |
| Research report or thesis source | Research report intake, then macro/equity research if needed | user-provided report or public/authorized sources | digest, claim ledger, verification queue, plan impact |
| Momentum stock discovery | KVN snapshot lookup and cross-section preparation | local KVN store, imported rankings, profile pool rules | Top10, ticker lookup, changes, candidates for research |
| Holding/risk question | Portfolio risk or position daily report | broker read-only source when authorized, runtime plan/profile | exposure, concentration, risk flags, user decisions |
| New order/fill | Post-order trade review | broker execution facts if authorized, setup/plan context | entry background, signal, confidence, risk plan |
| Closed trade | Post-exit trade review and stats when useful | broker result facts if authorized, review notes | outcome, exit quality, mistake tags, lessons |
| System performance | Trading stats | closed trade facts or approved snapshots | expectancy, setup/instrument/timeframe performance, improvement notes |

If an intent spans multiple workflows, the default order is:

1. source/report intake;
2. macro/equity verification;
3. trade plan preparation;
4. Active Market Plan deep or quick update;
5. setup scan;
6. portfolio risk;
7. trade review;
8. statistics.

### Router Precedence

When one user request can map to several workflows, use this precedence:

1. **Safety and write boundary first**: if the user asks to place, modify,
   cancel, or approve an order, refuse that action and offer decision-support
   alternatives.
2. **Source-led tasks first**: if the task starts from a report, PDF, screenshot,
   link, article, or copied research, route to report intake before plan impact.
3. **Current-state tasks second**: if the user asks "盘前", "现在", "今天",
   "盘中", or "有没有 setup", read the current Active Market Plan before doing
   new research.
4. **Broker-fact tasks third**: if the task mentions holdings, fills,
   executions, orders, PnL, or position report, use read-only broker source rules
   before asking the user for subjective context.
5. **Plan-building tasks fourth**: if the user asks for next week, weekly review,
   plan reset, setup discovery, or market outlook, run the deep plan path.
6. **System-improvement tasks last**: if the user asks about win rate,
   expectancy, setup quality, or mistake patterns, route to stats and review
   history.

### Clarifying Question Rules

The agent should ask at most one short question when a missing answer changes the
result materially. Otherwise, it should proceed with stated assumptions.

Must ask before proceeding when:

- the user requests a runtime write and the relevant write policy is not already
  confirmed;
- broker source is needed but multiple authorized sources may disagree;
- a report/source cannot be accessed and the user may have an authorized copy;
- a setup would require translating into an instrument type not enabled by the
  trading profile;
- risk exposure cannot be judged because holdings or account coverage is
  missing;
- the user asks for a trade action instead of decision support.

Proceed with disclosure when:

- a source is unavailable but enough other current sources can support a
  lower-confidence read;
- a market-data field is missing but the output can be limited to qualitative
  plan impact;
- the task is exploratory and does not write runtime state.

### Router Output Labels

Router-selected outputs should expose the workflow to the user only when useful.
Default labels:

- `本次路由`: one short phrase, such as "盘前 quick update" or "研报摄取 + 计划影响".
- `读取状态`: runtime files, broker source, web/current sources, and missing data.
- `结论`: the decision-useful answer.
- `变化`: only variables that changed the plan or risk.
- `影响`: affected holdings, candidates, setup status, or risk budget.
- `需要你决定`: user decisions or confirmations.
- `下一步`: next check or proposed write.

Do not expose internal focused-skill names as the main UX unless the user asks
for debug detail.

## Runtime State Model

Default runtime root:

```text
~/Documents/dailytrades-runtime/
```

Canonical private files:

```text
market-plan.md
trading-profile.md
updates/YYYY-MM-DD.md
daily/YYYY-MM-DD/
charts/
momentum/kvn.sqlite
```

State roles:

| Artifact | Role |
| --- | --- |
| `market-plan.md` | overwriteable current state of market regime, setup pool, risk budget, event focus |
| `trading-profile.md` | private strategy configuration: pools, instruments, timeframes, score thresholds, avoid rules |
| `updates/YYYY-MM-DD.md` | append-only rationale and change trail |
| `daily/YYYY-MM-DD/` | daily plans, watch state, review notes, generated artifacts, optional derived snapshots |
| `momentum/kvn.sqlite` | daily all-searchable KVN leaderboard history |
| broker read-only view | live source for objective positions, executions, orders, account facts |

The public repo provides templates and contracts, not private runtime data.

## Runtime Access Boundary

The runtime boundary separates public plugin assets from private trading
operations.

Runtime writes have three possible policies:

| Policy | Meaning | Best fit |
| --- | --- | --- |
| Draft-only | Agent may read and draft changes, but every runtime write needs explicit user confirmation | Highest control; best for `market-plan.md`, `trading-profile.md`, reviews, and manual strategy context |
| Confirmed source auto-write | Agent may write deterministic outputs after the input source, date, and destination are confirmed | Best for KVN snapshots, generated charts, imported fixtures, and repeatable derived artifacts |
| Never write | Agent may read or summarize, but must not mutate the source | Broker accounts, order state, public repo private data boundaries |

Recommended runtime write rules:

| Target | Agent may read? | Agent may draft? | Agent may write without confirmation? | Notes |
| --- | --- | --- | --- | --- |
| Public plugin docs/templates/scripts | yes | yes | yes during development task | Must stay general and git-managed |
| `{runtime_dir}/market-plan.md` | yes | yes | no | User should confirm plan overwrites |
| `{runtime_dir}/updates/YYYY-MM-DD.md` | yes | yes | no | Append-only rationale should still be confirmed |
| `{runtime_dir}/trading-profile.md` | yes | yes | no | Private strategy changes require explicit confirmation |
| `{runtime_dir}/daily/YYYY-MM-DD/` | yes | yes | no | Daily artifacts are private operational context |
| `{runtime_dir}/charts/` | yes | yes | no, unless generated on user request or an accepted chart automation rule | Chart artifacts may include private symbols/levels |
| `{runtime_dir}/momentum/kvn.sqlite` | yes | yes | yes for deterministic script output after source confirmation | KVN writes should disclose input source/date |
| Broker data | read-only when authorized | derived summaries only | never write broker state | No order placement, modification, cancellation, or approval |
| Google Drive or Sheets | only when explicitly authorized | summaries only | no by default | No private broker facts in public docs |

Missing runtime state should not be invented. The agent should report the gap and
ask whether to initialize, import, connect a source, or continue with a reduced
analysis.

Recommended default:

- `market-plan.md`, `updates`, `trading-profile.md`, review notes, and daily
  discretionary artifacts use **draft-only**.
- `kvn.sqlite`, generated chart HTML, and deterministic imported snapshots use
  **confirmed source auto-write** after the user has confirmed source/date/path
  for that run or recurring automation.
- Broker/account state uses **never write**.
- Public repo files are edited only during plugin development tasks and must be
  git-managed.

Accepted detail:

- `updates/YYYY-MM-DD.md` is a trading-judgment audit trail, not a mechanical
  log. It can include checked sources, changed variables, plan impact,
  rationale, pending decisions, and write summary. Because it becomes future
  agent context, append operations require user confirmation.
- Raw broker exports should not be saved by default and local files should not
  become the source of truth for objective broker facts. The agent may save
  derived broker summaries, such as position daily reports, exposure snapshots,
  missing-field lists, source/read-time disclosures, and visualization-ready
  fields, under the private runtime for comparison and later review context.
  Future reconciliation should still return to authorized read-only broker
  sources when exact holdings, executions, orders, or account facts matter.
- Chart artifacts are generated on demand by default. Opt-in chart automation may
  generate runtime chart artifacts for high-priority setup changes, invalidation
  checks, and trade reviews after trigger conditions, data source, and output
  path are confirmed. This does not create a persistent dashboard.

## Capability Boundaries

### In Scope

- AI-native synthesis and concise decision notes.
- Macro, policy, rates, liquidity, volatility, credit, and event-risk filtering.
- Longbridge `macrodata` as an optional macro/financial data source.
- KVN momentum leaderboard backed by imported/user-provided ticker snapshots and
  searchable local history. Agents read the scheduled or upstream script output;
  they do not re-rank, re-score, or replace ticker rows with themes/sectors.
- Cross-sectional candidate pool formation from momentum, industry strength,
  thesis checks, and trading profile rules.
- Authorized research report discovery and user-provided report digestion.
- Active Market Plan deep updates and quick updates.
- Setup-level plan formation and intraday status classification.
- Price-action timing with higher-timeframe environment and execution-timeframe
  trigger checks.
- Read-only broker position daily reports and portfolio risk summaries.
- Two-stage trade review: post-order context and post-exit outcome review.
- Basic trading statistics and system optimization notes.
- User-confirmed automations for development briefs and trading operations.
- Generated chart artifacts for inspection.

### Out Of Scope

- Order placement, order modification, cancellation, or approval.
- Fully automated trading.
- Guaranteed buy/sell instructions.
- Unbounded whole-market real-time scanning without a prepared plan or watchlist.
- Persistent dashboard/frontend as the first product surface.
- Google Sheets as canonical trade records.
- Paywall bypass or unauthorized report extraction.
- Tax, legal, or regulated investment advice.
- Hard-coded personal strategy defaults in the public plugin.
- KVN quantitative model construction, vendor selection, signal research, and
  backtesting. Those belong in a separate quantitative-model project or upstream
  data pipeline.

## Data Source Policy

Source priority should be explicit when confidence matters.

| Tier | Source type | Use |
| --- | --- | --- |
| S0 | Official sources: Fed, Treasury, SEC filings, company IR, exchange calendars | policy, rates, events, filings, corporate facts |
| S1 | Authorized connector data: Longbridge, IBKR, licensed market data | current positions, executions, prices, broker facts, macrodata |
| S2 | Authorized or public research: Seeking Alpha when accessible/provided, broker reports, PDFs, transcripts | thesis and counter-thesis extraction |
| S3 | Mainstream financial news and reputable aggregators | event leads and market narrative, verified before plan impact |
| S4 | Social media, Discord, screenshots, secondhand claims | leads only; never sufficient for plan changes without verification |

For policy/news filtering, keep only items that can affect tariffs, fiscal or
Treasury policy, Fed independence, rates/yields, energy/oil, sector regulation,
liquidity, or major market structure.

## Broker Source Configuration

Broker source choice should be configurable during plugin onboarding or runtime
initialization. The plugin should not hard-code one broker as the universal
default.

V1 supported broker sources:

- Longbridge skill/plugin.
- IBKR connector.

Broker source rules:

- During onboarding, ask which broker sources the user wants to enable.
- Store the user's preferred broker-source order in private runtime config or
  `trading-profile.md`, not in the public plugin repo.
- If only one supported source is enabled, use it for read-only broker facts.
- If both Longbridge and IBKR are enabled, use the configured preference.
- If no preference exists and the task requires broker facts, ask which source to
  use for that run.
- If the selected source is unavailable or unauthorized, disclose the gap and ask
  whether to use another enabled source or continue without broker facts.
- Broker access remains read-only regardless of source.

Manual CSV can remain a reduced fallback for one-off runs or fixtures, but it is
not a first-class broker integration in v1.

## Output Contract

Default user-facing output should be note-like Chinese Markdown:

- conclusion first;
- changed variables only;
- what matters vs what is noise;
- affected holdings or setup candidates;
- invalidation and confirmation checks;
- portfolio/risk constraint;
- user decision needed;
- source names or links only when they change confidence.

The agent should avoid long source dumps, calendar recitations, unexplained
internal state labels, and generic market commentary.

## Automation Boundary

There are two automation families.

| Family | Purpose | State |
| --- | --- | --- |
| Development automations | keep plugin work planned, reviewed, and reflected in public docs | repo docs |
| Trading operations automations | wake the agent for plan updates, setup checks, position reports, reviews | private runtime |

Trading operations automations may inspect state, read authorized sources, draft
updates, and ask questions. They must ask before writing files and must never
touch broker write actions.

Accepted automation default:

- Trading operations automations use **draft mode** by default.
- They may read runtime state, authorized broker data, authorized macro/market
  sources, and current web sources.
- They may generate draft `market-plan.md` changes, daily update notes, position
  reports, setup status updates, and review prompts.
- They must ask before writing trading-judgment runtime files such as
  `market-plan.md`, `updates/YYYY-MM-DD.md`, `trading-profile.md`, daily review
  notes, and discretionary setup plans.
- Deterministic derived artifacts can use confirmed-source auto-write only after
  the source, cadence, and destination have been confirmed.

## Generality And Personalization

The public plugin ships a framework. A user's concrete strategy lives in
`trading-profile.md`.

General framework concepts:

- Strategy Posture Score.
- Risk Budget Score.
- Trend Fit Score.
- Mean Reversion Fit Score.
- active pools and pool governance.
- setup-to-instrument translation.
- timeframe rules.
- crowding model.
- avoid rules and manual overrides.

Personal profile examples may exist only as private runtime files or anonymous
fixtures.

## Initial Development Plan

The development sequence should stabilize the agent interaction loop before
adding heavier data ingestion or automation. Each slice should be testable with
fixtures and should not require live broker or paid research access.

### P0: Lock The AI-Native Interaction Contract

Deliverables:

- Update README language so natural language tasks are the default UX.
- Keep focused skills documented as internal/advanced paths.
- Add router behavior fixtures for realistic prompts.
- Ensure outputs stay concise and decision-useful.

Done when:

- a new user understands they can ask goals directly;
- the router can select focused workflows without requiring manual skill names;
- README no longer implies focused skills are the primary UX.

Suggested issue slices:

1. Rewrite root/plugin README examples around natural language tasks.
2. Add router prompt fixtures for weekly plan, premarket update, report intake,
   setup scan, trade review, and position daily report.
3. Add a lightweight verifier that checks expected workflow routing labels.

### P1: Runtime And Profile Health

Deliverables:

- Add a runtime health/check command or script that verifies `market-plan.md`,
  `trading-profile.md`, updates directory, and momentum store availability.
- Make missing-state prompts explicit: initialize, import, or run without that
  source.

Done when:

- the agent can tell what state is available before running a plan update.
- Runtime health reports only status categories such as available, missing,
  stale, or unauthorized; it must not copy private runtime content into public
  repo files.

Suggested issue slices:

1. Define runtime health output contract.
2. Add a script that checks required runtime files and directories.
3. Add missing-state guidance to router and automation references.

### P1: KVN Momentum Leaderboard

KVN has two separate layers:

- the future KVN model module, documented in `docs/KVN_MODEL_PLAN.md`, which
  owns data ingestion, factor calculation, validation, and daily model-produced
  snapshots;
- the Trading Research System plugin, which consumes imported or upstream KVN
  snapshots and never re-ranks or re-scores them.

Deliverables:

- `momentum-leaderboard` focused workflow.
- `kvn.sqlite` schema and import fixture.
- Top10 default display.
- searchable ticker lookup.
- Top10 entry memory fields.

Done when:

- KVN can feed Cross-Section Candidate Pool without becoming a buy list.
- The plugin can consume KVN snapshots without owning the scoring formula.
- KVN output rows are ticker-only and preserve script-computed order.

Suggested issue slices:

1. Define KVN SQLite schema and CSV/snapshot import format.
2. Add fixture data with Top10 and ticker lookup examples.
3. Add `momentum-leaderboard` focused workflow and verifier.
4. Add daily update summary fields: new Top10 names, dropped names, consecutive
   Top10 days, recent Top10 count, last Top10 date.

### P1: Trade Plan Preparation

Deliverables:

- Formalize input reads: macro regime, financial conditions, policy/event risk,
  industry strength, company thesis, KVN, trading profile rules.
- Produce Cross-Section Candidate Pool before setup rows.
- Separate candidate idea from actionable setup.

Done when:

- a deep update can explain why a ticker is worth research, why it is not ready,
  or what confirmation is required.

Suggested issue slices:

1. Finalize Cross-Section Candidate Pool fields.
2. Connect macro/financial/policy/industry/company/KVN reads into one template.
3. Add expected fixture output showing candidate idea versus actionable setup.

### P1: Research Report Intake

Deliverables:

- Report discovery from public/authorized sources.
- User-provided report digestion.
- Claim Ledger and Verification Queue.
- Trade Plan Preparation impact.

Done when:

- reports influence candidate research only after claims are extracted and
  checked.

Suggested issue slices:

1. Forward-test on one user-provided report artifact.
2. Add source-priority and inaccessible-source behavior to fixtures.
3. Add plan-impact examples that update candidate confidence without promoting
   directly to a trade.

### P1: Position Daily Report

Deliverables:

- Broker-agnostic read-only position summary.
- Longbridge and IBKR source preference rules.
- Exposure, concentration, option/leveraged-product risk, and decision items.

Done when:

- the user can get a daily holdings/risk note without local trade-record tables.

Suggested issue slices:

1. Define broker-agnostic position daily report fixture.
2. Define exposure visualization fields.
3. Add automation prompt that asks for broker source and reports missing fields.

### P1: Intraday Setup Scan

Deliverables:

- Read existing plan/watchlist setups.
- Classify active, approaching, triggered, invalidated, needs_review, completed.
- Add attention priority and execution check requirement.

Done when:

- the scan monitors prepared plans instead of inventing unplanned trades.

Suggested issue slices:

1. Freeze setup row fields required by the scanner.
2. Add fixture scan cases: approaching, triggered, invalidated, needs_review,
   completed.
3. Implement scan script only after setup fields are stable.

### P2: Automations

Deliverables:

- Deep update prompt.
- Quick update prompt.
- Intraday monitor prompt.
- Post-market review prompt.
- Position daily report prompt.
- Development brief and progress review maintenance.

Done when:

- automations wake the correct chat, read the correct state, and ask before
  writing.

Suggested issue slices:

1. Define final automation prompts from the runtime health and router contracts.
2. Create or update Codex automations only after cadence and data-source
   permissions are confirmed.
3. Add end-of-day development progress guidance for this design document.

## Development Issue Queue

This queue converts the accepted design into small implementation slices. It
should become the basis for GitHub issues and the development task board.

| Order | Priority | Slice | Depends on | Deliverable |
| --- | --- | --- | --- | --- |
| 1 | P0 | Align README with AI-native task UX | accepted UX decision | Root README and plugin README show natural-language tasks first; focused skill names moved to advanced/internal section |
| 2 | P0 | Add router intent fixtures | accepted UX decision | Fixture prompts cover weekly plan, premarket update, setup scan, report intake, trade review, position daily report |
| 3 | P0 | Add router contract verifier | router intent fixtures | Local verifier checks that realistic prompts map to expected workflows and output labels |
| 4 | P1 | Define runtime health contract | accepted runtime boundary | Reference/template describing available, missing, stale, and unauthorized runtime states |
| 5 | P1 | Implement runtime health script | runtime health contract | Script checks plan/profile/updates/daily/momentum/broker-source availability without reading private content into public repo |
| 6 | P1 | Define KVN storage/import contract | accepted KVN scope | SQLite schema, CSV/snapshot import shape, Top10 memory fields, fixture examples |
| 7 | P1 | Add `momentum-leaderboard` workflow | KVN contract | Focused skill and verifier for Top10 display, ticker lookup, and change summary |
| 8 | P1 | Finalize Trade Plan Preparation fixture | router and runtime health | Expected output showing macro/financial/policy/industry/company/KVN/profile reads feeding Cross-Section Candidate Pool |
| 9 | P1 | Forward-test research report intake | source policy | One user-provided report fixture and one inaccessible-source behavior fixture |
| 10 | P1 | Define position daily report fixture | broker preference decision | Broker-agnostic output with exposure, concentration, missing fields, and decision items |
| 11 | P1 | Freeze setup scan row schema | Trade Plan Preparation fixture | Required fields for active/approaching/triggered/invalidated/needs_review/completed |
| 12 | P1 | Implement plan-scoped intraday scan script | setup scan schema | Script emits attention-priority setup statuses from fixture plan/watchlist rows |
| 13 | P2 | Define trading operations automation prompts | runtime health and confirmation model | Deep update, quick update, intraday monitor, post-market review, position daily report prompts |
| 14 | P2 | Add optional chart artifact attachment flow | accepted chart behavior | On-demand chart generation guidance and high-priority opt-in behavior |

Near-term development should start with slices 1-3 because they lock the
AI-native task UX and router behavior. Slices 4 and later can proceed after the
router fixtures because the runtime, automation, broker, KVN, and chart
boundaries are now accepted.

## Open Decisions

| Decision | Recommendation | Status |
| --- | --- | --- |
| Public README default UX | Natural language tasks first; focused skill names in advanced/internal section | accepted |
| Public-facing skill surface | `trading-research` as the conceptual router; focused skills remain callable but not the primary UX | accepted |
| Automation write confirmation | Trading ops automations should draft changes and wait for explicit confirmation before writing runtime files | accepted |
| Runtime health minimum | Check `market-plan.md`, `trading-profile.md`, `updates/`, daily directory, broker-source availability, and KVN store status | accepted |
| Broker preference when both are available | Ask during onboarding/runtime initialization and store enabled sources plus preference privately; v1 formally supports Longbridge skill/plugin and IBKR connector | accepted |
| KVN implementation path | Plugin consumes imported/user-provided KVN snapshots; model construction and backtesting stay outside plugin scope | accepted |
| Chart artifact behavior | Generate on demand by default; allow automatic attachment only for high-priority setup changes, invalidations, and reviews after user opts in | accepted |
