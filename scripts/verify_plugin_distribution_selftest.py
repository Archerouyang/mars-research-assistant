#!/usr/bin/env python3
"""Behavior tests for the repository plugin distribution contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFIER = REPO_ROOT / "scripts" / "verify_plugin_distribution.py"


class PluginDistributionContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = Path(self.tempdir.name)
        plugin_root = self.repo / "plugins" / "trading-research-system"
        (self.repo / ".agents" / "plugins").mkdir(parents=True)
        (plugin_root / ".codex-plugin").mkdir(parents=True)

        marketplace = {
            "name": "dailytrades",
            "interface": {"displayName": "Trading Research System"},
            "plugins": [
                {
                    "name": "trading-research-system",
                    "source": {
                        "source": "local",
                        "path": "./plugins/trading-research-system",
                    },
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        }
        manifest = {
            "name": "trading-research-system",
            "version": "0.1.1",
            "description": "Trading research workflows.",
            "author": {"name": "Archer"},
            "interface": {
                "displayName": "Trading Research System",
                "shortDescription": "Research workflows.",
                "longDescription": "Disciplined trading research workflows.",
                "developerName": "Archer",
                "category": "Productivity",
                "capabilities": ["Research"],
                "defaultPrompt": ["Review today's market plan."],
            },
        }
        (self.repo / ".agents" / "plugins" / "marketplace.json").write_text(
            json.dumps(marketplace), encoding="utf-8"
        )
        (plugin_root / ".codex-plugin" / "plugin.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (self.repo / "README.md").write_text(
            "codex plugin marketplace add Archerouyang/dailytrades --ref master\n"
            "在 /plugins 或桌面 Plugins 中安装 `trading-research-system`。\n",
            encoding="utf-8",
        )

    def run_verifier(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VERIFIER), "--repo-root", str(self.repo)],
            text=True,
            capture_output=True,
            check=False,
        )

    def read_json(self, relative_path: str) -> dict[str, Any]:
        return json.loads((self.repo / relative_path).read_text(encoding="utf-8"))

    def write_json(self, relative_path: str, value: dict[str, Any]) -> None:
        (self.repo / relative_path).write_text(json.dumps(value), encoding="utf-8")

    def assert_rejected(self, message: str) -> None:
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stderr)

    def test_accepts_repository_marketplace_contract(self) -> None:
        result = self.run_verifier()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "Plugin distribution contract ok: trading-research-system 0.1.1",
            result.stdout,
        )

    def test_rejects_missing_root_marketplace(self) -> None:
        (self.repo / ".agents" / "plugins" / "marketplace.json").unlink()

        self.assert_rejected("root marketplace missing")

    def test_rejects_source_path_drift(self) -> None:
        marketplace = self.read_json(".agents/plugins/marketplace.json")
        marketplace["plugins"][0]["source"]["path"] = "../trading-research-system"
        self.write_json(".agents/plugins/marketplace.json", marketplace)

        self.assert_rejected(
            "marketplace source.path must be ./plugins/trading-research-system"
        )

    def test_rejects_marketplace_and_manifest_name_drift(self) -> None:
        manifest = self.read_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json"
        )
        manifest["name"] = "different-plugin"
        self.write_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json", manifest
        )

        self.assert_rejected("marketplace and plugin manifest names differ")

    def test_rejects_marketplace_display_name_drift(self) -> None:
        marketplace = self.read_json(".agents/plugins/marketplace.json")
        marketplace["interface"]["displayName"] = "Different Display Name"
        self.write_json(".agents/plugins/marketplace.json", marketplace)

        self.assert_rejected("marketplace and plugin manifest display names differ")

    def test_rejects_invalid_marketplace_policy(self) -> None:
        marketplace = self.read_json(".agents/plugins/marketplace.json")
        marketplace["plugins"][0]["policy"]["installation"] = "AUTO"
        self.write_json(".agents/plugins/marketplace.json", marketplace)

        self.assert_rejected("marketplace policy.installation is invalid")

    def test_rejects_invalid_manifest_version(self) -> None:
        manifest = self.read_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json"
        )
        manifest["version"] = "release-next"
        self.write_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json", manifest
        )

        self.assert_rejected("plugin manifest version is not strict SemVer")

    def test_rejects_missing_manifest_default_prompt(self) -> None:
        manifest = self.read_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json"
        )
        del manifest["interface"]["defaultPrompt"]
        self.write_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json", manifest
        )

        self.assert_rejected("plugin manifest.interface.defaultPrompt is required")

    def test_rejects_missing_required_manifest_field(self) -> None:
        manifest = self.read_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json"
        )
        del manifest["description"]
        self.write_json(
            "plugins/trading-research-system/.codex-plugin/plugin.json", manifest
        )

        self.assert_rejected("plugin manifest.description is required")

    def test_rejects_duplicate_marketplace_version(self) -> None:
        marketplace = self.read_json(".agents/plugins/marketplace.json")
        marketplace["plugins"][0]["version"] = "0.1.0"
        self.write_json(".agents/plugins/marketplace.json", marketplace)

        self.assert_rejected("must not duplicate manifest version")

    def test_rejects_nested_marketplace(self) -> None:
        nested = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / ".agents"
            / "plugins"
            / "marketplace.json"
        )
        nested.parent.mkdir(parents=True)
        nested.write_text("{}", encoding="utf-8")

        self.assert_rejected("nested marketplace files conflict")

    def test_rejects_readme_repository_or_ref_drift(self) -> None:
        (self.repo / "README.md").write_text(
            "codex plugin marketplace add Archerouyang/dailytrades --ref dev\n"
            "在 /plugins 中安装 `trading-research-system`。\n",
            encoding="utf-8",
        )

        self.assert_rejected("README must contain exact install command")

    def test_rejects_readme_plugin_name_drift(self) -> None:
        (self.repo / "README.md").write_text(
            "codex plugin marketplace add Archerouyang/dailytrades --ref master\n"
            "在 /plugins 中安装 `different-plugin`。\n",
            encoding="utf-8",
        )

        self.assert_rejected(
            "README must name the installable plugin as `trading-research-system`"
        )


if __name__ == "__main__":
    unittest.main()
