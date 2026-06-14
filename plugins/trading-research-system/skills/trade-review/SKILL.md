---
name: trade-review
description: Run interactive trade review for actual trades, including post-order entry capture and post-exit outcome review. Use when the user wants to review a trade, fill the trading journal, use broker execution facts such as IBKR or Longbridge, record why they entered, capture signal bar and confidence, or complete exit review, R-multiple, mistake tags, and lessons.
---

# Trade Review

Use this skill to turn actual trades into structured `trades.csv` records and readable `reviews.md` notes.

## Workflow

1. Read `../trading-research/references/interactive-trade-review.md`.
2. Read `../trading-research/references/trade-journal.md`.
3. Read `../trading-research/references/broker-data-contract.md` when broker facts are involved.
4. If the trade came from a setup or plan, compare against `market-plan.md`, `trade-plans.csv`, or `intraday-watchlist.csv`.
5. If broker trade/order facts are available, use them only for objective fields:
   - symbol;
   - side;
   - quantity;
   - fill price;
   - fees;
   - time;
   - realized/unrealized PnL.
6. Ask one question at a time.
7. Determine the stage:
   - `post_order`: newly entered, open, or partially filled.
   - `post_exit`: closed, expired, stopped, scratched, or invalidated.
8. Do not write records until key fields are resolved and the user confirms.

## Post-Order Focus

Capture entry context while memory is fresh:

- linked plan;
- market background;
- setup type;
- signal bar;
- auxiliary evidence;
- confidence;
- entry price, stop, target, size, and planned R;
- whether this was plan-compliant.

## Post-Exit Focus

Complete the trade:

- exit reason;
- realized PnL and R;
- plan versus actual;
- execution quality;
- mistake tag;
- lesson;
- next rule.

## Output

Produce:

1. a `trades.csv` row draft or update;
2. a `reviews.md` section draft;
3. missing fields;
4. suggested `outcome`, `mistake_tag`, and confidence calibration.

Use Chinese and keep the interaction strict enough for later statistics.
