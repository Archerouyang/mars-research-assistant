# Daily Ops Orchestrator Output

Use this template when the user asks to start, continue, or check Daily Ops
without specifying every internal workflow.

## 当前日程阶段

- stage:
- reason:
- confidence:

## 读取状态

- runtime health:
- `ops-state.md`:
- `market-plan.md`:
- `trading-profile.md`:
- KVN snapshot:
- broker source:
- missing data:

## 缺失确认

List only confirmations that block useful output. If none, write `无阻塞确认`.

## Broker Source Setup

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

## Ticker / Setup 周期确认

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

State one Next Recommended Action. It should be the single workflow that best
unblocks the user's current Daily Ops loop.

## 下一步指引

- 默认建议:
- 可选路径:
- 你只需要回复:
- 我会执行:

Make this section operational, not descriptive. Give the user a short copyable
reply format such as:

```text
Broker 用 <Longbridge read-only / IBKR read-only / 两者 / 暂不启用>；
这些 ticker 的周期是 <ticker + trade_horizon + instrument>；
允许/不允许初始化今天 runtime 草稿。
```

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
