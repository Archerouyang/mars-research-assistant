# Trade Journal Schema

Use this reference for trade plans, review context, compatibility trade-record files, and system statistics.

The schema is informed by the user's historical Google Sheet `2026交易记录`. Current product direction is broker-live for objective broker facts; `trades.csv` and legacy Sheet import remain compatibility tools, fixtures, or user-approved snapshot paths rather than the default source of truth.

## Principles

- Active Market Plan, review context, and derived snapshots are local artifacts.
- Objective broker facts should come from authorized broker-live reads when available.
- Google Sheets is not a trade-record layer; do not silently merge Google Sheets edits back into local records.
- One row equals one smallest statistically measurable unit.
- Split partial fills into multiple rows and link them with `trade_id`.
- A trade can be reviewed in two stages: post-order captures entry context, and post-exit captures outcome quality, exit review, realized R when available, and lesson.
- Broker order/trade facts may prefill objective execution fields, but discretionary fields still require interactive review.
- Preserve raw review text, but extract structured fields for statistics.

## Daily Directory

Use:

```text
{runtime_dir}/daily/YYYY-MM-DD/
```

Recommended files:

- `daily-market-tracking.md`
- `portfolio_snapshot.csv`
- `broker_executions.csv`
- `broker_orders.csv`
- `watchlist.csv`
- `trade-plans.csv`
- `intraday-watchlist.csv`
- `trades.csv` only for compatibility snapshots or user-approved local statistics inputs
- `reviews.md`
- `research-notes.md`
- `portfolio.csv`

The current Active Market Plan should live at `{runtime_dir}/market-plan.md`. Append update trails to `{runtime_dir}/updates/YYYY-MM-DD.md`. Deep update notes can use `assets/templates/weekly-plan.md`.

Default `runtime_dir` is `~/Documents/dailytrades-runtime`. It can be overridden with `TRADING_RESEARCH_RUNTIME_DIR` or script-level `--runtime-dir`.

Create this structure with:

```bash
python3 scripts/init_daily.py --date YYYY-MM-DD
```

## Trade Plans

Required planning fields:

- `date`
- `trade_id`
- `setup_id`
- `theme_id`
- `status`
- `ticker`
- `underlying`
- `direction`
- `instrument_type`
- `strategy_type`
- `analysis_timeframe`
- `trigger_timeframe`
- `setup_type`
- `entry_trigger`
- `trigger_zone`
- `invalidation`
- `stop_price`
- `target_1`
- `target_2`
- `ema_context`
- `price_action_context`
- `options_context`
- `macro_context`
- `risk_per_trade`
- `max_position_size`
- `time_stop`
- `notes`

## Review Context

The default post-order and post-exit artifact is a readable review section in
`reviews.md`, written only after user confirmation. It can include broker-live
fact IDs, plan linkage, entry context, signal bar, confidence, exit result,
mistake tag, lesson, and next rule without creating `trades.csv`.

Use:

```bash
python3 scripts/write_trade_review_context.py \
  --date YYYY-MM-DD \
  --stage post-order \
  --trade-id TRADE_ID \
  --fields-json /path/to/review-context-fields.json \
  --review-file /path/to/review.md
```

Use `--stage post-exit` after the trade closes.

## Compatibility Actual Trades

Compatibility execution fields:

- `trade_id`
- `parent_trade_id`
- `setup_id`
- `theme_id`
- `status`
- `entry_date`
- `exit_date`
- `symbol`
- `underlying`
- `direction`
- `trade_type`
- `product`
- `instrument_type`
- `analysis_timeframe`
- `trigger_timeframe`
- `setup_tag`
- `signal_quality`
- `confidence`
- `entry_price`
- `stop_price`
- `target_price`
- `quantity`
- `cost`
- `fees`
- `pnl`
- `risk_amount`
- `planned_R`
- `realized_R`
- `outcome`
- `mistake_tag`
- `setup_review`
- `entry_review`
- `exit_review`
- `lesson`
- `review_raw`
- `chart_link`
- `currency`
- `broker`
- `account_id`
- `execution_id`

Review context should normally be filled through interactive trade review intake, not from memory in one freeform paragraph. Use `references/interactive-trade-review.md` when asking the user to complete missing fields.

Compatibility path: after the user explicitly asks to write a local trade-record snapshot, write the structured row and narrative review with:

