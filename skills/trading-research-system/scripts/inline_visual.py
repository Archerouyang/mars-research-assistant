#!/usr/bin/env python3
"""Compact Codex-native research visuals.

These renderers intentionally produce HTML fragments, not standalone documents.
The canonical ArtifactPacket renderers remain the offline Board implementation.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from html import escape
import json
from typing import Any, Mapping


def render_board_fragment(adapter: str, snapshot: Mapping[str, Any]) -> bytes:
    if adapter == "macro":
        return _macro(snapshot)
    if adapter == "portfolio":
        return _portfolio(snapshot)
    if adapter == "instrument":
        return _instrument(snapshot)
    raise ValueError("inline_adapter_invalid")


def render_price_action_fragment(payload: Mapping[str, Any]) -> bytes:
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
    html = f"""<div id="{root}" class="dt-inline"{_public_fixture_attr(payload.get('privacy'))}>
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


def _macro(snapshot: Mapping[str, Any]) -> bytes:
    payload = snapshot["payload"]
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
        important = row.get("importance") == "high"
        marker = '<span class="event-priority">重点</span>' if important else ""
        css_class = " event-high" if important else ""
        return (
            f'<article class="event-row{css_class}"><div class="event-head"><div><strong>{escape(str(row["event"]))}</strong>{marker}</div>'
            f'<span>{escape(_format_event_time(row["time"]))}</span></div>'
            f'<p><b>作用：</b>{escape(str(row["why_it_matters"]))}</p><p><b>观察：</b>{escape(str(row["watch"]))}</p>'
            f'<div class="event-branches"><span><b>偏紧：</b>{escape(str(row["if_hot"]))}</span><span><b>偏松：</b>{escape(str(row["if_cool"]))}</span></div></article>'
        )

    event_rows = "".join(event_html(row) for row in payload.get("event_watch", [])) or (
        '<p class="text-muted">下周事件数据缺失，不能建立事件联动。</p>'
    )
    scenario_rows = "".join(
        f'<article class="scenario-row"><div class="scenario-name"><span class="scenario-rank">{index:02d}</span><strong>{escape(str(row["name"]))}</strong></div>'
        f'<div class="scenario-flow"><div><span class="scenario-cell-label">触发</span><p>{escape(str(row["trigger"]))}</p></div>'
        f'<div><span class="scenario-cell-label">确认</span><p>{escape(str(row["confirms"]))}</p></div>'
        f'<div><span class="scenario-cell-label">传导</span><p>{escape(str(row["cross_asset"]))}</p></div>'
        f'<div><span class="scenario-cell-label">应对</span><p>{escape(str(row["posture"]))}</p></div></div></article>'
        for index, row in enumerate(payload.get("scenarios", []), start=1)
    )
    data = _script_json({"trend_series": trends})
    html = f"""<div id="{root}" class="dt-inline"{_public_fixture_attr(snapshot.get('privacy'))}>
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
    #{root} .state-list,#{root} .event-list{{display:grid;gap:0;border-top:1px solid var(--border)}}
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
    #{root} .macro-summary{{display:grid;grid-template-columns:1.2fr 1fr 1fr;border-block:1px solid var(--border)}}
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
    <button type="button" class="btn" data-view="events" aria-pressed="false">下周事件</button>
    <button type="button" class="btn" data-view="scenarios" aria-pressed="false">情景</button>
  </div>
  <section class="macro-panel is-active" data-panel="trend"><div class="series-controls" aria-label="趋势序列">{trend_buttons}</div><svg class="trend-chart" viewBox="0 0 720 300" role="img" aria-label="关键宏观指标趋势"><g class="trend-stage"></g></svg><div class="trend-caption text-small" aria-live="polite"></div></section>
  <section class="macro-panel" data-panel="current">{state_intro}{state_status}<div class="state-list">{state_head}{state_rows}</div></section>
  <section class="macro-panel" data-panel="events"><div class="event-list">{event_rows}</div></section>
  <section class="macro-panel" data-panel="scenarios"><div class="scenario-grid"><div class="scenario-head"><span>情景（按冲击排序）</span><div class="scenario-head-flow"><span>触发</span><span>确认</span><span>传导</span><span>应对</span></div></div>{scenario_rows}</div></section>
  <script>(()=>{{const root=document.getElementById('{root}');const data={data};const svg=root.querySelector('.trend-chart');const stage=root.querySelector('.trend-stage');const caption=root.querySelector('.trend-caption');const ns='http://www.w3.org/2000/svg';const W=720,H=300,left=48,right=20,top=16,bottom=34;function add(tag,attrs,text){{const el=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));if(text!==undefined)el.textContent=text;stage.appendChild(el);return el;}}function fmt(value,unit){{const n=Number(value).toLocaleString('zh-CN',{{maximumFractionDigits:2}});return unit==='percent'?n+'%':n;}}function renderTrend(label){{const series=data.trend_series.find(item=>item.label===label)||data.trend_series[0];stage.replaceChildren();if(!series||series.points.length<2){{caption.textContent='趋势数据不足，不能判断方向。';return;}}const values=series.points.map(p=>+p.value);let lo=Math.min(...values),hi=Math.max(...values);const pad=Math.max((hi-lo)*.15,Math.abs(hi)*.005,.01);lo-=pad;hi+=pad;const x=i=>left+i*(W-left-right)/Math.max(1,values.length-1);const y=v=>top+(hi-v)*(H-top-bottom)/(hi-lo);for(let i=0;i<4;i++){{const value=lo+(hi-lo)*i/3;add('line',{{x1:left,y1:y(value),x2:W-right,y2:y(value),class:'trend-grid'}});add('text',{{x:4,y:y(value)+4,class:'trend-axis'}},fmt(value,series.unit));}}const line=series.points.map((p,i)=>(i?'L':'M')+x(i).toFixed(1)+','+y(+p.value).toFixed(1)).join(' ');const area=line+' L'+x(values.length-1).toFixed(1)+','+(H-bottom)+' L'+left+','+(H-bottom)+' Z';add('path',{{d:area,class:'trend-area'}});add('path',{{d:line,class:'trend-line'}});series.points.forEach((p,i)=>add('circle',{{cx:x(i),cy:y(+p.value),r:i===series.points.length-1?5:2.5,class:'trend-dot'}}));add('text',{{x:left,y:H-10,class:'trend-axis'}},series.points[0].time.slice(5,10));add('text',{{x:W-right-34,y:H-10,class:'trend-axis'}},series.points[series.points.length-1].time.slice(5,10));const first=values[0],last=values[values.length-1],delta=last-first,pct=first===0?null:delta/Math.abs(first)*100;const arrow=delta>0?'↑':delta<0?'↓':'→';caption.textContent=series.label+' 当前 '+fmt(last,series.unit)+' · 区间 '+arrow+' '+fmt(Math.abs(delta),series.unit)+(pct===null?'':' ('+Math.abs(pct).toFixed(1)+'%)')+'。'+series.implication;root.querySelectorAll('[data-series]').forEach(btn=>{{const on=btn.dataset.series===series.label;btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('btn-primary',on);}});}}function show(view){{root.querySelectorAll('[data-panel]').forEach(panel=>panel.classList.toggle('is-active',panel.dataset.panel===view));root.querySelectorAll('[data-view]').forEach(btn=>{{const on=btn.dataset.view===view;btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('btn-primary',on);}});}}root.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>show(btn.dataset.view)));root.querySelectorAll('[data-series]').forEach(btn=>btn.addEventListener('click',()=>renderTrend(btn.dataset.series)));if(data.trend_series.length)renderTrend(data.trend_series[0].label);show('trend');}})();</script>
</div>
"""
    return html.encode("utf-8")


