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

## Rolling Price Action Update

Use this contract when the user asks for PA, 盘面分析, point updates, 加仓/减仓
levels, or a refresh of a prior chart read.

Read `visual-trigger-policy.md` before deciding whether the rolling update
should stay text-only or show a `PA Scenario Board`. Use the board when the user
directly asks for a chart, when 关键点位接近, or when scenario paths, support /
resistance, EMA context, add/TP zones, and invalidation are easier to inspect
visually than in a table.

When authorized or user-provided OHLCV JSON is available, use
`price_action_rollforward.py` to generate the baseline rolling PA note before
adding judgement. The script is local-only: it does not fetch market data, read
broker accounts, or create orders.

Before giving new levels, first look for previous analysis in:

1. current `market-plan.md` setup rows and holding plans;
2. latest `updates/YYYY-MM-DD.md` entries;
3. today's `daily/YYYY-MM-DD/` notes, watchlist, and chart artifacts;
4. user-provided prior analysis in the active chat.

If no prior analysis is available, say: `上次分析对照: 未找到可用记录，本次作为基准分析`.

Every rolling PA update must include:

- `主分析时间框架`: the higher timeframe used to judge structure, usually
  `4H`, `1D`, or `1W`.
- `辅助时间框架`: the lower timeframe used only to refine execution observation
  or near-term confirmation, usually `1H` or below.
- `上次分析对照`: what changed versus the prior read and which prior levels are
  still valid.
- `走势强弱参考点位`: levels or zones that separate strong continuation,
  repair/reclaim, neutral/range, weakness, and invalidation. Mark whether each
  level is `支撑/压力`, and state the `点位所属时间框架`.
- `加仓/减仓/暂停区`: add zones, TP/rebalance zones, and pause/review zones
  matched to the user's holding horizon. Long-term ETF holdings should discuss
  add and TP/rebalance, not ordinary tactical stop-loss exits.
- `成本/买入记录`: if holdings or prior buys are available, use them to decide
  whether a level is a good add zone, TP/rebalance zone, or just a risk-control
  zone. Do not treat a low-cost core position the same as high-cost chase lots.
- `比例式加减仓`: use qualitative or proportional sizing such as `少量`,
  `中等`, `较大`, `1/10`, `1/5`, or `1/3`. Do not bind the plan to exact share
  counts unless the user explicitly asks.
- `本周事件映射`: macro, rates, policy, earnings, and industry events that can
  validate or invalidate the level read.

Do not mix timeframe roles. The main timeframe decides the background; the
auxiliary timeframe can only refine execution observation or short-term
confirmation. If different tickers need different main timeframes, state that
explicitly ticker by ticker.

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
