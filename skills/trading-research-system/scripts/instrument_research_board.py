#!/usr/bin/env python3
"""Purpose-specific renderer for one validated Instrument Research snapshot."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
from typing import Any, Mapping


LIGHTWEIGHT_CHARTS_VERSION = "5.2.0"
LIGHTWEIGHT_CHARTS_ASSET = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "vendor"
    / f"lightweight-charts-{LIGHTWEIGHT_CHARTS_VERSION}"
    / "lightweight-charts.standalone.production.js"
)
VIEW_IDS = {
    "Overview": "overview",
    "Price & Setup": "price-setup",
    "Industry & Peers": "industry-peers",
    "Catalysts & Flows": "catalysts-flows",
}


def render_instrument_research_board(
    snapshot: Mapping[str, Any], default_view: str, presentation_state: str
) -> bytes:
    """Return deterministic, self-contained HTML with semantic no-JS content."""

    payload = snapshot["payload"]
    subject = payload["subject"]
    instrument_label = subject["instrument"] or "Unresolved instrument"
    modules = {module["id"]: module for module in payload["modules"]}
    privacy_label = "public fixture" if snapshot["privacy"] == "public_fixture" else "private"
    chart_json = _script_json(payload["price_setup"])
    default_view_id = VIEW_IDS[default_view]
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(instrument_label)} Instrument Research</title>
<meta name="generator" content="DailyTrades Instrument Research renderer {escape(snapshot['renderer_version'])}">
<style>
{_styles()}
</style>
</head>
<body>
<main id="instrument-board">
<header class="masthead">
<div>
<p class="eyebrow">Instrument Research</p>
<h1>{escape(instrument_label)} Research brief</h1>
<p class="lede">{escape(payload['question'])}</p>
</div>
<dl class="provenance" aria-label="Provenance">
<div><dt>Provenance</dt><dd>{escape(snapshot['snapshot_id'])}</dd></div>
<div><dt>Decision cutoff</dt><dd>{escape(snapshot['decision_cutoff'])}</dd></div>
<div><dt>Privacy</dt><dd>{privacy_label}</dd></div>
</dl>
</header>
<nav class="view-tabs" aria-label="Research views">{_render_view_buttons(payload['views'], default_view)}</nav>
<section class="summary" aria-label="Research summary">
<article><span>Current decision</span><strong>{escape(payload['decision'])}</strong></article>
<article><span>Coverage</span><strong>{snapshot['coverage']['required_complete']} of {snapshot['coverage']['required_total']} required gates complete</strong></article>
<article><span>Status</span><strong>Evidence: {escape(snapshot['evidence_state'])}<br>Presentation: {escape(presentation_state)}</strong></article>
</section>
<p class="thesis-boundary">Four-evidence balance. Price Action is timing evidence, not the research thesis.</p>
<div class="board-layout">
<div class="view-stack">
{_render_overview(payload, modules, default_view_id)}
{_render_price_setup(payload, default_view_id)}
{_render_industry_peers(payload, modules, default_view_id)}
{_render_catalysts_flows(payload, modules, default_view_id)}
</div>
{_render_evidence_rail(snapshot, payload)}
</div>
<footer>
<h2>Safety boundary</h2>
<p>Synthetic fixture. Not investment advice. No external requests or state-changing actions occur when this file is opened.</p>
</footer>
</main>
<script data-library="TradingView Lightweight Charts" data-version="{LIGHTWEIGHT_CHARTS_VERSION}">
{_load_lightweight_charts_script()}
</script>
<script>
const instrumentBoardPayload = {chart_json};
{_interaction_script(default_view_id)}
</script>
</body>
</html>
"""
    return html.encode("utf-8")


