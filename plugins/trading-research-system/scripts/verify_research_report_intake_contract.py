#!/usr/bin/env python3
"""Verify the research report intake contract is wired through the plugin."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "skill": ROOT / "skills" / "research-report-intake" / "SKILL.md",
    "reference": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "research-report-intake.md",
    "router": ROOT / "skills" / "trading-research" / "SKILL.md",
    "macro_skill": ROOT / "skills" / "macro-equity-research" / "SKILL.md",
    "equity_screening": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "equity-screening.md",
    "output_templates": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "output-templates.md",
    "report_log": ROOT / "assets" / "templates" / "research-report-log.csv",
    "expected_digest": ROOT
    / "assets"
    / "fixtures"
    / "expected"
    / "research-report-digest-sample.md",
    "input_user_report": ROOT
    / "assets"
    / "fixtures"
    / "input"
    / "research-report-user-provided-ai-infra.md",
    "input_discovery": ROOT
    / "assets"
    / "fixtures"
    / "input"
    / "research-report-discovery-ai-infra.md",
    "expected_user_report": ROOT
    / "assets"
    / "fixtures"
    / "expected"
    / "research-report-intake-ai-infra.md",
    "expected_discovery": ROOT
    / "assets"
    / "fixtures"
    / "expected"
    / "research-report-discovery-ai-infra.md",
    "readme": ROOT / "README.md",
    "manifest": ROOT / ".codex-plugin" / "plugin.json",
    "init_daily": ROOT / "scripts" / "init_daily.py",
    "record_schemas": ROOT / "scripts" / "record_schemas.py",
    "context": REPO / "CONTEXT.md",
    "roadmap": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "skill": [
        "name: research-report-intake",
        "Research Report Intake",
        "Report Discovery",
        "User-Provided Report Intake",
        "Claim Ledger",
        "Verification Queue",
        "Trade Plan Preparation Impact",
        "Do not bypass paywalls",
    ],
    "reference": [
        "Source Priority",
        "Discovery Mode",
        "Intake Mode",
        "Claim Ledger",
        "Verification Queue",
        "Research Report Digest",
        "Trade Plan Preparation Impact",
        "Copyright Boundary",
    ],
    "router": [
        "Research report discovery, user-provided PDF/link/text digestion",
        "research-report-intake",
    ],
    "macro_skill": [
        "research-report-intake",
        "Research Report Digest",
        "Claim Ledger",
    ],
    "equity_screening": [
        "research-report-intake",
        "Research Report Digest",
        "Claim Ledger",
    ],
    "output_templates": [
        "## Research Report Digest",
        "## Claim Ledger",
        "## Verification Queue",
        "## Trade Plan Preparation Impact",
    ],
    "report_log": [
        "report_id,source_priority,source_type,title,ticker_or_theme",
        "thesis,verification_status,next_check",
    ],
    "expected_digest": [
        "## 结论",
        "## Research Report Digest",
        "## Claim Ledger",
        "## Verification Queue",
        "## Trade Plan Preparation Impact",
        "Company Thesis Check",
        "needs_check",
        "不能直接升级为 setup",
    ],
    "input_user_report": [
        "synthetic fixture",
        "Source Metadata",
        "access_status",
        "source_priority",
        "user-provided",
        "Material Claims To Extract",
        "Do not promote the idea directly to `candidate setup`",
    ],
    "input_discovery": [
        "Report Discovery Fixture",
        "User Request",
        "Candidate Source States",
        "access_status",
        "inaccessible",
        "do not bypass any paywall",
        "Output what each source could change in Trade Plan Preparation",
    ],
    "expected_user_report": [
        "## 结论",
        "## Research Report Digest",
        "## Claim Ledger",
        "## Verification Queue",
        "## Trade Plan Preparation Impact",
        "## 不可访问来源处理",
        "S3 research/opinion",
        "needs_check",
        "Cross-Section Candidate Pool",
        "不能直接升级为 `candidate setup`",
        "must not bypass paywalls",
    ],
    "expected_discovery": [
        "## 结论",
        "## Discovery Sources",
        "## Verification Queue",
        "## Trade Plan Preparation Impact",
        "## Access Boundary",
        "S0 official / primary",
        "S1 market data / broker / macrodata / calendar",
        "S3 research / opinion",
        "inaccessible",
        "Do not bypass paywalls",
        "Do not imply the inaccessible report was read",
    ],
    "readme": [
        "读这篇 NVDA 研报",
        "Advanced Skill Surface",
        "research-report-intake",
        "Research report discovery",
        "User-provided report intake",
    ],
    "manifest": [
        "research reports",
        "Read this research report and extract the plan impact.",
    ],
    "init_daily": [
        "DAILY_TEMPLATE_TARGETS",
    ],
    "record_schemas": [
        "CSV_SCHEMAS",
        '"research-report-log.csv": "research-report-log.csv"',
    ],
    "context": [
        "研报摄取",
        "研报发现",
        "Claim Ledger",
        "Verification Queue",
        "Trade Plan Preparation Impact",
    ],
    "roadmap": [
        "Define research report intake contract",
        "research-report-intake",
    ],
}

FORBIDDEN = {
    "report_log": ["next_action"],
    "output_templates": ["## Report Digest"],
    "skill": ["`Report Digest`"],
    "macro_skill": ["`Report Digest`"],
    "expected_digest": ["## Report Digest", "next_action"],
    "input_user_report": ["guaranteed return"],
    "input_discovery": ["summarize inaccessible content"],
    "expected_user_report": ["## Report Digest", "next_action", "guaranteed"],
    "expected_discovery": ["## Report Digest", "next_action", "summarized inaccessible"],
}


SPEC = ContractSpec(
    name="research report intake",
    success_message="Research report intake contract verification passed.",
    failure_header="Research report intake contract verification failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED[key],
            forbidden_terms=FORBIDDEN.get(key, ()),
            forbidden_label="forbidden stale term",
            csv_header=CSV_SCHEMAS["research-report-log.csv"] if key == "report_log" else None,
            csv_rows_match_header=key == "report_log",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
