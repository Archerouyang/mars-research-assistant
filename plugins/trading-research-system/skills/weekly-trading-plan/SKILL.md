---
name: weekly-trading-plan
description: Initialize or deep-update the Active Market Plan with last week's trade summary review, current market tape, macro/rates, policy, news, future event preview, momentum leaderboard rebuild, setup-level opportunity discovery, and portfolio risk refresh. Use when the user asks for a weekly review, weekend prep, next-week outlook, deep plan update, macro/policy preview, momentum ranking update, or setup/opportunity discovery.
---

# Weekly Market Review And Trading Plan

Use this skill for a `deep_update` of the Active Market Plan. It should update the overwriteable `market-plan.md` and, when writing files, append the rationale to `updates/YYYY-MM-DD.md`.

This is decision support, not automated trading. Separate facts, assumptions, long case, short case, invalidation, and risk controls.

This is an AI-native workflow. Read broadly across market, macro, rates, policy, news, events, momentum, and user records, but show the user only the distilled plan changes, high-impact evidence, setup pool changes, and next checks.

The weekly note must be a decision-support memo tied to holdings and planned risk. Do not output a plain macro calendar. Every high-impact event should answer: why it matters, source priority, transmission path, affected holdings/plans, confirmation to watch, and what strategy posture it supports.

## Workflow

1. Read the shared references needed for the task:
   - Active plan model: `../trading-research/references/active-market-plan.md`.
   - Trading profile and instrument preferences: `../trading-research/references/trading-profile.md`.
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
   - source priority: classify macro, policy, news, research, market data, and rumor inputs by evidence quality before they can affect the plan;
   - macro/rates analysis: Treasury yields, Fed expectations, liquidity, dollar, oil, and factor impact;
   - policy analysis: market-moving fiscal, Treasury, tariff, regulatory, or Trump-related policy only when relevant;
   - news analysis: earnings, guidance, sector catalysts, credit/liquidity events, and verified high-impact headlines;
   - trade plan preparation: reduce upstream research into the five input reads, then build the Cross-Section Candidate Pool before touching the Setup Pool;
   - current holding impact: how the week changes add, TP/rebalance, or pause-and-review conditions for existing long-term ETF holdings;
   - new-position impact: whether planned risk such as 0DTE, ETF/2x ETF, LEAP, or post-event continuation should wait for confirmation;
   - strategy posture: decide whether the plan should be defensive, balanced, or high-beta momentum, and explain which conditions would change that posture;
   - key earnings this week: only include earnings that can affect current holdings, index/sector beta, momentum themes, or planned setups;
   - event priority ranking: P0/P1/P2 events sorted by decision impact;
   - next-week preview: macro releases, Fed/Treasury events, auctions, earnings, expirations, known policy deadlines, and relevant White House / Trump public remarks;
   - momentum candidate pool TODO: do not treat momentum ranking as a v1 input unless a separate quantitative model, data source, factor definition, ranking rule, and validation process have been defined;
   - setup pool refresh: promote only prepared candidates with higher-timeframe regime, strategy bias, price structure, trigger zone, invalidation, and next check into `candidate` or `active` setups;
   - setup details: long/short thesis, setup type, instrument type, analysis timeframe, trigger timeframe, trigger zone, invalidation, profile fit, and risk budget;
   - portfolio exposure impact.
4. Prefer `../../assets/templates/market-plan.md` for current state and `../../assets/templates/weekly-plan.md` for a longer deep-update note.
5. Convert only the highest-quality ideas into setup rows with status `active`; keep weaker ideas as `candidate`.

## Event Priority

Use this priority vocabulary in weekly outputs:

- `P0`: can change weekly risk budget, existing-holding add decisions, TP/rebalance decisions, or pause-and-review conditions.
- `P1`: can change setup attention, trigger zones, or holding bias, but should not reset the whole weekly plan by itself.
- `P2`: background only; should not drive same-day trading decisions unless later evidence raises its priority.

The event table must use these columns. `策略姿态含义` is portfolio-level guidance, not a direct buy/sell instruction.

| 优先级 | 时间 | 事件 | 为什么重要 | 信源优先级 | 传导路径 | 影响的持仓/计划 | 需要观察的确认 | 策略姿态含义 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Transmission paths should be explicit, for example: `rates`, `10Y/yields`, `USD`, `oil`, `sector`, `volatility`, `earnings`, or `liquidity`.

## Source Priority

Use the source priority vocabulary from `macro-policy-filter.md`:

- `S0 official / primary`: confirms policy, macro releases, exchange calendars, filings, and official remarks.
- `S1 market data / broker / macrodata / calendar`: confirms live macro values and market transmission through prices, yields, volatility, flows, and event timing.
- `S2 reputable financial media`: leads that need confirmation when they affect risk budget or policy interpretation.
- `S3 research / opinion`: thesis input and counterargument source, not proof of policy or macro facts.
- `S4 social / rumor / unsourced commentary`: ignore unless confirmed by higher-priority sources.

Weekly outputs must include a `信源优先级` section when macro, policy, or news events drive the plan.

## Trade Plan Preparation