def _styles() -> str:
    return """
:root { color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.45; --ink:#18212b; --muted:#5c6874; --line:#d7dde3; --paper:#fff; --wash:#f4f6f8; --green:#137a4b; --amber:#a15c00; --red:#bf3b33; --blue:#1769aa; }
* { box-sizing: border-box; }
body { margin:0; color:var(--ink); background:var(--paper); }
button { font:inherit; }
main { max-width:1120px; margin:0 auto; padding:20px; }
h1,h2,h3,p,dl,dd { margin-top:0; }
h1 { margin-bottom:6px; font-size:26px; letter-spacing:0; }
h2 { font-size:18px; }
h3 { font-size:15px; }
.masthead { display:flex; justify-content:space-between; gap:24px; padding-bottom:16px; border-bottom:3px solid var(--ink); }
.eyebrow { margin-bottom:4px; color:var(--green); font-size:12px; font-weight:700; text-transform:uppercase; }
.lede { max-width:680px; margin-bottom:0; color:var(--muted); }
.provenance { min-width:250px; margin-bottom:0; font-size:12px; }
.provenance div { display:grid; grid-template-columns:110px minmax(0,1fr); gap:8px; padding:3px 0; }
.provenance dt { color:var(--muted); }
.provenance dd { overflow-wrap:anywhere; }
.view-tabs { display:flex; flex-wrap:wrap; gap:6px; padding:12px 0; }
.view-tabs button { min-height:32px; padding:4px 10px; border:1px solid var(--line); border-radius:5px; color:var(--ink); background:var(--paper); cursor:pointer; }
.view-tabs button[aria-selected="true"] { border-color:var(--ink); color:var(--paper); background:var(--ink); }
.view-tabs button:focus-visible { outline:3px solid #7db9e8; outline-offset:2px; }
.summary { display:grid; grid-template-columns:1.25fr 1fr 1fr; gap:8px; }
.summary article { min-width:0; padding:11px; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.summary span,.field-label { display:block; margin-bottom:4px; color:var(--muted); font-size:11px; text-transform:uppercase; }
.summary strong { font-size:13px; font-weight:600; }
.thesis-boundary { margin:12px 0; padding:9px 11px; border-left:3px solid var(--amber); background:#fff8e7; font-size:13px; }
.board-layout { display:grid; grid-template-columns:minmax(0,1fr) 260px; gap:18px; align-items:start; }
.view-panel { padding-top:4px; }
.enhanced .view-panel[hidden] { display:none; }
.section-head { display:flex; flex-wrap:wrap; justify-content:space-between; gap:8px; align-items:baseline; margin-bottom:8px; }
.section-head p { margin:0; color:var(--muted); font-size:12px; }
.module-list,.ledger,.queue,.timeline,.scenario-list { border-top:1px solid var(--line); }
.module-row { display:grid; grid-template-columns:140px minmax(0,1fr); gap:12px; padding:12px 0; border-bottom:1px solid var(--line); }
.module-row h3 { margin-bottom:5px; }
.module-row p { margin-bottom:5px; }
.module-meta { color:var(--muted); font-size:11px; }
.badge { display:inline-block; padding:2px 6px; border-radius:3px; color:var(--ink); background:var(--wash); font-size:11px; font-weight:600; }
.badge.complete { color:#075c36; background:#dcf4e7; }
.badge.partial,.badge.stale { color:#805000; background:#fff0c2; }
.badge.source_error { color:#8d2822; background:#ffe4e1; }
.data-grid,.fact-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; margin-top:7px; }
.data-grid div,.fact-grid article { min-width:0; padding:8px; background:var(--wash); }
.data-grid span { display:block; color:var(--muted); font-size:11px; text-transform:uppercase; }
.ledger-row { display:grid; grid-template-columns:92px minmax(0,1fr) 92px; gap:10px; padding:10px 0; border-bottom:1px solid var(--line); }
.ledger-row p,.queue-row p,.timeline-row p,.scenario p { margin-bottom:4px; }
.queue-row { padding:10px 0; border-bottom:1px solid var(--line); }
.chart-shell { min-height:390px; margin:8px 0 12px; border:1px solid var(--line); background:var(--paper); }
#instrument-price-chart { width:100%; height:390px; }
.chart-fallback { padding:12px; }
.enhanced.chart-ready .chart-fallback { display:none; }
.fact-grid article { border-top:3px solid var(--line); }
.fact-grid strong { display:block; overflow-wrap:anywhere; }
.scenario { padding:11px 0; border-bottom:1px solid var(--line); }
table { width:100%; border-collapse:collapse; font-size:12px; }
th,td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-weight:600; }
.timeline-row { display:grid; grid-template-columns:120px minmax(0,1fr); gap:12px; padding:12px 0; border-bottom:1px solid var(--line); }
.evidence-rail { position:sticky; top:8px; padding-left:14px; border-left:3px solid var(--blue); }
.evidence-rail ul { margin:0; padding-left:18px; }
.evidence-rail li { margin-bottom:10px; }
.evidence-rail p,.evidence-rail li { font-size:12px; }
.source-time { display:block; color:var(--muted); }
footer { margin-top:22px; padding-top:12px; border-top:1px solid var(--line); color:var(--muted); font-size:12px; }
footer h2 { margin-bottom:4px; font-size:14px; color:var(--ink); }
@media (max-width:736px) { main{padding:14px}.masthead{display:block}.provenance{margin-top:12px;min-width:0}.summary{grid-template-columns:1fr}.board-layout{grid-template-columns:1fr}.evidence-rail{position:static;border-left:0;border-top:3px solid var(--blue);padding:12px 0 0}.module-row,.ledger-row,.timeline-row{grid-template-columns:1fr}.data-grid,.fact-grid{grid-template-columns:1fr}#instrument-price-chart,.chart-shell{height:340px;min-height:340px} }
@media (max-width:420px) { main{padding:10px}.view-tabs button{flex:1 1 46%;white-space:normal}.provenance div{grid-template-columns:1fr}.summary article{padding:9px 0}th,td{padding:6px 4px;font-size:11px} }
@media (max-width:520px) { .peer-table thead{display:none}.peer-table,.peer-table tbody,.peer-table tr,.peer-table td{display:block;width:100%}.peer-table tr{display:grid;grid-template-columns:1fr 1fr;padding:8px 0;border-bottom:1px solid var(--line)}.peer-table td{min-width:0;padding:4px;border:0;overflow-wrap:anywhere}.peer-table td::before{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;content:attr(data-label)} }
""".strip()


