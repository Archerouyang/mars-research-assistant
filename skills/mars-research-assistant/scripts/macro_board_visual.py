#!/usr/bin/env python3
"""Macro Board visual adapter."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Any, Mapping

from board_visual_contract import BoardVisualError, exact_fields
from board_visual_shared import (
    _base_css,
    _num,
    _public_fixture_attr,
    _public_fixture_badge,
    _root_id,
    _script_json,
)


BOARD = "macro_regime"


def normalize(visual: Mapping[str, Any]) -> dict[str, Any]:
    exact_fields(visual, {"adapter", "snapshot", "default_view"}, "visual_fields_invalid")
    snapshot = visual.get("snapshot")
    if not isinstance(snapshot, Mapping) or snapshot.get("board") != BOARD:
        raise BoardVisualError("visual_snapshot_invalid")
    normalized = copy.deepcopy(dict(visual))
    normalized["snapshot"] = copy.deepcopy(dict(snapshot))
    normalized["default_view"] = str(normalized.get("default_view") or "Overview")
    return normalized


def render(visual: Mapping[str, Any], privacy: str) -> bytes:
    del privacy
    snapshot = visual["snapshot"]
    return _render_snapshot(snapshot)


def _render_snapshot(snapshot: Mapping[str, Any]) -> bytes:
    payload = snapshot["payload"]
    is_mars_direct = payload.get("macro_profile") == "mars_direct_v1"
    root = _root_id("macro", snapshot)
    fixture_badge = _public_fixture_badge(snapshot.get("privacy"))
    series = payload.get("chart_series") or []
    stats = _macro_summary_groups(series)
    trends = payload.get("trend_series") or []
    trend_buttons = "".join(
        f'<button type="button" class="btn{" btn-primary" if index == 0 else ""}" data-series="{escape(str(row["label"]))}" aria-pressed="{"true" if index == 0 else "false"}">{escape(str(row["label"]))}</button>'
        for index, row in enumerate(trends)
    ) or '<span class="text-muted text-small">趋势数据缺失</span>'
    preferences = payload.get("asset_preferences") or []
    if preferences:
        state_intro = (
            f'<div class="liquidity-note"><strong>流动性背景</strong><span>{escape(str(payload["liquidity_background"]))}</span></div>'
        )
        state_status = '<div class="evidence-strip text-small">' + "".join(
            f'<span>{escape(str(row["label"]))} · {escape(_status_zh(row["status"]))}</span>'
            for row in payload.get("evidence", [])
            if row.get("category") != "thesis"
        ) + "</div>"
        state_head = '<div class="preference-head"><span>资产</span><span>偏好</span><span>影响</span><span>风险</span></div>'
        state_rows = "".join(
            f'<article class="preference-row"><strong>{escape(str(row["segment"]))}</strong>'
            f'<span class="preference-bias {_bias_class(row["bias"])}">{escape(_bias_zh(row["bias"]))}</span>'
            f'<p><span class="mobile-label">影响</span>{escape(str(row["impact"]))}</p>'
            f'<p><span class="mobile-label">风险</span>{escape(str(row["watch"]))}</p></article>'
            for row in preferences
        )
    else:
        state_intro = ""
        state_status = ""
        state_head = ""
        state_rows = "".join(
            f'<article class="state-row"><div><strong>{escape(str(row["label"]))}</strong><span class="state-badge">{escape(_status_zh(row["status"]))}</span></div>'
            f'<p>{escape(str(row["reading"]))}</p><p>{escape(str(row["transmission"]))}</p></article>'
            for row in payload.get("evidence", [])
        )

    def event_html(row: Mapping[str, Any]) -> str:
        if is_mars_direct:
            optional = []
            if row["revised_previous"] is not None:
                optional.append(f'修正前值：{escape(str(row["revised_previous"]))}')
            if row["actual"] is not None:
                optional.append(f'实际：{escape(str(row["actual"]))}')
            detail = " · ".join(optional)
            return (
                '<article class="event-row"><div class="event-head"><div><strong>'
                f'{escape(str(row["title"]))}</strong></div>'
                f'<span>{escape(_format_event_time(row["time"]))}</span></div>'
                f'<p class="event-meta">{escape(str(row["category"]))} · '
                f'{escape(str(row["timezone"]))} · 参考期：{escape(str(row["reference_period"]))}</p>'
                f'<p><b>共识：</b>{escape(str(row["consensus"]))} · '
                f'<b>前值：</b>{escape(str(row["previous"]))}'
                f'{" · " + detail if detail else ""}</p></article>'
            )
        important = row.get("importance") == "high"
        marker = '<span class="event-priority">重点</span>' if important else ""
        css_class = " event-high" if important else ""
        return (
            f'<article class="event-row{css_class}"><div class="event-head"><div><strong>{escape(str(row["event"]))}</strong>{marker}</div>'
            f'<span>{escape(_format_event_time(row["time"]))}</span></div>'
            f'<p><b>作用：</b>{escape(str(row["why_it_matters"]))}</p><p><b>观察：</b>{escape(str(row["watch"]))}</p>'
            f'<div class="event-branches"><span><b>偏紧：</b>{escape(str(row["if_hot"]))}</span><span><b>偏松：</b>{escape(str(row["if_cool"]))}</span></div></article>'
        )

    event_watch = payload.get("event_watch")
    event_label = "未来七日事件" if is_mars_direct else "下周事件"
    event_empty = (
        "未来七日事件数据缺失，不能建立事件联动。"
        if is_mars_direct
        else "下周事件数据缺失，不能建立事件联动。"
    )
    event_rows = "".join(event_html(row) for row in event_watch or []) or (
        f'<p class="text-muted">{event_empty}</p>'
    )
    event_control = (
        f'<button type="button" class="btn" data-view="events" aria-pressed="false">{event_label}</button>'
        if event_watch is not None
        else ""
    )
    event_panel = (
        f'<section class="macro-panel" data-panel="events"><div class="event-list">{event_rows}</div></section>'
        if event_watch is not None
        else ""
    )
    policy_watch = payload.get("policy_watch")
    policy_rows = "".join(
        f'<article class="policy-row"><div class="policy-head"><strong>{escape(str(row["title"]))}</strong>'
        f'<span>{escape(_format_event_time(row["published_at"]))}</span></div>'
        f'<span class="policy-source">{escape(str(row.get("original_title", "")))}</span>'
        f'<span class="policy-source">{escape(str(row["source"]))}'
        f'{" · " + escape(str(row["policy_status"])) + " · " + escape(str(row["posture_effect"])) if is_mars_direct else ""}'
        '</span></article>'
        for row in policy_watch or []
    ) or '<p class="text-muted">本轮白宫直接来源未返回行政政策记录；不作政策推断。</p>'
    policy_control = (
        '<button type="button" class="btn" data-view="policy" aria-pressed="false">白宫政策</button>'
        if policy_watch is not None
        else ""
    )
    policy_panel = (
        f'<section class="macro-panel" data-panel="policy"><div class="policy-list">{policy_rows}</div></section>'
        if policy_watch is not None
        else ""
    )
    scenario_rows = "".join(
        f'<article class="scenario-row"><div class="scenario-name"><span class="scenario-rank">{index:02d}</span><strong>{escape(str(row["name"]))}</strong></div>'
        f'<div class="scenario-flow"><div><span class="scenario-cell-label">触发</span><p>{escape(str(row["trigger"]))}</p></div>'
        f'<div><span class="scenario-cell-label">确认</span><p>{escape(str(row["confirms"]))}</p></div>'
        f'<div><span class="scenario-cell-label">传导</span><p>{escape(str(row["cross_asset"]))}</p></div>'
        f'<div><span class="scenario-cell-label">应对</span><p>{escape(str(row["posture"]))}</p></div></div></article>'
        for index, row in enumerate(payload.get("scenarios", []), start=1)
    )
    timing = payload.get("market_timing") or {}
    evidence_groups = payload.get("evidence_groups") or []
    mars_current_context = ""
    mars_css = ""
    if is_mars_direct:
        group_rows = "".join(
            f'<article class="group-row group-{escape(str(row["status"]))}"><div><strong>{escape(str(row["label"]))}</strong>'
            f'<span>{escape(str(row["status"]))}</span></div><p>{escape(str(row["reason"]))}</p></article>'
            for row in evidence_groups
        )
        mars_current_context = (
            '<div class="market-timing text-small"><strong>市场数据口径</strong>'
            f'<span>最近共同完成收盘：{escape(str(timing.get("market_reference_date", "Unavailable")))}</span>'
            f'<span>盘中数据：{"排除" if timing.get("intraday_excluded") else "未声明"}</span>'
            f'<span>新闻/政策截止：{escape(str(timing.get("news_policy_cutoff", "Unavailable")))}</span>'
            f'<p>{escape(str(timing.get("lag_reason", "")))}</p></div>'
            f'<div class="group-list">{group_rows}</div>'
        )
        mars_css = "\n    ".join(
            (
                f"#{root} .event-meta{{color:var(--muted-foreground);font-size:12px}}",
                f"#{root} .market-timing{{display:flex;flex-wrap:wrap;gap:6px 14px;padding:10px 12px;border-left:3px solid var(--viz-series-1);background:var(--muted)}}",
                f"#{root} .market-timing p{{flex-basis:100%;margin:0}}",
                f"#{root} .group-list{{display:grid;border-top:1px solid var(--border)}}",
                f"#{root} .group-row{{display:grid;grid-template-columns:180px minmax(0,1fr);gap:12px;padding:10px 0;border-bottom:1px solid var(--border)}}",
                f"#{root} .group-row div{{display:grid;align-content:start;gap:4px}}",
                f"#{root} .group-row span{{font-size:12px;color:var(--muted-foreground)}}",
                f"#{root} .group-row p{{margin:0}}",
                f"#{root} .group-supports strong{{color:var(--viz-series-1)}}",
                f"#{root} .group-pressures strong{{color:var(--destructive)}}",
            )
        )
    data = _script_json({"trend_series": trends})
    html = f"""<div id="{root}" class="dt-board"{_public_fixture_attr(snapshot.get('privacy'))}>
  <style>{_base_css(root)}
    #{root} .decision-note{{padding:10px 12px;border-left:3px solid var(--viz-series-2);background:var(--muted)}}
    #{root} .macro-panel{{display:none;gap:12px}}
    #{root} .macro-panel.is-active{{display:grid}}
    #{root} .series-controls{{display:flex;flex-wrap:wrap;gap:6px}}
    #{root} .trend-chart{{width:100%;height:auto;min-height:260px}}
    #{root} .trend-grid{{stroke:var(--border);stroke-width:1}}
    #{root} .trend-line{{fill:none;stroke:var(--viz-series-1);stroke-width:3}}
    #{root} .trend-area{{fill:color-mix(in srgb,var(--viz-series-1) 12%,transparent)}}
    #{root} .trend-dot{{fill:var(--viz-series-1)}}
    #{root} .trend-axis{{fill:var(--muted-foreground);font-size:11px}}
    #{root} .trend-caption{{padding:9px 0;border-top:1px solid var(--border)}}
    #{root} .state-list,#{root} .event-list,#{root} .policy-list{{display:grid;gap:0;border-top:1px solid var(--border)}}
    #{root} .state-row{{display:grid;grid-template-columns:145px minmax(0,1fr) minmax(0,1fr);gap:12px;padding:11px 0;border-bottom:1px solid var(--border)}}
    #{root} .state-row p,#{root} .event-row p,#{root} .scenario-row p{{margin:0}}
    #{root} .state-badge{{display:block;margin-top:4px;color:var(--muted-foreground);font-size:12px}}
    #{root} .liquidity-note{{display:grid;grid-template-columns:118px minmax(0,1fr);gap:12px;padding:10px 12px;border-left:3px solid var(--viz-series-1);background:var(--muted)}}
    #{root} .evidence-strip{{display:flex;flex-wrap:wrap;gap:6px 14px;color:var(--muted-foreground)}}
    #{root} .preference-head,#{root} .preference-row{{display:grid;grid-template-columns:92px 72px minmax(0,1fr) minmax(0,1fr);gap:12px}}
    #{root} .preference-head{{padding:8px 0;color:var(--muted-foreground);font-weight:500;border-bottom:1px solid var(--border)}}
    #{root} .preference-row{{padding:10px 0;border-bottom:1px solid var(--border)}}
    #{root} .preference-row p{{margin:0}}
    #{root} .preference-bias{{font-weight:650}}
    #{root} .bias-positive{{color:var(--viz-series-1)}}
    #{root} .bias-negative{{color:var(--destructive)}}
    #{root} .bias-neutral{{color:var(--muted-foreground)}}
    #{root} .mobile-label{{display:none;color:var(--muted-foreground);font-weight:500}}
    #{root} .event-row{{display:grid;gap:8px;padding:12px 0;border-bottom:1px solid var(--border)}}
    #{root} .event-high{{padding-left:10px;border-left:3px solid var(--destructive)}}
    #{root} .event-head{{display:flex;justify-content:space-between;gap:12px}}
    #{root} .event-head>div{{display:flex;align-items:center;gap:8px}}
    #{root} .event-head span{{color:var(--muted-foreground);font-size:12px}}
    #{root} .event-head .event-priority{{color:var(--destructive);font-weight:650}}
    #{root} .event-branches{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
    #{root} .event-branches span{{padding:8px;background:var(--muted)}}
    #{root} .policy-row{{display:grid;gap:7px;padding:12px 0;border-bottom:1px solid var(--border)}}
    #{root} .policy-head{{display:flex;justify-content:space-between;gap:12px}}
    #{root} .policy-head span,#{root} .policy-source{{color:var(--muted-foreground);font-size:12px}}
    {mars_css}
    #{root} .macro-summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));border-block:1px solid var(--border)}}
    #{root} .macro-summary-group{{display:grid;align-content:start;gap:7px;padding:12px 14px}}
    #{root} .macro-summary-group+ .macro-summary-group{{border-left:1px solid var(--border)}}
    #{root} .macro-summary-label{{color:var(--muted-foreground);font-weight:500}}
    #{root} .macro-summary-values{{display:flex;flex-wrap:wrap;gap:6px 14px;font-variant-numeric:tabular-nums}}
    #{root} .macro-summary-values span{{display:inline-flex;align-items:baseline;gap:4px;white-space:nowrap}}
    #{root} .macro-summary-key{{color:var(--muted-foreground)}}
    #{root} .macro-summary-values b{{font-weight:650}}
    #{root} .scenario-grid{{display:grid;border-top:1px solid var(--border)}}
    #{root} .scenario-head{{display:grid;grid-template-columns:minmax(118px,.24fr) minmax(0,1fr);gap:16px;padding:8px 0;border-bottom:1px solid var(--border);color:var(--muted-foreground);font-weight:500}}
    #{root} .scenario-head-flow{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}}
    #{root} .scenario-row{{display:grid;grid-template-columns:minmax(118px,.24fr) minmax(0,1fr);gap:16px;padding:14px 0;border-bottom:1px solid var(--border)}}
    #{root} .scenario-name{{display:flex;align-items:flex-start;gap:9px}}
    #{root} .scenario-rank{{color:var(--muted-foreground);font-variant-numeric:tabular-nums}}
    #{root} .scenario-flow{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}}
    #{root} .scenario-flow>div{{display:grid;align-content:start;gap:5px}}
    #{root} .scenario-cell-label{{display:none;color:var(--muted-foreground);font-weight:500}}
    @media(max-width:640px){{#{root} .macro-summary{{grid-template-columns:1fr}}#{root} .macro-summary-group+ .macro-summary-group{{border-left:0;border-top:1px solid var(--border)}}#{root} .preference-head{{display:none}}#{root} .preference-row{{grid-template-columns:92px 1fr}}#{root} .preference-row p{{grid-column:1/-1}}#{root} .mobile-label{{display:block}}#{root} .scenario-head{{display:none}}#{root} .scenario-row{{grid-template-columns:1fr}}#{root} .scenario-flow{{grid-template-columns:1fr 1fr}}#{root} .scenario-cell-label{{display:block}}}}
    @media(max-width:420px){{#{root} .state-row,#{root} .liquidity-note{{grid-template-columns:1fr}}#{root} .event-branches,#{root} .scenario-flow{{grid-template-columns:1fr}}#{root} .event-head{{display:grid}}}}
  </style>
  <div class="viz-row text-small">{fixture_badge}<span class="viz-badge">{escape(str(payload['posture']['label']))}</span><span>证据 {snapshot['coverage']['required_complete']}/{snapshot['coverage']['required_total']}</span><span class="text-muted">截至 {escape(str(snapshot['decision_cutoff']))}</span></div>
  <div class="macro-summary">{stats}</div>
  <div class="decision-note text-small"><strong>当前判断：</strong>{escape(str(payload['decision']))}</div>
  <div class="viz-controls" aria-label="宏观视图">
    <button type="button" class="btn btn-primary" data-view="trend" aria-pressed="true">趋势</button>
    <button type="button" class="btn" data-view="current" aria-pressed="false">当前状态</button>
    {event_control}
    {policy_control}
    <button type="button" class="btn" data-view="scenarios" aria-pressed="false">情景</button>
  </div>
  <section class="macro-panel is-active" data-panel="trend"><div class="series-controls" aria-label="趋势序列">{trend_buttons}</div><svg class="trend-chart" viewBox="0 0 720 300" role="img" aria-label="关键宏观指标趋势"><g class="trend-stage"></g></svg><div class="trend-caption text-small" aria-live="polite"></div></section>
  <section class="macro-panel" data-panel="current">{mars_current_context}{state_intro}{state_status}<div class="state-list">{state_head}{state_rows}</div></section>
  {event_panel}
  {policy_panel}
  <section class="macro-panel" data-panel="scenarios"><div class="scenario-grid"><div class="scenario-head"><span>情景（按冲击排序）</span><div class="scenario-head-flow"><span>触发</span><span>确认</span><span>传导</span><span>应对</span></div></div>{scenario_rows}</div></section>
  <script>(()=>{{const root=document.getElementById('{root}');const data={data};const svg=root.querySelector('.trend-chart');const stage=root.querySelector('.trend-stage');const caption=root.querySelector('.trend-caption');const ns='http://www.w3.org/2000/svg';const W=720,H=300,left=48,right=20,top=16,bottom=34;function add(tag,attrs,text){{const el=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));if(text!==undefined)el.textContent=text;stage.appendChild(el);return el;}}function fmt(value,unit){{const n=Number(value).toLocaleString('zh-CN',{{maximumFractionDigits:2}});return unit==='percent'?n+'%':n;}}function renderTrend(label){{const series=data.trend_series.find(item=>item.label===label)||data.trend_series[0];stage.replaceChildren();if(!series||series.points.length<2){{caption.textContent='趋势数据不足，不能判断方向。';return;}}const values=series.points.map(p=>+p.value);let lo=Math.min(...values),hi=Math.max(...values);const pad=Math.max((hi-lo)*.15,Math.abs(hi)*.005,.01);lo-=pad;hi+=pad;const x=i=>left+i*(W-left-right)/Math.max(1,values.length-1);const y=v=>top+(hi-v)*(H-top-bottom)/(hi-lo);for(let i=0;i<4;i++){{const value=lo+(hi-lo)*i/3;add('line',{{x1:left,y1:y(value),x2:W-right,y2:y(value),class:'trend-grid'}});add('text',{{x:4,y:y(value)+4,class:'trend-axis'}},fmt(value,series.unit));}}const line=series.points.map((p,i)=>(i?'L':'M')+x(i).toFixed(1)+','+y(+p.value).toFixed(1)).join(' ');const area=line+' L'+x(values.length-1).toFixed(1)+','+(H-bottom)+' L'+left+','+(H-bottom)+' Z';add('path',{{d:area,class:'trend-area'}});add('path',{{d:line,class:'trend-line'}});series.points.forEach((p,i)=>add('circle',{{cx:x(i),cy:y(+p.value),r:i===series.points.length-1?5:2.5,class:'trend-dot'}}));add('text',{{x:left,y:H-10,class:'trend-axis'}},series.points[0].time.slice(5,10));add('text',{{x:W-right-34,y:H-10,class:'trend-axis'}},series.points[series.points.length-1].time.slice(5,10));const first=values[0],last=values[values.length-1],delta=last-first,pct=first===0?null:delta/Math.abs(first)*100;const arrow=delta>0?'↑':delta<0?'↓':'→';caption.textContent=series.label+' 当前 '+fmt(last,series.unit)+' · 区间 '+arrow+' '+fmt(Math.abs(delta),series.unit)+(pct===null?'':' ('+Math.abs(pct).toFixed(1)+'%)')+'。'+series.implication;root.querySelectorAll('[data-series]').forEach(btn=>{{const on=btn.dataset.series===series.label;btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('btn-primary',on);}});}}function show(view){{root.querySelectorAll('[data-panel]').forEach(panel=>panel.classList.toggle('is-active',panel.dataset.panel===view));root.querySelectorAll('[data-view]').forEach(btn=>{{const on=btn.dataset.view===view;btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('btn-primary',on);}});}}root.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>show(btn.dataset.view)));root.querySelectorAll('[data-series]').forEach(btn=>btn.addEventListener('click',()=>renderTrend(btn.dataset.series)));if(data.trend_series.length)renderTrend(data.trend_series[0].label);show('trend');}})();</script>
