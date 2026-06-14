# Interactive Trade Review Intake

Use this mode when the user wants to record an actual trade, review today's trades, fill in a trade journal, or says they need help writing the review.

The interaction should feel like a disciplined `grill-me` session: ask one question at a time, give a recommended answer when the existing plan/chart/trade record provides enough evidence, and keep going until the trade can be written into local daily records.

## Purpose

Support two review stages:

1. **Post-order review**: immediately after an order or fill, capture the entry facts and decision context while the memory is fresh.
2. **Post-exit review**: after the trade is closed, complete result, exit quality, realized R, mistake tags, lessons, and next rules.

Each stage should produce or update two outputs:

1. A structured `trades.csv` row or row update.
2. A readable `reviews.md` section.

Do not accept vague answers when the field matters for statistics. If the user says "felt strong", ask what made it strong: trend, gap, support/resistance, EMA, signal bar, follow-through, volume, option flow, or macro context.

## Operating Rules

- Ask one question at a time.
- Prefer concrete facts: time, price, timeframe, signal bar, stop, target, quantity, cost, PnL.
- Use read-only broker order/trade facts when available for objective fields such as symbol, side, quantity, price, fees, order time, fill time, and PnL. Ask the user to confirm before writing.
- If the user already has a setup in `market-plan.md` or a planned trade in `trade-plans.csv`, compare the actual trade to that setup/plan.
- Keep a running draft of mapped fields internally and write the final result only after the key fields are resolved.
- If exact numeric data is missing, mark it as `unknown` or leave the field blank; do not fabricate.
- Preserve the user's original review wording in `review_raw` when useful.
- Extract structured review fields from the raw text.
- Do not wait until the trade is closed to capture entry rationale. The post-order review exists to prevent hindsight rewriting.

## Stage Selection

First determine the stage:

```text
这笔交易是刚下单/刚成交，需要做下单后记录，还是已经结束，需要做结束后复盘？
```

Use:

- `post_order` when the trade is open, newly filled, partially filled, or just entered.
- `post_exit` when the trade is closed, expired, stopped, scratched, or otherwise finished.

## Post-Order Question Sequence

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

If broker trade facts are available, prefill objective fields and ask the user to confirm the mapping.

### 2. Link To The Plan

Ask:

```text
这笔交易来自哪个 Active Market Plan setup、每日更新条目或预备交易计划？如果是计划外交易，为什么当时允许自己做？
```

Map to:

- `parent_trade_id`
- `setup_review`
- `review_raw`
- `mistake_tag` if this was a planless entry

### 3. Define The Trade Type And Timeframes

Ask:

```text
这是哪类交易：LEAP、swing option、2x/3x ETF、普通 ETF/股票、还是 0DTE QQQ/SPY？你当时用哪些时间框架看盘，实际触发用哪个时间框架？
```

Map to:

- `trade_type`
- `instrument_type`
- `analysis_timeframe`
- `trigger_timeframe`

### 4. Market Background

Ask:

```text
入场前你看到的盘面背景是什么？例如趋势/交易区间、跳空、关键支撑阻力、20/50 EMA、前高前低、宏观/利率背景。
```

Map to:

- `setup_review`
- `price_action_context` when updating a plan
- `ema_context` when updating a plan
- `review_raw`

### 5. Entry Reason

Ask:

```text
你的具体入场理由是什么？这笔交易是突破、回调、二次入场、失败突破、反转，还是区间高抛低吸？
```

Map to:

- `setup_tag`
- `entry_review`
- `entry_trigger` when updating a plan

### 6. Signal Bar

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

### 7. Auxiliary Evidence

Ask:

```text
有没有辅助信号？例如 50% 回撤、三推、成交量、异常期权、上级别 20/50 EMA、宏观/利率没有反向打脸。
```

Map to:

- `entry_review`
- `options_context` when relevant
- `macro_context` when relevant

### 8. Confidence

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

### 9. Execution And Risk

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

Post-order output should set:

- `status`: `open`
- `outcome`: `open`
- `exit_date`, `pnl`, `realized_R`, `exit_review`: blank or `unknown`

## Post-Exit Question Sequence

### 1. Identify Or Match The Open Trade

Ask:

```text
这笔结束的交易对应哪一条 open trade？如果 broker 里有成交记录，请确认 trade_id、setup_id、标的、方向、数量、入场价、出场价和时间。
```

Map to:

- `trade_id`
- `exit_date`
- `quantity`
- `fees`
- `pnl`

### 2. Exit And Result

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

### 3. Plan Versus Actual

Ask:

```text
这笔交易从入场到出场是否遵守了原计划？如果偏离了，是因为盘面变化、情绪、仓位、时间框架，还是原计划本身不完整？
```

Map to:

- `setup_review`
- `entry_review`
- `exit_review`
- `mistake_tag`
- `lesson`

### 4. Mistake And Lesson

Ask:

```text
这笔交易最大的错误或最好的一点是什么？如果明天遇到同类 setup，你要改哪一条规则？
```

Map to:

- `mistake_tag`
- `lesson`
- `review_raw`

Post-exit output should update:

- `status`: `closed` when the trade is fully finished, or keep `open` for partial exits.
- `outcome`
- `pnl`
- `realized_R`
- `exit_review`
- `mistake_tag`
- `lesson`

## Final Output

After the questions, produce:

1. A `trades.csv` row draft or row update.
2. A `reviews.md` post-order or post-exit section draft.
3. Any missing fields.
4. Suggested `mistake_tag`, `outcome`, and confidence calibration.

Then ask the user whether to write it into the local daily folder.

## Review Section Template

```markdown
### {trade_id} - {symbol}

- 产品/方向：
- 阶段：post_order / post_exit
- 分析时间框架：
- 触发时间框架：
- 盘面背景：
- 入场理由：
- 信号 K：
- 辅助信号：
- 入场信心：
- 风险计划：
- 出场与结果：
- 计划 vs 实际：
- 错误标签：
- 经验：
- 下次规则：
```
