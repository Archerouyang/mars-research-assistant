# Intraday Setup Scan

Use this reference when monitoring current-day trade plans, weekly review plan watchlist ideas, and planned setups.

The intraday scanner is a decision-support workflow. It can surface opportunities only inside the current weekly market review plan, daily tracking note, watchlist, or prepared trade plans. It does not place orders or turn price alerts into buy/sell instructions.

## Inputs

Use the current day's local records:

- `trade-plans.csv`
- `intraday-watchlist.csv`
- weekly market review plan and daily market tracking notes when available
- `portfolio.csv` or current holdings data when available
- current price/chart data from IBKR or another authorized source
- current macro/news context when a plan may be affected by events

Every scanned plan should include:

- `trade_id`
- `ticker`
- `underlying`
- `direction`
- `instrument_type`
- `market_analysis_timeframes`
- `execution_timeframe`
- `setup_type`
- `key_levels`
- `entry_trigger`
- `invalidation_condition`
- `current_status`

## Status Model

Use stable statuses:

- `waiting`: the plan is live, but price and structure are not close enough to require attention.
- `approaching`: price or structure is near the planned key area, but execution-timeframe confirmation is missing.
- `triggered`: the key area is reached and the execution timeframe shows the planned setup confirmation.
- `invalidated`: the plan's invalidation condition has been hit. This has highest priority and cannot auto-recover to `triggered`.
- `needs_review`: the state is unclear or unsafe for automated classification because data, plan quality, event context, timeframes, or portfolio risk need human review.

## Trigger Rules

Do not mark a plan as `triggered` from price contact alone. A triggered setup needs:

1. price at the planned level, zone, or structure;
2. execution-timeframe confirmation of the planned setup type;
3. at least medium signal-bar quality;
4. no clear conflict with the higher-timeframe background;
5. acceptable risk/reward after the trigger.

`invalidated` overrides every other status. If a plan is invalidated and a new strong setup appears, classify it as `needs_review` or require a new plan.

## Attention Priority

Sort scan output by attention priority:

1. `invalidated`
2. `triggered`
3. `needs_review`
4. `approaching`
5. `waiting`

Within the same status, sort by instrument urgency:

1. 0DTE QQQ/SPY options
2. short-dated or swing options
3. leveraged ETF trades
4. common stock or ETF swing trades
5. LEAP call/put trades

Attention priority means what the user should inspect first. It is not conviction ranking and not trade recommendation strength.

## Output

Produce a compact scan note:

- `trade_id`
- ticker and instrument
- status
- attention reason
- current setup read
- invalidation or stop risk
- portfolio exposure concern
- next user decision

When updating files, write structured state to `intraday-watchlist.csv` and narrative context to the daily review or intraday note. Do not overwrite the original plan thesis silently.
