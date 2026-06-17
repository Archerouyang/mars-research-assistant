#!/usr/bin/env python3
"""Verify the research report intake contract is wired through the plugin."""

from pathlib import Path
import sys


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
    "readme": ROOT / "README.md",
    "manifest": ROOT / ".codex-plugin" / "plugin.json",
    "init_daily": ROOT / "scripts" / "init_daily.py",
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
    "readme": [
        "$research-report-intake",
        "Research report discovery",
        "User-provided report intake",
    ],
    "manifest": [
        "research reports",
        "Read this research report and extract the plan impact.",
    ],
    "init_daily": [
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
}


def main() -> int:
    errors: list[str] = []
    for key, path in FILES.items():
        if not path.exists():
            errors.append(f"{key}: missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in REQUIRED[key]:
            if needle not in text:
                errors.append(f"{key}: missing {needle!r} in {path}")
        for needle in FORBIDDEN.get(key, []):
            if needle in text:
                errors.append(f"{key}: forbidden stale term {needle!r} in {path}")

    if errors:
        print("Research report intake contract verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Research report intake contract verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
