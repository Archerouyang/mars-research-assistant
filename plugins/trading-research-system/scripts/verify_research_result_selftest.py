#!/usr/bin/env python3
"""Focused self-test for the ResearchResult delivery seam."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

from research_result import ResearchResultError, build_delivery_packet
from longbridge_cli_adapter import portfolio_rows
from portfolio_fundamentals_adapter import (
    _implied_volatility_metrics,
    _option_positioning_metrics,
    _realized_volatility_metrics,
    _short_interest_metrics,
    _short_trade_metrics,
    _statement_metrics,
)
from portfolio_panel_adapter import build_portfolio_panel


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "assets" / "fixtures" / "input"
AS_OF = "2026-07-17T10:00:00Z"


def result(kind: str, visual: dict[str, object] | None) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "result_kind": kind,
        "as_of": AS_OF,
        "decision": "Maintain the current evidence gate until the next confirmation.",
        "key_evidence": [
            {
                "label": "Current read",
                "value": "Mixed but decision-useful",
                "evidence_type": "fact",
                "status": "complete",
                "as_of": AS_OF,
                "source_refs": ["fixture"],
            }
        ],
        "risks": [
            {
                "label": "Transmission risk",
                "severity": "medium",
                "detail": "The next event can change the current read.",
                "invalidation": "Cross-asset confirmation reverses.",
            }
        ],
        "scenarios": [
            {
                "name": "Confirmation",
                "condition": "the required evidence aligns",
                "implication": "reassess the current gate",
            }
        ],
        "next_checks": ["Refresh the decision-sensitive source."],
        "data_gaps": [],
        "sources": [{"id": "fixture", "label": "Synthetic fixture", "priority": "S1", "as_of": AS_OF}],
        "privacy": "public_fixture",
        "locale": "zh-CN",
        "visual": visual,
    }


def load(name: str) -> dict[str, object]:
    return json.loads((INPUT / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    statement = _statement_metrics(
        {
            "list": [
                {
                    "report_txt": "Q2 2026",
                    "rpt_date": "2026-07-15",
                    "fp_end": "2026-06-30",
                    "fields": [
                        {"field": "total_rev", "value": "100", "yoy": "0.20"},
                        {"field": "gp", "value": "60", "yoy": "0.25"},
                        {"field": "ni_company", "value": "25", "yoy": "0.30"},
                    ],
                }
            ]
        }
    )
    require(statement["gross_margin_pct"] == 60.0, "gross margin derivation failed")
    require(statement["report"] == "Q2 2026", "latest statement period missing")
    short_interest = _short_interest_metrics(
        {"data": [{"timestamp": "1782792000", "rate": "0.028", "days_to_cover": "0.53"}]},
        "2026-07-17T10:00:00Z",
    )
    require(abs(float(short_interest["short_interest_pct"] or 0) - 2.8) < 1e-9, "short-interest ratio derivation failed")
    iv30 = _implied_volatility_metrics(
        {"timestamp": "2026-07-17 03:44:42", "data": {"iv30": 52.81}},
        "2026-07-17T10:00:00Z",
    )
    require(iv30["iv30_pct"] == 52.81, "IV30 freshness gate failed")
    short_trade = _short_trade_metrics(
        {"data": [{"timestamp": "1784174400", "rate": "0.30"}, {"timestamp": "1784260800", "rate": "0.40"}]}
    )
    require(short_trade["short_volume_pct"] == 40.0, "daily short-volume ratio derivation failed")
    option_positioning = _option_positioning_metrics(
        {"stats": [{"timestamp": "1784260800", "put_call_volume_ratio": "1.25", "put_call_open_interest_ratio": "1.10"}]}
    )
    require(option_positioning["put_call_volume_ratio"] == 1.25, "Put/Call positioning derivation failed")
    volatility = _realized_volatility_metrics(
        [{"close": str(100 + index)} for index in range(24)],
        45.0,
    )
    require(volatility["hv20_pct"] is not None and volatility["implied_move_30d_pct"] is not None, "volatility context derivation failed")

    macro = result(
        "macro",
        {"adapter": "macro", "snapshot": load("macro-regime-complete.json"), "default_view": "Overview"},
    )
    first = build_delivery_packet(macro)
    second = build_delivery_packet(copy.deepcopy(macro))
    require(first == second, "same result must produce identical delivery bytes")
    require(b"## \xe7\xbb\x93\xe8\xae\xba" in first.markdown, "stable conclusion section missing")
    require(
        "证据 2026-07-17T10:00:00Z".encode() in first.markdown
        and b"Synthetic fixture @ 2026-07-17T10:00:00Z" in first.markdown,
        "evidence provenance missing",
    )
    require(first.inline_html is not None and b'data-view="trend"' in first.inline_html, "macro trend view missing")
    require(b'data-view="current"' in first.inline_html, "macro current-state view missing")
    require(b'data-view="events"' in first.inline_html, "macro event-watch view missing")
    require(b"trend-chart" in first.inline_html, "macro trend chart missing")
    require(b'class="bar-track"' not in first.inline_html, "macro raw-value bar chart must not be used")
    require(b'class="macro-summary"' in first.inline_html, "macro summary strip missing")
    require(b'class="scenario-flow"' in first.inline_html, "macro scenario flow missing")
    require("情景（按冲击排序）".encode() in first.inline_html, "macro scenario comparison header missing")
    require(b'class="scenario-card"' not in first.inline_html, "macro scenario cards must not be used")
    require("演示数据，不可用于交易".encode() in first.inline_html, "public fixture is not visibly disclosed")
    require("已验证".encode() in first.inline_html, "macro transmission status is not localized")
    require(b'class="liquidity-note"' in first.inline_html, "macro liquidity background missing")
    require("MAGS".encode() in first.inline_html and "小盘股".encode() in first.inline_html, "macro asset preference coverage missing")
    require(b'class="event-row event-high"' in first.inline_html, "high-impact event emphasis missing")
    for label in ("2Y", "10Y", "30Y", "CPI", "PPI", "NDX/RUT", "VXN"):
        require(label.encode() in first.inline_html, f"macro required observation missing: {label}")
    require("下周事件".encode() in first.inline_html, "macro next-week linkage missing")
    require("高利率下的指数分化".encode() in first.inline_html, "macro base scenario missing")
    require(first.inline_html.lstrip().startswith(b'<div id="dailytrades-macro-inline-'), "inline output is not a native fragment")
    require(b'data-public-fixture="true"' in first.inline_html, "public fixture marker missing")
    require(b"<iframe" not in first.inline_html.lower(), "inline output must not wrap a standalone board")
    require(b"<html" not in first.inline_html.lower(), "standalone html leaked into inline output")
    require(len(first.inline_html) < 100_000, "macro inline output is too large")
    macro_gap = result(
        "macro",
        {"adapter": "macro", "snapshot": load("macro-regime-partial.json"), "default_view": "Overview"},
    )
    macro_gap["key_evidence"][0]["status"] = "partial"
    macro_gap["data_gaps"] = [
        {"label": "Macro breadth", "reason": "Required series are incomplete.", "status": "partial"}
    ]
    macro_gap_packet = build_delivery_packet(macro_gap)
    require("## 数据缺口".encode() in macro_gap_packet.markdown, "macro gap is not visible in Markdown")
    require(macro_gap_packet.diagnostics == ("data_gap:partial:Macro breadth",), "safe diagnostics missing")
    require(
        macro_gap_packet.inline_html is not None
        and "证据 4/6".encode() in macro_gap_packet.inline_html
        and "待核验".encode() in macro_gap_packet.inline_html,
        "macro degraded state is hidden",
    )

    longbridge_rows = portfolio_rows(
        load("longbridge-portfolio-cli-2026-06-24.json"),
        as_of=AS_OF,
        account_id="Synthetic Longbridge",
        include_cash=True,
    )
    longbridge_rows = [row for row in longbridge_rows if row["currency"] == "USD"]
    portfolio_panel = build_portfolio_panel(
        longbridge_rows,
        as_of=AS_OF,
        reconciliation="reconciled",
        fundamentals={
            "source": "Longbridge CLI synthetic fixture",
            "as_of": AS_OF,
            "items": [
                {
                    "symbol": "TSM",
                    "display_name": "TSM",
                    "entity_type": "company",
                    "source_holdings": ["TSMX"],
                    "mapping_note": "2× 每日杠杆产品的单一公司底层",
                    "status": "available",
                    "metrics": {
                        "price": 190.0,
                        "current_pe": 28.0,
                        "forward_pe": 22.0,
                        "forward_eps": 8.64,
                        "eps_revision_30d_pct": 3.2,
                        "revenue_yoy_pct": 35.0,
                        "net_income_yoy_pct": 40.0,
                        "gross_margin_pct": 58.0,
                        "net_margin_pct": 45.0,
                        "roe_pct": 30.0,
                        "report": "2026.Q1",
                        "report_date": "2026-05-01",
                        "roe_report": "2026.Q1",
                        "short_interest_pct": 2.5,
                        "short_days_to_cover": 1.2,
                        "short_interest_as_of": "2026-06-30",
                        "short_interest_status": "available",
                        "iv30_pct": 45.0,
                        "iv30_as_of": "2026-07-17 20:00:00",
                        "iv30_status": "available",
                        "hv20_pct": 35.0,
                        "iv_hv_ratio": 1.29,
                        "iv_hv_spread_pct": 10.0,
                        "implied_move_30d_pct": 12.9,
                        "short_volume_pct": 40.0,
                        "short_volume_5d_avg_pct": 34.0,
                        "short_volume_as_of": "2026-07-17",
                        "short_volume_history": [
                            {"date": "2026-07-16", "value": 34.0},
                            {"date": "2026-07-17", "value": 40.0},
                        ],
                        "put_call_volume_ratio": 1.25,
                        "put_call_open_interest_ratio": 1.10,
                        "put_call_volume_20d_avg": 0.95,
                        "option_positioning_as_of": "2026-07-17",
                        "put_call_volume_history": [
                            {"date": "2026-07-16", "value": 0.9},
                            {"date": "2026-07-17", "value": 1.25},
                        ],
                        "margin_history": [
                            {"date": "2026-03-31", "gross_margin_pct": 55.0, "net_margin_pct": 42.0},
                            {"date": "2026-06-30", "gross_margin_pct": 58.0, "net_margin_pct": 45.0},
                        ],
                    },
                    "forward_pe_history": [
                        {"date": "2026-05-01", "value": 20.0},
                        {"date": "2026-06-01", "value": 22.0},
                    ],
                    "note": "Synthetic Forward P/E estimate.",
                }
            ],
        },
        privacy="public_fixture",
    )
    inverse_panel = build_portfolio_panel(
        [
            {
                "as_of": AS_OF,
                "broker": "Synthetic Broker",
                "symbol": "SQQQ",
                "underlying": "QQQ",
                "instrument_type": "leveraged_etf",
                "direction": "long",
                "quantity": "1",
                "market_value": "100",
                "currency": "USD",
                "delta_exposure": "100",
                "notional_exposure": "100",
                "theme_id": "tech_inverse_leverage",
            }
        ],
        as_of=AS_OF,
        reconciliation="reconciled",
        privacy="public_fixture",
    )
    inverse_totals = inverse_panel["payload"]["totals"]
    inverse_symbol = inverse_panel["payload"]["aggregations"]["by_symbol"][0]
    inverse_stress = next(
        row for row in inverse_panel["payload"]["stress_scenarios"] if row["family"] == "risk_off"
    )
    require(inverse_totals["gross_delta_exposure"] == 300.0, "inverse ETF gross delta is wrong")
    require(inverse_totals["net_delta_exposure"] == -300.0, "inverse ETF net delta lost its sign")
    require(inverse_symbol["delta_exposure"] == -300.0, "inverse ETF look-through direction was reversed")
    require(inverse_stress["estimated_impact"] == 30.0, "inverse ETF risk-off response has the wrong sign")
    inverse_packet = build_delivery_packet(
        result("portfolio", {"adapter": "portfolio", "panel": inverse_panel})
    )
    inverse_html = inverse_packet.inline_html or b""
    require(b"--risk-width:-" not in inverse_html, "inverse ETF produced a negative bar width")
    require(b"Net -$300" in inverse_html, "portfolio summary lost inverse net delta")
    require(
        b'<b class="stress-gain">+$30</b>' in inverse_html,
        "beneficial inverse stress response was rendered as a loss",
    )
    symbol_rows = portfolio_panel["payload"]["aggregations"]["by_symbol"]
    while len(symbol_rows) < 5:
        clone = dict(symbol_rows[-1])
        clone["label"] = f"Synthetic underlying {len(symbol_rows) + 1}"
        clone["affected_holdings"] = [clone["label"]]
        symbol_rows.append(clone)
    fifth_symbol = str(symbol_rows[4]["label"])
    portfolio = result("portfolio", {"adapter": "portfolio", "panel": portfolio_panel})
    require(
        any(
            row["label"] == "TSM" and "TSMX" in row["affected_holdings"]
            for row in portfolio_panel["payload"]["aggregations"]["by_symbol"]
        ),
        "leveraged product underlying mapping missing",
    )
    portfolio_packet = build_delivery_packet(portfolio)
    require(portfolio_packet.inline_html is not None and b'data-view="symbol"' in portfolio_packet.inline_html, "portfolio inline adapter missing")
    require(b"<iframe" not in portfolio_packet.inline_html.lower(), "portfolio inline output is not native")
    for anchor in (b"portfolio-summary", b"portfolio-overview", b"dimension-panel", b"fundamentals-panel", b"risk-ledger-row"):
        require(anchor in portfolio_packet.inline_html, f"portfolio prototype anchor missing: {anchor.decode()}")
    for expected in ("每日杠杆 ETF", "已对账 1/1", "用户排除 0", "历史 Forward P/E 估算", "基本面", "毛利率", "未平仓空头 / 流通股", "当日卖空成交占比", "P/C 成交量", "IV30", "HV20", "隐含30日区间"):
        require(expected.encode() in portfolio_packet.inline_html, f"portfolio requirement missing: {expected}")
    require(fifth_symbol.encode() in portfolio_packet.inline_html, "portfolio overview truncated the fifth underlying")
    require(b'data-fundamental-card="0"' in portfolio_packet.inline_html, "portfolio fundamentals must be pre-rendered")
    require(b'data-fundamental-view="positioning"' in portfolio_packet.inline_html, "portfolio positioning subview missing")
    require(b'data-fundamental-pane="volatility"' in portfolio_packet.inline_html, "portfolio volatility subview missing")
    require(b'class="stress-panel"' in portfolio_packet.inline_html, "portfolio stress must use a dedicated decision view")
    for expected in ("估算影响", "资本冲击", "计算假设", "不是价格预测"):
        require(expected.encode() in portfolio_packet.inline_html, f"portfolio stress meaning missing: {expected}")
    top_view_positions = [
        portfolio_packet.inline_html.find(f'data-view="{view}"'.encode())
        for view in ("overview", "symbol", "fundamentals", "theme", "product", "broker", "stress")
    ]
    require(all(position >= 0 for position in top_view_positions), "portfolio frozen top-level view missing")
    require(top_view_positions == sorted(top_view_positions), "portfolio frozen top-level view order changed")
    fundamental_view_positions = [
        portfolio_packet.inline_html.find(f'data-fundamental-view="{view}"'.encode())
        for view in ("valuation", "earnings", "positioning", "volatility")
    ]
    require(all(position >= 0 for position in fundamental_view_positions), "portfolio frozen fundamental view missing")
    require(fundamental_view_positions == sorted(fundamental_view_positions), "portfolio frozen fundamental view order changed")
    require(b'--dt-warning:' in portfolio_packet.inline_html, "portfolio component color fallbacks missing")
    require(b"drawFundamental" not in portfolio_packet.inline_html, "portfolio fundamentals leaked client-side rendering")
    portfolio_script = portfolio_packet.inline_html.split(b"<script>", 1)[1].split(b"</script>", 1)[0]
    require(len(portfolio_script) < 12_000, "portfolio client script exceeds the document.write-safe budget")

    instrument = result(
        "instrument",
        {"adapter": "instrument", "snapshot": load("instrument-research-complete.json"), "default_view": "Overview"},
    )
    instrument_packet = build_delivery_packet(instrument)
    require(instrument_packet.inline_html is not None and b'data-view="price"' in instrument_packet.inline_html, "instrument inline adapter missing")
    require(b"<iframe" not in instrument_packet.inline_html.lower(), "instrument inline output is not native")

    pa = result(
        "price_action",
        {"adapter": "price_action", "payload": load("chart-ohlcv-qqq-sample.json"), "title": "QQQ PA Scenario Board"},
    )
    pa_packet = build_delivery_packet(pa)
    require(pa_packet.inline_html is not None and b"pa-chart" in pa_packet.inline_html, "price action inline adapter missing")
    require(b"<iframe" not in pa_packet.inline_html.lower(), "price action inline output is not native")
    require("转强".encode() in pa_packet.inline_html and "分段建仓".encode() not in pa_packet.inline_html, "price action controls are not localized or optional plan leaked")
    require(len(pa_packet.inline_html) < 100_000, "price action inline output is too large")
    require(b"204.5" not in pa_packet.inline_html and b"197.5" not in pa_packet.inline_html, "prototype price leaked into PA")
    controls_at = pa_packet.inline_html.find(b'class="viz-controls"')
    scenario_copy_at = pa_packet.inline_html.find(b'class="scenario-detail')
    chart_at = pa_packet.inline_html.find(b'class="pa-chart"')
    require(0 <= controls_at < scenario_copy_at < chart_at, "frozen PA scenario hierarchy changed")
    for generic_copy in ("收复上方关键位。", "继续整理。", "复核失效。"):
        require(generic_copy.encode() not in pa_packet.inline_html, "generic PA scenario copy was invented")

    missing_pa_context = load("chart-ohlcv-qqq-sample.json")
    missing_pa_context.pop("ticker")
    try:
        build_delivery_packet(
            result(
                "price_action",
                {"adapter": "price_action", "payload": missing_pa_context, "title": "Invalid PA"},
            )
        )
    except ResearchResultError as error:
        require(str(error) == "ticker_invalid", "wrong missing PA context error code")
    else:
        raise AssertionError("price action without ticker was accepted")

    malformed_pa = load("chart-ohlcv-qqq-sample.json")
    malformed_pa["entry_plan"] = "bad"
    try:
        build_delivery_packet(
            result(
                "price_action",
                {"adapter": "price_action", "payload": malformed_pa, "title": "Malformed PA"},
            )
        )
    except ResearchResultError as error:
        require(str(error) == "visual_payload_invalid", "wrong malformed PA error code")
    else:
        raise AssertionError("malformed price action payload was accepted")

    malformed_atr = load("chart-ohlcv-qqq-sample.json")
    malformed_atr["atr14_primary"] = "bad"
    try:
        build_delivery_packet(
            result(
                "price_action",
                {"adapter": "price_action", "payload": malformed_atr, "title": "Malformed PA ATR"},
            )
        )
    except ResearchResultError as error:
        require(str(error) == "visual_payload_invalid", "wrong malformed ATR error code")
    else:
        raise AssertionError("malformed price action ATR was accepted")

    pa_alt_payload = load("chart-ohlcv-qqq-sample.json")
    pa_alt_payload.update({"primary_timeframe": "1H", "atr14_primary": 2.5})
    pa_alt = result(
        "price_action",
        {"adapter": "price_action", "payload": pa_alt_payload, "title": "QQQ 1H PA"},
    )
    pa_alt_html = build_delivery_packet(pa_alt).inline_html or b""
    require("1H EMA20 / 50".encode() in pa_alt_html, "primary EMA label is hard-coded")
    require("1H ATR14".encode() in pa_alt_html, "primary ATR label is hard-coded")
    require(b">2.5<" in pa_alt_html, "primary ATR value was dropped by the adapter")
    require("4H EMA20 / 50".encode() not in pa_alt_html, "4H prototype label leaked")

    pa_full_payload = load("chart-ohlcv-qqq-sample.json")
    pa_full_payload.update({
        "primary_timeframe": "4H",
        "auxiliary_timeframes": "1D / 1H",
        "daily_context": {"ema20": 500.0, "ema50": 490.0, "ema200": 450.0},
        "atr14_4h": 8.0,
        "decision_summary": "等待结构确认。",
        "structure_summary": "当前仍在均线压力下方。",
        "scenarios": {
            "bull": {"target": 520, "condition": "收复", "path": "上行", "action": "试仓"},
            "base": {"target": 500, "condition": "震荡", "path": "整理", "action": "等待"},
            "bear": {"target": 470, "condition": "失守", "path": "下行", "action": "取消"},
        },
        "entry_plan": [{"stage": "第1段", "allocation": "1/3", "condition": "确认后", "invalidation": "结构失效"}],
        "event_watch": [{"time": "07-23", "event": "公司财报", "importance": "high", "transmission": "需求验证", "watch": "指引"}],
        "event_note": "下一次公司事件待确认。",
        "notes": ["数据口径：演示。"],
    })
    pa_full = result(
        "price_action",
        {"adapter": "price_action", "payload": pa_full_payload, "title": "QQQ Complete PA Template"},
    )
    pa_full_html = build_delivery_packet(pa_full).inline_html or b""
    for anchor in (b"metric-strip", b"scenario-detail", b"pa-chart", b"level-ladder", b"entry-plan", b"event-list", b"data-notes"):
        require(anchor in pa_full_html, f"frozen price action anchor missing: {anchor.decode()}")
    for expected in ("4H", "1D / 1H", "结构失效", "试仓", "取消"):
        require(expected.encode() in pa_full_html, f"price action requirement missing: {expected}")
    require("20Y美债".encode() not in pa_full_html, "macro liquidity event leaked into price action template")
    require(len(pa_full_html) < 100_000, "complete price action inline output is too large")

    gap = result("report", None)
    gap["data_gaps"] = [{"label": "Primary source", "reason": "Unavailable", "status": "partial"}]
    require("## \u6570\u636e\u7f3a\u53e3" in build_delivery_packet(gap).markdown.decode("utf-8"), "visible data gap missing")

    unsafe = result("report", None)
    unsafe["decision"] = "Expose account_id in a public fixture."
    try:
        build_delivery_packet(unsafe)
    except ResearchResultError as error:
        require(str(error) == "public_privacy_invalid", "wrong privacy error code")
    else:
        raise AssertionError("public privacy sentinel was accepted")

    missing_source = result("report", None)
    missing_source["key_evidence"][0]["source_refs"] = []
    missing_source["sources"] = []
    try:
        build_delivery_packet(missing_source)
    except ResearchResultError as error:
        require(str(error) == "source_refs_required", "wrong missing-provenance error code")
    else:
        raise AssertionError("evidence without provenance was accepted")

    order_action = result("report", None)
    order_action["decision"] = "Place the order now."
    try:
        build_delivery_packet(order_action)
    except ResearchResultError as error:
        require(str(error) == "order_action_invalid", "wrong order-safety error code")
    else:
        raise AssertionError("order action was accepted")

    for instruction in (
        "Buy 100 shares now.",
        "Create a market order to buy NVDA now.",
        "Place a market order.",
        "下单买入100股。",
    ):
        unsafe_instruction = result("report", None)
        unsafe_instruction["decision"] = instruction
        try:
            build_delivery_packet(unsafe_instruction)
        except ResearchResultError as error:
            require(str(error) == "order_action_invalid", "wrong order-safety error code")
        else:
            raise AssertionError(f"order instruction was accepted: {instruction}")

    oversized = result("report", None)
    oversized["decision"] = "x" * 500_001
    try:
        build_delivery_packet(oversized)
    except ResearchResultError as error:
        require(str(error) == "result_size_invalid", "wrong result-size error code")
    else:
        raise AssertionError("oversized result was accepted")

    print("ResearchResult selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
