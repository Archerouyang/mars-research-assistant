# Portfolio Research

Use confirmed read-only holdings only. Keep source coverage and reconciliation
visible before aggregating accounts.

Evaluate direct market value, delta/notional when applicable, symbol, theme,
industry, product, broker, currency, cash/collateral, leverage, path dependency,
and stress scenarios. Disclose user exclusions while omitting them from the
requested calculation.

The standalone Board should lead with numeric concentration and product-risk visuals.
Text explains the decision and constraints after the exposure is inspectable.
Never expose account identifiers or raw broker rows.

## Frozen Standalone Board Contract

The user accepted and froze the Portfolio Risk structure on 2026-07-20, then
selected standalone-only delivery on 2026-07-22. Preserve this information
architecture and interaction order in the self-contained Board:

1. summary strip: capital context, cash buffer, delta-equivalent directional
   exposure, and worst standardized stress;
2. one concise primary-risk statement;
3. top-level views in this order: overview, symbol, fundamentals, theme,
   product, broker, and stress;
4. overview: leverage-adjusted underlying concentration beside the ranked risk
   ledger;
5. symbol, theme, product, and broker: comparable direct value,
   delta-equivalent exposure, and notional exposure;
6. fundamentals: look-through underlying tabs with valuation, earnings,
   positioning, and volatility subviews in that order;
7. stress: a dedicated comparison of scenario, potential loss, capital/NAV
   impact, assumptions, and risk response, visibly labelled as non-predictive;
8. source coverage, `as_of`, leverage share, and user exclusions remain visible.

Source-backed values, timestamps, concise copy, accessibility, responsive
behavior, and compatible defect fixes may change without redesign approval.
Changing the view order, first-viewport hierarchy, look-through mapping,
fundamental subviews, stress meaning, or read-only/privacy boundary requires
renewed user acceptance.

## Supported Helpers

- ingest and normalize saved read-only facts with
  `scripts/broker_snapshot_ingest.py`;
- query supported read-only broker surfaces with
  `scripts/ibkr_connector_adapter.py` and `scripts/longbridge_cli_adapter.py`;
- repair an explicitly selected local snapshot with
  `scripts/repair_portfolio_snapshot.py`;
- build read-only position and risk summaries with
  `scripts/position_daily_report.py` and `scripts/portfolio_risk.py`.

These helpers preserve source coverage and reconciliation state. They never
place, modify, or cancel orders.
