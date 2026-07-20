#!/usr/bin/env python3
"""Narrow compatibility smoke for retained canonical Board artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from artifact_packet import build_artifact_packet


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "assets" / "fixtures" / "input" / "macro-regime-complete.json"
    snapshot = json.loads(fixture.read_text(encoding="utf-8"))

    first = build_artifact_packet(snapshot)
    second = build_artifact_packet(snapshot)
    if first != second:
        raise SystemExit("artifact_packet_not_deterministic")

    manifest = json.loads(first.manifest)
    if manifest["html_sha256"] != hashlib.sha256(first.html).hexdigest():
        raise SystemExit("artifact_packet_html_hash_mismatch")
    if manifest["board"] != "macro_regime":
        raise SystemExit("artifact_packet_board_mismatch")

    html = first.html.decode("utf-8").lower()
    for forbidden in ("fetch(", "websocket", "broker write", "place order"):
        if forbidden in html:
            raise SystemExit(f"artifact_packet_forbidden_surface:{forbidden}")

    print("ArtifactPacket compatibility smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
