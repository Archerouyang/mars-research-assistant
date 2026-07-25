# Operations

Use `scripts/runtime_health.py --format json` only when runtime state changes
the next action. A missing saved Macro artifact is history state, not a reason
to skip acquisition of the current Macro Board.

## Unscoped Daily Ops

For an unscoped `开始今天的交易研究` request, execute the side-effect-free
router before each transition:

```bash
python3 scripts/daily_ops_routing.py \
  --intent unscoped_daily_start \
  --capability-state <pending|checked> \
  --macro-state <pending|delivered|blocked> \
  --holdings-review <undecided|requested|declined> \
  --holdings-state <not_read|displayed|unavailable>
```

1. `capability_state=pending`: run `broker_capability.py` for IBKR. It checks
   task-visible tool support only and must not read account, holdings, balance,
   quote, order, credentials, or market payloads.
2. `capability_state=checked`, `macro_state=pending`: acquire every required
   Macro field. Prefer an eligible broker market/macro record only when field
   identity, unit, native path, timestamp, and latest completed close/reference
   period are all present. Use the registered exact public primary source only
   for a field without an eligible broker record. Run Macro preflight and deliver
   exactly one canonical Macro standalone Board or one Data Acquisition Blocker.
   Do not substitute a prose summary, `visualize`, or hand-authored HTML.
3. `macro_state=delivered`: ask exactly: `是否读取并展示 IBKR 持仓，还是直接研究
   一个标的？` Do not automatically read holdings.
4. Only after a fresh explicit holdings confirmation: read IBKR, normalize the
   approved factual fields through `ibkr_holdings_adapter.py`, and render them
   through `holdings_display.py`. A failed read yields the concrete field gap
   and returns control to the user.
5. A named ticker at any point executes `run_named_instrument_research_bundle`.
   It does not require a holdings display and defaults to industry events,
   fundamentals, catalysts, valuation, counter-thesis, and a 4H PA Board.

The Macro Board or its blocker is the first decision-bearing artifact in an
unscoped start. Do not precede it with a runtime table, broker-health prose, or
a suggested ticker. The consented holdings display is factual only; it never
calculates portfolio risk, weights, leverage, stress, delta, or recommendations.

## Runtime Boundary

The private runtime may hold plans and dated research state. Ask before creating
or modifying it. Broker access remains read-only; account reads require fresh
user authorization, while market/macro retrieval does not authorize account
reads or runtime writes.

## Supported Helpers

- runtime health and initialization: `runtime_health.py`, `bootstrap_runtime.py`,
  `prepare_daily_runtime.py`, `init_daily.py`;
- guided routing and factual holdings: `daily_ops_routing.py`,
  `broker_capability.py`, `ibkr_holdings_adapter.py`,
  `holdings_display.py`;
- setup and review preparation: `prepare_setup_rows.py`, `intraday_scan.py`,
  `append_review.py`, `write_trade_review_context.py`;
- read-only summaries: `trade_stats.py`, `watchlist_score.py`, and
  `alpha_notification_adapter.py`.

These helpers never authorize broker writes. Runtime mutation still requires the
user's explicit approval for the requested local files.
