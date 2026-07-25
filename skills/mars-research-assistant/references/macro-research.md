# Macro Regime v1

先交付 Markdown Macro Event Brief，再决定是否可以生成 Board。

## Event Brief

覆盖未来七天的央行决议、CPI/PCE/PPI、就业、GDP、PMI、重大财政或关税政策、长期美债拍卖，和过去 24 小时内明确影响字段的重大事件。每项写明时间、状态（已发生/预期）、传导、`source`、`as_of`。Web Search 发现后必须打开原始来源确认。

## 冻结字段

- 美国财政部同一发布日期的 2Y、10Y、30Y Daily Treasury Par Yield Curve Rates；
- `^VIX`、`^VIX3M` 原始读数；
- `DX-Y.NYB`（DXY）、`CL=F`（WTI）、`GC=F`（COMEX Gold）；
- HYG/LQD 与 NDX/RUT 的最近 30 个共同完成交易日折线。

市场字段截至最近一个完成的美国交易日；财政部保留官方发布日期。VIX/VIX3M、准备金、TGA、ON RRP、z-score 与短周期比率不在范围内。

利率必须使用官方财政部来源。Longbridge 只可替代具有相同已完成日线语义的 VIX、信用与风格数据；否则回退 yfinance。缺少任何冻结字段时，不生成 Board。
