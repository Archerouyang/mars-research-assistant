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
Longbridge/IBKR capability check -> exact broker market or macro field when
available -> exact public primary-source fallback -> Web Search discovery plus
direct authority-page open when needed -> normalized field record ->
macro_preflight.py
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

Run `scripts/broker_capability.py` before Macro acquisition. Longbridge uses
only `check --format json`; IBKR is available only when the current task
exposes an Interactive Brokers market-data-capable tool. Do not infer tool names
from user text and do not call positions, accounts, balances, orders, or tokens.
The capability result is not an account authorization and does not choose a
portfolio source.

Macro field sources may be Longbridge macrodata/market data, IBKR market data,
or a registered direct public primary fallback. A field must name its actual
source in the normalized record. Web Search is a discovery fallback rather than
a source of values: it must lead to a directly opened authority page. When it
is used, the Board follow-up must state the affected fields, authority, and
common completed close/reference period. A newly discovered endpoint must
receive an exact source map, synthetic fixture, and regression test before it
can enter a Board; until then the field remains blocked rather than being
inferred from a search result.

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

## Legacy Frozen Macro Data Workflow (Compatibility Only)

The following 0.2.0 workflow remains as a compatibility reference for its
existing CLI helpers. It is not a Mars 1.0 Board acquisition route and cannot
override the direct-web gate above:

1. Establish capability with `longbridge --version` and `longbridge check`.
   Current-chat tool visibility, CLI installation, authentication, and data
   completeness are separate states. A sandbox-only log-file warning is not an
   authentication failure when the command itself returns valid data.
2. Discover macro indicator codes, then query a discovered code:

   ```bash
   longbridge macrodata --keyword <TERM> --country <COUNTRY> --format json
   longbridge macrodata <CODE> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --limit <N> --format json
   ```

   Do not guess or permanently hard-code an indicator code when the discovery
   response can supply it.
3. Read supported market history with:

   ```bash
   longbridge kline history <SYMBOL> --period day --start <YYYY-MM-DD> --end <YYYY-MM-DD> --format json
   ```

   This macro workflow is market-data and macrodata only; it does not call
   portfolio, assets, positions, or order commands.
4. Use purpose-specific sources for unsupported series instead of forcing one
   connector to own every fact: U.S. Treasury for the yield curve, Cboe for RUT
   and VXN, and an exact DXY index source for DXY. A labelled proxy is allowed
   only when the exact series is unavailable and the limitation remains
   visible.
5. Align market series to the same one-month observation window and common
   sessions before calculating ratios or changes. NDX/RUT must use same-session
   closes; missing observations are not silently forward-filled.
6. Preserve actual, forecast, media, and thesis categories, source registry,
   `as_of`, and data-gap disclosure through `ResearchResult -> DeliveryPacket`.
   Public fixtures remain visibly synthetic and can never support a live claim.
7. Render one self-contained standalone Board as a transient delivery packet.
   Retain a private snapshot only after the user separately approves that
   write. Do not emit an iframe, parallel inline fragment, or cross-unit bar
   chart.

Use this CLI-first sequence for eligible Mars Board fields only after preserving
the exact source identity and normalized field contract. Do not reinterpret
missing data as authorization failure, relabel a proxy as an exact index, or add
a second visual delivery path.

The retained read-only implementation surface is
`scripts/longbridge_macrodata_adapter.py` for normalized Longbridge responses
and `scripts/prepare_macro_panel.py` for an explicitly requested local macro
panel. Neither helper reads broker positions or performs order actions.

## Mars Standalone Format

Mars 1.0 keeps one self-contained `standalone_board` artifact. It renders only
the four field-contract surfaces named above. A failed required source path is
a Blocker, not an empty panel and not a partial artifact.

The Board must open without host CSS or network access, and its snapshot, HTML,
and manifest remain paired. Layout and new interaction surfaces still require
explicit visual acceptance before public cutover.
