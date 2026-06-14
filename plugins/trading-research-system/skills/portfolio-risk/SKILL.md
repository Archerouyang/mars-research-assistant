---
name: portfolio-risk
description: Review portfolio risk exposure, sizing, concentration, directionality, correlation, instrument risk, and trade impact before or after planned trades. Use when the user asks about holdings, risk exposure, position sizing, portfolio impact, max loss, concentration, or whether a new trade would overload existing risk.
---

# Portfolio Risk

Use this skill to keep trade ideas and actual trades inside portfolio constraints.

## Workflow

1. Read `../trading-research/references/portfolio-risk.md`.
2. Read `../trading-research/references/trade-journal.md` if planned or actual trades are involved.
3. Use `../../scripts/portfolio_risk.py` when a holdings or portfolio CSV is available.
4. Use live account/position data only when an authorized connector is available and the user asks for current exposure.
5. Check:
   - directional exposure;
   - single-name concentration;
   - sector/theme concentration;
   - correlated risk;
   - option premium at risk;
   - leverage and 0DTE risk;
   - max planned loss versus risk budget.

## Output

Use Chinese Markdown with:

- `当前暴露`
- `新增交易影响`
- `集中风险`
- `相关性风险`
- `最大损失`
- `仓位建议范围`
- `必须避免`

Do not approve a trade just because the setup is attractive. If exposure is already crowded, say so clearly.
