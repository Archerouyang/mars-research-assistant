# Daily Ops Orchestrator Output

Use this template when the user asks to start, continue, or check the trading
workflow without specifying every internal workflow.

## 当前流程阶段

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
