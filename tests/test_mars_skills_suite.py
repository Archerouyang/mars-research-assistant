from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
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
        defaulted_skills = (
            "ask-mars",
            "market-catalysts-brief",
            "market-snapshot",
            "instrument-research",
            "technical-analysis",
        )
        contracts = {
            identifier: json.loads(
                (
                    ROOT / "skills" / identifier / "capability.json"
                ).read_text(encoding="utf-8")
            )
            for identifier in defaulted_skills
        }
        ask_scenarios = {
            scenario["request"]: scenario["expected"]
            for scenario in contracts["ask-mars"]["scenarios"]
        }

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Mars Skills contract ok: ask-mars", result.stdout)
        for identifier, contract in contracts.items():
            with self.subTest(identifier=identifier):
                self.assertEqual(
                    contract["default_market"],
                    {
                        "when_unspecified": "US equities",
                        "currency": "USD",
                        "timezone": "America/New_York",
                        "user_timezone_does_not_select_market": True,
                        "explicit_market_overrides": True,
                        **(
                            {"default_daily_window": "next 7 calendar days"}
                            if identifier == "market-catalysts-brief"
                            else {}
                        ),
                    },
                )
        for request in ("/ask mars", "开始今天的交易研究"):
            with self.subTest(request=request):
                expected = ask_scenarios[request]
                self.assertEqual(expected["first_step"], "市场快照")
                self.assertEqual(expected["minimum_input"], [])
                self.assertEqual(
                    expected["quick_replies"],
                    ["开始", "只看市场快照", "添加 ticker"],
                )

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

    def test_drive_writeback_proposes_complete_initialization_without_writing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-empty.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            proposal = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化提议", proposal)
        self.assertIn("My Drive ID：my-drive-001", proposal)
        self.assertIn("交易研究中心 Drive ID：尚未创建", proposal)
        self.assertIn("交易研究中心/", proposal)
        self.assertIn("├── 总索引（Google Doc）", proposal)
        for directory in (
            "收件箱",
            "每日市场思考",
            "交易计划",
            "专题研究",
            "周度复盘",
            "案例复盘",
        ):
            self.assertIn(directory, proposal)
        self.assertIn(
            "初始化提议标识：initialize:parent:my-drive-001:交易研究中心",
            proposal,
        )
        self.assertIn("确认状态：等待用户明确确认", proposal)
        self.assertIn("初始化结果：未执行", proposal)
        self.assertNotIn("已创建", proposal)

    def test_drive_writeback_initialization_proposes_only_missing_children(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-partial.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            proposal = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化提议", proposal)
        self.assertIn("交易研究中心 Drive ID：center-001", proposal)
        self.assertIn("初始化提议标识：initialize:root:center-001", proposal)
        self.assertIn(
            "已存在项：交易研究中心（center-001）、总索引（index-001）、"
            "收件箱（inbox-001）、专题研究（topic-001）",
            proposal,
        )
        self.assertIn(
            "拟创建项：每日市场思考（文件夹）、交易计划（文件夹）、"
            "周度复盘（文件夹）、案例复盘（文件夹）",
            proposal,
        )
        self.assertNotIn("拟创建项：交易研究中心", proposal)
        self.assertNotIn("拟创建项：总索引", proposal)

    def test_drive_writeback_initialization_is_a_no_change_success_when_complete(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-complete.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化结果", result_markdown)
        self.assertIn("交易研究中心 Drive ID：center-001", result_markdown)
        self.assertIn("拟创建项：无", result_markdown)
        self.assertIn("确认状态：无需确认（无写入）", result_markdown)
        self.assertIn("初始化结果：无变更，目录结构已完整", result_markdown)
        self.assertNotIn("等待用户明确确认", result_markdown)
        self.assertNotIn("已模拟创建", result_markdown)

    def test_drive_writeback_initialization_stops_for_duplicate_roots(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-duplicate-roots.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            selection = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心根目录选择", selection)
        self.assertIn("发现多个 My Drive 同名根目录", selection)
        self.assertIn("候选 Drive ID：center-001、center-002", selection)
        self.assertIn("选择状态：等待用户明确选择", selection)
        self.assertIn("初始化结果：未执行", selection)
        self.assertNotIn("初始化提议标识：", selection)
        self.assertNotIn("拟创建项：", selection)

    def test_drive_writeback_initialization_rejects_a_confirmation_for_another_target(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-confirmation-mismatch.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            proposal = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化提议", proposal)
        self.assertIn("初始化提议标识：initialize:root:center-001", proposal)
        self.assertIn("目标 Drive ID：center-001", proposal)
        self.assertIn("确认状态：确认与当前初始化提议或目标不匹配", proposal)
        self.assertIn("初始化结果：未执行", proposal)
        self.assertNotIn("# 交易研究中心初始化结果", proposal)

    def test_drive_writeback_initialization_reports_partial_failure_per_item(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-partial-failure.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化结果", result_markdown)
        self.assertIn("目标 parent ID：center-001", result_markdown)
        self.assertIn(
            "created：每日市场思考（daily-002）、专题研究（topic-002）、"
            "周度复盘（weekly-002）、案例复盘（case-002）",
            result_markdown,
        )
        self.assertIn(
            "existing：交易研究中心（center-001）、收件箱（inbox-001）",
            result_markdown,
        )
        self.assertIn("failed：交易计划（权限不足）", result_markdown)
        self.assertIn("pending：总索引（等待六个目录完整后创建）", result_markdown)
        self.assertIn("读回验证：created 项均已验证", result_markdown)
        self.assertIn("初始化结果：部分失败；再次运行只补缺失项", result_markdown)
        self.assertNotIn("已完整初始化", result_markdown)

    def test_drive_writeback_initialization_retry_only_fills_gaps_and_builds_index(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-retry-success.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("created：交易计划（plan-003）、总索引（index-003）", result_markdown)
        self.assertIn("failed：无", result_markdown)
        self.assertIn("pending：无", result_markdown)
        self.assertIn("初始化结果：已完整初始化", result_markdown)
        self.assertIn("## 总索引模板", result_markdown)
        self.assertIn("交易研究中心用于归档已完成的交易研究", result_markdown)
        for directory_id, directory in (
            ("inbox-001", "收件箱"),
            ("daily-002", "每日市场思考"),
            ("plan-003", "交易计划"),
            ("topic-002", "专题研究"),
            ("weekly-002", "周度复盘"),
            ("case-002", "案例复盘"),
        ):
            self.assertIn(
                f"[{directory}](https://drive.google.com/drive/folders/{directory_id})",
                result_markdown,
            )
        for section in ("交易计划", "专题研究", "周度复盘", "案例复盘"):
            self.assertIn(f"### {section}索引", result_markdown)
        self.assertNotIn("### 收件箱索引", result_markdown)
        self.assertNotIn("### 每日市场思考索引", result_markdown)
        self.assertIn("最近更新时间：2026-07-28T10:30:00+08:00", result_markdown)
        self.assertIn("数据缺口：初始化未扫描或回填历史文档。", result_markdown)

    def test_drive_writeback_does_not_accept_a_created_item_with_wrong_readback_parent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = (
                repository
                / "tests"
                / "fixtures"
                / "drive-writeback-init-retry-success.json"
            )
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["execution"]["create_results"]["交易计划"]["readback"] = {
                "id": "plan-003",
                "name": "交易计划",
                "mime_type": "application/vnd.google-apps.folder",
                "parent_id": "wrong-parent",
            }
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                repository,
                "tests/fixtures/drive-writeback-init-retry-success.json",
                output_path,
            )
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("created：交易计划（plan-003）", result_markdown)
        self.assertIn("交易计划（读回验证失败）", result_markdown)
        self.assertIn("pending：总索引（等待六个目录完整后创建）", result_markdown)
        self.assertNotIn("初始化结果：已完整初始化", result_markdown)

    def test_drive_writeback_initialization_creates_full_skeleton_with_locked_parent_ids(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-empty-confirmed.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化结果", result_markdown)
        self.assertIn("交易研究中心 Drive ID：center-010", result_markdown)
        self.assertIn(
            "目标 parent ID：根目录→my-drive-001；子项→center-010",
            result_markdown,
        )
        self.assertIn("created：交易研究中心（center-010）", result_markdown)
        for item_id, item in (
            ("inbox-010", "收件箱"),
            ("daily-010", "每日市场思考"),
            ("plan-010", "交易计划"),
            ("topic-010", "专题研究"),
            ("weekly-010", "周度复盘"),
            ("case-010", "案例复盘"),
            ("index-010", "总索引"),
        ):
            self.assertIn(f"{item}（{item_id}）", result_markdown)
        self.assertIn("existing：无", result_markdown)
        self.assertIn("failed：无", result_markdown)
        self.assertIn("pending：无", result_markdown)
        self.assertIn("初始化结果：已完整初始化", result_markdown)
        self.assertNotIn("日期文档", result_markdown)
        self.assertNotIn("周次文档", result_markdown)
        self.assertNotIn("研究内容文档", result_markdown)

    def test_drive_writeback_requires_a_second_confirmation_after_initialization(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-dual-confirmation.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化结果", result_markdown)
        self.assertIn(
            "初始化提议标识：initialize:parent:my-drive-001:交易研究中心",
            result_markdown,
        )
        self.assertIn("# Drive 写入提议", result_markdown)
        self.assertIn(
            "归档提议标识：archive:topic_research:topic-020:"
            "专题研究 / 双确认测试",
            result_markdown,
        )
        self.assertIn("归档目标 Drive ID：topic-020", result_markdown)
        self.assertIn("确认状态：初始化确认不能授权研究归档", result_markdown)
        self.assertIn("写入结果：未执行", result_markdown)
        self.assertNotIn("# Drive 写入结果", result_markdown)

    def test_drive_writeback_executes_after_a_fresh_second_confirmation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-archive-second-confirmation.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertNotIn("# 交易研究中心初始化", result_markdown)
        self.assertIn("# Drive 写入结果", result_markdown)
        self.assertIn(
            "归档提议标识：archive:topic_research:topic-001:"
            "专题研究 / 第二次确认",
            result_markdown,
        )
        self.assertIn("归档目标 Drive ID：topic-001", result_markdown)
        self.assertIn("确认状态：已明确确认", result_markdown)
        self.assertIn("写入结果：已创建 research-001 并读回验证", result_markdown)
        self.assertIn("总索引：已更新", result_markdown)

    def test_drive_writeback_proposes_archive_after_completing_an_existing_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = (
                repository / "tests" / "fixtures" / "drive-writeback-init-partial.json"
            )
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture.update(
                {
                    "operation": "archive",
                    "research": {
                        "status": "completed",
                        "type": "topic_research",
                        "title": "已有根目录",
                        "content": "已完成的专题研究。",
                    },
                    "initialization_confirmation": {
                        "proposal_id": "initialize:root:center-001",
                        "target_id": "center-001",
                        "explicit": True,
                    },
                    "execution": {
                        "create_results": {
                            name: {
                                "status": "created",
                                "id": item_id,
                                "readback": {
                                    "id": item_id,
                                    "name": name,
                                    "mime_type": "application/vnd.google-apps.folder",
                                    "parent_id": "center-001",
                                },
                            }
                            for name, item_id in (
                                ("每日市场思考", "daily-004"),
                                ("交易计划", "plan-004"),
                                ("周度复盘", "weekly-004"),
                                ("案例复盘", "case-004"),
                            )
                        }
                    },
                    "archive_confirmation": None,
                }
            )
            fixture.pop("confirmation", None)
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                repository,
                "tests/fixtures/drive-writeback-init-partial.json",
                output_path,
            )
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("# 交易研究中心初始化结果", result_markdown)
        self.assertIn("初始化结果：已完整初始化", result_markdown)
        self.assertIn("# Drive 写入提议", result_markdown)
        self.assertIn("归档目标 Drive ID：topic-001", result_markdown)
        self.assertIn("写入结果：未执行", result_markdown)

    def test_drive_writeback_initialization_preserves_drive_failure_reason(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output_path = Path(temporary) / "drive-writeback.md"
            result = self._render_drive_writeback_fixture(
                ROOT,
                "tests/fixtures/drive-writeback-init-drive-unavailable.json",
                output_path,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("# 交易研究中心初始化失败", result_markdown)
        self.assertIn("失败代码：unavailable", result_markdown)
        self.assertIn("失败原因：Google Drive 工具不可用", result_markdown)
        self.assertIn("初始化结果：未执行", result_markdown)
        self.assertNotIn("已完整初始化", result_markdown)
        self.assertNotIn("created：", result_markdown)

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

    def test_drive_writeback_public_contract_describes_idempotent_initialization(
        self,
    ) -> None:
        skill_text = (ROOT / "skills" / "drive-writeback" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        contract = json.loads(
            (ROOT / "skills" / "drive-writeback" / "capability.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("目录初始化", skill_text)
        self.assertIn("My Drive", skill_text)
        self.assertIn("不在本地持久化 Drive ID", skill_text)
        self.assertIn("created / existing / failed / pending", skill_text)
        self.assertIn("初始化确认不能授权研究归档", skill_text)
        self.assertIn("初始化成功后不得自动继续归档", skill_text)
        self.assertIn("初始化和归档分别确认", readme)
        self.assertEqual(
            contract["supported_operations"],
            ["archive_completed_research", "initialize_research_center"],
        )
        self.assertFalse(contract["completed_research_required"])
        self.assertTrue(contract["archive_contract"]["completed_research_required"])
        initialization = contract["initialization_contract"]
        self.assertTrue(initialization["idempotent"])
        self.assertTrue(initialization["stateless_drive_id_resolution"])
        self.assertEqual(
            initialization["directories"],
            [
                "收件箱",
                "每日市场思考",
                "交易计划",
                "专题研究",
                "周度复盘",
                "案例复盘",
            ],
        )
        self.assertEqual(
            set(initialization["offline_fixtures"]),
            {
                "tests/fixtures/drive-writeback-init-empty.json",
                "tests/fixtures/drive-writeback-init-empty-confirmed.json",
                "tests/fixtures/drive-writeback-init-partial.json",
                "tests/fixtures/drive-writeback-init-complete.json",
                "tests/fixtures/drive-writeback-init-duplicate-roots.json",
                "tests/fixtures/drive-writeback-init-confirmation-mismatch.json",
                "tests/fixtures/drive-writeback-init-partial-failure.json",
                "tests/fixtures/drive-writeback-init-retry-success.json",
                "tests/fixtures/drive-writeback-dual-confirmation.json",
                "tests/fixtures/drive-writeback-init-drive-unavailable.json",
            },
        )

    def test_offline_verifier_discovers_drive_initialization_fixtures(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            repository = self._copy_repository(Path(temporary))
            fixture_path = (
                repository
                / "tests"
                / "fixtures"
                / "drive-writeback-init-drive-unavailable.json"
            )
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["operation"] = "unsupported"
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self._run_verifier(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture render failed", result.stdout + result.stderr)

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

    def _fake_uv_environment(
        self,
        directory: Path,
        *,
        exit_code: int = 0,
    ) -> dict[str, str]:
        binary_directory = directory / "bin"
        binary_directory.mkdir(parents=True)
        log_path = directory / "uv.log"
        fake_uv = binary_directory / "uv"
        fake_uv.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'printf "%s\\n" "$*" >> "$MARS_TEST_UV_LOG"\n'
            'if [[ "${1:-} ${2:-}" == "python find" ]]; then\n'
            '  if [[ "${MARS_TEST_UV_FAIL_FIRST_FIND:-0}" == "1"'
            ' && ! -f "$MARS_TEST_UV_FIND_STATE" ]]; then\n'
            '    touch "$MARS_TEST_UV_FIND_STATE"\n'
            "    exit 1\n"
            "  fi\n"
            '  printf "%s\\n" "$MARS_TEST_PYTHON"\n'
            "  exit 0\n"
            "fi\n"
            'if [[ "${1:-} ${2:-}" == "python install" ]]; then exit 0; fi\n'
            f"if [[ {exit_code} -ne 0 ]]; then exit {exit_code}; fi\n"
            'environment_root="${UV_PROJECT_ENVIRONMENT:-$PWD/.venv}"\n'
            'mkdir -p "$environment_root/bin"\n'
            "printf '#!/usr/bin/env bash\\nexec \"%s\" \"$@\"\\n'"
            ' "$MARS_TEST_PYTHON" > "$environment_root/bin/python"\n'
            'chmod 755 "$environment_root/bin/python"\n',
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{binary_directory}:{environment['PATH']}",
                "MARS_TEST_UV_LOG": str(log_path),
                "MARS_TEST_PYTHON": sys.executable,
                "MARS_TEST_UV_FIND_STATE": str(directory / "uv-find.state"),
            }
        )
        return environment

    def test_local_installer_rejects_legacy_argument_shapes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            target = Path(temporary) / "target"
            for legacy_arguments in (
                ["--skill", "../skills/ask-mars", "--target", str(target)],
                ["--all", "--target", str(target)],
            ):
                with self.subTest(arguments=legacy_arguments):
                    result = subprocess.run(
                        [
                            "bash",
                            "scripts/install-mars-skill.sh",
                            *legacy_arguments,
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 64)
                    self.assertIn("usage:", result.stdout + result.stderr)

    def test_local_installer_installs_the_full_release_collection_to_an_empty_target(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            directory = Path(temporary)
            target = directory / "mars-research-assistant"
            outside_environment = directory / "outside-environment"
            environment = self._fake_uv_environment(directory)
            environment["UV_PROJECT_ENVIRONMENT"] = str(outside_environment)
            environment["MARS_TEST_UV_FAIL_FIRST_FIND"] = "1"
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
                env=environment,
            )
            marker = json.loads(
                (target / ".mars-managed.json").read_text(encoding="utf-8")
            )
            uv_log = (directory / "uv.log").read_text(encoding="utf-8")
            root_skill_installed = (target / "SKILL.md").is_file()
            root_skill = (target / "SKILL.md").read_text(encoding="utf-8")
            environment_installed = (target / ".venv" / "bin" / "python").exists()
            environment_leaked = outside_environment.exists()
            child_skills = {
                path.name
                for path in (target / "skills").iterdir()
                if path.is_dir()
            }

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(root_skill_installed)
        self.assertTrue(environment_installed)
        self.assertFalse((target / "README.md").exists())
        self.assertFalse((target / "assets").exists())
        self.assertFalse(environment_leaked)
        self.assertIn("name: mars-research-assistant", root_skill)
        self.assertIn("公开网络", root_skill)
        self.assertIn("其他五个 Skill 不触发 uv", root_skill)
        self.assertEqual(
            child_skills,
            {
                "ask-mars",
                "market-catalysts-brief",
                "market-snapshot",
                "instrument-research",
                "technical-analysis",
                "drive-writeback",
            },
        )
        self.assertEqual(marker["managed_install_schema"], 1)
        self.assertIn("source_integrity", marker)
        self.assertIn("uv_lock_sha256", marker)
        self.assertIn("sync --project", uv_log)
        self.assertIn("--locked", uv_log)
        self.assertIn("python install 3.12", uv_log)
        self.assertIn("installed managed Mars Research Assistant package", result.stdout)

    def test_local_installer_rejects_a_conflicting_destination_without_partial_install(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            directory = Path(temporary)
            target = directory / "target"
            target.mkdir()
            sentinel = target / "sentinel.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            environment = self._fake_uv_environment(directory)
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
                env=environment,
            )
            sentinel_content = sentinel.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        self.assertIn("destination already exists and is not managed", result.stdout + result.stderr)
        self.assertEqual(sentinel_content, "preserve")

    def test_local_installer_preserves_a_managed_install_on_sync_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            directory = Path(temporary)
            target = directory / "target"
            first_environment = self._fake_uv_environment(directory)
            first = subprocess.run(
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
                env=first_environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            sentinel = target / "preserved.txt"
            sentinel.write_text("customized", encoding="utf-8")
            failing = self._fake_uv_environment(directory / "failure", exit_code=42)
            second = subprocess.run(
                [
                    "bash",
                    "scripts/install-mars-skill.sh",
                    "--target",
                    str(target),
                    "--force",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=failing,
            )
            sentinel_content = sentinel.read_text(encoding="utf-8")

        self.assertEqual(second.returncode, 42, second.stdout + second.stderr)
        self.assertEqual(sentinel_content, "customized")

    def test_local_installer_reuses_an_unchanged_managed_environment(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            directory = Path(temporary)
            target = directory / "target"
            environment = self._fake_uv_environment(directory)
            first = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            second = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            uv_log = (directory / "uv.log").read_text(encoding="utf-8")

        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("--locked --python", uv_log)
        self.assertIn("--offline --no-python-downloads", uv_log)

    def test_local_installer_never_executes_a_customized_target_verifier(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            directory = Path(temporary)
            target = directory / "target"
            executed = directory / "untrusted-code-executed"
            environment = self._fake_uv_environment(directory)
            first = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            (target / "scripts" / "managed_package.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(executed)!r}).write_text('executed')\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            untrusted_code_executed = executed.exists()

        self.assertEqual(result.returncode, 74, result.stdout + result.stderr)
        self.assertFalse(untrusted_code_executed)

    def test_local_installer_rejects_a_tampered_managed_environment(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            directory = Path(temporary)
            target = directory / "target"
            environment = self._fake_uv_environment(directory)
            first = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            (target / ".venv" / "tampered.py").write_text(
                "raise RuntimeError('tampered')\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )

        self.assertEqual(result.returncode, 74, result.stdout + result.stderr)
        self.assertIn("customized", result.stdout + result.stderr)

    def test_local_installer_requires_force_to_replace_a_customized_managed_install(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            directory = Path(temporary)
            target = directory / "target"
            environment = self._fake_uv_environment(directory)
            first = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            customization = target / "custom-note.md"
            customization.write_text("user customization", encoding="utf-8")

            rejected = subprocess.run(
                ["bash", "scripts/install-mars-skill.sh", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            preserved_after_rejection = customization.is_file()
            forced = subprocess.run(
                [
                    "bash",
                    "scripts/install-mars-skill.sh",
                    "--target",
                    str(target),
                    "--force",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            removed_after_force = not customization.exists()

        self.assertEqual(rejected.returncode, 74, rejected.stdout + rejected.stderr)
        self.assertTrue(preserved_after_rejection)
        self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
        self.assertTrue(removed_after_force)

    def test_red_upload_bundle_is_hash_manifested_and_filters_private_surface(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-skills-test-") as temporary:
            output = Path(temporary) / "mars-red-upload.zip"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_red_upload_bundle.py",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            manifest_path = output.with_suffix(".manifest.json")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            archive_digest = sha256(output.read_bytes()).hexdigest()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("mars-research-assistant/SKILL.md", names)
        self.assertIn(
            "mars-research-assistant/skills/technical-analysis/SKILL.md",
            names,
        )
        self.assertNotIn("mars-research-assistant/README.md", names)
        self.assertFalse(
            any(name.startswith("mars-research-assistant/assets/") for name in names)
        )
        for prohibited in (
            "/.git/",
            "/.venv/",
            "/tests/",
            "/docs/",
            "/examples/",
            "/AGENTS.md",
            "__pycache__",
            ".pyc",
            "credentials.json",
        ):
            self.assertFalse(any(prohibited in name for name in names), prohibited)
        self.assertEqual(
            manifest["archive_sha256"],
            archive_digest,
        )
        self.assertEqual(
            set(manifest["permissions"]),
            {
                "public_network_research",
                "managed_uv_install",
                "user_selected_local_artifact_write",
                "explicitly_confirmed_google_drive_write",
            },
        )

if __name__ == "__main__":
    unittest.main()
