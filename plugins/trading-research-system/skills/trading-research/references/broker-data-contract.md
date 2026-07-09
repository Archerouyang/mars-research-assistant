# Broker Data Contract

Use this reference when reading positions, executions, or order status from broker connectors, broker skills, or user-provided CSV files.

The Trading Research System is broker-agnostic. Broker sources provide read-only data and map it into a standard runtime view for analysis. The trading plugin does not place orders, modify accounts, cancel orders, or rebalance positions.

## Broker Sources

Supported source categories:

- IBKR connector when available and authorized.
- Longbridge skill/plugin/terminal when available and authorized.
- Manual CSV import.

Ask the user before the first broker read in a session:

```text
我需要读取券商数据来做持仓/成交对齐。可用来源：IBKR、Longbridge、手动 CSV。本次使用哪个？
```

If Longbridge is selected but unavailable, ask the user to install or enable the relevant skill/plugin. A user-managed installation path can be:

```bash
brew install --cask longbridge/tap/longbridge-terminal
```

Do not run that install command automatically from this plugin.

## Read-Only Boundary

Allowed:

- read positions;
- read executions/trades;
- read order status;
- read account-level risk fields when authorized;
- read market data when the selected broker source exposes it and the user requested it.

Not allowed in this plugin:

- create real orders;
- modify or cancel orders;
- close positions;
- rebalance accounts;
- write to broker accounts.

Even if a connected agent has broker write capability, this plugin should not call it.

## Raw Snapshots

Raw broker snapshots are optional. Store them by broker and date only when the user explicitly asks for a snapshot or when a fixture/debug run needs local files:

```text
{runtime_dir}/broker/ibkr/YYYY-MM-DD/positions.json
{runtime_dir}/broker/ibkr/YYYY-MM-DD/executions.json
{runtime_dir}/broker/ibkr/YYYY-MM-DD/orders.json
{runtime_dir}/broker/longbridge/YYYY-MM-DD/positions.json
{runtime_dir}/broker/longbridge/YYYY-MM-DD/executions.json
{runtime_dir}/broker/longbridge/YYYY-MM-DD/orders.json
```

Raw snapshots keep source detail for debugging adapter mappings. They are not required for normal broker-live reporting and should not be treated as the durable source of truth.

## Standard Runtime View

When scripts or fixtures need files, map broker data into:

```text
{runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv
{runtime_dir}/daily/YYYY-MM-DD/broker_executions.csv
{runtime_dir}/daily/YYYY-MM-DD/broker_orders.csv
```

Core risk, review, and statistics workflows should consume these fields from the broker-live runtime view. File materialization is an implementation detail for tests, fixtures, or user-approved snapshots.

For position daily reports, broker adapters should produce the standard
`portfolio_snapshot.csv` view, then use `position_daily_report.py` to render the
concise report. Keep connector-specific mapping outside the renderer so the
report stays broker-agnostic.

When a live connector is not being called by the plugin, use
`broker_snapshot_ingest.py` to normalize a read-only broker CSV export into the
same standard `portfolio_snapshot.csv` view:

This remains the read-only broker export path for CSV artifacts.

```bash
python3 plugins/trading-research-system/scripts/broker_snapshot_ingest.py \
  --input IBKR:/path/to/ibkr-positions.csv \
  --input Longbridge:/path/to/longbridge-positions.csv \
  --output {runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv \
  --as-of YYYY-MM-DDTHH:MM:SSZ
```

This is an adapter boundary, not broker access. It consumes user-approved local
exports or connector-produced CSV artifacts and does not perform live broker
reads, market-data calls, or order actions.

When the IBKR connector is authorized, the IBKR connector adapter can normalize
saved read-only connector results. Read-only calls such as
`get_account_positions` and `get_account_balances` can be saved as JSON and
normalized into the same standard runtime view:

```bash
python3 plugins/trading-research-system/scripts/ibkr_connector_adapter.py \
  --positions-json /tmp/ibkr-positions.json \
  --balances-json /tmp/ibkr-balances.json \
  --output {runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv \
  --as-of YYYY-MM-DDTHH:MM:SSZ
```

