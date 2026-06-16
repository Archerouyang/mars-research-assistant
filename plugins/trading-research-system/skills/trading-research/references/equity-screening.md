# Equity Screening

Use this reference for stock screens, company analysis, and research-note validation.

## Screening Dimensions

Rank candidates using:

- Macro fit: rates, USD, liquidity, fiscal policy, sector regulation.
- Industry structure: cycle, competition, pricing power, policy beneficiaries/losers.
- Company quality: revenue growth, margins, free cash flow, balance sheet, management guidance.
- Valuation: historical range, peer comparison, growth-adjusted valuation, downside multiple.
- Catalyst: earnings, guidance, product cycle, buybacks, M&A, index events, policy changes.
- Risk: regulatory, leverage, estimate cuts, valuation compression, liquidity, event risk.
- Technical state: trend, range, breakout, failed breakout, pullback quality.

## Research-Note Handling

When using Seeking Alpha or similar sources:

1. Identify author, date, stance, rating/target if available.
2. Extract the core thesis and key evidence.
3. Mark what is author opinion vs reported fact.
4. Validate claims against primary data:
   - SEC filings
   - earnings releases
   - investor presentations
   - conference call transcripts
   - official macro data
   - current market prices and valuation data
5. Find the best counterargument.
6. Do not quote long passages.

## Candidate Ranking

For screens, output a table with:

- ticker
- company
- thesis
- macro sensitivity
- valuation status
- catalyst
- key risk
- timing condition
- confidence
- next check

Use confidence labels:

- `High`: facts and setup align, remaining uncertainty is manageable.
- `Medium`: thesis is plausible but key validation remains.
- `Low`: mostly watchlist or speculative.

## Trade Plan Preparation Output

This reference feeds two Trade Plan Preparation input reads:

- `Industry/Sector Strength`: sector leadership, breadth, relative strength, rotation, policy beneficiaries/losers, and industry-level risk.
- `Company Thesis Check`: verified company thesis/counter-thesis, valuation, catalyst, earnings/guidance, balance sheet, and disconfirming facts.

For each read, output:

- `read`
- `supports`
- `pressures`
- `blocks`
- `evidence`
- `next_check`

The result should feed the Cross-Section Candidate Pool. Do not promote a ticker into the Setup Pool unless higher-timeframe regime, strategy bias, price structure, trigger zone, invalidation, risk context, and next check are clear.

## Rejection Criteria

Reject or downgrade candidates when:

- the thesis depends on stale data
- upside is already crowded and priced
- downside invalidation is unclear
- liquidity is poor
- the trade duplicates existing portfolio exposure
- macro condition contradicts the company thesis
