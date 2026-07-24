#!/usr/bin/env python3
"""Purpose-specific renderer for one validated Portfolio Risk Board snapshot."""

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

VIEW_IDS = {
    "Overview": "overview",
    "By Symbol": "by-symbol",
    "By Theme / Industry": "by-theme-industry",
    "By Product": "by-product",
    "By Broker": "by-broker",
    "Stress Tests": "stress-tests",
}


def render_portfolio_risk_board(
    snapshot: Mapping[str, Any], default_view: str, presentation_state: str, *, echarts_source: str
) -> bytes:
    payload = snapshot["payload"]
    modules = {module["id"]: module for module in payload["modules"]}
    default_id = VIEW_IDS[default_view]
    totals = payload["totals"]
    body = f"""{render_main_open('portfolio-risk-board')}
{render_masthead(eyebrow='Portfolio risk · confirmed-source scope', title='Portfolio Risk Board', question=payload['question'], snapshot_id=snapshot['snapshot_id'], decision_cutoff=snapshot['decision_cutoff'], privacy=snapshot['privacy'])}
{render_view_tabs(payload['views'], default_view, VIEW_IDS, 'Portfolio Risk views')}
{render_summary([
    ('Risk posture', payload['posture']['label'], presentation_state),
    ('Evidence coverage', f"{snapshot['coverage']['required_complete']}/{snapshot['coverage']['required_total']} required complete", snapshot['evidence_state']),
    ('Confirmed scope', totals['scope_label'], f"{len(totals['confirmed_source_refs'])} position-detail sources"),
    ('Cash / collateral context', _money(totals['cash_context']), totals['currency']),
], 'Portfolio risk summary')}
<section class="decision-card"><h2>Current portfolio decision</h2><p>{escape(payload['decision'])}</p>{render_decision_framing('Plan constraint', payload['plan_context']['constraints'])}</section>
<div class="board-layout"><div class="primary-flow">
{_overview(payload, modules, default_id)}
{_aggregation_view('By Symbol', 'by-symbol', payload['aggregations']['by_symbol'], default_id)}
{_theme_industry_view(payload, default_id)}
{_product_view(payload, default_id)}
{_broker_view(payload, default_id)}
{_stress_view(payload, modules, default_id)}
</div>{render_evidence_rail(snapshot, _evidence_rail_items(payload), 'At least one usable position-detail source; complete additionally requires reconciled detail, product fields, mappings, and stress inputs.')}</div>
{render_safety_footer('Decision support only. This artifact is offline, read-only, and performs no external data access or trade execution.')}
</main>"""
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none';"><title>Portfolio Risk Board</title><style>{_styles()}</style></head><body>{body}<script>{echarts_source}</script><script>const portfolioRiskPayload={_script_json(payload)};{_interaction_script(default_id)}</script></body></html>"""
    return html.encode("utf-8")


