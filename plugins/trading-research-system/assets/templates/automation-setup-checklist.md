# Daily Ops Automation Setup Checklist

Use this checklist before creating real Codex automations for trading operations.
It is a setup contract, not a market note and not an automation execution prompt.

Do not create real Codex automations until every required confirmation is
present. If anything is missing, return `Missing Decisions` and ask the user.

## Required Confirmations

Collect and confirm:

- Daily Ops thread: the fixed chat/thread that should receive trading-operation
  prompts and summaries.
- timezone: the user's scheduling timezone and the market calendar assumption.
- runtime_dir: the private runtime root, defaulting to
  `~/Documents/dailytrades-runtime` unless the user overrides it.
- enabled automations: which prompts should be scheduled now.
- cadence: exact local time, weekdays/weekends, event-window exceptions, and
  whether intraday monitors should run only when active setups exist.
- allowed sources: public web search, official/primary sources, Longbridge
  macrodata, IBKR connector, Longbridge broker source, manual CSV for a single
  run, and user-provided Seeking Alpha reports, excerpts, links, PDFs, or
  screenshots.
- Longbridge macrodata is an optional macro and financial-conditions source when
  installed and authorized.
- runtime write policy: draft-only, ask before writing, allowed runtime files,
  and no public repo writes.
- read-only broker policy: broker reads require explicit authorization and must
  remain read-only broker access.
- paywall/source policy: no paywall bypass; inaccessible reports become leads
  for the Research Report Intake queue.
- output style: concise Chinese note-style output, focused on changes,
  invalidations, required decisions, and next checks instead of news dumps.

## Supported Automation Set

Use only the automations with stable prompt contracts:

- `deep_update_prompt`: weekly or major-reset Active Market Plan deep update.
- `quick_update_prompt`: weekday premarket or fast daily update.
- `intraday_trigger_monitor`: market-hours monitor for prepared setups only.
- `post_market_review_prompt`: end-of-day setup and review cleanup.
- `position_daily_report`: read-only holdings and risk summary.
- `macro_industry_research_monitor`: recurring focused search over confirmed
  weekly P0/P1 variables.
- `broker_reconciliation_prompt`: optional read-only broker fact alignment when
  the user chooses a broker source.
- `alpha_daily_publish`: private `dailytrades-quant` price refresh, Bayesian
  update, and immutable Alpha snapshot publication after the US close.
- `alpha_weekly_shadow`: purged LightGBM shadow retraining; never changes the
  production rank directly.
- `alpha_monthly_governance`: purged walk-forward report and promotion blockers.
- `alpha_gmail_dispatch`: sends only sanitized audit events from the private
  outbox after a completed Alpha job.

## Output Contract

Return these sections:

### Automation Setup Summary

State what the user is trying to enable and whether setup is complete.

### Confirmed Configuration

List confirmed thread, timezone, runtime_dir, enabled automations, cadence,
allowed sources, runtime write policy, and broker-read policy.

### Missing Decisions

List every missing confirmation. Do not silently assume missing cadence,
thread, broker permissions, or source access.

### Draft Automation Plan

For each enabled automation, list purpose, cadence, target thread, source
requirements, runtime files it may read, runtime files it may propose writing,
and the prompt template it should use.

### Safety Boundaries

Always include:

- no broker write actions;
- no order placement, modification, cancellation, closing, or approval;
- no paywall bypass;
- no full raw broker export saved by default;
- no private runtime or broker data written to the public plugin repo.

### Next Action

If setup is incomplete, ask for the missing confirmations. If setup is complete,
ask whether to create the real Codex automations.
