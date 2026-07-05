# 持仓日报 - 2026-06-24

Source: broker-live fixture
Read time: 2026-06-24T20:00:00Z
Coverage: synthetic IBKR and Longbridge positions
Data status: fixture
Snapshot saved: fixture

## 结论

- 科技 beta and 半导体 exposure are both active.
- New CRDO risk should stay small until thesis and price structure confirm.
- QQQ 0DTE is execution_check_required only; it is not an order instruction.

## 需要用户决策

| 优先级 | 持仓/主题 | 问题 | 可选动作 | 需要确认 |
| --- | --- | --- | --- | --- |
| P0 | QQQ 0DTE | triggered status requires human decision | skip / execute manually / wait for second entry | 5m follow-through and VIX |
| P1 | 半导体 | SOXX plus CRDO raises correlated exposure | keep candidate small / wait / reduce other risk | SOXX/SPY and rates |
| P2 | CRDO | thesis not verified | research first | report and company facts |

## 风险变化

| 风险 | 当前状态 | 变化 | 影响 | 需要观察 |
| --- | --- | --- | --- | --- |
| 集中度 | tech_beta elevated | QQQ plus SOXX overlap | limits additional high-beta risk | NDX/RUT and SOXX/SPY |
| 半导体 | active | SOXX and CRDO overlap | position sizing should stay controlled | breadth confirmation |
| 0DTE | triggered fixture | time decay and execution risk | no averaging down | follow-through |

## 持仓影响

| 持仓 | 定位 | 当前影响 | Active Market Plan 动作 | 备注 |
| --- | --- | --- | --- | --- |
| QQQ | core ETF plus daytrade context | risk-on watch | continue holding core; 0DTE separate | fixture only |
| SOXX | semiconductor exposure | confirms or rejects sector breadth | needs_review before add | compare SOXX/SPY |
| CRDO | momentum candidate | small synthetic position | thesis verification required | KVN support only |

## 可视化

- Allocation by symbol: QQQ largest, SOXX second, CRDO smaller.
- Theme / sector exposure: tech_beta and semiconductor dominate.
- PnL contribution: QQQ and SOXX positive in fixture.
- Risk heatmap: high-beta concentration needs review.

## 数据缺口

- No live broker authorization.
- No real-time options chain.
- No current OHLCV in fixture.
