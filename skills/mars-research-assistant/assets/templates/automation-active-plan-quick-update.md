# Active Market Plan Quick Update Automation Prompt

Purpose: produce a weekday premarket or intraday delta note against the current
Active Market Plan. This is decision support only.

## Runtime

- Runtime root: `{runtime_dir}`.
- Run runtime health before reading private runtime files.
- Read `market-plan.md`, today's update note, `trading-profile.md` when
  available, `trade-plans.csv`, and `intraday-watchlist.csv`.

## Workflow

1. Identify only what changed since the current Active Market Plan.
2. Check current macro/rates, policy/news, events, earnings, market tape, and
   imported KVN snapshot freshness when relevant.
3. Update setup statuses and levels as draft changes:
   `active`, `approaching`, `triggered`, `invalidated`, `needs_review`, or
   `completed`.
4. Separate new evidence from noise.
5. Draft an append-only update note and ask before writing runtime files.

## Output

Use concise Chinese Markdown with:

- `结论`
- `变化`
- `Setup 状态`
- `关键价位/失效`
- `风险/数据缺口`
- `拟追加 update note`
- `需要用户确认`

## Safety

- No buy/sell instruction.
- `triggered` only means human execution check is required.
- Do not silently change the Active Market Plan.
- Do not invent missing KVN, broker, or market data.
