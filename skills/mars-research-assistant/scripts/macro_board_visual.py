#!/usr/bin/env python3
"""Self-contained Macro Regime Board renderer for one stateless delivery."""

from __future__ import annotations

from html import escape
import json
from typing import Any, Mapping


def render_macro_board(payload: Mapping[str, Any]) -> str:
    """Render only the frozen Macro v1 fields; no artifact or runtime protocol."""

    values = payload["values"]
    sources = payload["sources"]
    as_ofs = payload["as_ofs"]
    cards = (
        ("2Y", "treasury_2y", "%"),
        ("10Y", "treasury_10y", "%"),
        ("30Y", "treasury_30y", "%"),
        ("VIX", "vix", ""),
        ("VIX3M", "vix3m", ""),
        ("DXY", "dxy", ""),
        ("WTI", "wti", ""),
        ("Gold", "gold", ""),
    )
    cards_html = "".join(
        '<article class="card"><span>{label}</span><strong>{value}{suffix}</strong>'
        '<small>source: {source} · as_of: {as_of}</small></article>'.format(
            label=label,
            value=escape(f"{float(values[key]):,.2f}"),
            suffix=suffix,
            source=escape(str(sources[key])),
            as_of=escape(str(as_ofs[key])),
        )
        for label, key, suffix in cards
    )
    trends = json.dumps(payload["trend_series"], ensure_ascii=False).replace("<", "\\u003c")
    events_html = "".join(
        '<li><strong>{time} · {title}</strong><span>{category} · {status} · {transmission}</span>'
        '<small>evidence_kind: {evidence_kind} · primary_source_confirmed: {primary_source_confirmed}</small>'
        '<small>source: {source} · as_of: {as_of}</small></li>'.format(
            time=escape(str(event["time"])),
            title=escape(str(event["title"])),
            category=escape(str(event["category"])),
            status=escape(str(event["status"])),
            transmission=escape(str(event["transmission"])),
            evidence_kind=escape(str(event["evidence_kind"])),
            primary_source_confirmed=escape(
                str(event["primary_source_confirmed"]).lower()
            ),
            source=escape(str(event["original_source"])),
            as_of=escape(str(event["as_of"])),
        )
        for event in payload["events"]
    ) or '<li><span>none_found: 当前事件窗口未发现符合范围的重大事件</span></li>'
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Macro Regime Board</title><style>
body{{margin:0;background:#f5f7f8;color:#17212b;font:14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1080px;margin:auto;padding:24px}}h1{{margin:0}}.meta{{color:#586672;margin:8px 0 20px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}.card,.trend{{background:white;border:1px solid #d5dde4;padding:13px}}
.card span,.card small{{display:block;color:#586672;font-size:12px}}.card strong{{display:block;font-size:24px;margin:5px 0}}
.trends{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}}.trend h2{{margin:0 0 8px;font-size:16px}}
svg{{width:100%;height:180px}}.line{{fill:none;stroke:#1769aa;stroke-width:3}}.axis{{stroke:#d5dde4}}.events{{margin-top:12px;background:white;border:1px solid #d5dde4;padding:13px}}.events h2{{margin:0 0 8px;font-size:16px}}.events ul{{margin:0;padding-left:20px}}.events li{{margin:7px 0}}.events span,.events small{{display:block;color:#586672;font-size:12px}}@media(max-width:700px){{.grid,.trends{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:460px){{.grid,.trends{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>Macro Regime</h1>
<p class="meta">市场字段 as_of: {escape(str(payload['as_of']))} · Treasury as_of: {escape(str(payload['treasury_as_of']))}</p>
<section class="grid">{cards_html}</section><section class="trends"><div class="trend"><h2>HYG/LQD · 30D common sessions</h2><svg data-series="HYG/LQD"></svg><small>source: {escape(str(sources['hyg_lqd_history']))} · as_of: {escape(str(as_ofs['hyg_lqd_history']))}</small></div><div class="trend"><h2>NDX/RUT · 30D common sessions</h2><svg data-series="NDX/RUT"></svg><small>source: {escape(str(sources['ndx_rut_history']))} · as_of: {escape(str(as_ofs['ndx_rut_history']))}</small></div></section><section class="events"><h2>重大事件</h2><ul>{events_html}</ul></section>
</main><script>const series={trends};document.querySelectorAll('svg').forEach(svg=>{{const p=series[svg.dataset.series];const v=p.map(x=>x.value),lo=Math.min(...v),hi=Math.max(...v),span=hi-lo||1;svg.innerHTML='<line class="axis" x1="0" y1="160" x2="600" y2="160"/><path class="line" d="'+p.map((x,i)=>(i?'L':'M')+(i*600/(p.length-1))+','+(155-(x.value-lo)*140/span)).join(' ')+'"/>';}});</script></body></html>"""
