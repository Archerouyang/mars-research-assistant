#!/usr/bin/env python3
"""Canonical Private Runtime layout, preparation, health, and write policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil
from typing import Mapping

from record_schemas import CSV_SCHEMAS
from runtime_state import resolve_daily_dir


__all__ = (
    "PreparationScope",
    "prepare_private_runtime",
    "runtime_health_expectations",
    "startup_required_check_ids",
)


ROOT_DIRECTORIES = ("daily", "updates", "momentum", "charts", "reports")
ROOT_TEMPLATE_TARGETS: Mapping[str, str] = {
    "config.toml": "config.toml",
    "market-plan.md": "market-plan.md",
    "trading-profile.md": "trading-profile.md",
    "ops-state.md": "ops-state.md",
}
DAILY_TEMPLATE_TARGETS: Mapping[str, str] = {
    "watchlist.csv": "watchlist.csv",
    "trade-plans.csv": "trade-plans.csv",
    "intraday-watchlist.csv": "intraday-watchlist.csv",
    "trades.csv": "trades.csv",
    "holdings.csv": "portfolio.csv",
    "portfolio_snapshot.csv": "portfolio_snapshot.csv",
    "broker_executions.csv": "broker_executions.csv",
    "broker_orders.csv": "broker_orders.csv",
    "research-note-log.csv": "research-note-log.csv",
    "research-report-log.csv": "research-report-log.csv",
    "daily-macro-checklist.md": "daily-macro-checklist.md",
    "daily-market-tracking.md": "daily-market-tracking.md",
    "reviews.md": "reviews.md",
}
STARTUP_REQUIRED_CHECK_IDS = (
    "market_plan",
    "trading_profile",
    "updates_dir",
    "daily_dir",
)

RESEARCH_NOTES = """# Research Notes

## Information Collection

-

## Information Processing

-

## Trade Ideas

-

## Verification

-
"""


class PreparationScope(str, Enum):
    """Supported preparation plans exposed through CLI adapters."""

    BOOTSTRAP = "bootstrap"
    DAILY = "daily"
    DAILY_ONLY = "daily_only"


class OperationKind(str, Enum):
    ENSURE_DIR = "ensure_dir"
    COPY_TEMPLATE = "copy_template"
    WRITE_TEXT = "write_text"


@dataclass(frozen=True)
class PreparationOperation:
    kind: OperationKind
    target: Path
    source: Path | None = None
    text: str | None = None


@dataclass(frozen=True)
class RuntimePreparationPlan:
    operations: tuple[PreparationOperation, ...]
    prerequisites: tuple[tuple[Path, str], ...] = ()


@dataclass(frozen=True)
class RuntimeHealthExpectation:
    id: str
    label: str
    path: Path


@dataclass(frozen=True)
class RuntimeWriter:
    """Apply controlled writes without deleting or overwriting by default."""

    dry_run: bool = False
    overwrite: bool = False

    def ensure_dir(self, path: str | Path) -> str:
        target = Path(path).expanduser()
        if self.dry_run:
            if target.exists():
                return f"would keep existing dir {target}"
            return f"would create dir {target}"
        target.mkdir(parents=True, exist_ok=True)
        return f"created dir {target}"

    def copy_template(self, source: str | Path, target: str | Path) -> str:
        source_path = Path(source).expanduser()
        target_path = Path(target).expanduser()
        if not source_path.is_file():
            raise SystemExit(f"missing template: {source_path}")
        if target_path.exists() and not self.overwrite:
            return f"kept existing {target_path}"
        if self.dry_run:
            action = "would overwrite" if target_path.exists() else "would write"
            return f"{action} {target_path}"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
        return f"wrote {target_path}"

    def write_text(self, path: str | Path, text: str) -> str:
        target = Path(path).expanduser()
        if target.exists() and not self.overwrite:
            return f"kept existing {target}"
        if self.dry_run:
            action = "would overwrite" if target.exists() else "would write"
            return f"{action} {target}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return f"wrote {target}"


def update_note_text(trading_date: str) -> str:
    return f"""# Daily Update {trading_date}

