#!/usr/bin/env python3
"""Verify Daily runtime package preparation is documented and gated."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references
TEMPLATES = PATHS.templates

FILES = {
    "prepare_script": ROOT / "scripts" / "prepare_daily_runtime.py",
    "prepare_selftest": ROOT / "scripts" / "verify_daily_runtime_package_selftest.py",
    "intraday_scan": ROOT / "scripts" / "intraday_scan.py",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "runtime_health_reference": REFERENCES / "runtime-health.md",
    "router_skill": ROOT / "skills" / "trading-research" / "SKILL.md",
    "orchestrator_template": TEMPLATES / "daily-ops-orchestrator.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "mvp_runbook": REPO / "docs" / "MVP_RUNBOOK.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "prepare_script": [
        "Prepare a Daily Ops runtime package",
        "TRADING_RESEARCH_RUNTIME_DIR",
        "--dry-run",
        "--overwrite",
        "ops-state.md",
        "trade-plans.csv",
        "intraday-watchlist.csv",
        "header-only CSV containers",
        "No live broker reads",
        "no order actions",
        "Active Market Plan",
        "Trading Profile",
    ],
    "prepare_selftest": [
        "daily runtime package selftest ok",
        "--dry-run",
        "header-only",
        "must not overwrite user trade plans",
        "没有已准备的 setup 行",
        "runtime_health.py",
    ],
    "intraday_scan": [
        "没有已准备的 setup 行",
        "这是决策辅助，不是买卖指令",
        "cannot claim approaching / triggered",
    ],
    "contract_suite": [
        "verify_daily_runtime_package_selftest.py",
        "verify_daily_runtime_package_contract.py",
    ],
    "runtime_health_reference": [
        "prepare_daily_runtime.py",
        "daily runtime package",
        "header-only",
        "trade-plans.csv",
        "intraday-watchlist.csv",
    ],
    "router_skill": [
        "prepare_daily_runtime.py",
        "daily runtime package",
        "trade-plans.csv",
        "intraday-watchlist.csv",
    ],
    "orchestrator_template": [
        "prepare_daily_runtime.py",
        "初始化今天 runtime 草稿",
        "trade-plans.csv",
        "intraday-watchlist.csv",
        "不会覆盖已有文件",
    ],
    "root_readme": [
        "Daily runtime package",
        "prepare_daily_runtime.py",
        "header-only",
        "No live broker reads",
    ],
    "plugin_readme": [
        "Daily runtime package",
        "prepare_daily_runtime.py",
        "header-only",
        "No live broker reads",
    ],
    "mvp_runbook": [
        "Daily runtime package",
        "prepare_daily_runtime.py",
        "intraday-watchlist.csv",
    ],
    "development_plan": [
        "Daily runtime package",
        "prepare_daily_runtime.py",
    ],
    "project_log": [
        "Daily runtime package",
        "prepare_daily_runtime.py",
    ],
}

TEMPLATE_FILES = {
    "template_trade_plans": FileContract(
        TEMPLATES / "trade-plans.csv",
        csv_header=CSV_SCHEMAS["trade-plans.csv"],
        forbidden_terms=("QQQ 0DTE", "2026-06-12", "485C"),
        forbidden_label="sample trade row",
    ),
    "template_intraday_watchlist": FileContract(
        TEMPLATES / "intraday-watchlist.csv",
        csv_header=CSV_SCHEMAS["intraday-watchlist.csv"],
        forbidden_terms=("QQQ 0DTE", "2026-06-12", "485C"),
        forbidden_label="sample setup row",
    ),
    "template_trades": FileContract(
        TEMPLATES / "trades.csv",
        csv_header=CSV_SCHEMAS["trades.csv"],
        forbidden_terms=("QQQ 0DTE", "2026-06-12", "485C"),
        forbidden_label="sample trade row",
    ),
    "template_watchlist": FileContract(
        TEMPLATES / "watchlist.csv",
        csv_header=CSV_SCHEMAS["watchlist.csv"],
        forbidden_terms=("MSFT", "XLE", "quality AI platform"),
        forbidden_label="sample watchlist row",
    ),
    "template_portfolio": FileContract(
        TEMPLATES / "holdings.csv",
        csv_header=CSV_SCHEMAS["holdings.csv"],
        forbidden_terms=("SPY", "TLT", "core equity exposure"),
        forbidden_label="sample holding row",
    ),
}

SPEC = ContractSpec(
    name="daily runtime package",
    success_message="daily runtime package contract ok",
    failure_header="daily runtime package contract failed:",
    files={
        **{
            key: FileContract(path=path, required_terms=REQUIRED[key])
            for key, path in FILES.items()
        },
        **TEMPLATE_FILES,
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
