# Trading Research System Plugin

This plugin packages a trading research workflow for Codex.

It is designed for research, screening, risk review, and decision support. It does not provide guaranteed returns, personalized financial advice, or trading instructions that ignore user constraints.

## Capabilities

- Macro and policy filtering focused on market-moving variables.
- Trump policy, Treasury policy, rates, yields, and liquidity monitoring.
- Equity screening with thesis verification against primary sources.
- Seeking Alpha and similar research-note synthesis when accessible or provided by the user.
- High-level Al Brooks price action timing framework.
- Weekly trading plan construction and daily market tracking.
- Plan-scoped intraday setup scanning for prepared trade plans.
- Interactive post-order and post-exit actual-trade review intake and trade statistics.
- Portfolio risk exposure checks.
- Local daily trading records with CSV and Markdown templates.
- Daily folder initialization, portfolio exposure, watchlist ranking, and trade statistics scripts.

## Skill

Invoke the bundled skill with:

```text
$trading-research
```

Example prompts:

```text
$trading-research Analyze NVDA using my workflow: macro, research-note validation, price action, and portfolio risk.
```

```text
$trading-research Screen US stocks that benefit from lower long-end yields. My current holdings are...
```

## Data Boundaries

For current policy, market prices, rates, yields, financial statements, or news, Codex must verify against current sources. Paywalled sources such as Seeking Alpha can only be analyzed from publicly accessible content or user-provided excerpts.

## Capability Boundaries

This plugin does not:

- place trades or automate order execution;
- generate guaranteed buy/sell instructions;
- scan the entire market for unplanned intraday trades outside the weekly plan, watchlist, or prepared plans in the initial scope;
- use Google Sheets as the canonical source of truth;
- provide tax, legal, or regulated investment advice.

## Local Records

Use local daily folders as the first source of truth:

```text
data/daily/YYYY-MM-DD/
```

The plugin includes templates for weekly plans, daily market tracking, holdings, watchlists, trade plans, actual trades, reviews, research-note logs, and macro checklists.

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
