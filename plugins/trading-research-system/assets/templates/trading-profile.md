# Trading Profile

Blank user-owned template; plugin install provides no ticker, strategy, account,
or risk defaults.

## Purpose

- Primary trading objective:
- Preferred holding periods:
- Instruments generally allowed:
- Instruments generally avoided:
- Max portfolio heat:
- Max single-setup risk:
- Notes:

## Strategy Posture Scoring

| Score | Enabled | Inputs | Weights | Thresholds | Notes |
| --- | --- | --- | --- | --- | --- |
| Risk Budget Score | yes/no |  |  |  |  |
| Trend Fit Score | yes/no |  |  |  |  |
| Mean Reversion Fit Score | yes/no |  |  |  |  |

Manual override rules:

- Allow user override: yes/no
- Override must record:
- Hard risk stops:

## Active Trading Pools

| Pool | Role | Priority | Symbols/themes | Trend-mode behavior | Mean-reversion behavior | Avoid if |
| --- | --- | --- | --- | --- | --- | --- |
| Momentum pool | discovery / trading / confirmation |  |  |  |  |  |
| Large-cap liquidity leaders | trading / confirmation |  |  |  |  |  |
| Theme core pool | concentrated trading |  |  |  |  |  |
| Confirmation pool | confirmation only / trading allowed |  |  |  |  |  |

Multi-pool symbol rules:

- Symbols allowed in multiple pools: yes/no
- Tool selection is determined by:
- If multiple expressions are valid:
- User decision required when:

Promotion / demotion rules:

- Momentum Additions can become Watch when:
- Watch can be suggested for Core review when:
- Watch can become Core only after explicit user confirmation: yes/no
- Core can be demoted when:
- Dormant can be restored when:

## Long-Term ETF Portfolio

| ETF group | Role | Symbols | Add rules | TP/rebalance rules | Pause/review rules |
| --- | --- | --- | --- | --- | --- |
| Core beta | long-term core |  |  |  |  |
| Theme ETF | long-term theme |  |  |  |  |
| Defensive rebalance | risk-off rebalance |  |  |  |  |
| Macro allocation | macro setup |  |  |  |  |

## Crowding Model

| Scope | Enabled | Data sources | Inputs | Weighting | Action when crowded |
| --- | --- | --- | --- | --- | --- |
| Theme / sector | yes/no |  |  |  |  |
| Ticker | yes/no |  |  |  |  |

Crowding examples to track:

- Weighting data:
- Flow-driven factors:
- Institution / hedge-fund net exposure:
- Index weight / return contribution:
- Options crowding:

## Instrument Preference Rules

### ETF-Only Expression

- Use when:
- Preferred instruments:
- Avoid when:
- Typical analysis timeframe:
- Typical trigger timeframe:
- Notes:

### Momentum / Elasticity Stocks

- Use when:
- Preferred instruments:
- Add-on instruments:
- Avoid when:
- Typical analysis timeframe:
- Typical trigger timeframe:
- Notes:

### User-Defined Single-Stock Expression

User examples:

-

Rules:

- Consider common stock when:
- Consider 2x ETF expression when:
- Consider LEAP call add-on when:
- Avoid LEAP when:
- Typical analysis timeframe:
- Typical trigger timeframe:
- Notes:

## Setup Translation Rules

| Setup type | Market context | Preferred expression | Backup expression | Analysis timeframe | Trigger timeframe | Avoid if |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## Instrument Strictness

| Instrument type | Trigger strictness | Minimum signal quality | Time stop | Risk notes |
| --- | --- | --- | --- | --- |
| ETF |  |  |  |  |
| 2x ETF |  |  |  |  |
| Common stock |  |  |  |  |
| LEAP call |  |  |  |  |
| Same-day-expiry option (optional) |  |  |  |  |

## Personal Avoid Rules

- Do not trade:
- Reduce size when:
- Require manual review when:
- Do not add to losing setup when:
- Do not chase when:

## Review Tags To Track

- Common mistakes:
- Setup tags to separate:
- Instrument tags to separate:
- Confidence calibration notes:
