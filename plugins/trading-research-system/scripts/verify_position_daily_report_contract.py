#!/usr/bin/env python3
"""Verify position daily report contract files and fixture path."""

from __future__ import annotations

import sys
from pathlib import Path

from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
DAILY_DIR = ROOT / "assets" / "fixtures" / "runtime" / "active-market-plan-2026-06-24" / "daily" / "2026-06-24"


def build_spec() -> ContractSpec:
    return ContractSpec(
        name="position daily report",
        success_message="position daily report contract ok",
        failure_header="position daily report contract verification failed",
        files={
            "reference": FileContract(
                ROOT / "skills" / "trading-research" / "references" / "position-daily-report.md",
                required_terms=(
                    "# Position Daily Report",
                    "broker-live by default",
                    "Source Order",
                    "Script Path",
                    "position_daily_report.py",
                    "portfolio_snapshot.csv",
                    "does not connect to brokers",
                    "does not place orders",
                ),
            ),
            "broker contract": FileContract(
                ROOT / "skills" / "trading-research" / "references" / "broker-data-contract.md",
                required_terms=(
                    "read-only data",
                    "portfolio_snapshot.csv",
                    "position_daily_report.py",
                    "broker-agnostic",
                    "Do not run that install command automatically",
                ),
            ),
            "portfolio skill": FileContract(
                ROOT / "skills" / "portfolio-risk" / "SKILL.md",
                required_terms=(
                    "position_daily_report.py",
                    "portfolio_snapshot.csv",
                    "authorized connector",
                    "Do not approve a trade",
                ),
            ),
            "router": FileContract(
                ROOT / "skills" / "trading-research" / "SKILL.md",
                required_terms=(
                    "position_daily_report.py",
                    "Holdings, sizing, portfolio exposure",
                    "portfolio-risk",
                ),
            ),
            "script": FileContract(
                ROOT / "scripts" / "position_daily_report.py",
                required_terms=(
                    "portfolio_snapshot.csv",
                    "Source:",
                    "需要用户决策",
                    "产品暴露",
                    "Broker exposure",
                    "杠杆/单股 ETF",
                    "不生成任何订单动作",
                    "does not verify live broker authorization",
                ),
            ),
            "selftest": FileContract(
                ROOT / "scripts" / "verify_position_daily_report_selftest.py",
                required_terms=(
                    "position_daily_report.py",
                    "portfolio_snapshot.csv",
                    "position-daily-report.md",
                ),
            ),
            "fixture snapshot": FileContract(
                DAILY_DIR / "portfolio_snapshot.csv",
                csv_header=CSV_SCHEMAS["portfolio_snapshot.csv"],
                csv_rows_match_header=True,
            ),
            "fixture report": FileContract(
                DAILY_DIR / "position-daily-report.md",
                required_terms=(
                    "# 持仓日报 - 2026-06-24",
                    "Source: broker-live fixture",
                    "Coverage: 2 broker/account source(s)",
                    "需要用户决策",
                    "产品结构",
                    "杠杆/单股 ETF",
                    "Broker / account exposure",
                    "Active Market Plan risk budget",
                    "不生成任何订单动作",
                    "数据缺口",
                ),
            ),
            "automation template": FileContract(
                ROOT / "assets" / "templates" / "automation-position-daily-report.md",
                required_terms=(
                    "# Position Daily Report Automation Prompt",
                    "Longbridge skill/plugin",
                    "IBKR connector",
                    "portfolio_snapshot.csv",
                    "position_daily_report.py",
                    "Do not place, modify, cancel, close, or approve orders",
                    "Ask before writing runtime files",
                ),
            ),
            "automation contract": FileContract(
                ROOT / "skills" / "trading-research" / "references" / "automation-contract.md",
                required_terms=(
                    "automation-position-daily-report.md",
                    "position_daily_report.py",
                    "portfolio_snapshot.csv",
                    "If broker data is unavailable",
                ),
            ),
            "roadmap": FileContract(
                ROOT.parents[1] / "docs" / "ROADMAP.md",
                required_terms=(
                    "Broker-live position daily report script",
                    "position_daily_report.py",
                    "automation-position-daily-report.md",
                ),
            ),
            "development plan": FileContract(
                ROOT.parents[1] / "docs" / "DEVELOPMENT_PLAN.md",
                required_terms=(
                    "Add broker-live position daily report",
                    "position_daily_report.py",
                    "automation-position-daily-report.md",
                ),
            ),
        },
    )


if __name__ == "__main__":
    sys.exit(run_contract(build_spec()))
