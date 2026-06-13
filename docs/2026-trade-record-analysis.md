# 2026 交易记录分析

来源：Google Sheets `2026交易记录`，读取时间 2026-06-13。

该工作簿当前包含 `持仓分布`、`active`、`longterm`、`交易统计`、`结构优化建议`。其中 `active` 是主交易日志，`结构优化建议` 已经指出了后续系统化的关键方向。

## 当前 Sheet 状态

- `active`: 有表头和 2 条交易记录，当前是主交易日志。
- `持仓分布`: 有多个块状资产配置/持仓区域，适合查看但不适合自动汇总。
- `longterm`: 当前读取为空。
- `交易统计`: 当前读取为空。
- `结构优化建议`: 有结构化建议，包含字段补充、风险口径、复盘拆分、下拉字典、持仓台账和统计页建议。

## 同步方向

本地 `data/daily/YYYY-MM-DD/` 记录应作为第一事实记录层。Google Sheets 只做单向同步镜像、筛选和展示，不做自动回写来源。

## 当前结构

`active` 已有字段：

- `entry_date`
- `symbol`
- `direction`
- `trade_type`
- `product`
- `timeframe`
- `信号k类型`
- `background`
- `辅助信号`
- `入场价格`
- `初始止损`
- `初始目标`
- `初始盈亏比`
- `总成本`
- `盈亏`
- `思考复盘`
- `信心`
- `tradingview_link`
- `currency`

这些字段已经能记录交易想法、入场背景、信号质量、初始风险收益和复盘文本。

## 主要缺口

### 交易日志缺口

需要补充：

- `trade_id`
- `status`
- `exit_date`
- `exit_price`
- `quantity`
- `fees`
- `risk_amount`
- `planned_R`
- `realized_R`
- `outcome`
- `mistake_tag`
- `lesson`

原因：只记录盈亏金额会被仓位大小影响；要优化交易系统，必须用 R 倍数、错误标签和 setup 分类统计。

### 风险口径缺口

当前已有初始止损、初始目标、初始盈亏比，但缺少每笔计划风险。

标准口径：

```text
risk_amount = abs(entry_price - stop_price) * quantity
realized_R = pnl / risk_amount
```

期权交易需要按合约乘数和实际成本调整风险口径。

### 复盘文本缺口

当前 `思考复盘` 质量较高，但把 setup、入场、离场、错误和经验混在一个长文本中。

建议拆成：

- `setup_review`
- `entry_review`
- `exit_review`
- `mistake_tag`
- `lesson`
- `review_raw`

保留原始复盘文本，但新增结构化列用于统计。

### 多值单元格缺口

`入场价格` 中出现 `717,715` 这类多价格写入同一格的情况。

原则：

```text
1 行 = 1 个最小可统计单元
```

分批成交应拆成多行，用 `trade_id` 关联同一交易想法，避免公式和统计失效。

### 日期一致性缺口

文件名是 `2026交易记录`，但 `active` 中现有记录日期是 `2025-06-08`。

需要后续确认：

- 这是历史样例
- 这是模板数据
- 还是日期录入错误

年度统计前必须清理或归档。

## 持仓分布问题

`持仓分布` 当前是一页内多个资产块，适合查看，不适合自动汇总。

建议改成持仓台账：

- `date`
- `account`
- `symbol`
- `strategy`
- `currency`
- `quantity`
- `avg_cost`
- `last_price`
- `market_value`
- `target_weight`
- `current_weight`
- `notes`

展示页和再平衡建议从持仓台账生成，不直接手工维护块状结构。

## 推荐主表列顺序

```text
trade_id
status
entry_date
exit_date
symbol
underlying
direction
trade_type
product
instrument_type
market_analysis_timeframes
execution_timeframe
setup_tag
signal_quality
confidence
entry_price
stop_price
target_price
quantity
cost
fees
pnl
risk_amount
planned_R
realized_R
outcome
mistake_tag
setup_review
entry_review
exit_review
lesson
review_raw
chart_link
currency
```

## 对插件的要求

MVP 1 应支持：

1. 本地 `data/daily/YYYY-MM-DD/` 日分区记录。
2. 交易计划、实际交易记录、观察清单、持仓台账的 CSV 模板。
3. 用 R 倍数和 outcome 统计交易质量。
4. 按 `instrument_type`、`setup_tag`、`execution_timeframe`、`signal_quality`、`confidence` 分组统计。
5. 保留原始复盘文本，同时拆出结构化复盘字段。
6. 后续同步到 Google Sheets 时，Sheets 作为镜像和查看层，本地日分区记录仍是第一事实记录层。
