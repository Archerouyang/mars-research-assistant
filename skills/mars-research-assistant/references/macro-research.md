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

Start every Mars Macro request with the direct-public acquisition sequence
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

Read-only broker setup is separate and only applies to a later
account/portfolio-personalized workflow. Until the user confirms it, report
`authorization_pending` for broker capability only and do not call a broker
probe. After confirmation, run
`scripts/broker_capability.py --confirm-read-only --format json`: Longbridge
uses only `check --format json`; IBKR can be marked available only by a
current-task Interactive Brokers MCP tool name passed as `--task-tool`. Do not
infer tool names from user text or call an IBKR endpoint. Do not read positions,
accounts, balances, tokens, or market payloads. Show the user the available
choices, require exactly one default broker, and explicitly confirm read-only
use before writing the minimal private `mars-runtime-config.json` with
`configure_first_run`. Public and official field routes do not switch the
configured broker. `run_macro_board_from_runtime` remains a compatibility name
for the public blocker-or-Board seam; it does not inspect, require, or write
private broker configuration.

Macro Board fields never come from Longbridge, IBKR, an ETF proxy, a search
snippet, media, or a calendar summary. Broker selection is relevant only to
separately authorized account and portfolio workflows. A direct public source
discovered with Web search may be added only with an exact source map,
synthetic fixture, and regression test; otherwise the field stays absent.

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
