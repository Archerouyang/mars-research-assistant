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
   - For trade plans, trade records, reviews, or system statistics, read `references/trade-journal.md`.
   - For daily actual trade review intake or journal completion, read `references/interactive-trade-review.md`.
   - For final formatting, read `references/output-templates.md`.

5. Use bundled scripts when structured CSV input is available:
   - For holdings or exposure files, run `scripts/portfolio_risk.py`.
   - For candidate/watchlist files, run `scripts/watchlist_score.py`.
   - To create `data/daily/YYYY-MM-DD/`, run `scripts/init_daily.py`.
   - For closed-trade statistics, run `scripts/trade_stats.py`.
   - To append a completed review section to `reviews.md`, run `scripts/append_review.py`.
   - Use templates in `assets/templates/` when the user wants a data-capture format.
   - Treat script output as arithmetic support, not a substitute for judgment or current-data verification.

6. For Seeking Alpha or similar sources:
   - If content is publicly available, summarize only short relevant claims and cite the page.
   - If content is paywalled or unavailable, ask the user to provide excerpts or links they are authorized to use.
   - Do not quote large portions of copyrighted research.
   - Cross-check author claims against company filings, investor relations, official statistics, and current market data.

7. For Al Brooks-style price action:
   - Use high-level concepts only: trend, trading range, breakout, failed breakout, pullback, second entry, reversal attempt, measured move, risk/reward.
   - Do not claim a pattern guarantees an outcome.
   - Avoid stale chart conclusions. Use current chart data or ask the user for the chart/timeframe.

8. Finish with a compact action-oriented memo:
   - Research conclusion.
   - What is verified vs assumed.
   - Best long case and best short case.
   - Candidate ranking when screening.
   - Invalidation and risk controls.
   - Portfolio exposure impact.
   - Next research steps.

## Interactive Trade Review Mode

When the user wants to record actual trades, complete daily trading records, or review a trade, switch to interactive trade review mode:

1. Read `references/interactive-trade-review.md`.
2. Ask one question at a time.
3. Map each answer to `trades.csv` fields and a `reviews.md` section.
4. Compare against `trade-plans.csv` when a matching plan exists.
5. Do not write final records until the key fields are resolved and the user confirms.

Key fields to resolve include entry reason, market background, signal bar, auxiliary signal, confidence, risk plan, exit result, mistake tag, and lesson.

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

## Bundled Data Templates

- `assets/templates/holdings.csv`: portfolio risk input.
- `assets/templates/watchlist.csv`: candidate scoring input.
- `assets/templates/trade-plans.csv`: planned trades and intraday setup-scan input.
- `assets/templates/intraday-watchlist.csv`: plan-scoped intraday setup scan list.
- `assets/templates/trades.csv`: actual trade records.
- `assets/templates/reviews.md`: daily review notes.
- `assets/templates/research-note-log.csv`: research-note validation log.
- `assets/templates/daily-macro-checklist.md`: daily macro policy checklist.
