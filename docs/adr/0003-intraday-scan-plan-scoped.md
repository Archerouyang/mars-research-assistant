# Intraday scan is scoped to Active Market Plan setups

Intraday setup scanning will only evaluate setup-level entries already present in the Active Market Plan, current watchlist, or prepared setup files. It will monitor planned symbols, instruments, timeframes, trigger conditions, invalidation levels, and setup notes to determine whether a setup is active, approaching, triggered, invalidated, completed, or worth the user's attention.

**Considered Options**

- Scan only current Active Market Plan setups and prepared setup files.
- Scan the entire market for new intraday opportunities.

**Consequences**

- The intraday scanner stays aligned with planned setup execution instead of becoming a noisy idea generator.
- New opportunity discovery can be added later as a separate module.
- Setups must contain enough structured criteria for the scanner to evaluate them.
