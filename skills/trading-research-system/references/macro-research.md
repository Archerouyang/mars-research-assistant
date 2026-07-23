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
- White House Presidential Actions as a bounded U.S. executive-policy record.

The exact source URL, column/path, timing, and unit for every retained field
live in `mars-1-0-observation-source-contracts.json`. `mars_observation_adapter.py`
accepts only those raw source payloads in memory, normalizes them, and refuses
to persist the raw payload. `macro_preflight.py` derives ratios and changes
inside the boundary; callers cannot supply derived values or a prewritten
`ResearchResult`.

Every retained field is required. Completed-market fields must equal the latest
common completed close; official releases must identify the latest published
observation and preserve the reference period; policy evidence must be fetched
within 24 hours. Any missing, stale, unsupported, conflicted, or source-error
field returns one `Data Acquisition Blocker`. It never produces a partial Board,
placeholder, or proxy-backed result.

Macro Board fields never come from Longbridge, IBKR, an ETF proxy, a search
snippet, media, or a calendar summary. The configured broker remains relevant
only to separately authorized account and portfolio workflows. A direct public
source discovered with Web search may be added only with an exact source map,
synthetic fixture, and regression test; otherwise the field stays absent.

The following are currently excluded: HYG/LQD, SPX, seven-day event calendars,
DXY, Brent, gold, and S&P 500 forward P/E. Do not restore any with a proxy or
approximation. A later field-contract revision must establish a direct source
and test it first.

The standalone Board displays only fields that passed this gate. Its default
surfaces are `趋势`, `当前状态`, and `情景`; `下周事件` and `白宫政策` appear
only when their corresponding direct field is admitted. The policy surface
shows only title, publication time, and a White House source label: no raw page
text and no outbound network link enter the standalone artifact.

For visuals, show decision-sensitive metrics and their `as_of` in the first
viewport. NDX/RUT, VIX/VIX3M, and rates are time series with direction over the
aligned history window. Keep the text decision-dense, distinguish facts from
inferences, and do not create a trade instruction from the Macro Board.

## Legacy Frozen Macro Data Workflow

The user accepted and froze the following workflow on 2026-07-19 for the 0.2.0
release:

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
7. Render one self-contained standalone Board and retain its snapshot and
   manifest for event follow-up. Do not emit an iframe, parallel inline
   fragment, or cross-unit bar chart.

Without renewed user acceptance, do not replace this CLI-first sequence with a
bespoke scraper, collapse purpose-specific sources into Longbridge, reinterpret
missing data as authorization failure, relabel a proxy as DXY, change the
one-month default, or add a second visual delivery path.

The retained read-only implementation surface is
`scripts/longbridge_macrodata_adapter.py` for normalized Longbridge responses
and `scripts/prepare_macro_panel.py` for an explicitly requested local macro
panel. Neither helper reads broker positions or performs order actions.

## Mars Standalone Format

Mars 1.0 keeps one self-contained `standalone_board` artifact. `趋势`, `当前状态`,
and `情景` are always present. `下周事件` is present only if a complete direct
event contract is admitted; `白宫政策` is present only when the verified White
House policy field is available. This conditional visibility prevents a missing
field from becoming a misleading empty panel.

The trend view uses selectable time series; scenarios use `触发`, `确认`, `传导`,
and `应对`. The Board must open without host CSS or network access, and its
snapshot, HTML, and manifest remain paired. Layout and new interaction surfaces
still require explicit visual acceptance before public cutover.
