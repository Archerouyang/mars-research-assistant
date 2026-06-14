---
name: daily-market-tracking
description: Parse the current market against the active weekly trading plan and update which ideas are active, approaching, invalidated, or need more evidence. Use for daily market read, premarket prep, intraday plan updates, current tape analysis, and dynamic opportunity tracking within the user's weekly plan or watchlist.
---

# Daily Market Tracking

Use this skill to connect the active weekly plan to today's market. The goal is to keep planned ideas current and surface plan-scoped opportunities without drifting into random market scanning.

## Workflow

1. Load the active weekly plan or ask for it if it is unavailable.
2. Read relevant shared references:
   - Macro/rates context: `../trading-research/references/macro-policy-filter.md`.
   - Price action/timeframes: `../trading-research/references/price-action-timing.md`.
   - Intraday statuses: `../trading-research/references/intraday-setup-scan.md`.
   - Portfolio risk: `../trading-research/references/portfolio-risk.md`.
   - Trade journal schema: `../trading-research/references/trade-journal.md`.
3. Use current data for market state, rates/yields, news, prices, and chart context.
4. For each active idea, classify it as:
   - `waiting`
   - `approaching`
   - `triggered`
   - `invalidated`
   - `needs_review`
5. If a new opportunity appears, tie it back to an existing weekly theme/watchlist item or create a new draft plan before treating it as actionable.
6. Prefer `../../assets/templates/daily-market-tracking.md` for notes.

## Output

Use Chinese Markdown with:

- `当前盘面`
- `每周计划对照`
- `接近触发`
- `已失效`
- `需要复核`
- `新证据`
- `下一步看盘顺序`

Keep the note operational: what changed, what matters today, and what the user should inspect first.
