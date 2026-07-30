# 技术面分析参考

## 数据质量与失败关闭

- 只允许一次 yfinance 扩大历史窗口重试；可剔除位于末尾的一根未完成日线，不插值、合成、
  调换顺序或切换来源。
- 输出结论前必须为 `1D`、带时区并严格递增、明确为 adjusted，且每根均有有限 OHLCV、正
  成交量和一致价格边界；剔除未完成日线后至少 319 根。
- 质量门失败时只原子写出数据状态与数据缺口 `analysis.md`，不生成图表、`evidence.json` 或
  技术结论。

## 确定性证据与情景

SMA20/50/200、ATR14、趋势分类和关键位均由脚本确定性计算。关键位由确认 swing high/low
按 `0.5 × ATR14` 聚类，再按触碰次数、最近确认时间和距最新收盘价排序；每侧最多两个，缺失
时才明确标记为 120 日高低点 fallback。每个关键位保留 `method`、`lookback`、`anchor_dates`、
`touches`、`price`。

`evidence.json` 先记录最新收盘相对三条均线的距离、五根日线的均线方向、20/60/120 日收益、
ATR 和成交量、120 日回撤及关键位距离。Markdown/HTML 只能解释或展示同一数据。多头、震荡、
空头情景分别写支持条件、有利/不利表现、触发与失效条件；不输出概率、评分或伪置信度。

## 图表、背景与安全

临时 `chart.html` 内嵌固定版本 TradingView Lightweight Charts 5.2.0 和证据数据，不访问 CDN、
不要求 Node/npm、不刷新行情、不发起 fetch/XHR/WebSocket，也不使用浏览器持久状态。它包含
symbol、source、timezone、as_of、adjustment、bars_used、`evidence_id` 和关键位 provenance，
尽力在 24 小时后清理。

市场快照背景是非阻塞的：同批次可直接使用，外部背景按目标市场时区默认 24 小时有效；缺失或
无效时明确“仅基于技术面证据”并继续。背景只能解释共振或冲突，不能改变 `evidence_id`、图表、
指标或关键位。