def _render_view_buttons(views: list[str], default_view: str) -> str:
    return "".join(
        f'<button type="button" role="tab" id="tab-{VIEW_IDS[view]}" data-view-target="{VIEW_IDS[view]}" '
        f'aria-controls="view-{VIEW_IDS[view]}" aria-selected="{str(view == default_view).lower()}">{escape(view)}</button>'
        for view in views
    )


def _render_overview(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], default_view: str) -> str:
    rows = "".join(_render_module_row(modules[module_id]) for module_id in ("industry", "fundamentals", "catalysts", "market_instrument", "flows"))
    claims = "".join(
        '<article class="ledger-row">'
        f'<div><span class="badge">{escape(claim["kind"])}</span><p>{escape(claim["status"])}</p></div>'
        f'<div><strong>{escape(claim["claim"])}</strong><p class="module-meta">Evidence: {escape(", ".join(claim["evidence_refs"]))}</p></div>'
        f'<div><span class="field-label">Gate / impact</span><strong>{escape(claim["evidence_gate"])} · {escape(claim["impact"])}</strong></div>'
        '</article>'
        for claim in payload["claims"]
    )
    queue = "".join(
        '<article class="queue-row">'
        f'<strong>{escape(item["claim_id"])}</strong><p>{escape(item["check"])}</p>'
        f'<p class="module-meta">Due: {escape(item["due_event"])} · {escape(item["status"])}</p></article>'
        for item in payload["verification_queue"]
    ) or '<p class="queue-row">No unresolved verification items.</p>'
    return f"""<section class="view-panel" id="view-overview" data-view="overview" role="tabpanel" aria-labelledby="tab-overview"{_hidden('overview', default_view)}>
<div class="section-head"><h2>Overview</h2><p>Four-evidence balance with supporting flow</p></div>
<div class="module-list">{rows}</div>
<div class="section-head"><h2>Claim Ledger</h2><p>Decision-relevant claims remain traceable</p></div>
<div class="ledger">{claims}</div>
<div class="section-head"><h2>Verification Queue</h2><p>Open checks cannot be hidden by presentation</p></div>
<div class="queue">{queue}</div>
</section>"""


