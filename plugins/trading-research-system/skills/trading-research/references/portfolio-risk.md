# Portfolio Risk Exposure

Every new trade should be evaluated against the full book.

## Required Inputs

If the user provides holdings, use them. If not, ask for:

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
