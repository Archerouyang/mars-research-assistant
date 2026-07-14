# Daily Ops Weekend First Start Input

- User prompt: `周末首次启动，先看看下周。`
- Time: weekend.
- formal runtime available: runtime directory exists at the formal private path.
- startup_status partial: Active Market Plan and today's daily package are
  missing.
- broker source needs_review: no read-only broker status was supplied for this
  run.
- Public/official market and event sources may be used.
- Deterministic public-source fixture reads:
  - US 10Y yield: `4.45%`; pressure threshold: `4.50%`.
  - VIX: `18.2`; stress threshold: `20`.
  - Next-week P0 event: `CPI release`; actual result is not yet available.
  - QQQ/SOXX may be mentioned only as watch-only themes until the setup key is confirmed.
- Constraint: 不写 runtime，不读取 broker，不创建订单。
