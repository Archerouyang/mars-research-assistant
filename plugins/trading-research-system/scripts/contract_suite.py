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
        return cls(root=root, repo=root.parents[1])

    @property
    def scripts(self) -> Path:
        return self.root / "scripts"

    @property
    def skills(self) -> Path:
        return self.root / "skills"

    @property
    def references(self) -> Path:
        return self.skills / "trading-research" / "references"

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


@dataclass(frozen=True)
class ContractScript:
    """One executable contract or selftest script in a suite."""

    name: str
    path: Path


CORE_SUITE: tuple[tuple[str, str], ...] = (
    ("source-routing", "verify_source_routing_contract.py"),
    ("daily-ops-orchestrator", "verify_daily_ops_orchestrator_contract.py"),
    ("daily-market-tracking", "verify_daily_market_tracking_contract.py"),
    ("macro-industry-monitor", "verify_macro_industry_research_monitor_contract.py"),
    ("trade-plan-preparation", "verify_trade_plan_preparation_contract.py"),
    ("automation-setup", "verify_automation_setup_contract.py"),
    ("router", "verify_router_contract.py"),
    ("contract-suite-selftest", "verify_contract_suite_selftest.py"),
    ("contract-suite-contract", "verify_contract_suite_contract.py"),
    ("runtime-state-selftest", "verify_runtime_state_selftest.py"),
    ("runtime-state-contract", "verify_runtime_state_contract.py"),
    ("runtime-bootstrap-selftest", "verify_runtime_bootstrap_selftest.py"),
    ("runtime-bootstrap-contract", "verify_runtime_bootstrap_contract.py"),
    ("broker-snapshot-ingest-selftest", "verify_broker_snapshot_ingest_selftest.py"),
    ("broker-snapshot-ingest-contract", "verify_broker_snapshot_ingest_contract.py"),
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
