#!/usr/bin/env python3
"""Focused regression checks for standalone-only visual delivery."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from research_result import build_delivery_packet, write_delivery_packet


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "assets" / "fixtures" / "input"
AS_OF = "2026-07-17T10:00:00Z"


def _result() -> dict[str, object]:
    snapshot = json.loads(
        (INPUT / "macro-regime-complete.json").read_text(encoding="utf-8")
    )
    return {
        "schema_version": "1.0",
        "result_kind": "macro",
        "as_of": AS_OF,
        "decision": "Maintain the current evidence gate.",
        "key_evidence": [
            {
                "label": "Current read",
                "value": "Decision-useful",
                "evidence_type": "fact",
                "status": "complete",
                "as_of": AS_OF,
                "source_refs": ["fixture"],
            }
        ],
        "risks": [],
        "scenarios": [],
        "next_checks": [],
        "data_gaps": [],
        "sources": [
            {
                "id": "fixture",
                "label": "Synthetic fixture",
                "priority": "S1",
                "as_of": AS_OF,
            }
        ],
        "privacy": "public_fixture",
        "locale": "zh-CN",
        "visual": {
            "adapter": "macro",
            "snapshot": snapshot,
            "default_view": "Overview",
        },
    }


def main() -> int:
    packet = build_delivery_packet(_result())
    assert not hasattr(packet, "inline_html"), "deprecated Board surface remains public"
    assert packet.standalone_board is not None, "standalone board was not built"
    html = packet.standalone_board.html
    assert html.lstrip().lower().startswith(b"<!doctype html>"), "board is not a document"
    assert b"<html" in html.lower() and b"</html>" in html.lower(), "document shell missing"
    assert b"--foreground:" in html, "host-independent design tokens missing"
    assert b".btn{" in html and b".card{" in html, "host component styles missing"
    assert b"connect-src 'none'" in html, "offline network boundary missing"
    assert b'data-view="trend"' in html, "accepted visual views changed"
    assert b"<iframe" not in html.lower(), "standalone board must not wrap another page"
    manifest = json.loads(packet.standalone_board.manifest)
    assert manifest["views"] == ["trend", "current", "events", "scenarios"]
    assert manifest["default_view"] == "trend"
    assert manifest["decision_cutoff"] == AS_OF

    private_result = _result()
    private_result.pop("privacy")
    private_packet = build_delivery_packet(private_result)
    assert private_packet.standalone_board is not None
    private_manifest = json.loads(private_packet.standalone_board.manifest)
    assert private_manifest["privacy"] == "private"

    with tempfile.TemporaryDirectory(prefix="standalone-board-selftest-") as temporary:
        output = Path(temporary) / "delivery"
        paths = write_delivery_packet(packet, output)
        assert paths["board_html"].name == "research-brief.html"
        assert paths["board_snapshot"].name == "snapshot.canonical.json"
        assert paths["board_manifest"].name == "artifact.manifest.json"
        assert not (output / "inline.html").exists(), "deprecated inline artifact was written"

    print("Standalone Board selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
