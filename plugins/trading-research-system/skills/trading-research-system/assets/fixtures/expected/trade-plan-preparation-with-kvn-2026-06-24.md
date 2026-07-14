# Trade Plan Preparation With KVN Fixture

## 交易计划准备

This fixture shows how an imported KVN snapshot feeds Trade Plan Preparation.
KVN Momentum Leaderboard 是研究优先级输入，不是买入名单，也不是 Setup Pool。

### Input Reads

| Module | read | supports | pressures | blocks | evidence | next_check |
| --- | --- | --- | --- | --- | --- | --- |
| Macro Regime | risk-on but rates-sensitive | high-beta momentum can stay on watch | hot yields would pressure growth multiple | wait if 10Y spikes or USD tightens | current macro read placeholder | re-check rates and liquidity before promotion |
| Financial Conditions | balanced, not fully loose | semis and AI hardware can remain in candidate research | VIX or credit stress would reduce new risk | block fresh risk if VIX/rates confirm stress | market data placeholder | confirm HYG/LQD, 10Y, VIX |
| Policy/Event Risk | no immediate P0 block in fixture | imported KVN names can be researched | event gap risk can delay setup | block before earnings/FOMC if unresolved | event calendar placeholder | refresh event table |
| Industry/Sector Strength | AI hardware, memory, optical, and power themes lead | SNDK / CRDO / LITE / GLW / ARM / BE deserve research priority | broad market divergence would pressure smaller names | weak SOXX/SMH relative strength blocks promotion | sector RS placeholder | compare SOXX/SPY and NDX/RUT |
| Company Thesis Check | thesis not yet verified | CRDO, GLW, ARM, BE move to thesis queue | SNDK needs catalyst and valuation check | any unverified thesis remains cross-section only | report intake placeholder | verify company claims before setup |
| KVN Momentum Leaderboard | imported snapshot 2026-06-24 | SNDK rank 1, CRDO rank 3, LITE rank 5; Top10 memory supports repeated strength | SOXX query is not current Top10, so use it as sector confirmation rather than single-name priority | KVN alone cannot create a trade setup | kvn_leaderboard.py show/query/changes | run latest Top10, changes, and ticker lookup |

### Cross-Section Candidate Pool / 截面候选池

| rank | symbol/theme | drivers | supported_by | pressured_by | blocked_by | price_structure / risk_context | setup_readiness | next_check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | CRDO / AI infrastructure | KVN Top10 continuation, AI hardware theme strength | KVN Momentum Leaderboard, Industry/Sector Strength | high valuation and event gap risk | Company Thesis Check incomplete | 4H/1D/1W uptrend required; portfolio risk if semiconductor beta already crowded | can become `candidate setup` only after thesis verification and price structure confirmation | verify thesis, then inspect 4H pullback/reclaim |
| 2 | GLW / optical infrastructure | new Top10 entry and theme expansion | KVN Top10 change, sector rotation | lower direct AI beta than leaders | needs company-specific catalyst | 4H/1D/1W trend must confirm; risk_context should compare with existing tech beta | stays cross-section candidate until price structure appears | check relative strength and catalyst evidence |
| 3 | SOXX / semiconductor sector confirmation | queried ticker outside current Top10 but useful as sector ETF read | Financial Conditions and sector ETF breadth | rate spike or SMH/SOXX weakness | not a single-name setup | use SOXX/SPY for background; no direct candidate setup from this row | sector confirmation only | monitor SOXX vs SPY and SMH breadth |

### Promotion Rule

Only promote a KVN-driven candidate into `candidate setup` when these are present:

- `4H/1D/1W` higher-timeframe regime and allowed strategy bias;
- setup type and price structure;
- trigger zone and invalidation;
- `price_structure / risk_context` including portfolio risk and event risk;
- next check on 1H or lower execution timeframe.

KVN snapshot names without thesis verification or price structure stay in the
Cross-Section Candidate Pool.