def _evidence_rail_items(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = list(payload["modules"])
    items.extend(
        {
            "id": f'stress:{scenario["name"]}',
            "evidence_state": scenario["status"],
            "gap_reason": scenario["gap_reason"],
        }
        for scenario in payload["stress_scenarios"]
    )
    return items


def _overview(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], default_id: str) -> str:
    totals = payload["totals"]
    symbol_rows = payload["aggregations"]["by_symbol"]
    top_weight = symbol_rows[0]["weight_pct"] if symbol_rows else None
    top_label = symbol_rows[0]["label"] if symbol_rows else "Unavailable"
    metrics = (
        ("Gross market value", _money(totals["gross_market_value"])),
        ("Gross delta", _money(totals["gross_delta_exposure"])),
        ("Cash context", _money(totals["cash_context"])),
        (
            f"Top look-through · {top_label}",
            "Unavailable" if top_weight is None else f"{top_weight:.1f}%",
        ),
    )
    metric_cards = "".join(
        f'<article><span>{escape(label)}</span><strong>{escape(value)}</strong></article>'
        for label, value in metrics
    )
    chart_fallback = "".join(
        f'<li>{escape(row["label"])}: {row["weight_pct"]:.1f}%</li>'
        for row in symbol_rows
    ) or "<li>Confirmed symbol exposure is unavailable.</li>"
    ledger = "".join(
        f'<article class="ledger-row"><div><span class="badge {escape(item["severity"])}">{escape(item["severity"])}</span><h3>{escape(item["exposure"])}</h3></div><div><p><strong>Risk issue:</strong> {escape(item["risk_issue"])}</p><p><strong>Affected holdings:</strong> {escape(", ".join(item["affected_holdings"]))}</p><p><strong>Plan constraint:</strong> {escape(item["plan_constraint"])}</p></div></article>'
        for item in payload["risk_ledger"]
    )
    spine = "".join(
        f'<article class="spine-row"><h3>{escape(item["exposure"])}</h3><p>{escape(item["risk_issue"])}</p><p><strong>Across:</strong> {escape(" → ".join(item["decompositions"]))}</p><p><strong>Constraint:</strong> {escape(item["plan_constraint"])}</p></article>'
        for item in payload["exposure_spine"]
    )
    module_rows = "".join(_module_row(modules[module_id]) for module_id in modules)
    return f"""<section class="view-panel" id="view-overview" data-view="overview" role="tabpanel" aria-labelledby="tab-overview"{_hidden('overview', default_id)}><div class="section-head"><h2>Confirmed exposure now</h2><p>Numbers and concentration first</p></div><div class="risk-metrics">{metric_cards}</div><div class="chart-shell"><div id="portfolio-overview-chart" class="chart" role="img" aria-label="Confirmed look-through exposure by symbol"></div><div class="chart-fallback"><strong>Look-through weights</strong><ul>{chart_fallback}</ul></div></div><div class="section-head"><h2>Risk Decision Ledger</h2><p>Exposure → Risk issue → Affected holdings → Plan constraint</p></div><div class="ledger">{ledger}</div><div class="section-head"><h2>Exposure Spine</h2><p>Follow one correlated risk through every decomposition</p></div><div class="spine">{spine}</div><div class="section-head"><h2>Evidence modules</h2><p>Coverage and gaps remain visible</p></div>{module_rows}{_exclusions(payload)}</section>"""


def _aggregation_view(title: str, view_id: str, rows: list[Mapping[str, Any]], default_id: str) -> str:
    content = "".join(_aggregation_row(row) for row in rows)
    return f'<section class="view-panel" id="view-{view_id}" data-view="{view_id}" role="tabpanel" aria-labelledby="tab-{view_id}"{_hidden(view_id, default_id)}><div class="section-head"><h2>{escape(title)}</h2><p>Direct market value, delta/notional, look-through duplication, and plan limit</p></div><div class="aggregation-list">{content}</div></section>'


def _theme_industry_view(payload: Mapping[str, Any], default_id: str) -> str:
    themes = "".join(_aggregation_row(row) for row in payload["aggregations"]["by_theme"])
    industries = "".join(_aggregation_row(row) for row in payload["aggregations"]["by_industry"])
    return f'<section class="view-panel" id="view-by-theme-industry" data-view="by-theme-industry" role="tabpanel" aria-labelledby="tab-by-theme-industry"{_hidden("by-theme-industry", default_id)}><div class="section-head"><h2>Theme decomposition</h2><p>Look-through themes retain plan limits and affected holdings</p></div><div class="aggregation-list">{themes}</div><div class="section-head"><h2>Industry decomposition</h2><p>Industry concentration remains independently inspectable</p></div><div class="aggregation-list">{industries}</div></section>'


def _aggregation_row(row: Mapping[str, Any]) -> str:
    return f'<article class="aggregation-row"><div><h3>{escape(row["label"])}</h3><span class="metric">{row["weight_pct"]:.1f}% delta weight</span></div><dl><div><dt>Direct market value</dt><dd>{row["direct_market_value"]:,.0f}</dd></div><div><dt>Delta exposure</dt><dd>{row["delta_exposure"]:,.0f}</dd></div><div><dt>Notional exposure</dt><dd>{row["notional_exposure"]:,.0f}</dd></div></dl><p><strong>Affected holdings:</strong> {escape(", ".join(row["affected_holdings"]))}</p><p><strong>Plan limit:</strong> {escape(row["plan_limit"])}</p></article>'


