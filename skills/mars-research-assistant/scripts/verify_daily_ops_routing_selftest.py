#!/usr/bin/env python3
"""Regression coverage for the unscoped Daily Ops Board-first state machine."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from artifact_packet import canonical_json_bytes, sha256_hex
from daily_ops_routing import resolve_daily_ops_route
from research_result import build_delivery_packet


ROOT = Path(__file__).resolve().parents[1]
MACRO_FIXTURE = ROOT / "assets" / "fixtures" / "input" / "macro-regime-complete.json"
PORTFOLIO_FIXTURE = ROOT / "assets" / "fixtures" / "input" / "portfolio-risk-complete.json"
AS_OF = "2026-07-17T10:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _refresh_content_hash(snapshot: dict[str, object]) -> None:
    content = copy.deepcopy(snapshot)
    content.pop("content_hash", None)
    snapshot["content_hash"] = sha256_hex(canonical_json_bytes(content))


def _research_result(
    kind: str,
    visual: dict[str, object],
    *,
    partial: bool = False,
    privacy: str = "public_fixture",
) -> dict[str, object]:
    """Build a minimal public result through the production delivery seam."""

    evidence_status = "partial" if partial else "complete"
    return {
        "schema_version": "1.0",
        "result_kind": kind,
        "as_of": AS_OF,
        "decision": "Preserve the current evidence gate until confirmation.",
        "key_evidence": [
            {
                "label": "Canonical Board fixture",
                "value": "Render through the registered visual adapter.",
                "evidence_type": "fact",
                "status": evidence_status,
                "as_of": AS_OF,
                "source_refs": ["fixture"],
            }
        ],
        "risks": [],
        "scenarios": [],
        "next_checks": ["Refresh the decision-sensitive source."],
        "data_gaps": (
            [
                {
                    "label": "Option overlay Greeks",
                    "reason": "The overlay is excluded from delta and stress arithmetic.",
                    "status": "partial",
                }
            ]
            if partial
            else []
        ),
        "sources": [
            {
                "id": "fixture",
                "label": "Synthetic fixture",
                "priority": "S1",
                "as_of": AS_OF,
            }
        ],
        "privacy": privacy,
        "locale": "zh-CN",
        "visual": visual,
    }


def _require_markers_in_order(html: bytes, markers: tuple[bytes, ...], message: str) -> None:
    positions = [html.find(marker) for marker in markers]
    require(all(position >= 0 for position in positions), message)
    require(positions == sorted(positions), message)


def _option_overlay_snapshot() -> dict[str, object]:
    """Return a valid partial Board where an option's Greeks are unavailable."""

    snapshot = json.loads(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
    payload = snapshot["payload"]
    option = next(
        position
        for position in payload["positions"]
        if position["product_type"] == "option"
    )
    option["option_greeks"] = None
    option["delta_exposure"] = None
    option["source_delta_exposure"] = None

    included = [position for position in payload["positions"] if not position["excluded"]]
    totals = payload["totals"]
    totals["gross_market_value"] = sum(abs(position["market_value"]) for position in included)
    totals["net_market_value"] = sum(position["market_value"] for position in included)
    totals["gross_delta_exposure"] = sum(
        abs(position["delta_exposure"] or 0.0) for position in included
    )
    totals["net_delta_exposure"] = sum(
        position["delta_exposure"] or 0.0 for position in included
    )
    totals["options_delta_included"] = False

    positions_by_id = {position["id"]: position for position in payload["positions"]}
    for rows in payload["aggregations"].values():
        for row in rows:
            positions = [positions_by_id[position_id] for position_id in row["affected_position_ids"]]
            row["direct_market_value"] = sum(position["direct_exposure"] for position in positions)
            row["delta_exposure"] = sum(position["delta_exposure"] or 0.0 for position in positions)
            row["notional_exposure"] = sum(position["notional_exposure"] for position in positions)
            row["weight_pct"] = round(
                100.0
                * sum(abs(position["delta_exposure"] or 0.0) for position in positions)
                / totals["gross_delta_exposure"],
                1,
            )

    missing_option_id = option["id"]
    scope = totals["gross_delta_exposure"]
    unscoped_derivative_notional = abs(option["notional_exposure"])
    for scenario in payload["stress_scenarios"]:
        scenario["affected_position_ids"] = [
            position_id
            for position_id in scenario["affected_position_ids"]
            if position_id != missing_option_id
        ]
        scenario["affected_holdings"] = [
            positions_by_id[position_id]["symbol"]
            for position_id in scenario["affected_position_ids"]
        ]
        scenario["impact_contributions"] = [
            contribution
            for contribution in scenario["impact_contributions"]
            if contribution["position_id"] != missing_option_id
        ]
        scenario["estimated_impact"] = sum(
            contribution["estimated_impact"]
            for contribution in scenario["impact_contributions"]
        )
        scenario["covered_exposure"] = sum(
            abs(positions_by_id[position_id]["delta_exposure"] or 0.0)
            for position_id in scenario["affected_position_ids"]
        )
        scenario["missing_exposure"] = scope - scenario["covered_exposure"]
        scenario["unscoped_derivative_notional"] = unscoped_derivative_notional
        scenario["status"] = "partial"
        scenario["gap_reason"] = "Option overlay Greeks are unavailable and excluded from delta stress."

    for module in payload["modules"]:
        if module["id"] in {"product_risk", "stress_inputs"}:
            module["evidence_state"] = "partial"
            module["gap_reason"] = "Option overlay Greeks are unavailable."
    snapshot["coverage"] = {"required_complete": 4, "required_total": 6}
    snapshot["evidence_state"] = "partial"
    snapshot["state_reasons"].append(
        "Option overlay remains visible but is excluded from delta and stress calculations."
    )
    _refresh_content_hash(snapshot)
    return snapshot


def main() -> int:
    first_turn = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        macro_state="pending",
        broker_authorized=False,
        portfolio_state="not_read",
    )
    require(
        first_turn.required_actions == ("render_macro_research_result_or_blocker",),
        "an unscoped start must deliver Macro before any broker or prose route",
    )
    require(
        {"prose_only_macro_summary", "custom_html_board"}
        <= set(first_turn.forbidden_actions),
        "the Macro Board must not degrade into prose or replacement HTML",
    )

    macro_blocked = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        macro_state="blocked",
        broker_authorized=False,
        portfolio_state="not_read",
    )
    require(
        macro_blocked.required_actions == ("macro_data_acquisition_blocker",),
        "a failed Macro preflight must return the one acquisition blocker",
    )

    after_macro = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        macro_state="delivered",
        broker_authorized=False,
        portfolio_state="not_read",
    )
    require(
        after_macro.required_actions == ("request_read_only_broker_authorization",),
        "broker authorization belongs after the delivered Macro baseline",
    )

    ready = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        macro_state="delivered",
        broker_authorized=True,
        portfolio_state="ready",
    )
    require(
        ready.required_actions
        == ("render_portfolio_research_result", "ask_user_to_select_instrument"),
        "usable holdings must produce the Portfolio Risk Board before an instrument prompt",
    )
    require(
        {"custom_html_board", "individual_research", "price_action"}
        <= set(ready.forbidden_actions),
        "an unscoped portfolio baseline must use its canonical Board before ticker or PA work",
    )

    overlay_partial = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        macro_state="delivered",
        broker_authorized=True,
        portfolio_state="option_overlay_partial",
    )
    require(
        overlay_partial.required_actions
        == ("render_portfolio_research_result_partial", "ask_user_to_select_instrument"),
        "missing option Greeks must yield a partial Portfolio Risk Board, not a broker fallback",
    )
    require(
        "request_secondary_broker" in overlay_partial.forbidden_actions,
        "an option overlay gap must not silently expand the authorized broker scope",
    )
    require(
        "request_secondary_broker" in ready.forbidden_actions,
        "a ready single-broker baseline must not invite a second broker",
    )

    core_gap = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        macro_state="delivered",
        broker_authorized=True,
        portfolio_state="core_gap",
    )
    require(
        core_gap.required_actions == ("portfolio_data_gap",),
        "missing core holdings or capital context must stay a concrete portfolio gap",
    )
    require(
        {"individual_research", "price_action", "request_secondary_broker"}
        <= set(core_gap.forbidden_actions),
        "a core portfolio gap must not turn into ticker research or broker escalation",
    )

    macro_snapshot = json.loads(MACRO_FIXTURE.read_text(encoding="utf-8"))
    macro_delivery = build_delivery_packet(
        _research_result(
            "macro",
            {
                "adapter": "macro",
                "snapshot": macro_snapshot,
                "default_view": "Overview",
            },
        )
    )
    macro_html = macro_delivery.standalone_board.html if macro_delivery.standalone_board else b""
    _require_markers_in_order(
        macro_html,
        (
            b'aria-label="\xe5\xae\x8f\xe8\xa7\x82\xe8\xa7\x86\xe5\x9b\xbe"',
            b'data-view="trend"',
            b'data-view="current"',
            b'data-view="events"',
            b'data-view="scenarios"',
        ),
        "the Macro delivery must retain the frozen canonical view controls",
    )
    for anchor in (b"macro-summary", b"trend-chart", b"scenario-grid"):
        require(
            anchor in macro_html,
            f"the Macro delivery must retain the frozen renderer anchor: {anchor.decode()}",
        )

    portfolio_delivery = build_delivery_packet(
        _research_result(
            "portfolio",
            {"adapter": "portfolio", "panel": _option_overlay_snapshot()},
            partial=True,
        )
    )
    html = portfolio_delivery.standalone_board.html if portfolio_delivery.standalone_board else b""
    require(
        b"Greeks unavailable" in html,
        "the Portfolio Risk Board must visibly disclose missing option Greeks",
    )
    require(
        b"Option overlay Greeks are unavailable" in html,
        "the partial product-risk and stress gap must stay visible in the Board",
    )
    require(
        b"SAMP 2026-09 C220" in html,
        "the reported partial option must remain visible in the frozen Board",
    )
    _require_markers_in_order(
        html,
        (
            b'aria-label="\xe7\xbb\x84\xe5\x90\x88\xe9\xa3\x8e\xe9\x99\xa9\xe8\xa7\x86\xe5\x9b\xbe"',
            b'data-view="overview"',
            b'data-view="symbol"',
            b'data-view="fundamentals"',
            b'data-view="theme"',
            b'data-view="product"',
            b'data-view="broker"',
            b'data-view="stress"',
        ),
        "the partial Portfolio delivery must retain the frozen seven-view control order",
    )
    for anchor in (
        b"portfolio-summary",
        b"fundamentals-panel",
        b"stress-panel",
        b"risk-ledger-row",
    ):
        require(
            anchor in html,
            f"the Portfolio delivery must retain the frozen renderer anchor: {anchor.decode()}",
        )

    private_overlay = _option_overlay_snapshot()
    private_overlay["privacy"] = "private_runtime"
    _refresh_content_hash(private_overlay)
    private_delivery = build_delivery_packet(
        _research_result(
            "portfolio",
            {"adapter": "portfolio", "panel": private_overlay},
            partial=True,
            privacy="private",
        )
    )
    require(
        private_delivery.standalone_board is not None
        and b"Option overlay Greeks are unavailable" in private_delivery.standalone_board.html,
        "a private canonical snapshot must project into the same frozen partial Board",
    )

    explicit_instrument = resolve_daily_ops_route(
        intent="instrument_request",
        macro_state="pending",
        broker_authorized=False,
        portfolio_state="not_read",
    )
    require(
        explicit_instrument.required_actions == ("instrument_research_or_price_action",),
        "a user-named instrument may take the focused route",
    )

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    operations = (ROOT / "references" / "operations.md").read_text(encoding="utf-8")
    template = (ROOT / "assets" / "templates" / "daily-ops-orchestrator.md").read_text(encoding="utf-8")
    require("## Unscoped Daily Ops Baseline" in skill, "Skill must expose the Board-first baseline")
    require("## Unscoped Daily Ops Baseline" in operations, "operations must own the Board-first baseline")
    require("## 无标的 Daily Ops 启动基线" in template, "Daily Ops template must retain the Board-first baseline")
    for document, label in ((skill, "Skill"), (operations, "operations"), (template, "template")):
        require(
            "daily_ops_routing.py" in document and "option_overlay_partial" in document,
            f"{label} must require the executable phase gate and partial option path",
        )
        require(
            "request/read another broker" in document
            or "second broker" in document
            or "请求第二券商" in document
            or "request_secondary_broker" in document
            or "第二券商" in document,
            f"{label} must prohibit automatic secondary-broker escalation",
        )
    require(
        "not an individual-option" in skill,
        "Skill must keep option-purpose explanations out of individual research",
    )
    for document, label in ((skill, "Skill"), (operations, "operations"), (template, "template")):
        require(
            "first decision-bearing" in document or "第一个决策性用户交付" in document,
            f"{label} must put the required Board or Blocker before prose status output",
        )
        require(
            "ResearchResult" in document
            and "research_result.py" in document
            and "visualize" in document,
            f"{label} must require the canonical renderer and prohibit alternate visuals",
        )

    print("daily ops routing selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
