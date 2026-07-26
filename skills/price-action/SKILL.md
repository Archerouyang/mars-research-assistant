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

在输出技术结论前，确认 OHLCV 的时间范围适合问题，且具有带时区的时间戳、OHLC、成交量
与复权口径。任一项不足时，停止在“数据状态”和“数据缺口”：说明原因、来源及 `as_of`，
不要输出价格结构、关键位或情景。

优先使用用户提供的合格 OHLCV。若用户已在本地私密配置 FMP 且目标符号与权限覆盖 EOD，
可进行最小可用性/权限探测后将其作为可选 EOD 增强；不得索取、回显、保存或写入凭据。
FMP 未配置、未授权或限流时，明确标记状态并降级，不影响其他 Skill。公开数据候选（包括
yfinance/Yahoo）只能标为非官方、best-effort 的私人研究数据；它不代表实时、完整、官方
或可再分发的数据，也不能让不合格 OHLCV 通过质量检查。

不要自动加入基本面、行业、宏观、账户、持仓、订单或 Drive 写入；不执行交易，不持久化
研究状态。
