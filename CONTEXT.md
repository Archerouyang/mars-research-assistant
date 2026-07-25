# 火星投研助手

## Domain language

**无状态研究运行**：只获取当前请求所需字段，直接交付 Markdown 与可选的一个自包含 HTML Board；没有 runtime、计划、缓存、历史或工件注册表。

**数据源模式**：每次运行确定一次。Longbridge Profile 只有在 CLI 存在、授权有效且用户明确选择时使用；否则为 Portable Profile（yfinance + Web Search/原始来源）。模式不改变字段语义。

**批量懒回退**：主源按数据集批量请求并校验，仅把缺失或失败字段交给回退来源。字段可能混合来源，但每项必须带 `source` 与 `as_of`；不进行交叉比较。

**Macro Event Brief**：宏观运行始终最先交付的 Markdown，覆盖未来七日关键日历事件与最近 24 小时重大传导事件。

**Macro Regime Board**：只在 Treasury 2Y/10Y/30Y、VIX、VIX3M、DXY、WTI、Gold、HYG/LQD、NDX/RUT 和时间校验齐全时生成。HYG/LQD 与 NDX/RUT 展示 30 个共同完成交易日折线；不包含 VIX/VIX3M、TGA、ON RRP、准备金或 z-score。

**Instrument Research Board**：点名标的默认的 Overview、Fundamentals、Industry、Events & Catalysts 四视图。没有宏观、持仓、同行、价格或 setup。`N/A` 是经济上不适用，`none_found` 是窗口内无重大事件，`data_gap` 是来源缺失。

**Price Action Board**：只在用户明确询问趋势、点位、入场、减仓或交易计划时生成。它独占同一来源的 120 根完成、前复权 1D OHLCV，以及 EMA20、EMA50、ATR14、关键位、情景和失效条件。

**事件取证层级**：Web Search 仅发现候选资料；重大宏观、行业或公司事实必须用官方、监管、官方日历或公司 IR 原始来源确认。

**安全边界**：不创建、修改、取消或提交订单；不读取账户、持仓、订单、凭据或 token。Longbridge 预检只暴露 CLI/授权的布尔状态。
