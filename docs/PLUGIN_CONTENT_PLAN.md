# Plugin Content Plan

This document defines the minimum useful content set for the Dailytrades Trading Research System plugin. It is intentionally product-facing: every item should make the local trading research loop easier to run, test, or update.

## Product Principle

This plugin is AI-native. The agent should do the heavy reading, source checking, comparison, and synthesis work, then show the user only the decision-useful result.

Default user-facing output should be compressed:

- final read, not raw research dump;
- top signals and invalidations, not every headline;
- setup status and next action, not long narrative;
- evidence links or source names only where they change confidence;
- appendices only when the user asks for detail or audit trail.

The local files may store richer context for reproducibility, but interactive responses should stay brief enough for a trader to act on during planning or market hours.

## Goal

Make the plugin usable for the first local workflow:

1. maintain one overwriteable Active Market Plan;
2. append compact update notes;
3. apply private trading profile rules for instrument selection;
4. find or ingest research reports and reduce them to claim ledgers, verification queues, and plan-preparation impact;
5. compute or read a daily KVN momentum leaderboard that defaults to Top10 display while keeping all liquid symbols searchable;
6. prepare trade plans from macro, financial conditions, policy/event risk, KVN momentum, industry strength, and company thesis checks;
7. initialize daily local records;
8. plan setup-level trades;
9. scan prepared setups intraday;
10. read broker facts through a broker-live runtime view;
11. generate position daily reports with exposure/risk visualization fields;
12. capture post-order and post-exit review context;
13. compute basic risk and statistics snapshots.

## Required Content Map

| Area | Required content | Current state | Next implementation use |
| --- | --- | --- | --- |
| Router skill | `trading-research` routes broad requests to focused skills | present | Keep thin; forward-test on realistic prompts. |
| Weekly plan skill | deep Active Market Plan update and next-week plan | present | Read broad sources, then emit compact regime, events, trade plan preparation, cross-section candidates, themes, and setup deltas. |
| Daily tracking skill | quick market, macro, news, setup, profile-aware instrument fit, and level update | present | Convert daily noise into changed variables, setup status changes, and next checks. |
| Intraday scan skill | setup-scoped `candidate/active/approaching/triggered/invalidated/needs_review/completed` classification | present | Drives `intraday_scan.py`; output should be attention priority, not full commentary. |
| Trade review skill | post-order and post-exit interactive review | present | Ask only fields needed for review context; objective facts should come from broker-live sources when authorized. |
| Research report intake skill | public/authorized report discovery and user-provided report digestion | present | Produce `Research Report Digest`, `Claim Ledger`, `Verification Queue`, and Trade Plan Preparation impact before macro/equity research consumes report views. |
| Macro/equity skill | macro/rates filtering, thesis verification, screening | present | Read many sources, including Longbridge `macrodata` when available, reject noise, and return Trade Plan Preparation inputs plus Cross-Section Candidate Pool candidates. |
| Momentum leaderboard skill | daily KVN momentum leaderboard display and query | missing | Add a focused `momentum-leaderboard` skill that reads `{runtime_dir}/momentum/kvn.sqlite`, shows Top10 by default, queries any ticker, and summarizes Top10 changes. |
| Portfolio risk skill | exposure, sizing, and position daily report review | present | Needs broker-live fixture coverage; output should highlight only material concentration and constraint breaches. |
| Trading stats skill | closed-trade stats and system review | present | Needs closed-trade fixture rows; output should focus on actionable system changes. |
| Shared references | active plan, trading profile, broker-live contract, intraday scan, trade review context, risk, output rules, automation contract | present | Treat as product contract for scripts and fixtures. |
| Templates | market plan, trading profile, weekly plan, daily tracking, watchlist, trade plans, intraday watchlist, broker views, report snapshots, reviews | present | Make plan-preparation and position daily report output executable before building scan fixtures. |
| Scripts | daily init, watchlist score, portfolio risk, trade stats, append review | present | Add `kvn_leaderboard.py` and contract checks before building heavier intraday scan logic. |

## Minimum Fixture Package

Create a fixture set that can support tests and demos without live broker, Google, or market-data connectors.

Required files:

