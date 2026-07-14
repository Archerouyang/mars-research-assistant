# Macro / Industry Research Monitor Expected Output

Synthetic expected output for the 2026-07-06 weekly focus fixture. This is
decision support only.

## 结论

- 本次 monitor 只跟踪周度 P0/P1 变量，不重做完整 weekly plan。
- 组合含义：在 Fed minutes / yields 和 AI hardware confirmation 落地前，维持 balanced defensive；不新增高 beta 风险。
- 任何 S3 研报或 Seeking Alpha 观点只能进入 Research Report Intake，不能直接升级为 setup。

## 重点变化

| 优先级 | 变量 | 当前读法 | 影响的持仓/计划 | 动作 |
| --- | --- | --- | --- | --- |
| P0 | FOMC minutes / yields | 等待 minutes 与 10Y/30Y 确认 | QQQ, SOXX, ARM, AMD, MVLL, TSMX | 若 10Y > 4.50% 或 30Y 逼近 5.00%，降低高 beta 新增风险 |
| P0 | ISM Services | 只关注服务价格和增长组合 | QQQ, VOO, SOXX, MU, AMD, ARM, GLW | 服务价格不热才改善 risk-on 条件 |
| P1 | TSMC June revenue | TSMC June revenue 是 TSMX/semis 的直接确认项 | TSMX, AMD, ARM, SOXX, QQQ | 公布后更新 Company Thesis Check |
| P1 | AI hardware / custom chip | 区分 neocloud 压力和 broad AI capex cut | AMD, ARM, MVLL, GLW, TSMX | 只在扩散成 capex 下修时提高组合级风险 |
| P1 | DRAM pricing | DRAM pricing 支持中期 thesis，但短线可能拥挤 | MU/MUU/DRAM | 观察 MU 能否在好消息后企稳 |

## 信源优先级

| 等级 | 用途 | 本 monitor 怎么用 |
| --- | --- | --- |
| S0 official / primary | Fed minutes、TSMC IR、company filings、official macro data | 可以改变 Verification Queue 和 Active Market Plan impact |
| S1 market data / macrodata | 2Y/10Y/30Y、HY OAS、prices、relative strength | 用来确认传导是否发生 |
| S2 reputable financial media | AI hardware、custom chip、DRAM pricing 新闻线索 | 需要 S0/S1 确认后才改变风险预算 |
| S3 research / opinion | Seeking Alpha / sell-side thesis | 只能作为 Research Report Intake 输入 |
| S4 social / rumor | unsourced claims | 默认忽略 |

## 研报/资料线索

| 线索 | source priority | access | plan use |
| --- | --- | --- | --- |
| Fed minutes analysis | S0/S2 | public | macro/rates verification |
| TSMC June revenue release | S0 | public | Company Thesis Check for TSMX / semis |
| AI hardware custom chip article | S2/S3 | public or user-provided | Industry/Sector Strength lead |
| DRAM pricing note | S2/S3 | public or user-provided | MU/MUU/DRAM thesis check |

## Verification Queue

| 优先级 | 需要校验什么 | 首选信源 | 为什么重要 |
| --- | --- | --- | --- |
| P0 | FOMC minutes 是否推高 rate path / term premium | Fed / Treasury yields | 决定高 beta 新增风险是否暂停 |
| P0 | 10Y 是否站上 4.50%，30Y 是否逼近 5.00% | S1 market data / macrodata | 直接影响 QQQ/SOXX/AI hardware multiple |
| P1 | TSMC June revenue 是否确认 AI/HPC demand | TSMC IR | 决定 TSMX/SOXX Company Thesis Check |
| P1 | AI hardware 新闻是否是局部 neocloud 压力还是 broad AI capex cut | S2 media + company checks | 决定组合级风险是否升高 |
| P1 | DRAM/NAND pricing 是否继续支持 MU thesis | S2 industry media / company commentary | 决定 MU/MUU/DRAM 是 thesis support 还是 crowded watch |

## Active Market Plan impact

| 模块 | 影响 | 下一步 |
| --- | --- | --- |
| Macro Regime | watch only until FOMC minutes and yields confirm | 不追第一根高 beta 反弹 |
| Financial Conditions | pressures if 10Y/30Y break higher | 更新 risk posture 和 setup readiness |
| Industry/Sector Strength | supports only if TSMC / AI hardware / DRAM checks confirm | 进入 Trade Plan Preparation，不直接进 setup |
| Company Thesis Check | TSMX, MU, GLW, AMD, ARM, MVLL need source-specific checks | 用 Research Report Intake 管理 S3 研报 claim |

## 需要用户决策

1. 是否允许把这个 monitor 作为 Daily Ops recurring automation。
2. cadence：每天盘前、事件后一次、还是 P0 事件前后各一次。
3. 研报源：只用公开来源，还是允许用户提供 Seeking Alpha / sell-side excerpts。
4. 是否把 monitor 输出写入 `{runtime_dir}/updates/YYYY-MM-DD.md`，还是仅在 chat 中展示。

## 边界

- 不能直接升级为 setup。
- 不绕过 paywall。
- 不把 S3 研报当作已验证事实。
- 不创建、修改或暗示批准真实订单。
