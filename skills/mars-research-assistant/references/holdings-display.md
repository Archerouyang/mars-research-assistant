# Holdings Display

Use this reference only after the user explicitly asks to read holdings for the
current request. A previous broker connection, Macro data read, or stored
default broker does not constitute holdings consent.

1. Read only the configured default broker through its read-only host adapter.
2. Normalize the response to the existing portfolio snapshot row schema without
   exposing account identifiers or raw provider payloads.
3. Render with `scripts/holdings_display.py` and show only: broker, symbol,
   quantity, latest price, market value, cost, unrealized P&L, cash, currency,
   and retrieval time.
4. Render an absent factual field as `不可用`. Do not infer it from another field.
5. Do not calculate weights, concentration, leverage, delta, stress, scenario
   loss, risk scores, or portfolio recommendations. Do not start PA or a named
   instrument analysis unless the user asks for it.

The display is factual and single-broker. Never aggregate cash across currencies
or silently combine brokers. Account identifiers stay out of the rendered output.
