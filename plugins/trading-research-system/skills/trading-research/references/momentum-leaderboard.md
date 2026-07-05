# Momentum Leaderboard

Use this reference when a task needs the KVN Momentum Leaderboard, Top10
display, ticker lookup, Top10 changes, or a KVN input read for Trade Plan
Preparation.

KVN is an imported snapshot. The plugin consumes upstream or user-provided KVN
outputs; it does not construct the quantitative model, choose vendors, backtest
factors, or turn the leaderboard into a buy list.

## Runtime Store

Default store:

```text
{runtime_dir}/momentum/kvn.sqlite
```

The runtime store keeps all imported symbols searchable while user-facing output
defaults to Top10.

## Snapshot CSV Contract

Required CSV fields:

```text
snapshot_date,rank_vs_sp500,ticker,kvn_score,kvn_p,is_sp500
```

Supported aliases include the screenshot-style headers:

- `Rank vs S&P500`
- `Ticker`
- `KVN 分数`
- `KVN P`
- `当前是否 S&P500`

Field meaning:

- `snapshot_date`: trading date for the imported KVN snapshot.
- `rank_vs_sp500`: S&P500-benchmarked rank shown as context, not the Top10
  definition.
- `ticker`: symbol, normalized to uppercase.
- `kvn_score`: primary sort field; higher ranks first.
- `kvn_p`: percentile of the current KVN score versus the ticker's recent KVN
  score history, usually 60 trading days when supplied by the upstream model.
- `is_sp500`: whether the ticker is currently in the S&P500 universe.

Top10 means the first 10 rows after sorting by `kvn_score` descending. It does
not mean `rank_vs_sp500 <= 10`.

## Script

Use the bundled script:

```bash
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py import /path/to/kvn.csv --db ~/Documents/dailytrades-runtime/momentum/kvn.sqlite --source user
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py show --date 2026-06-24 --top 10
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py query SOXX --date 2026-06-24
python3 plugins/trading-research-system/scripts/kvn_leaderboard.py changes --date 2026-06-24
```

Commands:

- `import`: write one snapshot into SQLite, replacing prior rows for the same
  date.
- `show`: display Top10 by default with `Rank vs S&P500`, `Ticker`, `KVN 分数`,
  `KVN P`, `当前是否 S&P500`, `连续入选Top10天数`, `近20日入选Top10次数`, and
  `上次入选Top10时间`.
- `query`: look up any imported ticker, including non-Top10 names.
- `changes`: compare current Top10 with the previous imported snapshot.

## Output Rules

- State that the leaderboard is research priority only, not a buy list.
- Preserve Top10 entry memory fields for triage.
- Do not infer a trade setup from KVN alone.
- Feed KVN names into Trade Plan Preparation only after macro/financial
  conditions, industry strength, company thesis, price structure, and portfolio risk
  are checked.
- If the KVN store is missing or stale, run `runtime_health.py` and ask whether
  to import a snapshot or continue without KVN.
