#!/usr/bin/env python3
"""Self-test position daily report rendering against the fixture package."""

from __future__ import annotations

import subprocess
import sys
import csv
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "position_daily_report.py"
DAILY_DIR = ROOT / "assets" / "fixtures" / "runtime" / "active-market-plan-2026-06-24" / "daily" / "2026-06-24"
EXPECTED = DAILY_DIR / "position-daily-report.md"


def main() -> int:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(DAILY_DIR / "portfolio_snapshot.csv"),
            "--date",
            "2026-06-24",
            "--source",
            "broker-live fixture",
            "--data-status",
            "fixture",
            "--snapshot-saved",
            "fixture",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)

    expected = EXPECTED.read_text(encoding="utf-8").strip()
    actual = result.stdout.strip()
    if actual != expected:
        raise AssertionError(f"position daily report mismatch\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}")

    unavailable_multi_broker = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(DAILY_DIR / "portfolio_snapshot.csv"),
            "--portfolio-reconciliation",
            "unavailable",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if unavailable_multi_broker.returncode == 0:
        raise AssertionError("unavailable reconciliation must not aggregate a multi-broker snapshot")
    if "unavailable reconciliation cannot aggregate multiple broker sources" not in unavailable_multi_broker.stderr:
        raise AssertionError(unavailable_multi_broker.stderr or unavailable_multi_broker.stdout)
    if "总资产" in unavailable_multi_broker.stdout or "$85,060" in unavailable_multi_broker.stdout:
        raise AssertionError("unavailable multi-broker reconciliation must fail before rendering aggregate assets")

    missing_exclusion = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(DAILY_DIR / "portfolio_snapshot.csv"),
            "--portfolio-reconciliation",
            "not_confirmed",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if missing_exclusion.returncode == 0:
        raise AssertionError("not_confirmed report must require excluded-source metadata")
    if "not_confirmed requires at least one --excluded-source" not in missing_exclusion.stderr:
        raise AssertionError(missing_exclusion.stderr or missing_exclusion.stdout)

    bogus_exclusion = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(DAILY_DIR / "portfolio_snapshot.csv"),
            "--portfolio-reconciliation",
            "not_confirmed",
            "--excluded-source",
            "FakeBroker:partial_data",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if bogus_exclusion.returncode == 0:
        raise AssertionError("not_confirmed report must reject unrelated exclusion metadata")
    if "excluded-source must name IBKR or Longbridge" not in bogus_exclusion.stderr:
        raise AssertionError(bogus_exclusion.stderr or bogus_exclusion.stdout)

    invalid_metadata_cases = {
        "IBKR": "excluded-source must use exact SOURCE:STATUS metadata",
        " IBKR:partial_data": "excluded-source must use exact SOURCE:STATUS metadata",
        "IBKR:partial_data ": "excluded-source must use exact SOURCE:STATUS metadata",
        "Longbridge:partial_data(   )": "excluded-source must use exact SOURCE:STATUS metadata",
        ":partial_data": "excluded-source must use exact SOURCE:STATUS metadata",
        "IBKR:partial_data(NAV-only": "excluded-source must use exact SOURCE:STATUS metadata",
        "IBKR:partial_dataNAV-only)": "excluded-source must use exact SOURCE:STATUS metadata",
        "IBKR:bogus": "excluded-source must include a non-confirmed source status",
        "IBKR:available": "excluded-source status cannot be available, confirmed, or missing",
        "IBKR:confirmed": "excluded-source status cannot be available, confirmed, or missing",
        "IBKR:missing": "excluded-source status cannot be available, confirmed, or missing",
    }
    for metadata, expected_error in invalid_metadata_cases.items():
        invalid_metadata = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(DAILY_DIR / "portfolio_snapshot.csv"),
                "--portfolio-reconciliation",
                "not_confirmed",
                "--excluded-source",
                metadata,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if invalid_metadata.returncode == 0:
            raise AssertionError(f"not_confirmed report must reject malformed metadata {metadata!r}")
        if expected_error not in invalid_metadata.stderr:
            raise AssertionError(invalid_metadata.stderr or invalid_metadata.stdout)

    cross_mode_invalid_cases = (
        (
            ["--portfolio-reconciliation", "confirmed", "--excluded-source", "IBKR:partial_data(NAV-only"],
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            ["--excluded-source", "FakeBroker:bogus"],
            "excluded-source must name IBKR or Longbridge",
        ),
        (
            ["--portfolio-reconciliation", "confirmed", "--excluded-source", ""],
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            ["--excluded-source", "   "],
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            ["--portfolio-reconciliation", "unavailable", "--excluded-source", " IBKR:partial_data"],
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            ["--portfolio-reconciliation", "unavailable", "--excluded-source", "IBKR:partial_data "],
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
        (
            ["--portfolio-reconciliation", "unavailable", "--excluded-source", "Longbridge:partial_data(   )"],
            "excluded-source must use exact SOURCE:STATUS metadata",
        ),
    )
    for extra_args, expected_error in cross_mode_invalid_cases:
        cross_mode_invalid = subprocess.run(
            [sys.executable, str(SCRIPT), str(DAILY_DIR / "portfolio_snapshot.csv"), *extra_args],
            text=True,
            capture_output=True,
            check=False,
        )
        if cross_mode_invalid.returncode == 0:
            raise AssertionError(f"excluded-source metadata must be validated in every mode: {extra_args!r}")
        if expected_error not in cross_mode_invalid.stderr:
            raise AssertionError(cross_mode_invalid.stderr or cross_mode_invalid.stdout)

    valid_cross_mode_cases = (
        (["--portfolio-reconciliation", "confirmed"], "IBKR:partial_data"),
        (["--portfolio-reconciliation", "unavailable"], "Longbridge:needs_review"),
        (["--portfolio-reconciliation", "unavailable"], "Longbridge:needs_review(retry pending)"),
        ([], "IBKR:upstream_error"),
    )
    for reconciliation_args, metadata in valid_cross_mode_cases:
        misplaced_valid_exclusion = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(DAILY_DIR / "portfolio_snapshot.csv"),
                *reconciliation_args,
                "--excluded-source",
                metadata,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if misplaced_valid_exclusion.returncode == 0:
            raise AssertionError("excluded-source metadata must only accompany not_confirmed reconciliation")
        if "--excluded-source requires --portfolio-reconciliation not_confirmed" not in misplaced_valid_exclusion.stderr:
            raise AssertionError(misplaced_valid_exclusion.stderr or misplaced_valid_exclusion.stdout)

    rejected_merge = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(DAILY_DIR / "portfolio_snapshot.csv"),
            "--portfolio-reconciliation",
            "not_confirmed",
            "--excluded-source",
            "IBKR:partial_data",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if rejected_merge.returncode == 0:
        raise AssertionError("not_confirmed report must reject rows from an excluded broker source")
    if "excluded broker source present in snapshot: IBKR" not in rejected_merge.stderr:
        raise AssertionError(rejected_merge.stderr or rejected_merge.stdout)

    with tempfile.TemporaryDirectory() as raw_tmp:
        mixed_manual = Path(raw_tmp) / "ibkr-manual.csv"
        with (DAILY_DIR / "portfolio_snapshot.csv").open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames is None:
                raise AssertionError("fixture snapshot missing header")
            mixed_rows = []
            for row in reader:
                copied = dict(row)
                if copied.get("broker") == "Longbridge":
                    copied["broker"] = "ManualBroker"
                mixed_rows.append(copied)
            with mixed_manual.open("w", newline="", encoding="utf-8") as target:
                writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(mixed_rows)
        unavailable_ibkr_manual = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(mixed_manual),
                "--portfolio-reconciliation",
                "unavailable",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if unavailable_ibkr_manual.returncode == 0:
            raise AssertionError("unavailable reconciliation must fail closed for IBKR plus ManualBroker")
        if "unavailable reconciliation cannot aggregate multiple broker sources" not in unavailable_ibkr_manual.stderr:
            raise AssertionError(unavailable_ibkr_manual.stderr or unavailable_ibkr_manual.stdout)
        if "总资产" in unavailable_ibkr_manual.stdout:
            raise AssertionError("IBKR plus ManualBroker must fail before rendering aggregate assets")

        filtered = Path(raw_tmp) / "longbridge-only.csv"
        with (DAILY_DIR / "portfolio_snapshot.csv").open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            rows = [row for row in reader if row.get("broker") == "Longbridge"]
            if reader.fieldnames is None:
                raise AssertionError("fixture snapshot missing header")
            with filtered.open("w", newline="", encoding="utf-8") as target:
                writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        unavailable_single_source = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(filtered),
                "--portfolio-reconciliation",
                "unavailable",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if unavailable_single_source.returncode != 0:
            raise AssertionError(unavailable_single_source.stderr or unavailable_single_source.stdout)
        if "Portfolio reconciliation: unavailable" not in unavailable_single_source.stdout:
            raise AssertionError("single-source unavailable report must remain renderable")

        manual_only = Path(raw_tmp) / "manual-only.csv"
        with filtered.open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames is None:
                raise AssertionError("filtered fixture missing header")
            manual_rows = []
            for row in reader:
                copied = dict(row)
                copied["broker"] = "ManualBroker"
                manual_rows.append(copied)
            with manual_only.open("w", newline="", encoding="utf-8") as target:
                writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(manual_rows)
        unavailable_manual_only = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(manual_only),
                "--portfolio-reconciliation",
                "unavailable",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if unavailable_manual_only.returncode != 0:
            raise AssertionError(unavailable_manual_only.stderr or unavailable_manual_only.stdout)
        if "Portfolio reconciliation: unavailable" not in unavailable_manual_only.stdout:
            raise AssertionError("single arbitrary broker unavailable report must remain renderable")
        for metadata in ("IBKR:partial_data", "IBKR:partial_data(NAV-only)"):
            partial_report = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(filtered),
                    "--portfolio-reconciliation",
                    "not_confirmed",
                    "--excluded-source",
                    metadata,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if partial_report.returncode != 0:
                raise AssertionError(partial_report.stderr or partial_report.stdout)
            for term in (
                "Portfolio reconciliation: not_confirmed",
                f"Excluded broker sources: {metadata}",
                "已确认来源资产",
            ):
                if term not in partial_report.stdout:
                    raise AssertionError(f"partial report missing {term!r}")
            if "- 总资产" in partial_report.stdout:
                raise AssertionError("not_confirmed report must not label source-only assets as total portfolio assets")

    print("position daily report selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
