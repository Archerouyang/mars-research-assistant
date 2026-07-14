# Position Daily Report Automation Prompt

Purpose: produce a concise Chinese holdings and portfolio-risk note for the
fixed Trading Research Daily Ops chat. This is decision support only.

## Runtime

- Runtime root: `{runtime_dir}`.
- Read `market-plan.md` and `trading-profile.md` when available.
- Run runtime health before broker-dependent work.
- Use `{runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv` only after a
  broker read, adapter mapping, or user-approved snapshot provides it.

## Source Order

1. Longbridge skill/plugin when installed and authorized.
2. IBKR connector when installed and authorized.
3. Manual user export for a single run.
4. If no source is available, report the gap and do not invent holdings.

If multiple broker sources are enabled, use the user's private source
preference. If no preference exists, ask one short question before reading.

## Workflow

1. Check runtime health and broker-source availability.
2. Read current broker positions and account-risk fields only through authorized
   read-only sources.
3. Map broker facts into the standard `portfolio_snapshot.csv` view or use a
   user-approved existing snapshot. If the available source is a local
   read-only broker export, normalize it first with `broker_snapshot_ingest.py`.
4. Render the report with:

```bash
python3 scripts/position_daily_report.py \
  {runtime_dir}/daily/YYYY-MM-DD/portfolio_snapshot.csv \
  --date YYYY-MM-DD \
  --source "Longbridge / IBKR / manual"
```

5. Return only the concise report plus missing data and user decisions.

## Output

Use Chinese Markdown with:

- `结论`
- `需要用户决策`
- `风险变化`
- `持仓影响`
- `可视化`
- `数据缺口`

## Safety

- Do not place, modify, cancel, close, or approve orders.
- Do not save full raw broker exports by default.
- Do not publish account identifiers, credentials, or raw broker exports to the
  public plugin repo.
- Ask before writing runtime files unless the user has already confirmed the
  exact source, date, and destination.
