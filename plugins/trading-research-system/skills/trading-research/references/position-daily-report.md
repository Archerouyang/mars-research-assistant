# Position Daily Report

Use this reference for scheduled holdings and portfolio-risk reports.

The report is broker-live by default: read positions, account metrics, balances, and relevant order/execution facts from authorized read-only broker sources at run time. Do not require Google Sheets, local trade-record tables, or saved broker exports.

## Source Order

Use the first available source the user authorized for this run:

1. Longbridge skill/plugin.
2. IBKR connector.
3. Manual user export.

If no source is available, state the gap and do not invent positions.

## Script Path

When a standard runtime view is available, render the report with:

```bash
python3 plugins/trading-research-system/scripts/position_daily_report.py \
  {runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv \
  --date YYYY-MM-DD \
  --source "Longbridge / IBKR / manual / broker-live fixture"
```

Live broker adapters should map read-only broker facts into
`portfolio_snapshot.csv` first, then call the report renderer. The renderer is a
reporting layer only; it does not connect to brokers, save raw exports, or place
orders.

## Required Disclosures

Every report must include:

- source used;
- read time and timezone;
- broker/account coverage;
- whether values are live, delayed, prior close, or user-provided;
- missing fields;
- whether any snapshot or visualization artifact was saved.

## User-Facing Output

Keep the output concise and decision-useful:

1. **结论**: one to three bullets on today’s portfolio posture.
2. **需要用户决策**: only decisions that matter today.
3. **风险变化**: concentration, cash/margin, leverage, option expiry, event risk, correlated beta, and theme crowding.
4. **持仓影响**: existing holdings that need add/trim/hold/review attention according to the Active Market Plan.
5. **可视化**: links or requested artifacts for allocation, PnL contribution, theme exposure, and risk flags.
6. **缺口**: missing broker permissions, stale data, unavailable history, or fields that require user confirmation.

## Visualization Fields

When chart artifacts are generated, prefer:

- allocation by symbol;
- allocation by theme/sector;
- daily or since-open PnL contribution when available;
- unrealized PnL by holding;
- cash, margin, and buying power bands;
- option expiry and leveraged-product exposure;
- concentration heatmap.

Do not display unnecessary account identifiers, raw execution details, or private broker exports in public files.

## Safety

The report may say a holding needs attention, review, add-zone validation, TP/rebalance review, or risk-budget review. It must not place, modify, cancel, or imply approval of orders.
The renderer does not place orders and must not call broker write actions.
