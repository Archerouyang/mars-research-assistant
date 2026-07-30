from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "mars-research-assistant"
SNAPSHOT_RENDERER = RUNTIME / "scripts" / "render_equity_snapshot.py"
DEEP_RENDERER = (
    RUNTIME / "skills" / "deep-equity-research" / "scripts" / "render_deep_equity_research.py"
)
SNAPSHOT_FIXTURE = ROOT / "tests" / "fixtures" / "equity-snapshot-primary.json"
DEEP_FIXTURE = ROOT / "tests" / "fixtures" / "deep-equity-research-primary.json"
EXPECTED_SKILLS = {
    "ask-mars",
    "market-catalysts-brief",
    "market-snapshot",
    "instrument-research",
    "deep-equity-research",
    "technical-analysis",
    "drive-writeback",
}


class MarsV102SkillTests(unittest.TestCase):
    def _render(
        self, renderer: Path, fixture: Path, output: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(renderer), "--input", str(fixture), "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_runtime_package_is_discoverable_and_lightweight(self) -> None:
        self.assertFalse((ROOT / "SKILL.md").exists())
        manifest = json.loads((RUNTIME / "mars-skills.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("collection"), "Mars Research Assistant")
        self.assertEqual({item["id"] for item in manifest["skills"]}, EXPECTED_SKILLS)
        files = [path for path in RUNTIME.rglob("*") if path.is_file()]
        self.assertLessEqual(len(files), 60)
        self.assertLessEqual(sum(path.stat().st_size for path in files), 1 << 20)
        root_skill = (RUNTIME / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "npx skills add archerthegoat/mars-research-assistant",
            "--skill mars-research-assistant",
            "--agent codex",
            "--global",
            "--copy",
        ):
            self.assertIn(marker, root_skill)

    def test_skills_follow_the_concise_skill_structure(self) -> None:
        for identifier in EXPECTED_SKILLS | {"mars-research-assistant"}:
            skill_path = (
                RUNTIME / "SKILL.md"
                if identifier == "mars-research-assistant"
                else RUNTIME / "skills" / identifier / "SKILL.md"
            )
            with self.subTest(identifier=identifier):
                text = skill_path.read_text(encoding="utf-8")
                self.assertLessEqual(len(text.splitlines()), 100)
                self.assertIn("description:", text)

    def test_textual_skills_expose_a_non_overwriting_local_markdown_contract(self) -> None:
        expected = {
            "directory": "mars-research",
            "format": "markdown",
            "unique_name_required": True,
            "overwrite": "forbidden",
        }
        for identifier in EXPECTED_SKILLS:
            with self.subTest(identifier=identifier):
                capability = json.loads(
                    (RUNTIME / "skills" / identifier / "capability.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(capability.get("local_artifact_contract"), expected)

    def test_equity_snapshot_renders_required_data_and_recent_updates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            output = Path(temporary) / "mars-research" / "snapshot.md"
            started = perf_counter()
            result = self._render(SNAPSHOT_RENDERER, SNAPSHOT_FIXTURE, output)
            elapsed = perf_counter() - started
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLessEqual(elapsed, 1.0)
            rendered = output.read_text(encoding="utf-8")
        for marker in (
            "# 个股快览：TEST",
            "## 发行人身份",
            "## 关键公开数据",
            "## 最近 30 天公司相关公告或新闻",
            "as_of：",
            "## 数据缺口",
        ):
            self.assertIn(marker, rendered)

    def test_equity_snapshot_never_overwrites_and_requires_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            temporary_path = Path(temporary)
            output = temporary_path / "mars-research" / "snapshot.md"
            first = self._render(SNAPSHOT_RENDERER, SNAPSHOT_FIXTURE, output)
            second = self._render(SNAPSHOT_RENDERER, SNAPSHOT_FIXTURE, output)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("File exists", second.stderr)

            fixture = json.loads(SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))
            fixture["identity"] = {"status": "unavailable", "reason": "代码有歧义。"}
            ambiguous = temporary_path / "ambiguous.json"
            ambiguous.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            blocked_output = temporary_path / "mars-research" / "blocked.md"
            blocked = self._render(SNAPSHOT_RENDERER, ambiguous, blocked_output)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("not uniquely verified", blocked.stderr)
            self.assertFalse(blocked_output.exists())

            fixture = json.loads(SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))
            fixture["identity"]["verified"]["ticker"] = "OTHER"
            mismatch = temporary_path / "mismatched-identity.json"
            mismatch.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            mismatched_output = temporary_path / "mars-research" / "mismatched.md"
            mismatched = self._render(SNAPSHOT_RENDERER, mismatch, mismatched_output)
            self.assertNotEqual(mismatched.returncode, 0)
            self.assertIn("does not match", mismatched.stderr)
            self.assertFalse(mismatched_output.exists())

            cases = (
                ("unrelated", lambda item: item.update({"issuer": "Unrelated Issuer"}), "not directly related"),
                ("directive", lambda item: item.update({"value": "建议增持该股票。"}), "trade directive"),
                ("invalid-as-of", lambda item: item["source"].update({"as_of": "not-a-timestamp"}), "complete timestamp"),
                ("naive-as-of", lambda item: item["source"].update({"as_of": "2026-07-30T12:00:00"}), "timezone"),
                ("same-day-future-as-of", lambda item: item["source"].update({"as_of": "2026-07-30T12:00:01Z"}), "after research as_of"),
                ("future-as-of", lambda item: item["source"].update({"as_of": "2026-07-31T00:00:00Z"}), "after research as_of"),
            )
            for name, mutate, expected_error in cases:
                with self.subTest(name=name):
                    fixture = json.loads(SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))
                    target = (
                        fixture["recent_company_updates"][0]
                        if name == "unrelated"
                        else fixture["key_public_data"][0]
                    )
                    mutate(target)
                    path = temporary_path / f"{name}.json"
                    path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
                    output = temporary_path / "mars-research" / f"{name}.md"
                    result = self._render(SNAPSHOT_RENDERER, path, output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected_error, result.stderr)
                    self.assertFalse(output.exists())

    def test_equity_renderers_refuse_skill_runtime_output_paths(self) -> None:
        cases = (
            (SNAPSHOT_RENDERER, SNAPSHOT_FIXTURE, RUNTIME / "blocked-snapshot.md"),
            (
                DEEP_RENDERER,
                DEEP_FIXTURE,
                RUNTIME / "skills" / "deep-equity-research" / "blocked-deep-research.md",
            ),
        )
        for renderer, fixture, output in cases:
            with self.subTest(renderer=renderer.name):
                try:
                    result = self._render(renderer, fixture, output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Skill runtime package", result.stderr)
                    self.assertFalse(output.exists())
                finally:
                    output.unlink(missing_ok=True)

    def test_deep_research_renders_nine_chapters_and_reproducible_valuation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            output = Path(temporary) / "mars-research" / "deep.md"
            started = perf_counter()
            result = self._render(DEEP_RENDERER, DEEP_FIXTURE, output)
            elapsed = perf_counter() - started
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLessEqual(elapsed, 1.0)
            rendered = output.read_text(encoding="utf-8")
        for number, title in enumerate(
            (
                "研究范围与核心判断",
                "公司与商业模式",
                "行业与竞争格局",
                "管理层、治理与资本配置",
                "财务表现与质量核查",
                "预期差、催化剂与关键跟踪项",
                "三情景 DCF/反向 DCF",
                "风险、反方论点与可证伪条件",
                "来源、时间戳、假设与数据缺口",
            ),
            1,
        ):
            self.assertIn(f"## {number}. {title}", rendered)
        self.assertIn("### 四项最小财报质量检查", rendered)
        self.assertIn("### 三情景 DCF", rendered)
        self.assertIn("### 反向 DCF", rendered)
        self.assertIn("预测期：5 年（来源：", rendered)
        self.assertNotIn("买入", rendered)
        self.assertNotIn("卖出", rendered)
        capability = json.loads(
            (RUNTIME / "skills" / "deep-equity-research" / "capability.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            capability.get("reverse_dcf_input_contract"),
            {
                "required": ["current_free_cash_flow", "horizon_years"],
                "source_traceability_required": True,
                "horizon_years": {
                    "whole_number": True,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
        )

    def test_deep_research_keeps_valuation_gap_when_required_input_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            temporary_path = Path(temporary)
            fixture = json.loads(DEEP_FIXTURE.read_text(encoding="utf-8"))
            del fixture["valuation"]["price"]
            path = temporary_path / "missing-input.json"
            path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            output = temporary_path / "mars-research" / "deep.md"
            result = self._render(DEEP_RENDERER, path, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = output.read_text(encoding="utf-8")
        self.assertIn("估值未运行：缺少必要输入：price。", rendered)
        self.assertIn("## 9. 来源、时间戳、假设与数据缺口", rendered)

    def test_deep_research_rejects_mismatched_identity_unsupported_sources_and_trade_directives(self) -> None:
        cases = (
            ("identity", lambda fixture: fixture["identity"]["verified"].update({"ticker": "OTHER"}), "does not match"),
            ("source", lambda fixture: fixture["sections"]["company_and_business_model"][0]["source"].update({"kind": "search_summary"}), "not allowed"),
            ("directive", lambda fixture: fixture["sections"]["research_scope_and_core_view"][0].update({"statement": "建议买入该股票。"}), "trade directive"),
            ("directive-label", lambda fixture: fixture["sections"]["research_scope_and_core_view"][0].update({"label": "建议卖出"}), "trade directive"),
            ("directive-gap", lambda fixture: fixture["data_gaps"].append("应当加仓。"), "trade directive"),
            ("directive-rating", lambda fixture: fixture["sections"]["research_scope_and_core_view"][0].update({"statement": "建议增持该股票。"}), "trade directive"),
            ("invalid-as-of", lambda fixture: fixture["sections"]["company_and_business_model"][0]["source"].update({"as_of": "not-a-timestamp"}), "complete timestamp"),
            ("future-as-of", lambda fixture: fixture["sections"]["company_and_business_model"][0]["source"].update({"as_of": "2026-07-31T00:00:00Z"}), "after research as_of"),
        )
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            temporary_path = Path(temporary)
            for name, mutate, expected_error in cases:
                with self.subTest(name=name):
                    fixture = json.loads(DEEP_FIXTURE.read_text(encoding="utf-8"))
                    mutate(fixture)
                    path = temporary_path / f"{name}.json"
                    path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
                    output = temporary_path / "mars-research" / f"{name}.md"
                    result = self._render(DEEP_RENDERER, path, output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected_error, result.stderr)
                    self.assertFalse(output.exists())

    def test_deep_research_skips_dcf_when_scenarios_are_not_bear_base_bull(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            temporary_path = Path(temporary)
            fixture = json.loads(DEEP_FIXTURE.read_text(encoding="utf-8"))
            fixture["valuation"]["scenarios"][0]["name"] = "downside"
            path = temporary_path / "bad-scenarios.json"
            path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            output = temporary_path / "mars-research" / "deep.md"
            result = self._render(DEEP_RENDERER, path, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = output.read_text(encoding="utf-8")
        self.assertIn("估值未运行：valuation scenarios must be bear, base, and bull", rendered)

    def test_deep_research_records_a_gap_when_reverse_dcf_has_no_solution_in_range(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            temporary_path = Path(temporary)
            fixture = json.loads(DEEP_FIXTURE.read_text(encoding="utf-8"))
            fixture["valuation"]["price"]["value"] = 10_000_000.0
            path = temporary_path / "reverse-dcf-outside-range.json"
            path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            output = temporary_path / "mars-research" / "deep.md"
            result = self._render(DEEP_RENDERER, path, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = output.read_text(encoding="utf-8")
        self.assertIn("反向 DCF 无法在", rendered)
        self.assertNotIn("以当前股价隐含", rendered)

    def test_offline_verifier_accepts_v102_contract(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/verify_mars_skills.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Mars Skills v1.0.2 contract ok", result.stdout)

    def test_red_bundle_contains_only_the_runtime_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v102-test-") as temporary:
            bundle = Path(temporary) / "mars.zip"
            result = subprocess.run(
                [sys.executable, "scripts/build_red_upload_bundle.py", "--output", str(bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
        self.assertIn("mars-research-assistant/SKILL.md", names)
        self.assertIn(
            "mars-research-assistant/skills/deep-equity-research/SKILL.md", names
        )
        self.assertNotIn("mars-research-assistant/tests/test_mars_skills_suite.py", names)
        self.assertNotIn("mars-research-assistant/README.md", names)

    @unittest.skipUnless(
        os.environ.get("MARS_RUN_NPX_INTEGRATION") == "1",
        "set MARS_RUN_NPX_INTEGRATION=1 to run the local Skills CLI integration test",
    )
    def test_skills_cli_copies_only_the_runtime_package_into_a_local_project(self) -> None:
        npx = shutil.which("npx")
        self.assertIsNotNone(npx, "npx is required for the public Skills CLI entrypoint")
        with tempfile.TemporaryDirectory(prefix="mars-v102-npx-") as temporary:
            project = Path(temporary) / "consumer"
            setup = subprocess.run(
                ["git", "init", "--quiet", str(project)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            listed = subprocess.run(
                [npx, "skills", "add", str(ROOT), "--list"],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(listed.returncode, 0, listed.stdout + listed.stderr)
            discovery = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", listed.stdout)
            self.assertIn("Found 1 skill", discovery)
            self.assertEqual(discovery.count("mars-research-assistant"), 1)
            result = subprocess.run(
                [
                    npx,
                    "skills",
                    "add",
                    str(ROOT),
                    "--skill",
                    "mars-research-assistant",
                    "--agent",
                    "codex",
                    "--copy",
                    "--yes",
                ],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            installed = project / ".agents" / "skills" / "mars-research-assistant"
            self.assertTrue(installed.is_dir())
            expected_files = {
                path.relative_to(RUNTIME).as_posix()
                for path in RUNTIME.rglob("*")
                if path.is_file()
            }
            actual_files = {
                path.relative_to(installed).as_posix()
                for path in installed.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual_files, expected_files)


if __name__ == "__main__":
    unittest.main()
