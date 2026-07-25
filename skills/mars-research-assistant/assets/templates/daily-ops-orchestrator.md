# 交易研究日程引导输出

Use this template when the user asks to start, continue, or check Daily Ops
without specifying every internal workflow.

For an unscoped start, do not render the status sections below before the
required Macro standalone Board or its Data Acquisition Blocker. The Board or
Blocker is the first decision-bearing artifact; use this template afterward for
concise state, authorization, and next-step copy.

## 当前日程阶段

- stage:
- reason:
- confidence:

## 读取状态

- runtime health:
- runtime_dir:
- runtime_origin:
- formal runtime:
- startup_status:
- startup_reason:
- 当前模式:
- `ops-state.md`:
- `market-plan.md`:
- `trading-profile.md`:
- `daily/YYYY-MM-DD/`:
- broker source:
- missing data:

### 运行状态检查

Use the formal runtime path from `runtime_dir`; default is
`~/Documents/mars-research-assistant-runtime` unless the user or environment overrides it.
Do not treat repo fixtures, templates, or example plans as active runtime state.

| item | status | note |
| --- | --- | --- |
| runtime_dir |  |  |
| runtime_origin |  |  |
| formal runtime |  |  |
| startup_status |  |  |
| startup_reason |  |  |
| current_mode |  | 当前模式 |
| ops-state.md |  |  |
| market-plan.md |  |  |
| trading-profile.md |  |  |
| macro-panel.json |  | status only; keep the separate macro source section below |
| portfolio_snapshot.csv |  | status only; do not render private rows |
| daily/YYYY-MM-DD/ |  |  |

### 券商来源健康

Always include this table during a new Daily Ops chat, even when broker facts
are not needed yet.

Render `source_capability_health` before `broker_source_health`. Capability
availability and broker authorization are separate facts.

| capability | status | effect |
| --- | --- | --- |
| Longbridge broker skill | available / unauthorized / partial_data / upstream_error / empty_positions_unverified / needs_review / not_installed / missing / stale | preserve the exact runtime-health capability status; do not infer broker authorization |
| Longbridge Terminal CLI | available / unauthorized / partial_data / upstream_error / empty_positions_unverified / needs_review / not_installed / missing / stale | preserve the exact runtime-health capability status; do not infer broker authorization |
| Longbridge macrodata | available / unauthorized / partial_data / upstream_error / needs_review / not_installed / missing / stale | macro-data capability, not a broker account source |
| Official source fallback | available / partial_data / upstream_error / needs_review / missing / stale | official/public macro fallback capability |
| IBKR connector | available / unauthorized / partial_data / upstream_error / empty_positions_unverified / needs_review / not_installed / missing / stale | preserve the exact runtime-health capability status; do not infer broker authorization |
| Manual snapshot | available / needs_review / missing / stale | saved-input capability, not live authorization |

| source | status | effect |
| --- | --- | --- |
| Longbridge | available / unauthorized / partial_data / upstream_error / empty_positions_unverified / needs_review / not_installed / missing / stale |  |
| IBKR | available / unauthorized / partial_data / upstream_error / empty_positions_unverified / needs_review / not_installed / missing / stale |  |
| Manual snapshot | available / missing / stale |  |
| portfolio_reconciliation | confirmed / not_confirmed / unavailable | include excluded sources and missing confirmation when not confirmed |

If `portfolio_reconciliation=unavailable`, preserve the exact status, list
excluded sources, and state that combined portfolio exposure is fail-closed.

Do not collapse `partial_data`, `upstream_error`,
`empty_positions_unverified`, or `needs_review` into `unauthorized`.

### 宏观数据来源状态

Keep this separate from runtime and broker health.

| item | source status | effect |
| --- | --- | --- |
| macro-panel.json | available / missing / stale / needs_review |  |
| authorized/current macro values | available / missing / needs_review |  |

Disclose fixture/debug inputs explicitly. If no authorized/current macro values
exist, do not invent actual macro readings.

## 无标的 Daily Ops 启动基线

仅当用户未点名标的、研报或 PA 时使用。按以下顺序输出：

1. 每次阶段转换先执行 `python3 scripts/daily_ops_routing.py`，传入当前的 intent、macro、broker authorization 与 portfolio state。脚本返回的 `required_actions` 是强制交付，`forbidden_actions` 不得出现在本轮输出或工具路由中。
2. 第一轮 `macro_state=pending`：完整直接公开字段通过后，必须以其 canonical snapshot 构建 `ResearchResult(result_kind=macro, visual.adapter=macro)`，运行 `scripts/research_result.py`，并交付生成的 `standalone_board/research-brief.html`。任一必填字段失败才交付唯一的 `Data Acquisition Blocker`。不能用文字晨报、市场摘要、`visualize`、手写 HTML 或「下一步建议」代替。
3. `macro_state=delivered` 且未获 broker 只读授权：只询问授权；此时不提出 ticker、周期、公司研究或 PA。
4. 授权并选定唯一默认 broker 后，先读取该 broker 的许可持仓与资本字段，再分类：`ready` 和 `option_overlay_partial` 都必须以验证通过的 canonical Portfolio snapshot（或兼容 legacy normalized panel）构建 `ResearchResult(result_kind=portfolio, visual.adapter=portfolio)`，运行 `scripts/research_result.py`，并交付冻结的 Portfolio Risk standalone Board；`core_gap` 才明确持仓数据缺口，且不以个股分析代替。
5. 期权缺 multiplier、Greeks、delta 或可靠 notional，但具备身份、方向、市值、币种、时间戳和现金/NAV 上下文时，使用 `option_overlay_partial`：Board 保留该期权的来源和市值，明确其不进入 delta/stress 计算；不能补零、不能自行读/请求第二券商。
6. Macro 与持仓风险结果完成后，才请用户指定希望研究的 ticker；个股研究和 PA 仅针对用户点名标的。用户解释期权是备兑 Call、LEAP、对冲、TP 或降成本层，只用于分类，不构成 GOOGL 或任何标的的分析请求。

