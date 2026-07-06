# Daily Ops Orchestrator

Use this reference when the user asks to start, continue, or check the trading
workflow without naming a specific focused workflow. The Orchestrator is the
active process guide for Daily Ops. It decides the next workflow and asks only
for missing confirmations that block useful output.

The Orchestrator is not a new trading signal engine. It routes to existing
focused workflows and keeps the user from having to manually call out every
part of the system.

## Purpose

- detect the current Daily Ops stage;
- read runtime health and available state before choosing a workflow;
- decide the next recommended action;
- ask for missing confirmations, especially ticker-level trade horizon and
  instrument intent;
- route to the correct focused workflow after confirmation;
- keep outputs concise, Chinese, and decision-useful.

## Stage Detection

Classify the current stage from the user request, current date/time, runtime
health, and available state:

- `weekly_deep_update`: weekend, week reset, or user asks for next-week plan.
- `premarket_quick_update`: weekday premarket or user says "start today",
  "begin daily ops", "开始今天的交易研究日程", "盘前", or "今天怎么安排".
- `intraday_trigger_monitor`: market hours and prepared active/approaching
  setups exist.
- `post_market_review`: after market close or user asks to summarize today.
- `post_order_review`: a new order, fill, or manual entry is reported.
- `post_exit_review`: a trade has closed or broker result facts are available.
- `research_intake`: the user provides or asks to find a report, link,
  screenshot, PDF, or thesis source.
- `position_risk_check`: the user asks about holdings, exposure, cash, margin,
  or risk budget.
- `blocked_setup`: the workflow cannot proceed because trade horizon,
  instrument, runtime state, or source permission is missing.

If several stages apply, choose the one that removes the largest current
blocker. For example, if a ticker idea has no trade horizon, ask for that before
generating trigger levels.

## Required Reads

Before recommending a workflow, inspect only availability/status unless the
user has authorized deeper reads:

- runtime health via `runtime-health.md` and `runtime_health.py`;
- `{runtime_dir}/ops-state.md` when available;
- `{runtime_dir}/market-plan.md` status when available;
- `{runtime_dir}/trading-profile.md` status when available;
- today's daily directory status;
- KVN snapshot availability when the next step depends on momentum;
- broker-source authorization status when holdings, executions, or position
  daily report are needed.

Do not copy private runtime content into public repo docs. Do not write runtime
files unless the user confirms a proposed write package.

## Source Routing Boundary

Track source purpose separately from broker-source selection. Do not reuse broker-source selection as news-source selection.

- Longbridge or IBKR as a broker source can answer read-only holdings,
  executions, order status, and authorized market-data facts.
- Longbridge macrodata can support macro values but cannot replace official or reputable news sources.
- Macro policy facts still need S0 official sources.
- Industry/news monitoring should use the configured public/authorized source
  mix from `macro-policy-filter.md`.

## Ticker Trade Horizon Confirmation

Before a ticker can move from watchlist or Cross-Section Candidate Pool into a
specific setup, confirm the intended trade horizon and instrument.

Required grouping key:

```text
ticker + trade_horizon + instrument
```

`trade_horizon` allowed examples:

- `long-term holding`;
- `medium-term swing`;
- `short-term swing`;
- `intraday`;
- `0DTE`;
- `LEAP`;
- `2x ETF`;
- `macro allocation`;
- `watch only`.

If trade horizon is missing, do not produce concrete entry or exit triggers.
Ask one concise question such as:

```text
这些标的分别按什么周期处理？例如：QQQ 长期持有，QQQ 0DTE 日内，MU 中期波段，TSM LEAP，GLW 观察。
```

The same ticker may have multiple setups. Keep them separate:

- `QQQ + long-term holding + ETF`;
- `QQQ + 0DTE + option`;
- `TSM + LEAP + call`;
- `GLW + watch only + equity`.

## Workflow Routing

After stage detection and missing-confirmation checks, route in this order:

1. `research-report-intake` for reports, PDFs, links, excerpts, screenshots, or
   research discovery.
2. `macro-equity-research` when source verification, macro/policy/rates, or
   stock research is needed before plan impact.
3. `weekly-trading-plan` for a deep Active Market Plan reset.
4. `daily-market-tracking` for premarket or intraday quick update against the
   current plan.
5. `intraday-setup-scan` for prepared setup status checks only.
6. `portfolio-risk` before increasing exposure or when position/cash/margin
   risk matters.
7. `trade-review` after order/fill or exit facts.
8. `trading-stats` when the user asks about system performance.

Do not expose focused skill names as the main user experience unless useful for
debugging.

## Output Contract

Return the sections from `assets/templates/daily-ops-orchestrator.md`:

- 当前日程阶段;
- 读取状态;
- 缺失确认;
- Ticker / Setup 周期确认;
- 建议下一步;
- 为什么现在做这一步;
- 确认后我会执行;
- 安全边界.

Use `Next Recommended Action` as the internal concise summary for
`ops-state.md` and automation prompts.

## Safety Boundaries

- Do not create buy/sell instructions.
- Do not create, modify, cancel, close, or approve orders.
- Do not read broker data unless the user authorizes a read-only broker source.
- Do not bypass paywalls.
- Do not write runtime files without a confirmed proposed write package.
- Do not scan the whole market during intraday checks; use prepared setups.
