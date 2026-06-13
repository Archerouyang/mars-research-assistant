# Price Action Timing

Use high-level Al Brooks-style price action language. Do not treat patterns as deterministic signals.

## First Classification

Before timing, classify the market:

1. Strong trend
2. Weak trend
3. Trading range
4. Breakout attempt
5. Failed breakout
6. Reversal attempt

Then identify the trade type:

- trend continuation
- pullback entry
- breakout entry
- failed breakout reversal
- range scalp
- major reversal

## Key Concepts

- Trend: higher highs/lows or lower highs/lows with follow-through.
- Trading range: repeated failed breakouts and mean reversion.
- Breakout: move beyond a meaningful range, trendline, or prior high/low.
- Failed breakout: breakout lacks follow-through and returns into the range.
- Pullback: pause against the trend; second entries can be higher quality than first attempts.
- Reversal: requires exhaustion, failed continuation, strong reversal bar, and adequate risk/reward.
- Measured move: estimate from range height, prior swing, or breakout leg.

## Timing Checklist

Every setup needs:

1. Timeframe.
2. Market state.
3. Trade type.
4. Entry trigger.
5. Stop location tied to logic invalidation.
6. First target and optional second target.
7. What failure looks like after entry.
8. Whether the setup fits the user's time horizon and portfolio.

## Intraday Trigger Confirmation

For plan-scoped intraday setup scans, do not mark a plan as `triggered` from price contact alone. A triggered setup needs all default confirmation checks:

1. Price reaches the planned key level, zone, or structure.
2. The execution timeframe shows the planned setup type.
3. The signal bar is at least medium quality for that setup.
4. The setup is not clearly against the higher-timeframe background.
5. The post-trigger entry still has acceptable risk/reward.

If price is near the level but execution-timeframe confirmation is missing, use `approaching`. If the plan's invalidation condition is hit, use `invalidated` before considering any new setup. If data, plan fields, timeframes, news context, or portfolio risk make the state unclear, use `needs_review`.

## Instrument Strictness

Adjust trigger strictness by `instrument_type`:

- `qqq_0dte_call`, `qqq_0dte_put`, `spy_0dte_call`, `spy_0dte_put`: strictest. Require clear execution-timeframe confirmation, clean invalidation, and no vague signal bars.
- `leveraged_etf_2x`, `leveraged_etf_3x`: strict. Confirm trend structure, 20/50 EMA context, and risk before treating a setup as triggered.
- `stock_common`, `stock_high_momentum`, `etf_common`, `sector_etf`, `swing_option_call`, `swing_option_put`: balanced. Require planned setup confirmation and higher-timeframe alignment, but allow normal swing-trade noise.
- `leap_call`, `leap_put`: slower confirmation. Weight daily/weekly background more heavily than exact intraday prints, while preserving the planned invalidation condition.

## Warnings

- Do not buy in the middle of a trading range unless the trade is explicitly a scalp with tight risk.
- Do not chase late breakouts without follow-through or a clear stop.
- Do not short strong trends only because price looks high.
- Do not call a reversal before price action confirms failed continuation.
- For stale or missing chart data, ask for the ticker, timeframe, and current chart or browse for current data.
