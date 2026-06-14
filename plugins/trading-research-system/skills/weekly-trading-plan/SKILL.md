---
name: weekly-trading-plan
description: Initialize or deep-update the Active Market Plan with last week's trade summary review, current market tape, macro/rates, policy, news, future event preview, momentum leaderboard rebuild, setup-level opportunity discovery, and portfolio risk refresh. Use when the user asks for a weekly review, weekend prep, next-week outlook, deep plan update, macro/policy preview, momentum ranking update, or setup/opportunity discovery.
---

# Weekly Market Review And Trading Plan

Use this skill for a `deep_update` of the Active Market Plan. It should update the overwriteable `market-plan.md` and, when writing files, append the rationale to `updates/YYYY-MM-DD.md`.

This is decision support, not automated trading. Separate facts, assumptions, long case, short case, invalidation, and risk controls.

## Workflow

1. Read the shared references needed for the task:
   - Active plan model: `../trading-research/references/active-market-plan.md`.
   - Macro and rates: `../trading-research/references/macro-policy-filter.md`.
   - Equity screening and thesis validation: `../trading-research/references/equity-screening.md`.
   - Price action and timeframe rules: `../trading-research/references/price-action-timing.md`.
   - Trade plan schema: `../trading-research/references/trade-journal.md`.
   - Risk exposure: `../trading-research/references/portfolio-risk.md`.
   - Broker data contract when using account data: `../trading-research/references/broker-data-contract.md`.
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
   - setup pool refresh: setup-level candidates grouped by theme, symbol, and instrument type;
   - setup details: long/short thesis, setup type, instrument type, analysis timeframe, trigger timeframe, trigger zone, invalidation, and risk budget;
   - portfolio exposure impact.
4. Prefer `../../assets/templates/market-plan.md` for current state and `../../assets/templates/weekly-plan.md` for a longer deep-update note.
5. Convert only the highest-quality ideas into setup rows with status `active`; keep weaker ideas as `candidate`.

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
- `Setup Pool`
- `失效条件`
- `组合风险`
- `下一次更新重点`

Do not overfit one article, one chart, or one macro headline. If the plan needs evidence, state exactly what needs to be verified in later updates.