每个阶段的 Board 或 Blocker 都是第一个决策性用户交付。不能先渲染运行时状态表、券商健康表、文字宏观报告或推荐标的；这些信息只作为 Board/Blocker 内的来源和缺口，或其后的简短说明。

Macro 必须复用 `macro_board_visual.py`，Portfolio 必须复用
`portfolio_board_visual.py`；两者经 `ResearchResult -> DeliveryPacket` 输出。
此前冻结的组件 token、视图顺序和交互不允许在 Daily Ops 中重写。不能用
`visualize`、临时前端或自写 CSS 替代。

用户直接要求某个标的、研报或 PA 时，可以走相应的聚焦路径，不强制补做本基线。

## 缺失确认

List only confirmations that block useful output. If none, write `无阻塞确认`.
When reconciliation is unavailable, include the exact
`portfolio_reconciliation=unavailable` status and keep combined exposure
fail-closed until the missing broker-source confirmation is resolved.

## 券商只读来源设置

Render this section only after the required Macro Board or Data Acquisition
Blocker. Include it on every Daily Ops first start when read-only broker access
is still needed, including when unspecified live broker sources default to
`needs_review`. On later turns, `missing` or `unauthorized` enters `券商只读来源设置`.

On later turns, `needs_review` asks for matching verification/retry and
does not repeat authorization setup. `stale`, `partial_data`, `upstream_error`,
and `empty_positions_unverified` retain distinct availability or verification paths;
preserve the exact status and put the matching action under `缺失确认` / `下一步指引`.

Ask one concise question:

```text
是否启用只读 broker 数据？选项：Longbridge read-only / IBKR read-only / 两者都启用 / 暂不启用，本轮用 manual CSV 或 no broker facts。
```

State that this is read-only setup only. Do not read broker data, install
software, save source preferences, or write runtime files until the user
confirms.

## 标的与交易想法周期确认

Group every tradable idea by:

```text
ticker + trade_horizon + instrument
```

If trade horizon is missing, ask one concise question and do not generate entry
or exit triggers.

| ticker | trade_horizon | instrument | status | needed confirmation |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 周末首次启动

当 `startup_status=partial / uninitialized` 时，保持只读并按以下顺序输出：

1. 仍从 `macro_state=pending` 的 Macro standalone Board 或唯一的 Data
   Acquisition Blocker 开始，不能输出 `可用研究摘要` 代替。
2. 宏观结果后才说明运行时、broker 与保存计划的降级范围；不生成具体
   entry/exit trigger。
3. 未授权时只请求 broker read-only；授权和唯一默认来源确认后再走持仓
   基线。只有两张基线 Board（或明确 Blocker/gap）结束，才请求用户点名的
   `ticker + trade_horizon + instrument`。

不因运行时缺失跳过 Board；本轮不会写 runtime。

## 建议下一步

State one `建议下一步`. It should be the single workflow that best
unblocks the user's current Daily Ops loop.

## 下一步指引

- 默认建议:
- 可选路径:
- 你只需要回复:
- 我会执行:

Make this section operational, not descriptive. Give the user a short copyable
reply format such as:

```text
券商来源用 <Longbridge read-only / IBKR read-only / 两者 / 暂不启用>；
这些 ticker 的周期是 <ticker + trade_horizon + instrument>；
允许/不允许初始化今天 runtime 草稿。
```

If `daily/YYYY-MM-DD/`, `trade-plans.csv`, or `intraday-watchlist.csv` is
missing, propose `prepare_daily_runtime.py --dry-run` first. After confirmation,
`prepare_daily_runtime.py` may initialize today runtime 草稿 with header-only
`trade-plans.csv` and `intraday-watchlist.csv`; it 不会覆盖已有文件 by default,
does not read broker/market data, and does not create setup rows.

If those files exist but are header-only, ask the user to confirm the planned
`ticker + trade_horizon + instrument` setup rows. After confirmation, convert
them into user-confirmed setup JSON and use `prepare_setup_rows.py` to populate
populate setup rows. Do not use it to parse free-form trade ideas or invent plans.

## 为什么现在做这一步

Explain the routing reason in one or two bullets.

## 确认后我会执行

State the focused workflow or action that will run after the user confirms.
Keep this user-facing; do not make the user memorize skill names.

## 安全边界

- Do not create buy/sell instructions.
- Do not place, modify, cancel, close, or approve orders.
- Do not read broker data without read-only authorization.
- Do not write runtime files unless the user confirms a proposed write package.
- Do not create real automation unless the automation setup checklist is
  complete.
