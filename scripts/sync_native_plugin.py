#!/usr/bin/env python3
"""Deterministically generate native plugin wrappers from the portable Skill."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


REPO = Path(__file__).resolve().parents[1]
SKILL_NAME = "trading-research-system"
SOURCE = REPO / "skills" / SKILL_NAME
PLUGIN = REPO / "plugins" / SKILL_NAME
WRAPPER_SKILL = PLUGIN / "skills" / SKILL_NAME


def copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def sync() -> None:
    if not (SOURCE / "SKILL.md").is_file():
        raise SystemExit(f"portable Skill missing: {SOURCE}")
    shutil.copy2(REPO / "LICENSE", SOURCE / "LICENSE")

    skills_root = PLUGIN / "skills"
    if skills_root.exists():
        shutil.rmtree(skills_root)
    skills_root.mkdir(parents=True)
    copy_tree(SOURCE, WRAPPER_SKILL)

    copy_tree(SOURCE / "assets", PLUGIN / "assets")
    scripts_root = PLUGIN / "scripts"
    scripts_root.mkdir(parents=True, exist_ok=True)
    generated_names = {source.name for source in (SOURCE / "scripts").glob("*.py")}
    development_harness = {"contract_suite.py", "contract_verifier.py"}
    for target in scripts_root.glob("*.py"):
        if (
            target.name not in generated_names
            and target.name not in development_harness
            and not target.name.startswith("verify_")
        ):
            target.unlink()
    for source in sorted((SOURCE / "scripts").glob("*.py")):
        shutil.copy2(source, PLUGIN / "scripts" / source.name)
    shutil.copy2(SOURCE / "LICENSE", PLUGIN / "LICENSE")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    sync()
    print(f"native wrappers synced from {SOURCE}")


if __name__ == "__main__":
    main()
