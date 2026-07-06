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
- `S1 market data / broker / macrodata / calendar`: Longbridge `macrodata`, IBKR or other authorized broker feeds, exchange data, Treasury auction calendars, futures/ETF prices, yield curves, volatility indexes, earnings calendars. Use these to confirm current macro values, financial conditions, and market transmission.
- `S2 reputable financial media`: Reuters, AP, Bloomberg, WSJ, FT, MarketWatch, CNBC, and similar outlets. Treat these as leads unless the report cites or links primary evidence.
- `S3 research / opinion`: Seeking Alpha, sell-side notes, independent research, newsletters, Substack, podcasts, and analyst commentary. Use for thesis generation and counterarguments, not as proof of policy facts.
- `S4 social / rumor / unsourced commentary`: X posts, forum claims, viral clips, and unsourced summaries. Ignore unless confirmed by `S0` or strong `S1/S2` evidence.

Use media and research reports as leads only. Verify policy status:

- enacted
- officially announced
- proposed
- campaign rhetoric
- media speculation

Longbridge `macrodata` can speed up broad macro indicator queries, including
rates, yields, inflation, labor, liquidity, credit, FX, commodities, and
financial-condition reads, but it should not replace S0 sources for policy
facts, official speech text, release status, or legal/regulatory changes.

## Source Routing Boundary

Choose sources by claim type before using any evidence in the plan. Source
selection is scoped to the source purpose; selecting one connector for one
purpose must not make it the default evidence layer for unrelated claims.

| Source purpose | Allowed source class | What it can affect | Boundary |
| --- | --- | --- | --- |
| official policy facts | S0 official / primary | policy status, official remarks, releases, legal/regulatory facts | Macro policy facts require S0 |
| market data / macrodata | S1 market data / broker / macrodata / calendar | rates, yields, prices, VIX, spreads, macro values, inflation, labor, liquidity, credit, FX, commodities, event timing | Longbridge `macrodata` is S1 macro/financial data |
| news leads | S2 reputable financial media | headline triage, policy interpretation leads, industry events | Industry news leads require S2 or authorized research |
| research thesis | S3 research / opinion | thesis, counter-thesis, valuation debate, report leads | verify against S0/S1/S2 before changing risk budget |
| broker/account facts | read-only broker source | positions, executions, order status, account risk | Longbridge broker or market data is not a news source |

Selecting Longbridge for stock data does not make Longbridge the default source for macro, policy, industry, or news analysis. Longbridge broker or market data
is not a news source, and Longbridge `macrodata` is not a policy fact source.
Do not use one connector as the exclusive evidence layer.

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