def _render_module_row(module: Mapping[str, Any]) -> str:
    data = "".join(
        f'<div><span>{escape(key.replace("_", " "))}</span>{escape(str(value) if value else "Unavailable")}</div>'
        for key, value in module["data"].items()
    )
    return f"""<article class="module-row">
<div><h3>{escape(module['id'].replace('_', ' ').title())}</h3><span class="badge {escape(module['evidence_state'])}">{escape(module['evidence_state'])}</span><p class="module-meta">{escape(module['requirement'])}</p></div>
<div><p>{escape(module['summary'])}</p><div class="data-grid">{data}</div><p class="module-meta">As of {escape(module['as_of'])} · Gap: {escape(module['gap_reason'] or 'None')}</p></div>
</article>"""


def _render_price_setup(payload: Mapping[str, Any], default_view: str) -> str:
    setup = payload["price_setup"]
    product = setup["product_path"]
    liquidity = setup["liquidity"]
    volatility = setup["volatility"]
    scenarios = "".join(
        f'<article class="scenario"><h3>{escape(item["name"])} · {escape(item["bias"])}</h3>'
        f'<p><strong>Trigger:</strong> {escape(item["trigger"])}</p>'
        f'<p><strong>Evidence:</strong> {escape(item["evidence_required"])}</p>'
        f'<p><strong>Invalidation:</strong> {escape(item["invalidation"])}</p>'
        f'<p><strong>Response:</strong> {escape(item["response"])}</p></article>'
        for item in setup["scenarios"]
    )
    candles = setup["candles"][-5:]
    fallback_rows = "".join(
        f'<tr><td>{int(candle["time"])}</td><td>{candle["open"]:.2f}</td><td>{candle["high"]:.2f}</td><td>{candle["low"]:.2f}</td><td>{candle["close"]:.2f}</td></tr>'
        for candle in candles
    )
    zone_rows = "".join(
        f'<li><strong>{escape(zone["label"])}</strong> {zone["low"]:.2f}–{zone["high"]:.2f} · {escape(zone["kind"])}</li>'
        for zone in setup["zones"]
    ) or "<li>No active price zones.</li>"
    return f"""<section class="view-panel" id="view-price-setup" data-view="price-setup" role="tabpanel" aria-labelledby="tab-price-setup"{_hidden('price-setup', default_view)}>
<div class="section-head"><h2>Price &amp; Setup</h2><p>Main {escape(setup['main_timeframe'])} · Auxiliary {escape(setup['auxiliary_timeframe'])}</p></div>
<p class="thesis-boundary"><strong>Research gate: {escape(setup['research_gate_status'])}</strong>. Price Action is timing evidence, not the research thesis.</p>
<div class="chart-shell"><div id="instrument-price-chart" role="img" aria-label="Synthetic candlestick chart with volume, overlays, decision levels, and price zones"></div><div class="chart-fallback"><strong>Semantic price fallback</strong><table><thead><tr><th>Time</th><th>Open</th><th>High</th><th>Low</th><th>Close</th></tr></thead><tbody>{fallback_rows}</tbody></table></div></div>
<div class="zone-legend"><span class="field-label">Price zones</span><ul>{zone_rows}</ul></div>
<div class="fact-grid">
<article><span class="field-label">Underlying identity</span><strong>{escape(product['underlying_identity'])}</strong></article>
<article><span class="field-label">Leverage / reset</span><strong>{product['leverage_multiple']:.1f}x · {escape(product['reset_frequency'])}</strong></article>
<article><span class="field-label">Path risk</span><strong>{escape(product['path_dependency'])}</strong><p>{escape(product['risk_note'])}</p></article>
<article><span class="field-label">Liquidity</span><strong>{escape(liquidity['status'])}</strong><p>ADV {liquidity['average_daily_volume']:,.0f} · spread {liquidity['bid_ask_bps']:.1f} bps</p></article>
<article><span class="field-label">Volatility</span><strong>{escape(volatility['status'])}</strong><p>ATR {volatility['atr_percent']:.1f}% · realized 20d {volatility['realized_20d_percent']:.1f}%</p></article>
<article><span class="field-label">Setup / invalidation</span><strong>{escape(setup['setup_state'])}</strong><p>{setup['invalidation']['price']:.2f} · {escape(setup['invalidation']['condition'])}</p></article>
</div>
<div class="section-head"><h2>Scenario paths</h2><p>Conditional, evidence-gated, and non-prescriptive</p></div><div class="scenario-list">{scenarios}</div>
</section>"""