def _product_view(payload: Mapping[str, Any], default_id: str) -> str:
    products = "".join(_aggregation_row(row) for row in payload["aggregations"]["by_product"])
    positions = "".join(
        f'<article class="product-detail"><h3>{escape(item["symbol"])}</h3><p>{escape(item["product_type"])} · underlying {escape(item["underlying"])}</p><dl><div><dt>Market value</dt><dd>{_money(item["market_value"])}</dd></div><div><dt>Delta</dt><dd>{_money(item["delta_exposure"])}</dd></div><div><dt>Notional</dt><dd>{_money(item["notional_exposure"])}</dd></div><div><dt>Leverage / reset</dt><dd>{item["leverage_multiple"]:.1f}x · {escape(item["reset_frequency"])}</dd></div><div><dt>Liquidity</dt><dd>{escape(item["liquidity_status"])}</dd></div><div><dt>Risk horizon</dt><dd>{escape(item["risk_horizon"].replace("_", " "))}</dd></div><div><dt>Expiry</dt><dd>{escape(item["expiry_at"] or "Not applicable")}</dd></div></dl><p><strong>Path risk:</strong> {escape(item["path_dependency"])}</p>{_greeks(item)}</article>'
        for item in payload["positions"]
        if not item["excluded"]
    )
    return f'<section class="view-panel" id="view-by-product" data-view="by-product" role="tabpanel" aria-labelledby="tab-by-product"{_hidden("by-product", default_id)}><div class="section-head"><h2>By Product</h2><p>Market value never substitutes for horizon, leverage, delta, notional, reset, liquidity, or convexity</p></div><div class="aggregation-list">{products}</div><div class="product-grid">{positions}</div></section>'


def _greeks(position: Mapping[str, Any]) -> str:
    greeks = position["option_greeks"]
    if not greeks:
        return '<p><strong>Greeks unavailable:</strong> option delta, convexity, and related stress claims remain partial.</p>' if position["product_type"] == "option" else ""
    return f'<p><strong>Greeks:</strong> delta {greeks["delta"]:.2f} · gamma {greeks["gamma"]:.3f} · vega {greeks["vega"]:.2f} · theta {greeks["theta"]:.2f}</p>'


def _broker_view(payload: Mapping[str, Any], default_id: str) -> str:
    exposure_rows = "".join(_aggregation_row(row) for row in payload["aggregations"]["by_broker"])
    rows = "".join(
        f'<article class="broker-row"><div><h3>{escape(item["source_alias"])}</h3><p>{escape(item["account_alias"])}</p></div><dl><div><dt>Coverage</dt><dd>{escape(item["detail_status"])}</dd></div><div><dt>Reconciliation</dt><dd>{escape(item["reconciliation_status"])}</dd></div><div><dt>Currency</dt><dd>{escape(item["source_currency"])} → {escape(item["currency"])}</dd></div><div><dt>NAV context</dt><dd>{_money(item["source_nav_context"])} → {_money(item["nav_context"])}</dd></div><div><dt>FX rate</dt><dd>{item["fx_rate_to_base"]:.8g}</dd></div><div><dt>FX source / as of</dt><dd>{escape(item["fx_source_ref"] or "identity conversion")} · {escape(item["fx_as_of"])}</dd></div><div><dt>As of</dt><dd>{escape(item["as_of"])}</dd></div></dl><p>{escape(item["gap_reason"] or "No source gap")}</p></article>'
        for item in payload["source_coverage"]
    )
    conversions = "".join(_currency_conversion_row(item) for item in payload["positions"])
    conversions = conversions or "<p>No position-level conversions available.</p>"
    balances = "".join(_cash_collateral_row(item) for item in payload["cash_collateral"])
    balances = balances or "<p>No confirmed cash or collateral balances available.</p>"
    return f'<section class="view-panel" id="view-by-broker" data-view="by-broker" role="tabpanel" aria-labelledby="tab-by-broker"{_hidden("by-broker", default_id)}><div class="section-head"><h2>Broker exposure</h2><p>Confirmed market value, delta, notional, weight, holdings, and plan limit</p></div><div class="aggregation-list">{exposure_rows}</div><div class="section-head"><h2>Source coverage</h2><p>Position-detail scope remains separate from NAV-only context</p></div><div class="broker-list">{rows}</div><div class="section-head"><h2>Cash and collateral balances</h2><p>Explicit source balances retain account, conversion, and timestamp provenance</p></div><div class="broker-list">{balances}</div><div class="section-head"><h2>Currency conversion</h2><p>Every broker-reported position retains source values, base values, rate, source, and timestamp</p></div><div class="broker-list">{conversions}</div>{_exclusions(payload)}</section>'


