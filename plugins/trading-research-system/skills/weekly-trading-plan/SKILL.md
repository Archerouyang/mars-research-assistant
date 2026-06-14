---
name: weekly-trading-plan
description: Build a weekly market review and next-week trading plan covering last week's trade review, current market tape, macro/rates, policy, news, major event preview, momentum leaderboard updates, trade idea generation, and setup discovery. Use when the user asks for a weekly review, weekend prep, next-week plan, weekly trading plan, macro/policy preview, momentum ranking update, or setup/opportunity discovery for the coming week.
---

# Weekly Market Review And Trading Plan

Use this skill to produce the weekly operating note: review the previous week's trades, analyze the current market, preview next week's macro/policy/news/event risks, update momentum rankings, and turn the best ideas into planned setups for daily tracking.

This is decision support, not automated trading. Separate facts, assumptions, long case, short case, invalidation, and risk controls.

## Workflow

1. Read the shared references needed for the task:
   - Macro and rates: `../trading-research/references/macro-policy-filter.md`.
   - Equity screening and thesis validation: `../trading-research/references/equity-screening.md`.
   - Price action and timeframe rules: `../trading-research/references/price-action-timing.md`.
   - Trade plan schema: `../trading-research/references/trade-journal.md`.
   - Risk exposure: `../trading-research/references/portfolio-risk.md`.
   - Formatting: `../trading-research/references/output-templates.md`.
2. Use current sources for time-sensitive facts: policy, Treasury/rates/yields, prices, earnings, analyst claims, news, event calendars, and market state.
3. Build the weekly note in this order:
   - last week's trade review: wins, losses, missed setups, mistake tags, and process lessons;
   - current market tape: indexes, breadth, sector leadership, volatility, 20/50 EMA context, and trend/range state;
   - macro/rates analysis: Treasury yields, Fed expectations, liquidity, dollar, oil, and factor impact;
   - policy analysis: market-moving fiscal, Treasury, tariff, regulatory, or Trump-related policy only when relevant;
   - news analysis: earnings, guidance, sector catalysts, credit/liquidity events, and verified high-impact headlines;
   - next-week preview: macro releases, Fed/Treasury events, auctions, earnings, expirations, and known policy deadlines;
   - momentum leaderboard update: strongest and weakest symbols/themes, plus what changed versus the prior week;
   - trade idea and setup discovery: long/short thesis, setup type, instrument type, timeframes, levels, invalidation, and risk budget;
   - portfolio exposure impact.
4. Prefer the template at `../../assets/templates/weekly-plan.md` when the user wants a reusable note.
5. Convert only the highest-quality ideas into planned rows for `trade-plans.csv`; keep weaker ideas as watchlist candidates.

## Output

Write concise Chinese Markdown notes with:

- `市场状态`
- `上周交易复盘`
- `盘面分析`
- `宏观/利率`
- `政策/新闻`
- `下周事件预览`
- `动量榜单`
- `优先主题`
- `候选交易想法`
- `Setup 挖掘`
- `预备交易计划`
- `失效条件`
- `组合风险`
- `下周每日追踪重点`

Do not overfit one article, one chart, or one macro headline. If the plan needs evidence, state exactly what needs to be verified during daily tracking.
