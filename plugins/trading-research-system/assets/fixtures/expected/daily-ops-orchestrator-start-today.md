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
- 选择 Broker Source Setup：Longbridge read-only、IBKR read-only、两者都启用，或暂不启用并以 manual CSV / no broker facts 继续。
- 确认 QQQ、MU、TSM、GLW 分别是什么交易周期和工具。
- 确认是否需要在后续正式运行中允许 web/current-source 检查。

## Broker Source Setup

当前 broker source 是 unauthorized，所以不能只报告缺口，需要询问只读来源偏好。

是否启用只读 broker 数据？选项：

1. Longbridge read-only：读取持仓、成交、订单状态和授权行情；若未安装/启用，需要用户先处理 Longbridge skill/plugin/terminal。
2. IBKR read-only：读取持仓、成交、订单状态和授权行情；若 connector 未授权，需要用户先启用。
3. Longbridge read-only + IBKR read-only：两者都启用，并在后续确认 source order。
4. 暂不启用：本轮用 manual CSV 或 no broker facts 继续。

本步骤不会读取 broker，不会写 runtime，不会安装软件，也不会创建、修改、取消或批准订单。

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

## 下一步指引

- 默认建议: 本轮先不读 broker，先确认 QQQ、MU、TSM、GLW 的 `ticker + trade_horizon + instrument`，并允许初始化 `ops-state.md` 草稿；确认后再做盘前 quick update。
- 可选路径: 1. 先做 Broker Source Setup；2. 先初始化今天 runtime package；3. 不写 runtime，只做 reduced-scope dry-run；4. 先补 KVN snapshot 后再更新计划。
- 你只需要回复: `Broker 暂不启用；QQQ=长期持有 ETF + 0DTE option；MU=中期正股；TSM=LEAP call；GLW=watch only；允许初始化 ops-state 草稿。`
- 我会执行: 按确认后的分组读取 Active Market Plan，输出今日变化、需要盯的 setup、哪些接近触发、哪些暂停或复核；若允许写入，只生成 proposed write package，不直接写 runtime。

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