def _cash_collateral_row(item: Mapping[str, Any]) -> str:
    return f'<article class="broker-row"><div><h3>{escape(item["source_alias"])}</h3><p>{escape(item["account_alias"])}</p></div><dl><div><dt>Cash balance</dt><dd>{_money(item["source_cash_balance"])} → {_money(item["cash_balance"])}</dd></div><div><dt>Collateral value</dt><dd>{_money(item["source_collateral_value"])} → {_money(item["collateral_value"])}</dd></div><div><dt>Currency</dt><dd>{escape(item["source_currency"])} → {escape(item["currency"])}</dd></div><div><dt>FX rate</dt><dd>{item["fx_rate_to_base"]:.8g}</dd></div><div><dt>FX source / as of</dt><dd>{escape(item["fx_source_ref"] or "identity conversion")} · {escape(item["fx_as_of"])}</dd></div><div><dt>Balance source / as of</dt><dd>{escape(item["source_ref"])} · {escape(item["as_of"])}</dd></div></dl></article>'


def _currency_conversion_row(item: Mapping[str, Any]) -> str:
    status = "excluded from analytics" if item["excluded"] else "included"
    return f'<article class="broker-row currency-conversion"><div><h3>{escape(item["symbol"])}</h3><p>{escape(item["source_currency"])} → {escape(item["currency"])} · {escape(status)}</p></div><dl><div><dt>Market value</dt><dd>{_money(item["source_market_value"])} → {_money(item["market_value"])}</dd></div><div><dt>Direct exposure</dt><dd>{_money(item["source_direct_exposure"])} → {_money(item["direct_exposure"])}</dd></div><div><dt>Delta exposure</dt><dd>{_money(item["source_delta_exposure"])} → {_money(item["delta_exposure"])}</dd></div><div><dt>Notional exposure</dt><dd>{_money(item["source_notional_exposure"])} → {_money(item["notional_exposure"])}</dd></div><div><dt>FX rate</dt><dd>{item["fx_rate_to_base"]:.8g}</dd></div><div><dt>FX source / as of</dt><dd>{escape(item["fx_source_ref"] or "identity conversion")} · {escape(item["fx_as_of"])}</dd></div></dl></article>'


def _exclusions(payload: Mapping[str, Any]) -> str:
    if not payload["exclusions"]:
        return '<section class="exclusions"><h2>User-excluded holdings</h2><p>No user-excluded holdings in this snapshot.</p></section>'
    rows = "".join(
        f'<article><h3>{escape(item["symbol"])}</h3><p>Reported by {escape(item["source_alias"])} / {escape(item["account_alias"])} at {escape(item["as_of"])}</p><p><strong>Reported exposure:</strong> {_money(item["reported_exposure"])}</p><p><strong>Authorized scope:</strong> {escape(item["authorized_scope"])}</p><p><strong>Exclusion policy:</strong> {escape(item["exclusion_policy"])}</p><p><strong>Reason:</strong> {escape(item["reason"])}</p><p><strong>Affected totals:</strong> {escape(", ".join(item["affected_totals"]))}</p><p><strong>Affected scenarios:</strong> {escape(", ".join(item["affected_scenarios"]))}</p></article>'
        for item in payload["exclusions"]
    )
    return f'<section class="exclusions"><h2>User-excluded holdings</h2><p>Broker-reported positions remain disclosed even when excluded from calculations.</p>{rows}</section>'


