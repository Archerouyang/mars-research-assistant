# Intraday Setup Scan Expected Output

Synthetic expected output for the Active Market Plan fixture. This is not a buy/sell instruction.

## 结论

- QQQ 0DTE is `triggered`: execution_check_required and human decision needed.
- CRDO is `approaching`: thesis verification and 4H/1H price structure still
  required.
- SOXX is `needs_review`: sector confirmation and portfolio exposure are not
  resolved.
- GLW is `invalidated`: failed to reclaim before setup promotion.

## Setup 状态

| setup_id | 状态 | 为什么 | 下一步 |
| --- | --- | --- | --- |
| qqq-0dte-breakout-pullback | triggered | 5m trigger appeared inside active plan | execution_check_required; confirm follow-through and VIX |
| crdo-ai-infra-pullback | approaching | near trigger zone but Company Thesis Check incomplete | verify thesis then inspect 4H/1H |
| soxx-sector-confirmation | needs_review | sector ETF confirmation and portfolio risk incomplete | review SOXX/SPY and position daily report |
| glw-optical-reversal | invalidated | failed reclaim and incomplete catalyst evidence | archive or create a new setup later |

## 风险/失效

- QQQ 0DTE: time decay and range-middle risk.
- CRDO: KVN alone cannot create setup.
- SOXX: semiconductor exposure overlaps with current holdings.
- GLW: invalidated setups should not be resurrected automatically.
