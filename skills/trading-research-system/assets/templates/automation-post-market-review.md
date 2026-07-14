# Post-Market Review Automation Prompt

Purpose: close the trading day by cleaning up setup statuses, identifying
needed trade reviews, and preparing the next update queue. This is decision
support only.

## Runtime

- Runtime root: `{runtime_dir}`.
- Run runtime health before reading private runtime files.
- Read `market-plan.md`, today's update note, `intraday-watchlist.csv`,
  `reviews.md`, and authorized read-only broker facts when the user opts in.

## Workflow

1. Summarize which setup statuses changed during the day.
2. Identify trades or fills that need post-order review context.
3. Identify closed, expired, scratched, or invalidated trades that need
   post-exit review.
4. Compare the day's action to the Active Market Plan and note unresolved
   broker/trade facts.
5. Draft the next update queue and ask before writing runtime files.

## Output

Use concise Chinese Markdown with:

- `结论`
- `Setup 收盘状态`
- `需要 post-order 复盘`
- `需要 post-exit 复盘`
- `明日队列`
- `拟追加 update note`
- `需要用户确认`

## Safety

- Do not mutate broker state.
- Do not infer missing fills or PnL without broker facts or user confirmation.
- Do not require Google Sheets or local trade-record tables.
