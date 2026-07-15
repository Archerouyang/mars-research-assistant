# Active Market Plan

Use this reference for the core market planning loop. Weekly, daily, intraday, and post-trade work are not separate products; they are different update depths against the same active plan.

## Files

Use `runtime_dir` as the private working-memory root. Default:

```text
~/Documents/dailytrades-runtime/
```

The user or automation may override it with `TRADING_RESEARCH_RUNTIME_DIR`,
`--runtime-dir`, or the config template at `assets/templates/config.toml`.

Use:

```text
{runtime_dir}/market-plan.md
{runtime_dir}/ops-state.md
{runtime_dir}/trading-profile.md
{runtime_dir}/updates/YYYY-MM-DD.md
{runtime_dir}/daily/YYYY-MM-DD/
```

- `{runtime_dir}/market-plan.md`: overwriteable living state. It should always show the current plan.
- `{runtime_dir}/ops-state.md`: compact Daily Ops Orchestrator state. It records current stage, pending confirmations, active setup summary, and next recommended action.
- `{runtime_dir}/trading-profile.md`: private strategy profile for scoring rules, pools, ETF groups, instrument preferences, timeframe rules, crowding model, and avoid rules. Use the public template at `assets/templates/trading-profile.md`.
- `{runtime_dir}/updates/YYYY-MM-DD.md`: append-only update trail. It records what changed, why, and what to inspect next.
- `{runtime_dir}/daily/YYYY-MM-DD/`: daily records for trade plans, broker data, reviews, and statistics inputs.

Google Sheets is only a compact one-way mirror for review, filtering, and cross-device visibility. It is not the canonical source of truth.

## Update Depths

Use one loop with different depth, not separate modes:

- `deep_update`: weekend or major reset. Includes prior-week trade summary, market state, macro/rates, policy/news, event preview, optional external momentum context, setup pool refresh, and risk budget review.
- `quick_update`: weekday premarket or market-hours update. Focuses on what changed since the current plan and which setups move status or priority.
- `trigger_update`: intraday update focused on setup status, trigger zone, invalidation, execution checklist, and exposure constraints.
- `review_update`: post-order or post-exit update linking actual trade facts and review notes back to the setup.

## Setup Pool

The setup is the smallest planning unit. A setup is not just a ticker and not just a broad trade idea.

Before a new setup enters the setup pool, route research through `Trade Plan Preparation`:

1. Summarize the input reads: `Macro Regime`, `Financial Conditions`, `Policy/Event Risk`, `Industry/Sector Strength`, `Company Thesis Check`, and the read-only `Alpha Leaderboard` when available. `External Momentum Snapshot` remains a disclosed legacy fallback only.
2. Apply profile-defined strategy posture, pool, instrument, timeframe, and crowding rules.
3. Convert those reads into a `Cross-Section Candidate Pool`.
4. Promote only candidates with sufficient higher-timeframe regime, strategy bias, price structure, trigger zone, invalidation, and risk context into `candidate` or `active` setups.

The setup pool should not receive raw macro views, plain watchlist names,
unverified research claims, or momentum rankings without a prepared setup
structure. External momentum context can raise research priority, but it cannot
bypass higher-timeframe regime, price_structure, risk_context, or portfolio
checks.

Minimum promotion guidance from Cross-Section Candidate Pool to Setup Pool:

- `higher_timeframe_regime`: 4H / 1D / 1W read as uptrend, range, or downtrend;
- `strategy_bias`: long, short, neutral, or defensive bias allowed by the higher-timeframe regime;
- `setup_type`: for example pullback long, breakout pullback, range boundary, failed breakout, or resistance short;
- `price_structure`: the price-action structure that makes the candidate more than a watchlist name;
- `trigger_zone`: the area to watch, not an automatic entry;
- `invalidation`: what makes the candidate wrong or stale;
- `risk_context`: preliminary portfolio, product, event, liquidity, or concentration risk that would affect later sizing;
- `next_check`: the next inspection, usually 1H or lower execution observation or an event confirmation.

