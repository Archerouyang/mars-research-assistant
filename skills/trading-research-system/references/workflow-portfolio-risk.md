---
name: portfolio-risk
description: Review portfolio risk exposure, broker/account reconciliation, sizing, concentration, directionality, correlation, instrument risk, and trade impact before or after planned trades. Use when the user asks about holdings, risk exposure, position sizing, portfolio impact, max loss, concentration, broker positions, or whether a new trade would overload existing risk.
---

# Portfolio Risk

Use this skill to keep trade ideas and actual trades inside portfolio constraints.

## Workflow

1. Read `./portfolio-risk.md`.
2. Read `./position-daily-report.md` when the user asks for a holdings daily report, scheduled position report, or broker-native style position reminder.
3. Read `./broker-data-contract.md` when broker, account, or position reconciliation is involved.
4. Read `./trade-journal.md` if planned or actual trades are involved.
5. Use `scripts/position_daily_report.py` when the user asks for a scheduled holdings daily report or broker-native style position reminder and a standard `portfolio_snapshot.csv` is available.
6. Use `scripts/repair_portfolio_snapshot.py` first when a standard `portfolio_snapshot.csv` has stale or unmapped product/theme fields before rendering exposure summaries.
7. Use `scripts/portfolio_risk.py` when a broader holdings, portfolio, or broker-live fixture snapshot risk summary is needed.
8. Use live account/position data only when an authorized connector is available and the user asks for current exposure.
9. Read `portfolio_reconciliation` before any cross-broker total. A NAV-only
   source is `partial_data`, not confirmed position exposure. Keep it separate,
   pass excluded sources to `position_daily_report.py`, and never merge a
   NAV-only account total with another broker's detailed positions.
10. Check:
   - directional exposure;
   - total exposure across brokers;
   - broker/account breakdown;
   - single-name concentration;
   - sector/theme concentration;
   - correlated risk;
   - option premium at risk;
   - leverage and 0DTE risk;
   - max planned loss versus risk budget.

## Output

Use Chinese Markdown with:

- `当前暴露`
- `券商/账户拆分`
- `新增交易影响`
- `集中风险`
- `相关性风险`
- `最大损失`
- `仓位建议范围`
- `必须避免`

Do not approve a trade just because the setup is attractive. If exposure is already crowded, say so clearly.
