# Intraday Setup Scan

Use this reference when monitoring setup-level entries from the Active Market Plan.

The intraday scanner is a decision-support workflow. It can surface opportunities only inside the current `market-plan.md`, update note, watchlist, or prepared setup plan. It does not place orders or turn price alerts into buy/sell instructions.

## Inputs

Use the current day's local records:

- `market-plan.md`
- `trade-plans.csv`
- `intraday-watchlist.csv`
- `updates/YYYY-MM-DD.md` or daily market tracking notes when available
- `portfolio_snapshot.csv`, `portfolio.csv`, or current holdings data when available
- current price/chart data from IBKR or another authorized source
- current macro/news context when a plan may be affected by events

When `intraday-watchlist.csv` already contains prepared setup rows, render the
baseline scan with:

```bash
python3 plugins/trading-research-system/scripts/intraday_scan.py \
  {runtime_dir}/daily/YYYY-MM-DD/intraday-watchlist.csv \
  --date YYYY-MM-DD
```

Then layer current chart/price interpretation on top only when authorized data
is available.

If `trade-plans.csv` and `intraday-watchlist.csv` exist but are header-only,
first collect or derive setup rows from the Active Market Plan and ask the user
to confirm them as `ticker + trade_horizon + instrument` groups. After
confirmation, write user-confirmed setup JSON and populate the two CSV files
with:

```bash
python3 plugins/trading-research-system/scripts/prepare_setup_rows.py \
  --date YYYY-MM-DD \
  --setup-json /path/to/confirmed-setups.json
```

`prepare_setup_rows.py` consumes user-confirmed setup JSON only; it does not parse free-form trade ideas, read broker data, call market data, or create orders.

Before showing a visual, read `visual-trigger-policy.md`. Generate or request a
`PA Scenario Board` only when a setup is `approaching`, `triggered`,
`invalidated`, or `needs_review` and authorized chart/OHLCV data is available.
If every setup is merely `active`, `candidate`, or far from its planned zone,
keep the scan text-only and say which setup would unlock a chart.

Every scanned setup should include:

- `setup_id`
- `theme_id`
- `symbol`
- `underlying`
- `direction`
- `instrument_type`
- `analysis_timeframe`
- `trigger_timeframe`
- `setup_type`
- `key_levels`
- `trigger_zone`
- `invalidation`
- `status`

## Status Model

Use stable statuses:

- `candidate`: candidate setup, not yet actively tracked.
- `active`: confirmed in the current plan, but not close enough to require attention.
- `approaching`: price or structure is near the planned key area, but trigger-timeframe confirmation is missing.
- `triggered`: the key area is reached and the trigger timeframe shows the planned setup confirmation. This means human decision required, not an order instruction.
- `invalidated`: the setup's invalidation condition has been hit. This has highest priority and cannot auto-recover to `triggered`.
- `needs_review`: the state is unclear or unsafe for automated classification because data, plan quality, event context, timeframes, or portfolio risk need human review.
- `completed`: the trade completed, the setup expired, or the setup is archived.

## Trigger Rules

Do not mark a setup as `triggered` from price contact alone. A triggered setup needs:

1. price at the planned level, zone, or structure;
2. trigger-timeframe confirmation of the planned setup type;
3. at least medium signal-bar quality;
4. no clear conflict with the higher-timeframe background;
5. acceptable risk/reward after the trigger.

`invalidated` overrides every other status. If a setup is invalidated and a new strong pattern appears, classify it as `needs_review` or require a new setup.

## Attention Priority

Sort scan output by attention priority:

1. `invalidated`
2. `triggered`
3. `needs_review`
4. `approaching`
5. `active`
6. `candidate`
7. `completed`

Within the same status, sort by instrument urgency:

1. 0DTE QQQ/SPY options
2. short-dated or swing options
3. leveraged ETF trades
4. common stock or ETF swing trades
5. LEAP call/put trades

Attention priority means what the user should inspect first. It is not conviction ranking and not trade recommendation strength.

## Output

Produce a compact scan note:

- `setup_id`
- ticker and instrument
- status
- attention reason
- current setup read
- invalidation or stop risk
- portfolio exposure concern
- next user decision

When updating files, write current state to `market-plan.md` or `intraday-watchlist.csv` and append narrative context to `updates/YYYY-MM-DD.md`. Do not overwrite the original setup thesis silently; state the evidence for every material change.
