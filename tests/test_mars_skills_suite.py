from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MarsSkillsSuiteTests(unittest.TestCase):
    def _run_verifier(
        self, repository: Path, extra_environment: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "UV_CACHE_DIR": str(ROOT / ".scratch" / "uv-cache"),
                "UV_PROJECT_ENVIRONMENT": str(ROOT / ".scratch" / "uv-venv"),
                "UV_PYTHON_INSTALL_DIR": str(ROOT / ".scratch" / "uv-python"),
            }
        )
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

    def test_offline_suite_verifier_accepts_the_public_collection(self) -> None:
        result = self._run_verifier(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Mars Skills contract ok: ask-mars", result.stdout)

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
        for effect in ("research", "market_data", "board_render", "drive_write"):
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