def _portfolio(snapshot: Mapping[str, Any]) -> bytes:
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
    html = f"""<div id="{root}" class="dt-inline"{_public_fixture_attr(snapshot.get('privacy'))}>
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


def _instrument(snapshot: Mapping[str, Any]) -> bytes:
    payload = snapshot["payload"]
    root = _root_id("instrument", snapshot)
    subject = payload["subject"]
    modules = [
        {"label": row["id"].replace("_", " ").title(), "value": row["summary"], "meta": row["evidence_state"]}
        for row in payload.get("modules", [])
    ]
    peers = [
        {"label": row["symbol"], "value": f"Revenue {row['revenue_growth_pct']}% · GM {row['gross_margin_pct']}%", "meta": row["status"]}
        for row in payload.get("peers", [])
    ]
    events = [
        {"label": row["catalyst"], "value": row["expected_evidence"], "meta": row["status"]}
        for row in payload.get("event_transmission", [])
    ]
    price = payload.get("price_setup") or {}
    rows = "".join(_bar_row(row["label"], 100 - index * 12, index + 1, row["meta"]) for index, row in enumerate(modules))
    data = _script_json({"overview": modules, "peers": peers, "catalysts": events})
    price_data = _script_json({"candles": price.get("candles") or [], "overlays": price.get("overlays") or []})
    html = f"""<div id="{root}" class="dt-inline"{_public_fixture_attr(snapshot.get('privacy'))}>
  <style>{_base_css(root)}
    #{root} .price-plot{{display:none;width:100%;height:auto}}
    #{root} .price-plot.is-visible{{display:block}}
    #{root} .price-line{{fill:none;stroke:var(--viz-series-1);stroke-width:3}}
    #{root} .ema-line{{fill:none;stroke:var(--viz-series-2);stroke-width:2}}
    #{root} .grid{{stroke:var(--border);stroke-width:1}}
  </style>
  <div class="viz-row text-small">{_public_fixture_badge(snapshot.get('privacy'))}<span class="viz-badge">{escape(str(payload['posture']))}</span><span>{escape(str(subject['instrument']))} · {escape(str(subject['analysis_horizon']))}</span><span class="text-muted">as_of {escape(str(snapshot['decision_cutoff']))}</span></div>
  <div class="viz-grid">
    <div class="card viz-stat"><span class="text-muted">Evidence gate</span><span class="viz-stat-value">{snapshot['coverage']['required_complete']}/{snapshot['coverage']['required_total']}</span></div>
    <div class="card viz-stat"><span class="text-muted">Setup</span><span class="viz-stat-value">{escape(str(price.get('setup_state') or 'n/a'))}</span></div>
    <div class="card viz-stat"><span class="text-muted">Volatility</span><span class="viz-stat-value">{escape(str((price.get('volatility') or {}).get('status') or 'n/a'))}</span></div>
  </div>
  <div class="viz-controls" aria-label="Instrument views"><button type="button" class="btn btn-primary" data-view="overview" aria-pressed="true">Overview</button><button type="button" class="btn" data-view="price" aria-pressed="false">Price</button><button type="button" class="btn" data-view="peers" aria-pressed="false">Peers</button><button type="button" class="btn" data-view="catalysts" aria-pressed="false">Catalysts</button></div>
  <div class="chart" aria-live="polite">{rows}</div>
  <svg class="price-plot" viewBox="0 0 720 300" role="img" aria-label="Instrument price and EMA"><g class="price-stage"></g></svg>
  <div class="selected-detail text-small">{escape(str(payload['decision']))}</div>
  <script>(()=>{{const root=document.getElementById('{root}');const chart=root.querySelector('.chart');const plot=root.querySelector('.price-plot');const detail=root.querySelector('.selected-detail');const views={data};const price={price_data};function rows(data){{chart.replaceChildren();data.forEach((d,i)=>{{const el=document.createElement('div');el.className='bar-row';const label=document.createElement('div');label.className='bar-label';label.textContent=d.label;const track=document.createElement('div');track.className='bar-track';const fill=document.createElement('div');fill.className='bar-fill';fill.style.setProperty('--w',Math.max(20,100-i*12)+'%');fill.style.setProperty('--series','var(--viz-series-'+((i%6)+1)+')');track.appendChild(fill);const value=document.createElement('div');value.className='bar-value';value.textContent=d.meta;el.append(label,track,value);el.addEventListener('click',()=>detail.textContent=d.value);chart.appendChild(el);}});detail.textContent=data[0]?data[0].value:'';}}function render(view){{const isPrice=view==='price';chart.style.display=isPrice?'none':'grid';plot.classList.toggle('is-visible',isPrice);if(!isPrice)rows(views[view]);else detail.textContent='Price is timing evidence; required research gates still apply.';root.querySelectorAll('[data-view]').forEach(btn=>{{const on=btn.dataset.view===view;btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('btn-primary',on);}});}}const g=root.querySelector('.price-stage');if(price.candles.length){{const ns='http://www.w3.org/2000/svg',W=720,H=300,left=42,right=18,top=12,bottom=28;const vals=price.candles.flatMap(d=>[+d.low,+d.high]);let lo=Math.min(...vals),hi=Math.max(...vals);const pad=(hi-lo)*.08;lo-=pad;hi+=pad;const x=i=>left+i*(W-left-right)/Math.max(1,price.candles.length-1),y=v=>top+(hi-v)*(H-top-bottom)/(hi-lo);const add=(tag,a)=>{{const e=document.createElementNS(ns,tag);Object.entries(a).forEach(([k,v])=>e.setAttribute(k,v));g.appendChild(e);return e;}};for(let i=0;i<4;i++){{const v=lo+(hi-lo)*i/3;add('line',{{x1:left,y1:y(v),x2:W-right,y2:y(v),class:'grid'}});}}add('path',{{d:price.candles.map((d,i)=>(i?'L':'M')+x(i)+','+y(+d.close)).join(' '),class:'price-line'}});price.overlays.forEach(o=>{{const pts=o.points||[];if(pts.length)add('path',{{d:pts.map((p,i)=>(i?'L':'M')+(left+i*(W-left-right)/Math.max(1,pts.length-1))+','+y(+p.value)).join(' '),class:'ema-line'}});}});}}root.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>render(btn.dataset.view)));}})();</script>
