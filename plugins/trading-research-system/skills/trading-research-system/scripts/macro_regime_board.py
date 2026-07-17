#!/usr/bin/env python3
"""Purpose-specific renderer for one validated Macro Regime Board snapshot."""

from __future__ import annotations

from html import escape
import json
from typing import Any, Mapping

from research_brief_shell import (
    render_decision_framing,
    render_evidence_rail,
    render_main_open,
    render_masthead,
    render_safety_footer,
    render_summary,
    render_view_tabs,
    shared_shell_styles,
)

ECHARTS_VERSION = "6.1.0"
VIEW_IDS = {
    "Overview": "overview",
    "Rates & Liquidity": "rates-liquidity",
    "Inflation & Growth": "inflation-growth",
    "Cross-Asset Impact": "cross-asset-impact",
    "Event Scenarios": "event-scenarios",
}


def render_macro_regime_board(
    snapshot: Mapping[str, Any], default_view: str, presentation_state: str, *, echarts_source: str
) -> bytes:
    """Return deterministic, self-contained Macro Board HTML with semantic content."""

    payload = snapshot["payload"]
    modules = {module["id"]: module for module in payload["modules"]}
    sources = {source["id"]: source for source in snapshot["source_registry"]}
    privacy = "public fixture" if snapshot["privacy"] == "public_fixture" else "private"
    default_id = VIEW_IDS[default_view]
    plan_available = modules["plan_context"]["evidence_state"] == "complete"
    decision = (
        payload["decision"]
        if plan_available
        else "No plan-linked Macro decision is available until plan context is complete."
    )
    posture_summary = (
        ("Plan-linked posture", payload["posture"]["label"], payload["posture"]["consequence"])
        if plan_available
        else (
            "Plan linkage",
            "Plan-linked Macro decision unavailable",
            "Active Market Plan context is unavailable at this decision cutoff.",
        )
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Macro Regime Research brief</title>
<meta name="generator" content="DailyTrades Macro Regime renderer {escape(snapshot['renderer_version'])}">
<style>{_styles()}</style>
</head>
<body>
{render_main_open('macro-board')}
{render_masthead(eyebrow='Macro Regime', title='Macro Regime Research brief', question=payload['question'], snapshot_id=snapshot['snapshot_id'], decision_cutoff=snapshot['decision_cutoff'], privacy=privacy)}
{render_view_tabs(payload['views'], default_view, VIEW_IDS, 'Macro Board views')}
{render_summary((posture_summary, ('Coverage', f"{snapshot['coverage']['required_complete']} of {snapshot['coverage']['required_total']} required gates complete", None), ('Status', f"Evidence: {snapshot['evidence_state']} | Presentation: {presentation_state}", None)), 'Macro decision summary')}
{render_decision_framing('Current plan decision', decision)}
<div class="board-layout"><div class="view-stack">
{_overview(payload, modules, sources, default_id, plan_available)}
{_rates(payload, modules, sources, default_id, plan_available)}
{_inflation(payload, modules, sources, default_id, plan_available)}
{_cross_asset(payload, modules, sources, default_id, plan_available)}
{_scenarios(payload, modules, default_id, plan_available)}
</div>{render_evidence_rail(snapshot, payload['modules'], 'fresh plan, cross-asset transmission, and three decision-evidence families. Holdings remain conditional when unreconciled.')}</div>
{render_safety_footer('Synthetic fixture. Decision support only. This file has no network, private-state, broker, or execution operation.')}
</main>
<script data-library="Apache ECharts" data-version="{ECHARTS_VERSION}">{echarts_source}</script>
<script>const macroBoardPayload={_script_json({'chart_series': payload['chart_series']})};{_interaction_script(default_id)}</script>
</body></html>"""
    return html.encode("utf-8")


def _styles() -> str:
    return shared_shell_styles() + """
:root{color-scheme:light;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.45;--ink:#17212b;--muted:#586672;--line:#d5dde4;--paper:#fff;--wash:#f4f7f8;--green:#08724a;--amber:#9a5b00;--red:#ad342d;--blue:#1769aa}*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--paper)}button,select{font:inherit}main{max-width:1120px;margin:0 auto;padding:20px}h1,h2,h3,p,dl,dd{margin-top:0}h1{margin-bottom:6px;font-size:26px;letter-spacing:0}h2{font-size:18px}h3{font-size:15px}.masthead{display:flex;justify-content:space-between;gap:24px;padding-bottom:16px;border-bottom:3px solid var(--ink)}.eyebrow{margin-bottom:4px;color:var(--green);font-size:12px;font-weight:700;text-transform:uppercase}.lede{max-width:680px;margin-bottom:0;color:var(--muted)}.provenance{min-width:250px;margin-bottom:0;font-size:12px}.provenance div{display:grid;grid-template-columns:110px minmax(0,1fr);gap:8px;padding:3px 0}.provenance dt,.module-meta{color:var(--muted)}.provenance dd,.evidence-reading{overflow-wrap:anywhere}.view-tabs{display:flex;flex-wrap:wrap;gap:6px;padding:12px 0}.view-tabs button{min-height:32px;padding:4px 10px;border:1px solid var(--line);border-radius:5px;color:var(--ink);background:var(--paper);cursor:pointer}.view-tabs button[aria-selected="true"]{border-color:var(--ink);color:var(--paper);background:var(--ink)}button:focus-visible,select:focus-visible{outline:3px solid #7db9e8;outline-offset:2px}.summary{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:8px}.summary article{min-width:0;padding:11px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.summary span,.field-label{display:block;margin-bottom:4px;color:var(--muted);font-size:11px;text-transform:uppercase}.summary p{margin:5px 0 0;font-size:12px}.decision-framing{margin:12px 0;padding:9px 11px;border-left:3px solid var(--amber);background:#fff8e7;font-size:13px}.board-layout{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:18px;align-items:start}.view-panel{padding-top:4px}.enhanced .view-panel[hidden]{display:none}.section-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:baseline;margin:12px 0 8px}.section-head p{margin:0;color:var(--muted);font-size:12px}.module-list,.cascade,.evidence-list,.scenario-list,.exposure-list{border-top:1px solid var(--line)}.module-row,.cascade-row,.evidence-row,.scenario,.exposure{padding:11px 0;border-bottom:1px solid var(--line)}.module-row{display:grid;grid-template-columns:150px minmax(0,1fr);gap:12px}.module-row h3,.cascade-row h3,.scenario h3,.exposure h3{margin-bottom:5px}.module-row p,.cascade-row p,.scenario p,.exposure p{margin-bottom:5px}.badge{display:inline-block;padding:2px 6px;border-radius:3px;background:var(--wash);font-size:11px;font-weight:600}.badge.complete{color:#075c36;background:#dcf4e7}.badge.partial,.badge.stale{color:#805000;background:#fff0c2}.badge.source_error{color:#8d2822;background:#ffe4e1}.fact-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:7px}.fact-grid article{min-width:0;padding:8px;background:var(--wash)}.chart-shell{min-height:300px;margin:8px 0 12px;border:1px solid var(--line)}.macro-chart{width:100%;height:300px}.chart-fallback{padding:12px}.enhanced.chart-ready .chart-fallback{display:none}.cascade-row{display:grid;grid-template-columns:130px minmax(0,1fr);gap:12px}.cascade-row strong{display:block}.evidence-row{display:grid;grid-template-columns:95px minmax(0,1fr) 115px;gap:10px}.source-category{font-size:11px;text-transform:uppercase;color:var(--muted)}.exposure-control{display:flex;gap:8px;align-items:center;margin:8px 0 12px}.exposure-control select{min-width:190px;max-width:100%;padding:5px;border:1px solid var(--line);border-radius:4px;background:var(--paper)}.exposure[hidden]{display:none}.evidence-rail{position:sticky;top:8px;padding-left:14px;border-left:3px solid var(--blue)}.evidence-rail ul{margin:0;padding-left:18px}.evidence-rail li{margin-bottom:10px;font-size:12px}.source-time{display:block;color:var(--muted)}footer{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}footer h2{margin-bottom:4px;font-size:14px;color:var(--ink)}@media(max-width:736px){main{padding:14px}.masthead{display:block}.provenance{min-width:0;margin-top:12px}.summary,.board-layout{grid-template-columns:1fr}.evidence-rail{position:static;border-left:0;border-top:3px solid var(--blue);padding:12px 0 0}.module-row,.cascade-row,.evidence-row{grid-template-columns:1fr}.fact-grid{grid-template-columns:1fr}}@media(max-width:420px){main{padding:10px}.view-tabs button{flex:1 1 46%;white-space:normal}.provenance div{grid-template-columns:1fr}.summary article{padding:9px 0}.exposure-control{display:block}.exposure-control select{width:100%;margin-top:4px}}
""".strip()


def _overview(
    payload: Mapping[str, Any],
    modules: Mapping[str, Mapping[str, Any]],
    sources: Mapping[str, Mapping[str, Any]],
    default_id: str,
    plan_available: bool,
) -> str:
    plan = modules["plan_context"]
    holdings = payload["holdings_context"]
    plan_detail = (
        f"<strong>{escape(plan['summary'])}</strong><p>{escape(plan['data']['decision_rules'])}</p>"
        if plan_available
        else "<strong>Plan-linked Macro decision unavailable</strong><p>Plan context is not complete at the decision cutoff.</p>"
    )
    lens = _exposure_lens(payload["exposure_lens"], "overview", plan_available)
    return f"""<section class="view-panel" id="view-overview" data-view="overview" role="tabpanel" aria-labelledby="tab-overview"{_hidden('overview', default_id)}>
<div class="section-head"><h2>Overview</h2><p>Evidence to Transmission to Exposure to Plan Decision</p></div>
<div class="fact-grid"><article><span class="field-label">Active plan</span>{plan_detail}</article><article><span class="field-label">Holdings lens</span><strong>{escape(holdings['summary'])}</strong><p>{'Conditional portfolio impact' if holdings['conditional'] else 'Confirmed portfolio impact'}</p></article></div>
{_cascade(payload['evidence'], payload['exposure_lens'], sources, plan_available)}<div class="section-head"><h2>Holding-first Exposure Lens</h2><p>Drill-down; it does not create the Macro conclusion</p></div>{lens}</section>"""


def _rates(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], sources: Mapping[str, Mapping[str, Any]], default_id: str, plan_available: bool) -> str:
    return _family_view(payload, modules, sources, default_id, plan_available, "Rates &amp; Liquidity", "10Y, 30Y, credit, USD, oil, liquidity; Gold is optional confirmation", "rates-liquidity", "rates_liquidity")


def _inflation(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], sources: Mapping[str, Mapping[str, Any]], default_id: str, plan_available: bool) -> str:
    return _family_view(payload, modules, sources, default_id, plan_available, "Inflation &amp; Growth", "Actuals, forecasts, media context, and thesis remain distinct", "inflation-growth", "inflation_growth")


def _family_view(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], sources: Mapping[str, Mapping[str, Any]], default_id: str, plan_available: bool, title: str, description: str, view_id: str, family: str) -> str:
    return f"""<section class="view-panel" id="view-{view_id}" data-view="{view_id}" role="tabpanel" aria-labelledby="tab-{view_id}"{_hidden(view_id, default_id)}>
<div class="section-head"><h2>{title}</h2><p>{description}</p></div>{_module_row(modules[family])}{_evidence_rows(payload['evidence'], family, sources, plan_available)}</section>"""


def _cross_asset(
    payload: Mapping[str, Any],
    modules: Mapping[str, Mapping[str, Any]],
    sources: Mapping[str, Mapping[str, Any]],
    default_id: str,
    plan_available: bool,
) -> str:
    lens = _exposure_lens(payload['exposure_lens'], 'cross', plan_available)
    fallback = "".join(f"<li>{escape(row['label'])}: {escape(str(row['value']))}</li>" for row in payload['chart_series'])
    return f"""<section class="view-panel" id="view-cross-asset-impact" data-view="cross-asset-impact" role="tabpanel" aria-labelledby="tab-cross-asset-impact"{_hidden('cross-asset-impact', default_id)}>
<div class="section-head"><h2>Cross-Asset Impact</h2><p>Transmission must confirm before changing a plan risk budget</p></div>{_module_row(modules['cross_asset'])}
<div class="chart-shell"><div id="macro-cross-asset-chart" class="macro-chart" role="img" aria-label="Synthetic cross-asset transmission readings"></div><div class="chart-fallback"><strong>Semantic cross-asset fallback</strong><ul>{fallback}</ul></div></div>
{_cascade(payload['evidence'], payload['exposure_lens'], sources, plan_available)}<div class="section-head"><h2>Holding-first Exposure Lens</h2><p>Exposure sensitivity and current plan rules</p></div>{lens}</section>"""


def _scenarios(
    payload: Mapping[str, Any],
    modules: Mapping[str, Mapping[str, Any]],
    default_id: str,
    plan_available: bool,
) -> str:
    rows = "".join(
        f"<article class=\"scenario\"><h3>{escape(item['name'])}</h3><p><strong>Trigger:</strong> {escape(item['trigger'])}</p><p><strong>Confirming observations:</strong> {escape(item['confirms'])}</p><p><strong>Cross-asset:</strong> {escape(item['cross_asset'])}</p><p><strong>Affected exposures:</strong> {escape(', '.join(item['affected_exposures']))}</p>{_scenario_posture(item, plan_available)}</article>"
        for item in payload['scenarios']
    )
    return f"""<section class="view-panel" id="view-event-scenarios" data-view="event-scenarios" role="tabpanel" aria-labelledby="tab-event-scenarios"{_hidden('event-scenarios', default_id)}>
<div class="section-head"><h2>Event Scenarios</h2><p>Trigger to Cross-Asset to Exposure to Posture; ordered by decision impact</p></div>{_module_row(modules['event_scenarios'])}<div class="scenario-list">{rows}</div></section>"""


def _module_row(module: Mapping[str, Any]) -> str:
    details = "".join(
        f"<div><span>{escape(key.replace('_', ' '))}</span>{escape(value or 'Unavailable')}</div>"
        for key, value in module['data'].items()
    )
    return f"""<article class="module-row"><div><h3>{escape(module['id'].replace('_', ' ').title())}</h3><span class="badge {escape(module['evidence_state'])}">{escape(module['evidence_state'])}</span><p class="module-meta">{escape(module['requirement'])}</p></div><div><p>{escape(module['summary'])}</p><div class="fact-grid">{details}</div><p class="module-meta">As of {escape(module['as_of'])} · Gap: {escape(module['gap_reason'] or 'None')}</p></div></article>"""


def _cascade(
    evidence: list[Mapping[str, Any]],
    exposures: list[Mapping[str, Any]],
    sources: Mapping[str, Mapping[str, Any]],
    plan_available: bool,
) -> str:
    exposure_by_id = {item['id']: item for item in exposures}
    rows = "".join(
        f"<article class=\"cascade-row\"><div><span class=\"source-category\">{escape(row['category'])}</span><h3>{escape(row['label'])}</h3><p class=\"module-meta\">{escape(row['status'])} · {escape(row['as_of'])}</p></div><div><p><strong>Evidence:</strong> {escape(row['reading'])}</p><p><strong>Transmission:</strong> {escape(row['transmission'])}</p><p><strong>Exposure:</strong> {escape(exposure_by_id[row['exposure_id']]['label'])}</p>{_source_provenance(row, sources)}{_plan_decision(row, plan_available)}</div></article>"
        for row in evidence
    )
    return f'<div class="cascade">{rows}</div>'


def _evidence_rows(
    evidence: list[Mapping[str, Any]],
    family: str,
    sources: Mapping[str, Mapping[str, Any]],
    plan_available: bool,
) -> str:
    rows = "".join(
        f"<article class=\"evidence-row\"><div><span class=\"source-category\">{escape(row['category'])}</span><p class=\"module-meta\">{escape(row['status'])}</p></div><div><strong>{escape(row['label'])}</strong><p class=\"evidence-reading\">{escape(row['reading'])}</p><p>{escape(row['transmission'])}</p>{_source_provenance(row, sources)}</div>{_plan_effect(row, plan_available)}</article>"
        for row in evidence if row['family'] == family
    )
    return f'<div class="evidence-list">{rows}</div>'


def _exposure_lens(
    exposures: list[Mapping[str, Any]], scope: str, plan_available: bool
) -> str:
    options = "".join(f'<option value="{escape(item["id"])}">{escape(item["label"])}</option>' for item in exposures)
    rows = "".join(
        f"<article class=\"exposure\" data-exposure=\"{escape(item['id'])}\"{' hidden' if index else ''}><h3>{escape(item['label'])}</h3><p><strong>Sensitivity:</strong> {escape(item['sensitivity'])}</p>{_exposure_plan_details(item, plan_available)}</article>"
        for index, item in enumerate(exposures)
    )
    return f"""<div class="exposure-control"><label for="exposure-{scope}">Exposure</label><select id="exposure-{scope}" data-exposure-select>{options}</select></div><div class="exposure-list">{rows}</div>"""


def _source_provenance(
    evidence: Mapping[str, Any], sources: Mapping[str, Mapping[str, Any]]
) -> str:
    source = sources[evidence["source_ref"]]
    return (
        f"<p class=\"module-meta\">Source: {escape(source['alias'])} "
        f"({escape(source['id'])}) · {escape(source['priority'])} · "
        f"{escape(source['freshness_status'])} · {escape(source['as_of'])}</p>"
    )


def _plan_decision(evidence: Mapping[str, Any], plan_available: bool) -> str:
    if not plan_available:
        return ""
    return f"<p><strong>Plan decision:</strong> {escape(evidence['plan_effect'])}</p>"


def _plan_effect(evidence: Mapping[str, Any], plan_available: bool) -> str:
    if not plan_available:
        return ""
    return f'<div><span class="field-label">Plan effect</span><strong>{escape(evidence["plan_effect"])}</strong></div>'


def _exposure_plan_details(exposure: Mapping[str, Any], plan_available: bool) -> str:
    if not plan_available:
        return ""
    return f"<p><strong>Plan rule:</strong> {escape(exposure['plan_rule'])}</p><p><strong>Impact:</strong> {escape(exposure['impact'])}</p>"


def _scenario_posture(scenario: Mapping[str, Any], plan_available: bool) -> str:
    if not plan_available:
        return ""
    return f"<p><strong>Posture consequence:</strong> {escape(scenario['posture'])}</p>"


def _hidden(view_id: str, default_id: str) -> str:
    return "" if view_id == default_id else " hidden"


def _script_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _interaction_script(default_id: str) -> str:
    return f"""
document.documentElement.classList.add('enhanced');
const macroViews=document.querySelectorAll('.view-panel');
const macroTabs=[...document.querySelectorAll('[data-view-target]')];
function selectMacroView(button){{const target=button.dataset.viewTarget;macroViews.forEach((panel)=>{{panel.hidden=panel.dataset.view!==target;}});macroTabs.forEach((item)=>item.setAttribute('aria-selected',String(item===button)));}}
macroTabs.forEach((button,index)=>{{button.addEventListener('click',()=>selectMacroView(button));button.addEventListener('keydown',(event)=>{{if(!['ArrowRight','ArrowLeft'].includes(event.key))return;event.preventDefault();const step=event.key==='ArrowRight'?1:-1;const next=macroTabs[(index+step+macroTabs.length)%macroTabs.length];next.focus();selectMacroView(next);}});}});
document.querySelectorAll('[data-exposure-select]').forEach((select)=>select.addEventListener('change',()=>{{const list=select.closest('.view-panel').querySelectorAll('[data-exposure]');list.forEach((row)=>{{row.hidden=row.dataset.exposure!==select.value;}});}}));
const chart=document.getElementById('macro-cross-asset-chart');
if(chart&&window.echarts){{const chartInstance=echarts.init(chart,null,{{renderer: 'svg'}});chartInstance.setOption({{animation: false,aria: {{ enabled: true }},tooltip:{{show:false}},xAxis:{{type:'category',data:macroBoardPayload.chart_series.map((item)=>item.label)}},yAxis:{{type:'value'}},series:[{{type:'bar',data:macroBoardPayload.chart_series.map((item)=>item.value),itemStyle:{{color:'#1769aa'}}}}]}});document.documentElement.classList.add('chart-ready');window.addEventListener('resize',()=>chartInstance.resize());}}
window.__dailytradesBoardReady=true;
"""
