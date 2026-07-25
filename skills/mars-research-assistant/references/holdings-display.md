# Holdings Display

Use this reference only after the user explicitly asks to read holdings for the
current request. A previous IBKR connection or Macro data read does not
constitute holdings consent.

1. Read only IBKR through its read-only host adapter.
2. Normalize only the approved factual fields with
   `scripts/ibkr_holdings_adapter.py`, without exposing account identifiers or
   raw provider payloads.
3. Render with `scripts/holdings_display.py` and show only: broker, symbol,
   quantity, latest price, market value, cost, unrealized P&L, cash, currency,
   and retrieval time.
4. Render an absent factual field as `不可用`. Do not infer it from another field.
5. Do not calculate weights, concentration, leverage, delta, stress, scenario
   loss, risk scores, or portfolio recommendations. Do not start PA or a named
   instrument analysis unless the user asks for it.

The display is factual and IBKR-only. Never aggregate cash across currencies.
Account identifiers stay out of the rendered output. A legacy broker selection
file is unsupported and must not affect this path.
