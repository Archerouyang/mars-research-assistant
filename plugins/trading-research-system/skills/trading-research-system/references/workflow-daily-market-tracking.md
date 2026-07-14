---
name: daily-market-tracking
description: Quick-update the Active Market Plan during weekday premarket or intraday sessions with market tape, macro/rates, policy, news, event, momentum, setup status, and level changes. Use for daily market read, premarket prep, intraday plan updates, point/level updates, current tape analysis, and dynamic tracking of planned setup opportunities.
---

# Daily Market Tracking

Use this skill for `quick_update` or light `trigger_update` work against the same Active Market Plan. The goal is to answer what changed, which setup statuses or levels changed, and what the user should inspect next.

## Daily Ops First-Start Guard

If the user says the exact generic start phrase `开始今天的交易研究`, route through
the Daily Ops Orchestrator and its fixed startup health block before using this
skill. Do not let Daily Market Tracking replace the first-start status and
confirmation structure; run it only after Daily Ops routes to a quick update.

This is an AI-native workflow. Read current tape, macro/rates, policy/news, event calendar, momentum, and existing setup files, then return only what changed, which setup statuses moved, and what the user should inspect next.

## Rolling PA Setup-Key Gate

For the exact acceptance request `做 DRAM/SOXX/QQQ 的滚动盘面分析`, and for any
rolling PA, 盘面分析, point-update, or add/reduce-level request, apply this gate
before prior-level, OHLCV, or deep-research work. Bare tickers trigger this
lookup; they are not automatically unresolved.

Resolve each ticker's complete `ticker + trade_horizon + instrument` setup key
in this bounded order:

1. Use an explicit confirmation in the current request or current chat.
2. Otherwise, read only `ticker`, `trade_horizon`, and `instrument_type` from
   structured setup records in today's formal runtime
   `daily/YYYY-MM-DD/trade-plans.csv`, then
   `daily/YYYY-MM-DD/intraday-watchlist.csv`; map `instrument_type` to the
   setup key's `instrument` component.
3. An Active Plan Markdown row is a final fallback only when it explicitly
   carries all three canonical fields: `ticker`, `trade_horizon`, and
   `instrument_type`. Do not infer a missing horizon from `Symbol` or
   `Instrument` labels.

Apply this order independently for each ticker. Fall through only when a
higher-priority source has no row for that ticker. Once a source has rows, one
unique complete key wins and lower-priority rows do not override it; incomplete
or conflicting rows stay unresolved and do not fall through.

Never use a repo fixture, bundled example, or stale example plan as current plan
state. The formal runtime structured-record lookup is allowed only to resolve
the setup key; do not use it as prior PA evidence. Do not read prior levels or
OHLCV, and do not begin deep research, until key resolution completes.

If exactly one unambiguous complete key exists for every requested ticker,
continue the normal rolling PA workflow. If any ticker has zero, incomplete, or
multiple conflicting keys, return only a concise `watch-only` / reduced-scope
summary, ask one focused confirmation question covering the unresolved
`trade_horizon + instrument`, and stop before the workflow below.

When the request supplies ticker names only, label each as an unconfirmed watch
ticker and assert no structure, direction, or risk role. Do not add theme,
volatility, breadth, index-anchor, or instrument classifications that the input
did not provide.

While resolution is incomplete, do not output concrete levels, triggers,
invalidations, sizing, or instrument-specific risk advice, including
support/resistance and add/trim/pause zones.

### Unresolved Setup Key + Formal Runtime Unavailable

Apply this exact five-section, exact-two-action special case only when the
current request is exactly `做 DRAM/SOXX/QQQ 的滚动盘面分析` and its setup keys
remain unresolved and formal runtime is unavailable. Render exactly these
sections in order:

1. `运行状态`
2. `当前范围`
3. `Watch-only 摘要`
4. `可执行下一步`
5. `聚焦确认问题`

Primary status: `待复核`; keep `watch-only` only as a secondary qualifier. Under
`可执行下一步`, render exactly these two actions:

