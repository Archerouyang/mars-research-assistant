# Macro 完成会话完整性修复

状态：已确认，待实施。

## Problem Statement

Macro Regime Board 当前接受提供方的 `completed` 声明、预计算 ratio 点和 URL 形状校验。因而它可能将过期、含周末、并非 constituent 交集的市场数据呈现为“30 个共同完成交易日”，也可能将聚合新闻 URL 当作原始事件证据。用户无法据此辨别完整的最新 Macro 结果与看似完整的代理数据。

## Solution

保持一次无状态研究和 `stateless_research_run` 这一唯一外部验收 seam。调用者为每次运行明确给出带时区的研究参考时点与 XNYS 会话日历；数据源交付同源原始 1D 比率腿组，Skill 在本地验证会话、取交集并计算 HYG/LQD、NDX/RUT。事件只有在带确认的原始证据分类时才进入 Markdown 或 Board。任何不满足这些条件的数据都只交付 Event Brief 和具体 blocker；不生成 Macro Regime Board。

## User Stories

1. 作为宏观研究者，我希望本次研究有明确的参考时钟，以便“最新完成交易日”可复核。
2. 作为宏观研究者，我希望 Board 只使用参考时钟之前最近一个已完成 XNYS 会话的数据，以便不会把陈旧市场快照当作当前状态。
3. 作为宏观研究者，我希望 HYG/LQD 与 NDX/RUT 基于各自两条原始 1D 腿的真实共同会话计算，以便相对强弱有可审计的基础。
4. 作为宏观研究者，我希望周末、交易所休市日、重复日期和缺失腿都阻止 Board，以便缺口不会被 `completed` 标记掩盖。
5. 作为 Longbridge 用户，我希望同源腿组优先来自 Longbridge，以便获得稳定且快速的结构化数据。
6. 作为 Portable Profile 用户，我希望一个腿组不完整时整组懒回退到 yfinance，以便不会跨源拼接比率。
7. 作为研究者，我希望每条市场腿、派生比率与 Treasury 字段都保留实际来源与时间，以便区分来源角色。
8. 作为宏观用户，我希望 Event Brief 中的事件均附带受限的原始证据分类和确认状态，以便聚合新闻不会成为结论依据。
9. 作为宏观用户，我希望未来七天与过去二十四小时事件窗口仍基于本次研究参考时点，以便事件与市场观察有同一时间边界。
10. 作为宏观用户，我希望任一时间、会话、来源或事件证据门槛失败时得到具体 blocker，以便能判断应补哪类数据。
11. 作为使用者，我希望最终 HTML 仍是一个直接、自包含的 Board，以便不依赖 runtime、manifest 或 Gallery。
12. 作为维护者，我希望所有成功与失败路径都能通过注入的时钟、日历和字段响应复现，以便不依赖真实账号、实时网络或系统时钟。
13. 作为验收者，我希望看到代表性临时 Board 在应用内浏览器中的实际渲染，以便发现字符串测试无法覆盖的布局或脚本问题。

## Implementation Decisions

- `stateless_research_run` 保持唯一主行为与外部验收 seam；Macro 请求明确携带带时区的 `research_as_of`，并接收一个可注入的 XNYS 会话日历接口。
- **研究参考时点** 是确定最新完成会话、未来七日事件窗口和最近二十四小时窗口的唯一时钟；事件或提供方字段的 `as_of` 不能替代它。
- 每个相对强弱字段接收一个**同源比率腿组**：同一数据源的两条原始 1D 腿序列，且每个观测保留日期、收盘值、完成状态和来源时间。Skill 而非提供方负责与 XNYS 日历求交集、验证 30 个递增不重复的完成会话、确认末日等于最近完成会话，并在通过后计算 ratio 折线。
- 一个腿组的任一腿缺失、语义错误、会话不完整或来源不一致时，该腿组整体按既有批量懒回退规则转交下一个允许来源；不得以不同来源补齐单腿。
- Treasury 继续使用同一官方发布日期的曲线；市场字段、腿组和 Treasury 保持各自的时间口径，且每个输出值显示实际 `source` 与 `as_of`。
- Macro 事件新增 `evidence_kind` 与 `primary_source_confirmed`。允许的证据分类为官方日历、政府或监管披露、官方公告、公司 IR；只有确认的一手证据可显示。Web Search 仅产生候选，不是可接受的事件事实。
- Board 仍只在所有冻结字段和事件/时间/会话门槛通过时生成一个直接自包含 HTML；否则只输出 Event Brief 与 fail-closed blocker。
- 代表性 fixture 交付仅写入调用者的临时目录供人工验收，不形成 runtime、缓存、Gallery 或持久化产物。

## Testing Decisions

- 以 `stateless_research_run` 的外部结果为唯一主要测试 seam；注入 `research_as_of`、XNYS 日历、Longbridge/yfinance/官方字段响应和事件证据，而不测试真实网络或账号。
- 成功路径断言：最近完成会话、四腿原始序列的 30 会话交集、计算后的两条 ratio、逐项来源/时间、Event Brief 与一个自包含 Board。
- 失败路径至少覆盖：过期快照、周末或休市日、重复或无序日期、少于 30 会话、任一 constituent 缺失、跨源腿、末日不等于最近完成会话、无效 `research_as_of`、非官方 Treasury 和未确认/聚合事件来源；每项都断言无 Board 及具体 blocker。
- 覆盖 Longbridge 腿组完整时不请求回退，以及单腿不完整时只对整个腿组懒回退，不为交叉比较重复请求。
- 保留现有自包含性、无 manifest/Gallery/runtime 和无私有 broker 数据测试；在临时目录生成一份代表性 Board，并以应用内浏览器进行人工视觉验收。
- 从干净环境运行隔离安装 smoke 与标准 `uv` 验证；所有自动化测试使用 fixture，不访问实际市场、账户、持仓、订单、凭据或 token。

## Out of Scope

- 真实 Longbridge、yfinance、Web Search 或 Treasury 网络适配器的实现与权限测试。
- 新的 Macro 字段、跨供应商价格比较、盘中数据、持久化、runtime、Gallery、订单或账户读取。
- Instrument Research Board 与 Price Action Board 的数据契约或视觉改动。
- 自动化浏览器截图矩阵或将人工视觉验收替换为像素比较。

## Further Notes

- 本规格是 #95 代码审查发现的完成会话、原始证据和人工渲染验收缺口的修复边界；在通过前，#95 不应被视为完整交付。
- `CONTEXT.md` 的研究参考时点、共同完成市场会话、同源比率腿组与原始事件证据是本规格的术语来源；ADR 0016 记录了 Skill 拥有最终会话验证责任的取舍。
