# Analysis Delta

Use the private analysis store to recover prior conclusions before repeating a
ticker or scope analysis. Chat history is not the source of truth.

Stable key:

```text
symbol/scope + analysis_type + primary_timeframe + strategy_horizon
```

Default read-only store:

```text
{runtime_dir}/knowledge/analysis.sqlite
```

Read the latest full snapshot and its stored delta with:

```bash
python3 ../../scripts/analysis_delta_adapter.py latest \
  --symbol SOXX \
  --analysis-type decision_card \
  --primary-timeframe 1D \
  --strategy-horizon swing \
  --format json
```

Rules:

- Read the latest successful full snapshot before current analysis.
- Resolve latest by `as_of DESC, sequence_id DESC` with `status=success`; a
  later-inserted historical backfill or failed run must not replace newer
  analysis.
- Default user output to `updated`, `added`, and `invalidated` fields. Mention
  `unchanged` only when it confirms that an inherited level or thesis remains
  valid.
- A model-version or rule-version change requires `full_recompute`; do not
  pretend it is a small incremental update. The adapter compares the selected
  run with its successful predecessor and overrides inconsistent stored delta
  metadata fail closed.
- If the store or stable key is missing, say `本次作为基准分析`.
- The adapter is read-only. Current analysis is persisted by the private
  producer after the run, never by editing the database from this plugin.
