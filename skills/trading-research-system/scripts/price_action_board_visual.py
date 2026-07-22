#!/usr/bin/env python3
"""Price Action Board visual adapter."""

from __future__ import annotations

import copy
from html import escape
from typing import Any, Mapping

from chart_artifact import build_chart_payload
from board_visual_contract import BoardVisualError, exact_fields, required_text
from board_visual_shared import (
    _base_css,
    _latest_value,
    _num,
    _public_fixture_attr,
    _public_fixture_badge,
    _root_id,
    _script_json,
)


def normalize(visual: Mapping[str, Any]) -> dict[str, Any]:
    exact_fields(visual, {"adapter", "payload", "title"}, "visual_fields_invalid")
    raw_payload = visual.get("payload")
    if not isinstance(raw_payload, Mapping):
        raise BoardVisualError("visual_payload_invalid")
    normalized = copy.deepcopy(dict(visual))
    if "title" in normalized:
        normalized["title"] = str(normalized["title"])
    payload = copy.deepcopy(dict(raw_payload))
    _validate_payload(payload)
    try:
        normalized["payload"] = build_chart_payload(payload, normalized.get("title"))
    except SystemExit as error:
        raise BoardVisualError("visual_payload_invalid") from error
    return normalized


def render(visual: Mapping[str, Any], privacy: str) -> bytes:
    payload = copy.deepcopy(dict(visual["payload"]))
    payload["privacy"] = privacy
    return _render_payload(payload)


def _validate_payload(payload: Mapping[str, Any]) -> None:
    for key in (
        "ticker",
        "trade_horizon",
        "instrument",
        "primary_timeframe",
        "auxiliary_timeframes",
        "decision_summary",
        "structure_summary",
    ):
        required_text(payload, key)

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, Mapping) or set(scenarios) != {"bull", "base", "bear"}:
        raise BoardVisualError("price_action_scenarios_invalid")
    for row in scenarios.values():
        if not isinstance(row, Mapping) or set(row) != {"target", "condition", "path", "action"}:
            raise BoardVisualError("price_action_scenarios_invalid")
        for key in ("condition", "path", "action"):
            required_text(row, key)
        try:
            float(row["target"])
        except (TypeError, ValueError):
            raise BoardVisualError("price_action_scenarios_invalid") from None

    notes = payload.get("notes", [])
    if not isinstance(notes, list) or any(not isinstance(item, str) or not item.strip() for item in notes):
        raise BoardVisualError("visual_payload_invalid")

    daily = payload.get("daily_context", {})
    if not isinstance(daily, Mapping) or set(daily) - {"ema20", "ema50", "ema200"}:
        raise BoardVisualError("visual_payload_invalid")
    for value in daily.values():
        if value is not None:
            try:
                float(value)
            except (TypeError, ValueError):
                raise BoardVisualError("visual_payload_invalid") from None

    for key in ("atr14_primary", "atr14_4h"):
        if payload.get(key) is not None:
            try:
                float(payload[key])
            except (TypeError, ValueError):
                raise BoardVisualError("visual_payload_invalid") from None

    _validate_rows(
        payload.get("entry_plan", []),
        {"stage", "allocation", "condition", "invalidation"},
    )
    _validate_rows(
        payload.get("event_watch", []),
        {"time", "event", "importance", "transmission", "watch"},
    )
    if "event_note" in payload and not isinstance(payload["event_note"], str):
        raise BoardVisualError("visual_payload_invalid")


def _validate_rows(value: Any, fields: set[str]) -> None:
    if not isinstance(value, list):
        raise BoardVisualError("visual_payload_invalid")
    for row in value:
        if not isinstance(row, Mapping) or set(row) != fields:
            raise BoardVisualError("visual_payload_invalid")
        for key in fields:
            required_text(row, key)


