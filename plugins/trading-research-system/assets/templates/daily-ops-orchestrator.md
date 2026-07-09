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
- formal runtime:
- 当前模式:
- `ops-state.md`:
- `market-plan.md`:
- `trading-profile.md`:
- `daily/YYYY-MM-DD/`:
- optional external momentum snapshot:
- broker source:
- missing data:

### 运行状态检查

Use the formal runtime path from `runtime_dir`; default is
`~/Documents/dailytrades-runtime` unless the user or environment overrides it.
Do not treat repo fixtures, templates, or example plans as active runtime state.

| item | status | note |
| --- | --- | --- |
| runtime_dir |  |  |
| formal runtime |  |  |
| ops-state.md |  |  |
| market-plan.md |  |  |
| trading-profile.md |  |  |
| daily/YYYY-MM-DD/ |  |  |

### 券商来源健康

Always include this table during a new Daily Ops chat, even when broker facts
are not needed yet.

| source | status | effect |
| --- | --- | --- |
| Longbridge | available / unauthorized / not_installed / missing / stale |  |
| IBKR | available / unauthorized / not_installed / missing / stale |  |
| Manual snapshot | available / missing / stale |  |

当前模式: `live read-only` / `manual snapshot` / `dry-run`

## 缺失确认

List only confirmations that block useful output. If none, write `无阻塞确认`.

## 券商只读来源设置

Include this section when broker source is `missing`, `stale`, or
`unauthorized`, or when the next recommended action needs holdings, executions,
orders/status, margin, cash, or position risk.

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
