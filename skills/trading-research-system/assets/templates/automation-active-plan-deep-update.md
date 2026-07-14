# Active Market Plan Deep Update Automation Prompt

Purpose: produce a weekend or major-reset Active Market Plan update for the
fixed Trading Research Daily Ops chat. This is decision support only.

## Runtime

- Runtime root: `{runtime_dir}`.
- Run runtime health before reading private runtime files.
- Read `market-plan.md`, `trading-profile.md`, prior update notes, current
  setup pool, and saved review/report artifacts when available.
- If runtime state is missing or stale, report the gap and ask whether to
  initialize, import, or continue without it.

## Workflow

1. Review prior trade/review context when available.
2. Refresh current market tape, macro/rates, financial conditions,
   policy/news, upcoming events, and earnings that can affect current plans.
3. Read imported KVN snapshots through the KVN leaderboard path when available;
   do not rebuild or relabel public market data as KVN.
4. Convert macro/financial/policy/industry/company reads into Trade Plan
   Preparation and the Cross-Section Candidate Pool.
   Keep the exact `Trade Plan Preparation` section in the draft output.
5. Update setup-level opportunities only after higher-timeframe environment,
   price structure, trigger zone, invalidation, and risk context are clear.
6. Draft proposed `market-plan.md` changes and an append-only update note.
7. Ask before writing runtime files.

## Output

Use concise Chinese Markdown with:

- `结论`
- `本次变化`
- `交易计划准备`
- `Setup Pool 变化`
- `持仓/风险影响`
- `拟写入 market-plan.md`
- `拟追加 update note`
- `需要用户确认`

## Safety

- Do not place, modify, cancel, close, or approve orders.
- Do not silently overwrite `market-plan.md`.
- Do not invent broker facts, KVN rows, or unavailable report content.
- Keep private runtime content out of public repo files.
