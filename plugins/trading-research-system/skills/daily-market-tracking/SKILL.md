---
name: daily-market-tracking
description: Quick-update the Active Market Plan during weekday premarket or intraday sessions with market tape, macro/rates, policy, news, event, momentum, setup status, and level changes. Use for daily market read, premarket prep, intraday plan updates, point/level updates, current tape analysis, and dynamic tracking of planned setup opportunities.
---

# Daily Market Tracking

Use this skill for `quick_update` or light `trigger_update` work against the same Active Market Plan. The goal is to answer what changed, which setup statuses or levels changed, and what the user should inspect next.

## Workflow

1. Load the active `market-plan.md`, or ask for the current plan state if it is unavailable.
2. Read relevant shared references:
   - Active plan model: `../trading-research/references/active-market-plan.md`.
   - Trading profile and instrument preferences: `../trading-research/references/trading-profile.md`.
   - Macro/rates context: `../trading-research/references/macro-policy-filter.md`.
   - Price action/timeframes: `../trading-research/references/price-action-timing.md`.
   - Intraday statuses: `../trading-research/references/intraday-setup-scan.md`.
   - Portfolio risk: `../trading-research/references/portfolio-risk.md`.
   - Trade journal schema: `../trading-research/references/trade-journal.md`.
3. Use current data for:
   - index and sector tape;
   - rates/yields and macro variables;
   - fiscal/Treasury/Fed/policy headlines;
   - high-impact news and earnings;
   - major events in the current week and next-week preview window;
   - momentum leaderboard changes;
   - prices, key levels, and chart context.
4. Update setup-level fields:
   - trigger zone;
   - invalidation;
   - stop concept;
   - target zones;
   - execution timeframe;
   - instrument fit against trading profile;
   - risk/reward after the update.
5. For each relevant setup, classify it as:
   - `candidate`
   - `active`
   - `approaching`
   - `triggered`
   - `invalidated`
   - `needs_review`
   - `completed`
6. If a new opportunity appears, tie it back to an existing theme/context or create a new `candidate` setup before treating it as actively tracked.
7. Prefer `../../assets/templates/daily-market-tracking.md` for notes.

## Output

Use Chinese Markdown with:

- `当前盘面`
- `快速宏观/利率`
- `政策/新闻`
- `事件预览`
- `动量榜单更新`
- `Active Plan 对照`
- `点位更新`
- `交易风格匹配`
- `接近触发`
- `已失效`
- `需要复核`
- `新证据`
- `下一步看盘顺序`

Keep the note operational: what changed, what matters today, and what the user should inspect first.