```bash
python3 scripts/update_trade_record.py \
  --date YYYY-MM-DD \
  --stage post-order \
  --trade-id TRADE_ID \
  --fields-json /path/to/fields.json \
  --review-file /path/to/review.md
```

Use `--stage post-exit` to update the same `trade_id` after close. The `fields-json` object must use canonical `trades.csv` column names.

For legacy imports from older Sheets such as an `active` tab that lacks `quantity`, `fees`, or `risk_amount`, pass `--allow-unknown-execution-fields` so those missing execution fields are written as `unknown`. Do not use this flag for fresh post-order review when the user can still provide or confirm the execution facts.

To migrate a CSV export of a legacy `active` tab, use `import_legacy_active_csv.py`. It reads the old `active` headers, writes canonical `trades.csv` rows, appends `reviews.md`, and uses the legacy unknown-execution-field mode only for rows missing `quantity`, `fees`, or `risk_amount`.

If a legacy row has review text but no `盈亏`, treat it as settled but not counted: write `status=not_counted` and `outcome=not_counted` so it is preserved in local records but excluded from `trade_stats.py` closed-trade statistics.

Post-order intake should fill the fields known at entry time:

- `status`
- `entry_date`
- `symbol`
- `underlying`
- `direction`
- `trade_type`
- `product`
- `instrument_type`
- `analysis_timeframe`
- `trigger_timeframe`
- `setup_tag`
- `signal_quality`
- `confidence`
- `entry_price`
- `stop_price`
- `target_price`
- `quantity`
- `cost`
- `fees`
- `risk_amount`
- `planned_R`
- `setup_review`
- `entry_review`
- `review_raw`

Post-exit intake should update the same row with:

- `status`
- `exit_date`
- `pnl`
- `realized_R`
- `outcome`
- `mistake_tag`
- `exit_review`
- `lesson`
- `review_raw`

## R-Multiple

Use:

```text
risk_amount = abs(entry_price - stop_price) * quantity
realized_R = pnl / risk_amount
```

For options, adjust for contract multiplier, premium paid, spread width, and max loss. If exact risk cannot be computed, mark `risk_amount` as unknown and do not include the trade in R statistics until corrected.

## Outcome Labels

Use stable labels:

- `win`
- `loss`
- `breakeven`
- `scratch`
- `open`
- `invalidated_before_entry`
- `missed`

## Mistake Tags

Start with:

- `early_entry`
- `late_entry`
- `chased_breakout`
- `ignored_invalidation`
- `poor_exit`
- `oversized`
- `wrong_timeframe`
- `no_follow_through`
- `range_middle_entry`
- `news_or_event_risk`
- `none`

## Instrument Types

Initial enum:

- `stock_common`
- `stock_high_momentum`
- `etf_common`
- `sector_etf`
- `leveraged_etf_2x`
- `leveraged_etf_3x`
- `leap_call`
- `leap_put`
- `swing_option_call`
- `swing_option_put`
- `qqq_0dte_call`
- `qqq_0dte_put`
- `spy_0dte_call`
- `spy_0dte_put`
- `hedge_put`
- `earnings_option`
- `other`

## Statistics

Minimum useful statistics:

- total PnL
- win rate
- average R
- expectancy
- max drawdown
- setup performance
- instrument performance
- timeframe performance
- mistake-tag frequency
- confidence calibration

Compatibility statistics can still use a user-approved local `trades.csv`
snapshot or a broker-history-derived export. Use:

```bash
python3 scripts/trade_stats.py ~/Documents/dailytrades-runtime/daily/YYYY-MM-DD/trades.csv
python3 scripts/trade_stats.py ~/Documents/dailytrades-runtime/daily/YYYY-MM-DD/trades.csv --group-by instrument_type
python3 scripts/write_trade_review_context.py --date YYYY-MM-DD --stage post-order --trade-id TRADE_ID --fields-json /path/to/review-context-fields.json --review-file /path/to/review.md
python3 scripts/update_trade_record.py --date YYYY-MM-DD --stage post-order --trade-id TRADE_ID --fields-json /path/to/fields.json --review-file /path/to/review.md
python3 scripts/import_legacy_active_csv.py /path/to/active.csv --runtime-dir ~/Documents/dailytrades-runtime
```
