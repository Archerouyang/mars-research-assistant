#!/usr/bin/env python3
"""Focused self-test for the supported ResearchResult delivery seam."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from research_result import ResearchResultError, build_delivery_packet


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "assets" / "fixtures" / "input"
AS_OF = "2026-07-17T10:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(name: str) -> dict[str, object]:
    return json.loads((INPUT / name).read_text(encoding="utf-8"))


def result(kind: str, visual: dict[str, object] | None) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "result_kind": kind,
        "as_of": AS_OF,
        "decision": "Maintain the current evidence gate until the next confirmation.",
        "key_evidence": [{"label": "Current read", "value": "Decision-useful", "evidence_type": "fact", "status": "complete", "as_of": AS_OF, "source_refs": ["fixture"]}],
        "risks": [],
        "scenarios": [],
        "next_checks": ["Refresh the decision-sensitive source."],
        "data_gaps": [],
        "sources": [{"id": "fixture", "label": "Synthetic fixture", "priority": "S1", "as_of": AS_OF}],
        "privacy": "public_fixture",
        "locale": "zh-CN",
        "visual": visual,
    }


def main() -> int:
    macro = result("macro", {"adapter": "macro", "snapshot": load("macro-regime-complete.json"), "default_view": "Overview"})
    first = build_delivery_packet(macro)
    require(first == build_delivery_packet(copy.deepcopy(macro)), "Macro delivery must be deterministic")
    html = first.standalone_board.html if first.standalone_board else b""
    for marker in (b'data-view="trend"', b'data-view="current"', b'data-view="events"', b'data-view="scenarios"'):
        require(marker in html, "Macro Board lost a frozen view")
    require(b"<iframe" not in html.lower(), "standalone Board must not wrap another page")

    instrument = result("instrument", {"adapter": "instrument", "snapshot": load("instrument-research-complete.json"), "default_view": "Overview"})
    instrument_packet = build_delivery_packet(instrument)
    require(instrument_packet.standalone_board is not None, "instrument Board missing")

    pa = result("price_action", {"adapter": "price_action", "payload": load("chart-ohlcv-qqq-sample.json"), "title": "QQQ PA Scenario Board"})
    pa_packet = build_delivery_packet(pa)
    require(pa_packet.standalone_board is not None and b"pa-chart" in pa_packet.standalone_board.html, "PA Board missing")

    try:
        build_delivery_packet(result("portfolio", None))
    except ResearchResultError as error:
        require(str(error) == "result_kind_invalid", "retired Portfolio result error changed")
    else:
        raise AssertionError("retired Portfolio result kind was accepted")

    print("research result selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
