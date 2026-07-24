# Alpha Lab 1.0 Plan

Status: approved implementation contract.

This plan replaces the unimplemented KVN-model hypothesis with an independent,
auditable multi-factor research system. The user-facing product name is
`Alpha Leaderboard` / `多因子 Alpha 榜`. KVN remains a legacy import alias only.

## Product Boundary

`dailytrades-quant` is a separate private quant-research repository. It owns
public-data ingestion, point-in-time normalization, factor computation, model
training, walk-forward validation, model registration, daily inference, and
Alpha Leaderboard snapshots.

The public `mars-research-assistant` Skill will consume versioned snapshots and validation
summaries. It owns natural-language routing, concise explanation, incremental
analysis, Trade Plan Preparation, Price Action timing, and portfolio-risk
context. It must not let an agent re-rank or rewrite deterministic model output.
The existing optional external-snapshot router remains the current behavior
until the Skill-integration slice and its executable contract are complete.

The system is decision support. It performs no order actions and does not imply
approval of a broker order. Personal positions, broker exports, raw market data,
model binaries, API keys, and private run history remain outside the public
Skill repository.

The 1.0 model maturity is `Experimental`. A model result may prioritize
research, but it must not be described as a verified trading win rate.

## Data Architecture

The default private code/runtime split is:

```text
~/Documents/dailytrades-quant/          # private Git repository: code/contracts
~/Documents/dailytrades-quant-runtime/  # ignored data, models, runs, reports
~/Documents/mars-research-assistant-runtime/        # Skill-consumable current state/cache
```

FMP is the primary 1.0 provider for the symbol master, daily adjusted OHLCV,
delisted companies, symbol changes, historical constituents, financial
statements, and supported bulk datasets. The implementation reads its secret
only from `FMP_API_KEY`, redacts it from URLs/errors/logs, probes endpoint
capability, and records provider/plan limitations.

SEC EDGAR submissions and company facts verify CIK mappings, filing dates, and
source financial facts. Nasdaq Trader verifies current listing metadata.
FRED/ALFRED and Treasury official sources own macro/rates history. Authorized
Longbridge data may cross-check current values. The Qlib Yahoo collector is an
Experimental fallback, not a truth source.

Raw and normalized panel data use partitioned Parquet. Every dataset records
provider, fetch time, market-data cutoff, adjustment policy, schema version,
quality status, missingness, and a content fingerprint. A failed critical
quality gate preserves the last valid snapshot as stale; it never creates a
fake current leaderboard.

The liquid U.S. universe includes NYSE, Nasdaq, and NYSE American common stocks
and ADRs. It excludes ETFs from stock ranking, leveraged products, OTC,
preferred shares, SPAC shells, penny stocks, insufficient-history names, and
symbols failing configurable price, market-cap, or dollar-volume thresholds.
S&P 500 membership is metadata and a benchmark, not a universe restriction.

Raw data should retain the longest available history. The first formal
experiment uses data from 2010 onward, walk-forward evaluation from 2016, an
eight-year rolling LightGBM window versus an expanding-window control, and a
strict recent out-of-sample period from 2024 onward.

## Factor Architecture

Every factor belongs to a versioned Factor Registry containing:

- canonical name, family, formula, input datasets, lookbacks, availability lag;
- economic rationale, expected sign, universe applicability, and known failure
  modes;
- leakage, missingness, outlier, turnover, correlation, and stability checks;
- experiment runs, ablation results, promotion history, and current status.

The first production candidate set includes:

- Qlib Alpha158-style price and volume transforms;
- 5/10/20/50/60/120-day momentum, trend quality, and drawdown recovery;
- volume and dollar-volume moving averages, volume expansion, and price-volume
  confirmation;
- realized volatility, ATR-like range, downside risk, tail loss, and drawdown;
- liquidity, trading continuity, and dollar-volume stability;
- 20/50/200 EMA distance, slope, and stack features;
- level-one sector ETF and level-two industry/theme ETF relative strength;
- breadth, SPY/QQQ/IWM context, rates, credit, USD, and liquidity interactions;
- a small filing-date-aligned SEC fundamental quality and growth set.

Analyst revisions, options flow, short interest, ETF flow, 13F/crowding, and
news/report sentiment start as research adapters. They cannot enter the
champion until data provenance and point-in-time behavior pass validation.

Agents may generate and test candidate factors autonomously. Promotion requires
pre-registered formulas, walk-forward evidence, transaction-cost evaluation,
ablation, regime stability, an audit record, and the model-governance gate.

## Autonomous Factor Research Campaigns

Autonomous factor research borrows the constrained experiment loop from
Karpathy's `autoresearch`: a small editable hypothesis surface, a fixed
evaluation harness, a bounded experiment budget, and an explicit keep/discard
ledger. It does not permit an agent to optimize the evaluator, data cutoff, or
published model around a single backtest statistic.

