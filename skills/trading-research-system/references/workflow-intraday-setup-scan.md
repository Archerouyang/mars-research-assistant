---
name: intraday-setup-scan
description: Scan prepared Active Market Plan setups for intraday states such as active, approaching, triggered, invalidated, needs_review, or completed. Use when the user asks to monitor several tickers/charts, check whether a setup has appeared, prioritize active setups during the session, or review execution-timeframe signals.
---

# Intraday Setup Scan

Use this skill for setup-scoped intraday monitoring. It does not place orders and does not convert price contact into a buy/sell instruction.

## Workflow

1. Read `./active-market-plan.md`.
2. Read `./intraday-setup-scan.md`.
3. Read `./price-action-timing.md` for trigger confirmation and instrument-specific strictness.
4. Read `./visual-trigger-policy.md` before deciding whether to show a `PA Scenario Board`.
5. Read `./portfolio-risk.md` when exposure or sizing may constrain action.
6. Use `market-plan.md`, the current day's `intraday-watchlist.csv`, `trade-plans.csv`, and update notes when available.
7. Use current chart/price data from authorized sources, such as IBKR, when available.
8. When a prepared `intraday-watchlist.csv` exists, use `scripts/intraday_scan.py` to render the plan-scoped status summary, then add chart/current-data interpretation only where authorized data is available.
9. Classify each setup:
   - `candidate`
   - `active`
   - `invalidated`
   - `triggered`
   - `needs_review`
   - `approaching`
   - `completed`
10. Sort by attention priority, not conviction. Sort by attention priority because the scan is a queue for human inspection, not an order instruction.

Show or request a `PA Scenario Board` only for setups that are `approaching`,
`triggered`, `invalidated`, or `needs_review` and have authorized chart data.
Keep ordinary `active` or distant `candidate` setups text-only.

## Output

Write a compact Chinese scan note:

- `优先级`
- `setup_id`
- `标的/产品`
- `状态`
- `当前 setup`
- `信号时间框架`
- `失效/止损风险`
- `组合风险`
- `下一步人工判断`

For 0DTE options, require strict execution-timeframe confirmation and acceptable risk/reward. For LEAPs, weight daily/weekly background more heavily but keep invalidation explicit. `triggered` means human decision needed, not an order instruction.
