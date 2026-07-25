#!/usr/bin/env python3
"""Behavior checks for the guided Mars Daily Ops router."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from artifact_packet import canonical_json_bytes, sha256_hex
from daily_ops_routing import resolve_daily_ops_route
from research_result import build_delivery_packet


ROOT = Path(__file__).resolve().parents[1]
MACRO_FIXTURE = ROOT / "assets" / "fixtures" / "input" / "macro-regime-complete.json"
AS_OF = "2026-07-17T10:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _refresh_content_hash(snapshot: dict[str, object]) -> None:
    content = copy.deepcopy(snapshot)
    content.pop("content_hash", None)
    snapshot["content_hash"] = sha256_hex(canonical_json_bytes(content))


def _macro_result(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "result_kind": "macro",
        "as_of": AS_OF,
        "decision": "Preserve the current evidence gate until confirmation.",
        "key_evidence": [
            {
                "label": "Canonical Board fixture",
                "value": "Render through the registered visual adapter.",
                "evidence_type": "fact",
                "status": "complete",
                "as_of": AS_OF,
                "source_refs": ["fixture"],
            }
        ],
        "risks": [],
        "scenarios": [],
        "next_checks": ["Refresh the decision-sensitive source."],
        "data_gaps": [],
        "sources": [{"id": "fixture", "label": "Synthetic fixture", "priority": "S1", "as_of": AS_OF}],
        "privacy": "public_fixture",
        "locale": "zh-CN",
        "visual": {"adapter": "macro", "snapshot": snapshot, "default_view": "Overview"},
    }


def main() -> int:
    capability_pending = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        capability_state="pending",
        macro_state="pending",
        holdings_review="undecided",
        holdings_state="not_read",
    )
    require(
        capability_pending.required_actions == ("check_broker_capability",),
        "an unscoped start must check both broker capabilities before Macro acquisition",
    )
    require(
        {"read_default_broker_holdings", "derived_holdings_risk_analysis", "price_action"}
        <= set(capability_pending.forbidden_actions),
        "a capability check must not read private holdings or start analysis",
    )

    macro_pending = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        capability_state="checked",
        macro_state="pending",
        holdings_review="undecided",
        holdings_state="not_read",
    )
    require(
        macro_pending.required_actions == ("acquire_macro_fields_and_render_research_result_or_blocker",),
        "an unscoped start must automatically deliver Macro after capability detection",
    )

    after_macro = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        capability_state="checked",
        macro_state="delivered",
        holdings_review="undecided",
        holdings_state="not_read",
    )
    require(
        after_macro.required_actions == ("offer_next_research_action",),
        "Macro completion must guide the user rather than force a holdings read",
    )
    require(
        "derived_holdings_risk_analysis" in after_macro.forbidden_actions,
        "the guided flow must never derive risk analysis from an optional display",
    )

    holdings_requested = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        capability_state="checked",
        macro_state="delivered",
        holdings_review="requested",
        holdings_state="not_read",
    )
    require(
        holdings_requested.required_actions == ("read_consented_default_broker_holdings_and_render_display",),
        "holdings may be read only after explicit user selection",
    )
    require(
        "derived_holdings_risk_analysis" in holdings_requested.forbidden_actions,
        "a consented holdings read must remain display-only",
    )

    holdings_unavailable = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        capability_state="checked",
        macro_state="delivered",
        holdings_review="requested",
        holdings_state="unavailable",
    )
    require(
        holdings_unavailable.required_actions == ("holdings_display_data_gap", "offer_next_research_action"),
        "a failed holdings read must disclose the gap and return control to the user",
    )

    named_instrument = resolve_daily_ops_route(
        intent="instrument_request",
        capability_state="pending",
        macro_state="pending",
        holdings_review="undecided",
        holdings_state="not_read",
    )
    require(
        named_instrument.required_actions == ("run_named_instrument_research_bundle",),
        "a named ticker must bypass optional Holdings Display",
    )

    macro_snapshot = json.loads(MACRO_FIXTURE.read_text(encoding="utf-8"))
    _refresh_content_hash(macro_snapshot)
    macro_delivery = build_delivery_packet(_macro_result(macro_snapshot))
    macro_html = macro_delivery.standalone_board.html if macro_delivery.standalone_board else b""
    for marker in (
        b'aria-label="\xe5\xae\x8f\xe8\xa7\x82\xe8\xa7\x86\xe5\x9b\xbe"',
        b'data-view="trend"',
        b'data-view="current"',
        b'data-view="events"',
        b'data-view="scenarios"',
    ):
        require(marker in macro_html, "the Macro delivery must retain the frozen canonical view controls")

    print("daily ops routing selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