- 初始化今日运行包：仅在用户明确授权 runtime 写入后执行。
- 生成盘中观察清单：先确认 DRAM、SOXX、QQQ 各自完整 setup key，并在用户明确授权 runtime 写入后再生成。

Ask exactly one focused confirmation question. This special case overrides the
general Runtime Guidance Contract choice of 2-4 executable next actions only for
this state. Outside this state, keep the general Runtime Guidance Contract
unchanged. For every other ticker request, use the generic dynamic Runtime
Guidance Contract, adapt ticker names and actions, and never inherit
DRAM/SOXX/QQQ from this acceptance-only block.

## Workflow

1. Load the active `market-plan.md`, or ask for the current plan state if it is unavailable.
2. Read relevant shared references:
   - Active plan model: `./active-market-plan.md`.
   - Runtime health: `./runtime-health.md`.
   - Trading profile strategy rules, pools, timeframes, and instrument preferences: `./trading-profile.md`.
   - Macro/rates context: `./macro-policy-filter.md`.
   - Macro data source contract: `./macro-data-source-contract.md`.
   - Visual trigger policy: `./visual-trigger-policy.md`.
   - optional external quantitative momentum snapshots when already configured
     or explicitly provided by the user.
   - Price action/timeframes: `./price-action-timing.md`.
   - Intraday statuses: `./intraday-setup-scan.md`.
   - Portfolio risk: `./portfolio-risk.md`.
   - Trade journal schema: `./trade-journal.md`.
3. Use current data for:
   - index and sector tape;
   - rates/yields and macro variables;
   - fiscal/Treasury/Fed/policy headlines;
   - high-impact news and earnings;
   - major events in the current week and next-week preview window;
   - optional external quantitative momentum snapshot changes only when the
     source is already configured or explicitly provided;
   - prices, key levels, and chart context.
   For macro/rates and financial-condition reads, first report `宏观数据来源状态`.
   Use Longbridge macrodata for actual macro values when available, use
   IBKR market data for price/OHLCV transmission, and official source fallback
   for S0 facts or fallback values. Then include `实际宏观指标读数` with current values,
   5D/20D change when available, thresholds, strategy posture impact, source,
   and `数据时间戳`. Do not claim macro analysis if no actual macro values were read.
   If `macro-panel.json` or equivalent authorized macro values are available
   and the update discusses strategy posture, rates pressure, risk-on/risk-off,
   or financial conditions, apply `visual-trigger-policy.md` and show or request
   a `Macro Regime Mini-Panel`. If no macro chart is shown, say whether the
   reason is missing/stale macro values or that the update is text-only.
   If an external momentum snapshot is missing or stale, report that the
   optional snapshot is unavailable and continue without it unless the user
   explicitly provides a fresh file. Do not rebuild private quantitative models
   from public market data inside daily tracking. Public market data can support
   tape, sector breadth, and relative-strength notes only. Any sector/theme
   rotation belongs in market breadth, not in the external snapshot table.
4. Update setup-level fields:
   - trigger zone;
   - invalidation;
   - stop concept;
   - target zones;
   - execution timeframe;
   - instrument fit against trading profile;
   - risk/reward after the update.
5. For each relevant setup, classify it as:
   - `candidate`
   - `active`
   - `approaching`
   - `triggered`
   - `invalidated`
   - `needs_review`
   - `completed`
6. If a new opportunity appears, tie it back to an existing theme/context or create a new `candidate` setup before treating it as actively tracked.
7. Prefer `assets/templates/daily-market-tracking.md` for notes.

## Runtime Guidance Contract

Always translate the runtime state into user-facing Chinese before giving
market commentary. Internal slug values may appear only in parentheses after
the Chinese label, for example `盘前快速更新 (premarket_quick_update)`, `待复核
(needs_review)`, or `修复观察 (repair-watch)`. Do not make the internal slug
the primary status text.

Include `运行状态` and `可执行下一步` whenever runtime health is incomplete,
broker access is missing, optional external momentum input is missing/stale, or
the request cannot enter formal intraday scanning.

Use these user-facing status labels:

