# Price Action

Before concrete levels, establish `ticker + trade_horizon + instrument`. Use the
user's confirmed primary timeframe; auxiliary timeframes refine execution but do
not overwrite the primary structure.

Do not start Price Action merely because a Macro Board or Holdings Display
completed. A user-named ticker starts the named-instrument package and defaults
to the 4H PA Board unless the user narrows the requested scope.

Use authorized OHLCV or user-provided chart data. Distinguish observed structure
from interpretation. Include current price, relevant EMA context, support,
resistance, trigger/reclaim, invalidation, and add/reduce or rebalance zones when
position context is available.

Render bull, base, and bear paths as conditional scenarios, not predictions. For
rolling analysis, compare the prior stored read or state that this is the
baseline. Prefer proportional position language unless the user asks for exact
quantities.

The standalone Board is the primary visual output. Put the chart and key levels
before long prose.

## Frozen Standalone Template

The user accepted the PA template on 2026-07-19 and selected standalone-only
delivery on 2026-07-22. Keep this information hierarchy stable:

1. decision and structure summary;
2. continuous metric strip for current price, primary-timeframe EMA context,
   daily EMA context, and volatility;
3. Chinese `转强 / 整理 / 转弱` controls with `触发 / 路径 / 动作` copy;
4. the dominant price chart with EMA, zones, levels, and selected scenario path;
5. a descending price ladder anchored by the current price;
6. proportional staged entry, reduction, or rebalance actions when applicable;
7. company and direct supply-chain events relevant to the instrument; and
8. a compact, subordinate disclosure for data construction, current structure,
   and event boundaries.

Do not duplicate Macro-panel liquidity events in an instrument PA panel. Do not
render generic stat cards or a plain key-level table. Omit optional sections when
their evidence is absent rather than filling them with generic copy. Structural
changes to this hierarchy, event ownership, or visual interaction require new
user acceptance in the real chat surface.

PNG export is opt-in only. When the user explicitly asks for a downloadable
image, keep the accepted standalone Board HTML as the source and run
`scripts/export_board_png.mjs` to create a full-content PNG. Do not auto-save,
batch-export, or substitute a separately designed static page. Private exports
stay in a local artifact directory; public or README exports require a separate
explicit request and `--public`. They may use synthetic fixtures or dated public
market data after privacy review, but never account, broker, private-runtime, or
private-portfolio information.

Use `scripts/longbridge_ohlcv_adapter.py` for supported read-only OHLCV input
and `scripts/price_action_rollforward.py` when a prior analysis is explicitly
available for comparison. Missing history produces a baseline analysis; it is
not silently reconstructed.
