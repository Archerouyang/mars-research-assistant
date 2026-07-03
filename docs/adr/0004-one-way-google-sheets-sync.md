# One-way Google Sheets sync

Status: superseded for trade records by [0005 Broker-live position reporting](0005-broker-live-position-reporting.md). Google Sheets may still be considered later for non-sensitive summaries or report indexes, but it is no longer the trade-record layer.

Google Sheets sync will be one-way from local daily records to Google Sheets. Local `data/daily/YYYY-MM-DD/` records remain the first source of truth; Google Sheets is a mirror, review, filtering, and cross-device viewing layer.

**Considered Options**

- One-way sync from local files to Google Sheets.
- Two-way sync between local files and Google Sheets.
- Google Sheets as the only source of truth.

**Consequences**

- The system avoids edit conflicts between local CSV/Markdown and Sheets.
- Git history can preserve the canonical local record.
- Google Sheets can still provide views, filters, pivots, and dashboards.
- If a user edits Google Sheets manually, those edits must be reconciled explicitly rather than silently syncing back.
