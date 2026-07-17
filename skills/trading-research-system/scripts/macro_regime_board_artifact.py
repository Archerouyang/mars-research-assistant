#!/usr/bin/env python3
"""Generate one immutable canonical Macro Regime Board packet from a snapshot.

This is intentionally distinct from ``macro_regime_artifact.py``, the legacy
static SVG generator. The two paths coexist; this entrypoint never substitutes
or falls back to the SVG artifact.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from artifact_packet import ArtifactPacketError, build_artifact_packet, write_artifact_packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Validated Macro snapshot JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="Empty or byte-identical packet directory")
    args = parser.parse_args()
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        if not isinstance(snapshot, dict) or snapshot.get("board") != "macro_regime":
            raise ArtifactPacketError("board_invalid")
        packet = build_artifact_packet(snapshot)
        paths = write_artifact_packet(packet, args.output_dir)
    except (OSError, json.JSONDecodeError, ArtifactPacketError) as exc:
        code = str(exc) if isinstance(exc, ArtifactPacketError) else "input_unreadable"
        print(f"artifact packet failed: {code}", file=sys.stderr)
        return 1
    print(f"artifact packet written: {paths['json']} {paths['html']} {paths['manifest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
