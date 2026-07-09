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
| `longbridge_terminal_cli` | Longbridge Terminal CLI | positions/portfolio JSON produced by user-installed terminal | broker-live runtime views |
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
| `longbridge_broker_skill` | available / unauthorized / not_installed / missing / stale | whether Longbridge skill read-only account facts are usable |
| `longbridge_terminal_cli` | available / unauthorized / not_installed / missing / stale | whether Longbridge Terminal CLI read-only account facts are usable |
| `longbridge_macrodata` | available / unauthorized / not_installed / missing / stale | whether Longbridge macrodata values are usable |
| `ibkr_connector` | available / unauthorized / not_installed / missing / stale | whether IBKR connector facts are usable |
| `manual_snapshot` | available / missing / stale | whether a user-approved snapshot is usable |

If the Longbridge skill worked in another chat but is not visible in the current
Codex session, or not visible in the current Codex session after a fresh tool
search, mark the relevant capability `not_installed` and say:

```text
当前 chat 未暴露 Longbridge skill capability；这不代表 Longbridge 不存在，只代表本轮不能直接调用。
```

If the current machine has the user-installed Longbridge Terminal CLI and the
user has authorized read-only account access for this run, mark
`longbridge_terminal_cli=available` separately. Do not use terminal availability
as proof that `longbridge_macrodata` or a Codex-native Longbridge skill is
available.

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

## Terminal CLI Adapter

When `longbridge_terminal_cli` is available and authorized, use
`longbridge_cli_adapter.py` only on saved JSON produced by read-only CLI
commands such as `longbridge portfolio --format json`. The adapter maps the
saved JSON into:

- `{runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv`

The CLI adapter must disclose:

- `No live broker reads`;
- `No order actions`;
- the source JSON file or stdin;
- the snapshot timestamp used for `source_timestamp`.

It preserves each position or cash row's source currency and does not
FX-convert values. If a portfolio snapshot contains multiple currencies,
downstream reports must either convert through a separate authorized FX step or
label total exposure as multi-currency / partial.

The CLI adapter must not run `longbridge order buy`, `longbridge order sell`,
`longbridge order cancel`, `longbridge order replace`, or any other broker write
command.

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

When an authorized Longbridge macrodata read has been saved or passed into the
runtime, normalize it with:

```bash
python3 plugins/trading-research-system/scripts/prepare_macro_panel.py \
  --date YYYY-MM-DD \
  --macrodata-json /path/to/longbridge-macrodata.json \
  --as-of YYYY-MM-DDTHH:MM:SSZ
```

When the source is official fallback JSON rather than Longbridge macrodata, add
`--source-capability official_source_fallback` so the runtime panel does not
mislabel the data source.

`prepare_macro_panel.py` is the runtime wrapper around
`longbridge_macrodata_adapter.py`: it writes the standard
`{runtime_dir}/daily/YYYY-MM-DD/macro-panel.json`, keeps existing files by
default, and requires `--overwrite` before refreshing an existing panel. The
adapter reports `No live macrodata reads`, `not a broker account source`, and
`No order actions`. It standardizes the minimum macro panel into
`macro-panel.json`; it does not call Longbridge by itself and does not replace
official S0 policy/news confirmation.

## Safety Boundary

The Longbridge skill adapter is read-only. It must not create, submit, cancel,
or imply approval of real orders. It must not turn a Longbridge read into a trade
signal. It only prepares facts for the Trading Research workflows.
