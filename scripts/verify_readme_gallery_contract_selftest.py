#!/usr/bin/env python3
"""Behavior tests for the README gallery verifier CLI."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlparse

from verify_readme_gallery_contract import ContractError, validate_readme


REPO = Path(__file__).resolve().parents[1]
VERIFIER = REPO / "scripts" / "verify_readme_gallery_contract.py"


class ReadmeGalleryVerifierSelftest(unittest.TestCase):
    def test_english_readme_rejects_more_than_180_lines(self) -> None:
        source = (REPO / "README.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(source + "\n" + ("extra\n" * 31), encoding="utf-8")

            with self.assertRaisesRegex(ContractError, "150-180 lines"):
                validate_readme(readme, chinese=False)

    def test_unknown_argument_is_rejected(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VERIFIER), "--unknown-gallery-option"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_required_browser_capture_rejects_missing_browser(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VERIFIER),
                "--require-browser-capture",
                "--browser-path",
                "/definitely/missing/dailytrades-browser",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("required browser capture failed", result.stderr)

    def test_required_browser_capture_succeeds_with_hermetic_fake_browser(self) -> None:
        committed_png = REPO / "docs" / "assets" / "readme" / "price-action-panel.png"
        committed_before = committed_png.read_bytes()
        committed_stat = committed_png.stat()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_browser = root / "fake-browser"
            invocation = root / "browser-invocation.txt"
            fake_browser.write_text(
                f"""#!{sys.executable}
from pathlib import Path
import shutil
import sys

source = Path({str(committed_png)!r})
invocation = Path({str(invocation)!r})
arguments = sys.argv[1:]
screenshot = next(
    (item.split("=", 1)[1] for item in arguments if item.startswith("--screenshot=")),
    None,
)
if screenshot is None:
    raise SystemExit("missing --screenshot argument")
target = Path(screenshot)
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, target)
invocation.write_text("\\n".join(arguments), encoding="utf-8")
""",
                encoding="utf-8",
            )
            fake_browser.chmod(0o755)
            home = root / "home"
            home.mkdir()
            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(home),
                    "CODEX_HOME": str(root / "codex-home"),
                    "CLAUDE_CONFIG_DIR": str(root / "claude-config"),
                    "XDG_CONFIG_HOME": str(root / "xdg-config"),
                    "http_proxy": "http://127.0.0.1:9",
                    "https_proxy": "http://127.0.0.1:9",
                    "all_proxy": "http://127.0.0.1:9",
                    "HTTP_PROXY": "http://127.0.0.1:9",
                    "HTTPS_PROXY": "http://127.0.0.1:9",
                    "ALL_PROXY": "http://127.0.0.1:9",
                    "NO_PROXY": "",
                }
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(VERIFIER),
                    "--require-browser-capture",
                    "--browser-path",
                    str(fake_browser),
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fresh browser capture verified", result.stdout)
            arguments = invocation.read_text(encoding="utf-8").splitlines()
            screenshot_arg = next(
                item for item in arguments if item.startswith("--screenshot=")
            )
            screenshot_path = Path(screenshot_arg.split("=", 1)[1])
            html_uri = next(item for item in arguments if item.startswith("file:"))
            html_path = Path(unquote(urlparse(html_uri).path))
            self.assertEqual(screenshot_path.name, "price-action-panel.png")
            self.assertEqual(screenshot_path.parent.name, "browser-gallery")
            self.assertEqual(html_path.name, "price-action-panel.html")
            self.assertEqual(html_path.parent, screenshot_path.parent)
            self.assertFalse(str(screenshot_path).startswith(str(REPO)))
            self.assertFalse(screenshot_path.exists())

        self.assertEqual(committed_png.read_bytes(), committed_before)
        self.assertEqual(committed_png.stat().st_mtime_ns, committed_stat.st_mtime_ns)
        self.assertEqual(committed_png.stat().st_size, committed_stat.st_size)


if __name__ == "__main__":
    unittest.main()
