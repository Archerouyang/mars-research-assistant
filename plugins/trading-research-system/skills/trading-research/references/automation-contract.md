# Automation Contract

Use this reference when connecting Codex automations to the Trading Research System.

Automations are orchestration. They should wake the agent, inspect local/project state, ask for missing inputs, and propose updates. They must not place trades, modify broker accounts, or silently rewrite discretionary trading records.

Use separate thread boundaries:

- plugin development automations belong in the plugin development chat/repo;
- trading-operation reminders and assistant prompts belong in the fixed `交易研究 Daily Ops` chat and private runtime directory.

These are not automated trading systems. They may remind, inspect, summarize, and ask for human decisions; they must not place, route, modify, cancel, or approve orders.

## Automation Types

### Development Automations

These keep the plugin project moving:

- weekday development and task-planning brief;
- end-of-day development progress review;
- roadmap/project log update prompt.

They use `docs/DEVELOPMENT_PLAN.md` as the source of truth and should focus on product-capability work.

The daily task-planning brief should:

- inspect git status, `docs/DEVELOPMENT_PLAN.md`, `docs/ROADMAP.md`, `docs/PROJECT_LOG.md`, `CONTEXT.md`, and plugin files;
- report current P0/P1/P2 product tasks and status;
- recommend one main product-capability task for the day;
- ask the user for available time, chosen task, optional secondary task, definition of done, verification, and whether Claude Code should be assigned work;
- ask whether completion should update only `docs/DEVELOPMENT_PLAN.md` or also public roadmap/log files.

The end-of-day progress review should:

- ask what was planned, completed, verified, committed, pushed, blocked, or deferred;
- ask whether Claude Code contributed work;
- update project planning docs only after user confirmation;
- keep GitHub trajectory current when public capability boundaries or plugin behavior changed.

### Trading Operations Automations

These support the Active Market Plan loop:

- `deep_update_prompt`: weekend or major reset prompt for Active Market Plan review.
- `quick_update_prompt`: weekday premarket prompt for current market deltas and setup status changes.
- `intraday_trigger_monitor`: market-hours check for active/approaching/triggered setups.
- `post_market_review_prompt`: end-of-day prompt for setup status cleanup and trade review needs.
- `broker_reconciliation_prompt`: read-only broker data alignment prompt when the user opts into a broker source.
- `position_daily_report`: scheduled read-only holdings and portfolio-risk summary, modeled after broker-native position reminders but broker-agnostic.

## Source Of Truth

Trading automations should read:

- `{runtime_dir}/market-plan.md` for current state;
- `{runtime_dir}/trading-profile.md` for private strategy scoring, pools, ETF groups, instrument preferences, timeframe rules, and avoid rules when available;
- `{runtime_dir}/updates/YYYY-MM-DD.md` for the update trail;
- `{runtime_dir}/daily/YYYY-MM-DD/trade-plans.csv`;
- `{runtime_dir}/daily/YYYY-MM-DD/intraday-watchlist.csv`;
- saved report or review artifacts when they exist.

Broker facts should be read live from authorized read-only broker sources when the run requires current positions, account risk, executions, or order status. Do not require a local `trades.csv`, Google Sheet, or durable broker CSV as the source of truth for objective broker facts.

Default `runtime_dir` is `~/Documents/dailytrades-runtime`. The user or automation may override it with `TRADING_RESEARCH_RUNTIME_DIR`, script-level `--runtime-dir`, or the config template at `assets/templates/config.toml`.

If a file is missing, the automation should report the gap and ask whether to initialize or import data. It should not invent current plan state.

If `{runtime_dir}/trading-profile.md` is missing, ask for the relevant strategy posture, pool, instrument, timeframe, and avoid-rule preferences before translating setups into products.

## Broker Safety

Broker data access is read-only.

Before the first broker read in an automation run, ask which source to use:

- IBKR connector;
- Longbridge skill/plugin;
- manual CSV;
- no broker data for this run.

If broker authorization fails, fall back to manual CSV or run without broker facts. Do not retry by using a broker write-capable tool.

## Trading Automation Behaviors

### Deep Update Prompt

Purpose:

- review prior trades;
- refresh current market read, macro/rates, policy/news, future events, momentum leaderboard, setup pool, and risk budget.

Output:

- concise Chinese Markdown;
- proposed `market-plan.md` changes;
- append-only update note draft;
- questions for missing user context.

Do not edit files without user confirmation.

### Quick Update Prompt

Purpose:

- identify what changed since the current Active Market Plan;
- update setup statuses and levels;
- surface new evidence or invalidations.

Output:

- changed variables;
- setup status transitions;
- level changes;
- next inspection order;
- questions for missing user inputs.

### Intraday Trigger Monitor

Purpose:

- inspect active/approaching setups;
- classify `triggered`, `invalidated`, or `needs_review`;
- require execution check for `triggered` setups.

Output:

- priority ordered setup list;
- no buy/sell instruction;
- `execution_check_required` when triggered;
- explicit risk or data gaps.

### Post-Market Review Prompt

Purpose:

- summarize setup status changes;
- identify trades needing post-order or post-exit review;
- prepare the next day's update queue.

Output:

- what changed;
- what needs review;
- unresolved broker/trade facts;
- proposed update note.

### Position Daily Report

Purpose:

- read current positions and account-risk fields from authorized broker sources;
- summarize portfolio exposure, concentration, cash/margin pressure, PnL drivers, option/leveraged-product risk, and notable changes;
- connect current holdings to the Active Market Plan and list only decision-useful attention items.

Preferred source order:

1. Longbridge skill/plugin when installed and authorized by the user.
2. IBKR connector when installed and authorized by the user.
3. Manual user export for a single run.
4. Run without broker facts and report the gap.

Output:

- concise Chinese Markdown;
- source and read-time disclosure;
- broker/account coverage and missing fields;
- top exposures by symbol, theme, instrument type, sector when available, and currency when relevant;
- key changes versus the prior saved report snapshot when available;
- risk flags such as concentration, margin, cash drag, 2x/3x path risk, option expiry, correlated technology beta, or event risk;
- visual artifact requests or links when charts are generated;
- user decisions needed today.

Do not:

- place, modify, cancel, or imply approval of orders;
- save full raw broker exports by default;
- publish private account details to public repo files;
- require Google Sheets or local trade-record tables.

## Scheduling Guidance

Use schedules only after the user confirms cadence and timezone.

Recommended defaults for a US-market workflow:

- deep update: weekend morning or Sunday evening;
- quick update: weekday premarket;
- intraday trigger monitor: market-hours interval only when active setups exist;
- post-market review: after US market close;
- position daily report: after US market close or the user's local morning, using the user's confirmed timezone;
- development brief: local weekday morning;
- development progress review: local weekday evening.

Use the user's configured locale/timezone when creating Codex automations.

## Output Rules

Automation output should be concise Chinese note-style Markdown.

Include:

- automation purpose;
- data sources checked;
- missing data;
- proposed changes;
- questions for the user;
- next step.

Do not:

- place or suggest guaranteed orders;
- mutate broker state;
- silently overwrite `market-plan.md`;
- invent broker facts;
- publish private trade/account data to public docs.
