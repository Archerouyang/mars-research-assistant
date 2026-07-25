---
name: mars-research-assistant
description: Produce one-shot Chinese Macro Regime, Instrument Research, or requested Price Action research with Longbridge-first and portable fallbacks. Use for macro events, company fundamentals, industry/company catalysts, and trade-plan price action.
---

# 火星投研助手

为当前请求交付中文 Markdown，以及在确实有帮助时至多一个自包含 HTML Board。每次运行独立完成；不创建或读取 runtime、计划、缓存、历史、Gallery、manifest、账户、持仓或订单。

## 安全边界

1. 仅研究与决策支持；不创建、修改、取消、提交或暗示批准订单。
2. 不读取或展示账户、持仓、订单、凭据或 token。Longbridge 预检只能返回 CLI 是否存在、授权是否有效两个布尔值。
3. 不编造价格、事件、财报或来源。每个数值和事件附 `source` 与 `as_of`；明确区分事实、推断、风险和数据缺口。
4. Web Search 仅用于发现候选来源。会改变结论的宏观、行业或公司事件必须由官方公告、监管披露、官方日历或公司 IR 页面确认。

## 数据源选择

运行 `scripts/stateless_research_run.py` 的逻辑时，先只读检查 `longbridge auth status --format json`。

- CLI 存在且授权有效：询问用户本次是否使用 Longbridge；用户明确同意才启用。
- 未安装、未授权、权限不足或用户拒绝：直接采用 Portable Profile（yfinance + Web Search/原始来源），不能阻塞研究。
- Longbridge Profile 先批量获取结构化字段；仅缺失、校验失败或语义不等价的字段按批次回退到 yfinance 或官方来源。不得为了交叉比较重复请求完整字段。
- Longbridge CLI 是可选二进制。只有用户明确同意安装或登录时，才提示其使用官方安装与 OAuth 流程；绝不静默安装或登录。

## 意图与交付

### 宏观

先输出 **Macro Event Brief**：未来七天的央行决议、CPI/PCE/PPI、就业、GDP、PMI、重大财政/关税政策、长期美债拍卖，以及最近 24 小时已发生的重大传导事件。

仅当所有冻结字段与时间口径齐全时输出 Macro Regime Board：美国财政部同一发布日期的 2Y/10Y/30Y；`^VIX`、`^VIX3M`；`DX-Y.NYB`、`CL=F`、`GC=F`；以及最近 30 个共同完成交易日的 HYG/LQD、NDX/RUT 折线。缺少任一字段时只给简报和具体缺口，不生成半成品 Board。

### 点名标的

默认只输出 Instrument Research：Overview、Fundamentals、Industry、Events & Catalysts。覆盖身份、业务分部、五季/三完整财年财务趋势、现金流与资产负债、估值、近 30 天行业/公司事件与未来 90 天已知催化。

不默认输出宏观、持仓、对标公司、同业表、OHLCV 或技术分析。经济上不适用为 `N/A`，窗口内无事件为 `none_found`，来源缺失为 `data_gap`。只有身份不唯一或完全没有可用财务报表才阻塞 Board。

### Price Action

仅在用户明确要求趋势、点位、入场、减仓或交易计划时输出。使用同一来源的 120 根已完成、前复权 1D OHLCV，计算 EMA20、EMA50、ATR14、关键位、区域与牛/基准/熊情景。Longbridge 失败才整体切换到 yfinance；不得跨来源拼接 OHLCV 或指标。少于 120 根时只说明历史不足，不输出 Board。

## 视觉与安装

保留 Macro Regime、Instrument Research、Price Action 三类既有视觉语言，但直接交付单个自包含 HTML，不使用 ArtifactPacket、ResearchResult、内容哈希、PNG 导出或持久化工件。

Python 环境只按仓库 README 使用 `uv` 和精确锁定的 `requirements.txt`；不要全局 `pip install`。Longbridge CLI 不属于 Python 依赖。

按需阅读：

- 宏观字段与事件规则：`references/macro-research.md`
- 标的基本面与事件规则：`references/instrument-research.md`
- Price Action 规则：`references/price-action.md`
- 来源、时间和安全规则：`references/safety-and-sources.md`
