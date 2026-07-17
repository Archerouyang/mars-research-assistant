#!/usr/bin/env python3
"""Verify the repo-level Behavior Contract Matrix integration surface."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
MATRICES = REPO / "scripts" / "verify_behavior_contract_matrices.py"
POSITION_SELFTEST = (
    REPO
    / "plugins"
    / "trading-research-system"
    / "scripts"
    / "verify_position_daily_report_selftest.py"
)
PRICE_ACTION_SELFTEST = (
    REPO
    / "plugins"
    / "trading-research-system"
    / "scripts"
    / "verify_price_action_rollforward_selftest.py"
)
PLUGIN_GATE = REPO / "scripts" / "verify-plugin.sh"


def main() -> int:
    if not MATRICES.is_file():
        raise AssertionError(f"behavior matrix runner missing: {MATRICES}")

    for family in ("reconciliation", "startup", "setup-key"):
        result = subprocess.run(
            [sys.executable, str(MATRICES), "--family", family],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        expected = f"behavior contract matrix {family} ok"
        if result.stdout.strip() != expected:
            raise AssertionError(
                f"unexpected {family} matrix output: {result.stdout!r}"
            )

    old_selftest = POSITION_SELFTEST.read_text(encoding="utf-8")
    for migrated_term in (
        "invalid_metadata_cases",
        "cross_mode_invalid_cases",
        "unavailable_multi_broker",
        "rejected_merge",
    ):
        if migrated_term in old_selftest:
            raise AssertionError(
                f"migrated reconciliation scenario remains in old selftest: {migrated_term}"
            )

    price_action_selftest = PRICE_ACTION_SELFTEST.read_text(encoding="utf-8")
    for migrated_term in (
        "missing_cases",
        "omitted_ohlcv_result",
        "complete_key_without_ohlcv",
        "invalid_result",
    ):
        if migrated_term in price_action_selftest:
            raise AssertionError(
                f"migrated setup-key scenario remains in old selftest: {migrated_term}"
            )

    daily_ops_contract = (
        REPO
        / "plugins"
        / "trading-research-system"
        / "scripts"
        / "verify_daily_ops_orchestrator_contract.py"
    ).read_text(encoding="utf-8")
    if "def verify_startup_status_taxonomy" in daily_ops_contract:
        raise AssertionError("migrated startup-status taxonomy remains in Daily Ops contract")

    gate = PLUGIN_GATE.read_text(encoding="utf-8")
    for command in (
        "python scripts/verify_behavior_contract_matrix_selftest.py",
        "python scripts/verify_behavior_contract_matrices_contract.py",
    ):
        if command not in gate:
            raise AssertionError(f"plugin verification gate missing: {command}")

    print("behavior contract matrices contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
