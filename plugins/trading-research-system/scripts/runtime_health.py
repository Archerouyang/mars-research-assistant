#!/usr/bin/env python3
"""Report private runtime health without reading private file contents."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
import json
from pathlib import Path
import time

from runtime_state import default_runtime_dir, resolve_daily_dir, resolve_runtime_selection


STATUSES = {"available", "missing", "stale", "unauthorized", "needs_review"}
BROKER_STATUSES = STATUSES | {
    "not_installed",
    "partial_data",
    "upstream_error",
    "empty_positions_unverified",
}
BROKER_SOURCES = {"longbridge", "ibkr", "manual"}
LIVE_BROKER_SOURCES = ("longbridge", "ibkr")
SOURCE_CAPABILITIES = {
    "longbridge_broker_skill",
    "longbridge_terminal_cli",
    "longbridge_macrodata",
    "official_source_fallback",
    "ibkr_connector",
    "manual_snapshot",
}
BROKER_SOURCE_LABELS = {
    "longbridge": "Longbridge",
    "ibkr": "IBKR",
    "manual": "Manual snapshot",
}
BROKER_SOURCE_CHECK_IDS = {
    "longbridge": "longbridge_broker_source",
    "ibkr": "ibkr_broker_source",
    "manual": "manual_snapshot_source",
}
SOURCE_CAPABILITY_LABELS = {
    "longbridge_broker_skill": "Longbridge broker skill",
    "longbridge_terminal_cli": "Longbridge Terminal CLI",
    "longbridge_macrodata": "Longbridge macrodata",
    "official_source_fallback": "Official source fallback",
    "ibkr_connector": "IBKR connector",
    "manual_snapshot": "Manual snapshot",
}


@dataclass(frozen=True)
class RuntimeCheck:
    id: str
    label: str
    status: str
    path: str | None = None
    note: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check private Trading Research runtime state without reading file contents."
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=None,
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/dailytrades-runtime",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--broker-source",
        action="append",
        default=[],
        metavar="SOURCE=STATUS",
        help="Broker source status, e.g. longbridge=available or ibkr=unauthorized",
    )
    parser.add_argument(
        "--source-capability",
        action="append",
        default=[],
        metavar="CAPABILITY=STATUS",
        help=(
            "Source capability status, e.g. longbridge_macrodata=available, "
            "official_source_fallback=available, "
            "longbridge_terminal_cli=available, longbridge_broker_skill=not_installed, "
            "or ibkr_connector=available"
        ),
    )
    parser.add_argument(
        "--stale-after-days",
        type=int,
        default=None,
        help="Mark existing files stale when modified more than this many days ago",
    )
    return parser.parse_args()


def build_runtime_health(
    runtime_dir: Path,
    trading_date: str,
    broker_sources: list[str],
    source_capabilities: list[str] | None = None,
    stale_after_days: int | None = None,
    runtime_origin: str = "explicit_argument",
) -> dict[str, object]:
    runtime_dir = runtime_dir.expanduser()
    daily_dir = resolve_daily_dir(runtime_dir, trading_date)
    broker_health = build_broker_source_health(broker_sources)
    capability_health = build_source_capability_health(
        source_capabilities or [],
        broker_health["source_statuses"],
    )
    runtime_checks = [
        path_check("runtime_dir", "Runtime directory", runtime_dir, stale_after_days),
        path_check("market_plan", "Active Market Plan", runtime_dir / "market-plan.md", stale_after_days),
        path_check("ops_state", "Daily Ops State", runtime_dir / "ops-state.md", stale_after_days),
        path_check("trading_profile", "Trading Profile", runtime_dir / "trading-profile.md", stale_after_days),
        path_check("updates_dir", "Updates directory", runtime_dir / "updates", stale_after_days),
        path_check("daily_dir", "Daily directory", daily_dir, stale_after_days),
        path_check("trade_plans", "Trade plans", daily_dir / "trade-plans.csv", stale_after_days),
        path_check(
            "intraday_watchlist",
            "Intraday watchlist",
            daily_dir / "intraday-watchlist.csv",
            stale_after_days,
        ),
        path_check("macro_panel", "Macro panel", daily_dir / "macro-panel.json", stale_after_days),
        path_check(
            "portfolio_snapshot",
            "Portfolio snapshot",
            daily_dir / "portfolio_snapshot.csv",
            stale_after_days,
        ),
        path_check("kvn_store", "KVN store", runtime_dir / "momentum" / "kvn.sqlite", stale_after_days),
    ]
    checks = runtime_checks + capability_health["checks"] + broker_health["checks"]
    return {
        "runtime_dir": str(runtime_dir),
        "runtime_origin": runtime_origin,
        "startup_status": infer_startup_status(runtime_checks),
        "date": trading_date,
        "current_mode": broker_health["current_mode"],
        "source_capability_health": capability_health["source_capability_health"],
        "broker_source_health": broker_health["source_health"],
        "portfolio_reconciliation": broker_health["portfolio_reconciliation"],
        "checks": [asdict(check) for check in checks],
    }


def infer_startup_status(checks: list[RuntimeCheck]) -> str:
    """Classify runtime readiness without reading private file contents."""

    statuses = {check.id: check.status for check in checks}
    if statuses.get("runtime_dir") != "available":
        return "uninitialized"
    required = ("market_plan", "trading_profile", "updates_dir", "daily_dir")
    if all(statuses.get(check_id) == "available" for check_id in required):
        return "ready"
    return "partial"


def path_check(
    check_id: str,
    label: str,
    path: Path,
    stale_after_days: int | None,
) -> RuntimeCheck:
    if not path.exists():
        return RuntimeCheck(check_id, label, "missing", str(path), "not found")

    if stale_after_days is not None and path.is_file() and is_stale(path, stale_after_days):
        return RuntimeCheck(
            check_id,
            label,
            "stale",
            str(path),
            f"modified more than {stale_after_days} day(s) ago",
        )

    return RuntimeCheck(check_id, label, "available", str(path), "exists")


def is_stale(path: Path, stale_after_days: int) -> bool:
    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds > stale_after_days * 24 * 60 * 60


def build_broker_source_health(raw_sources: list[str]) -> dict[str, object]:
    parsed = [parse_broker_source(source) for source in raw_sources]
    invalid = [
        f"{source}={status}"
        for source, status in parsed
        if source not in BROKER_SOURCES or status not in BROKER_STATUSES
    ]

    source_statuses = {
        "longbridge": "needs_review",
        "ibkr": "needs_review",
        "manual": "missing",
    }
    for source, status in parsed:
        if source in BROKER_SOURCES and status in BROKER_STATUSES:
            source_statuses[source] = status

    source_health = [
        {
            "source": BROKER_SOURCE_LABELS[source],
            "id": source,
            "status": source_statuses[source],
            "note": broker_source_note(source, source_statuses[source], raw_sources),
        }
        for source in ("longbridge", "ibkr", "manual")
    ]

    current_mode = infer_current_mode(source_statuses)
    checks = [
        RuntimeCheck(
            BROKER_SOURCE_CHECK_IDS[source],
            f"{BROKER_SOURCE_LABELS[source]} source",
            source_statuses[source],
            None,
            broker_source_note(source, source_statuses[source], raw_sources),
        )
        for source in ("longbridge", "ibkr", "manual")
    ]
    checks.append(broker_aggregate_check(source_statuses, invalid, raw_sources))
    return {
        "current_mode": current_mode,
        "source_health": source_health,
        "source_statuses": source_statuses,
        "portfolio_reconciliation": build_portfolio_reconciliation(source_statuses),
        "checks": checks,
    }


def build_source_capability_health(
    raw_capabilities: list[str],
    broker_source_statuses: dict[str, str],
) -> dict[str, object]:
    parsed = [parse_source_capability(capability) for capability in raw_capabilities]
    invalid = [
        f"{capability}={status}"
        for capability, status in parsed
        if capability not in SOURCE_CAPABILITIES or status not in BROKER_STATUSES
    ]
    statuses = {
        "longbridge_broker_skill": broker_source_statuses["longbridge"],
        "longbridge_terminal_cli": "needs_review",
        "longbridge_macrodata": "needs_review",
        "official_source_fallback": "missing",
        "ibkr_connector": broker_source_statuses["ibkr"],
        "manual_snapshot": broker_source_statuses["manual"],
    }
    for capability, status in parsed:
        if capability in SOURCE_CAPABILITIES and status in BROKER_STATUSES:
            statuses[capability] = status

    capability_order = (
        "longbridge_broker_skill",
        "longbridge_terminal_cli",
        "longbridge_macrodata",
        "official_source_fallback",
        "ibkr_connector",
        "manual_snapshot",
    )
    source_capability_health = [
        {
            "source": SOURCE_CAPABILITY_LABELS[capability],
            "id": capability,
            "status": statuses[capability],
            "note": source_capability_note(capability, statuses[capability], raw_capabilities),
        }
        for capability in capability_order
    ]
    checks = [
        RuntimeCheck(
            capability,
            SOURCE_CAPABILITY_LABELS[capability],
            statuses[capability],
            None,
            source_capability_note(capability, statuses[capability], raw_capabilities),
        )
        for capability in capability_order
    ]
    if invalid:
        checks.append(
            RuntimeCheck(
                "source_capabilities",
                "Source capabilities",
                "needs_review",
                None,
                f"invalid source capability status: {', '.join(invalid)}",
            )
        )
    return {
        "source_capability_health": source_capability_health,
        "checks": checks,
    }


def broker_source_note(source: str, status: str, raw_sources: list[str]) -> str:
    if not raw_sources:
        return "no source status provided"
    if status == "available":
        return "read-only source available for this run"
    if status == "not_installed":
        return "source not installed or connector not present"
    if status == "missing":
        return "source output missing"
    if status == "stale":
        return "source output stale"
    if status == "needs_review":
        return "source status not confirmed; authorization is not inferred"
    if status == "partial_data":
        return "source is authorized but returned only partial data; exclude incomplete rows from confirmed combined exposure"
    if status == "upstream_error":
        return "source is authorized but its upstream request failed"
    if status == "empty_positions_unverified":
        return "source returned no positions, but an empty account has not been independently verified"
    if source in {parsed_source for parsed_source, _ in map(parse_broker_source, raw_sources)}:
        return "source provided but not authorized"
    return "no source status provided"


def source_capability_note(capability: str, status: str, raw_capabilities: list[str]) -> str:
    if status == "available":
        return "read-only capability available for this run"
    if status == "not_installed":
        return "skill, connector, or capability not visible in this Codex session"
    if status == "missing":
        return "capability output missing"
    if status == "stale":
        return "capability output stale"
    if status == "needs_review":
        return "capability status not confirmed; authorization is not inferred"
    if status == "partial_data":
        return "capability returned partial data"
    if status == "upstream_error":
        return "capability is authorized but the upstream request failed"
    if status == "empty_positions_unverified":
        return "capability returned an unverified empty positions result"
    parsed_capabilities = {parsed_capability for parsed_capability, _ in map(parse_source_capability, raw_capabilities)}
    if capability in parsed_capabilities:
        return "capability provided but not authorized"
    return "no capability status provided"


def infer_current_mode(source_statuses: dict[str, str]) -> str:
    if any(
        source_statuses[source]
        in {"available", "partial_data", "empty_positions_unverified"}
        for source in LIVE_BROKER_SOURCES
    ):
        return "live read-only"
    if source_statuses["manual"] == "available":
        return "manual snapshot"
    return "dry-run"


def broker_aggregate_check(
    source_statuses: dict[str, str],
    invalid: list[str],
    raw_sources: list[str],
) -> RuntimeCheck:
    if invalid:
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            "needs_review",
            None,
            f"invalid source status: {', '.join(invalid)}",
        )

    live_statuses = {source: source_statuses[source] for source in LIVE_BROKER_SOURCES}
    if any(status == "partial_data" for status in live_statuses.values()):
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            "partial_data",
            None,
            ", ".join(f"{source}={status}" for source, status in live_statuses.items()),
        )
    if any(status == "upstream_error" for status in live_statuses.values()):
        aggregate_status = "partial_data" if "available" in live_statuses.values() else "upstream_error"
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            aggregate_status,
            None,
            ", ".join(f"{source}={status}" for source, status in live_statuses.items()),
        )
    if any(status == "empty_positions_unverified" for status in live_statuses.values()):
        aggregate_status = (
            "partial_data" if "available" in live_statuses.values() else "empty_positions_unverified"
        )
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            aggregate_status,
            None,
            ", ".join(f"{source}={status}" for source, status in live_statuses.items()),
        )
    if any(status == "needs_review" for status in live_statuses.values()):
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            "needs_review",
            None,
            ", ".join(f"{source}={status}" for source, status in live_statuses.items()),
        )

    available = [
        source
        for source in ("longbridge", "ibkr", "manual")
        if source_statuses[source] == "available"
    ]
    if available:
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            "available",
            None,
            f"available: {', '.join(available)}",
        )

    statuses = set(source_statuses.values())
    if not raw_sources:
        status = "needs_review"
    elif "stale" in statuses:
        status = "stale"
    elif "not_installed" in statuses or "missing" in statuses:
        status = "missing"
    else:
        status = "unauthorized"

    return RuntimeCheck(
        "broker_sources",
        "Broker sources",
        status,
        None,
        ", ".join(f"{source}={source_statuses[source]}" for source in ("longbridge", "ibkr", "manual")),
    )


def build_portfolio_reconciliation(source_statuses: dict[str, str]) -> dict[str, object]:
    """State whether per-source position detail can be combined as confirmed exposure."""

    confirmed_sources = [
        source for source in LIVE_BROKER_SOURCES if source_statuses[source] == "available"
    ]
    excluded_sources = [
        source for source in LIVE_BROKER_SOURCES if source_statuses[source] != "available"
    ]
    if not confirmed_sources:
        status = "unavailable"
        note = "no broker has confirmed position-detail coverage"
    elif excluded_sources:
        status = "not_confirmed"
        note = (
            "do not present NAV-only, partial, failed, unauthorized, or unverified-empty "
            "sources as merged confirmed exposure"
        )
    else:
        status = "confirmed"
        note = "all configured live broker sources have confirmed position-detail coverage"
    return {
        "status": status,
        "confirmed_sources": confirmed_sources,
        "excluded_sources": excluded_sources,
        "note": note,
    }


def parse_broker_source(value: str) -> tuple[str, str]:
    if "=" not in value:
        return value.strip().lower(), "available"
    source, status = value.split("=", 1)
    return source.strip().lower(), status.strip().lower()


def parse_source_capability(value: str) -> tuple[str, str]:
    if "=" not in value:
        return value.strip().lower().replace("-", "_"), "available"
    capability, status = value.split("=", 1)
    return capability.strip().lower().replace("-", "_"), status.strip().lower()


def render_markdown(payload: dict[str, object]) -> str:
    checks = payload["checks"]
    assert isinstance(checks, list)
    broker_source_health = payload["broker_source_health"]
    assert isinstance(broker_source_health, list)
    source_capability_health = payload["source_capability_health"]
    assert isinstance(source_capability_health, list)

    lines = [
        "# Runtime Health",
        "",
        f"- Runtime dir: `{payload['runtime_dir']}`",
        f"- Runtime origin: `{payload['runtime_origin']}`",
        f"- Startup status: `{payload['startup_status']}`",
        f"- Date: `{payload['date']}`",
        f"- Current mode: `{payload['current_mode']}`",
        "",
        "## Source Capability Health",
        "",
        "| Capability | Status | Note |",
        "| --- | --- | --- |",
    ]
    for item in source_capability_health:
        assert isinstance(item, dict)
        lines.append(f"| {item['source']} | `{item['status']}` | {item['note']} |")

    lines += [
        "",
        "## Broker Source Health",
        "",
        "| Source | Status | Note |",
        "| --- | --- | --- |",
    ]
    for item in broker_source_health:
        assert isinstance(item, dict)
        lines.append(f"| {item['source']} | `{item['status']}` | {item['note']} |")

    reconciliation = payload["portfolio_reconciliation"]
    assert isinstance(reconciliation, dict)
    lines += [
        "",
        "## Portfolio Reconciliation",
        "",
        f"- Status: `{reconciliation['status']}`",
        f"- Confirmed sources: `{', '.join(reconciliation['confirmed_sources']) or 'none'}`",
        f"- Excluded sources: `{', '.join(reconciliation['excluded_sources']) or 'none'}`",
        f"- Note: {reconciliation['note']}",
    ]

    lines += [
        "",
        "| Check | Status | Path | Note |",
        "| --- | --- | --- | --- |",
    ]
    for item in checks:
        assert isinstance(item, dict)
        path = item.get("path") or ""
        path_text = f"`{path}`" if path else ""
        lines.append(f"| {item['label']} | `{item['status']}` | {path_text} | {item['note']} |")

    lines.append("")
    lines.append("No file contents were read.")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    runtime_selection = resolve_runtime_selection(args.runtime_dir)
    payload = build_runtime_health(
        runtime_selection.path,
        args.date,
        args.broker_source,
        args.source_capability,
        args.stale_after_days,
        runtime_selection.origin,
    )

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
