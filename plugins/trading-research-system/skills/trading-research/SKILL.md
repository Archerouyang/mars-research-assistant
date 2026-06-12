---
name: trading-research
description: Run a disciplined trading and investment research workflow covering market-moving macro policy, Treasury policy, rates and bond yields, equity screening, research-note verification, Al Brooks-style price action timing, and portfolio risk exposure. Use when the user asks for stock screening, trading research, macro-to-equity analysis, buy/sell timing, position review, portfolio risk, or explicitly invokes trading-research.
---

# Trading Research

Use this skill to help the user research trading ideas, screen stocks, validate market narratives, time entries/exits, and review portfolio risk.

This is a decision-support workflow. Do not present outputs as guaranteed returns, personalized financial advice, or certainty. Always separate facts, assumptions, thesis, counter-thesis, invalidation, and risk controls.

## Workflow

1. Clarify the research target only when needed.
   - If the user gives a ticker, theme, industry, watchlist, or portfolio, proceed.
   - If the user asks for concrete trade timing without time horizon, allowed instruments, account constraints, or current holdings, state the missing assumptions and produce a research memo instead of a direct trade instruction.

2. Use current sources for time-sensitive facts.
   - You must browse or use available live-data tools for policy, news, yields, prices, financial statements, valuation, earnings, ratings, analyst commentary, and market state.
   - Prefer primary sources. Use market commentary and Seeking Alpha-like articles as thesis inputs, not as facts.
   - Cite sources and dates in the final output.

3. Apply the research stack in this order:
   - Macro policy filter.
   - Rates, bond yields, liquidity, and factor impact.
   - Equity screening and thesis validation.
   - Price action timing.
   - Portfolio risk exposure.

4. Load only the references needed for the task:
   - For macro/policy/rates tasks, read `references/macro-policy-filter.md`.
   - For stock screening, research-note validation, or company analysis, read `references/equity-screening.md`.
   - For entry/exit timing, chart interpretation, or trade setup classification, read `references/price-action-timing.md`.
   - For holdings, sizing, correlation, or portfolio risk, read `references/portfolio-risk.md`.
   - For final formatting, read `references/output-templates.md`.

5. For Seeking Alpha or similar sources:
   - If content is publicly available, summarize only short relevant claims and cite the page.
   - If content is paywalled or unavailable, ask the user to provide excerpts or links they are authorized to use.
   - Do not quote large portions of copyrighted research.
   - Cross-check author claims against company filings, investor relations, official statistics, and current market data.

6. For Al Brooks-style price action:
   - Use high-level concepts only: trend, trading range, breakout, failed breakout, pullback, second entry, reversal attempt, measured move, risk/reward.
   - Do not claim a pattern guarantees an outcome.
   - Avoid stale chart conclusions. Use current chart data or ask the user for the chart/timeframe.

7. Finish with a compact action-oriented memo:
   - Research conclusion.
   - What is verified vs assumed.
   - Best long case and best short case.
   - Candidate ranking when screening.
   - Invalidation and risk controls.
   - Portfolio exposure impact.
   - Next research steps.

## Default Output Style

Use Chinese unless the user asks otherwise. Prefer Markdown notes suitable for Obsidian.

Use clear labels:

- `事实`
- `假设`
- `多头逻辑`
- `空头逻辑`
- `失效条件`
- `择时`
- `组合风险`
- `下一步`

## Safety Boundaries

- Do not tell the user that a trade is safe, certain, guaranteed, or risk-free.
- Do not ignore portfolio exposure, downside, liquidity, event risk, or position sizing.
- Do not use unsupported live facts from memory.
- Do not rely on one author, article, or social-media post as the thesis.
- Do not provide tax, legal, or regulated investment advice.
