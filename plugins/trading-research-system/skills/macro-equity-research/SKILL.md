---
name: macro-equity-research
description: Run macro-to-equity trading research covering market-moving policy, Treasury policy, rates and bond yields, equity screening, research-note verification, momentum/watchlist prioritization, and candidate trade idea formation. Use for stock screening, Seeking Alpha-style thesis checks, macro/rates impact analysis, Trump policy filtering, sector selection, and research-backed candidate ranking.
---

# Macro Equity Research

Use this skill to convert current macro/rates information and research claims into Trade Plan Preparation inputs and a Cross-Section Candidate Pool. It should prepare candidates for the Active Market Plan; it should not jump directly to intraday triggers.

Apply this gate before deep research on a specific tradable idea: confirm
`ticker + trade_horizon + instrument`. If any part is missing, provide only a
concise watch-only summary and ask one focused confirmation question; do not
spend the deep-research pass or generate concrete entry/exit levels yet.

## Workflow

1. Use current sources for policy, Treasury/rates/yields, prices, filings, earnings, and market state. When available and authorized, Longbridge `macrodata` can be used for macro and financial-condition reads, while official policy facts still need S0 confirmation.
2. Read shared references as needed:
   - `../trading-research/references/macro-policy-filter.md`
   - `../trading-research/references/macro-data-source-contract.md`
   - `../trading-research/references/research-report-intake.md` when the input is a report, PDF, link, excerpt, Seeking Alpha-style article, or report-discovery request.
   - `../trading-research/references/equity-screening.md`
   - optional external quantitative momentum context only when already
     configured or explicitly provided by the user.
   - `../trading-research/references/price-action-timing.md`
   - `../trading-research/references/portfolio-risk.md`
   - `../trading-research/references/output-templates.md`
3. Treat Seeking Alpha-like articles as thesis inputs, not primary facts. Use short summaries only and verify claims against primary/current sources.
4. When research reports are involved, first produce or consume a `Research Report Digest`, `Claim Ledger`, and `Verification Queue` from `research-report-intake`.
5. Build the Trade Plan Preparation input reads:
   - `Macro Regime`
   - `Financial Conditions`
   - `Policy/Event Risk`
   - `Industry/Sector Strength`
   - `Company Thesis Check`
   - `External Momentum Snapshot` when enabled
6. Each input read must return `read`, `supports`, `pressures`, `blocks`, `evidence`, and `next_check`.
   Macro and financial-condition reads must first show `宏观数据来源状态` and
   `实际宏观指标读数`. Use Longbridge macrodata for macro values when available,
   IBKR market data for price/OHLCV transmission, and official source fallback
   for S0 facts or fallback macro values.
7. Convert the reads into a `Cross-Section Candidate Pool`: candidates worth searching for setup structure.
8. Use external momentum context only from a user-authorized snapshot. The
   plugin does not calculate the model inside this research step and should not
   expose model construction, ranking generation, or backtesting as a v1
   capability.
9. Promote candidates toward the weekly plan only when the next step is clear: higher-timeframe environment check, price-structure check, setup type, trigger zone, invalidation, additional thesis validation, or portfolio-risk review.

## Source Routing Boundary

Choose sources by claim type before turning research into plan impact.
Longbridge `macrodata` can be used for macro and financial-condition reads, but
not as the exclusive source for macro, policy, industry, or news analysis.
Broker/account sources are not news sources; research articles are thesis
inputs, not primary policy or macro facts.

Macro research must not claim a complete macro read unless actual macro values
were read. If Longbridge macrodata, IBKR market data, and official source
fallback are unavailable, output the missing sources and continue only as a
degraded research note.

## Output

Use Chinese Markdown with:

- `事实`
- `假设`
- `Research Report Digest` when research reports are used
- `Claim Ledger` when report claims affect confidence
- `Verification Queue`
- `交易计划准备`
- `宏观数据来源状态`
- `实际宏观指标读数`
- `Macro Regime`
- `Financial Conditions`
- `Policy/Event Risk`
- `Industry/Sector Strength`
- `Company Thesis Check`
- `External Momentum Snapshot`
- `Cross-Section Candidate Pool`
- `多头逻辑 / 空头逻辑`
- `需要校验 / blocks`
- `可转化为 candidate setup 的下一步`
- `动量候选池 / optional external snapshot`
- `组合风险`

Do not rely on stale facts or unsupported analyst claims.
