#!/usr/bin/env python3
"""Verify natural-language router intent fixtures stay AI-native."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "router-intents.json"

ALLOWED_WORKFLOWS = {
    "broker_source_configuration",
    "daily_ops_orchestrator",
    "deep_active_market_plan_update",
    "intraday_setup_scan",
    "kvn_snapshot_lookup",
    "macro_equity_research",
    "portfolio_risk",
    "position_daily_report",
    "post_exit_trade_review",
    "post_order_trade_review",
    "quick_active_market_plan_update",
    "research_report_intake",
    "runtime_health",
    "trading_stats",
}

ALLOWED_LABELS = {
    "本次路由",
    "读取状态",
    "结论",
    "变化",
    "影响",
    "需要你决定",
    "下一步",
}

REQUIRED_LABELS = {"本次路由", "读取状态", "结论", "需要你决定"}

FOCUSED_SKILL_NAMES = {
    "$weekly-trading-plan",
    "$daily-market-tracking",
    "$intraday-setup-scan",
    "$trade-review",
    "$research-report-intake",
    "$macro-equity-research",
    "$portfolio-risk",
    "$trading-stats",
}


def main() -> int:
    failures = verify_router_contract(FIXTURE)
    if failures:
        print("router contract verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("router contract ok")
    return 0


def verify_router_contract(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing router intent fixture: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"invalid JSON in {path}: {error}"]

    if not isinstance(data, dict):
        return [f"router fixture root must be an object in {path}"]

    fixtures = data.get("router_intents")
    if not isinstance(fixtures, list) or not fixtures:
        return ["router_intents must be a non-empty list"]

    failures: list[str] = []
    seen_ids: set[str] = set()
    covered_workflows: set[str] = set()

    for index, fixture in enumerate(fixtures, start=1):
        if not isinstance(fixture, dict):
            failures.append(f"fixture {index}: must be an object")
            continue

        fixture_id = _required_str(fixture, "id", failures, index)
        prompt = _required_str(fixture, "prompt", failures, index)
        public_route_label = _required_str(
            fixture,
            "expected_public_route_label",
            failures,
            index,
        )

        if fixture_id:
            if fixture_id in seen_ids:
                failures.append(f"{fixture_id}: duplicate id")
            seen_ids.add(fixture_id)

        if prompt:
            if prompt.strip().startswith("$"):
                failures.append(f"{fixture_id}: prompt should be natural language, not a skill invocation")
            _check_no_focused_skill_names(fixture_id, "prompt", prompt, failures)

        if public_route_label:
            _check_no_focused_skill_names(
                fixture_id,
                "expected_public_route_label",
                public_route_label,
                failures,
            )

        workflows = _required_str_list(fixture, "expected_workflows", failures, fixture_id)
        for workflow in workflows:
            if workflow not in ALLOWED_WORKFLOWS:
                failures.append(f"{fixture_id}: unknown workflow {workflow!r}")
            covered_workflows.add(workflow)

        labels = set(_required_str_list(fixture, "expected_output_labels", failures, fixture_id))
        unknown_labels = labels - ALLOWED_LABELS
        if unknown_labels:
            failures.append(f"{fixture_id}: unknown output labels {sorted(unknown_labels)!r}")

        missing_labels = REQUIRED_LABELS - labels
        if missing_labels:
            failures.append(f"{fixture_id}: missing required output labels {sorted(missing_labels)!r}")

        _required_str_list(fixture, "required_reads", failures, fixture_id)

    required_coverage = {
        "daily_ops_orchestrator",
        "deep_active_market_plan_update",
        "quick_active_market_plan_update",
        "intraday_setup_scan",
        "research_report_intake",
        "post_order_trade_review",
        "post_exit_trade_review",
        "position_daily_report",
        "portfolio_risk",
        "kvn_snapshot_lookup",
    }
    missing_coverage = required_coverage - covered_workflows
    if missing_coverage:
        failures.append(f"missing workflow coverage: {sorted(missing_coverage)!r}")

    return failures


def _required_str(
    fixture: dict[str, Any],
    key: str,
    failures: list[str],
    index: int,
) -> str:
    value = fixture.get(key)
    fixture_id = fixture.get("id", f"fixture {index}")
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{fixture_id}: {key} must be a non-empty string")
        return ""
    return value


def _required_str_list(
    fixture: dict[str, Any],
    key: str,
    failures: list[str],
    fixture_id: str,
) -> list[str]:
    value = fixture.get(key)
    if not isinstance(value, list) or not value:
        failures.append(f"{fixture_id}: {key} must be a non-empty list")
        return []

    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            failures.append(f"{fixture_id}: {key} contains a non-string or empty item")
            continue
        result.append(item)
    return result


def _check_no_focused_skill_names(
    fixture_id: str,
    key: str,
    text: str,
    failures: list[str],
) -> None:
    for skill_name in sorted(FOCUSED_SKILL_NAMES):
        if skill_name in text:
            failures.append(f"{fixture_id}: {key} exposes focused skill {skill_name!r}")


if __name__ == "__main__":
    sys.exit(main())
