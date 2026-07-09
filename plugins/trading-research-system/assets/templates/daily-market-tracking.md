# Market Plan Update

## Date

- Date:
- Update depth: deep_update / quick_update / trigger_update / review_update
- Linked market plan:

## 运行状态

- 当前模式: 盘前快速更新 / 正式盘中扫描 / 盘中触发复核 / 收盘复盘
- 内部 slug (internal slug): only in parentheses after the Chinese label
- 降级原因:
- runtime health:
- missing blockers:
- broker source:
- optional external momentum snapshot:
- 数据时间戳:
- 行情数据: as of
- 宏观/利率数据: as of
- 券商快照: as of
- 官方事件数据: as of

Use Chinese status labels as the primary text. Examples: `盘前快速更新`,
`正式盘中扫描`, `待复核`, `修复观察`. Do not expose internal slugs as the main
status.
- Market regime:
- Rates/yields:
- Macro / policy events:
- News catalysts:
- Event preview:
- optional external momentum snapshot: provided / missing / stale / skipped
- If missing or stale: continue without optional external momentum unless the user explicitly provides a snapshot.
- Do not rebuild, rank, or backtest a private quantitative model inside this plugin.
- Portfolio exposure concern:

## 宏观数据来源状态

| source | status | used_for | fallback |
| --- | --- | --- | --- |
| Longbridge macrodata | available / unauthorized / not_installed / missing / stale | macro values and financial conditions | official source fallback |
| IBKR market data | available / unauthorized / not_installed / missing / stale | price and OHLCV transmission | public/authorized market data |
| official source fallback | available / pending / unavailable | S0 facts and fallback values | reputable media leads only |

## 实际宏观指标读数

| 指标 | 当前值 | 近5日/20日变化 | 阈值 | 对策略姿态影响 | 数据时间戳 | source |
| --- | --- | --- | --- | --- | --- | --- |
| 10Y |  |  | 4.5% | high beta momentum / balanced / defensive |  | Longbridge macrodata / official source fallback |
| 30Y |  |  | 5.0% | duration pressure / relief |  |  |
| HYG/LQD |  |  | widening / tightening | credit risk appetite |  |  |
| DXY |  |  | breakout / breakdown | USD liquidity and earnings pressure |  |  |
| Oil |  |  | spike / breakdown | inflation and volatility pressure |  |  |
| Gold |  |  | trend confirmation | optional defensive / easing hedge confirmation |  |  |

## 策略姿态

- posture: defensive / balanced / high beta momentum
- supports:
- pressures:
- blocks:

## Current Market Read

- Index structure:
- Sector leadership:
- Breadth / momentum:
- 20 EMA / 50 EMA context:
- Trading range or trend:
- Noise to ignore:

## Quick Macro / Policy / News

- Macro:
- Rates:
- Treasury / fiscal policy:
- Fed policy:
- Trump-related market-moving policy:
- News:
- Next major event:

## External Momentum Snapshot Update

| Ticker | Source rank | Score / percentile | Snapshot date | Source status | Plan impact |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Sector/theme rotation

| Theme / sector / asset class | Direction | Evidence | Setup impact |
| --- | --- | --- | --- |
|  |  |  |  |

## Setup Status Changes

| setup_id | Symbol | Instrument | Previous status | New status | Current read | Trigger zone | Invalidation | Updated levels | Attention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  | 候选 (candidate) / 激活 (active) / 接近触发 (approaching) / 已触发 (triggered) / 已失效 (invalidated) / 待复核 (needs_review) / 已完成 (completed) |  |  |  |  |  |

## New Evidence

- Verified facts:
- Assumptions:
- Research notes to validate:
- Option-flow clues:

## Opportunity Updates

### {setup_id} - {ticker}

- What changed:
- Setup read:
- Signal timeframe:
- Risk/reward now:
- Portfolio impact:
- Next user decision:

## Price Action 滚动盘面分析

## 时间框架声明

| 标的 | 主分析时间框架 | 辅助时间框架 | 为什么这样选 |
| --- | --- | --- | --- |
|  | 4H / 1D / 1W | 1H / 15m / 5m | 主分析时间框架判断走势环境；辅助时间框架只微调执行观察和短线确认 |

## 上次分析对照

| 标的 | 上次结论 | 上次关键点位 | 最新变化 | 本次是否修正 |
| --- | --- | --- | --- | --- |
|  | 未找到时写：本次作为基准分析 |  |  |  |

## 走势强弱参考点位

| 标的 | 点位所属时间框架 | 支撑/压力 | 强势延续 | 修复确认 | 中性/震荡 | 转弱 | 失效/暂停复核 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 4H / 1D / 1W / 1H | 支撑 / 压力 / 中轴 / 缺口 |  |  |  |  |  |

## 加仓/减仓/暂停区

| 标的 | 成本/买入记录 | 仓位定位 | 可考虑加仓区 | TP/再平衡区 | 暂停加仓/复核区 | 比例式加减仓 | 不做什么 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 均价 / 低成本核心 / 高成本批次 / unknown | 长期持有 / 主题仓 / 交易仓 |  |  |  | 少量 / 中等 / 较大 / 1/10 / 1/5 / 1/3 | 不默认给具体股数 |

## 本周事件映射

| 事件 | 时间 | 传导路径 | 影响标的 | 会增强什么判断 | 会削弱什么判断 |
| --- | --- | --- | --- | --- | --- |
|  | 日期 + 时区 | rates / yields / USD / oil / sector / volatility / earnings |  |  |  |

## End Of Day Notes

- Best opportunity:
- Missed opportunity:
- Invalidated idea:
- Plan update for next session:

## 可执行下一步

只列 2-4 个动作，按最能推进今天流程的顺序排列。

| 动作 | 适用条件 | 需要用户回复 | 执行后进入 |
| --- | --- | --- | --- |
| 初始化今日运行包 | `daily/YYYY-MM-DD/`、`trade-plans.csv` 或基础 daily 文件缺失 | 允许/不允许初始化今天 runtime 草稿 | 盘前快速更新或正式盘中扫描准备 |
| 生成盘中观察清单 | Active Plan 可读但 `intraday-watchlist.csv` 缺失 | 确认要跟踪的 setup / ticker + trade_horizon + instrument | 正式盘中扫描 |
| 启用外部动量快照 | 用户已有外部模型输出 snapshot | 提供文件路径或确认来源 | 交易计划准备 |
| 跳过外部动量快照 | 外部动量快照缺失/过期但今天仍要继续 | 确认本轮不用外部动量输入 | 继续盘前快速更新 |
| 继续盘前快速更新 | 关键宏观/事件尚未落地，或正式扫描条件不足 | 确认下一次检查时间/事件 | 盘前快速更新 |