def _render_industry_peers(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], default_view: str) -> str:
    peer_rows = "".join(
        f'<tr><td data-label="Symbol">{escape(peer["symbol"])}</td><td data-label="Role">{escape(peer["role"])}</td><td data-label="Status"><span class="badge {escape(peer["status"])}">{escape(peer["status"])}</span></td><td data-label="Revenue growth">{_peer_metric(peer["revenue_growth_pct"], "%")}</td><td data-label="Gross margin">{_peer_metric(peer["gross_margin_pct"], "%")}</td><td data-label="Valuation">{_peer_metric(peer["valuation_multiple"], "x")}</td><td data-label="Comparability gap">{escape(peer["comparability_gap"] or "None")}</td></tr>'
        for peer in payload["peers"]
    )
    return f"""<section class="view-panel" id="view-industry-peers" data-view="industry-peers" role="tabpanel" aria-labelledby="tab-industry-peers"{_hidden('industry-peers', default_view)}>
<div class="section-head"><h2>Industry &amp; Peers</h2><p>Industry facts, differentiation, and comparability gaps</p></div>
{_render_module_row(modules['industry'])}
{_render_module_row(modules['fundamentals'])}
<table class="peer-table"><thead><tr><th>Symbol</th><th>Role</th><th>Status</th><th>Revenue growth</th><th>Gross margin</th><th>Valuation</th><th>Comparability gap</th></tr></thead><tbody>{peer_rows}</tbody></table>
</section>"""


def _peer_metric(value: Any, suffix: str) -> str:
    return "Unavailable" if value is None else f"{value:.1f}{suffix}"


def _render_catalysts_flows(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], default_view: str) -> str:
    rows = "".join(
        f'<article class="timeline-row"><div><span class="badge">{escape(item["status"])}</span><h3>{escape(item["catalyst"])}</h3><p class="module-meta">{escape(item["event_time"])}</p></div>'
        f'<div><p><strong>Catalyst to Evidence to Decision</strong></p><p>{escape(item["expected_evidence"])}</p>'
        f'<p><strong>Confirm:</strong> {escape(item["confirmation"])}</p><p><strong>Invalidate:</strong> {escape(item["invalidation"])}</p>'
        f'<p><strong>Decision consequence:</strong> {escape(item["decision_consequence"])}</p></div></article>'
        for item in payload["event_transmission"]
    )
    return f"""<section class="view-panel" id="view-catalysts-flows" data-view="catalysts-flows" role="tabpanel" aria-labelledby="tab-catalysts-flows"{_hidden('catalysts-flows', default_view)}>
<div class="section-head"><h2>Catalysts &amp; Flows</h2><p>Ranked by thesis impact, not date alone</p></div>
<h3>Catalyst to Evidence to Decision</h3><div class="timeline">{rows}</div>
<div class="section-head"><h2>Supporting flow boundary</h2><p>Flow cannot prove or replace a required gate</p></div>
{_render_module_row(modules['flows'])}
</section>"""


