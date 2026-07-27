---
name: price-action
description: 针对用户指定的单一标的和时间框架，生成中文 Markdown 价格结构、关键位、情景与失效条件研究。仅在 OHLCV 可用且质量足够时给出技术结论；不用于基本面、行业或宏观研究。
---

# Price Action

同目录的 `capability.json` 定义本 Skill 的公开交付边界与离线验收场景。

```mars-skill-policy
{"delivery":"markdown_research","forbidden_effects":["fundamentals","industry_analysis","macro_analysis","account_access","broker_write","drive_write","persistent_state"]}
```

只研究一个明确标的与用户指定的时间框架。交付中文 Markdown，包含数据状态、价格结构、
关键位、情景与失效条件，以及数据缺口。结构观察、关键位和情景不是订单、仓位或交易指令。

唯一数据源为 yfinance，且必须显式标为非官方、best-effort 的私人研究数据；它不代表实时、
完整、官方或可再分发的数据。忽略任何其他来源、本地凭据和用户提供的 OHLCV，不询问、
探测、读取、保存或写入任何凭据。

当合格 OHLCV 为 1D 时，可在 Markdown 内嵌静态 SVG 日线图：展示最近 120 根 K 线、成交量、
SMA20/50/200 与已解析的关键位。为让 SMA200 覆盖全部可视区间，yfinance 需要至少 319 根
历史日线；图表与文字必须使用同一份 OHLCV，并标记来源和 as_of。图表不创建 HTML 文件、
浏览器状态或持久化研究状态。

在输出技术结论前，确认 OHLCV 的时间范围适合问题，且具有带时区的时间戳、OHLC、成交量
与复权口径；日线 SVG 还要求至少 319 根历史日线。任一项不足时，停止在“数据状态”和
“数据缺口”：说明原因、来源及 `as_of`，不要输出价格结构、关键位或情景。

无需询问数据源选择，直接进行 yfinance 的最小可用性探测。yfinance 不可用、限流或 OHLCV
不合格时，停止在“数据状态”和“数据缺口”；不得切换到其他数据源，也不能让不合格 OHLCV
通过质量检查。

不要自动加入基本面、行业、宏观、账户、持仓、订单或 Drive 写入；不执行交易，不持久化
研究状态。
