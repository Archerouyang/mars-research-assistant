# Macro Policy Filter

The user's macro focus is narrow: ignore political noise unless it changes asset pricing.

## Priority Topics

- Trump policy and election/presidential news that affects taxes, tariffs, spending, regulation, energy, trade, China policy, immigration, or Fed independence.
- U.S. Treasury policy: refunding, issuance mix, buybacks, TGA, bills vs coupons, deficit financing, debt ceiling, and Treasury market functioning.
- Rates: Fed path, inflation, labor data, real rates, financial conditions, rate-volatility.
- Bond yields: 2Y, 10Y, 30Y, yield curve, term premium, credit spreads.
- Liquidity: RRP, bank reserves, dollar liquidity, QT/QE, funding stress.

## Source Priority

Rank every macro/policy/news input by evidence quality before it can affect the plan:

- `S0 official / primary`: White House, U.S. Treasury, Federal Reserve, BLS, BEA, CBO, FRED, TreasuryDirect, SEC filings, company IR, exchange calendars. Use these to confirm facts, releases, policy status, holidays, and company-specific claims.
- `S1 market data / broker / calendar`: IBKR or other authorized broker feeds, exchange data, Treasury auction calendars, futures/ETF prices, yield curves, volatility indexes, earnings calendars. Use these to confirm current market transmission.
- `S2 reputable financial media`: Reuters, AP, Bloomberg, WSJ, FT, MarketWatch, CNBC, and similar outlets. Treat these as leads unless the report cites or links primary evidence.
- `S3 research / opinion`: Seeking Alpha, sell-side notes, independent research, newsletters, Substack, podcasts, and analyst commentary. Use for thesis generation and counterarguments, not as proof of policy facts.
- `S4 social / rumor / unsourced commentary`: X posts, forum claims, viral clips, and unsourced summaries. Ignore unless confirmed by `S0` or strong `S1/S2` evidence.

Use media and research reports as leads only. Verify policy status:

- enacted
- officially announced
- proposed
- campaign rhetoric
- media speculation

## Transmission Path

Every macro claim should state the chain:

```text
policy or data -> rates/liquidity/USD/sector -> earnings or valuation -> ticker impact
```

If that chain is weak, say so and downgrade confidence.

## Trade Plan Preparation Output

This reference feeds three Trade Plan Preparation input reads:

- `Macro Regime`: growth, inflation, Fed path, USD, oil, liquidity, and broad risk-on/risk-off state.
- `Financial Conditions`: 2Y, 10Y, 30Y, real yields, credit spreads, VIX, USD, funding stress, and liquidity pressure.
- `Policy/Event Risk`: White House / Trump policy, Treasury/fiscal policy, tariffs, Fed independence, auctions, FOMC, energy shocks, and major event windows.

For each read, output:

- `read`
- `supports`
- `pressures`
- `blocks`
- `evidence`
- `next_check`

Do not produce a standalone macro report when the task is trade plan preparation. The output should explain which themes or symbols can enter the Cross-Section Candidate Pool and which are blocked.

## Output Rules

- Ignore news that does not affect rates, liquidity, fiscal path, regulation, earnings expectations, or risk appetite.
- Separate signal from noise.
- Include dates for policy/data releases.
- Flag macro assumptions that would invalidate the equity thesis.
