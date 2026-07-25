# Price Action v1

仅响应明确的趋势、点位、入场、减仓或交易计划请求。使用至少 120 根已完成 1D 前复权 OHLCV，生成 EMA20、EMA50、ATR14、关键支撑/阻力、区域、当前结构、牛/基准/熊情景和失效条件。

Longbridge 使用前复权日线；缺口回退 yfinance `auto_adjust=True`。整条 OHLCV 和全部派生指标必须来自同一来源。禁止 4H、未完成 K 线、跨来源拼接和默认技术分析。历史不足 120 根时不生成 Board。
