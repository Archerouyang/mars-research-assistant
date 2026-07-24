# Safety And Sources

Use sources by purpose:

- `S0`: official releases, filings, policy, company IR, product terms;
- `S1`: authorized market, macro, calendar, and read-only broker data;
- `S2`: reputable media leads that need primary confirmation for material facts;
- `S3`: research, consensus, user thesis, and interpretation.

Use current primary sources when facts may have changed. A connector working for
one purpose does not make it authoritative for another. Preserve source status
exactly: `partial_data` and `upstream_error` are not `unauthorized`; empty
positions without reconciliation are not proof of an empty account.

No broker write action is supported. Do not expose account identifiers, raw
broker responses, credentials, or private runtime paths in public output.