def _render_evidence_rail(snapshot: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
    modules = payload["modules"]
    sources = "".join(
        f'<li><strong>{escape(source["alias"])}</strong><span class="source-time">{escape(source["priority"])} · {escape(source["freshness_status"])} · {escape(source["as_of"])}</span></li>'
        for source in snapshot["source_registry"]
    )
    gaps = [module for module in modules if module["evidence_state"] != "complete" or module["gap_reason"]]
    gap_rows = "".join(
        f'<li><strong>{escape(module["id"])}</strong><span class="source-time">{escape(module["evidence_state"])} · {escape(module["gap_reason"] or "No explicit gap")}</span></li>'
        for module in gaps
    ) or "<li>No evidence gaps in this snapshot.</li>"
    return f"""<aside class="evidence-rail" aria-labelledby="evidence-rail-title">
<h2 id="evidence-rail-title">Evidence rail</h2><ul>{sources}</ul>
<h3>Visible gaps</h3><ul>{gap_rows}</ul>
<p><strong>Minimum evidence:</strong> industry, fundamentals, catalysts/events, and market/instrument data. Flows are supporting-only.</p>
</aside>"""


def _hidden(view_id: str, default_view: str) -> str:
    return "" if view_id == default_view else " hidden"


def _script_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _load_lightweight_charts_script() -> str:
    source = LIGHTWEIGHT_CHARTS_ASSET.read_text(encoding="utf-8")
    source = re.sub(r"^/\*!.*?\*/\s*", "", source, count=1, flags=re.DOTALL)
    source = source.replace(
        "https://www.tradingview.com/?utm_medium=lwc-link&utm_campaign=lwc-chart${this.Jv()}",
        "about:blank",
    )
    return source.replace("</script", "<\\/script")


def _interaction_script(default_view_id: str) -> str:
    return f"""
const boardRoot = document.documentElement;
const tabs = Array.from(document.querySelectorAll('[data-view-target]'));
const panels = Array.from(document.querySelectorAll('[data-view]'));
let chartRendered = false;

function activateView(viewId) {{
  for (const tab of tabs) tab.setAttribute('aria-selected', String(tab.dataset.viewTarget === viewId));
  for (const panel of panels) panel.hidden = panel.dataset.view !== viewId;
  if (viewId === 'price-setup') renderPriceChart();
}}

function renderPriceChart() {{
  if (chartRendered || !window.LightweightCharts) return;
  const element = document.getElementById('instrument-price-chart');
  const chart = LightweightCharts.createChart(element, {{
    width: element.clientWidth,
    height: element.clientHeight,
    layout: {{ background: {{ color: '#ffffff' }}, textColor: '#18212b' }},
    grid: {{ vertLines: {{ color: '#eef1f3' }}, horzLines: {{ color: '#eef1f3' }} }},
    rightPriceScale: {{ borderVisible: false }},
    timeScale: {{ borderVisible: false, timeVisible: true }},
    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
  }});
  const candles = chart.addSeries(LightweightCharts.CandlestickSeries, {{
    upColor: '#137a4b', downColor: '#bf3b33', borderUpColor: '#137a4b', borderDownColor: '#bf3b33', wickUpColor: '#137a4b', wickDownColor: '#bf3b33'
  }});
  candles.setData(instrumentBoardPayload.candles);
  const volume = chart.addSeries(LightweightCharts.HistogramSeries, {{ priceFormat: {{ type: 'volume' }}, priceScaleId: '', lastValueVisible: false, priceLineVisible: false }});
  volume.setData(instrumentBoardPayload.candles.map(row => ({{ time: row.time, value: row.volume, color: row.close >= row.open ? 'rgba(19,122,75,.28)' : 'rgba(191,59,51,.28)' }})));
  chart.priceScale('').applyOptions({{ scaleMargins: {{ top: .82, bottom: 0 }} }});
  for (const overlay of instrumentBoardPayload.overlays) {{
    const line = chart.addSeries(LightweightCharts.LineSeries, {{ color: '#1769aa', lineWidth: 2, title: overlay.label, priceLineVisible: false }});
    line.setData(overlay.points);
  }}
  for (const level of instrumentBoardPayload.levels) {{
    candles.createPriceLine({{ price: level.price, color: level.kind === 'invalidation' ? '#bf3b33' : '#a15c00', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: level.label }});
  }}
  for (const zone of instrumentBoardPayload.zones) {{
    candles.createPriceLine({{ price: zone.low, color: '#1769aa', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: `${{zone.label}} low` }});
    candles.createPriceLine({{ price: zone.high, color: '#1769aa', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: `${{zone.label}} high` }});
  }}
  chart.timeScale().fitContent();
  new ResizeObserver(entries => {{ for (const entry of entries) chart.applyOptions({{ width: entry.contentRect.width }}); }}).observe(element);
  chartRendered = true;
  boardRoot.classList.add('chart-ready');
  element.dataset.renderStatus = 'ready';
}}

for (const tab of tabs) tab.addEventListener('click', () => activateView(tab.dataset.viewTarget));
document.addEventListener('keydown', event => {{
  if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  const selectedIndex = tabs.findIndex(tab => tab.getAttribute('aria-selected') === 'true');
  const direction = event.key === 'ArrowRight' ? 1 : -1;
  const next = tabs[(selectedIndex + direction + tabs.length) % tabs.length];
  activateView(next.dataset.viewTarget);
  next.focus();
  event.preventDefault();
}});
boardRoot.classList.add('enhanced');
activateView('{default_view_id}');
window.__dailytradesBoardReady = true;
""".strip()