def _stress_view(payload: Mapping[str, Any], modules: Mapping[str, Mapping[str, Any]], default_id: str) -> str:
    positions_by_id = {position["id"]: position for position in payload["positions"]}
    rows = "".join(
        _stress_row(item, positions_by_id, payload["totals"]["currency"])
        for item in payload["stress_scenarios"]
    )
    return f'<section class="view-panel" id="view-stress-tests" data-view="stress-tests" role="tabpanel" aria-labelledby="tab-stress-tests"{_hidden("stress-tests", default_id)}><div class="section-head"><h2>Stress-to-Decision Lab</h2><p>Assumptions → covered exposure → impact → confidence/gaps → plan posture</p></div>{_module_row(modules["stress_inputs"])}<div id="portfolio-stress-chart" class="chart" role="img" aria-label="Estimated additive scenario impacts"></div><div class="stress-list">{rows}</div></section>'


def _stress_row(
    item: Mapping[str, Any],
    positions_by_id: Mapping[str, Mapping[str, Any]],
    currency: str,
) -> str:
    contributions = "; ".join(
        f'{positions_by_id[contribution["position_id"]]["symbol"]}: {contribution["shock_pct"] * 100:.2f}% shock → {_money(contribution["estimated_impact"])}'
        for contribution in item["impact_contributions"]
    )
    return f'<article class="stress-row"><div><span class="badge {escape(item["status"])}">{escape(item["status"])} · {escape(item["confidence"])} confidence</span><h3>{escape(item["name"])}</h3></div><p><strong>Scenario gap:</strong> {escape(item["gap_reason"] or "None")}</p><p><strong>Assumptions:</strong> {escape("; ".join(item["assumptions"]))}</p><p><strong>Coverage basis:</strong> Gross delta exposure</p><p><strong>Impact model:</strong> {escape(item["impact_model"])}</p><dl><div><dt>Covered delta exposure</dt><dd>{item["covered_exposure"]:,.0f}</dd></div><div><dt>Missing delta exposure</dt><dd>{item["missing_exposure"]:,.0f}</dd></div><div><dt>Unscoped derivative notional</dt><dd>{item["unscoped_derivative_notional"]:,.0f}</dd></div><div><dt>Unscoped NAV context ({escape(currency)})</dt><dd>{item["unscoped_nav_context"]:,.0f}</dd></div><div><dt>Estimated impact</dt><dd>{item["estimated_impact"]:,.0f}</dd></div></dl><p><strong>Impact contributions:</strong> {escape(contributions)}</p><p><strong>Affected holdings:</strong> {escape(", ".join(item["affected_holdings"]))}</p><p><strong>Plan constraint:</strong> {escape(item["plan_constraint"])}</p><p class="module-meta">Versioned position-delta-times-shock additive model · no diversification credit</p></article>'


def _module_row(module: Mapping[str, Any]) -> str:
    facts = "".join(f'<div><span>{escape(key.replace("_", " "))}</span><strong>{escape(value)}</strong></div>' for key, value in module["data"].items())
    return f'<article class="module-row"><div><h3>{escape(module["id"].replace("_", " ").title())}</h3><span class="badge {escape(module["evidence_state"])}">{escape(module["evidence_state"])}</span></div><div><p>{escape(module["summary"])}</p><div class="fact-grid">{facts}</div><p class="module-meta">As of {escape(module["as_of"])} · Gap: {escape(module["gap_reason"] or "None")}</p></div></article>'


def _hidden(view_id: str, default_id: str) -> str:
    del default_id
    return "" if view_id == "overview" else " hidden"


def _money(value: int | float | None) -> str:
    return "Unavailable" if value is None else f"{value:,.0f}"


