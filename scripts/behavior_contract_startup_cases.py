#!/usr/bin/env python3
"""Startup-status runtime and documentation-surface behavior cases."""

from __future__ import annotations

from pathlib import Path
import sys

from behavior_contract_matrix import CommandCase, FileExpectation
from verify_startup_status_surface import SURFACES


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"
RUNTIME_HEALTH = SKILL / "scripts" / "runtime_health.py"
STARTUP_SURFACE = REPO / "scripts" / "verify_startup_status_surface.py"


def build_startup_cases(tmp: Path) -> tuple[CommandCase, ...]:
    uninitialized_runtime = tmp / "uninitialized-runtime"
    partial_runtime = tmp / "partial-runtime"
    partial_runtime.mkdir()
    partial_marker = partial_runtime / "market-plan.md"
    partial_marker.write_text("fixture plan\n", encoding="utf-8")

    ready_runtime = tmp / "ready-runtime"
    ready_runtime.mkdir()
    ready_marker = ready_runtime / "market-plan.md"
    ready_marker.write_text("fixture plan\n", encoding="utf-8")
    (ready_runtime / "trading-profile.md").write_text("fixture profile\n", encoding="utf-8")
    (ready_runtime / "updates").mkdir()
    (ready_runtime / "daily" / "2026-07-04").mkdir(parents=True)

    cases: list[CommandCase] = [
        CommandCase(
            case_id="status/uninitialized/missing-runtime",
            command=(
                sys.executable,
                str(RUNTIME_HEALTH),
                "--runtime-dir",
                str(uninitialized_runtime),
                "--date",
                "2026-07-04",
                "--format",
                "json",
            ),
            required_stdout=(
                '"runtime_origin": "explicit_argument"',
                '"startup_status": "uninitialized"',
                '"status": "missing"',
            ),
            forbidden_stdout=("PRIVATE",),
            files=(FileExpectation(uninitialized_runtime, "absent"),),
        ),
        CommandCase(
            case_id="status/partial/incomplete-runtime",
            command=(
                sys.executable,
                str(RUNTIME_HEALTH),
                "--runtime-dir",
                str(partial_runtime),
                "--date",
                "2026-07-04",
                "--format",
                "json",
            ),
            required_stdout=('"startup_status": "partial"',),
            files=(FileExpectation(partial_marker, "unchanged"),),
        ),
        CommandCase(
            case_id="status/ready/complete-runtime",
            command=(
                sys.executable,
                str(RUNTIME_HEALTH),
                "--runtime-dir",
                str(ready_runtime),
                "--date",
                "2026-07-04",
                "--format",
                "json",
            ),
            required_stdout=('"startup_status": "ready"',),
            files=(FileExpectation(ready_marker, "unchanged"),),
        ),
    ]
    for surface, status in SURFACES:
        cases.append(
            CommandCase(
                case_id=f"surface/{surface}/{status}",
                command=(
                    sys.executable,
                    str(STARTUP_SURFACE),
                    "--surface",
                    surface,
                    "--status",
                    status,
                ),
                required_stdout=(f"startup surface {surface}/{status} ok",),
            )
        )
    return tuple(cases)

