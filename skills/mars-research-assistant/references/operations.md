# Operations

Use `scripts/runtime_health.py --format json` before runtime-dependent work.
Report only the state that changes the next action. Preserve the returned
runtime and source statuses without translating them.

The private runtime may hold the active market plan, trading profile, dated
updates, daily containers, macro panel, portfolio snapshot, and research state.
Ask before creating or modifying it. Use bundled preparation scripts instead of
hand-writing structured runtime files.

A missing saved macro panel is a runtime-history condition, not a current
public-data condition. For a requested Macro Board, acquire and validate the
complete direct-public field set first. Deliver the Board transiently when the
preflight passes, or the one Data Acquisition Blocker when it fails. Ask for a
private-runtime write only after a valid Board exists and only when the user
wants that snapshot saved or replaced.

Broker access is read-only and source-specific. Reconcile before combining
accounts. If coverage is incomplete, keep portfolio conclusions conditional.

For a new session, provide useful reduced-scope public research first, then ask
for the smallest authorization or setup detail that unlocks personalization.

## Default Weekly Cadence

Use the weekday as a default research priority, not as a gate. The user's
current request always overrides this cadence.

- Monday: establish the market framework and this week's watchlist.
- Tuesday through Friday: update new market information, trading ideas, and
  existing plans.
- Saturday: review the market and completed trades, then prepare next week's
  watchlist.

Do not invent a fixed package for unlisted days. Keep the output proportional
to the decision and the information that changed.

## Supported Helpers

Use these narrow helpers instead of reconstructing runtime behavior in prose:

- health and explicit initialization: `scripts/runtime_health.py`,
  `scripts/bootstrap_runtime.py`, `scripts/prepare_daily_runtime.py`, and
  `scripts/init_daily.py`;
- setup and review preparation: `scripts/prepare_setup_rows.py`,
  `scripts/intraday_scan.py`, `scripts/append_review.py`, and
  `scripts/write_trade_review_context.py`;
- read-only summaries: `scripts/trade_stats.py` and
  `scripts/watchlist_score.py`;
- sanitized Alpha notification output: `scripts/alpha_notification_adapter.py`.

These commands do not authorize broker writes. Runtime mutation still requires
the user's explicit approval for the requested local files.
