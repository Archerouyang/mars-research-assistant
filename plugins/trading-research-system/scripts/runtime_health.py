#!/usr/bin/env python3
"""Report private runtime health without reading private file contents."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
import json
from pathlib import Path
import time

from runtime_state import default_runtime_dir, resolve_daily_dir


STATUSES = {"available", "missing", "stale", "unauthorized"}
BROKER_STATUSES = STATUSES | {"not_installed"}
BROKER_SOURCES = {"longbridge", "ibkr", "manual"}
LIVE_BROKER_SOURCES = ("longbridge", "ibkr")
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
        default=str(default_runtime_dir()),
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
    stale_after_days: int | None = None,
) -> dict[str, object]:
    runtime_dir = runtime_dir.expanduser()
    daily_dir = resolve_daily_dir(runtime_dir, trading_date)
    broker_health = build_broker_source_health(broker_sources)
    checks = [
        path_check("runtime_dir", "Runtime directory", runtime_dir, stale_after_days),
        path_check("market_plan", "Active Market Plan", runtime_dir / "market-plan.md", stale_after_days),
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
        path_check("kvn_store", "KVN store", runtime_dir / "momentum" / "kvn.sqlite", stale_after_days),
    ] + broker_health["checks"]
    return {
        "runtime_dir": str(runtime_dir),
        "date": trading_date,
        "current_mode": broker_health["current_mode"],
        "broker_source_health": broker_health["source_health"],
        "checks": [asdict(check) for check in checks],
    }


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
        "longbridge": "unauthorized",
        "ibkr": "unauthorized",
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
    if source in {parsed_source for parsed_source, _ in map(parse_broker_source, raw_sources)}:
        return "source provided but not authorized"
    return "no source status provided"


def infer_current_mode(source_statuses: dict[str, str]) -> str:
    if any(source_statuses[source] == "available" for source in LIVE_BROKER_SOURCES):
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
            "unauthorized",
            None,
            f"invalid source status: {', '.join(invalid)}",
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
        status = "unauthorized"
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


def parse_broker_source(value: str) -> tuple[str, str]:
    if "=" not in value:
        return value.strip().lower(), "available"
    source, status = value.split("=", 1)
    return source.strip().lower(), status.strip().lower()


def render_markdown(payload: dict[str, object]) -> str:
    checks = payload["checks"]
    assert isinstance(checks, list)
    broker_source_health = payload["broker_source_health"]
    assert isinstance(broker_source_health, list)

    lines = [
        "# Runtime Health",
        "",
        f"- Runtime dir: `{payload['runtime_dir']}`",
        f"- Date: `{payload['date']}`",
        f"- Current mode: `{payload['current_mode']}`",
        "",
        "## Broker Source Health",
        "",
        "| Source | Status | Note |",
        "| --- | --- | --- |",
    ]
    for item in broker_source_health:
        assert isinstance(item, dict)
        lines.append(f"| {item['source']} | `{item['status']}` | {item['note']} |")

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
    payload = build_runtime_health(
        Path(args.runtime_dir),
        args.date,
        args.broker_source,
        args.stale_after_days,
    )

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
