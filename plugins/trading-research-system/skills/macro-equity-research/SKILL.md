---
name: macro-equity-research
description: Run macro-to-equity trading research covering market-moving policy, Treasury policy, rates and bond yields, equity screening, research-note verification, momentum/watchlist prioritization, and candidate trade idea formation. Use for stock screening, Seeking Alpha-style thesis checks, macro/rates impact analysis, Trump policy filtering, sector selection, and research-backed candidate ranking.
---

# Macro Equity Research

Use this skill to convert current macro/rates information and research claims into Trade Plan Preparation inputs and a Cross-Section Candidate Pool. It should prepare candidates for the Active Market Plan; it should not jump directly to intraday triggers.

## Workflow

1. Use current sources for policy, Treasury/rates/yields, prices, filings, earnings, and market state. When available and authorized, Longbridge `macrodata` can be used for macro and financial-condition reads, while official policy facts still need S0 confirmation.
2. Read shared references as needed:
   - `../trading-research/references/macro-policy-filter.md`
   - `../trading-research/references/research-report-intake.md` when the input is a report, PDF, link, excerpt, Seeking Alpha-style article, or report-discovery request.
   - `../trading-research/references/equity-screening.md`
   - `../trading-research/references/price-action-timing.md`
   - `../trading-research/references/portfolio-risk.md`
   - `../trading-research/references/output-templates.md`
3. Treat Seeking Alpha-like articles as thesis inputs, not primary facts. Use short summaries only and verify claims against primary/current sources.
4. When research reports are involved, first produce or consume a `Research Report Digest`, `Claim Ledger`, and `Verification Queue` from `research-report-intake`.
5. Build the five Trade Plan Preparation input reads:
   - `Macro Regime`
   - `Financial Conditions`
   - `Policy/Event Risk`
   - `Industry/Sector Strength`
   - `Company Thesis Check`
6. Each input read must return `read`, `supports`, `pressures`, `blocks`, `evidence`, and `next_check`.
7. Convert the reads into a `Cross-Section Candidate Pool`: candidates worth searching for setup structure.
8. Do not treat the 动量候选池 as implemented in v1. It is a TODO requiring a separate quantitative model, data source, factor definition, ranking rule, and validation process.
9. Promote candidates toward the weekly plan only when the next step is clear: higher-timeframe environment check, price-structure check, setup type, trigger zone, invalidation, or additional thesis validation.

## Output

Use Chinese Markdown with:

- `事实`
- `假设`
- `Research Report Digest` when research reports are used
- `Claim Ledger` when report claims affect confidence
- `Verification Queue`
- `交易计划准备`
- `Macro Regime`
- `Financial Conditions`
- `Policy/Event Risk`
- `Industry/Sector Strength`
- `Company Thesis Check`
- `Cross-Section Candidate Pool`
- `多头逻辑 / 空头逻辑`
- `需要校验 / blocks`
- `可转化为 candidate setup 的下一步`
- `动量候选池 TODO`
- `组合风险`

Do not rely on stale facts or unsupported analyst claims.
