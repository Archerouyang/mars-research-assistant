# Macro Research

## Mars 1.0 Field-First Gate

When producing a Mars 1.0 Macro Board, run the canonical
`macro_preflight.py` seam before rendering. The retained core is deliberately
small and entirely field-contract driven:

- 2Y, 10Y, and 30Y U.S. Treasury yields;
- VIX/VIX3M from direct Cboe histories;
- NDX/RUT, its 1/5/20-session changes, and 20-session normalization from direct
  FRED/Cboe histories;
- reserve balances, TGA, and ON RRP as separate official liquidity fields;
- a seven-day allowlist of FOMC, CPI, employment, GDP, PMI, long-duration
  Treasury auctions, and major central-bank events from their direct official
  calendars;
- White House Presidential Actions as a bounded U.S. executive-policy record.

The exact field identity, unit, timing, and source path for every retained
field live in `mars-1-0-observation-source-contracts.json`. The host must use
this source order for every refresh:

```text
IBKR capability check -> exact IBKR market field when available -> registered
official source -> Web Search discovery plus direct authority-page open when
needed -> normalized field record -> macro_preflight.py
```

The broker route is field-level, not a blanket source preference: it may be
used only when the returned field has exact identity, native path, unit,
timestamp, and completed-close/reference-period basis. For every unsupported
or incomplete broker field, use the registered public primary source instead.
If that path fails, Web Search is mandatory as a discovery fallback: locate and
directly open the authority page, then verify the exact field identity, unit,
timestamp, and completed-close/reference-period basis. Search-result snippets,
ETF proxies, caller-derived ratios, and prewritten `ResearchResult` objects are
not field inputs. Raw provider responses remain in memory and are never
persisted by the Skill.

`macro_preflight.py` uses `web_search_required` only as an internal acquisition
retry state when a registered direct payload exists but fails field validation.
Do not show that state to the user. Repeat acquisition with a
`web_search_then_direct_open` receipt for the affected authority; only that
second failure may become the final Data Acquisition Blocker.

Every retained field is required. Completed-market fields must equal the latest
common completed close; official releases must identify the latest published
observation and preserve the reference period; all seven event-calendar sources
and White House policy evidence must be direct, current captures. Event rows
retain only title, category, scheduled time, timezone, reference period,
consensus, previous, optional revised previous, optional actual, and source
identity. Policy rows retain only title, publication time, source identity,
`confirmed`/`stated_not_enacted`/`unverified_lead`, and a qualitative posture
effect. An `unverified_lead` must be `neutral`. Any missing, stale,
unsupported, conflicted, or source-error field returns one `Data Acquisition
Blocker`. It never produces a partial Board, placeholder, or proxy-backed
result.

Start every Mars Macro request with the field-contract acquisition sequence
above. The absence of a saved `macro-panel.json`, a prior standalone Board, a
private runtime, or a broker configuration is only a missing historical
baseline; it must not block today's public field acquisition. A complete capture
returns a Board. An incomplete capture returns the one `Data Acquisition
Blocker`. Do not ask for broker authorization or private-runtime write approval
before attempting that binary public preflight.

The Board delivery is transient by default. After a valid Board has been
delivered, ask separately before saving or overwriting a private Macro snapshot.
If the user declines persistence, retain no saved runtime artifact and state
only that historical comparison is unavailable. Never combine permission to
read public sources with permission to persist private runtime state.

Run `scripts/broker_capability.py` before Macro acquisition. IBKR is available
only when the current task exposes an Interactive Brokers tool. Do not infer
tool names from user text and do not call positions, accounts, balances,
orders, or credentials during this check. The capability result is not account
authorization.

Macro field sources may be exact IBKR market data or a registered direct public
primary fallback. `scripts/ibkr_macro_adapter.py` currently admits only the
verified TNX and TYX contracts, applies the locked 0.1 scale, and proves the
latest bar is a completed daily close. It does not manufacture a 2Y route; 2Y
uses the official Treasury curve. A field must name its actual source in the
normalized record. Web Search is a discovery fallback rather than a source of
values: it must lead to a directly opened authority page. When used, render the
`fallback_disclosures` records after the Board, naming each affected field,
authority, and common completed close/reference period. A newly discovered
endpoint must receive an exact source map, fixture, and regression test before
it can enter a Board; until then the field remains blocked.

The following are currently excluded: HYG/LQD, SPX, DXY, Brent, gold, and S&P
500 forward P/E. Do not restore any with a proxy or approximation. A later
field-contract revision must establish a direct source and test it first.

The standalone Board is emitted only after every retained field passes this
gate. Its Mars 1.0 surfaces are `Overview`, `Rates & Liquidity`,
`Cross-Asset Impact`, and `Policy Watch`. `Policy Watch` contains the bounded
future-event allowlist and bounded White House policy state; it has no
inflation, generic scenario, or partial-data placeholder view. No raw page
text or outbound network link enter the standalone artifact.

For visuals, show decision-sensitive metrics and their `as_of` in the first
viewport. The current-state view must disclose the common completed market date,
that intraday data is excluded, the news/policy cutoff, and the four qualitative
evidence groups behind the exact posture label. NDX/RUT, VIX/VIX3M, and rates
are time series with direction over the aligned history window. Keep the text
decision-dense, distinguish facts from inferences, and do not create a trade
instruction from the Macro Board.

## Mars Standalone Format

Mars 1.0 keeps one self-contained `standalone_board` artifact. It renders only
the four field-contract surfaces named above. A failed required source path is
a Blocker, not an empty panel and not a partial artifact.

The Board must open without host CSS or network access, and its snapshot, HTML,
and manifest remain paired. Layout and new interaction surfaces still require
explicit visual acceptance before public cutover.
