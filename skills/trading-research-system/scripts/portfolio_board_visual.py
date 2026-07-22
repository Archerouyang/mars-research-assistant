#!/usr/bin/env python3
"""Portfolio risk Board visual adapter."""

from __future__ import annotations

import copy
from html import escape
from typing import Any, Mapping

from board_visual_contract import BoardVisualError, exact_fields
from board_visual_shared import (
    _base_css,
    _public_fixture_attr,
    _public_fixture_badge,
    _root_id,
    _script_json,
)
from portfolio_panel_adapter import validate_portfolio_panel


def normalize(visual: Mapping[str, Any]) -> dict[str, Any]:
    exact_fields(visual, {"adapter", "panel"}, "visual_fields_invalid")
    panel = visual.get("panel")
    if not isinstance(panel, Mapping):
        raise BoardVisualError("visual_panel_invalid")
    normalized = copy.deepcopy(dict(visual))
    normalized["panel"] = copy.deepcopy(dict(panel))
    validate_portfolio_panel(normalized["panel"])
    return normalized


def render(visual: Mapping[str, Any], privacy: str) -> bytes:
    panel = copy.deepcopy(dict(visual["panel"]))
    panel["privacy"] = privacy
    validate_portfolio_panel(panel)
    return _render_panel(panel)


