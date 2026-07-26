from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MarsSkillsSuiteTests(unittest.TestCase):
    def _offline_environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "UV_CACHE_DIR": str(ROOT / ".scratch" / "uv-cache"),
                "UV_PROJECT_ENVIRONMENT": str(ROOT / ".scratch" / "uv-venv"),
                "UV_PYTHON_INSTALL_DIR": str(ROOT / ".scratch" / "uv-python"),
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

    def _render_market_snapshot_fixture(
        self, repository: Path, output_path: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "run",
                "--offline",
                "--no-python-downloads",
                "--no-sync",
                "python",
                "scripts/render_market_snapshot_fixture.py",
                "--input",
                "tests/fixtures/market-snapshot-partial.json",
                "--output",
                str(output_path),
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
            env=self._offline_environment(),
        )

    def test_offline_suite_verifier_accepts_the_public_collection(self) -> None:
        result = self._run_verifier(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Mars Skills contract ok: ask-mars", result.stdout)

    def test_offline_suite_verifier_accepts_market_catalysts_brief_fixture(self) -> None:
        result = self._run_verifier(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("market-catalysts-brief", result.stdout)

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

    def test_local_installer_rejects_path_traversal(self) -> None:
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
        self.assertIn("invalid Mars Skill id", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