`ibkr_connector_adapter.py` consumes saved IBKR connector JSON only. No live broker reads.
It does not call the IBKR connector, perform market-data calls, or create,
modify, cancel, or submit orders. No order actions. The live read step must stay
explicit and read-only; the adapter step is just source-shape normalization.

When Longbridge Terminal CLI is user-installed and authorized, a read-only
portfolio command can produce JSON for a local adapter step:

```bash
longbridge portfolio --format json > /tmp/longbridge-portfolio.json
python3 plugins/trading-research-system/scripts/longbridge_cli_adapter.py \
  --portfolio-json /tmp/longbridge-portfolio.json \
  --output {runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv \
  --as-of YYYY-MM-DDTHH:MM:SSZ
```

`longbridge_cli_adapter.py` consumes saved Longbridge CLI JSON only. No live broker reads.
It does not run the Longbridge CLI, perform live broker reads, call market
data, or create/modify/cancel/submit orders.

The CLI adapter preserves each row's source currency and does not perform FX
conversion. Downstream reports must not aggregate multi-currency rows as one
currency unless a separate authorized FX conversion step has produced converted
values.

After adapter output is available, use `repair_portfolio_snapshot.py` when a
standard `portfolio_snapshot.csv` has stale or unmapped product/theme fields.
This repair step remaps `underlying`, `instrument_type`, and `theme_id` from
known symbol/product rules and appends a `Snapshot repair:` note. It consumes
the existing runtime CSV only; No live broker reads, no market-data calls, and
No order actions.

## Portfolio Snapshot Schema

Required columns:

- `as_of`
- `broker`
- `account_id`
- `symbol`
- `underlying`
- `instrument_type`
- `direction`
- `quantity`
- `avg_cost`
- `market_price`
- `market_value`
- `currency`
- `unrealized_pnl`
- `realized_pnl`
- `delta_exposure`
- `notional_exposure`
- `theme_id`
- `source_timestamp`
- `notes`

Default risk view is total portfolio exposure across all brokers, with broker/account breakdowns preserved.

## Execution Schema

Required columns:

- `execution_id`
- `broker`
- `account_id`
- `trade_id`
- `order_id`
- `symbol`
- `underlying`
- `side`
- `quantity`
- `price`
- `fees`
- `currency`
- `execution_time`
- `instrument_type`
- `setup_id`
- `source_timestamp`
- `notes`

Use broker execution IDs plus account and timestamp to detect duplicates. If the broker does not provide a stable execution ID, derive a deterministic import key from broker, account, symbol, side, quantity, price, and timestamp.

## Order Status Schema

Required columns:

- `order_id`
- `broker`
- `account_id`
- `symbol`
- `underlying`
- `side`
- `order_type`
- `status`
- `quantity`
- `filled_quantity`
- `limit_price`
- `avg_fill_price`
- `currency`
- `created_time`
- `updated_time`
- `instrument_type`
- `setup_id`
- `source_timestamp`
- `notes`

Order status is used to trigger review intake and reconcile actual trades. It is not used for order modification.

## Reconciliation Rules

- Preserve `broker` and `account_id` on every row.
- Aggregate portfolio exposure by total, broker/account, underlying, theme, and instrument type.
- Link executions to setups when `setup_id` is known; otherwise use interactive review to fill it.
- Do not silently overwrite user-entered review fields with broker data.
- If two broker sources disagree, mark the row `needs_review` in notes or create a reconciliation note.
- If connector authorization fails, fall back to manual CSV and state what could not be verified.

## Longbridge First Phase

Longbridge broker integration should be implemented as a Longbridge
skill/plugin/terminal adapter. It only needs these read-only account
capabilities first:

The Longbridge skill/plugin adapter and the Longbridge Terminal CLI adapter are
separate implementation paths that map into the same standard runtime views.

- positions;
- executions/trades;
- orders/status.

Do not make Longbridge market data a first-phase hard dependency. Use IBKR, public sources, or authorized market data sources for prices/charts when available.

Longbridge `macrodata` is a separate macro-data source. It is exposed through
the Longbridge skill/plugin capability when available. It belongs in
`macro-policy-filter.md` and macro/rates workflows, not in broker account
reconciliation.

Longbridge broker source does not become the source for macro policy or industry news.
