#!/usr/bin/env python3
"""Behavior test for the non-polluting plugin compile gate."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILE_GATE = REPO_ROOT / "scripts" / "verify-plugin-compile.sh"


class PluginCompileGateTest(unittest.TestCase):
    def test_compiles_without_writing_bytecode_into_plugin_package(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            plugin_scripts = root / "plugin" / "scripts"
            compile_cache = root / "compile-cache"
            plugin_scripts.mkdir(parents=True)
            (plugin_scripts / "example.py").write_text(
                "VALUE = 1\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update(
                {
                    "PLUGIN_SCRIPTS": str(plugin_scripts),
                    "PLUGIN_COMPILE_CACHE_ROOT": str(compile_cache),
                    "PYTHON_BIN": sys.executable,
                }
            )

            result = subprocess.run(
                ["bash", str(COMPILE_GATE)],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(list(plugin_scripts.rglob("__pycache__")))
            self.assertFalse(list(plugin_scripts.rglob("*.pyc")))
            self.assertTrue(list(compile_cache.rglob("*.pyc")))


if __name__ == "__main__":
    unittest.main()