Each campaign has an immutable Campaign Contract that records:

- the point-in-time dataset fingerprints, universe rules, label, benchmark,
  availability lags, adjustment policy, train/walk-forward/recent-OOS windows,
  transaction-cost model, random seeds, and compute/time budget;
- the fixed leakage, missingness, outlier, correlation, reproducibility, and
  cost checks; and
- the pre-declared multi-objective eligibility gates for Rank IC/ICIR,
  TopN excess return, turnover, transaction cost, drawdown, tail loss, and
  regime stability.

The agent may only add or edit an isolated, versioned Factor Candidate Spec:
formula or composition, inputs, lookbacks, availability lag, expected sign,
economic rationale, and known failure modes. The data loader, point-in-time
normalizer, labels, splitters, costs, gates, champion configuration, and
published snapshot path are read-only within a campaign. An agent-generated
code adapter is allowed only on a private experiment branch after the spec is
registered and its deterministic unit and leakage checks pass.

One loop is: propose and pre-register one hypothesis; normalize and validate
it; run the unchanged harness within the campaign budget; append the result to
the Experiment Ledger; then retain it as a research candidate or discard it.
Crashes, failed quality gates, and non-improving trials are recorded rather
than silently retried or erased. A retained candidate remains experimental; it
does not modify the champion, daily inference, Alpha Leaderboard, or Skill.

The private Experiment Ledger is append-only and records campaign and trial
IDs, Git commit, Factor Candidate Spec hash, dataset/model/evaluator versions,
budget consumption, all validation metrics, status (`kept`, `discarded`,
`failed`, or `blocked`), and a concise rationale. It is backed by immutable
run manifests and Parquet/SQLite indexes, with reports stored outside the
public Skill repository.

Unlike a single-score training experiment, factor retention is a Pareto-style
screen: a candidate must meet hard safety gates and demonstrate incremental
value after correlation and ablation checks. Model promotion remains governed
by the separate shadow, immutable-report, rollback, and Sol-review rules below.
Campaigns have explicit weekly trial and compute ceilings, and stop when data
quality is stale, the budget is exhausted, or a required gate is unavailable.

## Research Observability And Artifacts

