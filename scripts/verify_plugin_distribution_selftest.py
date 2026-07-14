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
        (plugin_root / "assets" / "fixtures").mkdir(parents=True)
        (plugin_root / "assets" / "templates").mkdir(parents=True)

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
        (plugin_root / "README.md").write_text(
            "# Plugin\n\n"
            "## Public plugin / private user state boundary\n\n"
            "| Area | Contents | Rule |\n"
            "| --- | --- | --- |\n"
            "| Public plugin | generic capabilities and blank templates | Installation and upgrades distribute public plugin capability only. |\n"
            "| Private user state | watchlists, plans, positions, runtime, and authorization | Each user initializes a blank private runtime locally. Preference synchronization is not part of this public plugin distribution. |\n\n"
            "Public plugin: generic capabilities. Private user state: local records.\n"
            "Installation and upgrades distribute public plugin capability only. Each user initializes a blank private runtime locally. Preference synchronization is not part of this release.\n\n"
            "## Local Records\n\n"
            "Private runtime stays on the user's device.\n",
            encoding="utf-8",
        )
        (plugin_root / "assets" / "fixtures" / "README.md").write_text(
            "# Synthetic, Sanitized Fixtures\n\n"
            "All files under this directory are synthetic, sanitized test fixtures.\n"
            "Ticker symbols are examples for contract tests, not a recommendation list, default watchlist, or user profile.\n"
            "Fixtures must never be populated from private runtime, broker exports, credentials, or research history.\n\n"
            "| Fixture area | Public purpose |\n"
            "| --- | --- |\n"
            "| input | sanitized contract inputs |\n"
            "| expected | deterministic expected outputs |\n"
            "| runtime | synthetic runtime-shaped fixtures |\n",
            encoding="utf-8",
        )
        (plugin_root / "assets" / "templates" / "holdings.csv").write_text(
            "ticker,direction,weight,notes\n", encoding="utf-8"
        )
        (plugin_root / "assets" / "templates" / "README.md").write_text(
            "# Blank Public Templates\n\n"
            "These templates define empty schemas and prompts for a user-owned private runtime.\n"
            "They contain no default watchlist, portfolio, setup, trading profile, personal risk parameter, broker state, or research history.\n"
            "Each user initializes a private runtime locally.\n\n"
            "| Format | Public contract |\n"
            "| --- | --- |\n"
            "| CSV | header-only schema |\n"
            "| Markdown/TOML | blank local-runtime scaffolding |\n",
            encoding="utf-8",
        )
        (self.repo / "README.md").write_text(
            "# Dailytrades\n\n"
            "## 安装与升级\n\n"
            "### 首次安装\n\n"
            "1. **安装前提**：使用 [Codex CLI](https://developers.openai.com/codex/cli/) 或 [Codex 桌面端](https://developers.openai.com/codex/app/)。\n"
            "2. **添加 marketplace**：运行命令。\n\n"
            "   ```bash\n"
            "   codex plugin marketplace add Archerouyang/dailytrades --ref master\n"
            "   ```\n\n"
            "3. **验证 marketplace**：确认名称。\n\n"
            "   ```bash\n"
            "   codex plugin marketplace list\n"
            "   ```\n\n"
            "4. **安装 plugin**：在 `/plugins` 或桌面 Plugins 中安装 `trading-research-system`。\n"
            "5. **新开 task 并测试**：打开新 task 后运行测试 prompt。\n"
            "6. **初始化 private runtime**：在本机从空白模板初始化。\n\n"
            "   ```text\n"
            "   请说明这个 plugin 的公开能力与私有 runtime 边界。\n"
            "   ```\n\n"
            "```mermaid\n"
            "flowchart LR\n"
            "  A[Login] --> B[Add marketplace] --> C[Install] --> D[New task] --> E[Local runtime]\n"
            "```\n\n"
            "### 升级\n\n"
            "1. **确认 marketplace**：先列出名称。\n"
            "2. **刷新 marketplace**：运行升级命令。\n\n"
            "   ```bash\n"
            "   codex plugin marketplace upgrade dailytrades\n"
            "   ```\n\n"
            "3. **更新 plugin**：在 Plugins 中更新。\n"
            "4. **新开 task**：重新加载。\n\n"
            "### 故障排查\n\n"
            "| 现象 | 处理 |\n"
            "| --- | --- |\n"
            "| 看不到 marketplace | 运行 list 后重试 |\n"
            "| 旧 task 未加载 | 新开 task |\n\n"
            "## Public plugin / Private user state\n\n"
            "| 区域 | 内容 | 分发规则 |\n"
            "| --- | --- | --- |\n"
            "| Public plugin（公开能力） | 通用 skills、references、scripts、空白模板、脱敏 fixtures 和通用契约 | 安装或升级只分发公开 plugin 能力，不复制、打包、提交或同步任何 private user state。 |\n"
            "| Private user state（私有用户状态） | 用户本机状态 | 每个用户必须在本机从空白模板独立初始化 private runtime；repo 不会自动恢复个人 profile 或 Active Market Plan。未来的用户偏好同步必须是独立、私有、显式 opt-in 的能力，不属于本次 public plugin 分发。 |\n\n"
            "```mermaid\n"
            "flowchart LR\n"
            "  P[Public plugin] --> R[Research loop]\n"
            "  U[Private runtime] --> R\n"
            "```\n\n"
            "## 核心闭环\n\n"
            "Research loop.\n",
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

    def test_rejects_private_runtime_file_in_plugin_package(self) -> None:
        private_state = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "runtime"
            / "market-plan.md"
        )
        private_state.parent.mkdir(parents=True)
        private_state.write_text("# Personal market plan\n", encoding="utf-8")

        self.assert_rejected("plugin package contains non-public path: runtime")

    def test_rejects_empty_private_runtime_directory_in_plugin_package(self) -> None:
        (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "runtime"
        ).mkdir()

        self.assert_rejected("plugin package contains non-public path: runtime")

    def test_rejects_pycache_directory(self) -> None:
        plugin_root = self.repo / "plugins" / "trading-research-system"
        cache_dir = plugin_root / "scripts" / "__pycache__"
        cache_dir.mkdir(parents=True)
        (cache_dir / "bootstrap_runtime.cpython-312.pyc").write_bytes(b"cache")

        self.assert_rejected("plugin package contains generated/cache artifact")

    def test_rejects_pyc_file(self) -> None:
        pyc = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "scripts"
            / "bootstrap_runtime.pyc"
        )
        pyc.parent.mkdir(parents=True)
        pyc.write_bytes(b"cache")

        self.assert_rejected("plugin package contains generated/cache artifact")

    def test_rejects_ds_store(self) -> None:
        metadata = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "scripts"
            / ".DS_Store"
        )
        metadata.parent.mkdir(parents=True)
        metadata.write_bytes(b"metadata")

        self.assert_rejected("plugin package contains generated/cache artifact")

    def test_rejects_symlink_in_plugin_package(self) -> None:
        scripts = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "scripts"
        )
        scripts.mkdir(parents=True)
        target = scripts / "public_script.py"
        target.write_text("print('public')\n", encoding="utf-8")
        (scripts / "linked_script.py").symlink_to(target.name)

        self.assert_rejected("plugin package must not contain symlink")

    def test_rejects_private_runtime_nested_under_scripts(self) -> None:
        private_snapshot = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "scripts"
            / "private-runtime"
            / "portfolio_snapshot.csv"
        )
        private_snapshot.parent.mkdir(parents=True)
        private_snapshot.write_text("ticker,quantity\nPRIVATE,10\n", encoding="utf-8")

        self.assert_rejected("plugin scripts allow only top-level Python files")

    def test_rejects_non_markdown_private_data_under_skills(self) -> None:
        private_data = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "skills"
            / "trading-research"
            / "references"
            / "portfolio_snapshot.csv"
        )
        private_data.parent.mkdir(parents=True)
        private_data.write_text("ticker,quantity\nPRIVATE,10\n", encoding="utf-8")

        self.assert_rejected("plugin skills allow only SKILL.md and Markdown references")

    def test_rejects_unknown_asset_directory(self) -> None:
        generated = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "assets"
            / "templates"
            / "generated"
            / "output.json"
        )
        generated.parent.mkdir(parents=True)
        generated.write_text("{}", encoding="utf-8")

        self.assert_rejected("plugin assets path is not in the public allowlist")

    def test_rejects_unknown_asset_extension(self) -> None:
        private_database = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "assets"
            / "templates"
            / "private-runtime.sqlite"
        )
        private_database.write_bytes(b"private")

        self.assert_rejected("plugin assets path is not in the public allowlist")

    def test_rejects_unlabelled_fixture_package(self) -> None:
        (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "assets"
            / "fixtures"
            / "README.md"
        ).unlink()

        self.assert_rejected("fixture disclosure missing")

    def test_rejects_prefilled_private_state_template(self) -> None:
        holdings = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "assets"
            / "templates"
            / "holdings.csv"
        )
        holdings.write_text(
            holdings.read_text(encoding="utf-8")
            + "NVDA,long,8%,personal default\n",
            encoding="utf-8",
        )

        self.assert_rejected("public CSV template must be header-only: holdings.csv")

    def test_rejects_templates_without_blank_runtime_disclosure(self) -> None:
        (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "assets"
            / "templates"
            / "README.md"
        ).unlink()

        self.assert_rejected("blank template disclosure missing")

    def test_rejects_readme_repository_or_ref_drift(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "codex plugin marketplace add Archerouyang/dailytrades --ref master",
                "codex plugin marketplace add Archerouyang/dailytrades --ref dev",
            ),
            encoding="utf-8",
        )

        self.assert_rejected("README first install missing fenced bash command")

    def test_accepts_semantically_rewritten_readme_body(self) -> None:
        readme = self.repo / "README.md"
        rewritten = readme.read_text(encoding="utf-8")
        rewritten = rewritten.replace(
            "安装或升级只分发公开 plugin 能力，不复制、打包、提交或同步任何 private user state。",
            "发布流程只取得仓库里的公共能力；用户自己的状态始终留在本机。",
        )
        rewritten = rewritten.replace(
            "每个用户必须在本机从空白模板独立初始化 private runtime；repo 不会自动恢复个人 profile 或 Active Market Plan。",
            "private runtime 由使用者在当前设备创建，初始内容为空。",
        )
        rewritten = rewritten.replace(
            "未来的用户偏好同步必须是独立、私有、显式 opt-in 的能力，不属于本次 public plugin 分发。",
            "若未来提供偏好迁移，它会是另一个私有且主动选择的产品。",
        )
        readme.write_text(rewritten, encoding="utf-8")

        result = self.run_verifier()

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_readme_plugin_name_drift(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "`trading-research-system`", "`different-plugin`"
            ),
            encoding="utf-8",
        )

        self.assert_rejected(
            "README first install must name plugin `trading-research-system`"
        )

    def test_rejects_readme_claim_that_account_syncs_user_state(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8")
            + "同账号登录会自动同步用户状态、交易偏好和 runtime。\n",
            encoding="utf-8",
        )

        self.assert_rejected("README must not claim that account login syncs user state")

    def test_rejects_plugin_readme_without_private_state_boundary(self) -> None:
        plugin_readme = (
            self.repo / "plugins" / "trading-research-system" / "README.md"
        )
        plugin_readme.write_text(
            plugin_readme.read_text(encoding="utf-8").replace(
                "| Private user state |", "| User data |"
            ),
            encoding="utf-8",
        )

        self.assert_rejected(
            "plugin README public/private boundary missing required table row"
        )

    def test_accepts_rewritten_package_documentation_prose(self) -> None:
        plugin_root = self.repo / "plugins" / "trading-research-system"
        replacements = {
            plugin_root / "README.md": {
                "Installation and upgrades distribute public plugin capability only.":
                    "The package delivers reusable plugin behavior.",
                "Each user initializes a blank private runtime locally.":
                    "Local records begin from empty scaffolding on each device.",
            },
            plugin_root / "assets" / "fixtures" / "README.md": {
                "All files under this directory are synthetic, sanitized test fixtures.":
                    "This tree contains invented public contract examples.",
                "Fixtures must never be populated from private runtime, broker exports, credentials, or research history.":
                    "Only purpose-built public test material belongs here.",
            },
            plugin_root / "assets" / "templates" / "README.md": {
                "These templates define empty schemas and prompts for a user-owned private runtime.":
                    "These files scaffold a new local workspace.",
                "Each user initializes a private runtime locally.":
                    "Initialization happens on the current device.",
            },
        }
        for path, path_replacements in replacements.items():
            text = path.read_text(encoding="utf-8")
            for old, new in path_replacements.items():
                text = text.replace(old, new)
            path.write_text(text, encoding="utf-8")

        result = self.run_verifier()

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_missing_readme_install_section(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "## 安装与升级", "## Getting Started"
            ),
            encoding="utf-8",
        )

        self.assert_rejected(
            "README installation section must be the first level-2 section"
        )

    def test_rejects_missing_readme_install_step(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "6. **初始化 private runtime**：在本机从空白模板初始化。\n", ""
            ),
            encoding="utf-8",
        )

        self.assert_rejected(
            "README first-install ordered steps are incomplete or out of order"
        )

    def test_rejects_malformed_mermaid_flow(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "flowchart LR", "not-a-mermaid-flow", 1
            ),
            encoding="utf-8",
        )

        self.assert_rejected("README installation Mermaid must start with flowchart")


if __name__ == "__main__":
    unittest.main()
