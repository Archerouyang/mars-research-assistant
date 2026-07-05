# KVN Model Plan

Status: planning contract. No model implementation is included in the current
plugin slice.

This document defines the future KVN model module. It exists to keep the
quantitative model separate from the Trading Research System plugin while making
the expected data, scoring, validation, and output contracts explicit.

## Goal

Build a daily ticker-level momentum leaderboard model that helps select research
candidates for Trade Plan Preparation. The model should rank liquid stocks and
approved ETFs by a reproducible KVN score, preserve historical Top10 memory, and
write standardized snapshots that the Trading Research System plugin can read.

KVN is a research-priority model. It is not a buy list, not a setup detector,
and not a trading-order system.

## Module Boundary

| Component | Owns | Does not own |
| --- | --- | --- |
| KVN model module | universe, data ingestion, factor computation, ranking, model validation, daily snapshots | trade plan writing, price-action trigger calls, broker reads, order actions |
| Trading Research System plugin | snapshot import/read/query/change summary, Trade Plan Preparation input, concise explanation | factor research, score calculation, model backtesting, vendor selection |
| Agent | explains KVN output and combines it with macro, industry, thesis, price structure, and risk | re-ranking, re-scoring, inventing KVN-like results |

## Output Contract

Every daily snapshot should contain these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `snapshot_date` | yes | completed trading date for the score |
| `model_version` | yes | version of the KVN model formula and data contract |
| `source` | yes | model job, user import, or upstream provider label |
| `benchmark_universe` | yes | benchmark used for `rank_vs_sp500`, initially `S&P500` |
| `ticker` | yes | row key; uppercase ticker only |
| `rank_vs_sp500` | yes | rank relative to the S&P500 benchmark distribution |
| `kvn_score` | yes | primary sort score; higher ranks first |
| `kvn_p` | yes | percentile of current score versus the ticker's recent score history |
| `is_sp500` | yes | whether the ticker is currently in S&P500 |
| `top10_consecutive_days` | derived | consecutive Top10 appearances through `snapshot_date` |
| `top10_count_20d` | derived | Top10 count over the latest 20 imported snapshots |
| `last_top10_date` | derived | previous Top10 date before current snapshot, or `-` |

The plugin may support legacy snapshot CSVs without metadata for manual import,
but model-produced snapshots should include `model_version`, `source`, and
`benchmark_universe`.

## Universe

KVN v1 should use a liquid, configurable U.S.-listed universe.

Initial inclusion rules:

- common stocks, ADRs, and approved ETFs when explicitly enabled;
- price above 5 USD;
- average 20-day dollar volume above 20 million USD;
- market cap above 1 billion USD when the field is available;
- sufficient OHLCV history for the longest active lookback window.

Initial exclusion rules:

- OTC names;
- low-liquidity penny stocks;
- symbols with broken or missing corporate-action-adjusted price history;
- instruments whose structure makes stock-style momentum misleading unless
  explicitly enabled.

Theme and sector labels are model features or analysis context. They are not KVN
rows.

## Candidate Factor Groups

The first model should stay explainable. A starting design can use three factor
groups:

| Group | Purpose | Example signals |
| --- | --- | --- |
| `K`: price momentum | identify strong individual price trends | 20/50/60-day return, risk-adjusted return, return versus SPY/QQQ, proximity to 60-day or 52-week high, EMA stack |
| `V`: volume and volatility quality | prefer liquid, durable momentum over unstable spikes | average dollar volume, volume expansion, ATR-adjusted move, drawdown penalty, realized-volatility penalty |
| `N`: neighborhood momentum | capture theme, industry, and peer-group confirmation | industry ETF strength, peer median return, theme breadth, related-leader participation |

Do not treat `N` as narrative text. It should be a reproducible peer/theme/ETF
feature set.

## Initial Scoring Hypothesis

The initial formula is only a hypothesis and must be validated before use:

```text
kvn_score =
  50% normalized price momentum
+ 20% normalized volume / volatility quality
+ 30% normalized neighborhood momentum
```

The final score should be normalized cross-sectionally for each snapshot date.
`kvn_p` should be computed from the ticker's own rolling score history, with a
default 50 or 60 trading-day lookback.

## Validation Plan

The model should not be treated as reliable until it passes a minimum validation
package:

- point-in-time universe and membership handling;
- adjusted price handling and split/dividend sanity checks;
- walk-forward daily snapshot generation;
- Top10 and Top20 forward return study over 1, 5, 10, and 20 trading days;
- comparison against SPY, QQQ, SPMO, SMH/SOXX, and relevant sector ETFs;
- turnover, drawdown, volatility, and concentration analysis;
- sector/theme concentration report;
- bear, range, and risk-on regime slices;
- forward-test period with no formula changes.

Model changes must produce a new `model_version` and a short validation note.

## Runtime Layout

The future module should write deterministic artifacts under the private runtime
or another user-approved model runtime:

```text
{runtime_dir}/momentum/
  kvn.sqlite
  snapshots/YYYY-MM-DD.csv
  model-runs/YYYY-MM-DD.json
  validation/
```

The public plugin repo should keep only fixtures and contracts, not private
market-data downloads or user-specific model runs.

## Implementation Phases

1. **Contract only**: document model boundary, output fields, universe rules,
   factor groups, and validation requirements.
2. **Data audit prototype**: inspect available authorized OHLCV, corporate
   actions, universe membership, sector/theme mapping, and benchmark data.
3. **Offline factor prototype**: compute candidate factor tables for a fixed
   historical period without connecting to plugin workflows.
4. **Backtest harness**: evaluate Top10/Top20 forward returns, turnover,
   drawdown, regime behavior, and concentration.
5. **Daily job**: run after market close, write model metadata and daily
   snapshots into the private runtime.
6. **Plugin read path**: keep using the existing KVN snapshot read/query/change
   interface; do not move scoring logic into the plugin.
7. **Forward-test governance**: freeze a model version, observe live results, and
   only then increase confidence in Trade Plan Preparation.

## Open Questions

- Which data provider should own adjusted OHLCV, market cap, dollar volume, and
  point-in-time universe membership?
- Should approved ETFs be part of the same rank table or a separate ETF
  confirmation table?
- What is the first benchmark universe beyond S&P500: all liquid U.S. listings,
  Russell 3000, or a broker/data-provider universe?
- Should theme/peer mapping be manual configuration, vendor taxonomy, or a
  hybrid?
- What minimum validation threshold is required before KVN becomes a primary
  research-priority input?
