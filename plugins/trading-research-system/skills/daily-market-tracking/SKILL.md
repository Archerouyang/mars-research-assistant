---
name: daily-market-tracking
description: Quick-update the Active Market Plan during weekday premarket or intraday sessions with market tape, macro/rates, policy, news, event, momentum, setup status, and level changes. Use for daily market read, premarket prep, intraday plan updates, point/level updates, current tape analysis, and dynamic tracking of planned setup opportunities.
---

# Daily Market Tracking

Use this skill for `quick_update` or light `trigger_update` work against the same Active Market Plan. The goal is to answer what changed, which setup statuses or levels changed, and what the user should inspect next.

This is an AI-native workflow. Read current tape, macro/rates, policy/news, event calendar, momentum, and existing setup files, then return only what changed, which setup statuses moved, and what the user should inspect next.

## Workflow

1. Load the active `market-plan.md`, or ask for the current plan state if it is unavailable.
2. Read relevant shared references:
   - Active plan model: `../trading-research/references/active-market-plan.md`.
   - Runtime health: `../trading-research/references/runtime-health.md`.
   - Trading profile strategy rules, pools, timeframes, and instrument preferences: `../trading-research/references/trading-profile.md`.
   - Macro/rates context: `../trading-research/references/macro-policy-filter.md`.
   - KVN imported snapshots: `../trading-research/references/momentum-leaderboard.md`.
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
   - KVN Momentum Leaderboard changes from imported snapshots only;
   - prices, key levels, and chart context.
   Use `../../scripts/kvn_leaderboard.py` only when runtime health shows the
   KVN store is available. If the KVN store is missing or stale, report that KVN
   is unavailable and ask whether to import a snapshot or continue without KVN.
   KVN output is ticker-only. Preserve the imported script order and do not
   re-rank, re-score, or reorder KVN rows. Do not rebuild KVN from public market
   data inside daily tracking. Do not label public market data as KVN; public
   market data can support tape, sector breadth, and relative-strength notes
   only. Any sector/theme rotation belongs in market breadth, not in the KVN
   table. Daily tracking must not re-rank, re-score, or reorder KVN rows.
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

## Runtime Guidance Contract

Always translate the runtime state into user-facing Chinese before giving
market commentary. Internal slug values may appear only in parentheses after
the Chinese label, for example `盘前快速更新 (premarket_quick_update)`, `待复核
(needs_review)`, or `修复观察 (repair-watch)`. Do not make the internal slug
the primary status text.

Include `运行状态` and `可执行下一步` whenever runtime health is incomplete,
broker access is missing, the KVN store is missing/stale, or the request cannot
enter formal intraday scanning.

Use these user-facing status labels:

- `盘前快速更新`: useful quick market read, but not a formal scan.
- `正式盘中扫描`: prepared setup scan using today's plan/watchlist files.
- `待复核`: setup or data state needs user/agent review before a trigger call.
- `修复观察`: rebound or repair tape that is not yet full risk-on confirmation.

When degraded, choose 2-4 concrete `可执行下一步` actions from this set and
adapt them to the exact missing files:

- `初始化今日运行包`: create today's daily runtime directory and base files.
- `生成盘中观察清单`: build `intraday-watchlist.csv` from Active Plan setups.
- `导入 KVN snapshot`: import a user/upstream KVN snapshot before KVN output.
- `跳过 KVN`: continue without KVN and do not label public data as KVN.
- `继续盘前快速更新`: stay in quick-update mode until the next macro/event check.

Every live quote, macro indicator, broker snapshot, and official data point
must carry a `数据时间戳`, preferably `as of <timestamp/source date>`. If the
timestamp is unavailable, say `as of 未确认` instead of implying freshness.

## Output

Use Chinese Markdown with:

- `运行状态`
- `结论`
- `重要变化`
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
- `可执行下一步`

Keep the note operational: what changed, what matters today, and what the user should inspect first. Avoid long intraday commentary; collapse repeated headlines and price noise into changed variables, setup transitions, and explicit invalidations.