</div>
"""
    return html.encode("utf-8")


def _macro_summary_groups(series: list[Mapping[str, Any]]) -> str:
    by_label = {str(row["label"]).lower(): row for row in series}

    def value(label: str, suffix: str = "") -> str:
        row = by_label.get(label.lower())
        return f"{_num(row['value'])}{suffix}" if row is not None else "缺失"

    groups = (
        ("收益率曲线", (("2Y", value("2Y", "%")), ("10Y", value("10Y", "%")), ("30Y", value("30Y", "%")))),
        ("波动期限结构", (("VIX/VIX3M", value("VIX/VIX3M")),)),
        ("成长/小盘", (("NDX/RUT", value("NDX/RUT")), ("5D", value("NDX/RUT 5D", "%")), ("20D", value("NDX/RUT 20D", "%")))),
        ("流动性", (("准备金", value("准备金", "B")), ("TGA", value("TGA", "B")), ("ON RRP", value("ON RRP", "B")))),
    )

    def readings_html(readings: tuple[tuple[str, str], ...]) -> str:
        return "".join(
            f'<span><span class="macro-summary-key">{item}</span><b>{reading}</b></span>'
            for item, reading in readings
        )

    return "".join(
        f'<section class="macro-summary-group"><span class="macro-summary-label">{label}</span>'
        f'<div class="macro-summary-values">{readings_html(readings)}</div></section>'
        for label, readings in groups
    )


def _status_zh(status: Any) -> str:
    return {
        "verified": "已验证",
        "complete": "完整",
        "needs_check": "待核验",
        "lead": "线索",
        "plan_rule": "计划约束",
        "partial": "部分可用",
        "stale": "已过期",
        "source_error": "来源异常",
    }.get(str(status), str(status))


def _bias_zh(bias: Any) -> str:
    return {
        "overweight": "相对偏强",
        "neutral": "中性",
        "underweight": "相对偏弱",
    }.get(str(bias), str(bias))


def _bias_class(bias: Any) -> str:
    return {
        "overweight": "bias-positive",
        "underweight": "bias-negative",
    }.get(str(bias), "bias-neutral")


def _format_event_time(value: Any) -> str:
    try:
        observed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    china = observed.astimezone(timezone(timedelta(hours=8)))
    return china.strftime("%m-%d %H:%M CST")
