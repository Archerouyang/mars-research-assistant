---
name: trade-review
description: Run interactive trade review for actual trades, including post-order entry capture and post-exit outcome review. Use when the user wants to review a trade, fill the trading journal, use broker execution facts such as IBKR or Longbridge, record why they entered, capture signal bar and confidence, or complete exit review, R-multiple, mistake tags, and lessons.
---

# Trade Review

Use this skill to capture two-stage trade review context from actual trades.
Objective execution/result facts come from read-only broker-live facts when
available. The default artifact is a structured review-context section in
`reviews.md`, not a durable local trade-record table.

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
8. Do not write local artifacts until key fields are resolved and the user confirms.
9. After confirmation, write the review context with `../../scripts/write_trade_review_context.py`:
   - pass `--stage post-order` or `--stage post-exit`;
   - pass a fields JSON file through `--fields-json` containing review-context fields;
   - pass `--review-file` for the user's preserved Markdown review text when available.
10. Compatibility path: if the user explicitly asks for a local trade-record snapshot, write it with `../../scripts/update_trade_record.py`:
   - pass `--stage post-order` or `--stage post-exit`;
   - pass a fields JSON file through `--fields-json` containing only valid `trades.csv` fields;
   - pass `--review-file` for the reviewed Markdown text when available;
   - use `--allow-unknown-execution-fields` only for legacy sheet imports that lack `quantity`, `fees`, or `risk_amount`; do not use it to skip fresh post-order questions.

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

1. a review-context draft;
2. a `reviews.md` section draft;
3. missing fields;
4. suggested `outcome`, `mistake_tag`, and confidence calibration;
5. after user confirmation, the exact `write_trade_review_context.py` command or a short note that it was written.
6. Compatibility path only when requested: the exact `update_trade_record.py` command for a local `trades.csv` snapshot.

Use Chinese and keep the interaction strict enough for later statistics.