def _render_panel(snapshot: Mapping[str, Any]) -> bytes:
    payload = snapshot["payload"]
    root = _root_id("portfolio", snapshot)
    totals = payload["totals"]
    aggs = payload["aggregations"]
    source_count = len(payload.get("source_coverage") or [])
    reconciled_count = sum(
        1
        for row in payload.get("source_coverage") or []
        if row.get("reconciliation_status") == "reconciled"
    )
    exclusion_count = len(payload.get("exclusions") or [])
    capital_context = float(totals["gross_market_value"]) + float(totals["cash_context"])
    cash_pct = (
        float(totals["cash_context"]) / capital_context * 100
        if capital_context
        else 0.0
    )
    delta_multiple = (
        float(totals["gross_delta_exposure"]) / float(totals["gross_market_value"])
        if float(totals["gross_market_value"])
        else 0.0
    )
    stresses = sorted(
        payload.get("stress_scenarios") or [],
        key=lambda row: float(row["estimated_impact"]),
    )
    worst = stresses[0] if stresses else None
    worst_pct = (
        abs(float(worst["estimated_impact"])) / capital_context * 100
        if worst and capital_context
        else 0.0
    )
    top_symbol = (aggs.get("by_symbol") or [{}])[0]
    leveraged = next(
        (
            row
            for row in aggs.get("by_product", [])
            if "lever" in str(row.get("label", "")).lower()
            or "杠杆" in str(row.get("label", ""))
        ),
        None,
    )
    leveraged_pct = float(leveraged["weight_pct"]) if leveraged else 0.0
    primary_risk = next(
        (row for row in payload.get("risk_ledger", []) if row.get("severity") == "high"),
        (payload.get("risk_ledger") or [{}])[0],
    )
    exclusion_labels = [str(row.get("symbol") or "已排除项") for row in payload.get("exclusions", [])]
    fundamentals_payload = payload.get("fundamentals") or {"source": "not_provided", "as_of": "", "items": []}

    def normalized_rows(name: str, rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for row in rows:
            label = str(row["label"])
            if name == "broker":
                label = label.split(" / ", 1)[0]
            normalized.append(
                {
                    "label": label,
                    "weight_pct": float(row["weight_pct"]),
                    "direct_pct": (
                        float(row["direct_market_value"])
                        / float(totals["gross_market_value"])
                        * 100
                        if float(totals["gross_market_value"])
                        else 0.0
                    ),
                    "delta_pct": (
                        abs(float(row["delta_exposure"]))
                        / float(totals["gross_delta_exposure"])
                        * 100
                        if float(totals["gross_delta_exposure"])
                        else 0.0
                    ),
                    "signed_delta_pct": (
                        float(row["delta_exposure"])
                        / float(totals["gross_delta_exposure"])
                        * 100
                        if float(totals["gross_delta_exposure"])
                        else 0.0
                    ),
                    "direct_market_value": float(row["direct_market_value"]),
                    "delta_exposure": float(row["delta_exposure"]),
                    "notional_exposure": float(row["notional_exposure"]),
                    "plan_limit": str(row["plan_limit"]),
                    "affected_holdings": list(row.get("affected_holdings") or []),
                }
            )
        return normalized

    views = {
        "symbol": normalized_rows("symbol", aggs.get("by_symbol", [])),
        "theme": normalized_rows("theme", aggs.get("by_theme", [])),
        "product": normalized_rows("product", aggs.get("by_product", [])),
        "broker": normalized_rows("broker", aggs.get("by_broker", [])),
        "stress": [
            {
                "label": row["name"],
                "weight_pct": (
                    abs(float(row["estimated_impact"])) / capital_context * 100
                    if capital_context
                    else 0.0
                ),
                "estimated_impact": float(row["estimated_impact"]),
                "confidence": str(row["confidence"]),
                "assumptions": list(row.get("assumptions") or []),
                "plan_limit": row["plan_constraint"],
            }
            for row in stresses
        ],
    }
    concentration_rows = "".join(
        f'<div class="concentration-row"><div class="concentration-copy"><strong>{escape(str(row["label"]))}</strong><span>{escape(str(row["plan_limit"]))}</span></div>'
        f'<div class="exposure-compare"><div><small>直接</small><span class="concentration-track"><i class="direct" style="--risk-width:{min(100.0, float(row["direct_pct"])):.1f}%"></i></span><b>{float(row["direct_pct"]):.1f}%</b></div>'
        f'<div><small>等效</small><span class="concentration-track"><i class="delta" style="--risk-width:{min(100.0, float(row["delta_pct"])):.1f}%"></i></span><b>{float(row["signed_delta_pct"]):+.1f}%</b></div></div></div>'
        for row in views["symbol"][:6]
    )
    risk_rows = "".join(
        f'<article class="risk-ledger-row"><span class="risk-severity {escape(str(row["severity"]))}">{escape({"high": "高", "medium": "中", "low": "低"}.get(str(row["severity"]), str(row["severity"])))}</span>'
        f'<div><strong>{escape(str(row["exposure"]))}</strong><p>{escape(str(row["risk_issue"]))}</p>'
        f'<small>{escape(str(row["plan_constraint"]))}</small></div></article>'
        for row in payload.get("risk_ledger", [])[:3]
    )
    exclusions = (
        f'<span>已排除：{escape("、".join(exclusion_labels))}</span>'
        if exclusion_labels
        else '<span>无用户排除项</span>'
    )
    confidence_labels = {"high": "高置信", "medium": "中置信", "low": "低置信"}
    stress_rows = "".join(
        '<article class="stress-row">'
        f'<div class="stress-scenario"><strong>{escape(str(row["name"]))}</strong>'
        f'<small>{escape(confidence_labels.get(str(row.get("confidence")), str(row.get("confidence") or "置信度未标注")))}</small></div>'
        f'<b class="{"stress-loss" if float(row["estimated_impact"]) < 0 else "stress-gain"}">{_signed_money(float(row["estimated_impact"]))}</b>'
        f'<b class="stress-nav">{float(row["estimated_impact"]) / capital_context * 100:+.1f}%</b>'
        f'<div class="stress-assumption"><span>{escape("；".join(str(item) for item in row.get("assumptions") or []) or "计算假设缺失")}</span>'
        f'<small>{escape(str(row.get("plan_constraint") or "未定义风险响应"))}</small></div></article>'
        for row in stresses
    ) or '<p class="stress-empty">暂无可用压力情景。</p>'

    def metric_card(label: str, value: str, meta: str = "") -> str:
        return (
            '<div class="fundamental-metric">'
            f'<span>{escape(label)}</span><b>{escape(value)}</b><small>{escape(meta)}</small></div>'
        )

    def number_text(value: Any, digits: int = 1, suffix: str = "") -> str:
        try:
            return f"{float(value):.{digits}f}{suffix}"
        except (TypeError, ValueError):
            return "n/a"

    def pct_text(value: Any) -> str:
        try:
            number = float(value)
            return f"{'+' if number >= 0 else ''}{number:.1f}%"
        except (TypeError, ValueError):
            return "n/a"

    def line_chart(
        points: list[Mapping[str, Any]],
        *,
        suffix: str,
        empty_text: str,
        aria_label: str,
        color: str = "var(--dt-series-1)",
    ) -> tuple[str, str]:
        clean = [
            (str(point.get("date") or ""), float(point["value"]))
            for point in points
            if point.get("date") and point.get("value") is not None
        ]
        if len(clean) < 2:
            return f'<div class="fundamental-empty text-small">{escape(empty_text)}</div>', "数据不足"
        values = [value for _, value in clean]
        low, high = min(values), max(values)
        pad = max((high - low) * 0.12, 0.5)
        minimum, maximum = low - pad, high + pad
        width, height, left, right, top, bottom = 640, 190, 42, 12, 16, 25
        coords = []
        for index, (_, value) in enumerate(clean):
            x = left + (width - left - right) * index / (len(clean) - 1)
            y = top + (maximum - value) / (maximum - minimum) * (height - top - bottom)
            coords.append((x, y))
        path = " ".join(
            f"{'M' if index == 0 else 'L'}{x:.1f} {y:.1f}"
            for index, (x, y) in enumerate(coords)
        )
        grid = "".join(
            f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--dt-border)"/>'
            f'<text x="{left-6}" y="{y+4:.1f}" text-anchor="end" fill="var(--dt-muted-foreground)" font-size="10">{value:.1f}{escape(suffix)}</text>'
            for y, value in (
                (top, maximum),
                ((height - bottom + top) / 2, (maximum + minimum) / 2),
                (height - bottom, minimum),
            )
        )
        last_x, last_y = coords[-1]
        svg = (
            f'<svg class="fundamental-chart" viewBox="0 0 640 190" preserveAspectRatio="none" role="img" aria-label="{escape(aria_label)}">'
            f'{grid}<path d="{path}" fill="none" stroke="{color}" stroke-width="2" vector-effect="non-scaling-stroke"/>'
            f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="4" fill="{color}"/>'
            f'<text x="{left}" y="{height-7}" fill="var(--dt-muted-foreground)" font-size="10">{escape(clean[0][0])}</text>'
            f'<text x="{width-right}" y="{height-7}" text-anchor="end" fill="var(--dt-muted-foreground)" font-size="10">{escape(clean[-1][0])}</text></svg>'
        )
        return svg, f"区间 {low:.1f}{suffix}–{high:.1f}{suffix} · 当前 {values[-1]:.1f}{suffix}"

    def pe_chart(points: list[Mapping[str, Any]]) -> tuple[str, str]:
        return line_chart(
            points,
            suffix="×",
            empty_text="暂无可匹配的历史一致预期 EPS。",
            aria_label="历史 Forward P/E 估算折线图",
        )

    def margin_chart(points: list[Mapping[str, Any]]) -> tuple[str, str]:
        clean = [
            {
                "date": str(point.get("date") or ""),
                "gross": point.get("gross_margin_pct"),
                "net": point.get("net_margin_pct"),
            }
            for point in points
            if point.get("date") and (point.get("gross_margin_pct") is not None or point.get("net_margin_pct") is not None)
        ]
        if len(clean) < 2:
            return '<div class="fundamental-empty text-small">历史利润率数据不足。</div>', "数据不足"
        values = [float(value) for point in clean for value in (point["gross"], point["net"]) if value is not None]
        low, high = min(values), max(values)
        pad = max((high - low) * 0.12, 1.0)
        minimum, maximum = low - pad, high + pad
        width, height, left, right, top, bottom = 640, 190, 42, 12, 16, 25

        def series(field: str, color: str) -> str:
            coords = []
            for index, point in enumerate(clean):
                value = point[field]
                if value is None:
                    continue
                x = left + (width - left - right) * index / (len(clean) - 1)
                y = top + (maximum - float(value)) / (maximum - minimum) * (height - top - bottom)
                coords.append((x, y))
            path = " ".join(f"{'M' if index == 0 else 'L'}{x:.1f} {y:.1f}" for index, (x, y) in enumerate(coords))
            return f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" vector-effect="non-scaling-stroke"/>' if len(coords) >= 2 else ""

        grid = "".join(
            f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--dt-border)"/>'
            f'<text x="{left-6}" y="{y+4:.1f}" text-anchor="end" fill="var(--dt-muted-foreground)" font-size="10">{value:.1f}%</text>'
            for y, value in ((top, maximum), ((height - bottom + top) / 2, (maximum + minimum) / 2), (height - bottom, minimum))
        )
        svg = (
            '<svg class="fundamental-chart" viewBox="0 0 640 190" preserveAspectRatio="none" role="img" aria-label="毛利率与净利率趋势">'
            f'{grid}{series("gross", "var(--dt-series-1)")}{series("net", "var(--dt-series-3)")}'
            f'<text x="{left}" y="{height-7}" fill="var(--dt-muted-foreground)" font-size="10">{escape(clean[0]["date"])}</text>'
            f'<text x="{width-right}" y="{height-7}" text-anchor="end" fill="var(--dt-muted-foreground)" font-size="10">{escape(clean[-1]["date"])}</text></svg>'
        )
        return svg, '<span class="series-key gross">毛利率</span><span class="series-key net">净利率</span>'

    fundamental_items = list(fundamentals_payload.get("items") or [])
    fundamental_tabs = "".join(
        f'<button type="button" data-fundamental-tab="{index}" class="{"is-active" if index == 0 else ""}">'
        f'{escape("/".join(item.get("source_holdings") or []))}{" → " if any(symbol != item.get("symbol") for symbol in item.get("source_holdings") or []) else ""}{escape(str(item.get("symbol") or "")) if any(symbol != item.get("symbol") for symbol in item.get("source_holdings") or []) else ""}</button>'
        for index, item in enumerate(fundamental_items)
    ) or '<span class="text-small">尚未接入底层基本面数据。</span>'
    fundamental_cards = []
    status_labels = {"available": "完整", "partial": "部分", "proxy": "篮子代理"}
    for index, item in enumerate(fundamental_items):
        metrics = item.get("metrics") or {}
        holdings = list(item.get("source_holdings") or [])
        symbol = str(item.get("symbol") or "")
        mapping = (
            f'{"、".join(holdings)} → {symbol} · {item.get("mapping_note")}'
            if any(holding != symbol for holding in holdings)
            else f'{symbol} · {item.get("mapping_note")}'
        )
        pe_visual, pe_range = pe_chart(list(item.get("forward_pe_history") or []))
        margin_visual, margin_legend = margin_chart(list(metrics.get("margin_history") or []))
        short_visual, short_range = line_chart(
            list(metrics.get("short_volume_history") or []),
            suffix="%",
            empty_text="暂无每日卖空成交历史。",
            aria_label="每日卖空成交占比趋势",
            color="var(--dt-series-3)",
        )
        put_call_visual, put_call_range = line_chart(
            list(metrics.get("put_call_volume_history") or []),
            suffix="×",
            empty_text="暂无 Put/Call 成交量历史。",
            aria_label="Put Call 成交量比趋势",
            color="var(--dt-warning)",
        )
        report = str(metrics.get("report") or "")
        report_meta = f'{report} · 发布 {metrics.get("report_date")}' if metrics.get("report_date") else report
        short_status = str(metrics.get("short_interest_status") or "missing")
        short_meta = (
            f'{metrics.get("short_interest_as_of")} · DTC {number_text(metrics.get("short_days_to_cover"), 2)}'
            if short_status == "available"
            else f'数据过期：{metrics.get("short_interest_as_of")}'
            if short_status == "stale"
            else "无可用 FINRA 数据"
        )
        iv_status = str(metrics.get("iv30_status") or "missing")
        iv_meta = (
            f'Cboe 延迟 · {metrics.get("iv30_as_of")}'
            if iv_status == "available"
            else f'Cboe 数据过期 · {metrics.get("iv30_as_of")}'
            if iv_status == "stale"
            else "无可用期权波动率"
        )
        valuation_cards = "".join(
            [
                metric_card("价格", f"${number_text(metrics.get('price'), 2)}" if metrics.get("price") is not None else "n/a", "最近交易日"),
                metric_card("当前 P/E", number_text(metrics.get("current_pe"), 1, "×"), "Longbridge 历史估值口径"),
                metric_card("Forward P/E", number_text(metrics.get("forward_pe"), 1, "×"), "价格 ÷ 一致预期 EPS"),
                metric_card("预期 EPS", number_text(metrics.get("forward_eps"), 2), f"{pct_text(metrics.get('eps_revision_30d_pct'))} / 30日"),
            ]
        )
        earnings_cards = "".join(
            [
                metric_card("营收同比", pct_text(metrics.get("revenue_yoy_pct")), report_meta),
                metric_card("毛利率", number_text(metrics.get("gross_margin_pct"), 1, "%"), report_meta),
                metric_card("净利润同比", pct_text(metrics.get("net_income_yoy_pct")), report_meta),
                metric_card("净利率", number_text(metrics.get("net_margin_pct"), 1, "%"), report_meta),
                metric_card("ROE", number_text(metrics.get("roe_pct"), 1, "%"), str(metrics.get("roe_report") or "最近可用报告")),
            ]
        )
        short_volume = metrics.get("short_volume_pct")
        short_average = metrics.get("short_volume_5d_avg_pct")
        short_read = "每日卖空量包括做市与对冲，不等同于新增净空仓。"
        if short_volume is not None and short_average is not None:
            if float(short_volume) > float(short_average) * 1.1:
                short_read = "卖空成交高于5日均值，短线对冲或做空流量升温；不等同于空头净仓同步增加。"
            elif float(short_volume) < float(short_average) * 0.9:
                short_read = "卖空成交低于5日均值，短线压力缓和；仍需结合未平仓空头确认。"
        put_call = metrics.get("put_call_volume_ratio")
        put_call_read = "期权成交结构接近均衡。"
        if put_call is not None and float(put_call) > 1.2:
            put_call_read = "Put成交量高于Call，保护性需求或偏空交易升温。"
        elif put_call is not None and float(put_call) < 0.8:
            put_call_read = "Call成交量占优，方向性上行需求更强。"
        positioning_cards = "".join(
            [
                metric_card("未平仓空头 / 流通股", number_text(metrics.get("short_interest_pct"), 2, "%"), short_meta),
                metric_card("回补天数", number_text(metrics.get("short_days_to_cover"), 2, "天"), "FINRA双周未平仓口径"),
                metric_card("当日卖空成交占比", number_text(short_volume, 1, "%"), str(metrics.get("short_volume_as_of") or "Longbridge")),
                metric_card("5日卖空均值", number_text(short_average, 1, "%"), "用于判断短线流量偏离"),
                metric_card("P/C 成交量", number_text(put_call, 2, "×"), f"20日均值 {number_text(metrics.get('put_call_volume_20d_avg'), 2, '×')}"),
                metric_card("P/C 未平仓", number_text(metrics.get("put_call_open_interest_ratio"), 2, "×"), str(metrics.get("option_positioning_as_of") or "Longbridge")),
            ]
        )
        iv30_value = metrics.get("iv30_pct")
        hv20_value = metrics.get("hv20_pct")
        iv_hv_ratio = metrics.get("iv_hv_ratio")
        vol_read = "波动数据不足，暂不判断期权定价是否昂贵。"
        if iv_hv_ratio is not None:
            if float(iv_hv_ratio) > 1.2:
                vol_read = "IV明显高于近20日实际波动，期权正在为未来事件风险收取较高溢价。"
            elif float(iv_hv_ratio) < 0.85:
                vol_read = "IV低于近20日实际波动，期权定价未充分延续近期振幅。"
            else:
                vol_read = "IV与近20日实际波动接近，期权定价大致匹配近期振幅。"
        volatility_cards = "".join(
            [
                metric_card("IV30", number_text(iv30_value, 1, "%"), iv_meta),
                metric_card("HV20", number_text(hv20_value, 1, "%"), "Longbridge日线收盘计算"),
                metric_card("IV / HV", number_text(iv_hv_ratio, 2, "×"), f"溢价 {number_text(metrics.get('iv_hv_spread_pct'), 1, 'pct')}"),
                metric_card("隐含30日区间", f"±{number_text(metrics.get('implied_move_30d_pct'), 1, '%')}", "由IV30换算，非目标价"),
            ]
        )
        vol_scale = max(float(iv30_value or 0), float(hv20_value or 0), 1.0)
        volatility_compare = (
            '<div class="vol-compare" aria-label="隐含波动率与实际波动率对比">'
            f'<div><span>IV30</span><i><b style="--vol-width:{float(iv30_value or 0) / vol_scale * 100:.1f}%"></b></i><strong>{number_text(iv30_value, 1, "%")}</strong></div>'
            f'<div><span>HV20</span><i><b class="realized" style="--vol-width:{float(hv20_value or 0) / vol_scale * 100:.1f}%"></b></i><strong>{number_text(hv20_value, 1, "%")}</strong></div></div>'
        )
        subview_tabs = "".join(
            f'<button type="button" data-fundamental-view="{view}" class="{"is-active" if view == "valuation" else ""}">{label}</button>'
            for view, label in (("valuation", "估值"), ("earnings", "盈利"), ("positioning", "定位"), ("volatility", "波动"))
        )
        fundamental_cards.append(
            f'<article class="fundamental-card {"is-active" if index == 0 else ""}" data-fundamental-card="{index}">'
            f'<div class="fundamental-head"><div><h3>{escape(str(item.get("display_name") or symbol))}</h3><div class="fundamental-map text-small">{escape(mapping)}</div></div>'
            f'<span class="fundamental-state {escape(str(item.get("status") or "partial"))}">{escape(status_labels.get(str(item.get("status")), str(item.get("status") or "partial")))}</span></div>'
            f'<div class="fundamental-subtabs">{subview_tabs}</div>'
            f'<section class="fundamental-pane is-active" data-fundamental-pane="valuation"><div class="fundamental-metrics">{valuation_cards}</div><div class="fundamental-chart-wrap"><div class="fundamental-chart-head"><strong>历史 Forward P/E 估算</strong><span class="text-small">{escape(pe_range)}</span></div>{pe_visual}</div></section>'
            f'<section class="fundamental-pane" data-fundamental-pane="earnings"><div class="fundamental-metrics">{earnings_cards}</div><div class="fundamental-chart-wrap"><div class="fundamental-chart-head"><strong>利润率趋势</strong><span class="text-small series-legend">{margin_legend}</span></div>{margin_visual}</div></section>'
            f'<section class="fundamental-pane" data-fundamental-pane="positioning"><div class="fundamental-metrics">{positioning_cards}</div><div class="fundamental-chart-grid"><div class="fundamental-chart-wrap"><div class="fundamental-chart-head"><strong>每日卖空成交占比</strong><span class="text-small">{escape(short_range)}</span></div>{short_visual}</div><div class="fundamental-chart-wrap"><div class="fundamental-chart-head"><strong>Put/Call 成交量比</strong><span class="text-small">{escape(put_call_range)}</span></div>{put_call_visual}</div></div><p class="fundamental-read">{escape(short_read)} {escape(put_call_read)}</p></section>'
            f'<section class="fundamental-pane" data-fundamental-pane="volatility"><div class="fundamental-metrics">{volatility_cards}</div>{volatility_compare}<p class="fundamental-read">{escape(vol_read)} 隐含区间只表达市场定价的振幅，不表达方向。</p></section>'
            f'<div class="fundamental-note text-small">{escape(str(item.get("note") or ""))} · 来源：{escape(str(fundamentals_payload.get("source") or "not_provided"))} · 截至 {escape(str(fundamentals_payload.get("as_of") or snapshot["decision_cutoff"]))}</div></article>'
        )
    fundamental_cards_html = "".join(fundamental_cards)
    data = _script_json(views)
    html = f"""<div id="{root}" class="dt-board"{_public_fixture_attr(snapshot.get('privacy'))}>
  <style>{_base_css(root)}
    #{root}{{--dt-foreground:var(--foreground,#17212b);--dt-muted-foreground:var(--muted-foreground,#66727d);--dt-border:var(--border,#d7dee4);--dt-muted:var(--muted,#edf1f4);--dt-surface:var(--card,#f8fafb);--dt-series-1:var(--viz-series-1,#147d73);--dt-series-2:var(--viz-series-2,#2a76b8);--dt-series-3:var(--viz-series-3,#d05a48);--dt-success:var(--success,#147d73);--dt-warning:var(--warning,#c98718);--dt-destructive:var(--destructive,#ba3344);color:var(--dt-foreground)}}
    #{root} .portfolio-head{{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}}
    #{root} .portfolio-head h3{{margin:3px 0 0;font-size:18px}}
    #{root} .portfolio-meta{{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:5px 12px;color:var(--muted-foreground)}}
    #{root} .source-state{{display:inline-flex;align-items:center;gap:6px;color:var(--foreground)}}
    #{root} .source-state::before{{content:"";width:7px;height:7px;border-radius:50%;background:var(--viz-series-1)}}
    #{root} .portfolio-summary{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-block:1px solid var(--border)}}
    #{root} .summary-metric{{display:grid;min-width:0;gap:3px;padding:10px 12px 11px 0;border-right:1px solid var(--border)}}
    #{root} .summary-metric+ .summary-metric{{padding-left:12px}}
    #{root} .summary-metric:last-child{{border-right:0}}
    #{root} .summary-metric span,#{root} .summary-metric small{{color:var(--muted-foreground)}}
    #{root} .summary-metric b{{font-size:18px;font-variant-numeric:tabular-nums}}
    #{root} .summary-metric.risk b{{color:var(--destructive)}}
    #{root} .portfolio-decision{{display:grid;grid-template-columns:92px minmax(0,1fr);gap:4px 14px;padding:10px 0;border-bottom:1px solid var(--border)}}
    #{root} .portfolio-decision>span{{grid-row:1/3;color:var(--destructive);font-size:12px;font-weight:650}}
    #{root} .portfolio-decision p{{margin:0;color:var(--muted-foreground)}}
    #{root} .portfolio-overview{{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(260px,.8fr);gap:18px}}
    #{root} .overview-section{{display:grid;align-content:start;gap:0}}
    #{root} .overview-section h3,#{root} .dimension-head h3{{margin:0;padding:0 0 8px;font-size:14px}}
    #{root} .concentration-row{{display:grid;min-width:0;gap:8px;padding:10px 0;border-top:1px solid var(--border)}}
    #{root} .concentration-copy{{display:grid;min-width:0;gap:2px}}
    #{root} .concentration-copy strong,#{root} .concentration-copy span{{overflow-wrap:anywhere}}
    #{root} .concentration-copy span{{color:var(--muted-foreground);font-size:11px}}
    #{root} .exposure-compare{{display:grid;min-width:0;gap:6px}}
    #{root} .exposure-compare>div{{display:grid;min-width:0;grid-template-columns:42px minmax(0,1fr) 48px;gap:8px;align-items:center}}
    #{root} .exposure-compare small{{color:var(--muted-foreground)}}
    #{root} .exposure-compare b{{text-align:right;font-variant-numeric:tabular-nums}}
    #{root} .concentration-track{{display:block;height:6px;background:var(--muted);overflow:hidden}}
    #{root} .concentration-track i{{display:block;width:var(--risk-width);height:100%}}
    #{root} .concentration-track .direct{{background:var(--viz-series-3)}}
    #{root} .concentration-track .delta{{background:var(--viz-series-1)}}
    #{root} .risk-ledger-row{{display:grid;grid-template-columns:52px minmax(0,1fr);gap:10px;padding:9px 0;border-top:1px solid var(--border)}}
    #{root} .risk-ledger-row p{{margin:2px 0}}
    #{root} .risk-ledger-row small{{color:var(--muted-foreground)}}
    #{root} .risk-severity{{align-self:start;padding:2px 6px;text-align:center;font-size:11px;border:1px solid var(--border)}}
    #{root} .risk-severity.high{{color:var(--destructive);border-color:color-mix(in srgb,var(--destructive) 35%,var(--border))}}
    #{root} .dimension-panel{{display:none}}
    #{root} .dimension-panel.is-active{{display:grid;gap:0}}
    #{root} .dimension-head{{display:grid;grid-template-columns:minmax(0,1fr) repeat(3,100px);gap:10px;padding:0 0 7px;color:var(--muted-foreground);font-size:11px}}
    #{root} .dimension-row{{display:grid;grid-template-columns:minmax(0,1fr) repeat(3,100px);gap:10px;align-items:center;padding:10px 0;border-top:1px solid var(--border)}}
    #{root} .dimension-identity{{display:grid;min-width:0;grid-template-columns:minmax(0,1fr) 54px;gap:5px 9px;align-items:center}}
    #{root} .dimension-identity strong{{min-width:0;overflow-wrap:anywhere}}
    #{root} .dimension-identity b,#{root} .dimension-row>span{{font-variant-numeric:tabular-nums}}
    #{root} .dimension-identity em{{font-style:normal;text-align:right}}
    #{root} .dimension-track{{grid-column:1/-1;min-width:0;height:7px;background:var(--muted);overflow:hidden}}
    #{root} .dimension-track i{{display:block;width:var(--risk-width);height:100%;background:var(--viz-series-1)}}
    #{root} .dimension-detail{{min-height:32px;padding:8px 0;color:var(--dt-muted-foreground);border-top:1px solid var(--dt-border)}}
    #{root} .stress-panel{{display:none;gap:10px}}
    #{root} .stress-panel.is-active{{display:grid}}
    #{root} .stress-intro{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px 18px;align-items:end;padding:10px 12px;border-left:3px solid var(--dt-destructive);background:var(--dt-muted)}}
    #{root} .stress-intro strong{{font-size:14px}}
    #{root} .stress-intro p{{grid-column:1;margin:3px 0 0;color:var(--dt-muted-foreground);font-size:12px;line-height:1.5}}
    #{root} .stress-intro span{{grid-column:2;grid-row:1/3;align-self:center;color:var(--dt-destructive);font-size:12px;font-weight:650}}
    #{root} .stress-head,#{root} .stress-row{{display:grid;grid-template-columns:minmax(180px,.8fr) 120px 90px minmax(280px,1.7fr);gap:12px;align-items:center}}
    #{root} .stress-head{{padding:0 10px 5px;color:var(--dt-muted-foreground);font-size:11px}}
    #{root} .stress-row{{padding:11px 10px;border-top:1px solid var(--dt-border)}}
    #{root} .stress-scenario,#{root} .stress-assumption{{display:grid;min-width:0;gap:3px}}
    #{root} .stress-scenario small,#{root} .stress-assumption span,#{root} .stress-assumption small{{color:var(--dt-muted-foreground);font-size:11px;line-height:1.45}}
    #{root} .stress-loss,#{root} .stress-gain,#{root} .stress-nav{{font-variant-numeric:tabular-nums}}
    #{root} .stress-loss{{color:var(--dt-destructive)}}
    #{root} .stress-gain{{color:var(--dt-success)}}
    #{root} .stress-nav{{color:var(--dt-warning)}}
    #{root} .stress-empty{{color:var(--dt-muted-foreground)}}
    #{root} .fundamentals-panel{{display:none;gap:12px}}
    #{root} .fundamentals-panel.is-active{{display:grid}}
    #{root} .fundamental-tabs{{display:flex;flex-wrap:wrap;gap:6px;padding-bottom:8px;border-bottom:1px solid var(--dt-border)}}
    #{root} .fundamental-tabs button{{border:1px solid var(--dt-border);background:transparent;color:var(--dt-muted-foreground);padding:4px 9px;cursor:pointer}}
    #{root} .fundamental-tabs button.is-active{{color:var(--dt-foreground);border-color:var(--dt-series-1);background:color-mix(in srgb,var(--dt-series-1) 10%,transparent)}}
    #{root} .fundamental-cards{{display:grid;min-width:0}}
    #{root} .fundamental-card{{display:none;min-width:0;gap:12px}}
    #{root} .fundamental-card.is-active{{display:grid}}
    #{root} .fundamental-head{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}
    #{root} .fundamental-head h3{{margin:0;font-size:16px}}
    #{root} .fundamental-map{{margin-top:3px;color:var(--dt-muted-foreground)}}
    #{root} .fundamental-state{{padding:2px 7px;border:1px solid var(--dt-border);font-size:11px;white-space:nowrap}}
    #{root} .fundamental-state.available{{color:var(--dt-series-1)}}
    #{root} .fundamental-state.partial,#{root} .fundamental-state.proxy{{color:var(--dt-warning)}}
    #{root} .fundamental-subtabs{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-bottom:1px solid var(--dt-border)}}
    #{root} .fundamental-subtabs button{{border:0;border-bottom:2px solid transparent;background:transparent;color:var(--dt-muted-foreground);padding:8px 6px;cursor:pointer}}
    #{root} .fundamental-subtabs button.is-active{{color:var(--dt-foreground);border-bottom-color:var(--dt-series-1);font-weight:650}}
    #{root} .fundamental-pane{{display:none;min-width:0;gap:12px}}
    #{root} .fundamental-pane.is-active{{display:grid}}
    #{root} .fundamental-metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}}
    #{root} .fundamental-metric{{display:grid;min-width:0;gap:3px;padding:9px;border:1px solid var(--dt-border);border-radius:6px;background:var(--dt-surface)}}
    #{root} .fundamental-metric span,#{root} .fundamental-metric small{{color:var(--dt-muted-foreground)}}
    #{root} .fundamental-metric b{{font-size:16px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}}
    #{root} .fundamental-chart-wrap{{display:grid;gap:6px;min-width:0;padding-top:2px}}
    #{root} .fundamental-chart-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
    #{root} .fundamental-chart-head{{display:flex;justify-content:space-between;gap:10px;align-items:baseline}}
    #{root} .fundamental-chart-head strong{{font-size:13px}}
    #{root} .fundamental-chart-head span{{color:var(--dt-muted-foreground)}}
    #{root} .fundamental-chart{{display:block;width:100%;height:190px;overflow:visible;border-block:1px solid var(--dt-border)}}
    #{root} .fundamental-empty{{display:grid;min-height:110px;place-items:center;color:var(--dt-muted-foreground);border-block:1px solid var(--dt-border)}}
    #{root} .series-legend{{display:flex;gap:10px}}
    #{root} .series-key::before{{content:"";display:inline-block;width:12px;height:2px;margin:0 5px 3px 0;background:var(--dt-series-1)}}
    #{root} .series-key.net::before{{background:var(--dt-series-3)}}
    #{root} .fundamental-read{{margin:0;padding:9px 0;border-top:1px solid var(--dt-border);color:var(--dt-muted-foreground);font-size:12px;line-height:1.55}}
    #{root} .vol-compare{{display:grid;gap:9px;padding:10px 0;border-block:1px solid var(--dt-border)}}
    #{root} .vol-compare>div{{display:grid;grid-template-columns:42px minmax(0,1fr) 58px;gap:9px;align-items:center}}
    #{root} .vol-compare span{{color:var(--dt-muted-foreground);font-size:11px}}
    #{root} .vol-compare i{{display:block;height:8px;background:var(--dt-muted);border:1px solid var(--dt-border);overflow:hidden}}
    #{root} .vol-compare i b{{display:block;width:var(--vol-width);height:100%;background:var(--dt-warning)}}
    #{root} .vol-compare i b.realized{{background:var(--dt-series-1)}}
    #{root} .vol-compare strong{{text-align:right;font-variant-numeric:tabular-nums}}
    #{root} .fundamental-note{{color:var(--dt-muted-foreground)}}
    #{root} .portfolio-foot{{display:flex;flex-wrap:wrap;gap:8px 16px;padding-top:7px;color:var(--muted-foreground);border-top:1px solid var(--border)}}
    @media(max-width:720px){{#{root} .portfolio-head{{display:grid}}#{root} .portfolio-overview{{grid-template-columns:minmax(0,1fr)}}#{root} .portfolio-meta{{justify-content:flex-start}}#{root} .portfolio-summary{{grid-template-columns:1fr 1fr}}#{root} .summary-metric:nth-child(2){{border-right:0}}#{root} .dimension-head,#{root} .stress-head{{display:none}}#{root} .dimension-row{{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}#{root} .dimension-identity{{grid-column:1/-1}}#{root} .stress-row{{grid-template-columns:minmax(0,1fr) 110px 80px}}#{root} .stress-assumption{{grid-column:1/-1}}#{root} .fundamental-metrics{{grid-template-columns:1fr 1fr}}#{root} .fundamental-chart-grid{{grid-template-columns:minmax(0,1fr)}}}}
    @media(max-width:480px){{#{root} .portfolio-summary{{grid-template-columns:minmax(0,1fr)}}#{root} .summary-metric,#{root} .summary-metric+ .summary-metric{{padding-left:0;border-right:0}}#{root} .portfolio-decision{{grid-template-columns:minmax(0,1fr)}}#{root} .portfolio-decision>span{{grid-row:auto}}#{root} .exposure-compare>div{{grid-template-columns:36px minmax(0,1fr) 44px;gap:6px}}#{root} .dimension-row{{grid-template-columns:minmax(0,1fr)}}#{root} .dimension-identity,#{root} .dimension-row>span{{grid-column:1}}#{root} .stress-intro{{grid-template-columns:minmax(0,1fr)}}#{root} .stress-intro span{{grid-column:1;grid-row:auto}}#{root} .stress-row{{grid-template-columns:minmax(0,1fr) 1fr 1fr}}#{root} .stress-scenario,#{root} .stress-assumption{{grid-column:1/-1}}#{root} .fundamental-head{{display:grid}}#{root} .fundamental-metrics{{grid-template-columns:minmax(0,1fr)}}}}
  </style>
  <div class="portfolio-head"><div><div class="viz-row text-small">{_public_fixture_badge(snapshot.get('privacy'))}<span class="viz-badge">组合风险</span></div><h3>{escape(str(payload['posture']['label']))}</h3></div><div class="portfolio-meta text-small"><span class="source-state">已对账 {reconciled_count}/{source_count}</span><span>证据 {snapshot['coverage']['required_complete']}/{snapshot['coverage']['required_total']}</span><span>截至 {escape(str(snapshot['decision_cutoff']))}</span></div></div>
  <div class="portfolio-summary">
    <div class="summary-metric"><span>资本上下文</span><b>{_money(capital_context)}</b><small>持仓 {_money(totals['gross_market_value'])}</small></div>
    <div class="summary-metric"><span>现金缓冲</span><b>{_money(totals['cash_context'])}</b><small>{cash_pct:.1f}% 资本上下文</small></div>
    <div class="summary-metric"><span>穿透敞口</span><b>{_money(totals['gross_delta_exposure'])}</b><small>Gross Delta · {delta_multiple:.2f}× · Net {_signed_money(totals['net_delta_exposure'])}</small></div>
    <div class="summary-metric {'risk' if worst and float(worst['estimated_impact']) < 0 else ''}"><span>最坏压力</span><b>{_signed_money(float(worst["estimated_impact"])) if worst else 'n/a'}</b><small>{escape(str(worst['name'])) if worst else '情景缺失'} · {worst_pct:.1f}% 资本上下文</small></div>
  </div>
  <div class="portfolio-decision"><span>主要风险</span><strong>{escape(str(primary_risk.get('exposure') or top_symbol.get('label') or '集中度待确认'))}</strong><p>{escape(str(primary_risk.get('risk_issue') or payload['decision']))} · {escape(str(primary_risk.get('plan_constraint') or '等待风险边界确认。'))}</p></div>
  <div class="viz-controls" aria-label="组合风险视图"><button type="button" class="btn btn-primary" data-view="overview" aria-pressed="true">总览</button><button type="button" class="btn" data-view="symbol" aria-pressed="false">标的</button><button type="button" class="btn" data-view="fundamentals" aria-pressed="false">基本面</button><button type="button" class="btn" data-view="theme" aria-pressed="false">主题</button><button type="button" class="btn" data-view="product" aria-pressed="false">产品</button><button type="button" class="btn" data-view="broker" aria-pressed="false">券商</button><button type="button" class="btn" data-view="stress" aria-pressed="false">压力</button></div>
  <section class="portfolio-overview" data-panel="overview"><div class="overview-section"><h3>杠杆调整后集中度</h3>{concentration_rows}</div><div class="overview-section"><h3>风险账本</h3>{risk_rows}</div></section>
  <section class="dimension-panel" data-panel="dimension" aria-live="polite"><div class="dimension-head"><h3 data-view-title>标的</h3><span>直接市值</span><span>等效方向</span><span>名义敞口</span></div><div data-dimension-rows></div><div class="dimension-detail text-small" data-dimension-detail></div></section>
  <section class="fundamentals-panel" data-panel="fundamentals" aria-live="polite"><div class="fundamental-tabs">{fundamental_tabs}</div><div class="fundamental-cards">{fundamental_cards_html}</div></section>
  <section class="stress-panel" data-panel="stress" aria-live="polite"><div class="stress-intro"><strong>压力测试回答什么</strong><p>对已确认的等效方向敞口施加标准化冲击，比较资本损益，用于识别组合最脆弱或可对冲的风险来源。</p><span>不是价格预测</span></div><div class="stress-head"><span>情景</span><span>估算影响</span><span>资本冲击</span><span>计算假设 / 风险响应</span></div><div class="stress-rows">{stress_rows}</div></section>
  <div class="portfolio-foot text-small"><span>{escape(str(totals['scope_label']))}</span><span>杠杆产品 {leveraged_pct:.1f}%</span><span>用户排除 {exclusion_count}</span>{exclusions}</div>
  <script>(()=>{{
    const root=document.getElementById('{root}');
    const views={data};
    const overview=root.querySelector('[data-panel="overview"]');
    const panel=root.querySelector('[data-panel="dimension"]');
    const fundamentalsPanel=root.querySelector('[data-panel="fundamentals"]');
    const stressPanel=root.querySelector('[data-panel="stress"]');
    const rowsRoot=root.querySelector('[data-dimension-rows]');
    const detail=root.querySelector('[data-dimension-detail]');
    const title=root.querySelector('[data-view-title]');
    const money=new Intl.NumberFormat('en-US',{{style:'currency',currency:'USD',maximumFractionDigits:0}});
    const labels={{symbol:'标的',theme:'主题',product:'产品',broker:'券商'}};
    function cell(value){{const el=document.createElement('span');el.textContent=money.format(value);return el;}}
    function render(view){{
      const isOverview=view==='overview';
      const isFundamentals=view==='fundamentals';
      const isStress=view==='stress';
      overview.style.display=isOverview?'grid':'none';
      panel.classList.toggle('is-active',!isOverview&&!isFundamentals&&!isStress);
      fundamentalsPanel.classList.toggle('is-active',isFundamentals);
      stressPanel.classList.toggle('is-active',isStress);
      if(!isOverview&&!isFundamentals&&!isStress){{
        title.textContent=labels[view];
        rowsRoot.replaceChildren();
        const rows=views[view]||[];
        rows.forEach(row=>{{
          const line=document.createElement('div');line.className='dimension-row';
          const identity=document.createElement('div');identity.className='dimension-identity';
          const label=document.createElement('strong');label.textContent=row.label;
          const track=document.createElement('div');track.className='dimension-track';
          const fill=document.createElement('i');fill.style.setProperty('--risk-width',Math.max(2,Math.min(100,+row.weight_pct))+'%');track.appendChild(fill);
          const pctText=document.createElement('em');pctText.textContent=Number(row.weight_pct).toFixed(1)+'%';
          identity.append(label,pctText,track);line.appendChild(identity);
          line.append(cell(row.direct_market_value),cell(row.delta_exposure),cell(row.notional_exposure));
          line.addEventListener('click',()=>detail.textContent=(row.affected_holdings||[]).join('、')+' · '+row.plan_limit);
          rowsRoot.appendChild(line);
        }});
        detail.textContent=rows[0]?(rows[0].affected_holdings||[]).join('、')+' · '+rows[0].plan_limit:'该维度暂无可用数据。';
      }}
      root.querySelectorAll('[data-view]').forEach(btn=>{{const on=btn.dataset.view===view;btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('btn-primary',on);}});
    }}
    root.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>render(btn.dataset.view)));
    const fundamentalTabs=Array.from(root.querySelectorAll('[data-fundamental-tab]'));
    const fundamentalCards=Array.from(root.querySelectorAll('[data-fundamental-card]'));
    fundamentalTabs.forEach(tab=>tab.addEventListener('click',()=>{{
      const key=tab.dataset.fundamentalTab;
      fundamentalTabs.forEach(item=>item.classList.toggle('is-active',item===tab));
      fundamentalCards.forEach(card=>card.classList.toggle('is-active',card.dataset.fundamentalCard===key));
    }}));
    fundamentalCards.forEach(card=>{{
      const tabs=Array.from(card.querySelectorAll('[data-fundamental-view]'));
      const panes=Array.from(card.querySelectorAll('[data-fundamental-pane]'));
      tabs.forEach(tab=>tab.addEventListener('click',()=>{{
        const key=tab.dataset.fundamentalView;
        tabs.forEach(item=>item.classList.toggle('is-active',item===tab));
        panes.forEach(pane=>pane.classList.toggle('is-active',pane.dataset.fundamentalPane===key));
      }}));
    }});
    render('overview');
  }})();</script>
</div>
"""
    return html.encode("utf-8")


def _money(value: Any) -> str:
    return f"${float(value):,.0f}"


def _signed_money(value: Any) -> str:
    number = float(value)
    return f"{'+' if number >= 0 else '-'}{_money(abs(number))}"
