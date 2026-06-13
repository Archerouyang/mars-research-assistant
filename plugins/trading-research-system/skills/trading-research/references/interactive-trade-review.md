# Interactive Trade Review Intake

Use this mode when the user wants to record an actual trade, review today's trades, fill in a trade journal, or says they need help writing the review.

The interaction should feel like a disciplined `grill-me` session: ask one question at a time, give a recommended answer when the existing plan/chart/trade record provides enough evidence, and keep going until the trade can be written into local daily records.

## Purpose

Produce two outputs:

1. A structured `trades.csv` row or row update.
2. A readable `reviews.md` section.

Do not accept vague answers when the field matters for statistics. If the user says "felt strong", ask what made it strong: trend, gap, support/resistance, EMA, signal bar, follow-through, volume, option flow, or macro context.

## Operating Rules

- Ask one question at a time.
- Prefer concrete facts: time, price, timeframe, signal bar, stop, target, quantity, cost, PnL.
- If the user already has a planned trade in `trade-plans.csv`, compare the actual trade to that plan.
- Keep a running draft of mapped fields internally and write the final result only after the key fields are resolved.
- If exact numeric data is missing, mark it as `unknown` or leave the field blank; do not fabricate.
- Preserve the user's original review wording in `review_raw` when useful.
- Extract structured review fields from the raw text.

## Question Sequence

### 1. Identify The Trade

Ask:

```text
这笔交易是哪一天、哪个标的、什么方向、什么产品？如果它来自今天的某个预备交易计划，trade_id 是哪个？
```

Map to:

- `entry_date`
- `symbol`
- `underlying`
- `direction`
- `product`
- `instrument_type`
- `parent_trade_id`
- `trade_id`

### 2. Define The Trade Type And Timeframes

Ask:

```text
这是哪类交易：LEAP、swing option、2x/3x ETF、普通 ETF/股票、还是 0DTE QQQ/SPY？你当时用哪些时间框架看盘，实际触发用哪个时间框架？
```

Map to:

- `trade_type`
- `instrument_type`
- `market_analysis_timeframes`
- `execution_timeframe`

### 3. Market Background

Ask:

```text
入场前你看到的盘面背景是什么？例如趋势/交易区间、跳空、关键支撑阻力、20/50 EMA、前高前低、宏观/利率背景。
```

Map to:

- `setup_review`
- `price_action_context` when updating a plan
- `ema_context` when updating a plan
- `review_raw`

### 4. Entry Reason

Ask:

```text
你的具体入场理由是什么？这笔交易是突破、回调、二次入场、失败突破、反转，还是区间高抛低吸？
```

Map to:

- `setup_tag`
- `entry_review`
- `entry_trigger` when updating a plan

### 5. Signal Bar

Ask:

```text
你入场时看到的信号 K 是什么样的？强/中/弱？它有没有突破前一根 K 的高低点、站上/跌破 20EMA，后面有没有跟随？
```

Map to:

- `signal_quality`
- `entry_review`
- `mistake_tag` if signal quality was poor but entry was taken

Signal labels:

- `strong`
- `medium`
- `weak`
- `no_signal`

### 6. Auxiliary Evidence

Ask:

```text
有没有辅助信号？例如 50% 回撤、三推、成交量、异常期权、上级别 20/50 EMA、宏观/利率没有反向打脸。
```

Map to:

- `entry_review`
- `options_context` when relevant
- `macro_context` when relevant

### 7. Confidence

Ask:

```text
入场时你的信心是高、中、低？为什么？这个信心来自背景、信号 K、跟随、风险收益比，还是只是情绪？
```

Map to:

- `confidence`
- `entry_review`

Confidence labels:

- `high`
- `medium`
- `low`

### 8. Execution And Risk

Ask:

```text
入场价格、止损、目标、数量/合约数、总成本、手续费是多少？当时计划亏损多少，目标 R 是多少？
```

Map to:

- `entry_price`
- `stop_price`
- `target_price`
- `quantity`
- `cost`
- `fees`
- `risk_amount`
- `planned_R`

### 9. Exit And Result

Ask:

```text
你在哪里出场？为什么出场？最后盈亏是多少？按计划风险算大约是多少 R？
```

Map to:

- `exit_date`
- `pnl`
- `realized_R`
- `outcome`
- `exit_review`

Outcome labels:

- `win`
- `loss`
- `breakeven`
- `scratch`
- `open`
- `invalidated_before_entry`
- `missed`

### 10. Mistake And Lesson

Ask:

```text
这笔交易最大的错误或最好的一点是什么？如果明天遇到同类 setup，你要改哪一条规则？
```

Map to:

- `mistake_tag`
- `lesson`
- `review_raw`

## Final Output

After the questions, produce:

1. A `trades.csv` row draft.
2. A `reviews.md` section draft.
3. Any missing fields.
4. Suggested `mistake_tag`, `outcome`, and confidence calibration.

Then ask the user whether to write it into the local daily folder.

## Review Section Template

```markdown
### {trade_id} - {symbol}

- 产品/方向：
- 分析时间框架：
- 触发时间框架：
- 盘面背景：
- 入场理由：
- 信号 K：
- 辅助信号：
- 入场信心：
- 风险计划：
- 出场与结果：
- 错误标签：
- 经验：
- 下次规则：
```
