# Visual Trigger Policy

Use this reference when deciding whether a trading-research answer should show a
chat-first visual artifact, stay text-only, or ask for more data first.

The goal is not to make every answer visual. Visuals appear only when they
compress a decision: strategy posture, key level proximity, setup state change,
or portfolio risk.

## Default Rules

- Default display mode is transient chat output under `.scratch/visual-artifacts`.
- Durable save is opt-in only. Ask before writing chart artifacts, manifests, or
  private runtime chart records.
- Use authorized OHLCV, authorized macro/market-condition data, user-provided
  chart data, or fixtures. If current data is missing, say why the visual was
  skipped.
- No broker write actions. Visuals are decision support and never an order
  instruction.
- A chart must state its source, data timestamp, and whether it is live,
  delayed, prior-close, fixture, or user-provided.

## 视觉触发矩阵

| Workflow | Default visual | Trigger | Text-only when |
| --- | --- | --- | --- |
| Daily Ops startup | Macro Regime Mini-Panel | `macro-panel.json` is available and the answer discusses strategy posture, rates pressure, risk-on/risk-off, or financial conditions | macro panel is missing/stale or the answer is only a runtime setup prompt |
| Weekly plan | Macro Regime Mini-Panel | Weekly plan includes macro/rates/financial-condition reads that can change strategy posture, risk budget, or add/TP/pause decisions | macro values were not read; output is only an event calendar draft |
| Daily quick update | Macro Regime Mini-Panel | 10Y, 30Y, VIX, DXY, HYG/LQD, oil, gold, or liquidity crosses or approaches a threshold | no actual macro values were read |
| Rolling PA / 盘面分析 | PA Scenario Board | 用户直接要求图表, rolling PA analysis, or key levels are hard to inspect in text | no authorized OHLCV/chart data is available |
| Intraday setup scan | PA Scenario Board | setup state becomes `approaching`, `triggered`, `invalidated`, or `needs_review` and chart data is available | all setups are far from key levels or the scan is a status-only fixture run |
| Position daily report | Position Risk Visual | `portfolio_snapshot.csv` shows concentration, leveraged ETF exposure, broker/account imbalance, cash constraint, or theme crowding | holdings are unavailable or no risk changed |
| Trade review | PA Scenario Board | post-order or post-exit review depends on signal K, failed follow-through, exit timing, or chart context | review is only capturing text rationale and no chart data is available |

## Visual Types

### Macro Regime Mini-Panel

Use `macro_regime_artifact.py` when macro/rates values can change portfolio
posture. Inputs should come from `macro-panel.json` or an equivalent authorized
macro panel.

Show it when the answer needs to compare:

- 10Y and 30Y pressure;
- VIX or volatility state;
- HYG/LQD or credit appetite;
- DXY / USD pressure;
- oil, gold, liquidity, or defensive-asset confirmation;
- NDX/RUT, SOXX/SPY, XLK/SPY, or other user-approved regime ratios.

If the macro panel is missing, say: `未生成宏观图：macro-panel.json 缺失/过期，
本次只能文字说明数据缺口。`

### PA Scenario Board

Use `chart_artifact.py` now, and a future richer scenario renderer when
available, for symbol-level price action reads. The board should show:

- main and auxiliary timeframe;
- current price, 20/50/200 EMA when available;
- support, resistance, midpoint, gaps, trigger zone, invalidation, add zone,
  and TP/rebalance zone;
- `bull path`, `base path`, and `bear path` only as illustrative scenarios, not
  forecasts;
- a compact `MAGNET / PRICE / DIST / ROLE` style table;
- 3-5 read bullets that explain what would confirm or invalidate the setup.

Trigger it when the user asks for a chart, when 关键点位接近, or when PA levels
are easier to compare visually than in text.

### Position Risk Visual

Use position visuals when `portfolio_snapshot.csv` or an authorized broker view
shows a risk decision rather than a static holding list.

Preferred visuals:

- allocation by symbol;
- theme/sector exposure;
- instrument/product exposure;
- leveraged ETF and option expiry risk;
- broker/account exposure;
- cash, margin, and buying-power bands.

Do not display private account identifiers, raw execution details, or raw broker
exports in public repo files.

## Do Not Trigger

Do not generate a visual when:

- the answer is a plain authorization/setup question;
- the user asks for a quick one-line status;
- no actual macro, price, OHLCV, or portfolio values were read;
- the only available data is a stale fixture and the user expected live context;
- the visual would contain more raw data than decision-useful synthesis;
- generating it would require saving private data without confirmation.

In these cases, include a short line explaining why no chart appears and what
data would unlock it.
