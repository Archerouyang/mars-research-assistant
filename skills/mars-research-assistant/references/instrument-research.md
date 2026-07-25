# Instrument Research

For a user-named ticker, the default package includes industry events,
fundamentals, catalysts, valuation, counter-thesis, and 4H Price Action. The
4H PA component uses the frozen standalone Board; the other sections are concise
Markdown. Do not require Holdings Display first, and honor any user request that
explicitly narrows this package.

An instrument thesis requires four evidence families:

1. industry structure and peers;
2. company fundamentals and valuation;
3. events, catalysts, and market reaction;
4. market, liquidity, volatility, and product-path data.

Flows are supporting evidence, not proof of a fundamental claim. Price Action
owns timing and invalidation, not the whole thesis. Keep a compact claim ledger
and verification queue when unresolved claims can change the decision.

For leveraged, inverse, option, or path-dependent products, distinguish the
underlying thesis from the product's reset, decay, liquidity, gap, and convexity
risk.

Broker-backed price and OHLCV data use IBKR only. Company fundamentals and
events may use issuer filings, official releases, and directly opened verified
Web sources. Do not start this package from a holdings display unless the user
names the instrument or explicitly accepts the proposed next step.

Published Alpha inputs remain read-only supporting evidence through
`scripts/alpha_leaderboard_adapter.py` and
`scripts/analysis_delta_adapter.py`. They do not mutate rankings, promote a
candidate to a setup, or replace primary-source verification.
