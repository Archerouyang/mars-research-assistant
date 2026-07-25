#!/usr/bin/env python3
"""Self-contained, interactive Macro Regime Board for one stateless delivery."""

from __future__ import annotations

from html import escape
import json
from typing import Any, Mapping, Sequence


def _number(value: Any, *, digits: int = 2) -> str:
    return f"{float(value):,.{digits}f}"


def _metric_card(
    label: str,
    key: str,
    suffix: str,
    values: Mapping[str, Any],
    sources: Mapping[str, Any],
    as_ofs: Mapping[str, Any],
) -> str:
    return (
        '<article class="market-card"><span class="field-label">{label}</span>'
        '<strong>{value}{suffix}</strong>'
        '<small>source: {source} · as_of: {as_of}</small></article>'
    ).format(
        label=escape(label),
        value=escape(_number(values[key])),
        suffix=escape(suffix),
        source=escape(str(sources[key])),
        as_of=escape(str(as_ofs[key])),
    )


def _trend_stat(points: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    first = points[0]
    latest = points[-1]
    start = float(first["value"])
    end = float(latest["value"])
    change = end - start
    return {
        "start": start,
        "end": end,
        "change": change,
        "percent_change": (change / abs(start) * 100) if start else None,
        "start_date": str(first["date"]),
        "end_date": str(latest["date"]),
    }


def _signed_change(stat: Mapping[str, Any]) -> str:
    change = float(stat["change"])
    percent = stat["percent_change"]
    direction = "上升" if change > 0 else "下降" if change < 0 else "持平"
    if percent is None:
        return f"30D {direction} {_number(abs(change))}"
    return f"30D {direction} {_number(abs(change))} ({abs(float(percent)):.1f}%)"


def _status_row(label: str, reading: str, note: str, source: str) -> str:
    return (
        '<article class="status-row"><div><h3>{label}</h3><p class="module-meta">{source}</p></div>'
        '<p>{reading}</p><p>{note}</p></article>'
    ).format(
        label=escape(label),
        reading=escape(reading),
        note=escape(note),
        source=escape(source),
    )


def _exposure_row(exposure: Mapping[str, str], *, selected: bool) -> str:
    selected_attr = "" if selected else " hidden"
    return (
        '<article class="exposure" data-exposure="{identifier}"{selected_attr}>'
        '<h3>{label}</h3><p><strong>当前读数：</strong>{reading}</p>'
        '<p><strong>因子敏感度：</strong>{sensitivity}</p>'
        '<p><strong>后续确认：</strong>{watch}</p></article>'
    ).format(
        identifier=escape(exposure["id"]),
        selected_attr=selected_attr,
        label=escape(exposure["label"]),
        reading=escape(exposure["reading"]),
        sensitivity=escape(exposure["sensitivity"]),
        watch=escape(exposure["watch"]),
    )


def _event_row(event: Mapping[str, Any]) -> str:
    return (
        '<article class="evidence-row"><div><span class="source-category">{category}</span>'
        '<p class="module-meta">{status}</p></div><div><h3>{time} · {title}</h3>'
        '<p>{transmission}</p><p class="evidence-reading">evidence_kind: {evidence_kind}'
        ' · primary_source_confirmed: {primary_source_confirmed}</p>'
        '<p class="module-meta">source: {source} · as_of: {as_of}</p></div></article>'
    ).format(
        category=escape(str(event["category"])),
        status=escape(str(event["status"])),
        time=escape(str(event["time"])),
        title=escape(str(event["title"])),
        transmission=escape(str(event["transmission"])),
        evidence_kind=escape(str(event["evidence_kind"])),
        primary_source_confirmed=escape(
            str(event["primary_source_confirmed"]).lower()
        ),
        source=escape(str(event["original_source"])),
        as_of=escape(str(event["as_of"])),
    )


def _scenario_row(
    name: str,
    trigger: str,
    confirmation: str,
    transmission: str,
    posture: str,
) -> str:
    return (
        '<article class="scenario-row"><div><h3>{name}</h3></div><div class="scenario-flow">'
        '<p><span>触发</span>{trigger}</p><p><span>确认</span>{confirmation}</p>'
        '<p><span>传导</span>{transmission}</p><p><span>应对</span>{posture}</p>'
        '</div></article>'
    ).format(
        name=escape(name),
        trigger=escape(trigger),
        confirmation=escape(confirmation),
        transmission=escape(transmission),
        posture=escape(posture),
    )


def _scenario_rows(
    events: Sequence[Mapping[str, Any]],
    trend_stats: Mapping[str, Mapping[str, Any]],
) -> str:
    hyg = trend_stats["HYG/LQD"]
    ndx = trend_stats["NDX/RUT"]
    rows = [
        _scenario_row(
            "风险偏好改善",
            f"HYG/LQD 与 NDX/RUT 均高于本期基准（{_number(hyg['end'])} / {_number(ndx['end'])}）。",
            "下一共同完成交易日两项相对强弱保持或改善。",
            "信用相对稳定且成长/小盘相对强弱未继续恶化。",
            "仅更新宏观观察；不产生持仓、下单或仓位建议。",
        ),
        _scenario_row(
            "风险偏好收紧",
            f"HYG/LQD 或 NDX/RUT 低于本期基准（{_number(hyg['end'])} / {_number(ndx['end'])}）。",
            "两项相对强弱同步走弱，或已确认事件出现明确风险传导。",
            "信用与风险偏好同时承压，需重新核对利率与波动率。",
            "保持观察，等待下一次完整快照；不把情景框架当作交易指令。",
        ),
    ]
    for event in events:
        rows.append(
            _scenario_row(
                f"事件核验 · {str(event['title'])}",
                f"已确认时间：{str(event['time'])}。",
                "事件发生后比较利率、信用和相对强弱是否与传导描述一致。",
                str(event["transmission"]),
                "在一手来源和完成交易日数据齐全前，不改变一次性研究结论。",
            )
        )
    return "".join(rows)


def _interactive_payload(
    payload: Mapping[str, Any],
    trend_stats: Mapping[str, Mapping[str, Any]],
) -> str:
    return json.dumps(
        {"trend_series": payload["trend_series"], "trend_stats": trend_stats},
        ensure_ascii=False,
    ).replace("<", "\\u003c")


def render_macro_board(payload: Mapping[str, Any]) -> str:
    """Render the frozen Macro v1 fields in a one-shot interactive Board."""

    values = payload["values"]
    sources = payload["sources"]
    as_ofs = payload["as_ofs"]
    trend_series = payload["trend_series"]
    trend_stats = {
        label: _trend_stat(points) for label, points in trend_series.items()
    }
    hyg_stat = trend_stats["HYG/LQD"]
    ndx_stat = trend_stats["NDX/RUT"]
    slope_10y_2y = (float(values["treasury_10y"]) - float(values["treasury_2y"])) * 100
    slope_30y_10y = (float(values["treasury_30y"]) - float(values["treasury_10y"])) * 100
    rate_cards = "".join(
        _metric_card(label, key, "%", values, sources, as_ofs)
        for label, key in (
            ("2Y", "treasury_2y"),
            ("10Y", "treasury_10y"),
            ("30Y", "treasury_30y"),
        )
    )
    cross_asset_cards = "".join(
        _metric_card(label, key, "", values, sources, as_ofs)
        for label, key in (
            ("VIX", "vix"),
            ("VIX3M", "vix3m"),
            ("DXY", "dxy"),
            ("WTI", "wti"),
            ("Gold", "gold"),
        )
    )
    decision_frame = (
        f"2Y/10Y/30Y 为 {_number(values['treasury_2y'])}% / "
        f"{_number(values['treasury_10y'])}% / {_number(values['treasury_30y'])}%；"
        f"10Y-2Y {_number(slope_10y_2y)}bp，30Y-10Y {_number(slope_30y_10y)}bp。"
        f"HYG/LQD {_signed_change(hyg_stat)}，NDX/RUT {_signed_change(ndx_stat)}。"
        "这是冻结快照的读数，不包含未经验证的政策、增长或美元叙事。"
    )
    current_status = "".join(
        (
            _status_row(
                "收益率曲线",
                f"2Y {_number(values['treasury_2y'])}% · 10Y {_number(values['treasury_10y'])}% · "
                f"30Y {_number(values['treasury_30y'])}%；10Y-2Y {_number(slope_10y_2y)}bp。",
                "只描述同一 Treasury 发布日的当期曲线，不推断后续利率方向。",
                f"source: {sources['treasury_2y']} · as_of: {as_ofs['treasury_2y']}",
            ),
            _status_row(
                "波动与跨资产",
                f"VIX {_number(values['vix'])} · VIX3M {_number(values['vix3m'])} · "
                f"DXY {_number(values['dxy'])} · WTI {_number(values['wti'])} · Gold {_number(values['gold'])}。",
                "这些是各字段最近完成会话的独立读数，未将不同来源的历史拼接为趋势。",
                f"source: {sources['vix']} · as_of: {as_ofs['vix']}",
            ),
            _status_row(
                "相对强弱",
                f"HYG/LQD {_number(hyg_stat['end'])}（{_signed_change(hyg_stat)}）· "
                f"NDX/RUT {_number(ndx_stat['end'])}（{_signed_change(ndx_stat)}）。",
                "仅使用最近 30 个共同完成的 XNYS 交易日；两个比率均由同源原始腿本地计算。",
                f"source: {sources['hyg_lqd_history']} · as_of: {as_ofs['hyg_lqd_history']}",
            ),
        )
    )
    exposures = (
        {
            "id": "rates",
            "label": "利率与久期因子",
            "reading": f"10Y-2Y {_number(slope_10y_2y)}bp；30Y-10Y {_number(slope_30y_10y)}bp。",
            "sensitivity": "用于观察长久期资产对收益率曲线变化的宏观敏感度，不代表任何个人持仓。",
            "watch": "下一次已确认重大事件后的 Treasury 同日发布数据。",
        },
        {
            "id": "credit",
            "label": "信用与风险偏好因子",
            "reading": f"HYG/LQD {_number(hyg_stat['end'])}，{_signed_change(hyg_stat)}。",
            "sensitivity": "用于观察信用相对强弱；不将单一读数解释为全市场风险结论。",
            "watch": "HYG/LQD 是否在下一完整会话保持或反转本期方向。",
        },
        {
            "id": "growth_small",
            "label": "成长与小盘相对强弱",
            "reading": f"NDX/RUT {_number(ndx_stat['end'])}，{_signed_change(ndx_stat)}。",
            "sensitivity": "用于观察成长/小盘相对强弱，不代表组合行业暴露或选股结论。",
            "watch": "NDX/RUT 是否与信用因子给出一致的下一会话确认。",
        },
    )
    exposure_options = "".join(
        '<option value="{identifier}">{label}</option>'.format(
            identifier=escape(exposure["id"]), label=escape(exposure["label"])
        )
        for exposure in exposures
    )
    exposure_rows = "".join(
        _exposure_row(exposure, selected=index == 0)
        for index, exposure in enumerate(exposures)
    )
    events_html = "".join(_event_row(event) for event in payload["events"]) or (
        '<p class="module-meta">none_found: 当前事件窗口未发现符合范围的重大事件</p>'
    )
    replacements = {
        "__AS_OF__": escape(str(payload["as_of"])),
        "__TREASURY_AS_OF__": escape(str(payload["treasury_as_of"])),
        "__EVENT_SOURCE__": escape(str(sources["macro_events"])),
        "__EVENT_AS_OF__": escape(str(as_ofs["macro_events"])),
        "__RATE_CARDS__": rate_cards,
        "__CROSS_ASSET_CARDS__": cross_asset_cards,
        "__DECISION_FRAME__": escape(decision_frame),
        "__CURRENT_STATUS__": current_status,
        "__EXPOSURE_OPTIONS__": exposure_options,
        "__EXPOSURE_ROWS__": exposure_rows,
        "__EVENTS__": events_html,
        "__SCENARIOS__": _scenario_rows(payload["events"], trend_stats),
        "__INTERACTIVE_PAYLOAD__": _interactive_payload(payload, trend_stats),
        "__HYG_SOURCE__": escape(str(sources["hyg_lqd_history"])),
        "__HYG_AS_OF__": escape(str(as_ofs["hyg_lqd_history"])),
        "__NDX_SOURCE__": escape(str(sources["ndx_rut_history"])),
        "__NDX_AS_OF__": escape(str(as_ofs["ndx_rut_history"])),
    }
    rendered = _HTML_TEMPLATE
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    return rendered


_HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Macro Regime Research Brief</title>
<style>
:root{color-scheme:light;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.45;--ink:#17212b;--muted:#586672;--line:#d5dde4;--paper:#fff;--wash:#f4f7f8;--green:#08724a;--amber:#9a5b00;--blue:#1769aa}*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--paper)}button,select{font:inherit}main{max-width:1120px;margin:0 auto;padding:20px}h1,h2,h3,p,dl,dd{margin-top:0}h1{margin-bottom:6px;font-size:26px;letter-spacing:0}h2{margin-bottom:0;font-size:18px}h3{margin-bottom:5px;font-size:15px}.masthead{display:flex;justify-content:space-between;gap:24px;padding-bottom:16px;border-bottom:3px solid var(--ink)}.eyebrow{margin-bottom:4px;color:var(--green);font-size:12px;font-weight:700;text-transform:uppercase}.lede{max-width:680px;margin-bottom:0;color:var(--muted)}.provenance{min-width:250px;margin-bottom:0;font-size:12px}.provenance div{display:grid;grid-template-columns:110px minmax(0,1fr);gap:8px;padding:3px 0}.provenance dt,.module-meta{color:var(--muted)}.provenance dd,.evidence-reading{overflow-wrap:anywhere}.summary{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:8px;margin-top:14px}.summary article{min-width:0;padding:11px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.summary p{margin:5px 0 0;font-size:12px}.field-label{display:block;margin-bottom:4px;color:var(--muted);font-size:11px;text-transform:uppercase}.decision-framing{margin:12px 0;padding:9px 11px;border-left:3px solid var(--amber);background:#fff8e7;font-size:13px}.market-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:12px 0 18px}.market-card{min-width:0;padding:11px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.market-card strong{display:block;font-size:20px;line-height:1.2}.market-card small{display:block;margin-top:6px;color:var(--muted);font-size:11px;overflow-wrap:anywhere}.view-tabs{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 12px}.view-tab{min-height:32px;padding:4px 10px;border:1px solid var(--line);border-radius:5px;color:var(--ink);background:var(--paper);cursor:pointer}.view-tab[aria-selected="true"]{border-color:var(--ink);color:var(--paper);background:var(--ink)}button:focus-visible,select:focus-visible{outline:3px solid #7db9e8;outline-offset:2px}.view-panel{display:none;padding-top:4px}.view-panel.is-active{display:block}.section-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:baseline;margin:0 0 8px}.section-head p{margin:0;color:var(--muted);font-size:12px}.series-controls{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}.series-control{min-height:30px;padding:4px 10px;border:1px solid var(--line);border-radius:5px;color:var(--ink);background:var(--paper);cursor:pointer}.series-control[aria-pressed="true"]{border-color:var(--blue);color:var(--paper);background:var(--blue)}.chart-shell{margin:0 0 12px;padding:12px;border:1px solid var(--line)}.macro-chart{display:block;width:100%;height:300px;background:linear-gradient(180deg,#fff 0%,#f8fafb 100%)}.chart-axis{stroke:var(--line);stroke-width:1}.chart-guide{stroke:#e8edf0;stroke-width:1;stroke-dasharray:3 4}.chart-line{fill:none;stroke:#147e6a;stroke-width:3;stroke-linejoin:round;stroke-linecap:round}.chart-area{fill:#147e6a;fill-opacity:.12}.chart-dot{fill:#147e6a}.chart-label{fill:var(--muted);font:11px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.trend-caption{margin:10px 0 0;padding-top:10px;border-top:1px solid var(--line);font-size:13px}.status-list,.evidence-list,.exposure-list,.scenario-grid{border-top:1px solid var(--line)}.status-row{display:grid;grid-template-columns:145px minmax(0,1fr) minmax(0,1fr);gap:12px;padding:11px 0;border-bottom:1px solid var(--line)}.status-row p,.evidence-row p,.exposure p,.scenario-row p{margin-bottom:5px}.exposure-control{display:flex;gap:8px;align-items:center;margin:18px 0 10px}.exposure-control select{min-width:220px;max-width:100%;padding:5px;border:1px solid var(--line);border-radius:4px;background:var(--paper)}.exposure{padding:11px 0;border-bottom:1px solid var(--line)}.evidence-rail{position:static;padding-left:14px;border-left:3px solid var(--blue)}.evidence-row{display:grid;grid-template-columns:95px minmax(0,1fr);gap:10px;padding:11px 0;border-bottom:1px solid var(--line)}.source-category{font-size:11px;text-transform:uppercase;color:var(--muted)}.scenario-row{display:grid;grid-template-columns:150px minmax(0,1fr);gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}.scenario-flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.scenario-flow p{margin:0}.scenario-flow span{display:block;margin-bottom:4px;color:var(--muted);font-size:11px;text-transform:uppercase}footer{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}@media(max-width:736px){main{padding:14px}.masthead{display:block}.provenance{min-width:0;margin-top:12px}.summary{grid-template-columns:1fr}.market-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.status-row,.scenario-row{grid-template-columns:1fr}.scenario-flow{grid-template-columns:1fr 1fr}.evidence-rail{border-left:0;border-top:3px solid var(--blue);padding:12px 0 0}}@media(max-width:420px){main{padding:10px}.market-strip{grid-template-columns:1fr}.provenance div,.evidence-row{grid-template-columns:1fr}.scenario-flow{grid-template-columns:1fr}.exposure-control{display:block}.exposure-control select{width:100%;margin-top:4px}}
:root{--fixture-ink:#7b3900;--fixture-wash:#fff0dc}.fixture-notice{margin:0 0 12px;padding:9px 11px;border-left:3px solid var(--amber);background:var(--fixture-wash);color:var(--fixture-ink);font-size:13px}
</style>
<style>
:root{--macro-font-sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--macro-font-numeric:"SF Mono","Roboto Mono","Noto Sans Mono CJK SC",ui-monospace,monospace}body,button,select{font-family:var(--macro-font-sans);font-synthesis:none}h1{font-weight:650;letter-spacing:-.015em}h2{font-weight:650;letter-spacing:-.01em}h3{font-weight:600}.lede,.decision-framing,.status-row,.evidence-row,.scenario-row{line-height:1.55}.market-card strong,.summary strong{font-weight:650;letter-spacing:-.015em;font-variant-numeric:tabular-nums}.provenance,.module-meta,.market-card small,.field-label,.source-category{font-weight:450}.view-tab,.series-control{font-weight:560;letter-spacing:.005em}.chart-label{font-family:var(--macro-font-numeric);font-weight:500;font-variant-numeric:tabular-nums}.trend-caption{font-variant-numeric:tabular-nums}.fixture-notice{font-weight:500}
</style>
</head>
<body>
<main id="macro-board">
<header class="masthead">
  <div><p class="eyebrow">Macro Regime</p><h1>Macro Regime Research Brief</h1><p class="lede">冻结市场快照、相对强弱与已确认重大事件；所有交互只在本页内发生，不保存状态。</p></div>
  <dl class="provenance" aria-label="数据时点与来源"><div><dt>Market as_of</dt><dd>__AS_OF__</dd></div><div><dt>Treasury as_of</dt><dd>__TREASURY_AS_OF__</dd></div><div><dt>Event source</dt><dd>__EVENT_SOURCE__ · __EVENT_AS_OF__</dd></div></dl>
</header>
<section class="summary" aria-label="Macro snapshot summary"><article><span class="field-label">Delivery scope</span><strong>Rates, volatility &amp; cross-asset</strong><p>只呈现冻结的 Macro v1 字段。</p></article><article><span class="field-label">Relative strength</span><strong>HYG/LQD · NDX/RUT</strong><p>30 个共同完成的 XNYS 交易日。</p></article><article><span class="field-label">Interaction model</span><strong>One-shot, browser-only</strong><p>页签与筛选不会持久化。</p></article></section>
<p class="decision-framing"><strong>当前快照：</strong>__DECISION_FRAME__</p>
<section class="market-strip" aria-label="Rates and cross asset snapshot">__RATE_CARDS____CROSS_ASSET_CARDS__</section>
<nav class="view-tabs" role="tablist" aria-label="Macro Board views"><button class="view-tab" type="button" role="tab" data-view="trend" aria-controls="panel-trend" aria-selected="true">趋势</button><button class="view-tab" type="button" role="tab" data-view="current" aria-controls="panel-current" aria-selected="false">当前状态</button><button class="view-tab" type="button" role="tab" data-view="events" aria-controls="panel-events" aria-selected="false">下周事件</button><button class="view-tab" type="button" role="tab" data-view="scenarios" aria-controls="panel-scenarios" aria-selected="false">情景</button></nav>
<section class="view-panel is-active" id="panel-trend" data-panel="trend" role="tabpanel"><div class="section-head"><div><p class="eyebrow">Relative strength</p><h2>相对强弱趋势</h2></div><p>30D common XNYS sessions</p></div><div class="series-controls" aria-label="趋势序列"><button class="series-control" type="button" data-series="HYG/LQD" aria-pressed="false">HYG/LQD</button><button class="series-control" type="button" data-series="NDX/RUT" aria-pressed="true">NDX/RUT</button></div><div class="chart-shell"><svg class="macro-chart" role="img" aria-label="Macro relative strength trend"></svg><p class="trend-caption" aria-live="polite"></p></div><p class="module-meta">HYG/LQD source: __HYG_SOURCE__ · as_of: __HYG_AS_OF__<br>NDX/RUT source: __NDX_SOURCE__ · as_of: __NDX_AS_OF__</p></section>
<section class="view-panel" id="panel-current" data-panel="current" role="tabpanel" hidden><div class="section-head"><div><p class="eyebrow">Snapshot</p><h2>当前状态</h2></div><p>基于当前冻结字段，不引入外部叙事。</p></div><div class="status-list">__CURRENT_STATUS__</div><div class="exposure-control"><label for="macro-exposure">宏观因子暴露</label><select id="macro-exposure" data-exposure-select>__EXPOSURE_OPTIONS__</select></div><p class="module-meta">风险暴露只描述宏观因子敏感度，不代表持仓、账户、仓位或交易建议。</p><div class="exposure-list">__EXPOSURE_ROWS__</div></section>
<section class="view-panel" id="panel-events" data-panel="events" role="tabpanel" hidden><div class="evidence-rail"><div class="section-head"><div><p class="eyebrow">Primary-source evidence</p><h2>重大事件</h2></div><p>未来七天及过去 24 小时。</p></div><div class="evidence-list">__EVENTS__</div></div></section>
<section class="view-panel" id="panel-scenarios" data-panel="scenarios" role="tabpanel" hidden><div class="section-head"><div><p class="eyebrow">Conditional framework</p><h2>情景</h2></div><p>条件框架，不是预测。</p></div><div class="scenario-grid">__SCENARIOS__</div></section>
<footer>Macro Regime Board · 一次性自包含研究交付</footer>
</main>
<script>
const board=document.getElementById('macro-board');
const boardData=__INTERACTIVE_PAYLOAD__;
const tabs=[...board.querySelectorAll('[data-view]')];
const panels=[...board.querySelectorAll('[data-panel]')];
const chart=board.querySelector('.macro-chart');
const caption=board.querySelector('.trend-caption');
const chartWidth=720,chartHeight=300,chartPad={top:22,right:24,bottom:34,left:50};
function showView(view){panels.forEach((panel)=>{const active=panel.dataset.panel===view;panel.classList.toggle('is-active',active);panel.hidden=!active;});tabs.forEach((tab)=>tab.setAttribute('aria-selected',String(tab.dataset.view===view)));}
function trendText(label,points){const first=Number(points[0].value),last=Number(points[points.length-1].value),change=last-first,percent=first===0?null:change/Math.abs(first)*100;const direction=change>0?'上升':change<0?'下降':'持平';return `${label} 当前 ${last.toFixed(2)} · 30D ${direction} ${Math.abs(change).toFixed(2)}${percent===null?'':` (${Math.abs(percent).toFixed(1)}%)`} · ${points[0].date} 至 ${points[points.length-1].date}。`;}
function renderTrend(label){const points=boardData.trend_series[label]||[];if(!points.length){chart.innerHTML='<text class="chart-label" x="12" y="24">No completed observations</text>';caption.textContent='趋势数据不足。';return;}const values=points.map((point)=>Number(point.value));const min=Math.min(...values),max=Math.max(...values),span=max-min||1;const innerWidth=chartWidth-chartPad.left-chartPad.right,innerHeight=chartHeight-chartPad.top-chartPad.bottom;const x=(index)=>chartPad.left+(points.length===1?innerWidth/2:index*innerWidth/(points.length-1));const y=(value)=>chartPad.top+innerHeight-(value-min)*innerHeight/span;const guides=[0,.5,1].map((ratio)=>{const value=min+span*ratio,guideY=y(value);return `<line class="chart-guide" x1="${chartPad.left}" y1="${guideY}" x2="${chartWidth-chartPad.right}" y2="${guideY}"/><text class="chart-label" x="2" y="${guideY+4}">${value.toFixed(2)}</text>`;}).join('');const line=points.map((point,index)=>`${index?'L':'M'}${x(index).toFixed(2)},${y(Number(point.value)).toFixed(2)}`).join(' ');const area=`${line} L${x(points.length-1)},${chartHeight-chartPad.bottom} L${x(0)},${chartHeight-chartPad.bottom} Z`;chart.setAttribute('viewBox',`0 0 ${chartWidth} ${chartHeight}`);chart.innerHTML=`${guides}<line class="chart-axis" x1="${chartPad.left}" y1="${chartHeight-chartPad.bottom}" x2="${chartWidth-chartPad.right}" y2="${chartHeight-chartPad.bottom}"/><path class="chart-area" d="${area}"/><path class="chart-line" d="${line}"/><circle class="chart-dot" cx="${x(0)}" cy="${y(values[0])}" r="3"/><circle class="chart-dot" cx="${x(points.length-1)}" cy="${y(values[values.length-1])}" r="4"/><text class="chart-label" x="${chartPad.left}" y="${chartHeight-10}">${points[0].date}</text><text class="chart-label" text-anchor="end" x="${chartWidth-chartPad.right}" y="${chartHeight-10}">${points[points.length-1].date}</text>`;caption.textContent=trendText(label,points);board.querySelectorAll('[data-series]').forEach((button)=>button.setAttribute('aria-pressed',String(button.dataset.series===label)));}
tabs.forEach((tab,index)=>{tab.addEventListener('click',()=>showView(tab.dataset.view));tab.addEventListener('keydown',(event)=>{if(!['ArrowRight','ArrowLeft'].includes(event.key))return;event.preventDefault();const step=event.key==='ArrowRight'?1:-1;const next=tabs[(index+step+tabs.length)%tabs.length];next.focus();showView(next.dataset.view);});});
board.querySelectorAll('[data-series]').forEach((button)=>button.addEventListener('click',()=>renderTrend(button.dataset.series)));
board.querySelector('[data-exposure-select]').addEventListener('change',(event)=>{board.querySelectorAll('[data-exposure]').forEach((row)=>{row.hidden=row.dataset.exposure!==event.target.value;});});
renderTrend('NDX/RUT');
</script>
</body>
</html>"""
