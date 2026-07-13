#!/usr/bin/env python3
"""Verify the public release surface and composer starter prompts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)

FILES = {
    "root_readme": PATHS.repo / "README.md",
    "plugin_readme": PATHS.root / "README.md",
    "router_skill": PATHS.skills / "trading-research" / "SKILL.md",
    "daily_skill": PATHS.skills / "daily-market-tracking" / "SKILL.md",
    "weekly_skill": PATHS.skills / "weekly-trading-plan" / "SKILL.md",
    "daily_template": PATHS.templates / "daily-market-tracking.md",
    "plugin_manifest": PATHS.root / ".codex-plugin" / "plugin.json",
    "router_fixture": PATHS.fixture_input / "router-intents.json",
    "router_contract": PATHS.scripts / "verify_router_contract.py",
}

HIDDEN_QUANT_TERMS = [
    "KVN",
    "kvn",
    "momentum-leaderboard",
    "Momentum Leaderboard",
    "kvn_snapshot_lookup",
    "导入 KVN",
    "跳过 KVN",
    "update momentum rankings",
]

SPEC = ContractSpec(
    name="release surface hidden quant modules",
    success_message="release surface contract ok",
    failure_header="release surface contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=(
                (
                    "Actual trade record, broker execution facts",
                    "use `trade-review`",
                    "Macro policy, rates/yields, research-note verification, stock screening",
                    "use `macro-equity-research`",
                )
                if key == "router_skill"
                else ()
            ),
            forbidden_terms=HIDDEN_QUANT_TERMS,
            forbidden_label="hidden quant module exposed",
        )
        for key, path in FILES.items()
    },
)


def validate_default_prompts(manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prompts = manifest.get("interface", {}).get("defaultPrompt")
    if not isinstance(prompts, list) or not prompts:
        return ["interface.defaultPrompt must be a non-empty array"]

    failures: list[str] = []
    if len(prompts) > 3:
        failures.append(f"interface.defaultPrompt must contain at most 3 entries; found {len(prompts)}")
    for index, prompt in enumerate(prompts, start=1):
        if not isinstance(prompt, str) or not prompt.strip():
            failures.append(f"interface.defaultPrompt[{index}] must be a non-empty string")
        elif len(prompt) > 128:
            failures.append(
                f"interface.defaultPrompt[{index}] must be at most 128 characters; found {len(prompt)}"
            )
    return failures


def main() -> int:
    failures: list[str] = []
    hidden_skill = PATHS.skills / "momentum-leaderboard" / "SKILL.md"
    if hidden_skill.exists():
        failures.append(f"hidden focused skill still exposed: {hidden_skill}")
    failures.extend(validate_default_prompts(FILES["plugin_manifest"]))

    contract_status = run_contract(SPEC)
    if contract_status != 0:
        return contract_status

    if failures:
        print("release surface contract failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
