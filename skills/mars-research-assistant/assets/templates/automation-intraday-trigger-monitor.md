# Intraday Trigger Monitor Automation Prompt

Purpose: inspect prepared Active Market Plan setups during market hours and
surface attention priorities. This is decision support only.

## Runtime

- Runtime root: `{runtime_dir}`.
- Run runtime health before reading private runtime files.
- Read `market-plan.md`, `trading-profile.md`, `trade-plans.csv`, and
  `intraday-watchlist.csv`.

## Workflow

1. Limit scope to prepared setups in the Active Market Plan, setup pool,
   trade plans, or intraday watchlist.
2. Check whether each setup is `active`, `approaching`, `triggered`,
   `invalidated`, `needs_review`, or `completed`.
3. Require execution-timeframe confirmation for `triggered`; price contact alone
   is only `approaching`.
4. Include factual broker holdings only when the user has authorized the
   read-only account read for that request; do not derive portfolio risk.
   available or a current position daily report exists.
5. Ask before writing any update note or status change.

## Output

Use concise Chinese Markdown with:

- `结论`
- `优先级`
- `Setup 状态`
- `execution_check_required`
- `失效/风险`
- `需要用户确认`

## Safety

- Do not scan the entire market for unplanned trades.
- Do not place, modify, cancel, close, or approve orders.
- Do not describe `triggered` as permission to trade.
