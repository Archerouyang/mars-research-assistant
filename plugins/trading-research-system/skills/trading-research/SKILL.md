---
name: trading-research
description: Route trading research requests to the right Trading Research System workflow. Use when the user invokes trading-research generally, asks for trading help without naming a specific sub-skill, or needs coordination across weekly market review and next-week planning, daily tracking, intraday scanning, trade review, macro/equity research, portfolio risk, and trading statistics.
---

# Trading Research Router

Use this skill as the general entrypoint for the Trading Research System plugin. Keep it lightweight: choose the most specific sub-skill and follow that workflow.

This is decision support, not automated trading. Do not present outputs as guaranteed returns, personalized financial advice, or certainty. Always separate facts, assumptions, thesis, counter-thesis, invalidation, and risk controls.

## Routing

- Weekly market review, last-week trade review, next-week macro/policy/news/event preview, momentum update, setup discovery:
  use `weekly-trading-plan`.
- Daily premarket/intraday quick market read, macro/policy/news/event update, momentum update, planned opportunity and level tracking:
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

1. `macro-equity-research` when deeper source verification, screening, or macro/policy analysis is needed.
2. `weekly-trading-plan` to synthesize the weekly review and next-week plan.
3. `daily-market-tracking` to update the plan against today's market.
4. `intraday-setup-scan` to classify prepared setups during the session.
5. `portfolio-risk` before increasing or concentrating exposure.
6. `trade-review` after orders/fills and after exits.
7. `trading-stats` after enough closed-trade records exist.

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
