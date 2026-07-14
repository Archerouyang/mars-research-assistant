# Source Routing Boundary

## Scenario

Longbridge stock data selected for authorized prices or broker-adjacent market
data.

## Conclusion

Longbridge stock data selected is not sufficient for policy/news. Selecting
Longbridge for stock data can support market-data reads, but it cannot become
the default source for macro policy, industry news, research thesis, or official
event confirmation.

## Allowed source mix

| source purpose | allowed source mix | what it can change |
| --- | --- | --- |
| S0 official | Fed, Treasury, White House, BLS, BEA, SEC, company IR, exchange calendars | policy facts, official remarks, release status, company facts |
| S1 macrodata | Longbridge macrodata, IBKR/authorized market data, yields, spreads, calendars | macro values, financial conditions, market transmission |
| S2 reputable media | Reuters, AP, Bloomberg, WSJ, FT, CNBC, MarketWatch | news leads and event interpretation after confirmation |
| S3 research | Seeking Alpha, sell-side notes, authorized research, newsletters | thesis/counter-thesis and verification queue inputs |
| broker/account facts | Longbridge or IBKR read-only broker data | positions, executions, order status, account risk |

## Rule

Use the allowed source mix according to source purpose. Do not use a broker,
market-data feed, or macrodata command as the exclusive evidence layer for
macro, policy, industry, or news analysis.
