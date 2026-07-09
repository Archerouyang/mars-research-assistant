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
- visual trigger policy via `visual-trigger-policy.md`;
- `{runtime_dir}/ops-state.md` when available;
- `{runtime_dir}/market-plan.md` status when available;
- `{runtime_dir}/trading-profile.md` status when available;
- `{runtime_dir}/daily/YYYY-MM-DD/macro-panel.json` status when available;
- `{runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv` status when available;
- today's daily directory status;
- optional external momentum snapshot availability when the next step depends
  on a user-configured momentum model;
- broker-source authorization status when holdings, executions, or position
  daily report are needed.

The formal runtime is `runtime_dir`, defaulting to
`~/Documents/dailytrades-runtime` unless the user or environment provides an
override. A repo fixture, bundled template, or stale example plan is not the
active runtime. If only repo fixture state is available, label it as `fixture /
debug only`, do not call it the current Active Market Plan, and ask whether to
bootstrap or point to the formal runtime.

Do not copy private runtime content into public repo docs. Do not write runtime
files unless the user confirms a proposed write package.

## Startup Health Block

Every new Daily Ops chat or "start today" response must include a fixed startup
health block before analysis. This block prevents the agent from guessing which
state it can trust.

In `读取状态`, include:

### 运行状态检查

- `runtime_dir`: the formal runtime path or `unknown`.
- `formal runtime`: `available`, `missing`, `stale`, or `unauthorized`.
- `ops-state.md`: status only.
- `market-plan.md`: status only.
- `trading-profile.md`: status only.
- `macro-panel.json`: status only.
- `portfolio_snapshot.csv`: status only.
- `daily/YYYY-MM-DD/`: status only.
- `current_mode` / `当前模式`: one of `live read-only`, `manual snapshot`, or `dry-run`.

### 券商来源健康

Always show compact source capability and broker source tables. When
`runtime_health.py` returns `source_capability_health`, show it before broker
source health:

| capability | status | effect |
| --- | --- | --- |
| Longbridge broker skill | available / unauthorized / not_installed / missing / stale |  |
| Longbridge Terminal CLI | available / unauthorized / not_installed / missing / stale |  |
| Longbridge macrodata | available / unauthorized / not_installed / missing / stale |  |
| IBKR connector | available / unauthorized / not_installed / missing / stale |  |
| Manual snapshot | available / missing / stale |  |

If the user says Longbridge worked in another chat but the current chat cannot
see the capability, say: `当前 chat 未暴露 Longbridge skill capability；这不代表
Longbridge 不存在，只代表本轮不能直接调用。`

Then show broker source health:

| source | status | effect |
| --- | --- | --- |
| Longbridge | available / unauthorized / not_installed / missing / stale |  |
| IBKR | available / unauthorized / not_installed / missing / stale |  |
| Manual snapshot | available / missing / stale |  |

Use `current_mode` from `runtime_health.py` when available:

- `live read-only`: at least one authorized broker source is available.
- `manual snapshot`: no live broker source is available, but a user-approved
  snapshot is available.
- `dry-run`: no broker facts should be assumed.

If `current_mode` is `dry-run`, the next step can still proceed with public data
and plan context, but portfolio sizing, broker facts, and execution review must
be marked as reduced confidence.

### 宏观图触发判断

After the startup health block, apply `visual-trigger-policy.md`:

- if `macro-panel.json` is available and the next answer discusses strategy
  posture, rates pressure, risk-on/risk-off, or financial conditions, generate
  or request a `Macro Regime Mini-Panel`;
- if `portfolio_snapshot.csv` is available and the next answer discusses
  concentration, leveraged ETF exposure, cash pressure, or theme crowding,
  generate or request a `Position Risk Visual`;
- if either file is missing or stale, say why no visual appears instead of
  silently skipping the chart.
- if `macro-panel.json` is missing but a saved Longbridge macrodata or official
  fallback JSON is available, suggest `prepare_macro_panel.py --macrodata-json`
  as the next runtime step instead of inventing macro values.

## 券商只读来源设置

When runtime health reports broker-source status as `missing` or
`unauthorized`, enter `券商只读来源设置` instead of only reporting the gap.
This setup is a one-question read-only authorization preference check; it is not
plugin installation and not broker authentication by itself.

Ask the user which broker facts source to enable for Daily Ops:

1. `Longbridge read-only` for positions, executions/trades, orders/status, and
   authorized market data when the Longbridge skill/plugin is installed.
2. `IBKR read-only` for positions, executions/trades, orders/status, and
   authorized market data when the IBKR connector is enabled.
3. `Longbridge read-only + IBKR read-only` when both should be used, then ask
   for preferred source order if the two disagree.
4. `暂不启用` and continue this run with manual CSV or no broker facts.

If Longbridge is selected but unavailable, ask the user to install or enable the
Longbridge skill/plugin/terminal. A user-managed installation path can be:

```bash
brew install --cask longbridge/tap/longbridge-terminal
```

If IBKR is selected but unauthorized, ask the user to enable the IBKR connector
or continue without broker facts. Do not retry with a broker write-capable tool.

`券商只读来源设置` may propose a private runtime write such as source
preference or enabled source order, but only after a proposed write package is
confirmed. It must not read broker data until the user authorizes a read-only
source for the current run or stored private runtime config already allows it.

## Next Step Guidance

Daily Ops output must not end with a vague summary. After `建议下一步`, include
`下一步指引` that tells the user exactly what to do now and what the agent will
do after the reply.

The section should include:

- `默认建议`: one recommended path that removes the largest blocker first.
- `可选路径`: 2-4 alternatives when there are meaningful choices, such as
  `券商只读来源设置`, runtime initialization, ticker horizon confirmation,
  current-source refresh, or continuing reduced-scope.
- `你只需要回复`: a short copyable reply format the user can send.
- `我会执行`: the next focused workflow or runtime action after confirmation.

Keep this concise. Do not ask the user to choose from every possible module.
Prefer the shortest decision that unlocks the next useful Daily Ops step.

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
- 券商只读来源设置;
- 标的与交易想法周期确认;
- 建议下一步;
- 下一步指引;
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
