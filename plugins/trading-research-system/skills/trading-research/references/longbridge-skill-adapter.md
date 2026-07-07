# Longbridge Skill Adapter

Use this reference when a Trading Research workflow wants to read Longbridge
through the installed Longbridge skill/plugin. This is a capability adapter
contract, not an instruction to install Longbridge, authenticate an account, or
call any broker write action.

## Capability Split

Treat Longbridge as two separate read-only capabilities:

| capability id | user-facing name | purpose | standard output |
| --- | --- | --- | --- |
| `longbridge_broker_skill` | Longbridge broker skill | positions, executions/trades, orders/status | broker-live runtime views |
| `longbridge_macrodata` | Longbridge macrodata | rates, yields, credit, FX, commodities, liquidity, macro indicators | macro panel runtime view |

The Longbridge broker skill and Longbridge macrodata are not interchangeable.
Broker facts do not prove macro regime, and macrodata does not prove account
positions or executions.

## Runtime Health

Before using Longbridge, call `runtime_health.py` or perform the equivalent
status check and show `source_capability_health`.

Required rows:

| capability | status | meaning |
| --- | --- | --- |
| `longbridge_broker_skill` | available / unauthorized / not_installed / missing / stale | whether Longbridge read-only account facts are usable |
| `longbridge_macrodata` | available / unauthorized / not_installed / missing / stale | whether Longbridge macrodata values are usable |
| `ibkr_connector` | available / unauthorized / not_installed / missing / stale | whether IBKR connector facts are usable |
| `manual_snapshot` | available / missing / stale | whether a user-approved snapshot is usable |

If the Longbridge skill worked in another chat but is not visible in the current
Codex session, or not visible in the current Codex session after a fresh tool
search, mark the relevant capability `not_installed` and say:

```text
当前 chat 未暴露 Longbridge skill capability；这不代表 Longbridge 不存在，只代表本轮不能直接调用。
```

## Broker Skill Adapter

When `longbridge_broker_skill` is available and authorized, the adapter may read
only:

- positions;
- executions/trades;
- orders/status;
- account-level risk facts if the Longbridge skill exposes them as read-only.

Map results into the standard broker-live runtime views:

- `{runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv`
- `{runtime_dir}/daily/YYYY-MM-DD/broker_executions.csv`
- `{runtime_dir}/daily/YYYY-MM-DD/broker_orders.csv`

Do not pass raw Longbridge shapes directly into portfolio risk, position daily
report, trade review, or statistics workflows. The adapter boundary exists so
the rest of the plugin can stay broker-agnostic.

## Macrodata Adapter

When `longbridge_macrodata` is available and authorized, use it before IBKR
market data or web-only commentary for actual macro and financial-condition
values.

Minimum macro panel:

| field | purpose |
| --- | --- |
| `10Y` | long-rate pressure on growth / AI / semis |
| `30Y` | duration and fiscal-risk pressure |
| `HYG/LQD` | credit risk appetite |
| `DXY` | USD liquidity / earnings pressure |
| `Oil` | inflation and geopolitical shock pressure |
| `Gold` | defensive / easing hedge confirmation |
| `liquidity` | reserves, RRP, TGA, or configured liquidity proxy |

Map results into a standard macro panel runtime view:

- `{runtime_dir}/daily/YYYY-MM-DD/macro-panel.json`

The macro panel must preserve `value`, `change_5d`, `change_20d` when available,
`threshold`, `source`, and `timestamp`. If Longbridge macrodata is unavailable,
use official source fallback or mark the macro read degraded.

## Safety Boundary

The Longbridge skill adapter is read-only. It must not create, submit, cancel,
or imply approval of real orders. It must not turn a Longbridge read into a trade
signal. It only prepares facts for the Trading Research workflows.
