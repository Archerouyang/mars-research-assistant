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
live in `mars-1-0-observation-source-contracts.json`. The host must use this
sequence for every refresh:

```text
web search -> direct open of the exact contract URL -> MarsWebCapture ->
mars_observation_adapter.py -> macro_preflight.py
```

`MarsWebCapture` is transient and requires a direct-open receipt for every
contract source. The public `run_macro_board` seam accepts that typed capture
only: it does not accept a generic payload map, broker configuration, proxy,
search-result snippet, caller-derived ratio, or prewritten `ResearchResult`.
Raw page responses remain in memory and are never persisted by the Skill.

Every retained field is required. Completed-market fields must equal the latest
common completed close; official releases must identify the latest published
observation and preserve the reference period; policy evidence must be fetched
within 24 hours. Any missing, stale, unsupported, conflicted, or source-error
field returns one `Data Acquisition Blocker`. It never produces a partial Board,
placeholder, or proxy-backed result.

Before the first Mars Macro run, obtain only a capability-only probe for
Longbridge and IBKR. Do not read positions, accounts, balances, tokens, or
market payloads. Ask the user to choose exactly one available default broker
and explicitly confirm read-only use, then write the minimal private
`mars-runtime-config.json` with `configure_first_run`. Public and official
field routes do not switch the configured broker. Later runs use
`run_macro_board_from_runtime`: an absent config returns setup guidance, and a
field-contract, Skill-version, or capability-probe change returns
`capability_recheck_required` without a Board or broker read.

Macro Board fields never come from Longbridge, IBKR, an ETF proxy, a search
snippet, media, or a calendar summary. Broker selection is relevant only to
separately authorized account and portfolio workflows. A direct public source
discovered with Web search may be added only with an exact source map,
synthetic fixture, and regression test; otherwise the field stays absent.

The following are currently excluded: HYG/LQD, SPX, seven-day event calendars,
DXY, Brent, gold, and S&P 500 forward P/E. Do not restore any with a proxy or
approximation. A later field-contract revision must establish a direct source
and test it first.

The standalone Board is emitted only after every retained field passes this
gate. Its Mars 1.0 surfaces are `Overview`, `Rates & Liquidity`,
`Cross-Asset Impact`, and `Policy Watch`; it has no inflation, generic event,
or partial-data placeholder view. The policy surface shows only title,
publication time, and a White House source label: no raw page text and no
outbound network link enter the standalone artifact.

For visuals, show decision-sensitive metrics and their `as_of` in the first
viewport. NDX/RUT, VIX/VIX3M, and rates are time series with direction over the
aligned history window. Keep the text decision-dense, distinguish facts from
inferences, and do not create a trade instruction from the Macro Board.

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
7. Render one self-contained standalone Board and retain its snapshot and
   manifest for event follow-up. Do not emit an iframe, parallel inline
   fragment, or cross-unit bar chart.

Do not use this CLI-first sequence to populate a Mars Board, reinterpret
missing data as authorization failure, relabel a proxy as an exact index, or
add a second visual delivery path.

The retained read-only implementation surface is
`scripts/longbridge_macrodata_adapter.py` for normalized Longbridge responses
and `scripts/prepare_macro_panel.py` for an explicitly requested local macro
panel. Neither helper reads broker positions or performs order actions.

## Mars Standalone Format

Mars 1.0 keeps one self-contained `standalone_board` artifact. It renders only
the four direct-field surfaces named above. A failed direct source is a Blocker,
not an empty panel and not a partial artifact.

The Board must open without host CSS or network access, and its snapshot, HTML,
and manifest remain paired. Layout and new interaction surfaces still require
explicit visual acceptance before public cutover.
