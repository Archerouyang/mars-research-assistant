#!/usr/bin/env python3
"""Offline structural self-check for a staged or installed Mars package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SKILLS = {
    "ask-mars",
    "market-catalysts-brief",
    "market-snapshot",
    "instrument-research",
    "technical-analysis",
    "drive-writeback",
}


def verify(root: Path) -> None:
    required = (
        "SKILL.md",
        "README.md",
        "LICENSE",
        "pyproject.toml",
        "uv.lock",
        "mars-skills.json",
        "package-files.txt",
    )
    for relative in required:
        if not (root / relative).is_file():
            raise ValueError(f"installed package is missing {relative}")
    root_skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if "name: mars-research-assistant" not in root_skill:
        raise ValueError("root Skill identity is invalid")
    manifest = json.loads((root / "mars-skills.json").read_text(encoding="utf-8"))
    identifiers = {
        row["id"] for row in manifest.get("skills", []) if isinstance(row, dict)
    }
    if identifiers != SKILLS:
        raise ValueError("installed package must contain exactly six child Skills")
    listed_files = {
        line.strip()
        for line in (root / "package-files.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and ".venv" not in path.relative_to(root).parts
        and path.name != ".mars-managed.json"
    }
    if actual_files != listed_files:
        raise ValueError("installed package differs from its strict file allowlist")
    for identifier in sorted(SKILLS):
        child = root / "skills" / identifier
        if not (child / "SKILL.md").is_file() or not (child / "capability.json").is_file():
            raise ValueError(f"installed child Skill is incomplete: {identifier}")
    vendor = (
        root
        / "skills"
        / "technical-analysis"
        / "vendor"
        / "lightweight-charts"
        / "5.2.0"
    )
    if not (vendor / "LICENSE").is_file() or not (
        vendor / "lightweight-charts.standalone.production.js"
    ).is_file():
        raise ValueError("Lightweight Charts vendor or license is missing")
    for prohibited in (".git", "tests", "AGENTS.md", "credentials.json", ".env"):
        if (root / prohibited).exists():
            raise ValueError(f"development or private item leaked into package: {prohibited}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        verify(arguments.root.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Mars package self-check failed: {error}", file=sys.stderr)
        return 65
    print("Mars managed package self-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
