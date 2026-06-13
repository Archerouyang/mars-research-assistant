# Trading Research System Roadmap

## MVP Definition

Trading Research System is a plugin-first trading research and risk decision-support system. It turns information into verified trade ideas, planned trades, intraday setup scans, actual trade records, reviews, and statistics for improving the trading system.

It is not an automatic trading system and does not generate guaranteed buy/sell instructions.

## Priorities

### P0: Language And Research Note Template

Status: in progress.

Deliverables:

- Domain glossary in `CONTEXT.md`.
- Research memo template.
- Macro/rates/research-note/price-action/risk references.
- Plugin skill that routes tasks through the workflow.

### P1: Local Data Structure

Status: started.

Deliverables:

- Local daily directory convention: `data/daily/YYYY-MM-DD/`.
- `watchlist.csv`.
- `trade-plans.csv`.
- `intraday-watchlist.csv`.
- `trades.csv`.
- `portfolio.csv`.
- `reviews.md`.
- CSV schemas informed by Google Sheets `2026交易记录`.
- Daily folder initializer.
- First source of truth remains local daily records.

### P2: Analysis Modules

Status: started.

Deliverables:

- Portfolio risk exposure summary.
- Watchlist ranking and momentum-candidate prioritization.
- Closed-trade statistics from local `trades.csv`.
- Macro/rates filter.
- Research-note verification.
- Intraday setup scan scoped to planned trades.
- Price action timing using 20 EMA, 50 EMA, and multi-timeframe analysis.
- Option-flow anomaly analysis after data source selection.

### P3: Review Statistics

Status: planned.

Deliverables:

- Win rate.
- Average R.
- Expectancy.
- Drawdown.
- Setup performance.
- Instrument-type performance.
- Timeframe performance.
- Mistake-tag frequency.
- Confidence calibration.

### P4: External Connections And Automation

Status: planned.

Deliverables:

- One-way Google Sheets sync from local daily records.
- Google Drive research archive.
- IBKR market/account data.
- Option data API after vendor research.
- Daily market brief.
- Intraday plan monitor.
- Post-market review automation.

## MVP 1 Acceptance Criteria

MVP 1 is complete when:

1. The plugin contains the research workflow skill and references.
2. Local CSV/Markdown templates exist for watchlist, trade plans, trades, reviews, research-note logs, and portfolio holdings.
3. Scripts can summarize portfolio exposure and rank watchlist candidates from template CSV files.
4. The trade journal schema can represent current `2026交易记录` fields plus missing statistics fields.
5. The plugin validates and can be installed from the personal marketplace.

## Deferred

- Persistent frontend/dashboard.
- Full automatic option data ingestion.
- Full momentum model vendor selection.
- Auto-order placement.
- Two-way Google Sheets sync.
