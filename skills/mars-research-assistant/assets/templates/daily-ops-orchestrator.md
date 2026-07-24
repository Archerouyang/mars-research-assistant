# 交易研究日程引导输出

Use this template when the user asks to start, continue, or check Daily Ops
without specifying every internal workflow.

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

## 缺失确认

List only confirmations that block useful output. If none, write `无阻塞确认`.
When reconciliation is unavailable, include the exact
`portfolio_reconciliation=unavailable` status and keep combined exposure
fail-closed until the missing broker-source confirmation is resolved.

## 券商只读来源设置

Include this section on every Daily Ops first start, including when unspecified
live broker sources default to `needs_review`. On later turns, `missing` or
`unauthorized` enters `券商只读来源设置`.

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

1. `可用研究摘要`：用当前公开/授权的非账户信源概括市场环境、下周 P0/P1
   事件和主题影响。
2. `降级范围`：明确未读取 broker、未验证组合暴露、未读取保存计划，且不生成
   具体 entry/exit trigger。
3. `下一步确认`：再请求 broker read-only、
   `ticker + trade_horizon + instrument` 和 runtime dry-run/初始化选择。

先摘要，后授权/初始化；本轮不会写 runtime。

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
