#!/usr/bin/env python3
"""Setup-key, OHLCV provenance, and side-effect behavior cases."""

from __future__ import annotations

from pathlib import Path
import sys

from behavior_contract_matrix import CommandCase, FileExpectation


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"
PRICE_ACTION = SKILL / "scripts" / "price_action_rollforward.py"
OHLCV_FIXTURE = (
    SKILL / "assets" / "fixtures" / "input" / "chart-ohlcv-qqq-sample.json"
)


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
                    "--ohlcv-status",
                    "authorized",
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

    for ohlcv_status in ("authorized", "user_provided", "fixture", "needs_review"):
        case_status = ohlcv_status.replace("_", "-")
        complete_output = tmp / f"complete-{case_status}.md"
        complete_board = tmp / f"complete-{case_status}.svg"
        board_expected = ohlcv_status != "needs_review"
        cases.append(
            CommandCase(
                case_id=f"ohlcv/{case_status}/complete-key",
                command=_price_action_command(
                    *common,
                    "--ohlcv-status",
                    ohlcv_status,
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
                        required_terms=("# Price Action Rollforward - QQQ",),
                        forbidden_terms=()
                        if board_expected
                        else ("## PA Scenario Board", "![PA Scenario Board]"),
                    ),
                    FileExpectation(
                        complete_board,
                        "created" if board_expected else "absent",
                        required_terms=("<svg", "QQQ") if board_expected else (),
                    ),
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


