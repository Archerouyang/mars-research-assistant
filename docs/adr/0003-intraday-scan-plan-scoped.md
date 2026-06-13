# Intraday scan is scoped to existing trade plans

Intraday setup scanning will only evaluate trade plans already prepared for the current trading day. It will monitor planned tickers, timeframes, trigger conditions, invalidation levels, and setup notes to determine whether a plan is becoming actionable, invalidated, or worth the user's attention.

**Considered Options**

- Scan only the current day's prepared trade plans.
- Scan the entire market for new intraday opportunities.

**Consequences**

- The intraday scanner stays aligned with planned execution instead of becoming a noisy idea generator.
- New opportunity discovery can be added later as a separate module.
- Trade plans must contain enough structured setup criteria for the scanner to evaluate them.
