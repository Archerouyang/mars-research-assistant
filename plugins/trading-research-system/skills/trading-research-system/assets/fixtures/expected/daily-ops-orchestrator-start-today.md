# 当前日程阶段

- stage: 盘前快速更新
- reason: 用户说“开始今天的交易研究”，当前上下文是 weekday premarket，且已有 `market-plan.md` 和 `trading-profile.md` fixture 可读。
- confidence: medium，因为 broker capability/source 仍需复核且 KVN snapshot missing。

## 读取状态

- runtime health: available
- runtime_dir: `/private/tmp/dailytrades-uat-runtime-9a24200`
- runtime_origin: `explicit_argument`
- formal runtime: available，正式 runtime 可用；不要把 repo fixture 当作当前 Active Market Plan
- startup_status: `ready`
- startup_reason: runtime_health.py 未提供；不得另行推断
- 当前模式: `dry-run`
- `ops-state.md`: missing，需要建议初始化但不会写 runtime
- `market-plan.md`: available
- `trading-profile.md`: available
- `daily/YYYY-MM-DD/`: available
- KVN snapshot: missing，本次不能把公开行情重建成 KVN
- broker source: needs_review，本次不会读取 broker facts
- portfolio_reconciliation: `unavailable`，Longbridge 与 IBKR 均 excluded；组合暴露 fail-closed
- missing data: ticker 交易周期未知，不能生成具体 entry / exit trigger

### 运行状态检查

| item | status | note |
| --- | --- | --- |
| runtime_dir | available | `/private/tmp/dailytrades-uat-runtime-9a24200` |
| runtime_origin | explicit_argument | `--runtime-dir` 的确定性结果；不得改写为 default 或 environment |
| formal runtime | available | 正式 runtime 可用；只读取状态，不复制私有内容 |
| startup_status | ready | 保留 runtime_health.py 的确定性状态；不因 `ops-state.md` 缺失而改写 |
| startup_reason | not_provided | runtime_health.py 未提供 reason；不得另行推断 |
| current_mode | dry-run | 当前模式；不假设 broker、持仓、订单或成交事实 |
| ops-state.md | missing | 可建议初始化草稿，但需要用户确认 |
| market-plan.md | available | 只作为当前状态读取 |
| trading-profile.md | available | 用于交易周期和工具偏好 |
| macro-panel.json | missing | 只显示状态；宏观来源详情见独立区块 |
| portfolio_snapshot.csv | available | status only；仅确认文件存在，不读取私有持仓行 |
| daily/YYYY-MM-DD/ | available | 当日运行包存在；只读取状态 |

### 券商来源健康

`source_capability_health` 先于 `broker_source_health` 展示；capability 状态不等同于 broker 授权状态。

| capability | status | effect |
| --- | --- | --- |
| Longbridge broker skill | needs_review | capability status not confirmed; authorization is not inferred |
| Longbridge Terminal CLI | needs_review | capability status not confirmed; authorization is not inferred |
| Longbridge macrodata | needs_review | capability status not confirmed; authorization is not inferred；这是宏观数据能力，不是 broker account source |
| Official source fallback | missing | capability output missing |
| IBKR connector | needs_review | capability status not confirmed; authorization is not inferred |
| Manual snapshot | missing | capability output missing |

| source | status | effect |
| --- | --- | --- |
| Longbridge | needs_review | 未提供本轮只读来源状态；不能读取 broker facts |
| IBKR | needs_review | 未提供本轮只读来源状态；不能读取 broker facts |
| Manual snapshot | missing | 本轮没有用户确认的 broker snapshot |
| portfolio_reconciliation | unavailable | longbridge、ibkr 均 excluded；合并组合暴露 fail-closed |

当前模式: `dry-run`，可以做公开数据和计划状态 quick update，但持仓 sizing、成交事实和组合风险只能降级处理。

### 宏观数据来源状态

| item | source status | effect |
| --- | --- | --- |
| macro-panel.json | missing | 不能生成已验证的 Macro Regime Mini-Panel |
| authorized/current macro values | missing | 本 fixture 没有已授权/当前宏观数值，不输出或虚构实际宏观指标读数 |

