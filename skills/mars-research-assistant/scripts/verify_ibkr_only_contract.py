#!/usr/bin/env python3
"""Fail when the active Mars product surface regains a second broker path."""

from __future__ import annotations

from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
FORBIDDEN = "longbridge"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def active_files() -> list[Path]:
    files = [
        SKILL / "SKILL.md",
        REPO / "README.md",
        REPO / "docs" / "MARS_RESEARCH_ASSISTANT_1_0_SPEC.md",
    ]
    files.extend((SKILL / "references").glob("*"))
    files.extend((SKILL / "assets" / "templates").glob("*"))
    files.extend((SKILL / "assets" / "fixtures").rglob("*"))
    files.extend(
        path
        for path in (SKILL / "scripts").glob("*")
        if not path.name.startswith("verify_")
    )
    return sorted(path for path in files if path.is_file())


def main() -> int:
    forbidden_paths = [
        path
        for path in SKILL.rglob("*")
        if path.is_file() and FORBIDDEN in path.name.casefold()
    ]
    require(
        not forbidden_paths,
        "active second-broker files remain: "
        + ", ".join(str(path.relative_to(REPO)) for path in forbidden_paths),
    )

    leaked = []
    for path in active_files():
        text = path.read_text(encoding="utf-8", errors="ignore").casefold()
        if FORBIDDEN in text:
            leaked.append(path.relative_to(REPO))
    require(
        not leaked,
        "active second-broker references remain: "
        + ", ".join(str(path) for path in leaked),
    )

    require(
        not (SKILL / "scripts" / "mars_runtime_config.py").exists(),
        "legacy broker-choice configuration must stay retired",
    )
    require(
        not (SKILL / "scripts" / "ibkr_connector_adapter.py").exists(),
        "legacy risk-bearing IBKR connector adapter must stay retired",
    )
    require(
        (SKILL / "scripts" / "ibkr_provider.py").is_file(),
        "the shared IBKR-only Provider boundary is missing",
    )
    require(
        (SKILL / "scripts" / "ibkr_holdings_adapter.py").is_file(),
        "the minimal IBKR holdings adapter is missing",
    )

    print("IBKR-only contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
