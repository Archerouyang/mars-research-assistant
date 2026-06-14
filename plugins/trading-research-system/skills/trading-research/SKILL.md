---
name: trading-research
description: Route trading research requests to the right Trading Research System workflow. Use when the user invokes trading-research generally, asks for trading help without naming a specific sub-skill, or needs coordination across Active Market Plan updates, weekly deep updates, daily quick updates, intraday setup scanning, trade review, broker data reconciliation, automations, macro/equity research, portfolio risk, and trading statistics.
---

# Trading Research Router

Use this skill as the general entrypoint for the Trading Research System plugin. Keep it lightweight: choose the most specific sub-skill and follow that workflow.

This is decision support, not automated trading. Do not present outputs as guaranteed returns, personalized financial advice, or certainty. Always separate facts, assumptions, thesis, counter-thesis, invalidation, and risk controls.

## Routing

- Active Market Plan initialization or deep update with last-week trade review, macro/policy/news/event preview, momentum rebuild, and setup discovery:
  use `weekly-trading-plan`.
- Daily quick update against `market-plan.md`: macro/policy/news/event delta, momentum change, setup status changes, and level updates:
  use `daily-market-tracking`.
- Several active setups, multiple tickers/charts, trigger checks, and attention priority:
  use `intraday-setup-scan`.
- Actual trade record, broker execution facts, post-order note, post-exit review:
  use `trade-review`.
- Macro policy, rates/yields, research-note verification, stock screening:
  use `macro-equity-research`.
- Holdings, sizing, portfolio exposure, risk budget, trade impact:
  use `portfolio-risk`.
- Win rate, R-multiple, setup performance, mistake tags, system review:
  use `trading-stats`.
- Automation design, recurring brief, scheduled Active Market Plan update, or monitor:
  read `references/automation-contract.md` and use the Codex automation tool when creating or updating actual automations.

If a request spans multiple workflows, run them in the natural order:

1. `macro-equity-research` when deeper source verification, screening, or macro/policy analysis is needed.
2. `weekly-trading-plan` to initialize or deep-update the Active Market Plan.
3. `daily-market-tracking` to quick-update the same plan against today's market.
4. `intraday-setup-scan` to classify setup-level status during the session.
5. `portfolio-risk` before increasing or concentrating exposure, using canonical broker data when available.
6. `trade-review` after orders/fills and after exits.
7. `trading-stats` after enough closed-trade records exist.

## Shared Resources

Detailed domain rules remain in:

- `references/macro-policy-filter.md`
- `references/equity-screening.md`
- `references/active-market-plan.md`
- `references/trading-profile.md`
- `references/broker-data-contract.md`
- `references/automation-contract.md`
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
