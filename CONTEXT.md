# 火星投研助手

## Domain language

**无状态研究运行**：只获取当前请求所需字段，直接交付 Markdown 与可选的一个自包含 HTML Board；没有 runtime、计划、缓存、历史或工件注册表。

**数据源模式**：每次运行确定一次。Longbridge Profile 只有在 CLI 存在、授权有效且用户明确选择时使用；否则为 Portable Profile（yfinance + Web Search/原始来源）。模式不改变字段语义。

**批量懒回退**：主源按数据集批量请求并校验，仅把缺失或失败字段交给回退来源。字段可能混合来源，但每项必须带 `source` 与 `as_of`；不进行交叉比较。

**研究参考时点**：一次无状态研究由调用者明确传入的带时区时钟。它是判断最近已完成 XNYS 会话的唯一基准，不从事件或市场字段的 `as_of` 反推。
_Avoid_: 事件 `as_of`、提供方行情时间

**Macro Event Brief**：宏观运行始终最先交付的 Markdown，覆盖未来七日关键日历事件与最近 24 小时重大传导事件。

**Macro Regime Board**：只在 Treasury 2Y/10Y/30Y、VIX、VIX3M、DXY、WTI、Gold、HYG/LQD、NDX/RUT 和时间校验齐全时生成。HYG/LQD 与 NDX/RUT 展示 30 个共同完成交易日折线；不包含 VIX/VIX3M、TGA、ON RRP、准备金或 z-score。

**共同完成市场会话**：HYG、LQD、NDX 与 RUT 四腿均有已完成 1D 观测、且位于同一注入的 XNYS 会话日历中的交易日；其最后一日必须等于本次市场参考日。比率在该交集后计算，数据源不是会话完整性的权威。
_Avoid_: 提供方 `completed` 标记、预计算比率日期

**同源比率腿组**：一个相对强弱字段内两条原始腿的完整 1D 序列，来自同一数据源并作为不可拆分的懒回退单位。Skill 只在腿组内部取共同会话并计算比率，不能拼接不同来源的腿。
_Avoid_: 跨源腿拼接、单条预计算比率

**Instrument Research Board**：点名标的默认的 Overview、Fundamentals、Industry、Events & Catalysts 四视图。没有宏观、持仓、同行、价格或 setup。`N/A` 是经济上不适用，`none_found` 是窗口内无重大事件，`data_gap` 是来源缺失。

**Price Action Board**：只在用户明确询问趋势、点位、入场、减仓或交易计划时生成。它独占同一来源的 120 根完成、前复权 1D OHLCV，以及 EMA20、EMA50、ATR14、关键位、情景和失效条件。

**原始事件证据**：可进入研究结果的事件必须携带 `official_calendar`、`government_or_regulatory_filing`、`official_announcement` 或 `company_ir` 的 `evidence_kind`，并有 `primary_source_confirmed=true`。本次运行还注入一手来源登记器，它只批准已登记的“事件标题、类别、带时区时间、证据分类 + 精确原始 URL”组合。Web Search 仅发现候选资料，不能成为事件事实。
_Avoid_: 聚合新闻 URL、仅校验 `https` 的来源、未登记或与事件不匹配的一手来源

**安全边界**：不创建、修改、取消或提交订单；不读取账户、持仓、订单、凭据或 token。Longbridge 预检只暴露 CLI/授权的布尔状态。
