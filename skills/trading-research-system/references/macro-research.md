# Macro Research

## Mars 1.0 Field-First Gate

When producing a Mars 1.0 Macro Board, run the canonical
`macro_preflight.py` seam before rendering. The retained 1.0 core is rates,
HYG/LQD credit, VIX/VIX3M, SPX/NDX/RUT relative strength, the separate reserve
balances/TGA/ON RRP series, and approved event or U.S. executive-policy risk.

Every retained core field must have an exact, fresh, semantically verified
source and the completed-market fields must share one market-reference date. A
missing, stale, unsupported, conflicted, or source-error core field returns one
batched `Data Acquisition Blocker`; it does not produce a partial Board,
placeholder, or proxy-backed result.

DXY, ICE Brent settlement/contract/roll state, XAU/USD, and S&P 500 Forward
12M P/E history are deferred from the 1.0 contract. Do not restore them with
UUP, oil ETFs, GLD, generic P/E, or another approximation. Reintroducing any
of them requires a direct public source map and a synthetic golden case in a
new field-contract revision.

The frozen 0.2 workflow below is historical context only. It cannot override
the Mars 1.0 field contract.

Separate actual data, forecasts, media context, and plan assumptions. Evaluate
the transmission chain rather than listing headlines:

`event or policy -> rates/liquidity/USD/credit/commodities -> industries and holdings -> plan consequence`

Use official sources for releases and policy facts, authorized macro/market
sources for current values, and media only as leads. A forecast never replaces
an actual release.

When the Longbridge CLI exposes `macrodata`, use it for supported indicator
history, actuals, forecasts, and release metadata. Do not assume it supplies
every market series: use U.S. Treasury data for the daily yield curve and Cboe
data for VXN and RUT when those series are absent. A proxy such as UUP must be
labelled as a proxy and must never be presented as DXY.

For visuals, put decision-sensitive numbers and charts in the first viewport.
Show at least the metrics that drive the stated posture, their `as_of`, and
scenario confirmation. Missing values remain visible.

The stable macro Board uses four compact views: `趋势`, `当前状态`,
`下周事件`, and `情景`. Its minimum observation set is:

- short and long rates: 2Y plus 10Y and/or 30Y;
- inflation actuals: headline/core CPI and headline/core PPI when available;
- cross-asset breadth and volatility: NDX/RUT and VXN;
- the additional USD, credit, commodity, and liquidity readings that actually
  drive the stated posture.

Machine states remain stable internally, but visible status labels and scenario
descriptions use the response locale. Do not use a cross-unit bar chart as the
primary Macro visual. NDX/RUT, VXN, DXY, and decision-sensitive rates must be
shown as time series with visible direction and change over the selected
window. Unless the user requests another horizon, use one month of aligned
market sessions. The trend explanation must state the period change, important
inflection, cross-asset confirmation, and implication for market breadth,
volatility, liquidity, or duration risk.

Every next-week event row states why the event matters, the exact observation
to monitor, and which scenario becomes more likely under hotter/tighter versus
cooler/easier evidence. Scenarios must connect current evidence, the upcoming
event trigger, cross-asset confirmation, and the plan consequence; a label
without that causal chain is incomplete.

Color emphasis is reserved for events explicitly classified as high impact by
the research result. Do not infer importance in the renderer and do not force a
highlight when the evidence is mixed.

The current-state view explains the liquidity background through relative
asset preference and impact. For a US equity view, consider value, mega-cap
platforms, broad technology, semiconductors, momentum, and small caps when they
are decision-relevant. Do not repeat plan constraints in place of asset-impact
analysis.

Keep visible copy decision-dense: one function per field, one conclusion per
sentence, and no restatement across `trigger`, `confirmation`, `transmission`,
and `response`. Prefer compact clauses over narrative paragraphs. Preserve
necessary evidence and uncertainty; remove only repetition and filler.

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

## Frozen Standalone Format

The Macro structure accepted on 2026-07-19 and migrated unchanged to standalone
delivery on 2026-07-22 is frozen: summary strip, `趋势`, `当前状态`, `下周事件`,
and `情景`, in that order. The trend view uses selectable time series; current state uses the
liquidity note and asset-preference matrix; events use importance only when the
research result explicitly supplies it; scenarios use comparison rows with
`触发`, `确认`, `传导`, and `应对`.

Without renewed visual acceptance, changes are limited to source-backed data,
provenance, timestamps, concise copy, accessibility, and defect fixes that do
not alter the information architecture or interaction model. Layout, tab order,
primary interactions, and scenario presentation require renewed visual
acceptance.
