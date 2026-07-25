# Macro Regime v1

先交付 Markdown Macro Event Brief，再决定是否可以生成 Board。

## Event Brief

覆盖未来七天的央行决议、CPI/PCE/PPI、就业、GDP、PMI、重大财政或关税政策、长期美债拍卖，和过去 24 小时内明确影响字段的重大事件。每项写明时间、状态（已发生/预期）、传导、`evidence_kind`、`primary_source_confirmed`、`source`、`as_of`。

只有 `official_calendar`、`government_or_regulatory_filing`、`official_announcement` 或 `company_ir` 是可展示的 `evidence_kind`，且 `primary_source_confirmed` 必须为 `true`。每次 Macro 运行还须注入一手来源登记器；它只批准已登记的“证据分类 + 精确原始 URL”组合。Web Search 与聚合新闻只可用于发现候选；它们不能单独成为事件事实。分类缺失、来源未确认、未登记 URL、聚合证据或无效时间都会给出 blocker，并抑制整个 Board。

人工视觉验收时，在调用者新建的临时目录写入一份纯合成代表性 Board：

```bash
uv run python scripts/macro_fixture_board.py --output-dir /absolute/temporary/directory
```

该命令只创建 `research-brief.html`，拒绝覆盖已有文件；它不读取实时提供方，也不会创建 runtime、缓存、Gallery 或持久化研究工件。

## 冻结字段

- 美国财政部同一发布日期的 2Y、10Y、30Y Daily Treasury Par Yield Curve Rates；
- `^VIX`、`^VIX3M` 原始读数；
- `DX-Y.NYB`（DXY）、`CL=F`（WTI）、`GC=F`（COMEX Gold）；
- HYG/LQD 与 NDX/RUT 的最近 30 个共同完成交易日折线。

每次 Macro 运行显式传入带时区的 `research_as_of` 与 XNYS 会话日历；市场字段和折线必须截至该时点前最近一个完成的美国交易日，财政部保留官方发布日期。VIX/VIX3M、准备金、TGA、ON RRP、z-score 与短周期比率不在范围内。

HYG/LQD 与 NDX/RUT 各自由同一来源的两条原始 1D 腿序列计算。Skill 以 XNYS 日历取交集，验证最近 30 个完成会话和末日，再计算比率；任一腿缺失、跨源或会话无效时，整组才可回退到 yfinance，不能拼接单腿。

利率必须使用官方财政部来源。Longbridge 只可替代具有相同已完成日线语义的 VIX、信用与风格数据；否则回退 yfinance。缺少任何冻结字段时，不生成 Board。
