# Trading Profile Fixture

synthetic fixture for testing only. It is not a personal account allocation.

## strategy posture

- Defensive: hold core ETF exposure and avoid new high-beta risk.
- Balanced: allow selective candidates after macro and price confirmation.
- High-beta momentum: allow KVN-driven research candidates after thesis,
  4H/1D/1W structure, and risk checks.

## instrument preference

- ETF core: QQQ, VOO, SOXX style exposure; low-turnover by default.
- momentum additions: stock_common first, then LEAP only after thesis and
  liquidity checks.
- 0DTE: QQQ/SPY only, with tight trigger discipline and no averaging down.
- LEAP: only for high-conviction large-cap or platform names after valuation and
  event checks.

## risk limits

- Do not add risk when technology beta and semiconductor exposure are both
  crowded.
- Use position daily report before adding correlated exposure.
- Any 0DTE setup needs execution_check_required and same-day invalidation.

## Avoid Rules

- Do not treat KVN Top10 as a buy list.
- Do not promote a symbol to setup without price structure.
- Do not use broker fixtures as live broker truth.