def _script_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _interaction_script(default_id: str) -> str:
    return f"""
document.documentElement.classList.add('enhanced');
const portfolioPanels=[...document.querySelectorAll('[data-view]')];
const portfolioTabs=[...document.querySelectorAll('[data-view-target]')];
let portfolioStressChart=null;
let portfolioOverviewChart=null;
function selectPortfolioView(button){{const target=button.dataset.viewTarget;portfolioPanels.forEach((panel)=>panel.hidden=panel.dataset.view!==target);portfolioTabs.forEach((item)=>item.setAttribute('aria-selected',String(item===button)));if(target==='stress-tests'&&portfolioStressChart){{requestAnimationFrame(()=>portfolioStressChart.resize());}}if(target==='overview'&&portfolioOverviewChart){{requestAnimationFrame(()=>portfolioOverviewChart.resize());}}}}
portfolioTabs.forEach((button,index)=>{{button.addEventListener('click',()=>selectPortfolioView(button));button.addEventListener('keydown',(event)=>{{if(!['ArrowRight','ArrowLeft'].includes(event.key))return;event.preventDefault();const step=event.key==='ArrowRight'?1:-1;const next=portfolioTabs[(index+step+portfolioTabs.length)%portfolioTabs.length];next.focus();selectPortfolioView(next);}});}});
selectPortfolioView(portfolioTabs.find((button)=>button.dataset.viewTarget==={json.dumps(default_id)})||portfolioTabs[0]);
const overviewChart=document.getElementById('portfolio-overview-chart');
if(overviewChart&&window.echarts&&portfolioRiskPayload.aggregations.by_symbol.length){{portfolioOverviewChart=echarts.init(overviewChart,null,{{renderer:'svg'}});portfolioOverviewChart.setOption({{animation:false,aria:{{enabled:true}},grid:{{left:124,right:36,top:18,bottom:28}},tooltip:{{trigger:'axis',valueFormatter:(value)=>value.toFixed(1)+'%'}},xAxis:{{type:'value',max:100,axisLabel:{{formatter:'{{value}}%'}},splitLine:{{lineStyle:{{color:'#e5e9ed'}}}}}},yAxis:{{type:'category',data:portfolioRiskPayload.aggregations.by_symbol.map((item)=>item.label),axisTick:{{show:false}},axisLine:{{show:false}}}},series:[{{type:'bar',barWidth:22,data:portfolioRiskPayload.aggregations.by_symbol.map((item)=>item.weight_pct),itemStyle:{{color:'#1769aa'}},label:{{show:true,position:'right',formatter:'{{c}}%'}}}}]}});document.documentElement.classList.add('overview-chart-ready');}}
const stressChart=document.getElementById('portfolio-stress-chart');
if(stressChart&&window.echarts){{portfolioStressChart=echarts.init(stressChart,null,{{renderer:'svg'}});portfolioStressChart.setOption({{baseOption:{{animation:false,aria:{{enabled:true}},tooltip:{{show:false}},xAxis:{{type:'value'}},yAxis:{{type:'category',data:portfolioRiskPayload.stress_scenarios.map((item)=>item.name)}},series:[{{type:'bar',data:portfolioRiskPayload.stress_scenarios.map((item)=>item.estimated_impact),itemStyle:{{color:'#b43b32'}}}}]}},media:[{{query:{{maxWidth:360}},option:{{grid:{{left:145,right:12,bottom:20}},xAxis:{{axisLabel:{{show:false}}}}}}}}]}});document.documentElement.classList.add('chart-ready');window.addEventListener('resize',()=>{{portfolioStressChart.resize();if(portfolioOverviewChart)portfolioOverviewChart.resize();}});}}
window.__marsResearchAssistantBoardReady=true;
"""


