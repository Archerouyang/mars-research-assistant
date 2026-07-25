# 火星投研助手 1.0 规格

Status: accepted
Accepted: 2026-07-23

## Objective

Release the existing trading-research product as the Skill-only `火星投研助手`
and make Macro Board data acquisition deterministic, field-first, and
fail-closed for its retained core fields. Version `1.0.0` is a deliberate hard cut: it does not preserve the
DailyTrades, Trading Research System, or native Plugin identities.

Macro Board answers one question:

> 当前金融条件是否支持增加高 Beta 风险，以及未来一周哪些事件可能改变这个判断？

Its allowed postures are:

- `risk_expansion_allowed`
- `hold_current_risk`
- `risk_reduction_required`

## Product Boundary

- User-facing name: `火星投研助手`
- Skill and repository id: `mars-research-assistant`
- Canonical Skill: `skills/mars-research-assistant/`
- Private runtime: `~/Documents/mars-research-runtime`
- Private config: `~/Documents/mars-research-runtime/config.json`
- Release: `1.0.0`
- Distribution: portable Agent Skill only
- Removed boundary: native Plugin wrappers, marketplace manifests, and generated
  Plugin projections

The repository, local checkout, installed Skill, and private runtime are renamed
without compatibility aliases. Runtime migration must preserve and verify user
data before the old directory is retired.

## 1.0 Scope

This release includes:

- the complete product and path rename;
- first-run configuration for one default read-only broker;
- a shared canonical field-status shape that later Boards can adopt;
- the complete field acquisition contract for Macro Board;
- existing standalone Board rendering after a successful Preflight.

Portfolio, Price Action, Instrument Research, Earnings, and News/Event Boards
receive the new product identity but retain their existing data behavior in this
release. Their field-contract migrations are later vertical slices.

## Minimal Runtime Shape

火星投研助手 remains a Skill, not a data platform:

- Skill instructions own workflow, field requirements, source routing, and user
  interaction;
- small deterministic Python helpers own capability probing, normalization, and
  validation;
- one private JSON file owns setup state;
- no database, daemon, task queue, or default raw-response archive is added;
- `--capture-raw` may be used explicitly for private debugging only.

The private configuration stores only:

- `default_broker`
- `broker_read_only_enabled`
- `setup_completed_at`
- `skill_version`
- `field_contract_version`
- `last_capability_probe_at`
- field coverage status

It must not store credentials, tokens, account identifiers, or market payloads.

## First-Run Setup

The first Skill invocation checks for `config.json`. If it is absent, the Skill:

1. detects available read-only Longbridge and IBKR capabilities without reading
   account positions;
2. asks the user to select one `default_broker`;
3. records read-only consent;
4. runs a field-level capability probe for Macro Board;
5. records command, parameters, response field path, type, and coverage for each
   required field;
6. reports `configured` or `configured_partial`.

The Skill never switches to another broker automatically. A different broker is
used only after the user changes `default_broker`.

The capability probe reruns when:

- the field-contract version changes;
- the default broker or its connector/CLI version changes;
- a Provider schema fingerprint changes;
- a field becomes `unsupported`;
- a source returns two consecutive `source_error` results;
- the user asks to recheck setup.

Daily research performs only a lightweight health and freshness check.

## Acquisition Pipeline

```text
load config
-> resolve Macro required fields
-> apply field-specific source routing
-> acquire and normalize exact fields
-> validate semantics, common close date, and freshness
-> reject with Data Acquisition Blocker on any unresolved retained core field
-> otherwise render the standalone Macro Board
```

The contract is field-first. A successful command, token check, HTTP response,
or top-level Provider status does not prove field coverage.

Search is a source-discovery mechanism. A search-result snippet cannot satisfy a
field; the workflow must open a qualified source and extract the exact value,
definition, period, and timestamp.

### Field Admission Rule

Version 1.0 keeps only fields whose exact meaning, completed-session timing, and
stable direct public retrieval can be proven before implementation. A desired
signal without such a route is **not** represented as `missing`, a proxy, a
user waiver, or a partial Board section: it is outside the 1.0 field contract.
Adding it later requires a new field map, a qualified source opened through
search or an approved direct endpoint, and a synthetic golden case.

