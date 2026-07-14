---
name: weekly-trading-plan
description: Initialize or deep-update the Active Market Plan with last week's trade summary review, current market tape, macro/rates, policy, news, future event preview, optional external momentum context, setup-level opportunity discovery, and portfolio risk refresh. Use when the user asks for a weekly review, weekend prep, next-week outlook, deep plan update, macro/policy preview, momentum context update, or setup/opportunity discovery.
---

# Weekly Market Review And Trading Plan

Use this skill for a `deep_update` of the Active Market Plan. It should update the overwriteable `market-plan.md` and, when writing files, append the rationale to `updates/YYYY-MM-DD.md`.

This is decision support, not automated trading. Separate facts, assumptions, long case, short case, invalidation, and risk controls.

## Exact Weekend First-Start Daily Ops Guard

For the exact request `周末首次启动，先看看下周`, do not begin the normal weekly
analysis directly. Run `python3 plugins/trading-research-system/scripts/runtime_health.py --format json` as a
status-only check, then follow the Daily Ops Orchestrator before this weekly
workflow.

### 运行状态检查

Before analysis, explicitly render the returned `runtime_origin`, formal
runtime availability, and `startup_status`. Preserve the deterministic values
without reinterpretation. When `TRADING_RESEARCH_RUNTIME_DIR` selects a path
that does not exist, render `runtime_origin=environment`,
`formal runtime=missing`, and `startup_status=uninitialized`. Keep runtime
availability and startup completeness as independent axes.

### 可用研究摘要

After the status block, give a concise current public-source reduced-scope
weekly summary. Keep the user-facing order “先摘要，后授权/初始化”, label the
missing personalization, and do not turn the summary into a setup or trading
instruction.

### 摘要后缺失确认

After the summary, request all three choices: broker read-only preference, the
complete `ticker + trade_horizon + instrument` key, and whether to stay in
`dry-run` or initialize the private runtime. A broker preference records intent
only and does not read an account. Initialization requires separate explicit
runtime-write authorization; neither broker preference nor setup-key
confirmation authorizes a write.

### 安全边界

Do not write runtime in this first response. Do not read private runtime file
contents. Do not read broker or private account data. Do not generate setups or
buy/sell instructions.

For a weekend first start with a partial or uninitialized runtime, first provide
a current public-source reduced-scope research summary, then ask for runtime or
broker authorization. In that first response, do not write runtime. Before deep
research or setup work on a specific symbol, confirm
`ticker + trade_horizon + instrument`; otherwise keep symbol comments watch-only.

This is an AI-native workflow. Read broadly across market, macro, rates, policy, news, events, momentum, and user records, but show the user only the distilled plan changes, high-impact evidence, setup pool changes, and next checks.

The weekly note must be a decision-support memo tied to holdings and planned risk. Do not output a plain macro calendar. Every high-impact event should answer: why it matters, source priority, transmission path, affected holdings/plans, confirmation to watch, and what strategy posture it supports.

## Workflow

1. Read the shared references needed for the task:
   - Active plan model: `../trading-research/references/active-market-plan.md`.
   - Trading profile strategy rules, pools, timeframes, and instrument preferences: `../trading-research/references/trading-profile.md`.
   - Macro and rates: `../trading-research/references/macro-policy-filter.md`.
   - Equity screening and thesis validation: `../trading-research/references/equity-screening.md`.
   - optional external quantitative momentum context when already configured
     or explicitly provided by the user.
   - Price action and timeframe rules: `../trading-research/references/price-action-timing.md`.
   - Trade plan schema: `../trading-research/references/trade-journal.md`.
   - Risk exposure: `../trading-research/references/portfolio-risk.md`.
   - Broker data contract when using account data: `../trading-research/references/broker-data-contract.md`.
   - Visual trigger policy: `../trading-research/references/visual-trigger-policy.md`.
   - Formatting: `../trading-research/references/output-templates.md`.
