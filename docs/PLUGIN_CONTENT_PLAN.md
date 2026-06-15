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
4. initialize daily local records;
5. plan setup-level trades;
6. scan prepared setups intraday;
7. reconcile read-only broker facts into canonical CSV;
8. capture post-order and post-exit reviews;
9. compute basic risk and statistics.

## Required Content Map

| Area | Required content | Current state | Next implementation use |
| --- | --- | --- | --- |
| Router skill | `trading-research` routes broad requests to focused skills | present | Keep thin; forward-test on realistic prompts. |
| Weekly plan skill | deep Active Market Plan update and next-week plan | present | Read broad sources, then emit compact regime, events, themes, and setup deltas. |
| Daily tracking skill | quick market, macro, news, setup, profile-aware instrument fit, and level update | present | Convert daily noise into changed variables, setup status changes, and next checks. |
| Intraday scan skill | setup-scoped `candidate/active/approaching/triggered/invalidated/needs_review/completed` classification | present | Drives `intraday_scan.py`; output should be attention priority, not full commentary. |
| Trade review skill | post-order and post-exit interactive review | present | Ask only fields needed for `trades.csv` and `reviews.md`; summarize lessons tightly. |
| Macro/equity skill | macro/rates filtering, thesis verification, screening | present | Read many sources, reject noise, and return ranked candidates plus invalidations. |
| Portfolio risk skill | exposure and sizing review | present | Needs canonical broker CSV fixture coverage; output should highlight only material concentration and constraint breaches. |
| Trading stats skill | closed-trade stats and system review | present | Needs closed-trade fixture rows; output should focus on actionable system changes. |
| Shared references | active plan, trading profile, broker contract, intraday scan, trade journal, risk, output rules, automation contract | present | Treat as product contract for scripts and fixtures. |
| Templates | market plan, trading profile, weekly plan, daily tracking, watchlist, trade plans, intraday watchlist, broker CSV, trades, reviews | present | Convert into sample fixture package. |
| Scripts | daily init, watchlist score, portfolio risk, trade stats, append review | present | Add intraday scan and review CSV write path next. |

## Minimum Fixture Package

Create a fixture set that can support tests and demos without live broker, Google, or market-data connectors.

Required files:

- `data/market-plan.md`: one realistic Active Market Plan with event preview, momentum leaderboard, themes, and setup pool.
- `data/trading-profile.md`: one private-style fixture profile for instrument preferences and setup translation rules.
- `data/updates/YYYY-MM-DD.md`: one deep update and one quick update note.
- `data/daily/YYYY-MM-DD/trade-plans.csv`: setup-level planned trades covering multiple instrument types.
- `data/daily/YYYY-MM-DD/intraday-watchlist.csv`: current setup statuses and next checks.
- `data/daily/YYYY-MM-DD/portfolio_snapshot.csv`: canonical account/position exposure.
- `data/daily/YYYY-MM-DD/broker_executions.csv`: read-only execution facts for at least one open trade and one closed trade.
- `data/daily/YYYY-MM-DD/broker_orders.csv`: read-only order status facts.
- `data/daily/YYYY-MM-DD/trades.csv`: post-order and post-exit rows.
- `data/daily/YYYY-MM-DD/reviews.md`: matching narrative entry and exit reviews.
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
| P1 | Trading profile translation | Candidate setups can be translated into ETF, stock, 2x ETF, LEAP, or 0DTE expressions without assuming the same tool for every idea. |
| P1 | Fixture package | The fixture files cover weekly plan, daily tracking, broker facts, review writing, and expected scan output. |
| P1 | Intraday scan script | The script reads fixture plan/watchlist rows and emits stable status plus attention priority. |
| P1 | Two-stage review writer | Post-order creates or updates open rows; post-exit completes result, R multiple, tags, and review notes. |
| P1 | Broker reconciliation view | Canonical broker CSV can be compared against trade records without touching broker write actions. |
| P2 | Portfolio risk and stats refinement | Fixture trades can produce exposure summaries and closed-trade stats. |
| P2 | Google Sheets sync | Local records mirror one-way to Sheets after row mapping is stable. |
| P2 | Chart artifacts | OHLCV fixtures can generate reviewable price-action artifacts. |
| P2 | Automations | User-confirmed schedules call existing workflows and ask before writing records. |

## Deferred

- broker write actions;
- two-way Google Sheets sync;
- persistent dashboard/frontend;
- unbounded whole-market real-time scan;
- option-flow anomaly implementation before vendor and schema are selected.

## Next Slice

Build the fixture package first, then implement `intraday_scan.py` against it. Review CSV writing should follow immediately after the scan contract is executable.
