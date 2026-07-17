#!/usr/bin/env python3
"""Contract Suite discovery and runner for Trading Research System checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Mapping


@dataclass(frozen=True)
class PluginPaths:
    """Common repo/plugin paths used by contract checks."""

    root: Path
    repo: Path

    @classmethod
    def from_script(cls, script_path: str | Path) -> "PluginPaths":
        root = Path(script_path).resolve().parents[1]
        repo_candidates = (
            root.parents[1],
            Path.cwd(),
        )
        for candidate in repo_candidates:
            if is_repo_checkout(candidate):
                return cls(root=root, repo=candidate.resolve())
        return cls(root=root, repo=root.parents[1])

    @property
    def scripts(self) -> Path:
        return self.root / "scripts"

    @property
    def skills(self) -> Path:
        return self.root / "skills"

    @property
    def references(self) -> Path:
        return self.skills / "trading-research-system" / "references"

    @property
    def templates(self) -> Path:
        return self.root / "assets" / "templates"

    @property
    def fixtures(self) -> Path:
        return self.root / "assets" / "fixtures"

    @property
    def fixture_input(self) -> Path:
        return self.fixtures / "input"

    @property
    def fixture_expected(self) -> Path:
        return self.fixtures / "expected"


def is_repo_checkout(path: Path) -> bool:
    """Return true when path looks like the public dailytrades repo checkout."""

    return (
        (path / "docs").is_dir()
        and (path / "plugins" / "trading-research-system").is_dir()
        and (path / "README.md").is_file()
    )


@dataclass(frozen=True)
class ContractScript:
    """One executable contract or selftest script in a suite."""

    name: str
    path: Path


CORE_SUITE: tuple[tuple[str, str], ...] = (
    ("source-routing", "verify_source_routing_contract.py"),
    ("alpha-lab", "verify_alpha_lab_contract.py"),
    ("alpha-leaderboard-adapter-selftest", "verify_alpha_leaderboard_adapter_selftest.py"),
    ("alpha-leaderboard-adapter-contract", "verify_alpha_leaderboard_adapter_contract.py"),
    ("analysis-delta-adapter-selftest", "verify_analysis_delta_adapter_selftest.py"),
    ("analysis-delta-adapter-contract", "verify_analysis_delta_adapter_contract.py"),
    ("macro-data-source", "verify_macro_data_source_contract.py"),
    ("longbridge-skill-adapter", "verify_longbridge_skill_adapter_contract.py"),
    ("daily-ops-orchestrator", "verify_daily_ops_orchestrator_contract.py"),
    ("daily-market-tracking", "verify_daily_market_tracking_contract.py"),
    ("release-surface", "verify_release_surface_contract.py"),
    ("one-zero-acceptance", "verify_1_0_acceptance_contract.py"),
    ("price-action-rollforward-selftest", "verify_price_action_rollforward_selftest.py"),
    ("price-action-rollforward", "verify_price_action_rollforward_contract.py"),
    ("longbridge-ohlcv-adapter-selftest", "verify_longbridge_ohlcv_adapter_selftest.py"),
    ("longbridge-ohlcv-adapter-contract", "verify_longbridge_ohlcv_adapter_contract.py"),
    ("macro-industry-monitor", "verify_macro_industry_research_monitor_contract.py"),
    ("trade-plan-preparation", "verify_trade_plan_preparation_contract.py"),
    ("automation-setup", "verify_automation_setup_contract.py"),
    ("alpha-automations", "verify_alpha_automation_contract.py"),
    ("alpha-notification-adapter-selftest", "verify_alpha_notification_adapter_selftest.py"),
    ("router", "verify_router_contract.py"),
    ("contract-suite-selftest", "verify_contract_suite_selftest.py"),
    ("contract-suite-contract", "verify_contract_suite_contract.py"),
    ("runtime-health-selftest", "verify_runtime_health_selftest.py"),
    ("runtime-health-contract", "verify_runtime_health_contract.py"),
    ("runtime-state-selftest", "verify_runtime_state_selftest.py"),
    ("runtime-state-contract", "verify_runtime_state_contract.py"),
    ("runtime-bootstrap-selftest", "verify_runtime_bootstrap_selftest.py"),
    ("runtime-bootstrap-contract", "verify_runtime_bootstrap_contract.py"),
    ("daily-runtime-package-selftest", "verify_daily_runtime_package_selftest.py"),
    ("daily-runtime-package-contract", "verify_daily_runtime_package_contract.py"),
    ("setup-row-preparation-selftest", "verify_prepare_setup_rows_selftest.py"),
    ("setup-row-preparation-contract", "verify_prepare_setup_rows_contract.py"),
    ("visual-artifact-selftest", "verify_visual_artifact_selftest.py"),
    ("visual-artifact-contract", "verify_visual_artifact_contract.py"),
    ("artifact-packet-selftest", "verify_artifact_packet_selftest.py"),
    ("instrument-research-board-selftest", "verify_instrument_research_board_selftest.py"),
    ("macro-regime-board-selftest", "verify_macro_regime_board_selftest.py"),
    ("visual-trigger", "verify_visual_trigger_contract.py"),
    ("position-daily-report-selftest", "verify_position_daily_report_selftest.py"),
    ("position-daily-report-contract", "verify_position_daily_report_contract.py"),
    ("broker-snapshot-ingest-selftest", "verify_broker_snapshot_ingest_selftest.py"),
    ("broker-snapshot-ingest-contract", "verify_broker_snapshot_ingest_contract.py"),
    ("ibkr-connector-adapter-selftest", "verify_ibkr_connector_adapter_selftest.py"),
    ("ibkr-connector-adapter-contract", "verify_ibkr_connector_adapter_contract.py"),
    ("longbridge-cli-adapter-selftest", "verify_longbridge_cli_adapter_selftest.py"),
    ("longbridge-cli-adapter-contract", "verify_longbridge_cli_adapter_contract.py"),
    ("portfolio-snapshot-repair-selftest", "verify_repair_portfolio_snapshot_selftest.py"),
    ("portfolio-snapshot-repair-contract", "verify_repair_portfolio_snapshot_contract.py"),
    ("longbridge-macrodata-adapter-selftest", "verify_longbridge_macrodata_adapter_selftest.py"),
    ("longbridge-macrodata-adapter-contract", "verify_longbridge_macrodata_adapter_contract.py"),
    ("prepare-macro-panel-selftest", "verify_prepare_macro_panel_selftest.py"),
    ("prepare-macro-panel-contract", "verify_prepare_macro_panel_contract.py"),
)

SUITES: Mapping[str, tuple[tuple[str, str], ...]] = {
    "core": CORE_SUITE,
}


def suite_scripts(suite_name: str = "core", paths: PluginPaths | None = None) -> tuple[ContractScript, ...]:
    """Return the registered scripts for a contract suite."""

    if suite_name not in SUITES:
        known = ", ".join(sorted(SUITES))
        raise ValueError(f"unknown contract suite {suite_name!r}; known suites: {known}")

    resolved_paths = paths or PluginPaths.from_script(__file__)
    return tuple(
        ContractScript(name=name, path=resolved_paths.scripts / filename)
        for name, filename in SUITES[suite_name]
    )


def run_scripts(
    scripts: Iterable[ContractScript],
    python: str | Path | None = None,
    *,
    emit_output: bool = True,
) -> int:
    """Run scripts in order and return the first non-zero exit code."""

    python_bin = str(python or sys.executable)
    for script in scripts:
        if not script.path.is_file():
            print(f"contract suite missing {script.name}: {script.path}", file=sys.stderr)
            return 1

        result = subprocess.run(
            [python_bin, str(script.path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if emit_output and result.stdout:
            print(result.stdout, end="")
        if emit_output and result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        if result.returncode != 0:
            if emit_output:
                print(f"contract suite failed at {script.name}", file=sys.stderr)
            return result.returncode

    return 0


def run_contract_suite(suite_name: str = "core", python: str | Path | None = None) -> int:
    """Run a registered contract suite."""

    return run_scripts(suite_scripts(suite_name), python=python)
