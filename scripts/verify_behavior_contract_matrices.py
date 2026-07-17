#!/usr/bin/env python3
"""Run high-risk Trading Research System behavior matrices."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
import tempfile

from behavior_contract_matrix import CommandCase, FileExpectation, run_command_matrix


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"
POSITION_REPORT = SKILL / "scripts" / "position_daily_report.py"
PRICE_ACTION = SKILL / "scripts" / "price_action_rollforward.py"
RUNTIME_HEALTH = SKILL / "scripts" / "runtime_health.py"
STARTUP_SURFACE = REPO / "scripts" / "verify_startup_status_surface.py"
OHLCV_FIXTURE = SKILL / "assets" / "fixtures" / "input" / "chart-ohlcv-qqq-sample.json"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        choices=("reconciliation", "startup", "setup-key"),
        required=True,
    )
    return parser.parse_args()


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

    return tuple(cases)


def run_reconciliation_matrix() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        result = run_command_matrix(
            "reconciliation",
            build_reconciliation_cases(Path(raw_tmp)),
        )
    if not result.ok:
        print(result.render_failures(), file=sys.stderr)
        return 1
    print("behavior contract matrix reconciliation ok")
    return 0


def _price_action_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, str(PRICE_ACTION), *args)


def build_setup_key_cases(tmp: Path) -> tuple[CommandCase, ...]:
    common = (
        "--ohlcv-json",
        str(OHLCV_FIXTURE),
        "--main-timeframe",
        "1D",
        "--aux-timeframe",
        "1H",
        "--analysis-intent",
        "position_reassessment",
        "--ohlcv-status",
        "authorized",
    )
    supplied_by_missing = {
        "ticker": ("--trade-horizon", "medium-term swing", "--instrument", "equity"),
        "trade-horizon": ("--ticker", "QQQ", "--instrument", "equity"),
        "instrument": ("--ticker", "QQQ", "--trade-horizon", "medium-term swing"),
    }
    cases: list[CommandCase] = []
    for missing, supplied in supplied_by_missing.items():
        output = tmp / f"missing-{missing}.md"
        board = tmp / f"missing-{missing}.svg"
        cases.append(
            CommandCase(
                case_id=f"completeness/missing-{missing}",
                command=_price_action_command(
                    *common,
                    *supplied,
                    "--display-output",
                    str(board),
                    "--output",
                    str(output),
                ),
                files=(
                    FileExpectation(
                        output,
                        "created",
                        required_terms=(
                            "# Price Action Watch-only",
                            "ticker + trade_horizon + instrument",
                            f"`{missing.replace('-', '_')}`",
                        ),
                        forbidden_terms=(
                            "## 走势强弱参考点位",
                            "![PA Scenario Board]",
                        ),
                    ),
                    FileExpectation(board, "absent"),
                ),
            )
        )

    omitted_output = tmp / "omitted-ohlcv.md"
    omitted_board = tmp / "omitted-ohlcv.svg"
    cases.append(
        CommandCase(
            case_id="precedence/incomplete-key-before-omitted-ohlcv",
            command=_price_action_command(
                "--ticker",
                "QQQ",
                "--instrument",
                "ETF",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H",
                "--display-output",
                str(omitted_board),
                "--output",
                str(omitted_output),
            ),
            files=(
                FileExpectation(
                    omitted_output,
                    "created",
                    required_terms=("# Price Action Watch-only - QQQ", "`trade_horizon`"),
                    forbidden_terms=("![PA Scenario Board]",),
                ),
                FileExpectation(omitted_board, "absent"),
            ),
        )
    )

    invalid_ohlcv = tmp / "invalid-ohlcv.txt"
    invalid_ohlcv.write_text("not JSON; setup validation must run before this is read\n", encoding="utf-8")
    invalid_output = tmp / "invalid-ohlcv.md"
    invalid_board = tmp / "invalid-ohlcv.svg"
    cases.append(
        CommandCase(
            case_id="precedence/incomplete-key-before-invalid-ohlcv",
            command=_price_action_command(
                "--ohlcv-json",
                str(invalid_ohlcv),
                "--ticker",
                "QQQ",
                "--instrument",
                "ETF",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H",
                "--display-output",
                str(invalid_board),
                "--output",
                str(invalid_output),
            ),
            files=(
                FileExpectation(
                    invalid_ohlcv,
                    "unchanged",
                ),
                FileExpectation(
                    invalid_output,
                    "created",
                    required_terms=(
                        "# Price Action Watch-only - QQQ",
                        "`trade_horizon`",
                        "OHLCV 未读取：complete setup key missing",
                    ),
                ),
                FileExpectation(invalid_board, "absent"),
            ),
        )
    )

    complete_output = tmp / "complete.md"
    complete_board = tmp / "complete.svg"
    cases.append(
        CommandCase(
            case_id="completeness/complete-authorized-ohlcv",
            command=_price_action_command(
                *common,
                "--ticker",
                "QQQ",
                "--trade-horizon",
                "medium-term swing",
                "--instrument",
                "equity",
                "--display-output",
                str(complete_board),
                "--output",
                str(complete_output),
            ),
            files=(
                FileExpectation(
                    complete_output,
                    "created",
                    required_terms=("# Price Action Rollforward - QQQ", "## PA Scenario Board"),
                ),
                FileExpectation(complete_board, "created", required_terms=("<svg", "QQQ")),
            ),
        )
    )

    no_ohlcv_output = tmp / "complete-no-ohlcv.md"
    no_ohlcv_board = tmp / "complete-no-ohlcv.svg"
    cases.append(
        CommandCase(
            case_id="ohlcv/complete-key-missing-payload",
            command=_price_action_command(
                "--ticker",
                "QQQ",
                "--trade-horizon",
                "medium-term swing",
                "--instrument",
                "ETF",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H",
                "--display-output",
                str(no_ohlcv_board),
                "--output",
                str(no_ohlcv_output),
            ),
            expected_returncode=1,
            required_stderr=(
                "complete setup key requires --ohlcv-json authorized or fixture OHLCV data",
            ),
            files=(
                FileExpectation(no_ohlcv_output, "absent"),
                FileExpectation(no_ohlcv_board, "absent"),
            ),
        )
    )
    return tuple(cases)


def run_setup_key_matrix() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        result = run_command_matrix("setup-key", build_setup_key_cases(Path(raw_tmp)))
    if not result.ok:
        print(result.render_failures(), file=sys.stderr)
        return 1
    print("behavior contract matrix setup-key ok")
    return 0


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
    for surface, status in (
        ("router", "uninitialized"),
        ("reference", "ready"),
        ("reference", "partial"),
        ("reference", "uninitialized"),
        ("template", "partial"),
        ("template", "uninitialized"),
        ("fixture", "ready"),
        ("fixture", "partial"),
        ("fixture", "uninitialized"),
        ("direct-activation", "uninitialized"),
    ):
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


def run_startup_matrix() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        result = run_command_matrix("startup", build_startup_cases(Path(raw_tmp)))
    if not result.ok:
        print(result.render_failures(), file=sys.stderr)
        return 1
    print("behavior contract matrix startup ok")
    return 0


def main() -> int:
    args = parse_args()
    if args.family == "reconciliation":
        return run_reconciliation_matrix()
    if args.family == "startup":
        return run_startup_matrix()
    if args.family == "setup-key":
        return run_setup_key_matrix()
    raise AssertionError(f"unhandled family: {args.family}")


if __name__ == "__main__":
    raise SystemExit(main())
