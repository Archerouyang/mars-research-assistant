#!/usr/bin/env python3
"""Verify the public release surface does not expose hidden quant modules."""

from __future__ import annotations

import json
import sys

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
    "marketplace": PATHS.repo / ".agents" / "plugins" / "marketplace.json",
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
        **{
            key: FileContract(
                path=path,
                forbidden_terms=HIDDEN_QUANT_TERMS,
                forbidden_label="hidden quant module exposed",
            )
            for key, path in FILES.items()
            if key != "root_readme"
        },
        "root_readme": FileContract(
            path=FILES["root_readme"],
            required_terms=(
                "codex plugin marketplace add Archerouyang/dailytrades",
                "codex plugin add trading-research-system@dailytrades",
                "trading-research-system@dailytrades",
                "新开一个 Codex task",
            ),
            forbidden_terms=HIDDEN_QUANT_TERMS,
            forbidden_label="hidden quant module exposed",
        ),
    },
)


def main() -> int:
    failures: list[str] = []
    hidden_skill = PATHS.skills / "momentum-leaderboard" / "SKILL.md"
    if hidden_skill.exists():
        failures.append(f"hidden focused skill still exposed: {hidden_skill}")

    contract_status = run_contract(SPEC)
    if contract_status != 0:
        return contract_status

    marketplace_path = FILES["marketplace"]
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        plugins = marketplace["plugins"]
        entry = plugins[0]
    except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
        failures.append(f"invalid Dailytrades marketplace manifest: {error}")
    else:
        expected = {
            "marketplace_name": marketplace.get("name"),
            "plugin_count": len(plugins),
            "plugin_name": entry.get("name"),
            "source": entry.get("source"),
            "installation": entry.get("policy", {}).get("installation"),
            "authentication": entry.get("policy", {}).get("authentication"),
        }
        if expected != {
            "marketplace_name": "dailytrades",
            "plugin_count": 1,
            "plugin_name": "trading-research-system",
            "source": {
                "source": "local",
                "path": "./plugins/trading-research-system",
            },
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        }:
            failures.append(f"unexpected Dailytrades marketplace shape: {expected}")

    manifest_path = FILES["plugin_manifest"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        default_prompts = manifest["interface"]["defaultPrompt"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        failures.append(f"invalid plugin interface manifest: {error}")
    else:
        if not isinstance(default_prompts, list) or not 1 <= len(default_prompts) <= 3:
            failures.append("plugin defaultPrompt must contain 1..3 prompts")

    if failures:
        print("release surface contract failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
