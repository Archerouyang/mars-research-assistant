---
name: trading-stats
description: Analyze closed trade records and review notes for win rate, R-multiple, expectancy, drawdown, setup performance, instrument performance, timeframe performance, mistake tags, and confidence calibration. Use when the user asks for trading statistics, system review, performance by setup, review optimization, or whether the trading system is improving.
---

# Trading Stats

Use this skill to measure whether the user's trading process is improving.

## Workflow

1. Read `./trade-journal.md`.
2. Use `scripts/trade_stats.py` when `trades.csv` is available.
3. Separate outcome quality from execution quality:
   - a good trade can lose;
   - a bad trade can win;
   - statistics should identify repeatable edge and repeatable mistakes.
4. Group by useful dimensions:
   - setup;
   - instrument type;
   - direction;
   - timeframe;
   - confidence;
   - mistake tag;
   - planned versus unplanned.
5. Avoid overfitting small samples. Label weak evidence clearly.

## Output

Use Chinese Markdown with:

- `样本范围`
- `核心统计`
- `Setup 表现`
- `工具类型表现`
- `时间框架表现`
- `错误标签`
- `信心校准`
- `系统优化`
- `下一批要验证的规则`

When data is incomplete, state which fields must be repaired before trusting the statistics.