The following desired signals are therefore deferred from 1.0: DXY, ICE Brent
front-month settlement/contract/roll state, XAU/USD daily close, and S&P 500
Forward 12M P/E plus its ten-year comparison. The Board must not substitute
UUP, oil ETFs, GLD, generic P/E, or any other approximate series for them.

## Source Routing

| Field family | Preferred route | Fallback |
| --- | --- | --- |
| Broker positions and account facts | configured default broker | none |
| Market close and OHLCV | configured default broker | only a field-specific direct public source map |
| Economic actuals | Longbridge macrodata when the default broker is Longbridge | official statistical agency |
| Treasury yields and liquidity | official U.S. source | qualified exact-data source |
| Policy, release timing, and regulation | official source | search discovery to the primary source |
| News | discovery source | original announcement or primary evidence |

The default broker is never switched automatically. A broker-dependent market
field blocks when that broker cannot supply it; an official fallback is allowed
only where the field contract names a direct source map. Generic
`qualified_*` source identifiers are prohibited.

## Field Map Requirement

Each Provider map must define:

- canonical field id;
- command or retrieval method;
- non-sensitive parameters;
- raw response field path;
- normalization rule;
- unit;
- freshness rule;
- allowed fallback;
- semantic evidence or golden case.

Longbridge command candidates include `quote`, `kline`, `macrodata`, and
`finance-calendar macrodata` with JSON output. A command is not accepted into
the map until a golden case verifies the nested response field and meaning.
Broad `additionalProperties` schemas are insufficient evidence.

## Normalized Field Shape

Every acquired raw field is stored as one normalized record. At minimum, the
record contains:

- `field_id`;
- `value`;
- `unit`;
- `status`;
- `data_as_of`;
- `market_reference_date` or `reference_period`, as applicable;
- `source_id`;
- `retrieval_method`;
- `raw_field_path`;
- `source_url` and `source_columns` when a direct public map requires them;
- aligned normalized `history` when a downstream deterministic calculation
  requires it;
- `diagnostic_ref` when acquisition did not finish as `available`.

Derived fields are never accepted as caller-provided records. Preflight derives
ratios, completed-session changes, and NDX/RUT normalization from validated raw
records and aligned histories, then retains the formula and input lineage in
its resolved output.

The Board payload carries a `preflight` binding with the field-contract version,
the common market-reference date, the exact validated field-id set, and explicit
chart/trend label-to-field mappings. Preflight compares every bound displayed
numeric value with its resolved value before a standalone Board can render. A
payload that is unbound, mismatched, or contains a deferred signal is rejected.

`raw_field_path` identifies the exact value inside the Provider response; it is
not a copy of the raw payload. Provider-specific names never become Board
fields directly. Normalization must preserve enough provenance to reproduce the
value without storing credentials, account identifiers, or an unrestricted raw
response.

For completed-session market fields, `data_as_of` records the source timestamp
and `market_reference_date` records the common completed close or settlement
date used by the Board. For economic releases, `reference_period` and
`data_as_of` are both required so release time is not confused with the period
being measured.

## Required Macro Fields

### Rates

- `rates.us_2y_yield`
- `rates.us_10y_yield`
- `rates.us_30y_yield`

### Volatility

- `volatility.vix_close`
- `volatility.vix3m_close`
- derived `volatility.vix_vix3m_ratio`

Only the ratio is presented as the term-structure signal; the two source values
remain in the normalized snapshot for audit.

### Equity Risk and Relative Strength

- `equity.ndx_close`
- `equity.rut_close`
- derived `equity.ndx_rut_ratio`
- derived `equity.ndx_rut_normalized_20d`
- ratio changes over 1, 5, and 20 trading days

The raw NDX/RUT level has no fixed economic threshold. The Board interprets its
direction and normalized trend.

### Liquidity

- `liquidity.reserve_balances`
- `liquidity.tga_balance`
- `liquidity.on_rrp_usage`

The three series remain separate. Version 1.0 does not invent a composite net
liquidity formula.

### Event and Policy Risk

The seven-day event allowlist includes:

- FOMC decisions, minutes, and Chair press conferences;
- CPI, PCE, PPI;
- payrolls, unemployment, and ECI;
- GDP;
- ISM or Flash PMI;
- long-duration U.S. Treasury auctions;
- major central-bank decisions that materially affect dollar financial
  conditions.

Event fields include name, release time, timezone, reference period, actual,
consensus, previous, revised previous, official source, and field status.
Before release, `actual` may be empty; time, period, and consensus must be
present.

