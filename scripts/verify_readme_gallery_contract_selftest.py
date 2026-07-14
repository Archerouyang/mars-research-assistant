#!/usr/bin/env python3
"""Behavior tests for the README gallery verifier CLI."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
VERIFIER = REPO / "scripts" / "verify_readme_gallery_contract.py"


class ReadmeGalleryVerifierSelftest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
