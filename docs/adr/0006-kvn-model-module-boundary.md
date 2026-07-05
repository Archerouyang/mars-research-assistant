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