Weekly outputs must include a `交易计划准备` section before setup discovery. This section is the bridge from research to Active Market Plan, and must not be skipped in favor of immediate setup rows.

Use these five input reads:

- `Macro Regime`: growth, inflation, Fed path, USD, oil, liquidity, and broad risk-on/risk-off state.
- `Financial Conditions`: 2Y/10Y/30Y, real yields, credit spreads, VIX, USD, and liquidity pressure.
- `Policy/Event Risk`: White House / Trump policy, Treasury/fiscal, tariffs, Fed independence, auctions, FOMC, earnings, holidays, and other event risk.
- `Industry/Sector Strength`: sector leadership, breadth, relative strength, rotation, and themes that deserve or lose attention.
- `Company Thesis Check`: verified company thesis/counter-thesis, valuation, catalyst, earnings, guidance, and disconfirming facts.

Each input read should use this shape: `read`, `supports`, `pressures`, `blocks`, `evidence`, and `next_check`. Keep it concise; this is not five separate reports.

Then build `Cross-Section Candidate Pool` with candidates worth searching for setups. The pool is not a buy list and not the Setup Pool. Momentum leaderboard output is a separate future quantitative model and should not be treated as a required v1 input.

Before promoting a cross-section candidate into the Setup Pool, check:

- higher-timeframe regime from `4H`, `1D`, and `1W`: uptrend, range, or downtrend;
- strategy bias allowed by that regime;
- setup type;
- price structure;
- trigger zone;
- invalidation;
- preliminary risk context;
- next check, usually `1H` or lower execution observation or event confirmation.

Candidates missing those fields stay in the Cross-Section Candidate Pool instead of becoming setup rows.

## Strategy Posture

Weekly outputs must include `策略姿态建议` before detailed event tables. This section should answer whether current evidence supports:

- `防御`: reduce new risk, tighten review conditions, favor cash/TLT/hedge thinking, or pause high-beta additions.
- `平衡`: keep core holdings, wait for confirmations, allow only selective setup-level risk.
- `高 beta 动量`: allow stronger QQQ/SOXX/DRAM or momentum-stock risk only after rates, volatility, breadth, and price-action confirmation.

Do not describe `优先观察清单` or `交易含义` as generic ticker advice. Tie them back to the overall posture first, then explain which holdings or setup groups are affected.

## Key Earnings This Week

Weekly outputs must include `当周重点财报` when earnings season, index weights, sector leadership, or watchlist names can affect the plan.

Do not dump a full earnings calendar. Include only earnings that meet at least one condition:

- index-weighted name that can move QQQ, VOO, SOXX, or another current holding;
- semiconductor, AI, cloud, software, consumer, bank, energy, or rate-sensitive name that can confirm or reject a current theme;
- watchlist or setup-pool name with a planned trade idea;
- earnings likely to affect strategy posture through volatility, breadth, sector rotation, or gap risk.

Each row should state source priority, date/time, why it matters, affected holdings/plans, what confirmation matters after the print, and whether the event argues for `防御`, `平衡`, or `高 beta 动量`.

## Holding And Plan Impact

For existing long-term ETF holdings such as QQQ, VOO, DRAM, and SOXX:

- discuss add zones, TP/rebalance, or pause-and-review only;
- do not frame normal pullbacks as tactical stop-loss exits;
- connect macro/rates/news variables to concrete holding management choices.

For new-position plans:

- state whether new risk is allowed now or should wait for event confirmation;
- name the product class when relevant: 0DTE, ETF/2x ETF, LEAP, common stock, or sector ETF;
- call out when adding risk would crowd existing tech beta, semiconductor exposure, rate sensitivity, or short-dated option risk.

## User-Facing Status Language

Avoid unexplained internal status-jump phrasing in user-facing weekly summaries.

When a status term is necessary, include a Chinese explanation in the same sentence. Example:

- `candidate（候选，只表示值得继续观察，不代表可以交易）`
- `approaching（接近计划区域，但还缺少执行时间框架确认）`
- `triggered（计划内触发已出现，需要人工决策，不是下单指令）`

## Output

Write concise Chinese Markdown notes with:

- `结论`
- `本周真正重要的 3 个变量`
- `市场状态`
- `上周交易复盘`
- `盘面分析`
- `信源优先级`
- `宏观/利率`
- `政策/新闻`
- `交易计划准备`
- `对当前持仓的总体影响`
- `策略姿态建议`
- `当周重点财报`
- `事件重要性排序`
- `宏观/政策/新闻时间线`
- `特朗普/白宫公开讲话与政策风险`
- `对现有持仓计划的影响`
- `对新增持仓计划的影响`
- `下周事件预览`
- `动量榜单`
- `优先主题`
- `候选交易想法`
- `Setup 挖掘`
- `Setup Pool`
- `交易风格匹配`
- `失效条件`
- `组合风险`
- `需要用户决策的事项`
- `下一次更新重点`

Keep detailed source-reading out of the main answer unless the user asks for the audit trail. Do not overfit one article, one chart, or one macro headline. If the plan needs evidence, state exactly what needs to be verified in later updates.