def _render_payload(payload: Mapping[str, Any]) -> bytes:
    root = _root_id("price-action", payload)
    candles = payload["candles"]
    latest = candles[-1]
    ema20 = _latest_value(payload.get("ema20"))
    ema50 = _latest_value(payload.get("ema50"))
    levels = payload.get("levels") or []
    zones = payload.get("zones") or []
    notes = payload.get("notes") or []
    scenarios = payload.get("scenarios") or {}
    entry_plan = payload.get("entry_plan") or []
    daily = payload.get("daily_context") or {}
    primary = str(payload.get("primary_timeframe") or "主周期未标注")
    auxiliary = str(payload.get("auxiliary_timeframes") or "辅助周期未标注")
    decision_summary = str(payload.get("decision_summary") or "等待价格结构确认。")
    structure_summary = str(payload.get("structure_summary") or "当前结构信息不足。")
    event_note = str(payload.get("event_note") or "")
    latest_close = float(latest["close"])
    supplied_emas = [
        value
        for value in (ema20, ema50, daily.get("ema20"), daily.get("ema50"), daily.get("ema200"))
        if value is not None
    ]
    if not supplied_emas:
        price_context = "均线位置不可判定"
    elif latest_close > max(float(value) for value in supplied_emas):
        price_context = "高于已提供均线"
    elif latest_close < min(float(value) for value in supplied_emas):
        price_context = "低于已提供均线"
    else:
        price_context = "位于已提供均线之间"
    if ema20 is None or ema50 is None:
        primary_context = f"{primary}均线结构不完整"
    elif ema20 > ema50:
        primary_context = "EMA20高于EMA50"
    elif ema20 < ema50:
        primary_context = "EMA20低于EMA50"
    else:
        primary_context = "EMA20与EMA50重合"
    atr14 = payload.get("atr14_primary")
    if atr14 is None:
        atr14 = payload.get("atr14_4h")
    atr_context = (
        "波动尺度，不替代结构失效位"
        if atr14 is not None
        else "波动数据缺失"
    )
    ladder_rows = [dict(row) for row in levels[:6]]
    ladder_rows.append({"label": "当前价格", "price": latest_close, "kind": "最新收盘", "current": True})
    ladder_rows.sort(key=lambda row: float(row["price"]), reverse=True)
    level_ladder = "".join(
        f'<div class="level-row {"level-current" if row.get("current") else "level-above" if float(row["price"]) > latest_close else "level-below"}">'
        f'<b class="level-price">{_num(row["price"])}</b><div><strong>{escape(str(row["label"]))}</strong>'
        f'<span>{escape(str(row["kind"]))}</span></div><em>{(float(row["price"]) / latest_close - 1) * 100:+.1f}%</em></div>'
        for row in ladder_rows
    ) or '<p class="text-muted">关键位尚未定义</p>'
    notes_html = "".join(
        f'<p><span>{index:02d}</span>{escape(str(item))}</p>'
        for index, item in enumerate(notes[:4], start=1)
    )
    entry_rows = "".join(
        f'<div class="entry-row"><span class="step-index">{index:02d}</span><div class="entry-copy">'
        f'<div><strong>{escape(str(row.get("stage") or "阶段"))}</strong><b>{escape(str(row.get("allocation") or ""))}</b></div>'
        f'<p>{escape(str(row.get("condition") or ""))}</p>'
        f'<small>失效：{escape(str(row.get("invalidation") or "未定义"))}</small></div></div>'
        for index, row in enumerate(entry_plan[:4], start=1)
    )
    event_rows = "".join(
        f'<article class="pa-event{" event-high" if row.get("importance") == "high" else ""}">'
        f'<time>{escape(str(row.get("time") or "待确认"))}</time><div><div class="event-title"><strong>{escape(str(row.get("event") or "事件"))}</strong>'
        f'{"<span>重点</span>" if row.get("importance") == "high" else ""}</div>'
        f'<p>{escape(str(row.get("transmission") or ""))}</p><small>观察：{escape(str(row.get("watch") or "未定义"))}</small></div></article>'
        for row in (payload.get("event_watch") or [])[:4]
    )
    event_note_html = f'<p class="event-note">{escape(event_note)}</p>' if event_note else ""
    scenario_payload = {
        name: {
            "target": row.get("target"),
            "description": str(row.get("description") or ""),
            "condition": str(row.get("condition") or ""),
            "path": str(row.get("path") or ""),
            "action": str(row.get("action") or ""),
        }
        for name, row in scenarios.items()
        if name in {"bull", "base", "bear"} and isinstance(row, Mapping)
    }
    data = _script_json(
        {
            "candles": candles,
            "ema20": payload.get("ema20") or [],
            "ema50": payload.get("ema50") or [],
            "levels": levels,
            "zones": zones,
            "scenarios": scenario_payload,
        }
    )
    html = f"""<div id="{root}" class="dt-board"{_public_fixture_attr(payload.get('privacy'))}>
  <style>{_base_css(root)}
    #{root} .pa-chart{{width:100%;height:auto}}
    #{root} .grid{{stroke:var(--border);stroke-width:1}}
    #{root} .axis{{fill:var(--muted-foreground);font-size:11px}}
    #{root} .wick{{stroke:var(--muted-foreground);stroke-width:1}}
    #{root} .up{{fill:var(--viz-series-1)}}
    #{root} .down{{fill:var(--destructive)}}
    #{root} .ema20{{fill:none;stroke:var(--viz-series-2);stroke-width:2}}
    #{root} .ema50{{fill:none;stroke:var(--viz-series-3);stroke-width:2}}
    #{root} .level{{stroke:var(--border);stroke-width:1;stroke-dasharray:4 4}}
    #{root} .scenario{{fill:none;stroke:var(--viz-series-1);stroke-width:3}}
    #{root} .scenario-dot{{fill:var(--viz-series-1)}}
    #{root} .zone{{fill:color-mix(in srgb,var(--viz-series-2) 13%,transparent)}}
    #{root} .pa-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}}
    #{root} .pa-meta{{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:5px 12px;color:var(--muted-foreground)}}
    #{root} .decision-band{{display:grid;grid-template-columns:92px minmax(0,1fr);gap:5px 14px;padding:11px 0;border-block:1px solid var(--border)}}
    #{root} .decision-band>span{{grid-row:1/3;color:var(--viz-series-1);font-size:12px;font-weight:650}}
    #{root} .decision-band strong{{font-size:15px}}
    #{root} .decision-band p{{margin:0;color:var(--muted-foreground)}}
    #{root} .metric-strip{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-bottom:1px solid var(--border)}}
    #{root} .metric{{display:grid;gap:3px;padding:9px 12px 11px 0;border-right:1px solid var(--border)}}
    #{root} .metric+ .metric{{padding-left:12px}}
    #{root} .metric:last-child{{border-right:0}}
    #{root} .metric span,#{root} .metric small{{color:var(--muted-foreground)}}
    #{root} .metric b{{font-size:17px;font-variant-numeric:tabular-nums}}
    #{root} .scenario-detail{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border-block:1px solid var(--border)}}
    #{root} .scenario-detail>div{{display:grid;gap:4px;padding:9px 12px 10px 0}}
    #{root} .scenario-detail>div+div{{padding-left:12px;border-left:1px solid var(--border)}}
    #{root} .scenario-detail span{{color:var(--muted-foreground);font-size:12px}}
    #{root} .scenario-detail p{{margin:0}}
    #{root} .entry-plan{{display:grid;border-top:1px solid var(--border)}}
    #{root} .entry-row{{display:grid;grid-template-columns:34px minmax(0,1fr);gap:10px;padding:10px 0;border-bottom:1px solid var(--border)}}
    #{root} .step-index{{color:var(--viz-series-1);font-weight:650}}
    #{root} .entry-copy{{display:grid;gap:4px}}
    #{root} .entry-copy>div{{display:flex;align-items:center;gap:8px}}
    #{root} .entry-copy b{{color:var(--viz-series-1)}}
    #{root} .entry-copy p{{margin:0}}
    #{root} .entry-copy small{{color:var(--muted-foreground)}}
    #{root} .level-ladder{{display:grid;border-top:1px solid var(--border)}}
    #{root} .level-row{{display:grid;grid-template-columns:72px minmax(0,1fr) 58px;gap:12px;align-items:center;padding:9px 10px;border-bottom:1px solid var(--border);border-left:3px solid transparent}}
    #{root} .level-row>div{{display:grid;gap:2px}}
    #{root} .level-row span{{color:var(--muted-foreground);font-size:12px}}
    #{root} .level-price{{font-size:16px;font-variant-numeric:tabular-nums}}
    #{root} .level-row em{{text-align:right;font-style:normal;font-variant-numeric:tabular-nums}}
    #{root} .level-above{{border-left-color:var(--viz-series-1)}}
    #{root} .level-below{{border-left-color:var(--destructive)}}
    #{root} .level-current{{border-left-color:var(--viz-series-2);background:var(--muted)}}
    #{root} .event-list{{display:grid;border-top:1px solid var(--border)}}
    #{root} .pa-event{{display:grid;grid-template-columns:126px minmax(0,1fr);gap:12px;padding:10px 0;border-bottom:1px solid var(--border)}}
    #{root} .pa-event time{{color:var(--muted-foreground);font-variant-numeric:tabular-nums}}
    #{root} .pa-event p{{margin:3px 0}}
    #{root} .pa-event small{{color:var(--muted-foreground)}}
    #{root} .event-high{{padding-left:9px;border-left:3px solid var(--destructive)}}
    #{root} .event-title{{display:flex;align-items:center;gap:8px}}
    #{root} .event-title span{{color:var(--destructive);font-size:11px;font-weight:650}}
    #{root} .event-note{{margin:0;padding:9px 0;color:var(--muted-foreground);border-bottom:1px solid var(--border)}}
    #{root} .data-notes{{border-top:1px solid var(--border);padding-top:8px}}
    #{root} .data-notes summary{{cursor:pointer;color:var(--muted-foreground);font-size:12px}}
    #{root} .note-list{{display:grid;gap:5px;padding-top:8px}}
    #{root} .note-list p{{display:grid;grid-template-columns:26px minmax(0,1fr);gap:7px;margin:0;color:var(--muted-foreground);font-size:12px}}
    #{root} .note-list span{{color:var(--viz-series-1);font-weight:650}}
    @media(max-width:640px){{#{root} .pa-head{{display:grid}}#{root} .pa-meta{{justify-content:flex-start}}#{root} .metric-strip{{grid-template-columns:1fr 1fr}}#{root} .metric:nth-child(2){{border-right:0}}#{root} .scenario-detail{{grid-template-columns:1fr}}#{root} .scenario-detail>div+div{{padding-left:0;border-left:0;border-top:1px solid var(--border)}}#{root} .pa-event{{grid-template-columns:1fr;gap:3px}}}}
  </style>
  <div class="pa-head">
    <div class="viz-row text-small">{_public_fixture_badge(payload.get('privacy'))}<span class="viz-badge">{escape(str(payload.get('setup_status') or 'watch'))}</span><strong>{escape(str(payload.get('ticker') or payload.get('symbol')))}</strong></div>
    <div class="pa-meta text-small"><span>持有周期 {escape(str(payload.get('trade_horizon')))}</span><span>工具 {escape(str(payload.get('instrument')))}</span><span>主周期 {escape(primary)}</span><span>辅助周期 {escape(auxiliary)}</span><span>截至 {escape(str(payload.get('data_as_of') or latest['time']))}</span><span>{escape(str(payload.get('source') or '数据源未标注'))}</span></div>
  </div>
  <div class="decision-band"><span>当前判断</span><strong>{escape(decision_summary)}</strong><p>{escape(structure_summary)}</p></div>
  <div class="metric-strip">
    <div class="metric"><span>最新价格</span><b>{_num(latest['close'])}</b><small>{escape(price_context)}</small></div>
    <div class="metric"><span>{escape(primary)} EMA20 / 50</span><b>{_num(ema20) if ema20 is not None else 'n/a'} / {_num(ema50) if ema50 is not None else 'n/a'}</b><small>{escape(primary_context)}</small></div>
    <div class="metric"><span>1D EMA20 / 50</span><b>{_num(daily.get('ema20')) if daily.get('ema20') is not None else 'n/a'} / {_num(daily.get('ema50')) if daily.get('ema50') is not None else 'n/a'}</b><small>EMA200 {_num(daily.get('ema200')) if daily.get('ema200') is not None else 'n/a'}</small></div>
    <div class="metric"><span>{escape(primary)} ATR14</span><b>{_num(atr14) if atr14 is not None else 'n/a'}</b><small>{escape(atr_context)}</small></div>
  </div>
  <div class="viz-controls" aria-label="情景路径">
    <button type="button" class="btn" data-scenario="bull" aria-pressed="false">转强</button>
    <button type="button" class="btn btn-primary" data-scenario="base" aria-pressed="true">整理</button>
    <button type="button" class="btn" data-scenario="bear" aria-pressed="false">转弱</button>
  </div>
  <div class="scenario-detail text-small" aria-live="polite">
    <div><span>触发</span><p data-scenario-copy="condition"></p></div>
    <div><span>路径</span><p data-scenario-copy="path"></p></div>
    <div><span>动作</span><p data-scenario-copy="action"></p></div>
  </div>
  <svg class="pa-chart" viewBox="0 0 720 360" role="img" aria-label="价格、均线、关键位与条件路径"><g class="pa-stage"></g></svg>
  <h3>关键位</h3><div class="level-ladder">{level_ladder}</div>
  {f'<h3>分段建仓</h3><div class="entry-plan">{entry_rows}</div>' if entry_rows else ''}
  {f'<h3>下周公司与产业链事件</h3><div class="event-list">{event_rows}</div>{event_note_html}' if event_rows else ''}
  {f'<details class="data-notes"><summary>数据口径与事件边界</summary><div class="note-list">{notes_html}</div></details>' if notes_html else ''}
  <script>(()=>{{
    const root=document.getElementById('{root}');
    const data={data};
    const g=root.querySelector('.pa-stage');
    const ns='http://www.w3.org/2000/svg';
    const W=720,H=360,left=44,right=112,top=14,bottom=30;
    const prices=data.candles.flatMap(d=>[+d.low,+d.high]).concat(data.levels.map(d=>+d.price),data.zones.flatMap(d=>[+d.low,+d.high]));
    let lo=Math.min(...prices),hi=Math.max(...prices);const pad=Math.max((hi-lo)*.08,.01);lo-=pad;hi+=pad;
    const candleEnd=540,pw=candleEnd-left,ph=H-top-bottom;
    const x=i=>left+i*pw/Math.max(1,data.candles.length-1);const y=v=>top+(hi-v)*ph/(hi-lo);
    const add=(tag,attrs,text)=>{{const el=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));if(text!==undefined)el.textContent=text;g.appendChild(el);return el;}};
    for(let i=0;i<5;i++){{const v=lo+(hi-lo)*i/4;add('line',{{x1:left,y1:y(v),x2:W-right,y2:y(v),class:'grid'}});add('text',{{x:4,y:y(v)+4,class:'axis'}},v.toFixed(2));}}
    data.zones.forEach(z=>add('rect',{{x:left,y:y(+z.high),width:pw,height:Math.max(1,y(+z.low)-y(+z.high)),class:'zone'}}));
    data.levels.forEach(d=>{{add('line',{{x1:left,y1:y(+d.price),x2:W-right,y2:y(+d.price),class:'level'}});add('text',{{x:W-right+6,y:y(+d.price)+4,class:'axis'}},String(d.label));}});
    const cw=Math.max(3,pw/data.candles.length*.55);
    data.candles.forEach((d,i)=>{{const xx=x(i),o=+d.open,h=+d.high,l=+d.low,c=+d.close;add('line',{{x1:xx,y1:y(h),x2:xx,y2:y(l),class:'wick'}});add('rect',{{x:xx-cw/2,y:y(Math.max(o,c)),width:cw,height:Math.max(1,Math.abs(y(o)-y(c))),class:c>=o?'up':'down'}});}});
    const overlay=(points,cls)=>{{if(!points.length)return;const byTime=new Map(data.candles.map((d,i)=>[String(d.time),i]));const usable=points.filter(p=>byTime.has(String(p.time)));if(!usable.length)return;add('path',{{d:usable.map((p,i)=>(i?'L':'M')+x(byTime.get(String(p.time))).toFixed(1)+','+y(+p.value).toFixed(1)).join(' '),class:cls}});}};
    overlay(data.ema20,'ema20');overlay(data.ema50,'ema50');
    const last=+data.candles[data.candles.length-1].close;
    const targets=Object.fromEntries(Object.entries(data.scenarios).map(([name,row])=>[name,Number(row.target)]));
    const scenarioCopy=data.scenarios;
    const path=add('path',{{class:'scenario',d:''}});const dots=add('g',{{}});const sx=[candleEnd,582,625,668];
    function select(name){{const target=targets[name],mid=(last+target)/2;const values=[last,mid,target,target];path.setAttribute('d',values.map((v,i)=>(i?'L':'M')+sx[i]+','+y(v)).join(' '));dots.replaceChildren();values.forEach((v,i)=>{{const c=document.createElementNS(ns,'circle');c.setAttribute('cx',sx[i]);c.setAttribute('cy',y(v));c.setAttribute('r','4');c.setAttribute('class','scenario-dot');dots.appendChild(c);}});Object.entries(scenarioCopy[name]).forEach(([key,value])=>{{root.querySelector(`[data-scenario-copy="${{key}}"]`).textContent=value;}});root.querySelectorAll('[data-scenario]').forEach(btn=>{{const on=btn.dataset.scenario===name;btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('btn-primary',on);}});}}
    root.querySelectorAll('[data-scenario]').forEach(btn=>btn.addEventListener('click',()=>select(btn.dataset.scenario)));select('base');
  }})();</script>
</div>
"""
    return html.encode("utf-8")
