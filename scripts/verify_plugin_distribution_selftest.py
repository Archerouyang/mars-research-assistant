#!/usr/bin/env python3
"""Behavior tests for command-first distribution validation."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VERIFIER = REPO / "scripts" / "verify_plugin_distribution.py"


class DistributionSelftest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        for relative in (
            "skills",
            "plugins",
            ".agents",
            ".claude-plugin",
        ):
            shutil.copytree(REPO / relative, self.repo / relative)
        (self.repo / "scripts").mkdir()
        shutil.copy2(
            REPO / "scripts" / "smoke-portable-skill-install.sh",
            self.repo / "scripts" / "smoke-portable-skill-install.sh",
        )
        for relative in ("README.md", "README.zh-CN.md", "LICENSE"):
            shutil.copy2(REPO / relative, self.repo / relative)

    def run_verifier(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VERIFIER), "--repo-root", str(self.repo)],
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_rejected(self, term: str) -> None:
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(term, result.stderr)

    def test_accepts_one_self_contained_skill_and_wrappers(self) -> None:
        result = self.run_verifier()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("trading-research-system 0.1.1", result.stdout)

    def test_rejects_second_public_skill(self) -> None:
        second = self.repo / "skills" / "partial-workflow"
        second.mkdir()
        (second / "SKILL.md").write_text(
            "---\nname: partial-workflow\ndescription: partial\n---\n",
            encoding="utf-8",
        )
        self.assert_rejected("root skills discovery must expose exactly")

    def test_rejects_native_wrapper_drift(self) -> None:
        target = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "skills"
            / "trading-research-system"
            / "SKILL.md"
        )
        target.write_text(target.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
        self.assert_rejected("native wrapper drift")

    def test_rejects_noncanonical_wrapper_behavior_script(self) -> None:
        target = (
            self.repo
            / "plugins"
            / "trading-research-system"
            / "scripts"
            / "rogue_runtime.py"
        )
        target.write_text("print('second behavior source')\n", encoding="utf-8")
        self.assert_rejected("non-canonical behavior scripts")

    def test_rejects_private_absolute_path(self) -> None:
        target = self.repo / "skills" / "trading-research-system" / "references" / "leak.md"
        target.write_text("/Users/example/Documents/private-runtime/positions.csv\n", encoding="utf-8")
        self.assert_rejected("private absolute path bundled")

    def test_rejects_unapproved_runtime_shaped_path(self) -> None:
        targets = (
            self.repo
            / "skills"
            / "trading-research-system"
            / "runtime"
            / "watchlist.csv",
            self.repo
            / "plugins"
            / "trading-research-system"
            / "skills"
            / "trading-research-system"
            / "runtime"
            / "watchlist.csv",
        )
        for target in targets:
            target.parent.mkdir()
            target.write_text("ticker\nPRIVATE\n", encoding="utf-8")
        self.assert_rejected("unsupported portable Skill path")

    def test_rejects_missing_claude_wrapper(self) -> None:
        (
            self.repo
            / "plugins"
            / "trading-research-system"
            / ".claude-plugin"
            / "plugin.json"
        ).unlink()
        self.assert_rejected("plugin.json")

    def test_rejects_install_command_duplication(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8")
            + "\nnpx skills@latest add Archerouyang/dailytrades --skill trading-research-system -g\n",
            encoding="utf-8",
        )
        self.assert_rejected("install command must appear exactly once")


if __name__ == "__main__":
    unittest.main()
