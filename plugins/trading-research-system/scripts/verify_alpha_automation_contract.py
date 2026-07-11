#!/usr/bin/env python3
"""Verify scheduled Alpha jobs and Gmail outbox safety contracts."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)

SPEC = ContractSpec(
    name="alpha automations",
    success_message="alpha automation contract ok",
    failure_header="alpha automation contract failed:",
    files={
        "daily": FileContract(
            PATHS.templates / "automation-alpha-daily-publish.md",
            required_terms=(
                "uv run",
                "schedule-plan",
                "run-acquire",
                "provider-probe",
                "refresh-prices",
                "train-champion",
                "publish-daily",
                "outbox.sqlite",
                "run-complete",
                "不得包含 API key",
                "禁止 broker/order",
                "{quant_repo}",
                "cd {quant_repo} && uv run dailytrades-quant schedule-plan",
            ),
            forbidden_terms=("/Users/archer",),
        ),
        "weekly": FileContract(
            PATHS.templates / "automation-alpha-weekly-shadow.md",
            required_terms=(
                "weekly",
                "train-challenger",
                "target_end_date < validation_start",
                "shadow",
                "不改变 production Alpha Rank",
                "20 个 shadow trading days",
                "GPT-5.6 Sol",
            ),
        ),
        "monthly": FileContract(
            PATHS.templates / "automation-alpha-monthly-governance.md",
            required_terms=(
                "monthly",
                "evaluate-bayesian",
                "governance-report",
                "Rank IC",
                "Top5/Top10/Top20",
                "Brier score",
                "point_in_time_status",
                "survivorship-biased",
                "sol_review=pending",
            ),
        ),
        "gmail": FileContract(
            PATHS.templates / "automation-alpha-gmail-dispatch.md",
            required_terms=(
                "outbox-next",
                "Gmail connector",
                "outbox-mark-sent",
                "outbox-mark-failed",
                "event id",
                "发送失败不回滚 Alpha",
                "API key",
                "positions",
                "alpha_notification_adapter.py",
                "fail closed",
            ),
        ),
        "notification_adapter": FileContract(
            PATHS.scripts / "alpha_notification_adapter.py",
            required_terms=(
                "connect_read_only",
                "?mode=ro",
                "ALLOWED_KINDS",
                "ALLOWED_METADATA",
                "FORBIDDEN_CONTENT",
                "build_outbound_event",
                "ALLOWED_NEXT_ACTIONS",
                "non-allowlisted metadata",
            ),
            forbidden_terms=("UPDATE notification_outbox", "DELETE FROM"),
        ),
        "notification_selftest": FileContract(
            PATHS.scripts / "verify_alpha_notification_adapter_selftest.py",
            required_terms=(
                "private outbox metadata must fail closed",
                "secret-like notification content must fail closed",
                "alpha notification adapter selftest ok",
            ),
        ),
        "setup": FileContract(
            PATHS.templates / "automation-setup-checklist.md",
            required_terms=(
                "alpha_daily_publish",
                "alpha_weekly_shadow",
                "alpha_monthly_governance",
                "alpha_gmail_dispatch",
                "dailytrades-quant",
                "quant_repo",
                "quant_runtime",
                "uat-dry-run",
                "alpha_leaderboard_adapter.py",
                "alpha_notification_adapter.py",
                "Gmail `not_sent`",
                "broker/network `not_used`",
                "isolated dry-run evidence",
                "clean runtime",
            ),
        ),
    },
)


if __name__ == "__main__":
    sys.exit(run_contract(SPEC))
