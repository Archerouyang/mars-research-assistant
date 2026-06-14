# Trading Research System Plugin

This plugin packages a trading research workflow for Codex.

It is designed for research, screening, risk review, and decision support. It does not provide guaranteed returns, personalized financial advice, or trading instructions that ignore user constraints.

## Capabilities

- Macro and policy filtering focused on market-moving variables.
- Trump policy, Treasury policy, rates, yields, and liquidity monitoring.
- Equity screening with thesis verification against primary sources.
- Seeking Alpha and similar research-note synthesis when accessible or provided by the user.
- High-level Al Brooks price action timing framework.
- Active Market Plan maintenance with an overwriteable current state and append-only update trail.
- Trading profile template for personal style, instrument preference, and setup-to-instrument translation.
- Automation-ready deep update, quick update, intraday monitor, and post-market review workflows.
- Deep updates for weekend/weekly review, including prior trades, future events, momentum, and setup discovery.
- Quick updates for weekday premarket and intraday level/status changes.
- Setup-scoped intraday scanning for prepared setup plans.
- Interactive post-order and post-exit actual-trade review intake from read-only broker facts and user context.
- Broker-agnostic portfolio risk exposure checks.
- Canonical broker data templates for read-only IBKR, Longbridge, or manual CSV sources.
- Local daily trading records with CSV and Markdown templates.
- Daily folder initialization, portfolio exposure, watchlist ranking, and trade statistics scripts.

## Skill

Invoke the router skill with:

```text
$trading-research
```

For more specific workflows, use the smaller skills directly:

- `$weekly-trading-plan`: deep-update the Active Market Plan with prior trade review, market/macro/policy/news analysis, event preview, momentum update, and setup discovery.
- `$daily-market-tracking`: quick-update the Active Market Plan with market/macro/policy/news changes, setup status changes, and level updates.
- `$intraday-setup-scan`: plan-scoped intraday setup status.
- `$trade-review`: post-order and post-exit actual trade review using broker facts when available.
- `$macro-equity-research`: macro/rates, research validation, and screening.
- `$portfolio-risk`: exposure and sizing review.
- `$trading-stats`: win rate, R-multiple, setup performance, and system review.

Example prompts:

```text
$weekly-trading-plan Deep-update my Active Market Plan for next week.
```

```text
$daily-market-tracking Quick-update today's market plan and setup levels.
```

```text
$macro-equity-research Screen US stocks that benefit from lower long-end yields. My current holdings are...
```

```text
$trade-review Review my latest broker execution interactively.
```

## Data Boundaries

For current policy, market prices, rates, yields, financial statements, or news, Codex must verify against current sources. Paywalled sources such as Seeking Alpha can only be analyzed from publicly accessible content or user-provided excerpts.

## Capability Boundaries

This plugin does not:

- place trades or automate order execution;
- modify or cancel broker orders;
- generate guaranteed buy/sell instructions;
- scan the entire market for unplanned intraday trades outside the Active Market Plan, watchlist, or prepared setups in the initial scope;
- use Google Sheets as the canonical source of truth;
- provide tax, legal, or regulated investment advice.

## Local Records

Use local daily folders as the first source of truth:

```text
data/market-plan.md
data/trading-profile.md
data/updates/YYYY-MM-DD.md
data/daily/YYYY-MM-DD/
```

The plugin includes templates for Active Market Plans, update notes, holdings, canonical broker snapshots, watchlists, trade plans, actual trades, reviews, research-note logs, and macro checklists.

Use `data/trading-profile.md` for private trading style and instrument preferences. The public repo only ships a blank template and does not store personal account allocation.

Broker adapters are read-only sources. IBKR, Longbridge, and manual CSV should map positions, executions, and order status into canonical local files before core risk or review workflows consume them.

Codex automations can be used to schedule prompts around the Active Market Plan loop, but they should ask before editing local records and must not touch broker write actions.

Google Sheets sync is planned as a later mirror/review layer.

## Project Plan

In the source repository, `docs/ROADMAP.md` is the public planning document for capability boundaries, execution method, task breakdown, and progress tracking.

Use `docs/PROJECT_LOG.md` for the public GitHub trajectory of milestone updates and important plugin changes.

## Scripts

```bash
python3 plugins/trading-research-system/scripts/init_daily.py --date 2026-06-12
python3 plugins/trading-research-system/scripts/portfolio_risk.py data/daily/2026-06-12/portfolio.csv
python3 plugins/trading-research-system/scripts/watchlist_score.py data/daily/2026-06-12/watchlist.csv
python3 plugins/trading-research-system/scripts/trade_stats.py data/daily/2026-06-12/trades.csv --group-by instrument_type
python3 plugins/trading-research-system/scripts/append_review.py --date 2026-06-12 --trade-id 20260612-QQQ-001 --symbol QQQ --review-file /path/to/review.md
```
