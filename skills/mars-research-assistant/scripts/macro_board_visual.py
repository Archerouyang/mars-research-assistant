#!/usr/bin/env python3
"""Self-contained Macro Regime Board renderer for one stateless delivery."""

from __future__ import annotations

from html import escape
import json
from typing import Any, Mapping


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
        value=escape(f"{float(values[key]):,.2f}"),
        suffix=escape(suffix),
        source=escape(str(sources[key])),
        as_of=escape(str(as_ofs[key])),
    )


def _trend_panel(
    label: str,
    field: str,
    sources: Mapping[str, Any],
    as_ofs: Mapping[str, Any],
) -> str:
    return (
        '<section class="chart-shell"><div class="section-head">'
        '<div><p class="eyebrow">Relative strength</p><h2>{label}</h2></div>'
        '<p>30D common XNYS sessions</p></div>'
        '<svg class="macro-chart" data-series="{label}" role="img" '
        'aria-label="{label} 30 day relative strength line chart"></svg>'
        '<p class="module-meta">source: {source} · as_of: {as_of}</p></section>'
    ).format(
        label=escape(label),
        field=escape(field),
        source=escape(str(sources[field])),
        as_of=escape(str(as_ofs[field])),
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


def render_macro_board(payload: Mapping[str, Any]) -> str:
    """Render frozen Macro v1 fields in the established standalone Board visual."""

    values = payload["values"]
    sources = payload["sources"]
    as_ofs = payload["as_ofs"]
    rate_cards = "".join(
        _metric_card(label, key, "%", values, sources, as_ofs)
        for label, key in (("2Y", "treasury_2y"), ("10Y", "treasury_10y"), ("30Y", "treasury_30y"))
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
    trends = json.dumps(payload["trend_series"], ensure_ascii=False).replace(
        "<", "\\u003c"
    )
    events_html = "".join(_event_row(event) for event in payload["events"]) or (
        '<p class="module-meta">none_found: 当前事件窗口未发现符合范围的重大事件</p>'
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Macro Regime Research Brief</title>
<style>
:root{{color-scheme:light;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.45;--ink:#17212b;--muted:#586672;--line:#d5dde4;--paper:#fff;--wash:#f4f7f8;--green:#08724a;--amber:#9a5b00;--blue:#1769aa}}*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background:var(--paper)}}main{{max-width:1120px;margin:0 auto;padding:20px}}h1,h2,h3,p,dl,dd{{margin-top:0}}h1{{margin-bottom:6px;font-size:26px;letter-spacing:0}}h2{{margin-bottom:0;font-size:18px}}h3{{margin-bottom:5px;font-size:15px}}.masthead{{display:flex;justify-content:space-between;gap:24px;padding-bottom:16px;border-bottom:3px solid var(--ink)}}.eyebrow{{margin-bottom:4px;color:var(--green);font-size:12px;font-weight:700;text-transform:uppercase}}.lede{{max-width:680px;margin-bottom:0;color:var(--muted)}}.provenance{{min-width:250px;margin-bottom:0;font-size:12px}}.provenance div{{display:grid;grid-template-columns:110px minmax(0,1fr);gap:8px;padding:3px 0}}.provenance dt,.module-meta{{color:var(--muted)}}.provenance dd,.evidence-reading{{overflow-wrap:anywhere}}.summary{{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:8px;margin-top:14px}}.summary article{{min-width:0;padding:11px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.summary p{{margin:5px 0 0;font-size:12px}}.field-label{{display:block;margin-bottom:4px;color:var(--muted);font-size:11px;text-transform:uppercase}}.decision-framing{{margin:12px 0;padding:9px 11px;border-left:3px solid var(--amber);background:#fff8e7;font-size:13px}}.market-strip{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:12px 0 18px}}.market-card{{min-width:0;padding:11px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.market-card strong{{display:block;font-size:20px;line-height:1.2}}.market-card small{{display:block;margin-top:6px;color:var(--muted);font-size:11px;overflow-wrap:anywhere}}.board-layout{{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:18px;align-items:start}}.section-head{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:baseline;margin:0 0 8px}}.section-head p{{margin:0;color:var(--muted);font-size:12px}}.chart-shell{{margin:0 0 12px;padding:12px;border:1px solid var(--line)}}.macro-chart{{display:block;width:100%;height:252px;background:linear-gradient(180deg,#fff 0%,#f8fafb 100%)}}.chart-axis{{stroke:var(--line);stroke-width:1}}.chart-guide{{stroke:#e8edf0;stroke-width:1;stroke-dasharray:3 4}}.chart-line{{fill:none;stroke:var(--blue);stroke-width:3;stroke-linejoin:round;stroke-linecap:round}}.chart-dot{{fill:var(--blue)}}.chart-label{{fill:var(--muted);font:11px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.evidence-rail{{position:sticky;top:8px;padding-left:14px;border-left:3px solid var(--blue)}}.evidence-rail h2{{margin-bottom:5px}}.evidence-rail>p{{margin-bottom:10px;color:var(--muted);font-size:12px}}.evidence-list{{border-top:1px solid var(--line)}}.evidence-row{{display:grid;grid-template-columns:78px minmax(0,1fr);gap:10px;padding:11px 0;border-bottom:1px solid var(--line)}}.evidence-row p{{margin-bottom:5px;font-size:12px}}.source-category{{font-size:11px;text-transform:uppercase;color:var(--muted)}}footer{{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}@media(max-width:736px){{main{{padding:14px}}.masthead{{display:block}}.provenance{{min-width:0;margin-top:12px}}.summary,.board-layout{{grid-template-columns:1fr}}.market-strip{{grid-template-columns:repeat(2,minmax(0,1fr))}}.evidence-rail{{position:static;border-left:0;border-top:3px solid var(--blue);padding:12px 0 0}}}}@media(max-width:420px){{main{{padding:10px}}.market-strip{{grid-template-columns:1fr}}.provenance div,.evidence-row{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<main>
<header class="masthead">
  <div><p class="eyebrow">Macro Regime</p><h1>Macro Regime Research Brief</h1><p class="lede">冻结市场快照、相对强弱与已确认重大事件；每项字段都保留来源和 as_of。</p></div>
  <dl class="provenance" aria-label="数据时点与来源"><div><dt>Market as_of</dt><dd>{escape(str(payload['as_of']))}</dd></div><div><dt>Treasury as_of</dt><dd>{escape(str(payload['treasury_as_of']))}</dd></div><div><dt>Event source</dt><dd>{escape(str(sources['macro_events']))} · {escape(str(as_ofs['macro_events']))}</dd></div></dl>
</header>
<section class="summary" aria-label="Macro snapshot summary"><article><span class="field-label">Delivery scope</span><strong>Rates, volatility &amp; cross-asset</strong><p>只呈现冻结的 Macro v1 字段。</p></article><article><span class="field-label">Relative strength</span><strong>HYG/LQD · NDX/RUT</strong><p>30 个共同完成的 XNYS 交易日。</p></article><article><span class="field-label">Event evidence</span><strong>Primary source confirmed</strong><p>只显示经验证的重大事件。</p></article></section>
<p class="decision-framing"><strong>Research frame:</strong> 将市场读数与重大事件分开呈现，避免把未验证叙事当作决策证据。</p>
<section class="market-strip" aria-label="Rates and cross asset snapshot">{rate_cards}{cross_asset_cards}</section>
<div class="board-layout"><div>
  {_trend_panel('HYG/LQD', 'hyg_lqd_history', sources, as_ofs)}
  {_trend_panel('NDX/RUT', 'ndx_rut_history', sources, as_ofs)}
</div><aside class="evidence-rail" aria-label="Major event evidence"><p class="eyebrow">Primary-source evidence</p><h2>重大事件</h2><p>事件窗口内、已确认的 Macro 事件。</p><div class="evidence-list">{events_html}</div></aside></div>
<footer>Macro Regime Board · 一次性自包含研究交付</footer>
</main>
<script>
const series={trends};
const chartWidth=720,chartHeight=252,chartPad={{top:24,right:24,bottom:34,left:46}};
document.querySelectorAll('.macro-chart').forEach((svg)=>{{
  const points=series[svg.dataset.series]||[];
  const values=points.map((point)=>Number(point.value)).filter(Number.isFinite);
  if(!values.length){{svg.innerHTML='<text class="chart-label" x="12" y="24">No completed observations</text>';return;}}
  const min=Math.min(...values),max=Math.max(...values),span=max-min||1;
  const innerWidth=chartWidth-chartPad.left-chartPad.right,innerHeight=chartHeight-chartPad.top-chartPad.bottom;
  const x=(index)=>chartPad.left+(points.length===1?innerWidth/2:index*innerWidth/(points.length-1));
  const y=(value)=>chartPad.top+innerHeight-(value-min)*innerHeight/span;
  const guides=[0,.5,1].map((ratio)=>{{const value=min+span*ratio;const guideY=y(value);return `<line class="chart-guide" x1="${{chartPad.left}}" y1="${{guideY}}" x2="${{chartWidth-chartPad.right}}" y2="${{guideY}}"/><text class="chart-label" x="2" y="${{guideY+4}}">${{value.toFixed(2)}}</text>`;}}).join('');
  const path=points.map((point,index)=>`${{index?'L':'M'}}${{x(index).toFixed(2)}},${{y(Number(point.value)).toFixed(2)}}`).join(' ');
  const latest=points[points.length-1],first=points[0];
  svg.setAttribute('viewBox',`0 0 ${{chartWidth}} ${{chartHeight}}`);
  svg.innerHTML=`${{guides}}<line class="chart-axis" x1="${{chartPad.left}}" y1="${{chartHeight-chartPad.bottom}}" x2="${{chartWidth-chartPad.right}}" y2="${{chartHeight-chartPad.bottom}}"/><path class="chart-line" d="${{path}}"/><circle class="chart-dot" cx="${{x(0)}}" cy="${{y(Number(first.value))}}" r="3"/><circle class="chart-dot" cx="${{x(points.length-1)}}" cy="${{y(Number(latest.value))}}" r="3"/><text class="chart-label" x="${{chartPad.left}}" y="${{chartHeight-10}}">${{first.date}}</text><text class="chart-label" text-anchor="end" x="${{chartWidth-chartPad.right}}" y="${{chartHeight-10}}">${{latest.date}}</text>`;
}});
</script>
</body>
</html>"""
