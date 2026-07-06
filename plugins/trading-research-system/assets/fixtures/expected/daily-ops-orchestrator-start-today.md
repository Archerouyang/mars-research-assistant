# 当前日程阶段

- stage: 盘前 quick update
- reason: 用户说“开始今天的交易研究日程”，当前上下文是 weekday premarket，且已有 `market-plan.md` 和 `trading-profile.md` 可读。
- confidence: medium，因为 `ops-state.md` 缺失且 KVN snapshot stale。

## 读取状态

- runtime health: available
- `ops-state.md`: missing，需要建议初始化但不会写 runtime
- `market-plan.md`: available
- `trading-profile.md`: available
- KVN snapshot: stale，本次不能把公开行情重建成 KVN
- broker source: unauthorized，本次不会读取 broker
- missing data: ticker 交易周期未知，不能生成具体 entry / exit trigger

## 缺失确认

- 确认是否允许初始化 `ops-state.md` 草稿。
- 确认 QQQ、MU、TSM、GLW 分别是什么交易周期和工具。
- 确认是否需要在后续正式运行中允许 web/current-source 检查。

## Ticker / Setup 周期确认

当前不能按 ticker 直接生成触发点。需要先按 `ticker + trade_horizon + instrument` 分组。

| ticker | trade_horizon | instrument | status | needed confirmation |
| --- | --- | --- | --- | --- |
| QQQ | unknown | unknown | blocked_setup | 是长期持有 ETF、0DTE、日内，还是 swing？ |
| MU | unknown | unknown | blocked_setup | 是中期波段、LEAP、正股，还是观察？ |
| TSM | unknown | unknown | blocked_setup | 是 LEAP、正股中期、长期持有，还是观察？ |
| GLW | unknown | unknown | blocked_setup | 是中期波段、主题观察，还是只 watch only？ |

## 建议下一步

Next Recommended Action: 先完成 ticker / setup 周期确认，然后执行盘前 quick update。

## 为什么现在做这一步

- 盘前 quick update 需要知道每个标的是长期配置、波段、日内、0DTE、LEAP 还是观察，否则时间框架和触发严格度会错。
- KVN stale 和 broker unauthorized 不阻止流程开始，但会降低动量和持仓风险判断的置信度。

## 确认后我会执行

确认每个标的的 trade_horizon 和 instrument 后，我会读取当前 Active Market Plan，以盘前 quick update 的方式输出：今日变化、需要盯的 setup、哪些接近触发、哪些需要暂停或复核。不会写 runtime，不会读取 broker，不会创建真实 automation。

## 安全边界

- 不会生成买卖指令。
- 不会下单、改单、撤单、平仓或批准订单。
- 不会读取 broker，除非用户授权 read-only source。
- 不会写 runtime，除非用户确认 proposed write package。
- 不会创建真实 automation。