The Trump / U.S. executive-policy module includes only actions or directly
attributable statements from President Trump or his administration that can
materially affect tariffs and trade, Federal Reserve governance, fiscal or tax
policy, sanctions and export controls, energy, oil, shipping, or supply chains.
Its evidence states are:

- `confirmed`
- `stated_not_enacted`
- `unverified_lead`

Only confirmed actions and directly attributable statements can affect the
posture. Anonymous media leads remain visible context only.

## Conditional Fields

Detailed CPI, PCE, PPI, labor, GDP, or PMI fields become required when the
release is recent, is on the seven-day event list, or is used in a conclusion.
Additional volatility series, gold-hedge interpretation, company earnings, and
portfolio holdings may not be introduced into a conclusion without activating
and satisfying their corresponding field requirements.

## Snapshot and Freshness

Macro Board does not support intraday market data.

- All market fields use the most recent common date on which every required
  field has a completed close or settlement.
- NDX, RUT, VIX, and VIX3M use that completed session.
- Market changes are computed from completed daily observations only.
- The decision cutoff is timezone-aware; a same-date market row is not accepted
  as a completed close in 1.0, and a completed-market row older than seven
  calendar days is stale.
- Liquidity fields use the latest official releases and retain their distinct
  reporting periods.
- Future event times are rechecked on every run.
- U.S. executive-policy state is rechecked within 24 hours.

The Board header always displays:

- `market_reference_date`;
- a statement that premarket, postmarket, and current-session moves are not
  included;
- a separate news and policy cutoff;
- the number of days of lag and reason when the common market date is older than
  the latest completed session.

## Field Status

Allowed statuses:

- `available`
- `stale`
- `missing`
- `unsupported`
- `source_error`
- `conflicted`

`derived` is lineage, not a status. Preflight calculates every derived value
from `available` raw inputs; `fallback` is a retrieval path, not a status.

Required fields do not accept proxies. IWM cannot satisfy RUT and a volatility
ETF cannot satisfy VIX or VIX3M. Deferred 1.0 signals likewise cannot return
through proxy substitution: UUP cannot satisfy DXY, an oil ETF cannot satisfy
Brent, GLD cannot satisfy XAU/USD, and a generic P/E cannot satisfy the deferred
S&P 500 Forward 12M P/E comparison.

## Failure and User Interaction

Any unresolved required field rejects Board generation. The Skill returns one
batched `Data Acquisition Blocker` containing:

- missing field and decision purpose;
- attempted command or source;
- failure status and reason;
- any non-equivalent proxy as context only; and
- the next exact retrieval action.

The user does not waive a retained core field in 1.0. A permanently unavailable
desired signal is removed only by an explicit field-contract revision; a
temporary failure of a retained core field remains a blocker.

Successful Boards show only a concise source and coverage summary. Raw field
paths and detailed acquisition diagnostics remain in the normalized diagnostic
output and are shown only when requested.

## Posture Synthesis

Evidence is grouped into:

- rates;
- volatility;
- large-cap versus small-cap relative strength;
- liquidity; and
- policy events.

Each group returns `supports`, `neutral`, or `pressures` with cited fields. The
Agent synthesizes the final posture from these groups. Version 1.0 does not add
an unvalidated numeric score or probability model.

## Acceptance

Version 1.0 is acceptable when focused tests prove:

1. missing config triggers first-run setup;
2. only one default broker is selected and another broker is never used
   automatically;
3. capability probing records exact command and raw-field mappings without
   secrets;
4. a required field that is missing, stale, unsupported, errored, or conflicted
   produces no Board;
5. multiple missing fields produce one batched blocker;
6. deferred signals are absent from the 1.0 requirement set and cannot return
   through a proxy or a generic substitute;
7. prohibited proxies cannot satisfy required fields;
8. all market inputs share one completed reference date;
9. Board headers disclose market and policy/news cutoffs;
10. successful input produces the existing standalone Macro Board;
11. public fixtures are synthetic and privacy-safe;
12. the installable product contains one canonical `mars-research-assistant`
    Skill and no native Plugin distribution layer;
13. every normalized retained-core raw field contains the required provenance
    and timing metadata, direct public maps verify endpoint/columns/path, and
    no Board value accepts caller-supplied derived data.