def _styles() -> str:
    return f"""
:root{{--bg:#f7f8fa;--surface:#fff;--ink:#17202a;--muted:#65717e;--line:#dce2e8;--accent:#1769aa;--danger:#b43b32;--warn:#9a6700;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--ink);background:var(--bg)}}*{{box-sizing:border-box}}body{{margin:0;padding:16px;background:var(--bg);color:var(--ink)}}{shared_shell_styles()}main{{max-width:1180px;margin:auto}}.masthead,.section-head,.decision-card,.summary article,.risk-metrics article,.module-row,.ledger-row,.spine-row,.aggregation-row,.product-detail,.broker-row,.stress-row,.exclusions,.evidence-rail,footer{{background:var(--surface);border:1px solid var(--line);border-radius:8px}}.masthead{{display:flex;justify-content:space-between;gap:20px;padding:20px}}h1,h2,h3,p{{margin-top:0}}.eyebrow,.module-meta,.source-time,dt{{color:var(--muted);font-size:.82rem}}.provenance{{display:grid;gap:8px;min-width:250px}}.provenance div,dl div{{display:flex;justify-content:space-between;gap:14px}}.provenance dt,.provenance dd,dl dd{{margin:0}}.view-tabs{{display:none;flex-wrap:wrap;gap:6px;margin:14px 0}}.enhanced .view-tabs{{display:flex}}button{{border:1px solid var(--line);background:var(--surface);padding:8px 10px;border-radius:6px;color:inherit}}button[aria-selected=true]{{background:var(--ink);color:white}}button:focus-visible{{outline:3px solid #69a7d6;outline-offset:2px}}.summary,.risk-metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}.summary article,.risk-metrics article{{padding:14px}}.summary span,.risk-metrics span{{display:block;color:var(--muted);font-size:.78rem;text-transform:uppercase}}.summary strong,.risk-metrics strong{{display:block;margin-top:5px}}.risk-metrics strong{{font-size:1.45rem}}.decision-card{{padding:18px;margin:12px 0}}.decision-framing{{margin-bottom:0}}.board-layout{{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:14px;align-items:start}}.primary-flow,.ledger,.spine,.aggregation-list,.product-grid,.broker-list,.stress-list{{display:grid;gap:10px}}.view-panel{{display:grid;gap:10px}}.section-head{{display:flex;justify-content:space-between;gap:12px;padding:12px 14px;align-items:baseline}}.section-head h2,.section-head p{{margin:0}}.ledger-row,.module-row{{display:grid;grid-template-columns:minmax(150px,.45fr) minmax(0,1.55fr);gap:14px;padding:14px}}.spine-row,.aggregation-row,.product-detail,.broker-row,.stress-row,.exclusions{{padding:14px}}.aggregation-row dl,.product-detail dl,.broker-row dl,.stress-row dl,.fact-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}}.aggregation-row dl div,.product-detail dl div,.broker-row dl div,.stress-row dl div,.fact-grid div{{display:grid;gap:2px;padding:8px;background:#f3f5f7;border-radius:6px}}.metric,.badge{{display:inline-block;padding:3px 7px;border-radius:999px;background:#e8eef5;font-size:.78rem}}.badge.high,.badge.source_error{{background:#fde7e5;color:#8f261e}}.badge.medium,.badge.partial,.badge.stale{{background:#fff0cf;color:#765000}}.badge.complete{{background:#e5f3e8;color:#246a36}}.evidence-rail{{padding:14px;position:sticky;top:10px}}.evidence-rail ul{{padding-left:18px}}.evidence-rail li{{margin-bottom:9px}}.source-time{{display:block}}.chart-shell{{position:relative}}.chart{{height:280px;background:var(--surface);border:1px solid var(--line);border-radius:8px}}.chart-fallback{{padding:14px;background:var(--surface);border:1px solid var(--line);border-radius:8px}}.overview-chart-ready .chart-fallback{{display:none}}footer{{padding:14px;margin-top:14px}}.enhanced [data-view][hidden]{{display:none!important}}@media(max-width:760px){{body{{padding:8px}}.masthead{{display:grid}}.provenance{{min-width:0}}.summary,.board-layout{{grid-template-columns:1fr}}.risk-metrics{{grid-template-columns:repeat(2,minmax(0,1fr))}}.evidence-rail{{position:static}}.ledger-row,.module-row{{grid-template-columns:1fr}}}}@media(max-width:380px){{.summary,.risk-metrics{{grid-template-columns:1fr}}.section-head{{display:grid}}button{{flex:1 1 46%}}}}
"""
