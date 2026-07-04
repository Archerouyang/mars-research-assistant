#!/usr/bin/env python3
"""Report private runtime health without reading private file contents."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
import json
import os
from pathlib import Path
import time


STATUSES = {"available", "missing", "stale", "unauthorized"}
BROKER_SOURCES = {"longbridge", "ibkr", "manual"}


@dataclass(frozen=True)
class RuntimeCheck:
    id: str
    label: str
    status: str
    path: str | None = None
    note: str = ""


def default_runtime_dir() -> Path:
    configured = os.environ.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Documents" / "dailytrades-runtime"


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
    daily_dir = runtime_dir / "daily" / trading_date
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
        broker_check(broker_sources),
    ]
    return {
        "runtime_dir": str(runtime_dir),
        "date": trading_date,
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


def broker_check(raw_sources: list[str]) -> RuntimeCheck:
    if not raw_sources:
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            "unauthorized",
            None,
            "no broker source status provided",
        )

    parsed = [parse_broker_source(source) for source in raw_sources]
    invalid = [source for source, status in parsed if source not in BROKER_SOURCES or status not in STATUSES]
    if invalid:
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            "unauthorized",
            None,
            f"invalid source status: {', '.join(raw_sources)}",
        )

    available = [source for source, status in parsed if status == "available"]
    if available:
        return RuntimeCheck(
            "broker_sources",
            "Broker sources",
            "available",
            None,
            f"available: {', '.join(available)}",
        )

    statuses = {status for _, status in parsed}
    if "stale" in statuses:
        status = "stale"
    elif "missing" in statuses:
        status = "missing"
    else:
        status = "unauthorized"

    return RuntimeCheck(
        "broker_sources",
        "Broker sources",
        status,
        None,
        ", ".join(f"{source}={source_status}" for source, source_status in parsed),
    )


def parse_broker_source(value: str) -> tuple[str, str]:
    if "=" not in value:
        return value.strip().lower(), "available"
    source, status = value.split("=", 1)
    return source.strip().lower(), status.strip().lower()


def render_markdown(payload: dict[str, object]) -> str:
    checks = payload["checks"]
    assert isinstance(checks, list)

    lines = [
        "# Runtime Health",
        "",
        f"- Runtime dir: `{payload['runtime_dir']}`",
        f"- Date: `{payload['date']}`",
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
