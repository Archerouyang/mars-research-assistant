from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]


class MarsSkillsSuiteTests(unittest.TestCase):
    def _offline_environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "UV_CACHE_DIR": str(ROOT / ".scratch" / "uv-cache"),
                "UV_PROJECT_ENVIRONMENT": str(ROOT / ".scratch" / "uv-venv"),
                "UV_PYTHON_INSTALL_DIR": str(ROOT / ".scratch" / "uv-python"),
                "UV_PYTHON": sys.executable,
            }
        )
        return environment

    def _run_verifier(
        self, repository: Path, extra_environment: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = self._offline_environment()
        if extra_environment:
            environment.update(extra_environment)
        return subprocess.run(
            [
                "uv",
                "run",
                "--offline",
                "--no-python-downloads",
                "--no-sync",
                "python",
                "scripts/verify_mars_skills.py",
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

    def _copy_repository(self, destination: Path) -> Path:
        copied = destination / "mars-skills"
        shutil.copytree(
            ROOT,
            copied,
            ignore=shutil.ignore_patterns(
                ".git",
                ".scratch",
                ".venv",
                ".mypy_cache",
                ".ruff_cache",
                "__pycache__",
                ".env",
                "auth.json",
                "credentials.json",
                "*.pem",
                "*.log",
                "data",
                "broker",
            ),
        )
        return copied

    def _render_fixture(
        self, repository: Path, renderer: str, fixture: str, output_path: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "run",
                "--offline",
                "--no-python-downloads",
                "--no-sync",
                "python",
                renderer,
                "--input",
                fixture,
                "--output",
                str(output_path),
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
            env=self._offline_environment(),
        )

    def _render_market_snapshot_fixture(
        self, repository: Path, output_path: Path
    ) -> subprocess.CompletedProcess[str]:
        return self._render_fixture(
            repository,
            "scripts/render_market_snapshot_fixture.py",
            "tests/fixtures/market-snapshot-partial.json",
            output_path,
        )

    def _render_instrument_research_fixture(
        self, repository: Path, fixture: str, output_path: Path
    ) -> subprocess.CompletedProcess[str]:
        return self._render_fixture(
            repository,
            "scripts/render_instrument_research_fixture.py",
            fixture,
            output_path,
        )

    def _render_drive_writeback_fixture(
        self, repository: Path, fixture: str, output_path: Path
    ) -> subprocess.CompletedProcess[str]:
        return self._render_fixture(
            repository,
            "scripts/render_drive_writeback_fixture.py",
            fixture,
            output_path,
        )

    def test_offline_suite_verifier_accepts_the_public_collection(self) -> None:
        result = self._run_verifier(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Mars Skills contract ok: ask-mars", result.stdout)

    def test_offline_suite_verifier_accepts_market_catalysts_brief_fixture(self) -> None:
        result = self._run_verifier(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("market-catalysts-brief", result.stdout)

    def test_offline_suite_verifier_requires_all_six_release_skills(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            manifest_path = repository / "mars-skills.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["skills"] = [
                skill for skill in manifest["skills"] if skill["id"] != "drive-writeback"
            ]
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            shutil.rmtree(repository / "skills" / "drive-writeback")

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("six release Skills", result.stdout + result.stderr)

    def test_offline_suite_verifier_requires_evidence_markers_for_data_skills(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            contract_path = (
                repository / "skills" / "technical-analysis" / "capability.json"
            )
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            markers = contract["fixture_validation"]["required_markers"]
            contract["fixture_validation"]["required_markers"] = [
                marker for marker in markers if marker != "as_of："
            ]
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence markers missing", result.stdout + result.stderr)

    def test_readme_describes_yfinance_only_technical_analysis_and_release_checks(
        self,
    ) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("只使用 yfinance", readme)
        self.assertNotIn("FMP", readme)
        self.assertIn("bash scripts/verify-mars-skills.sh", readme)
        self.assertNotIn("long" + "bridge", readme.lower())

    def test_drive_writeback_proposes_a_daily_destination_without_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-proposal.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            proposal = output_path.read_text(encoding="utf-8")

        self.assertIn("# Drive 写入提议", proposal)
        self.assertIn("目标位置：每日市场思考 / 2026-07-26", proposal)
        self.assertIn(
            "提议标识：daily_market_thought:每日市场思考 / 2026-07-26",
            proposal,
        )
        self.assertIn("确认状态：等待用户明确确认", proposal)
        self.assertIn("写入结果：未执行", proposal)
        self.assertIn("总索引：不更新", proposal)

    def test_drive_writeback_allows_confirmed_topic_creation_and_index_update(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-confirmed-topic.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("# Drive 写入结果", result_markdown)
        self.assertIn("目标位置：专题研究 / 半导体资本开支", result_markdown)
        self.assertIn("确认状态：已明确确认", result_markdown)
        self.assertIn("写入结果：已模拟创建", result_markdown)
        self.assertIn("总索引：更新（模拟）", result_markdown)

    def test_drive_writeback_does_not_write_for_a_confirmation_of_another_proposal(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "drive-writeback-confirmed-topic.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["confirmation"] = {
                "proposal_id": "topic_research:专题研究 / 另一份研究",
                "explicit": True,
            }
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                repository,
                "tests/fixtures/drive-writeback-confirmed-topic.json",
                output_path,
            )
            proposal = output_path.read_text(encoding="utf-8") if output_path.exists() else ""

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("# Drive 写入提议", proposal)
        self.assertIn("确认状态：确认与当前提议不匹配", proposal)
        self.assertIn("写入结果：未执行", proposal)
        self.assertNotIn("# Drive 写入结果", proposal)

    def test_drive_writeback_proposes_each_research_center_destination(self) -> None:
        cases = (
            ("inbox", "盘前想法", "收件箱 / 盘前想法", "总索引：不更新"),
            (
                "daily_market_thought",
                "半导体资本开支",
                "每日市场思考 / 2026-07-26",
                "总索引：不更新",
            ),
            ("trade_plan", "半导体资本开支", "交易计划 / 2026-W31", "总索引：更新"),
            ("topic_research", "半导体资本开支", "专题研究 / 半导体资本开支", "总索引：更新"),
            ("weekly_review", "半导体资本开支", "周度复盘 / 2026-W31", "总索引：更新"),
            ("case_review", "半导体资本开支", "案例复盘 / 半导体资本开支", "总索引：更新"),
        )
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "drive-writeback-proposal.json"
            for research_type, title, destination, index_status in cases:
                with self.subTest(research_type=research_type):
                    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
                    fixture["research"] = {
                        "status": "completed",
                        "type": research_type,
                        "date": "2026-07-26",
                        "period": "2026-W31",
                        "title": title,
                        "content": "已完成的研究内容。",
                    }
                    fixture_path.write_text(
                        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    output_path = Path(temporary) / "drive-writeback.md"
                    result = self._render_drive_writeback_fixture(
                        repository,
                        "tests/fixtures/drive-writeback-proposal.json",
                        output_path,
                    )
                    proposal = output_path.read_text(encoding="utf-8") if output_path.exists() else ""

                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(f"目标位置：{destination}", proposal)
                    self.assertIn(index_status, proposal)

    def test_drive_writeback_rejects_research_that_is_not_completed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "drive-writeback-proposal.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["research"]["status"] = "draft"
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                repository,
                "tests/fixtures/drive-writeback-proposal.json",
                output_path,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("only completed research can be archived", result.stdout + result.stderr)
        self.assertFalse(output_path.exists())

    def test_drive_writeback_rejects_completed_research_without_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "drive-writeback-proposal.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["research"].pop("content", None)
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                repository,
                "tests/fixtures/drive-writeback-proposal.json",
                output_path,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("research content requires text", result.stdout + result.stderr)
        self.assertFalse(output_path.exists())

    def test_offline_suite_verifier_rejects_drive_writeback_without_confirmation_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            contract_path = repository / "skills" / "drive-writeback" / "capability.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["explicit_confirmation_required"] = False
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit confirmation required", result.stdout + result.stderr)

    def test_instrument_research_fixture_excludes_macro_and_technical_analysis(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "instrument-research.md"
            result = self._render_instrument_research_fixture(
                ROOT,
                "tests/fixtures/instrument-research-primary.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            research = output_path.read_text(encoding="utf-8")

        self.assertIn("# 标的研究：NVDA", research)
        self.assertIn("## 事实与证据", research)
        self.assertIn("SEC 披露", research)
        self.assertIn("发行人 IR", research)
        self.assertIn("## 基本面", research)
        self.assertIn("## 行业背景", research)
        self.assertIn("## 公司事件", research)
        self.assertIn("## 推断", research)
        self.assertIn("验证条件：后续季度披露继续确认数据中心需求。", research)
        self.assertIn("## 数据缺口", research)
        self.assertNotIn("## 宏观", research)
        self.assertNotIn("## 技术面分析", research)

    def test_instrument_research_fixture_keeps_evidence_gap_visible_without_company_facts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "instrument-research.md"
            result = self._render_instrument_research_fixture(
                ROOT,
                "tests/fixtures/instrument-research-evidence-gap.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            research = output_path.read_text(encoding="utf-8")

        self.assertIn("# 标的研究：UNKNOWN", research)
        self.assertIn("发行人身份未确认", research)
        self.assertIn("数据不可用", research)
        self.assertIn("来源：未提供可验证资料", research)
        self.assertIn("as_of：2026-07-26T09:00:00-04:00", research)
        self.assertIn("不会将聚合资料写成公司事实", research)
        self.assertNotIn("## 基本面", research)

    def test_instrument_research_renderer_rejects_company_facts_without_primary_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "instrument-research-primary.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["fundamentals"][0]["source"]["kind"] = "aggregate_quote"
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._render_instrument_research_fixture(
                repository,
                "tests/fixtures/instrument-research-primary.json",
                Path(temporary) / "instrument-research.md",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires primary filing or issuer IR evidence", result.stdout + result.stderr)

    def test_instrument_research_keeps_confirmed_issuer_research_when_one_section_is_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "instrument-research-primary.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture.pop("industry_context")
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_path = Path(temporary) / "instrument-research.md"

            result = self._render_instrument_research_fixture(
                repository,
                "tests/fixtures/instrument-research-primary.json",
                output_path,
            )
            research = output_path.read_text(encoding="utf-8") if output_path.exists() else ""

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("## 基本面", research)
        self.assertIn("## 行业背景", research)
        self.assertIn("数据不可用：未提供行业背景的一手证据。", research)
        self.assertIn("## 数据缺口", research)

    def test_instrument_research_fixture_accepts_non_us_regulatory_disclosure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "instrument-research.md"
            result = self._render_instrument_research_fixture(
                ROOT,
                "tests/fixtures/instrument-research-non-us.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            research = output_path.read_text(encoding="utf-8")

        self.assertIn("# 标的研究：7203.T", research)
        self.assertIn("监管披露", research)
        self.assertIn("非美国发行人", research)

    def test_offline_suite_verifier_rejects_instrument_research_without_a_single_instrument(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            contract_path = repository / "skills" / "instrument-research" / "capability.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["single_instrument_required"] = False
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("single instrument", result.stdout + result.stderr)

    def test_market_snapshot_fixture_renders_a_partial_markdown_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "market-snapshot.md"
            result = self._render_market_snapshot_fixture(ROOT, output_path)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            snapshot = output_path.read_text(encoding="utf-8")

        self.assertIn("# 市场快照", snapshot)
        self.assertIn("## 当前状态", snapshot)
        self.assertIn("## 核心指标", snapshot)
        self.assertIn("2 年期国债", snapshot)
        self.assertIn("CPI（同比）", snapshot)
        self.assertIn("VIX3M", snapshot)
        self.assertIn("HYG/LQD", snapshot)
        self.assertIn("DXY", snapshot)
        self.assertIn("WTI 原油", snapshot)
        self.assertIn("黄金", snapshot)
        self.assertIn("数据不可用", snapshot)
        self.assertIn("美国财政部", snapshot)
        self.assertIn("Cboe", snapshot)
        self.assertIn("2026-07-26T09:00:00-04:00", snapshot)

    def test_market_snapshot_renderer_rejects_an_unavailable_indicator_without_a_reason(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "market-snapshot-partial.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["indicator_groups"][2]["indicators"][0].pop("reason")
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._render_market_snapshot_fixture(
                repository, Path(temporary) / "market-snapshot.md"
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unavailable indicator requires a reason", result.stdout + result.stderr)

    def test_market_snapshot_renderer_keeps_a_partial_snapshot_when_optional_sections_absent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "market-snapshot-partial.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            for section in ("event_context", "scenarios", "risks"):
                fixture.pop(section)
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_path = Path(temporary) / "market-snapshot.md"

            result = self._render_market_snapshot_fixture(repository, output_path)
            snapshot = output_path.read_text(encoding="utf-8") if output_path.exists() else ""

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("## 近期催化剂", snapshot)
        self.assertIn("## 情景与触发", snapshot)
        self.assertIn("## 风险暴露", snapshot)
        self.assertIn("数据不可用", snapshot)

    def test_market_snapshot_renderer_rejects_a_populated_indicator_without_source(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "market-snapshot-partial.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["indicator_groups"][0]["indicators"][0].pop("source", None)
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._render_market_snapshot_fixture(
                repository, Path(temporary) / "market-snapshot.md"
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("indicator requires a source", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_market_snapshot_without_explicit_request(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            contract_path = repository / "skills" / "market-snapshot" / "capability.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["explicit_request_required"] = False
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit request", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_catalyst_without_market_transmission(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "market-catalysts-brief.json"
            fixture_path.write_text(
                fixture_path.read_text(encoding="utf-8").replace(
                    '"market_transmission": "美国利率路径预期可能重估。",\n',
                    "",
                    1,
                ),
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("market transmission", result.stdout + result.stderr)

    def test_offline_suite_verifier_checks_every_catalyst_fixture(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            contract_path = (
                repository / "skills" / "market-catalysts-brief" / "capability.json"
            )
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            extra_scenario = dict(contract["scenarios"][0])
            extra_scenario["fixture"] = "tests/fixtures/missing-catalysts-fixture.json"
            contract["scenarios"].append(extra_scenario)
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture missing", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_catalyst_fixture_outside_the_repository(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = repository / "tests" / "fixtures" / "market-catalysts-brief.json"
            outside_fixture = repository.parent / "outside-fixture.json"
            outside_fixture.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")
            contract_path = (
                repository / "skills" / "market-catalysts-brief" / "capability.json"
            )
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["scenarios"][0]["fixture"] = "../outside-fixture.json"
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the repository", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_credential_in_public_docs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            (repository / "docs" / "credential-example.md").write_text(
                "api_" + "key=fake-test-value\n", encoding="utf-8"
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("possible credential assignment", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_credential_in_a_public_log(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            (repository / "public.log").write_text(
                "api_" + "key=fake-test-value\n", encoding="utf-8"
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("possible credential assignment", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_credential_in_an_extensionless_public_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            (repository / "credential").write_text(
                "api_" + "key=fake-test-value\n", encoding="utf-8"
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("possible credential assignment", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_generic_private_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            (repository / "private-path").write_text(
                "/" + "home" + "/example/private/research\n", encoding="utf-8"
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("private absolute path", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_a_skill_symlink(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            (repository / "skills" / "ask-mars" / "external").symlink_to("/etc/hosts")

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symbolic link", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_an_unconsumed_capability_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            skill_path = repository / "skills" / "ask-mars" / "SKILL.md"
            skill_path.write_text(
                skill_path.read_text(encoding="utf-8").replace("capability.json", ""),
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("capability contract", result.stdout + result.stderr)

    def test_offline_suite_verifier_rejects_each_missing_ask_mars_policy_effect(self) -> None:
        for effect in ("research", "market_data", "drive_write"):
            with self.subTest(effect=effect), tempfile.TemporaryDirectory(
                prefix="mars-skills-test-"
            ) as temporary:
                repository = self._copy_repository(Path(temporary))
                skill_path = repository / "skills" / "ask-mars" / "SKILL.md"
                skill_text = skill_path.read_text(encoding="utf-8")
                self.assertIn(f'"{effect}"', skill_text)
                skill_path.write_text(
                    skill_text.replace(f'"{effect}"', f'"removed-{effect}"', 1),
                    encoding="utf-8",
                )

                result = self._run_verifier(repository)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Skill policy", result.stdout + result.stderr)

    def test_offline_suite_verifier_refuses_an_unavailable_python(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            result = self._run_verifier(
                ROOT,
                {
                    "UV_CACHE_DIR": str(Path(temporary) / "uv-cache"),
                    "UV_PROJECT_ENVIRONMENT": str(Path(temporary) / "uv-venv"),
                    "UV_PYTHON": "3.99",
                },
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python", result.stdout + result.stderr)

    def test_local_installer_rejects_legacy_single_skill_arguments(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            target = Path(temporary) / "target"
            result = subprocess.run(
                [
                    "bash",
                    "scripts/install-mars-skill.sh",
                    "--skill",
                    "../skills/ask-mars",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout + result.stderr)

    def test_local_installer_installs_the_full_release_collection_to_an_empty_target(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            target = Path(temporary) / "target"
            result = subprocess.run(
                [
                    "bash",
                    "scripts/install-mars-skill.sh",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            installed = {
                path.name: {
                    file.relative_to(path): file.read_bytes()
                    for file in path.rglob("*")
                    if file.is_file()
                }
                for path in target.iterdir()
                if path.is_dir() and not path.name.startswith(".")
            }

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(set(installed), {
            "ask-mars",
            "market-catalysts-brief",
            "market-snapshot",
            "instrument-research",
            "technical-analysis",
            "drive-writeback",
        })
        for identifier, installed_files in installed.items():
            self.assertEqual(
                {
                    path.relative_to(ROOT / "skills" / identifier): path.read_bytes()
                    for path in (ROOT / "skills" / identifier).rglob("*")
                    if path.is_file()
                },
                installed_files,
            )
        self.assertIn("installed all 6 Mars Skills", result.stdout)

    def test_local_installer_rejects_a_conflicting_destination_without_partial_install(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            target = Path(temporary) / "target"
            conflict = target / "technical-analysis"
            conflict.mkdir(parents=True)
            (conflict / "sentinel.txt").write_text("preserve", encoding="utf-8")
            result = subprocess.run(
                [
                    "bash",
                    "scripts/install-mars-skill.sh",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            remaining = sorted(path.name for path in target.iterdir())

        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        self.assertIn("destination already exists", result.stdout + result.stderr)
        self.assertEqual(remaining, ["technical-analysis"])

    def test_local_installer_rejects_the_legacy_all_argument(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            target = Path(temporary) / "target"
            result = subprocess.run(
                [
                    "bash",
                    "scripts/install-mars-skill.sh",
                    "--all",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 64, result.stdout + result.stderr)
        self.assertIn("usage:", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
