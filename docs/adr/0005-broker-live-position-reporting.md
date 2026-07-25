# Broker-live position reporting

> Superseded by ADR 0012 and ADR 0013. Account and holdings reads are outside
> the stateless Skill boundary.

> Superseded by Issue #86 for Mars Research Assistant. The current Skill
> supports IBKR only, provides a factual holdings display only after per-request
> consent, and does not expose the former multi-broker or portfolio-risk flow.
> The remainder of this ADR is retained as historical context.

The system will treat IBKR, Longbridge, and other broker integrations as read-only live sources for positions, account risk, executions, and order status. It will not require a local spreadsheet, Google Sheet, or durable `trades.csv` copy of broker trade facts as the product source of truth.

**Considered Options**

- Persist normalized broker facts into local CSV files and optionally mirror them to Google Sheets.
- Read broker facts live on demand and save only derived summaries, charts, and review context.
- Keep only broker-native views and avoid any local artifacts.

**Decision**

Use broker-live reads for objective broker facts. The Skill may save derived artifacts such as position daily reports, exposure charts, setup review notes, and statistics snapshots, but should avoid persisting unnecessary raw broker exports or full trade-record tables.

**Consequences**

- Position and risk reports should prefer authorized Longbridge or IBKR read-only data at run time.
- Google Sheets is no longer a trade-record layer; it may only mirror non-sensitive summaries if the user explicitly asks.
- Trade review should focus on user context: plan linkage, market background, signal bar, confidence, mistake tags, and lessons.
- Statistics that require historical broker facts depend on broker API history availability or user-approved snapshots.
- Reports must state data source, read time, broker/account coverage, missing fields, and whether data may be delayed.
