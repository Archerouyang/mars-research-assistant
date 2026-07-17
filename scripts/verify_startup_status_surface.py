#!/usr/bin/env python3
"""Probe one canonical startup-status documentation or fixture surface."""

from __future__ import annotations

import argparse
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"

SURFACES: dict[tuple[str, str], tuple[Path, tuple[str, ...]]] = {
    ("router", "uninitialized"): (
        SKILL / "SKILL.md",
        ("startup_status=uninitialized", "Exact Weekend First Start"),
    ),
    ("reference", "ready"): (
        SKILL / "references" / "daily-ops-orchestrator.md",
        ("ready / partial / uninitialized", "startup completeness axis"),
    ),
    ("reference", "partial"): (
        SKILL / "references" / "daily-ops-orchestrator.md",
        ("startup_status=partial", "formal runtime"),
    ),
    ("reference", "uninitialized"): (
        SKILL / "references" / "daily-ops-orchestrator.md",
        ("ready / partial / uninitialized", "`startup_status=partial` or `uninitialized`"),
    ),
    ("template", "partial"): (
        SKILL / "assets" / "templates" / "daily-ops-orchestrator.md",
        ("startup_status=partial / uninitialized", "可用研究摘要"),
    ),
    ("template", "uninitialized"): (
        SKILL / "assets" / "templates" / "daily-ops-orchestrator.md",
        ("startup_status=partial / uninitialized", "缺失确认"),
    ),
    ("fixture", "ready"): (
        SKILL / "assets" / "fixtures" / "expected" / "daily-ops-orchestrator-start-today.md",
        ("| startup_status | ready |", "runtime_origin | explicit_argument"),
    ),
    ("fixture", "partial"): (
        SKILL / "assets" / "fixtures" / "expected" / "daily-ops-weekend-first-start.md",
        ("| startup_status | partial |", "| formal runtime | available |"),
    ),
    ("fixture", "uninitialized"): (
        SKILL
        / "assets"
        / "fixtures"
        / "expected"
        / "daily-ops-weekend-empty-runtime-first-start.md",
        ("| startup_status | uninitialized |", "| formal runtime | missing |"),
    ),
    ("direct-activation", "uninitialized"): (
        SKILL / "references" / "workflow-weekly-trading-plan.md",
        ("startup_status=uninitialized", "Daily Ops Orchestrator"),
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", required=True)
    parser.add_argument("--status", required=True)
    args = parser.parse_args()
    key = (args.surface, args.status)
    if key not in SURFACES:
        raise SystemExit(f"unsupported startup surface/status pair: {key!r}")
    path, required_terms = SURFACES[key]
    text = path.read_text(encoding="utf-8")
    missing = [term for term in required_terms if term not in text]
    if missing:
        raise SystemExit(f"{args.surface}/{args.status} missing {missing!r} in {path}")
    if "formal runtime 为 partial / uninitialized" in text:
        raise SystemExit(f"{args.surface}/{args.status} mixes runtime and startup taxonomies")
    print(f"startup surface {args.surface}/{args.status} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
