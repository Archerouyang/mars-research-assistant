#!/usr/bin/env python3
"""Instrument research chat visual adapter."""

from __future__ import annotations

import copy
from html import escape
from typing import Any, Mapping

from artifact_packet import build_artifact_packet
from chat_visual_contract import ChatVisualError, exact_fields
from chat_visual_shared import (
    _base_css,
    _num,
    _public_fixture_attr,
    _public_fixture_badge,
    _root_id,
    _script_json,
)


BOARD = "instrument_research"


def normalize(visual: Mapping[str, Any]) -> dict[str, Any]:
    exact_fields(visual, {"adapter", "snapshot", "default_view"}, "visual_fields_invalid")
    snapshot = visual.get("snapshot")
    if not isinstance(snapshot, Mapping) or snapshot.get("board") != BOARD:
        raise ChatVisualError("visual_snapshot_invalid")
    normalized = copy.deepcopy(dict(visual))
    normalized["snapshot"] = copy.deepcopy(dict(snapshot))
    normalized["default_view"] = str(normalized.get("default_view") or "Overview")
    return normalized


def render(visual: Mapping[str, Any], privacy: str) -> bytes:
    del privacy
    snapshot = visual["snapshot"]
    build_artifact_packet(
        snapshot,
        default_view=str(visual["default_view"]),
        presentation_state="ready",
    )
    return _render_snapshot(snapshot)


def _render_snapshot(snapshot: Mapping[str, Any]) -> bytes:
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


def _bar_row(label: Any, value: Any, series: int, display: str | None = None) -> str:
    numeric = abs(float(value))
    width = max(3.0, min(100.0, numeric))
    shown = display if display is not None else _num(value)
    return (
        f'<div class="bar-row"><div class="bar-label">{escape(str(label))}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="--w:{width:.2f}%;--series:var(--viz-series-{((series - 1) % 6) + 1})"></div></div>'
        f'<div class="bar-value">{escape(shown)}</div></div>'
    )