</div>
"""
    return html.encode("utf-8")


def _public_fixture_attr(privacy: Any) -> str:
    return ' data-public-fixture="true"' if privacy == "public_fixture" else ""


def _public_fixture_badge(privacy: Any) -> str:
    if privacy != "public_fixture":
        return ""
    return '<span class="viz-badge">演示数据，不可用于交易</span>'


def _base_css(root: str) -> str:
    return f"""
    #{root}{{width:100%;display:grid;gap:12px;color:var(--foreground)}}
    #{root} .viz-row{{justify-content:flex-start;gap:10px}}
    #{root} .viz-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}
    #{root} .viz-stat-value{{display:block}}
    #{root} .chart{{display:grid;gap:9px}}
    #{root} .bar-row{{display:grid;grid-template-columns:minmax(84px,.42fr) minmax(110px,1fr) minmax(64px,.28fr);align-items:center;gap:9px;cursor:pointer}}
    #{root} .bar-label{{font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
    #{root} .bar-track{{height:14px;overflow:hidden;background:var(--muted)}}
    #{root} .bar-fill{{width:var(--w);height:100%;min-width:2px;background:var(--series)}}
    #{root} .bar-value{{text-align:right;font-variant-numeric:tabular-nums}}
    #{root} .selected-detail{{min-height:22px;padding-top:8px;border-top:1px solid var(--border)}}
    #{root} table{{width:100%;border-collapse:collapse}}
    #{root} th,#{root} td{{padding:7px 8px;text-align:left;border-bottom:1px solid var(--border)}}
    #{root} th{{color:var(--muted-foreground);font-weight:500}}
    #{root} .compact-list{{margin:0;padding-left:20px}}
    @media(max-width:520px){{#{root} .viz-grid{{grid-template-columns:1fr}}#{root} .bar-row{{grid-template-columns:72px minmax(70px,1fr) 58px;gap:6px}}}}
  """.strip()


def _bar_row(label: Any, value: Any, series: int, display: str | None = None) -> str:
    numeric = abs(float(value))
    width = max(3.0, min(100.0, numeric))
    shown = display if display is not None else _num(value)
    return (
        f'<div class="bar-row"><div class="bar-label">{escape(str(label))}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="--w:{width:.2f}%;--series:var(--viz-series-{((series - 1) % 6) + 1})"></div></div>'
        f'<div class="bar-value">{escape(shown)}</div></div>'
    )


def _root_id(adapter: str, value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return f"dailytrades-{adapter}-inline-{hashlib.sha256(encoded).hexdigest()[:10]}"


def _script_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _latest_value(points: Any) -> float | None:
    if not isinstance(points, list) or not points:
        return None
    try:
        return float(points[-1]["value"])
    except (KeyError, TypeError, ValueError):
        return None


def _macro_summary_groups(series: list[Mapping[str, Any]]) -> str:
    by_label = {str(row["label"]).lower(): row for row in series}

    def value(label: str, suffix: str = "") -> str:
        row = by_label.get(label.lower())
        return f"{_num(row['value'])}{suffix}" if row is not None else "缺失"

    groups = (
        ("收益率曲线", (("2Y", value("2Y", "%")), ("10Y", value("10Y", "%")), ("30Y", value("30Y", "%")))),
        ("通胀", (("CPI", value("CPI", "%")), ("Core", value("Core CPI", "%")), ("PPI", value("PPI", "%")))),
        ("风险广度", (("NDX/RUT", value("NDX/RUT")), ("VXN", value("VXN")))),
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


def _money(value: Any) -> str:
    return f"${float(value):,.0f}"


def _signed_money(value: Any) -> str:
    number = float(value)
    return f"{'+' if number >= 0 else '-'}{_money(abs(number))}"


def _num(value: Any) -> str:
    return f"{float(value):,.2f}".rstrip("0").rstrip(".")
