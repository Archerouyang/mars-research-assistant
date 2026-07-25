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

For a new unscoped Daily Ops session, do not start with a prose public-market
summary. Run the phase gate below: its capability-only source check comes first,
then the Macro Board or Data Acquisition Blocker is the first decision-bearing
artifact. Only after that Board ask whether the user wants portfolio
personalization.

## Unscoped Daily Ops Baseline

Use this sequence only for an unscoped `开始今天的交易研究` / `continue Daily
Ops` request. A named instrument, report, or Price Action request takes its
focused route instead.

1. Execute the side-effect-free phase gate before each transition:

   ```bash
   python3 scripts/daily_ops_routing.py \
     --intent unscoped_daily_start \
     --capability-state <pending|checked> \
     --macro-state <pending|delivered|blocked> \
     --portfolio-review <undecided|requested|declined> \
     --broker-authorized <true|false> \
     --portfolio-state <not_read|ready|option_overlay_partial|core_gap>
   ```

   Its `required_actions` are mandatory. Never emit an action listed in
   `forbidden_actions`.
2. At `capability_state=pending`, run `broker_capability.py` for both supported
   connections. It is capability-only: it checks Longbridge with `check --format
   json` and recognizes only host-visible IBKR task tools. It must not read an
   account, portfolio, balance, quote, order, or credential, and it must not
   alter the installed default broker. Installation setup provides permission
   for this check; a missing setup is a capability gap, not an account read.
3. At `capability_state=checked` and `macro_state=pending`, run the complete
   direct-public Macro preflight.
   On success, pass its exact canonical snapshot to a `ResearchResult`
   (`result_kind=macro`, `visual.adapter=macro`) and execute
   `scripts/research_result.py`; deliver exactly that generated
   `standalone_board/research-brief.html`. On failure, deliver one `Data
   Acquisition Blocker`. Do not replace either with prose, `visualize`,
   hand-authored HTML, or another Board renderer.
4. At `macro_state=delivered` with `portfolio_review=undecided`, ask whether
   the user wants the installed default broker's holdings included in the
   Portfolio Risk Panel. Do not read them automatically. If declined, ask which
   research mode the user wants next; do not begin company research, Price
   Action, or trade guidance.
5. Only at `portfolio_review=requested`, ask for account read-only authorization
   when it is missing, then read the installed default broker's permitted
   holdings and capital context. Classify the result:
   `ready` yields a `ResearchResult` with `result_kind=portfolio` and
   `visual.adapter=portfolio`, carrying the validated canonical Portfolio
   snapshot (or a legacy normalized panel); `option_overlay_partial` uses the
   same canonical Portfolio Risk renderer while marking unavailable option
   delta/notional/stress fields; `core_gap` yields a concrete data gap only.
6. After the Portfolio result/gap, or after the user declines portfolio review,
   ask whether they want individual research, Price Action, or trade guidance.
   The question itself must not emit a panel. Individual research requires a
   user-named ticker; Price Action and trade guidance both require
   `ticker + trade_horizon + instrument`.

An option overlay is not a core portfolio gap merely because its multiplier,
Greeks, delta, or underlying notional are missing. With valid broker position
identity, direction, market value, currency, timestamp, and cash/NAV context,
keep it visible as an unmodeled `option_overlay_partial` and exclude it from
delta and stress arithmetic. Do not silently zero the field, imply a hedge, or
read/request a second broker. A user explanation of the overlay's purpose is
classification evidence, not a request to analyse its underlying ticker.

The required Board or Blocker is the first decision-bearing artifact in its
phase. Do not precede it with a runtime table, a prose macro report, broker
health output, or a suggested ticker. Source coverage and gaps appear in the
Board/Blocker and concise copy after it.

The accepted renderer chain is fixed: `macro_preflight.py` snapshot ->
`ResearchResult(result_kind=macro, visual.adapter=macro)` ->
`macro_board_visual.py`, and a validated Portfolio snapshot ->
`ResearchResult(result_kind=portfolio, visual.adapter=portfolio)` ->
`portfolio_board_visual.py`. Both are written by `research_result.py` as one
offline `standalone_board` packet. The Portfolio input bridge changes fields,
not the frozen view structure. Do not substitute `visualize`, custom HTML, or a
separate CSS system.

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
