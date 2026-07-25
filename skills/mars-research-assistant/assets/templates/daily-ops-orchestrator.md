# 交易研究日程引导输出

Use this template only after the required Macro Board or its Data Acquisition
Blocker. It must not replace either artifact with a prose market summary.

## 当前日程阶段

- stage:
- reason:
- confidence:

## 运行状态

| item | status | note |
| --- | --- | --- |
| runtime_dir |  |  |
| formal runtime |  |  |
| startup_status |  |  |
| current_mode |  |  |
| IBKR capability |  | capability only; no account read |

## 无标的 Daily Ops 启动基线

1. Capability-only check IBKR. It reads no account, holdings,
   balance, order, or credentials.
2. Acquire required Macro fields: exact IBKR market records first,
   exact public primary-source fallback per missing field. Deliver the canonical
   Macro Board or exactly one Data Acquisition Blocker.
3. Ask: `是否读取并展示 IBKR 持仓，还是直接研究一个标的？`
4. Only after explicit confirmation, read IBKR and display:
   broker, symbol, quantity, latest price, market value, cost, unrealized P&L,
   cash, currency, and retrieval time. Missing factual fields are `不可用`.
5. A user-named ticker directly starts the full package: industry events,
   fundamentals, catalysts, valuation, counter-thesis, and the frozen 4H PA
   standalone Board. User scope restrictions narrow the package.

Never derive concentration, leverage, delta, stress, risk scores, portfolio
recommendations, or a next trade from the holdings display. Never start PA or
company analysis without the user's named instrument request.

## 下一步指引

- 建议下一步:
- 你只需要回复:
- 我会执行:

Use one short, copyable reply. Do not ask the user to select a workflow the
router has already determined.

## 安全边界

- Do not create, modify, cancel, close, or approve orders.
- Do not read holdings without fresh per-request user consent.
- Do not write runtime files unless the user confirms the proposed write.
