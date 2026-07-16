# Synthetic, Sanitized Fixtures

All files under this directory are synthetic, sanitized test fixtures.

Ticker symbols are examples for contract tests, not a recommendation list, default watchlist, or user profile.

Fixtures must never be populated from private runtime, broker exports, credentials, or research history.

The `input/`, `expected/`, and `runtime/` trees exist only to exercise generic
plugin contracts. They are public test data and must not be replaced with a
user's watchlist, trading profile, Active Market Plan, setups, positions,
executions, reviews, account configuration, or connector authorization state.

| Fixture area | Public purpose |
| --- | --- |
| input | Synthetic inputs for deterministic contract tests. |
| expected | Sanitized expected outputs checked by local verification. |
| runtime | Runtime-shaped data invented solely for fixture-backed tests. |

The canonical Instrument Research corpus under `input/` contains deterministic
`complete`, `partial`, `stale`, and `source_error` snapshots. Each snapshot is
synthetic, privacy-safe, and exercises the same artifact-packet boundary. Flow
evidence is supporting-only in every state.
