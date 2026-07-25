#!/usr/bin/env python3
"""Focused temporary-runtime checks for Private Runtime preparation and health."""

from __future__ import annotations

from pathlib import Path
import tempfile

from private_runtime import PreparationScope, prepare_private_runtime
from runtime_health import build_runtime_health


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "assets" / "templates"
TRADING_DATE = "2026-07-20"


def checks_by_id(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    checks = payload["checks"]
    assert isinstance(checks, list)
    return {
        str(check["id"]): check
        for check in checks
        if isinstance(check, dict) and "id" in check
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mars-research-assistant-private-runtime-") as temp_dir:
        temp_root = Path(temp_dir)
        dry_run_runtime = temp_root / "dry-run-runtime"
        prepare_private_runtime(
            dry_run_runtime,
            TRADING_DATE,
            TEMPLATE_DIR,
            scope=PreparationScope.DAILY,
            dry_run=True,
        )
        assert not dry_run_runtime.exists()

        custom_daily_root = temp_root / "custom-daily"
        prepare_private_runtime(
            temp_root / "unused-runtime",
            TRADING_DATE,
            TEMPLATE_DIR,
            scope=PreparationScope.DAILY_ONLY,
            daily_root=custom_daily_root,
        )
        assert (custom_daily_root / TRADING_DATE / "trade-plans.csv").is_file()
        assert not (temp_root / "unused-runtime").exists()

        runtime_dir = temp_root / "runtime"
        legacy_store = runtime_dir / "alpha" / "leaderboard.sqlite"
        legacy_store.parent.mkdir(parents=True)
        legacy_store.write_text("private data must survive\n", encoding="utf-8")

        prepare_private_runtime(
            runtime_dir,
            TRADING_DATE,
            TEMPLATE_DIR,
            scope=PreparationScope.DAILY,
        )

        daily_dir = runtime_dir / "daily" / TRADING_DATE
        trade_plans = daily_dir / "trade-plans.csv"
        research_notes = daily_dir / "research-notes.md"
        assert trade_plans.is_file()
        assert research_notes.is_file()

        sentinel = trade_plans.read_text(encoding="utf-8") + "# preserved\n"
        trade_plans.write_text(sentinel, encoding="utf-8")
        prepare_private_runtime(
            runtime_dir,
            TRADING_DATE,
            TEMPLATE_DIR,
            scope=PreparationScope.DAILY,
        )
        assert trade_plans.read_text(encoding="utf-8") == sentinel

        partial_health = build_runtime_health(runtime_dir, TRADING_DATE, [])
        assert partial_health["startup_status"] == "partial"
        assert partial_health["provider_configuration"] == {
            "status": "absent",
            "reason": "no_broker_choice_config_required",
        }
        partial_checks = checks_by_id(partial_health)
        assert "alpha_leaderboard_store" not in partial_checks
        assert "analysis_store" not in partial_checks
        assert not any(
            str(check.get("path", "")).endswith((".sqlite", ".sqlite3", ".db"))
            for check in partial_checks.values()
        )

        prepare_private_runtime(
            runtime_dir,
            TRADING_DATE,
            TEMPLATE_DIR,
            scope=PreparationScope.BOOTSTRAP,
        )
        ready_health = build_runtime_health(runtime_dir, TRADING_DATE, [])
        assert ready_health["startup_status"] == "ready"
        assert checks_by_id(ready_health)["trade_plans"]["status"] == "available"
        assert trade_plans.read_text(encoding="utf-8") == sentinel
        assert legacy_store.read_text(encoding="utf-8") == "private data must survive\n"

        (runtime_dir / "mars-runtime-config.json").write_text(
            '{"default_broker":"longbridge"}\n',
            encoding="utf-8",
        )
        incompatible = build_runtime_health(runtime_dir, TRADING_DATE, [])
        assert incompatible["provider_configuration"] == {
            "status": "version_incompatible",
            "reason": "legacy_broker_choice_config_retired",
        }

    print("private runtime selftest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
