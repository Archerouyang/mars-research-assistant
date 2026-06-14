---
name: trading-research
description: Route trading research requests to the right Trading Research System workflow. Use when the user invokes trading-research generally, asks for trading help without naming a specific sub-skill, or needs coordination across weekly planning, daily tracking, intraday scanning, trade review, macro/equity research, portfolio risk, and trading statistics.
---

# Trading Research Router

Use this skill as the general entrypoint for the Trading Research System plugin. Keep it lightweight: choose the most specific sub-skill and follow that workflow.

This is decision support, not automated trading. Do not present outputs as guaranteed returns, personalized financial advice, or certainty. Always separate facts, assumptions, thesis, counter-thesis, invalidation, and risk controls.

## Routing

- Weekly plan, next-week prep, initial trade ideas, priority watchlist:
  use `weekly-trading-plan`.
- Current market read, premarket/market-hours update, dynamic tracking:
  use `daily-market-tracking`.
- Several active plans, multiple tickers/charts, setup status:
  use `intraday-setup-scan`.
- Actual trade record, IBKR trade facts, post-order note, post-exit review:
  use `trade-review`.
- Macro policy, rates/yields, research-note verification, stock screening:
  use `macro-equity-research`.
- Holdings, sizing, portfolio exposure, risk budget, trade impact:
  use `portfolio-risk`.
- Win rate, R-multiple, setup performance, mistake tags, system review:
  use `trading-stats`.

If a request spans multiple workflows, run them in the natural order:

1. `macro-equity-research`
2. `weekly-trading-plan`
3. `daily-market-tracking`
4. `intraday-setup-scan`
5. `portfolio-risk`
6. `trade-review`
7. `trading-stats`

## Shared Resources

Detailed domain rules remain in:

- `references/macro-policy-filter.md`
- `references/equity-screening.md`
- `references/price-action-timing.md`
- `references/intraday-setup-scan.md`
- `references/interactive-trade-review.md`
- `references/trade-journal.md`
- `references/portfolio-risk.md`
- `references/output-templates.md`

Shared scripts and templates remain in the plugin root:

- `../../scripts/`
- `../../assets/templates/`

## Output Style

Use Chinese unless the user asks otherwise. Prefer Markdown notes suitable for Obsidian.

Use clear labels when applicable:

- `事实`
- `假设`
- `多头逻辑`
- `空头逻辑`
- `失效条件`
- `择时`
- `组合风险`
- `下一步`

When a task needs current facts, use browsing or authorized connectors. Do not rely on memory for policy, market data, yields, company facts, or current prices.
