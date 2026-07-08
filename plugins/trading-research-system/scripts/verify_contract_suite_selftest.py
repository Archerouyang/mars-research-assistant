#!/usr/bin/env python3
"""Self-test Contract Suite discovery and runner behavior."""

from __future__ import annotations

from pathlib import Path
import tempfile

from contract_suite import ContractScript, PluginPaths, run_scripts, suite_scripts


def main() -> None:
    paths = PluginPaths.from_script(__file__)
    if paths.root != Path(__file__).resolve().parents[1]:
        raise AssertionError("PluginPaths should resolve plugin root from script path")
    if paths.repo != paths.root.parents[1]:
        raise AssertionError("PluginPaths should expose repo root")

    scripts = suite_scripts("core", paths)
    names = [script.name for script in scripts]
    if names[0] != "source-routing":
        raise AssertionError(f"core suite should start with source-routing, got {names[0]!r}")
    if "macro-data-source" not in names:
        raise AssertionError("core suite should include macro-data-source")
    if "longbridge-skill-adapter" not in names:
        raise AssertionError("core suite should include longbridge-skill-adapter")
    if "broker-snapshot-ingest-contract" not in names:
        raise AssertionError("core suite should include broker snapshot contract")
    if names[-1] != "longbridge-cli-adapter-contract":
        raise AssertionError(f"core suite should end with Longbridge CLI adapter contract, got {names[-1]!r}")
    if len(names) != len(set(names)):
        raise AssertionError("core suite should not contain duplicate names")

    missing = [script.path for script in scripts if not script.path.is_file()]
    if missing:
        raise AssertionError(f"core suite contains missing scripts: {missing!r}")

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        ok = tmp / "ok.py"
        ok.write_text("print('suite ok')\n", encoding="utf-8")
        fail = tmp / "fail.py"
        fail.write_text("import sys\nprint('suite fail')\nsys.exit(7)\n", encoding="utf-8")

        if run_scripts([ContractScript("ok", ok)], emit_output=False) != 0:
            raise AssertionError("run_scripts should pass successful scripts")
        if run_scripts([ContractScript("fail", fail)], emit_output=False) != 7:
            raise AssertionError("run_scripts should return failing script exit code")

    print("contract suite selftest ok")


if __name__ == "__main__":
    main()
