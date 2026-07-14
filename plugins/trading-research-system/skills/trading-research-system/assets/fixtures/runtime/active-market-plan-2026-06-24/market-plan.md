# Active Market Plan Fixture

Synthetic fixture for plugin tests and demos. This is decision support only and
not a live trading plan.

## State

- As of: 2026-06-24
- Last update depth: deep_update
- Market regime: balanced high-beta watch with rates-sensitive confirmation
- Primary themes: AI infrastructure, semiconductor breadth, QQQ risk-on
- Risk budget: fixture only; no broker write action
- Broker data source used: broker-live fixture
- Trading profile used: synthetic profile fixture
- Open questions: rates confirmation, thesis verification, price structure

## Trade Plan Preparation

### Input Reads

| Module | Read | Supports | Pressures | Blocks | Evidence | Next check |
| --- | --- | --- | --- | --- | --- | --- |
| Macro Regime | risk-on but rates-sensitive | high-beta momentum can stay on watch | hot yields pressure growth multiple | wait if 10Y spikes | macro fixture | re-check rates |
| Financial Conditions | balanced | semis and AI hardware stay in candidate pool | VIX or credit stress reduces risk | block fresh risk if stress confirms | financial fixture | HYG/LQD and VIX |
| Policy/Event Risk | no immediate P0 block | KVN names can be researched | event gap risk can delay setup | unresolved event risk blocks promotion | event fixture | event table refresh |
| Industry/Sector Strength | AI hardware and optical themes lead | CRDO / GLW / ARM / BE deserve research | weak SOXX would pressure single names | failed sector breadth blocks promotion | sector fixture | SOXX/SPY and NDX/RUT |
| Company Thesis Check | thesis incomplete | CRDO and GLW move to verification queue | valuation and catalyst gaps | no setup without thesis check | report fixture | verify company claims |
| KVN Momentum Leaderboard | imported snapshot 2026-06-24 | CRDO continuation; GLW new Top10; SNDK rank 1 | SOXX not Top10 so use as sector confirmation | KVN alone cannot create setup | kvn_leaderboard.py show/query/changes | latest Top10 and ticker lookup |

### Cross-Section Candidate Pool

| Rank | Symbol/theme | Drivers | Supported by | Pressured by | Blocked by | Price structure / risk context | Setup readiness | Next check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | CRDO / AI infrastructure | KVN Top10 continuation and AI hardware strength | KVN Momentum Leaderboard; Industry/Sector Strength | valuation and event risk | Company Thesis Check incomplete | 4H/1D/1W uptrend required; semiconductor exposure check | candidate setup only after thesis and price structure confirmation | inspect 4H pullback/reclaim |
| 2 | GLW / optical infrastructure | new Top10 entry and theme expansion | KVN Top10 changes; sector rotation | lower direct AI beta than leaders | needs catalyst evidence | needs 4H trend and portfolio fit | cross-section only | verify catalyst |
| 3 | SOXX / semiconductor sector confirmation | sector ETF confirms or rejects breadth | Financial Conditions; sector ETF read | rates spike or SOXX/SPY weakness | no single-name setup from sector confirmation | background confirmation only | watchlist support | monitor SOXX/SPY |

## Event Preview

| Date | Event | Why it matters | Bullish if | Bearish if | Setups affected |
| --- | --- | --- | --- | --- | --- |
| 2026-06-24 | Synthetic rates check | confirms whether high-beta risk can stay active | 10Y stable and VIX contained | yields spike and VIX expands | crdo-ai-infra-pullback; qqq-0dte-breakout-pullback |

## Setup Pool

| setup_id | theme_id | Symbol | Direction | Instrument | Background filter TF | Background condition | Execution trigger TF | Execution trigger | Setup | Status | Trigger zone | Invalidation | Target zone | Risk budget | Next check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| crdo-ai-infra-pullback | ai-infra-momentum | CRDO | long | stock_common | 4H/1D/1W | uptrend or reclaim required | 1H/15m | pullback hold and signal bar | breakout_pullback | candidate | 118-122 | failed reclaim below 112 | 132 then 145 | fixture 1R | thesis verification then 4H check |
| qqq-0dte-breakout-pullback | qqq-risk-on | QQQ 0DTE call | long | qqq_0dte_call | 1H/15m | above 20/50 EMA and VIX contained | 5m | breakout pullback with follow-through | breakout_pullback | active | 724-726 | back into range below 718 | intraday extension | fixture 0.5R | execution_check_required if triggered |
| soxx-sector-confirmation | semiconductor-confirmation | SOXX | long | sector_etf | 1D/4H | sector breadth confirms | 1H | reclaim prior high | sector_confirmation | needs_review | 258-262 | failed reclaim below 250 | 272 | fixture only | compare SOXX/SPY |

## Broker-Live Fixture

- Source: broker-live fixture
- Position daily report: daily/2026-06-24/position-daily-report.md
- Objective broker facts: daily/2026-06-24/portfolio_snapshot.csv
- No broker write actions are allowed.

## Portfolio Exposure

- Tech beta: elevated but within fixture limit.
- Semiconductor: active watch because QQQ / SOXX / CRDO overlap.
- Short-dated option risk: QQQ 0DTE requires execution_check_required.

## Next Update Queue

1. Confirm rates and VIX.
2. Verify CRDO and GLW thesis.
3. Refresh QQQ 5m/15m trigger only if setup is still active.
4. Use position daily report before adding semiconductor exposure.