- `盘前快速更新`: useful quick market read, but not a formal scan.
- `正式盘中扫描`: prepared setup scan using today's plan/watchlist files.
- `待复核`: setup or data state needs user/agent review before a trigger call.
- `修复观察`: rebound or repair tape that is not yet full risk-on confirmation.

When degraded, choose 2-4 concrete `可执行下一步` actions from this set and
adapt them to the exact missing files:

- `初始化今日运行包`: create today's daily runtime directory and base files.
- `生成盘中观察清单`: build `intraday-watchlist.csv` from Active Plan setups.
- `启用外部动量快照`: use a user-confirmed external momentum snapshot as an
  optional input.
- `跳过外部动量快照`: continue without optional external momentum input.
- `继续盘前快速更新`: stay in quick-update mode until the next macro/event check.

Every live quote, macro indicator, broker snapshot, and official data point
must carry a `数据时间戳`, preferably `as of <timestamp/source date>`. If the
timestamp is unavailable, say `as of 未确认` instead of implying freshness.

## Output

Use Chinese Markdown with:

- `运行状态`
- `结论`
- `重要变化`
- `宏观数据来源状态`
- `实际宏观指标读数`
- `当前盘面`
- `快速宏观/利率`
- `政策/新闻`
- `事件预览`
- `动量榜单更新`
- `Price Action 滚动盘面分析`
- `上次分析对照`
- `走势强弱参考点位`
- `加仓/减仓/暂停区`
- `本周事件映射`
- `Active Plan 对照`
- `点位更新`
- `交易风格匹配`
- `接近触发`
- `已失效`
- `需要复核`
- `新证据`
- `下一步看盘顺序`
- `可执行下一步`

Keep the note operational: what changed, what matters today, and what the user should inspect first. Avoid long intraday commentary; collapse repeated headlines and price noise into changed variables, setup transitions, and explicit invalidations.

## Price Action Rolling Output

Only enter this section after every ticker has a complete confirmed setup key.
If the setup key is incomplete, use the watch-only gate above and do not render
this section.

When the user asks for PA, 盘面分析, point updates, or add/reduce levels, include
`Price Action 滚动盘面分析` even in a quick update.

Before giving new levels, check the previous analysis in this order:

1. current `market-plan.md` setup rows and holding plans;
2. latest `updates/YYYY-MM-DD.md` notes;
3. today's `daily/YYYY-MM-DD/` notes and watchlist rows;
4. user-provided prior analysis in the current chat.

If no previous analysis is available, say `上次分析对照: 未找到可用记录，本次作为基准分析`.

When authorized or user-provided `OHLCV` JSON is available, use
`price_action_rollforward.py` as the local baseline generator before adding
judgement. It only transforms provided data; it does not fetch market data,
read broker accounts, or create orders.
If the source is saved Longbridge kline output, use
`longbridge_ohlcv_adapter.py` to normalize it into OHLCV first.

For every ticker, state:

- `主分析时间框架`: the higher timeframe used to judge structure, normally
  `4H`, `1D`, or `1W`.
- `辅助时间框架`: the lower timeframe used for execution observation or level
  refinement, normally `1H` or below.
- `走势强弱参考点位`: levels that separate strong continuation, repair,
  neutral/range, weakness, and invalidation.
- `加仓/减仓/暂停区`: add, TP/rebalance, and pause/review zones tied to the
  user's holding horizon. Long-term ETF holdings should discuss add and
  TP/rebalance, not ordinary stop-loss exits.
- `支撑/压力`: every key level should say whether it is support, resistance,
  midpoint, gap, or invalidation.
- `点位所属时间框架`: every add/reduce/pause level should say whether it comes
  from `4H`, `1D`, `1W`, `1H`, or a lower execution timeframe.
- `成本/买入记录`: when holdings or prior buys are available, distinguish
  low-cost core lots from high-cost chase lots before proposing add or
  TP/rebalance zones.
- `比例式加减仓`: use `少量`, `中等`, `较大`, `1/10`, `1/5`, or `1/3` style
  sizing. Do not give exact share counts unless the user explicitly asks.
- `本周事件映射`: macro, rates, policy, earnings, or industry events that can
  make those levels more or less reliable.
