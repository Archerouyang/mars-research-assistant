# Rolling PA Missing Setup Key Input Fixture

User prompt:

```text
做 DRAM/SOXX/QQQ 的滚动盘面分析
```

Available context:

- tickers: DRAM, SOXX, QQQ
- trade_horizon: missing for every ticker
- instrument: missing for every ticker
- formal runtime Active Plan: unavailable
- repo fixture: may contain QQQ/SOXX examples but is forbidden as current plan state
- authorized OHLCV/current prices: unavailable

Constraints:

- Do not read or borrow repo fixture levels.
- Do not generate concrete levels, triggers, invalidations, sizing, or instrument-specific risk advice.
- Ask one focused setup-key confirmation question.
