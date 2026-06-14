---
name: intraday-setup-scan
description: Scan prepared trade plans and high-priority watchlist ideas for intraday setup states such as waiting, approaching, triggered, invalidated, or needs_review. Use when the user asks to monitor several tickers/charts, check whether a setup has appeared, prioritize active plans during the session, or review execution-timeframe signals.
---

# Intraday Setup Scan

Use this skill for plan-scoped intraday monitoring. It does not place orders and does not convert price contact into a buy/sell instruction.

## Workflow

1. Read `../trading-research/references/intraday-setup-scan.md`.
2. Read `../trading-research/references/price-action-timing.md` for trigger confirmation and instrument-specific strictness.
3. Read `../trading-research/references/portfolio-risk.md` when exposure or sizing may constrain action.
4. Use the current day's `intraday-watchlist.csv`, `trade-plans.csv`, and daily tracking note when available.
5. Use current chart/price data from authorized sources, such as IBKR, when available.
6. Classify each plan:
   - `invalidated`
   - `triggered`
   - `needs_review`
   - `approaching`
   - `waiting`
7. Sort by attention priority, not conviction.

## Output

Write a compact Chinese scan note:

- `优先级`
- `trade_id`
- `标的/产品`
- `状态`
- `当前 setup`
- `信号时间框架`
- `失效/止损风险`
- `组合风险`
- `下一步人工判断`

For 0DTE options, require strict execution-timeframe confirmation and acceptable risk/reward. For LEAPs, weight daily/weekly background more heavily but keep invalidation explicit.