If these are missing, keep the item in Cross-Section Candidate Pool instead of promoting it into Setup Pool.

Required setup fields:

- `setup_id`
- `theme_id`
- `market_context_id`
- `symbol`
- `underlying`
- `direction`
- `trade_horizon`
- `instrument_type`
- `analysis_timeframe`
- `trigger_timeframe`
- `setup_type`
- `status`
- `trigger_zone`
- `invalidation`
- `stop_concept`
- `target_zone`
- `risk_budget`
- `evidence_needed`
- `last_updated`

For user-facing notes and Sheets mirrors, label timeframes by role:

- `analysis_timeframe` = `背景过滤时间框架`: decides whether the setup deserves attention.
- `trigger_timeframe` = `执行触发时间框架`: decides whether the setup can move to `triggered`.

Do not collapse them into one generic `条件/触发` field. For fast products such as 0DTE options, the background timeframe can qualify the setup while the execution timeframe supplies the actual signal bar.

### Ticker Trade Horizon Confirmation

Before promoting a ticker into a setup, confirm the intended
`ticker + trade_horizon + instrument` grouping. The same ticker can have several
separate setups if the user trades it differently, for example:

- `QQQ + long-term holding + ETF`;
- `QQQ + 0DTE + option`;
- `MU + medium-term swing + equity`;
- `TSM + LEAP + call`;
- `GLW + watch only + equity`.

If trade horizon is missing, do not generate concrete entry or exit triggers.
Keep the item in Cross-Section Candidate Pool or `blocked_setup` and ask the
user to confirm whether it is a long-term holding, medium-term swing,
short-term swing, intraday, 0DTE, LEAP, 2x ETF, macro allocation, or watch only
idea.

If the same market opportunity can be traded with multiple instruments, create multiple setups that share the same `theme_id` or `market_context_id`.

Use `{runtime_dir}/trading-profile.md` when choosing strategy expression, pool membership, instrument, timeframe, and risk framing. The setup pool should reflect the user's private strategy profile, not a generic default.

Example:

- `theme_id`: `qqq-risk-on-breakout`
- `setup_id`: `qqq-0dte-call-breakout-pullback`
- `setup_id`: `tqqq-daytrade-breakout-pullback`
- `setup_id`: `qqq-etf-swing-breakout-pullback`

## Setup Statuses

Use stable statuses:

- `candidate`: candidate idea, not yet actively tracked.
- `active`: confirmed in the current plan and should be updated.
- `approaching`: near the planned key area, but execution confirmation is missing.
- `triggered`: planned trigger conditions appeared and a human decision is needed.
- `invalidated`: the original plan is no longer valid.
- `needs_review`: classification is unsafe because data, context, plan quality, event risk, or portfolio risk needs human review.
- `completed`: trade completed, setup expired, or setup archived.

Do not use `triggered` as a buy/sell instruction. `triggered` means `execution_check_required`.

## Execution Check

Before a triggered setup can become an actual trade, check:

- portfolio exposure and correlated risk;
- trading profile avoid rules and instrument fit;
- day risk limit and emotional/operational constraints;
- nearby macro, earnings, policy, or auction events;
- liquidity, spread, IV, and product-specific costs;
- instrument-specific time window and trigger strictness;
- whether the setup still has acceptable risk/reward.

The plugin may surface the checklist. The user places orders manually.

## Update Rules

When updating `market-plan.md`:

1. Preserve current useful state.
2. Change only fields justified by new evidence.
3. Mark stale assumptions explicitly.
4. Move setup statuses forward or to `needs_review` when evidence is incomplete.
5. Do not resurrect `invalidated` setups automatically; create a new setup or require human review.
6. Append the update rationale to `{runtime_dir}/updates/YYYY-MM-DD.md`.

When writing update notes, keep the audit trail compact:

- update depth;
- changed market variables;
- changed setup statuses;
- changed levels;
- source/evidence;
- next inspection order.