状态来源是 synthetic fixture/debug input，不代表 fresh-session 已完成实时核验。

## 缺失确认

- 确认是否允许初始化 `ops-state.md` 草稿。
- `portfolio_reconciliation=unavailable`：确认 broker read-only 来源后再复核；此前组合合并暴露保持 fail-closed。
- 选择券商只读来源设置：Longbridge read-only、IBKR read-only、两者都启用，或暂不启用并以 manual CSV / no broker facts 继续。
- 确认 QQQ、MU、TSM、GLW 分别是什么交易周期和工具。
- 确认是否需要在后续正式运行中允许 web/current-source 检查。

## 券商只读来源设置

这是 Daily Ops first start；Longbridge 与 IBKR 当前均为 needs_review，所以需要询问只读来源偏好，但不能误报 unauthorized。

是否启用只读 broker 数据？选项：

1. Longbridge read-only：读取持仓、成交、订单状态和授权行情；若未安装/启用，需要用户先处理 Longbridge skill/plugin/terminal。
2. IBKR read-only：读取持仓、成交、订单状态和授权行情；若 connector 未授权，需要用户先启用。
3. Longbridge read-only + IBKR read-only：两者都启用，并在后续确认 source order。
4. 暂不启用：本轮用 manual CSV 或 no broker facts 继续。

本步骤不会读取 broker，不会写 runtime，不会安装软件，也不会创建、修改、取消或批准订单。

## 标的与交易想法周期确认

当前不能按 ticker 直接生成触发点。需要先按 `ticker + trade_horizon + instrument` 分组。

| ticker | trade_horizon | instrument | status | needed confirmation |
| --- | --- | --- | --- | --- |
| QQQ | unknown | unknown | blocked_setup | 是长期持有 ETF、0DTE、日内，还是 swing？ |
| MU | unknown | unknown | blocked_setup | 是中期波段、LEAP、正股，还是观察？ |
| TSM | unknown | unknown | blocked_setup | 是 LEAP、正股中期、长期持有，还是观察？ |
| GLW | unknown | unknown | blocked_setup | 是中期波段、主题观察，还是只 watch only？ |

## 建议下一步

建议下一步: 先完成标的与交易想法周期确认，然后执行盘前快速更新。

## 下一步指引

- 默认建议: 本轮先不读 broker，先确认 QQQ、MU、TSM、GLW 的 `ticker + trade_horizon + instrument`，并允许初始化 `ops-state.md` 草稿；确认后再做盘前快速更新。
- 可选路径: 1. 先做券商只读来源设置；2. 只提出 `ops-state.md` 初始化草稿；3. 不写 runtime，只做 reduced-scope dry-run；4. 先补 KVN snapshot 后再更新计划。
- 你只需要回复: `券商来源暂不启用；QQQ=长期持有 ETF + 0DTE option；MU=中期正股；TSM=LEAP call；GLW=watch only；允许初始化 ops-state 草稿。`
- 我会执行: 按确认后的分组读取 Active Market Plan，输出今日变化、需要盯的 setup、哪些接近触发、哪些暂停或复核；若允许写入，只生成 proposed write package，不直接写 runtime。

## 为什么现在做这一步

- 盘前快速更新需要知道每个标的是长期配置、波段、日内、0DTE、LEAP 还是观察，否则时间框架和触发严格度会错。
- KVN missing、broker needs_review 和 portfolio reconciliation unavailable 不阻止 reduced-scope 流程开始，但会降低动量和持仓风险判断的置信度。

## 确认后我会执行

确认每个标的的 trade_horizon 和 instrument 后，我会读取当前 Active Market Plan，以盘前快速更新的方式输出：今日变化、需要盯的 setup、哪些接近触发、哪些需要暂停或复核。不会写 runtime，不会读取 broker，不会创建真实 automation。

## 安全边界

- 不会生成买卖指令。
- 不会下单、改单、撤单、平仓或批准订单。
- 不会读取 broker，除非用户授权 read-only source。
- 不会写 runtime，除非用户确认 proposed write package。
- 不会创建真实 automation。
