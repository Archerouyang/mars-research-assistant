---
name: weekly-trading-plan
description: Build a weekly trading plan from macro context, rates, watchlists, candidate trade ideas, price action, instrument-specific timeframes, and portfolio risk. Use when the user asks for a weekly plan, next-week trade ideas, a weekend/weekly trading prep note, initial trade plan construction, or a prioritized watchlist for the coming week.
---

# Weekly Trading Plan

Use this skill to turn market context into a weekly plan that can feed daily tracking, intraday scans, trade plans, and later reviews.

This is decision support, not automated trading. Separate facts, assumptions, long case, short case, invalidation, and risk controls.

## Workflow

1. Read the shared references needed for the task:
   - Macro and rates: `../trading-research/references/macro-policy-filter.md`.
   - Equity screening and thesis validation: `../trading-research/references/equity-screening.md`.
   - Price action and timeframe rules: `../trading-research/references/price-action-timing.md`.
   - Trade plan schema: `../trading-research/references/trade-journal.md`.
   - Risk exposure: `../trading-research/references/portfolio-risk.md`.
   - Formatting: `../trading-research/references/output-templates.md`.
2. Use current sources for time-sensitive facts: policy, Treasury/rates/yields, prices, earnings, analyst claims, and market state.
3. Build the plan in this order:
   - market regime;
   - macro/rates variables to watch;
   - priority themes;
   - candidate symbols and trade ideas;
   - setup and instrument type;
   - analysis timeframe and trigger timeframe;
   - invalidation, stop concept, target concept, and risk budget;
   - portfolio exposure impact.
4. Prefer the template at `../../assets/templates/weekly-plan.md` when the user wants a reusable note.
5. Convert only the highest-quality ideas into planned rows for `trade-plans.csv`; keep weaker ideas as watchlist candidates.

## Output

Write concise Chinese Markdown notes with:

- `市场状态`
- `本周核心变量`
- `优先主题`
- `候选交易想法`
- `预备交易计划`
- `失效条件`
- `组合风险`
- `明日追踪重点`

Do not overfit one article, one chart, or one macro headline. If the plan needs evidence, state exactly what needs to be verified during daily tracking.