The [kansoku](https://github.com/Innei/kansoku) project is a useful reference
for the separation between source data, orchestrated research workflows, and
durable research artifacts. Alpha Lab adopts that record-and-index discipline,
not its personal trading journal, real-time monitoring scope, or account-data
model.

For every campaign and accepted candidate, the private runtime writes immutable,
schema-versioned artifacts: the Campaign Contract, Factor Candidate Spec, run
manifest, deterministic evaluation summary, metric tables, failure records,
and concise research note. These artifacts are the research record. SQLite may
index runs, reports, and latest-success pointers for fast retrieval, but it
cannot replace, rewrite, or become the only copy of the underlying evidence.

The 1.0 presentation remains chat-first with immutable static report bundles.
It does not add a persistent dashboard, personal trade journal, real-time quote
service, or broker-position surface. A future local read-only observability
console may render the same report bundle and historical chart data using the
latest presentation code, but it must not alter the stored run, re-rank model
output, or expose private data. Deterministic computed metrics remain distinct
from any optional AI commentary and execution telemetry.

## Model Architecture

The prediction label is the future 20-trading-day excess return versus SPY.
Industry and theme ETF strength are model features; the label is not fully
sector-neutralized because the trading system deliberately seeks strong
industry leadership. A separate attribution decomposes broad market, industry,
and stock-specific contributions.

The initial Bayesian champion is a transparent, time-decayed Bayesian linear
factor model. It produces a posterior expected excess return and predictive
uncertainty. The primary Alpha Score is a risk-adjusted posterior score. This
predictive uncertainty must remain visible beside any probability. It also
publishes `P(20D excess return > 0)` with an uncertainty interval and
`Experimental` maturity.

The LightGBM challenger learns nonlinear factor interactions and emits an
independent cross-sectional ranking. It runs in shadow mode and does not expose
an uncalibrated probability. Ranking objectives and regression objectives may
both be evaluated, but the winning configuration is selected only from
walk-forward results.

Primary validation metrics are Rank IC, ICIR, Top5/Top10/Top20 excess return,
Top-minus-bottom spread, drawdown, tail loss, turnover, estimated transaction
cost, concentration, and regime stability. Hit rate is secondary. Personal
trade records are not model labels; they evaluate the downstream research and
execution process separately.

## Knowledge Base

The private knowledge base uses three storage modes:

- Parquet for market panels, factors, predictions, and leaderboard history;
- SQLite for entities, run indexes, model/factor registries, source claims,
  exact retrieval, latest-success pointers, and relationships;
- SQLite FTS5 for research notes, report summaries, PA cases, and trade-review
  text.

An external vector database is not required for 1.0. Exact structured retrieval
precedes full-text retrieval. Future embeddings may improve recall for long
research reports, but cannot become a fact authority.

Every analysis run writes a full snapshot and a delta against the previous
successful run with the same stable key:

```text
symbol/scope + analysis_type + primary_timeframe + strategy_horizon
```

The dependency graph fingerprints market data, holdings, events, factors,
models, knowledge rules, and source claims. Only changed nodes are recomputed.
The user-facing note defaults to the delta, while the full snapshot remains
available for deterministic reconstruction. A model, schema, or rule-version
change forces a full recomputation.

Expert material is stored as sourced, challengeable knowledge. Public Jane
Street material contributes probabilistic reasoning, expected value,
calibration, market microstructure, and risk principles. Licensed/user-provided
Al Brooks material contributes high-level Price Action classification. Neither
is presented as proprietary replication or unquestionable authority.

## Skill Integration

The quant lab publishes a versioned full-universe snapshot plus validation and
run metadata. The Skill caches a read-only normalized view in the private
runtime. New snapshots use Alpha names; legacy KVN CSV/SQLite imports remain a
compatibility path during migration.

The full eligible universe remains queryable. Normal chat output shows Top10,
the Cross-Section Candidate Pool considers Top20, and deep research prioritizes
Top5 plus persistent or rapidly strengthening Top20 names. Trajectory states
are `new`, `strengthening`, `persistent`, and `fading`; they do not alter the
model rank.

Each symbol analysis uses the same Decision Card:

1. delta from the prior run;
2. explicit decision state;
3. Alpha rank, persistence, factor attribution, model probability, and
   uncertainty;
4. large-timeframe regime using 1W/1D/4H as appropriate;
5. 1H-or-lower execution context;
6. Al Brooks-style PA plus 20/50/200 EMA;
7. timeframe-owned support, resistance, add, and TP/trim zones;
8. relevant weekly events and news;
9. invalidation and next check;
10. proportional sizing language unless exact sizing is requested.

Numeric probabilities are model-owned. Macro/news/PA/EMA synthesis may give a
clear action state and evidence strength, but cannot invent a probability.

## Model Governance

There is one published Alpha Leaderboard champion and one or more shadow
challengers. A challenger may promote autonomously only after deterministic
gates pass, at least 20 trading days of shadow operation complete, and an
immutable promotion report and rollback point are written.

Promotion requires a recorded GPT-5.6 Sol review when Sol is available. If Sol
is unavailable, autonomous promotion is blocked and the challenger remains in
shadow mode; the system must report the capability gap rather than silently
substitute a lower tier.

Promotion must improve rank quality and Top-portfolio behavior without an
unacceptable deterioration in turnover, transaction cost, drawdown, tail risk,
or regime stability. Post-promotion monitoring can automatically roll back to
the prior champion after the same Sol escalation and an immutable rollback
record.

Daily ingestion, Bayesian update, inference, and leaderboard history run after
the completed U.S. trading session. LightGBM retrains weekly. Full walk-forward
and hyperparameter evaluation run monthly. Factor experiments and promotion
checks run weekly. The exchange calendar, not a fixed Beijing-time cron, owns
trading-day scheduling.

Local registries are authoritative. Gmail is an optional notification channel:
send immediate concise notices for Top5 entries, stale/failed runs, drift,
promotion, and rollback; send one weekly research digest; never include secrets
or private broker details.

When model-tier subagents are available, Luna performs bounded preprocessing,
Terra performs primary analysis, and Sol reviews escalation cases. Deterministic
scripts and registries remain the source of truth regardless of model tier.

## 1.0 Acceptance

Alpha Lab 1.0 is accepted only when:

1. `dailytrades-quant` is a private Git-managed, uv-based project with no
   committed secrets or private datasets.
2. FMP capability probing, public-source fallbacks, redaction, incremental
   ingestion, corporate-action handling, and data-quality reports pass tests.
3. A small pilot universe and then the full eligible universe complete an
   end-to-end run without future leakage.
4. The Factor Registry, autonomous-research Campaign Contract and Experiment
   Ledger, Bayesian champion, LightGBM challenger, walk-forward metrics, model
   registry, and reproducible run manifests are present.
5. The daily Alpha snapshot supports full-universe query, Top10 display, Top20
   research intake, Top5 focus, persistence fields, factor attribution, and
   Experimental model probability.
6. The knowledge base can retrieve the previous matching run, compute a delta,
   preserve a full snapshot, and force recomputation on version changes.
7. The Skill consumes the new snapshot without agent re-ranking and renders
   the fixed Decision Card with probability boundaries.
8. Daily, weekly, and monthly schedules pass isolated dry-runs; only then are
   real automations and Gmail notifications enabled.
9. Both repositories pass their focused tests, full verification suites,
   secret scans, and fresh-chat acceptance before release promotion.

The active runtime starts clean with only the approved private trading profile.
Old runtime artifacts remain outside the active retrieval root and are not an
input to 1.0 acceptance.
