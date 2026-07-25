#!/usr/bin/env python3
"""Verify the minimal public stateless Skill package."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "mars-research-assistant"
REQUIRED = {
    Path("LICENSE"),
    Path("SKILL.md"),
    Path("agents/openai.yaml"),
    Path("references/macro-research.md"),
    Path("references/instrument-research.md"),
    Path("references/price-action.md"),
    Path("references/safety-and-sources.md"),
    Path("scripts/macro_board_visual.py"),
    Path("scripts/macro_delivery.py"),
    Path("scripts/macro_fixture.py"),
    Path("scripts/macro_fixture_board.py"),
    Path("scripts/stateless_research_run.py"),
    Path("scripts/verify_macro_research_run_selftest.py"),
    Path("scripts/verify_stateless_research_run_selftest.py"),
}
PRIVATE_PATH = re.compile(r"/Users/[^/]+/(?:Documents|Library)/")
RETIRED_PATH_PARTS = (
    "artifact_packet",
    "research_result",
    "runtime_health",
    "daily_ops",
    "holdings_display",
    "gateway",
    "ibkr",
)


def main() -> int:
    files = {
        path.relative_to(SKILL)
        for path in SKILL.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    missing = sorted(str(path) for path in REQUIRED - files)
    if missing:
        raise SystemExit("portable distribution contract failed: missing " + ", ".join(missing))
    for path in SKILL.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".py", ".json", ".yaml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        if PRIVATE_PATH.search(text):
            raise SystemExit(f"portable distribution contract failed: private path in {path}")
    retired = [
        str(path)
        for path in files
        if any(part in path.name.lower() for part in RETIRED_PATH_PARTS)
    ]
    if retired:
        raise SystemExit("portable distribution contract failed: retired file " + ", ".join(retired))
    print("portable distribution contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
