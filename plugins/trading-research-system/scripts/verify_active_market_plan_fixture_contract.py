#!/usr/bin/env python3
"""Verify the Active Market Plan fixture package is complete and coherent."""

from __future__ import annotations

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "assets" / "fixtures" / "runtime" / "active-market-plan-2026-06-24"
DAILY_DIR = FIXTURE_ROOT / "daily" / "2026-06-24"
EXPECTED_DIR = ROOT / "assets" / "fixtures" / "expected"


def build_spec() -> ContractSpec:
    return ContractSpec(
        name="active market plan fixture",
        success_message="active market plan fixture contract ok",
        failure_header="active market plan fixture verification failed",
        files={
            "market plan": FileContract(
                FIXTURE_ROOT / "market-plan.md",
                required_terms=(
                    "# Active Market Plan Fixture",
                    "As of: 2026-06-24",
                    "Trade Plan Preparation",
                    "KVN Momentum Leaderboard",
                    "Cross-Section Candidate Pool",
                    "Setup Pool",
                    "crdo-ai-infra-pullback",
                    "qqq-0dte-breakout-pullback",
                    "position daily report",
                    "broker-live fixture",
                    "decision support only",
                ),
            ),
            "trading profile": FileContract(
                FIXTURE_ROOT / "trading-profile.md",
                required_terms=(
                    "# Trading Profile Fixture",
                    "strategy posture",
                    "instrument preference",
                    "ETF core",
                    "momentum additions",
                    "0DTE",
                    "LEAP",
                    "risk limits",
                    "synthetic fixture",
                ),
            ),
            "update note": FileContract(
                FIXTURE_ROOT / "updates" / "2026-06-24.md",
                required_terms=(
                    "# Active Market Plan Update",
                    "deep_update",
                    "KVN snapshot",
                    "setup status changes",
                    "portfolio exposure",
                    "next inspection order",
                ),
            ),
            "trade plans": FileContract(
                DAILY_DIR / "trade-plans.csv",
                csv_header=CSV_SCHEMAS["trade-plans.csv"],
                csv_rows_match_header=True,
                required_terms=(
                    "crdo-ai-infra-pullback",
                    "qqq-0dte-breakout-pullback",
                    "soxx-sector-confirmation",
                    "candidate",
                    "active",
                ),
            ),
            "intraday watchlist": FileContract(
                DAILY_DIR / "intraday-watchlist.csv",
                csv_header=CSV_SCHEMAS["intraday-watchlist.csv"],
                csv_rows_match_header=True,
                required_terms=(
                    "approaching",
                    "needs_review",
                    "triggered",
                    "execution_check_required",
                ),
            ),
            "portfolio snapshot": FileContract(
                DAILY_DIR / "portfolio_snapshot.csv",
                csv_header=CSV_SCHEMAS["portfolio_snapshot.csv"],
                csv_rows_match_header=True,
                required_terms=(
                    "Longbridge",
                    "IBKR",
                    "QQQ",
                    "SOXX",
                    "semiconductor",
                    "tech_beta",
                ),
            ),
            "broker executions": FileContract(
                DAILY_DIR / "broker_executions.csv",
                csv_header=CSV_SCHEMAS["broker_executions.csv"],
                csv_rows_match_header=True,
                required_terms=("SIM-EXEC-001", "post_order", "crdo-ai-infra-pullback"),
            ),
            "broker orders": FileContract(
                DAILY_DIR / "broker_orders.csv",
                csv_header=CSV_SCHEMAS["broker_orders.csv"],
                csv_rows_match_header=True,
                required_terms=("SIM-ORD-001", "submitted", "qqq-0dte-breakout-pullback"),
            ),
            "position daily report": FileContract(
                DAILY_DIR / "position-daily-report.md",
                required_terms=(
                    "# 持仓日报 - 2026-06-24",
                    "broker-live fixture",
                    "需要用户决策",
                    "tech_beta",
                    "semiconductor",
                    "可视化",
                    "Snapshot saved: fixture",
                ),
            ),
            "reviews": FileContract(
                DAILY_DIR / "reviews.md",
                required_terms=(
                    "# Daily Review",
                    "post_order",
                    "post_exit",
                    "Plan vs actual",
                    "CRDO",
                    "QQQ 0DTE",
                    "System Notes",
                ),
            ),
            "expected scan": FileContract(
                EXPECTED_DIR / "intraday-scan-2026-06-24.md",
                required_terms=(
                    "# Intraday Setup Scan Expected Output",
                    "approaching",
                    "triggered",
                    "invalidated",
                    "needs_review",
                    "execution_check_required",
                    "not a buy/sell instruction",
                ),
            ),
        },
    )


if __name__ == "__main__":
    sys.exit(run_contract(build_spec()))
