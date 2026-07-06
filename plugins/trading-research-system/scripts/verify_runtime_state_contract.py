#!/usr/bin/env python3
"""Verify Runtime State module is the shared runtime path/write seam."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "runtime_state": ROOT / "scripts" / "runtime_state.py",
    "selftest": ROOT / "scripts" / "verify_runtime_state_selftest.py",
    "bootstrap_runtime": ROOT / "scripts" / "bootstrap_runtime.py",
    "init_daily": ROOT / "scripts" / "init_daily.py",
    "runtime_health": ROOT / "scripts" / "runtime_health.py",
    "append_review": ROOT / "scripts" / "append_review.py",
    "write_trade_review_context": ROOT / "scripts" / "write_trade_review_context.py",
    "update_trade_record": ROOT / "scripts" / "update_trade_record.py",
    "import_legacy_active_csv": ROOT / "scripts" / "import_legacy_active_csv.py",
    "kvn_leaderboard": ROOT / "scripts" / "kvn_leaderboard.py",
    "verify_plugin": REPO / "scripts" / "verify-plugin.sh",
}

REQUIRED = {
    "runtime_state": [
        "default_runtime_dir",
        "template_dir_from_script",
        "resolve_daily_root",
        "resolve_daily_dir",
        "RuntimeWriter",
        "dry_run",
        "overwrite",
        "TRADING_RESEARCH_RUNTIME_DIR",
    ],
    "selftest": [
        "runtime state selftest ok",
        "resolve_daily_dir",
        "RuntimeWriter",
        "would write",
        "kept existing",
    ],
    "bootstrap_runtime": ["from runtime_state import", "RuntimeWriter", "default_runtime_dir"],
    "init_daily": ["from runtime_state import", "RuntimeWriter", "resolve_daily_dir"],
    "runtime_health": ["from runtime_state import", "default_runtime_dir", "resolve_daily_dir"],
    "append_review": ["from runtime_state import", "default_runtime_dir", "resolve_daily_dir"],
    "write_trade_review_context": ["from runtime_state import", "default_runtime_dir", "runtime_daily_dir"],
    "update_trade_record": ["from runtime_state import", "default_runtime_dir", "runtime_daily_dir"],
    "import_legacy_active_csv": ["from runtime_state import", "default_runtime_dir", "resolve_daily_root"],
    "kvn_leaderboard": ["from runtime_state import", "default_runtime_dir"],
    "verify_plugin": ["verify_runtime_state_selftest.py", "verify_runtime_state_contract.py"],
}

FORBIDDEN = {
    "bootstrap_runtime": ["import os", "import shutil"],
    "init_daily": ["import os", "import shutil"],
    "runtime_health": ["import os"],
    "append_review": ["import os"],
    "write_trade_review_context": ["import os"],
    "update_trade_record": ["import os"],
    "import_legacy_active_csv": ["import os"],
    "kvn_leaderboard": ["import os"],
}

SPEC = ContractSpec(
    name="runtime state",
    success_message="runtime state contract ok",
    failure_header="runtime state contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED[key],
            forbidden_terms=FORBIDDEN.get(key, ()),
            forbidden_label="duplicated runtime implementation",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