2. Use current sources for time-sensitive facts: policy, Treasury/rates/yields, prices, earnings, analyst claims, news, event calendars, and market state.
3. Build the weekly note in this order:
   - last week's trade review: wins, losses, missed setups, mistake tags, and process lessons;
   - current market tape: indexes, breadth, sector leadership, volatility, 20/50 EMA context, and trend/range state;
   - source priority: classify macro, policy, news, research, market data, and rumor inputs by evidence quality before they can affect the plan;
   - macro/rates analysis: Treasury yields, Fed expectations, liquidity, dollar, oil, and factor impact;
   - policy analysis: market-moving fiscal, Treasury, tariff, regulatory, or Trump-related policy only when relevant;
   - news analysis: earnings, guidance, sector catalysts, credit/liquidity events, and verified high-impact headlines;
   - trade plan preparation: reduce upstream research into input reads,
     including optional external momentum context only when configured or
     explicitly provided, then build the Cross-Section Candidate Pool before
     touching the Setup Pool;
   - current holding impact: how the week changes add, TP/rebalance, or pause-and-review conditions for existing long-term ETF holdings;
   - new-position impact: whether planned risk such as 0DTE, ETF/2x ETF, LEAP, or post-event continuation should wait for confirmation;
   - strategy posture: decide whether the plan should be defensive, balanced, or high-beta momentum, and explain which conditions would change that posture;
   - key earnings this week: only include earnings that can affect current holdings, index/sector beta, momentum themes, or planned setups;
   - event priority ranking: P0/P1/P2 events sorted by decision impact;
   - next-week preview: macro releases, Fed/Treasury events, auctions, earnings, expirations, known policy deadlines, and relevant White House / Trump public remarks;
   - optional external momentum context: consume an already configured or
     user-provided snapshot only as research-priority context. If missing or
     stale, continue without it instead of rebuilding a quantitative model
     during the weekly plan;
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

## Source Routing Boundary

Choose sources by claim type. Selecting Longbridge for stock data does not make Longbridge the default source for macro, policy, industry, or news analysis.
Longbridge `macrodata` may support macro and financial-condition values, but
policy facts require S0 official sources and industry/news leads require S2 or
authorized research before they can change risk budget.

Read `../trading-research/references/macro-data-source-contract.md` before
writing `Macro Regime`, `Financial Conditions`, or `策略姿态`. Weekly output
must include `宏观数据来源状态` and `实际宏观指标读数`: use Longbridge macrodata
as the preferred S1 source for macro values when available, IBKR market data for
price/OHLCV transmission, and official source fallback for S0 facts or when
Longbridge macrodata is unavailable.

When actual macro values are available and the weekly plan uses them to set
strategy posture, risk budget, add/TP/pause decisions, or event sensitivity,
apply `visual-trigger-policy.md` and include a `Macro Regime Mini-Panel` or say
why it was skipped. When a setup candidate needs visual inspection of support,
resistance, EMA context, trigger zone, or invalidation, use the same policy to
request or show a `PA Scenario Board`.

## Trade Plan Preparation

Weekly outputs must include a `交易计划准备` section before setup discovery. This section is the bridge from research to Active Market Plan, and must not be skipped in favor of immediate setup rows.

Use these input reads:

- `Macro Regime`: growth, inflation, Fed path, USD, oil, liquidity, and broad risk-on/risk-off state.
- `Financial Conditions`: 2Y/10Y/30Y, real yields, credit spreads, VIX, USD, and liquidity pressure.
- `Policy/Event Risk`: White House / Trump policy, Treasury/fiscal, tariffs, Fed independence, auctions, FOMC, earnings, holidays, and other event risk.
- `Industry/Sector Strength`: sector leadership, breadth, relative strength, rotation, and themes that deserve or lose attention.
- `Company Thesis Check`: verified company thesis/counter-thesis, valuation, catalyst, earnings, guidance, and disconfirming facts.
- `External Momentum Snapshot`: optional imported model output when the user has
  already provided or configured a separate quantitative model. Treat it as an
  optional external snapshot and research priority only, not a buy list. Do not
  rebuild, re-rank, or re-score the model inside the plugin.

Each input read should use this shape: `read`, `supports`, `pressures`, `blocks`, `evidence`, and `next_check`. Keep it concise; this is not five separate reports.

Then build `Cross-Section Candidate Pool` with candidates worth searching for
setups. The pool is not a buy list and not the Setup Pool. External momentum
context can raise or lower research priority, but candidates still need
macro/financial support, industry or company evidence, price structure, and
preliminary portfolio risk context before promotion.

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
- `外部动量快照（如已启用）`
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