## Changes

-

## Decisions Needed

-

## Next Checks

-
"""


def csv_header_text(schema_name: str) -> str:
    return ",".join(CSV_SCHEMAS[schema_name]) + "\n"


def daily_package_operations(
    daily_dir: Path,
    template_dir: Path,
    *,
    generate_csv_headers: bool = False,
    include_research_notes: bool = True,
) -> tuple[PreparationOperation, ...]:
    operations = [PreparationOperation(OperationKind.ENSURE_DIR, daily_dir)]
    for template_name, target_name in DAILY_TEMPLATE_TARGETS.items():
        target = daily_dir / target_name
        if template_name.endswith(".csv") and generate_csv_headers:
            if template_name not in CSV_SCHEMAS:
                raise SystemExit(f"missing schema for daily template: {template_name}")
            operations.append(
                PreparationOperation(
                    OperationKind.WRITE_TEXT,
                    target,
                    text=csv_header_text(template_name),
                )
            )
        else:
            operations.append(
                PreparationOperation(
                    OperationKind.COPY_TEMPLATE,
                    target,
                    source=template_dir / template_name,
                )
            )
    if include_research_notes:
        operations.append(
            PreparationOperation(
                OperationKind.WRITE_TEXT,
                daily_dir / "research-notes.md",
                text=RESEARCH_NOTES,
            )
        )
    return tuple(operations)


def build_preparation_plan(
    runtime_dir: str | Path,
    trading_date: str,
    template_dir: str | Path,
    *,
    scope: PreparationScope,
    include_daily: bool = True,
    daily_root: str | Path | None = None,
) -> RuntimePreparationPlan:
    runtime_path = Path(runtime_dir).expanduser()
    templates = Path(template_dir).expanduser()
    daily_dir = resolve_daily_dir(runtime_path, trading_date, root=daily_root)

    if scope is PreparationScope.BOOTSTRAP:
        operations = [
            PreparationOperation(OperationKind.ENSURE_DIR, runtime_path / directory)
            for directory in ROOT_DIRECTORIES
        ]
        operations.extend(
            PreparationOperation(
                OperationKind.COPY_TEMPLATE,
                runtime_path / target_name,
                source=templates / template_name,
            )
            for template_name, target_name in ROOT_TEMPLATE_TARGETS.items()
        )
        operations.append(
            PreparationOperation(
                OperationKind.WRITE_TEXT,
                runtime_path / "updates" / f"{trading_date}.md",
                text=update_note_text(trading_date),
            )
        )
        if include_daily:
            operations.extend(
                daily_package_operations(
                    daily_dir,
                    templates,
                    include_research_notes=False,
                )
            )
        return RuntimePreparationPlan(tuple(operations))

    if scope is PreparationScope.DAILY:
        operations = [
            PreparationOperation(OperationKind.ENSURE_DIR, runtime_path),
            PreparationOperation(OperationKind.ENSURE_DIR, runtime_path / "updates"),
            PreparationOperation(OperationKind.ENSURE_DIR, runtime_path / "daily"),
            PreparationOperation(
                OperationKind.COPY_TEMPLATE,
                runtime_path / "ops-state.md",
                source=templates / "ops-state.md",
            ),
            PreparationOperation(
                OperationKind.WRITE_TEXT,
                runtime_path / "updates" / f"{trading_date}.md",
                text=update_note_text(trading_date),
            ),
        ]
        operations.extend(
            daily_package_operations(
                daily_dir,
                templates,
                generate_csv_headers=True,
            )
        )
        return RuntimePreparationPlan(
            tuple(operations),
            prerequisites=(
                (runtime_path / "market-plan.md", "Active Market Plan"),
                (runtime_path / "trading-profile.md", "Trading Profile"),
            ),
        )

    if scope is PreparationScope.DAILY_ONLY:
        return RuntimePreparationPlan(daily_package_operations(daily_dir, templates))

    raise ValueError(f"unsupported preparation scope: {scope}")


def apply_preparation_plan(
    plan: RuntimePreparationPlan,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[str]:
    writer = RuntimeWriter(dry_run=dry_run, overwrite=overwrite)
    messages: list[str] = []
    for operation in plan.operations:
        if operation.kind is OperationKind.ENSURE_DIR:
            messages.append(writer.ensure_dir(operation.target))
        elif operation.kind is OperationKind.COPY_TEMPLATE:
            assert operation.source is not None
            messages.append(writer.copy_template(operation.source, operation.target))
        elif operation.kind is OperationKind.WRITE_TEXT:
            assert operation.text is not None
            messages.append(writer.write_text(operation.target, operation.text))
        else:
            raise ValueError(f"unsupported preparation operation: {operation.kind}")
    messages.extend(prerequisite_status(path, label) for path, label in plan.prerequisites)
    return messages


def prepare_private_runtime(
    runtime_dir: str | Path,
    trading_date: str,
    template_dir: str | Path,
    *,
    scope: PreparationScope,
    dry_run: bool = False,
    overwrite: bool = False,
    include_daily: bool = True,
    daily_root: str | Path | None = None,
) -> list[str]:
    plan = build_preparation_plan(
        runtime_dir,
        trading_date,
        template_dir,
        scope=scope,
        include_daily=include_daily,
        daily_root=daily_root,
    )
    return apply_preparation_plan(plan, dry_run=dry_run, overwrite=overwrite)


def prerequisite_status(path: Path, label: str) -> str:
    if path.exists():
        return f"{label}: available at {path}"
    return f"{label}: missing; run bootstrap or complete the plan before full Daily Ops analysis"


def runtime_health_expectations(
    runtime_dir: str | Path,
    trading_date: str,
) -> tuple[RuntimeHealthExpectation, ...]:
    runtime_path = Path(runtime_dir).expanduser()
    daily_dir = resolve_daily_dir(runtime_path, trading_date)
    return (
        RuntimeHealthExpectation("runtime_dir", "Runtime directory", runtime_path),
        RuntimeHealthExpectation(
            "market_plan",
            "Active Market Plan",
            runtime_path / ROOT_TEMPLATE_TARGETS["market-plan.md"],
        ),
        RuntimeHealthExpectation(
            "ops_state",
            "Daily Ops State",
            runtime_path / ROOT_TEMPLATE_TARGETS["ops-state.md"],
        ),
        RuntimeHealthExpectation(
            "trading_profile",
            "Trading Profile",
            runtime_path / ROOT_TEMPLATE_TARGETS["trading-profile.md"],
        ),
        RuntimeHealthExpectation(
            "updates_dir",
            "Updates directory",
            runtime_path / "updates",
        ),
        RuntimeHealthExpectation(
            "daily_dir",
            "Daily directory",
            daily_dir,
        ),
        RuntimeHealthExpectation(
            "trade_plans",
            "Trade plans",
            daily_dir / DAILY_TEMPLATE_TARGETS["trade-plans.csv"],
        ),
        RuntimeHealthExpectation(
            "intraday_watchlist",
            "Intraday watchlist",
            daily_dir / DAILY_TEMPLATE_TARGETS["intraday-watchlist.csv"],
        ),
        RuntimeHealthExpectation("macro_panel", "Macro panel", daily_dir / "macro-panel.json"),
        RuntimeHealthExpectation(
            "portfolio_snapshot",
            "Portfolio snapshot",
            daily_dir / DAILY_TEMPLATE_TARGETS["portfolio_snapshot.csv"],
        ),
    )


def startup_required_check_ids() -> tuple[str, ...]:
    return STARTUP_REQUIRED_CHECK_IDS
