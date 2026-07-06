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
- KVN source status:
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
- KVN source status: imported snapshot / missing / stale
- KVN ticker-only Top10:
- KVN change summary:
- If missing or stale: Do not rebuild KVN; ask whether to import a snapshot or continue without KVN.
- Do not re-rank or re-score KVN; preserve the script-computed ticker order.
- Portfolio exposure concern:

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

## KVN Momentum Leaderboard Update

| Ticker | Rank vs S&P500 | KVN 分数 | KVN P | 当前是否 S&P500 | Top10 memory | Plan impact |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

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
| 导入 KVN snapshot | 用户有新的 KVN CSV 或上游 snapshot | 提供文件路径或确认导入来源 | KVN ticker-only Top10 更新 |
| 跳过 KVN | KVN store 缺失/过期但今天仍要继续 | 确认本轮不使用 KVN | 继续盘前快速更新 |
| 继续盘前快速更新 | 关键宏观/事件尚未落地，或正式扫描条件不足 | 确认下一次检查时间/事件 | 盘前快速更新 |
