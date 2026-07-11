# Alpha Leaderboard

Use this reference when the user asks for the current multi-factor Alpha
ranking, ticker lookup, ranking changes, cross-sectional candidates, or the
quantitative input to Trade Plan Preparation.

The Alpha Lab is a separate private system. This public plugin is a read-only
consumer. It does not train models, calculate Alpha Score, change model
probabilities, or promote a challenger.

## Runtime Contract

The normalized private runtime view is:

```text
{runtime_dir}/alpha/leaderboard.sqlite
```

Run `runtime_health.py` first, then use:

```bash
python3 ../../scripts/alpha_leaderboard_adapter.py show --top 10
python3 ../../scripts/alpha_leaderboard_adapter.py query NVDA
python3 ../../scripts/alpha_leaderboard_adapter.py changes --top 10
```

The adapter opens SQLite with `mode=ro`. A missing store is a capability gap;
the adapter must not create an empty database or rebuild the model from public
market data.

Every readable run must declare `model_role=champion`,
`publication_status=published`, a positive `row_count`, and a SHA-256
`snapshot_hash`. The adapter recomputes the hash from the complete ranked rows,
requires contiguous ranks, and rejects incomplete, shadow, stale-schema, or
out-of-range payloads instead of displaying them as production output.

The full eligible universe remains queryable. Normal output shows Top10. Top20
forms the Cross-Section Candidate Pool. Deep research starts with Top5 plus
persistent or rapidly strengthening names inside Top20.

## Agent Boundary

- The stored `Alpha Rank` is authoritative. The agent must not re-rank,
  re-score, reorder, or replace ticker rows using news, charts, macro views, or
  personal preference.
- The Bayesian champion owns `Alpha Score`, historical percentile,
  `P(20D excess return > 0)`, and predictive uncertainty.
- Probability maturity remains `Experimental`; always display predictive
  uncertainty beside the probability.
- A LightGBM challenger may appear as shadow metadata. Challenger output cannot
  change the published order unless Alpha Lab has completed deterministic
  promotion gates and Sol review.
- Trajectory and Top10-memory fields guide research priority only. They do not
  create a setup, entry, exit, or order.
- Macro, industry research, PA, EMA, events, and portfolio risk decide whether a
  ranked ticker deserves further work; they do not edit the model rank.

## Output Contract

For a standalone leaderboard request, return the stored rows and a short delta:

- Alpha Rank, ticker, Alpha Score;
- historical percentile (own-history comparison, not cross-sectional rank);
- `P(20D excess return > 0)` plus predictive uncertainty;
- Rank vs S&P500 and current S&P500 membership when present;
- trajectory, consecutive Top10 days, recent Top10 count, and prior Top10 date;
- candidate/deep-research flags;
- model run id, snapshot date, and freshness status.

For Trade Plan Preparation, use the Alpha snapshot as one input read. Send Top20
to cross-sectional research, then require macro/financial conditions, industry
or company evidence, higher-timeframe structure, portfolio risk, and a defined
next check before creating a candidate setup.

## Legacy KVN Compatibility

`momentum/kvn.sqlite` and `kvn_leaderboard.py` remain a legacy import path for
user-provided KVN snapshots. Prefer the Alpha Leaderboard whenever the Alpha
store is available. Never merge Alpha and KVN scores, silently relabel KVN as
Alpha, or show both as competing production rankings. If Alpha is missing and a
legacy KVN snapshot is available, disclose the fallback and preserve the KVN
script order.
