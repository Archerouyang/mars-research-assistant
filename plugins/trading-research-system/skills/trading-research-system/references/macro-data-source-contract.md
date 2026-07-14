# Macro Data Source Contract

Use this reference before Daily Ops quick updates, weekly/deep Active Market
Plan updates, and macro-equity research whenever macro regime, financial
conditions, rates, liquidity, or strategy posture affect the output.

## Source Roles

Longbridge macrodata is the preferred S1 source for macro values when the
Longbridge skill/plugin is installed and authorized. Use it for actual macro and
financial-condition values such as rates, yields, inflation, labor, liquidity,
credit, FX, commodities, and broad financial conditions.

IBKR market data is price and OHLCV transmission. Use it for live prices,
historical OHLCV, charts, sector/index tape, VIX/ETF confirmation when
available, and broker/account facts when authorized. Do not use IBKR market data
as a replacement for broad macrodata or official policy facts.

official source fallback means S0 official / primary sources such as Federal
Reserve, Treasury, BLS, BEA, FRED, TreasuryDirect, exchange calendars, company
IR, and SEC filings. Use official sources to confirm policy facts, release
status, economic data publication, official speech text, and legal/regulatory
facts. Use them as fallback macro values only when Longbridge macrodata is
unavailable or when primary confirmation matters.

News and research sources are leads, not macro-data sources. They can explain
why a move matters, but they cannot replace actual macro values.

## Macro Data Source Health

Before claiming macro analysis, show `宏观数据来源状态`:

| source | status | used_for | fallback |
| --- | --- | --- | --- |
| Longbridge macrodata | available / unauthorized / not_installed / missing / stale | preferred S1 macro values | official source fallback |
| IBKR market data | available / unauthorized / not_installed / missing / stale | price and OHLCV transmission | public/authorized market data |
| official source fallback | available / pending / unavailable | S0 facts and fallback macro values | reputable media leads only |

If Longbridge macrodata is `available`, use it before web search for macro and
financial-condition values. If it is not available, state the reason and use
official source fallback or clearly mark the run as degraded.

## Actual Macro Reads

Macro/rates output must include `实际宏观指标读数` when macro is part of the
decision. Do not claim macro analysis if no actual macro values were read.

Minimum table:

| 指标 | 当前值 | 近5日/20日变化 | 阈值 | 对策略姿态影响 | 数据时间戳 | source |
| --- | --- | --- | --- | --- | --- | --- |
| 10Y |  |  | 4.5% | high beta momentum / balanced / defensive |  | Longbridge macrodata / official source fallback |
| 30Y |  |  | 5.0% | duration pressure / relief |  |  |
| HYG/LQD |  |  | widening / tightening | credit risk appetite |  |  |
| DXY |  |  | breakout / breakdown | USD liquidity and earnings pressure |  |  |
| Oil |  |  | spike / breakdown | inflation and volatility pressure |  |  |
| Gold |  |  | trend confirmation | optional defensive / easing hedge confirmation |  |  |

Add or remove rows only when useful. For the user's current framework, the key
answer is whether financial conditions support `high beta momentum`, require a
`balanced` posture, or argue for `defensive` risk posture.

For the standard panel, `10Y`, `30Y`, `HYG/LQD`, `DXY`, `Oil`, and
`liquidity` are required posture inputs. `Gold` is an optional confirmation
input: disclose it when missing, but do not mark the whole panel degraded when
Gold is the only absent indicator.

When Longbridge macrodata values are available as saved or tool-returned JSON,
normalize them into the standard runtime view:

```bash
python3 scripts/prepare_macro_panel.py \
  --date YYYY-MM-DD \
  --macrodata-json /path/to/longbridge-macrodata.json \
  --as-of YYYY-MM-DDTHH:MM:SSZ
```

When using official fallback JSON instead of Longbridge macrodata, call the same
script with `--source-capability official_source_fallback`. The panel must
preserve the provided item-level `source` when present.

`prepare_macro_panel.py` wraps `longbridge_macrodata_adapter.py` for the private
runtime path and reports `No live macrodata reads`; it does not invent values
when `--macrodata-json` is missing.

The standard `macro-panel.json` preserves `value`, `change_5d`, `change_20d`,
`threshold`, `source`, `timestamp`, `strategy_posture`, and
`missing_indicators`, plus `missing_required_indicators` and
`missing_optional_indicators`. It is a macro values panel, not a policy/news
source and not a broker account source.

## Strategy Posture Link

Translate macro reads into `策略姿态`:

- `high beta momentum`: yields stable/down, credit healthy, USD not tightening,
  volatility contained, and breadth/sector tape supports risk-on.
- `balanced`: mixed macro reads, event risk pending, or leadership narrow.
- `defensive`: yields or USD tighten, credit weakens, oil shock or volatility
  rises, or policy/event risk blocks new beta.

Do not let strategy posture become a generic preference statement. It must cite
which actual macro values support, pressure, or block the posture.

## Degraded Runs

If Longbridge macrodata, official source fallback, and market transmission data
are all unavailable, say:

```text
宏观数据读取不足：本轮不能声称完成宏观/金融条件分析，只能列出待抓取指标和降级原因。
```

Continue with plan or price-action work only if useful, but mark macro
confidence as low.
