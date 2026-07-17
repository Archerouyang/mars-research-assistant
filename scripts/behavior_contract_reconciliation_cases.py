#!/usr/bin/env python3
"""Reconciliation-mode and broker-composition behavior cases."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

from behavior_contract_matrix import CommandCase


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"
POSITION_REPORT = SKILL / "scripts" / "position_daily_report.py"
DAILY_DIR = (
    SKILL
    / "assets"
    / "fixtures"
    / "runtime"
    / "active-market-plan-2026-06-24"
    / "daily"
    / "2026-06-24"
)
PORTFOLIO_SNAPSHOT = DAILY_DIR / "portfolio_snapshot.csv"


def _position_command(snapshot: Path, *args: str) -> tuple[str, ...]:
    return (
        sys.executable,
        str(POSITION_REPORT),
        str(snapshot),
        *args,
    )


def _write_snapshot_variant(
    target: Path,
    *,
    keep_brokers: set[str] | None = None,
    rename_brokers: dict[str, str] | None = None,
) -> Path:
    with PORTFOLIO_SNAPSHOT.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise AssertionError("fixture snapshot missing header")
        rows: list[dict[str, str]] = []
        for row in reader:
            broker = row.get("broker", "")
            if keep_brokers is not None and broker not in keep_brokers:
                continue
            copied = dict(row)
            if rename_brokers and broker in rename_brokers:
                copied["broker"] = rename_brokers[broker]
            rows.append(copied)

    if not rows:
        raise AssertionError(f"snapshot variant has no rows: {target}")
    with target.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target


def build_reconciliation_cases(tmp: Path) -> tuple[CommandCase, ...]:
    longbridge_only = _write_snapshot_variant(
        tmp / "longbridge-only.csv",
        keep_brokers={"Longbridge"},
    )
    ibkr_only = _write_snapshot_variant(
        tmp / "ibkr-only.csv",
        keep_brokers={"IBKR"},
    )
    manual_only = _write_snapshot_variant(
        tmp / "manual-only.csv",
        keep_brokers={"Longbridge"},
        rename_brokers={"Longbridge": "ManualBroker"},
    )
    ibkr_manual = _write_snapshot_variant(
        tmp / "ibkr-manual.csv",
        rename_brokers={"Longbridge": "ManualBroker"},
    )

    cases: list[CommandCase] = [
        CommandCase(
            case_id="mode/confirmed/two-brokers",
            command=_position_command(
                PORTFOLIO_SNAPSHOT,
                "--portfolio-reconciliation",
                "confirmed",
            ),
            required_stdout=("Portfolio reconciliation: confirmed", "- 总资产"),
        ),
        CommandCase(
            case_id="composition/confirmed/ibkr-only",
            command=_position_command(
                ibkr_only,
                "--portfolio-reconciliation",
                "confirmed",
            ),
            required_stdout=("Portfolio reconciliation: confirmed", "- 总资产"),
        ),
        CommandCase(
            case_id="composition/confirmed/longbridge-only",
            command=_position_command(
                longbridge_only,
                "--portfolio-reconciliation",
                "confirmed",
            ),
            required_stdout=("Portfolio reconciliation: confirmed", "- 总资产"),
        ),
        CommandCase(
            case_id="composition/confirmed/manual-only",
            command=_position_command(
                manual_only,
                "--portfolio-reconciliation",
                "confirmed",
            ),
            required_stdout=("Portfolio reconciliation: confirmed", "- 总资产"),
        ),
        CommandCase(
            case_id="mode/unavailable/two-brokers",
            command=_position_command(
                PORTFOLIO_SNAPSHOT,
                "--portfolio-reconciliation",
                "unavailable",
            ),
            expected_returncode=1,
            required_stderr=(
                "unavailable reconciliation cannot aggregate multiple broker sources",
            ),
            forbidden_stdout=("总资产", "$85,060"),
        ),
        CommandCase(
            case_id="mode/not-confirmed/missing-exclusion",
            command=_position_command(
                PORTFOLIO_SNAPSHOT,
                "--portfolio-reconciliation",
                "not_confirmed",
            ),
            expected_returncode=1,
            required_stderr=(
                "not_confirmed requires at least one --excluded-source",
            ),
        ),
        CommandCase(
            case_id="mode/not-confirmed/unrelated-exclusion",
            command=_position_command(
                PORTFOLIO_SNAPSHOT,
                "--portfolio-reconciliation",
                "not_confirmed",
                "--excluded-source",
                "FakeBroker:partial_data",
            ),
            expected_returncode=1,
            required_stderr=("excluded-source must name IBKR or Longbridge",),
        ),
        CommandCase(
            case_id="mode/not-confirmed/excluded-source-present",
            command=_position_command(
                PORTFOLIO_SNAPSHOT,
                "--portfolio-reconciliation",
                "not_confirmed",
                "--excluded-source",
                "IBKR:partial_data",
            ),
            expected_returncode=1,
            required_stderr=("excluded broker source present in snapshot: IBKR",),
        ),
        CommandCase(
            case_id="composition/unavailable/ibkr-manual",
            command=_position_command(
                ibkr_manual,
                "--portfolio-reconciliation",
                "unavailable",
            ),
            expected_returncode=1,
            required_stderr=(
                "unavailable reconciliation cannot aggregate multiple broker sources",
            ),
            forbidden_stdout=("总资产",),
        ),
        CommandCase(
            case_id="composition/unavailable/longbridge-only",
            command=_position_command(
                longbridge_only,
                "--portfolio-reconciliation",
                "unavailable",
            ),
            required_stdout=("Portfolio reconciliation: unavailable",),
        ),
        CommandCase(
            case_id="composition/unavailable/ibkr-only",
            command=_position_command(
                ibkr_only,
                "--portfolio-reconciliation",
                "unavailable",
            ),
            required_stdout=("Portfolio reconciliation: unavailable",),
        ),
        CommandCase(
            case_id="composition/unavailable/manual-only",
            command=_position_command(
                manual_only,
                "--portfolio-reconciliation",
                "unavailable",
            ),
            required_stdout=("Portfolio reconciliation: unavailable",),
        ),
    ]

    invalid_metadata_cases = (
        ("bare-source", "IBKR", "excluded-source must use exact SOURCE:STATUS metadata"),
        ("leading-space", " IBKR:partial_data", "excluded-source must use exact SOURCE:STATUS metadata"),
        ("trailing-space", "IBKR:partial_data ", "excluded-source must use exact SOURCE:STATUS metadata"),
        ("blank-note", "Longbridge:partial_data(   )", "excluded-source must use exact SOURCE:STATUS metadata"),
        ("missing-source", ":partial_data", "excluded-source must use exact SOURCE:STATUS metadata"),
        ("unclosed-note", "IBKR:partial_data(NAV-only", "excluded-source must use exact SOURCE:STATUS metadata"),
        ("orphan-close", "IBKR:partial_dataNAV-only)", "excluded-source must use exact SOURCE:STATUS metadata"),
        ("unknown-status", "IBKR:bogus", "excluded-source must include a non-confirmed source status"),
        ("available", "IBKR:available", "excluded-source status cannot be available, confirmed, or missing"),
        ("confirmed", "IBKR:confirmed", "excluded-source status cannot be available, confirmed, or missing"),
        ("missing", "IBKR:missing", "excluded-source status cannot be available, confirmed, or missing"),
    )
    for case_name, metadata, expected_error in invalid_metadata_cases:
        cases.append(
            CommandCase(
                case_id=f"metadata/not-confirmed/{case_name}",
                command=_position_command(
                    PORTFOLIO_SNAPSHOT,
                    "--portfolio-reconciliation",
                    "not_confirmed",
                    "--excluded-source",
                    metadata,
                ),
                expected_returncode=1,
                required_stderr=(expected_error,),
            )
        )

    cross_mode_invalid_cases = (
        (
            "confirmed-unclosed-note",
            ("--portfolio-reconciliation", "confirmed"),
            "IBKR:partial_data(NAV-only",
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            "default-unrelated-source",
            (),
            "FakeBroker:bogus",
            "excluded-source must name IBKR or Longbridge",
        ),
        (
            "confirmed-empty",
            ("--portfolio-reconciliation", "confirmed"),
            "",
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            "default-whitespace",
            (),
            "   ",
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            "unavailable-leading-space",
            ("--portfolio-reconciliation", "unavailable"),
            " IBKR:partial_data",
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            "unavailable-trailing-space",
            ("--portfolio-reconciliation", "unavailable"),
            "IBKR:partial_data ",
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            "unavailable-blank-note",
            ("--portfolio-reconciliation", "unavailable"),
            "Longbridge:partial_data(   )",
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
    )
    for case_name, mode_args, metadata, expected_error in cross_mode_invalid_cases:
        cases.append(
            CommandCase(
                case_id=f"metadata/cross-mode/{case_name}",
                command=_position_command(
                    PORTFOLIO_SNAPSHOT,
                    *mode_args,
                    "--excluded-source",
                    metadata,
                ),
                expected_returncode=1,
                required_stderr=(expected_error,),
                forbidden_stderr=(
                    "--excluded-source requires --portfolio-reconciliation not_confirmed",
                ),
            )
        )

    misplaced_valid_cases = (
        (
            "confirmed-partial",
            ("--portfolio-reconciliation", "confirmed"),
            "IBKR:partial_data",
        ),
        (
            "unavailable-needs-review",
            ("--portfolio-reconciliation", "unavailable"),
            "Longbridge:needs_review",
        ),
        (
            "unavailable-needs-review-note",
            ("--portfolio-reconciliation", "unavailable"),
            "Longbridge:needs_review(retry pending)",
        ),
        ("default-upstream-error", (), "IBKR:upstream_error"),
    )
    for case_name, mode_args, metadata in misplaced_valid_cases:
        cases.append(
            CommandCase(
                case_id=f"metadata/misplaced/{case_name}",
                command=_position_command(
                    PORTFOLIO_SNAPSHOT,
                    *mode_args,
                    "--excluded-source",
                    metadata,
                ),
                expected_returncode=1,
                required_stderr=(
                    "--excluded-source requires --portfolio-reconciliation not_confirmed",
                ),
            )
        )

    for suffix, metadata in (
        ("plain", "IBKR:partial_data"),
        ("noted", "IBKR:partial_data(NAV-only)"),
    ):
        cases.append(
            CommandCase(
                case_id=f"composition/not-confirmed/longbridge-only-{suffix}",
                command=_position_command(
                    longbridge_only,
                    "--portfolio-reconciliation",
                    "not_confirmed",
                    "--excluded-source",
                    metadata,
                ),
                required_stdout=(
                    "Portfolio reconciliation: not_confirmed",
                    f"Excluded broker sources: {metadata}",
                    "已确认来源资产",
                ),
                forbidden_stdout=("- 总资产",),
            )
        )

    for suffix, metadata in (
        ("plain", "Longbridge:partial_data"),
        ("noted", "Longbridge:partial_data(feed delayed)"),
    ):
        cases.append(
            CommandCase(
                case_id=f"composition/not-confirmed/ibkr-only-{suffix}",
                command=_position_command(
                    ibkr_only,
                    "--portfolio-reconciliation",
                    "not_confirmed",
                    "--excluded-source",
                    metadata,
                ),
                required_stdout=(
                    "Portfolio reconciliation: not_confirmed",
                    f"Excluded broker sources: {metadata}",
                    "已确认来源资产",
                ),
                forbidden_stdout=("- 总资产",),
            )
        )

    return tuple(cases)


