#!/usr/bin/env python3
"""Regression coverage for the unscoped Daily Ops Board-first state machine."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from artifact_packet import build_artifact_packet, canonical_json_bytes, sha256_hex
from daily_ops_routing import resolve_daily_ops_route


ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_FIXTURE = ROOT / "assets" / "fixtures" / "input" / "portfolio-risk-complete.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _refresh_content_hash(snapshot: dict[str, object]) -> None:
    content = copy.deepcopy(snapshot)
    content.pop("content_hash", None)
    snapshot["content_hash"] = sha256_hex(canonical_json_bytes(content))


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
        first_turn.required_actions == ("macro_board_or_blocker",),
        "an unscoped start must deliver Macro before any broker or prose route",
    )
    require(
        "prose_only_macro_summary" in first_turn.forbidden_actions,
        "the Macro Board must not degrade into a prose-only summary",
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
        ready.required_actions == ("portfolio_risk_board", "ask_user_to_select_instrument"),
        "usable holdings must produce the Portfolio Risk Board before an instrument prompt",
    )
    require(
        "individual_research" in ready.forbidden_actions
        and "price_action" in ready.forbidden_actions,
        "an unscoped portfolio baseline must not select an individual ticker or PA path",
    )

    overlay_partial = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        macro_state="delivered",
        broker_authorized=True,
        portfolio_state="option_overlay_partial",
    )
    require(
        overlay_partial.required_actions == ("portfolio_risk_board_partial", "ask_user_to_select_instrument"),
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

    packet = build_artifact_packet(_option_overlay_snapshot())
    html = packet.html.decode("utf-8")
    require(
        "Greeks unavailable" in html,
        "the Portfolio Risk Board must visibly disclose missing option Greeks",
    )
    require(
        "Option overlay Greeks are unavailable" in html,
        "the partial product-risk and stress gap must stay visible in the Board",
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

    print("daily ops routing selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
