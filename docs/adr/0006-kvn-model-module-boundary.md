# KVN model module boundary

The system will treat KVN as a separate quantitative model module that produces
daily ticker-level momentum snapshots. The Trading Research System plugin will
consume those snapshots, but will not own model construction, factor research,
vendor selection, or backtesting.

**Considered Options**

- Put KVN factor calculation directly inside the Trading Research System plugin.
- Keep KVN entirely outside the project and only allow manual CSV import.
- Define a separate KVN model module contract, then let the plugin consume the
  module's standardized outputs.

**Decision**

Use a separate KVN model module contract. The KVN model module is responsible for
universe selection, market-data ingestion, factor computation, score ranking,
historical Top10 memory, model versioning, and validation. The plugin is
responsible only for reading the resulting snapshots, querying tickers, showing
Top10, summarizing changes, and feeding ticker candidates into Trade Plan
Preparation.

The KVN module may later live in a separate package, repository, or runtime job.
Until that implementation exists, the plugin must continue to treat KVN as an
imported or upstream snapshot source.

The KVN module does not need to run on the same machine as the plugin. It may run
as a local batch job, cloud scheduled job, GitHub Action, managed container, or
read-only model API, provided the plugin receives the same standardized
snapshot/API contract. Deployment location is an implementation detail; the
architectural dependency is the versioned model output.

**Consequences**

- The plugin must not calculate, re-rank, re-score, or relabel KVN rows.
- KVN rows remain ticker-level rows only; sectors and themes remain context
  inputs outside the KVN table.
- KVN snapshots must include model metadata such as source, model version, data
  date, and benchmark universe before they are treated as model outputs.
- KVN model implementation can be planned and tested independently from Trading
  Research plugin behavior.
- The model must be validated through backtests and forward tests before its
  scores are used as a high-confidence research-priority input.
- Cloud deployment is allowed, but the plugin should cache imported/fetched
  snapshots into the private runtime before using them so research notes remain
  reproducible.
- Any cloud API must be read-only from the plugin's perspective and must not
  make the plugin responsible for model scoring, vendor data licensing, or
  backtest governance.
