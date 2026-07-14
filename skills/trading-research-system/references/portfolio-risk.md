# Portfolio Risk Exposure

Every new trade should be evaluated against the full book.

## Required Inputs

If the user provides holdings or broker-live data, use them. If authorized broker sources are available, prefer a live read-only view for current exposure. If not, ask for:

- broker/account when relevant
- ticker
- direction
- position size or percentage
- cost basis
- time horizon
- stop/invalidation
- options exposure if any
- leverage if any

If holdings are unavailable, make risk comments conditional and say what cannot be assessed.

## Exposure Checks

Review:

- net long/short exposure
- total exposure across broker sources
- broker/account split
- single-name concentration
- sector concentration
- factor exposure: beta, growth, value, momentum, small-cap, quality
- rate sensitivity
- USD and FX sensitivity
- policy sensitivity
- earnings/event clustering
- correlation between positions
- liquidity and gap risk
- max drawdown scenarios

When broker-live data or fixture broker files exist, prefer the current position view for exposure and keep `broker` and `account_id` visible in the output when that does not expose private details unnecessarily. The default view should be total portfolio exposure, then broker/account breakdown.

Before presenting total exposure, read `portfolio_reconciliation`. Do not merge
NAV-only account totals with position-detail snapshots. Show a NAV-only IBKR
result separately as `partial_data`; if Longbridge has detailed positions,
describe Longbridge exposure as confirmed for that source only and the combined
portfolio as `not_confirmed`.

## Scenario Tests

At minimum consider:

- yields rise sharply
- long-end yields fall sharply
- USD strengthens
- risk appetite deteriorates
- inflation reaccelerates
- Fed cuts are delayed
- Treasury issuance pressures duration assets
- policy or tariff shock
- target company misses earnings

## Output

Use a risk table:

- exposure
- current issue
- affected holdings
- severity
- mitigation

Severity labels:

- `High`: can materially damage portfolio or duplicate major macro exposure.
- `Medium`: manageable but should be monitored.
- `Low`: noted but not decision-critical.