- `data/market-plan.md`: one realistic Active Market Plan with event preview, Trade Plan Preparation input reads, Cross-Section Candidate Pool, themes, and setup pool.
- `data/trading-profile.md`: one private-style fixture profile for instrument preferences and setup translation rules.
- `data/updates/YYYY-MM-DD.md`: one deep update and one quick update note.
- `data/daily/YYYY-MM-DD/trade-plans.csv`: setup-level planned trades covering multiple instrument types.
- `data/daily/YYYY-MM-DD/intraday-watchlist.csv`: current setup statuses and next checks.
- `data/daily/YYYY-MM-DD/portfolio_snapshot.csv`: fixture account/position exposure matching the broker-live runtime view.
- `data/daily/YYYY-MM-DD/broker_executions.csv`: fixture execution facts for testing only.
- `data/daily/YYYY-MM-DD/broker_orders.csv`: fixture order status facts for testing only.
- `data/daily/YYYY-MM-DD/position-daily-report.md`: expected concise holdings/risk report output.
- `data/daily/YYYY-MM-DD/reviews.md`: matching review-context examples.
- `data/fixtures/expected/trade-plan-preparation.md`: expected plan-preparation output showing input reads, cross-section candidates, and which candidates can become `candidate setup`.
- `data/fixtures/expected/kvn-leaderboard.md`: expected Top10 display plus one ticker lookup using a fixture SQLite or CSV snapshot.
- `data/fixtures/expected/intraday-scan.md`: expected scanner output, including `approaching`, `triggered`, `invalidated`, and `needs_review`.

Coverage requirements:

- one LEAP call or put setup;
- one 2x or 3x leveraged ETF setup;
- one ETF or stock swing setup;
- one 0DTE QQQ or SPY option setup;
- one setup that is invalidated before trigger;
- one setup that requires human review because data, event risk, or portfolio exposure is incomplete.

## Product Priorities

| Priority | Capability | Done when |
| --- | --- | --- |
| P0 | AI-native synthesis contract | Skills consistently read broadly, filter aggressively, and return concise decision notes instead of source dumps. |
| P0 | Active Market Plan current state and update trail | A deep update can overwrite `data/market-plan.md` and append `data/updates/YYYY-MM-DD.md` with clear rationale. |
| P1 | Trade plan preparation contract | Macro, financial conditions, policy/event risk, industry strength, and company thesis checks produce input reads and a Cross-Section Candidate Pool before setup rows are created. |
| P1 | KVN momentum leaderboard contract | A daily local script can store all liquid universe KVN scores and the skill can show Top10, query any ticker, and expose Top10 entry memory without turning the list into buy/sell advice. |
| P1 | Research report intake contract | Report discovery and user-provided report digestion produce concise, source-prioritized, verifiable claim ledgers instead of long summaries or direct setup calls. |
| P1 | Trading profile translation | Candidate setups can be translated into ETF, stock, 2x ETF, LEAP, or 0DTE expressions without assuming the same tool for every idea. |
| P1 | Fixture package | The fixture files first cover trade plan preparation, then daily tracking, broker-live facts, position daily report output, review context, and expected scan output. |
| P1 | Intraday scan script | The script reads fixture plan/watchlist rows and emits stable status plus attention priority after setup pool fields are stable. |
| P1 | Broker-live position daily report | Authorized broker facts can produce a concise holdings/risk report and visualization fields without touching broker write actions. |
| P1 | Two-stage review context | Post-order and post-exit flows capture plan linkage, signal context, confidence, mistake tags, and lessons without requiring a local trade-record table. |
| P2 | Portfolio risk and stats refinement | Fixture trades can produce exposure summaries and closed-trade stats. |
| P2 | Google Sheets summary display | Optional non-sensitive summary mirror after report outputs are stable. |
| P2 | Chart artifacts | OHLCV fixtures can generate reviewable price-action artifacts. |
| P2 | Automations | User-confirmed schedules call existing workflows and ask before writing records. |

## Deferred

- broker write actions;
- two-way Google Sheets sync;
- persistent dashboard/frontend;
- unbounded whole-market real-time scan;
- option-flow anomaly implementation before vendor and schema are selected.

## Next Slice

Stabilize the analysis-first path before more record/sync work: define the `momentum-leaderboard` skill contract, KVN field schema, SQLite storage contract, fixture output, and verification script. Then update Trade Plan Preparation fixtures so macro/rates, policy, KVN momentum, industry strength, and company thesis checks jointly feed the Cross-Section Candidate Pool. Implement `intraday_scan.py` only after setup pool fields are stable.
