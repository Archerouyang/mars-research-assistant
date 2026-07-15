#!/usr/bin/env python3
"""Self-test Contract Suite discovery and runner behavior."""

from __future__ import annotations

from pathlib import Path
import tempfile

from contract_suite import ContractScript, PluginPaths, is_repo_checkout, run_scripts, suite_scripts


def main() -> None:
    paths = PluginPaths.from_script(__file__)
    if paths.root != Path(__file__).resolve().parents[1]:
        raise AssertionError("PluginPaths should resolve plugin root from script path")
    expected_repo = paths.root.parents[1] if is_repo_checkout(paths.root.parents[1]) else Path.cwd().resolve()
    if paths.repo != expected_repo:
        raise AssertionError("PluginPaths should expose repo root")
    if not is_repo_checkout(paths.repo):
        raise AssertionError("repo root should be detected as a dailytrades checkout")

    scripts = suite_scripts("core", paths)
    names = [script.name for script in scripts]
    if names[0] != "source-routing":
        raise AssertionError(f"core suite should start with source-routing, got {names[0]!r}")
    if "macro-data-source" not in names:
        raise AssertionError("core suite should include macro-data-source")
    if "alpha-leaderboard-adapter-contract" not in names:
        raise AssertionError("core suite should include Alpha Leaderboard adapter contract")
    if "analysis-delta-adapter-contract" not in names:
        raise AssertionError("core suite should include analysis delta adapter contract")
    if "alpha-automations" not in names:
        raise AssertionError("core suite should include Alpha automation contract")
    if "longbridge-skill-adapter" not in names:
        raise AssertionError("core suite should include longbridge-skill-adapter")
    if "broker-snapshot-ingest-contract" not in names:
        raise AssertionError("core suite should include broker snapshot contract")
    if "ibkr-connector-adapter-contract" not in names:
        raise AssertionError("core suite should include IBKR connector adapter contract")
    if "longbridge-cli-adapter-contract" not in names:
        raise AssertionError("core suite should include Longbridge CLI adapter contract")
    if "longbridge-macrodata-adapter-contract" not in names:
        raise AssertionError("core suite should include Longbridge macrodata adapter contract")
    if "setup-row-preparation-contract" not in names:
        raise AssertionError("core suite should include setup row preparation contract")
    if "one-zero-acceptance" not in names:
        raise AssertionError("core suite should include 1.0 acceptance contract")
    if "visual-trigger" not in names:
        raise AssertionError("core suite should include visual trigger contract")
    if "artifact-packet-selftest" not in names:
        raise AssertionError("core suite should include artifact packet selftest")
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

        packaged = tmp / "cache" / "personal" / "trading-research-system" / "0.1.0+codex.test" / "scripts"
        packaged.mkdir(parents=True)
        packaged_script = packaged / "verify_example.py"
        packaged_script.write_text("print('packaged')\n", encoding="utf-8")
        packaged_paths = PluginPaths.from_script(packaged_script)
        if packaged_paths.root != packaged.parent.resolve():
            raise AssertionError("packaged PluginPaths should keep plugin cache root")
        if packaged_paths.repo != paths.repo:
            raise AssertionError("packaged PluginPaths should use cwd repo checkout for repo docs")

    print("contract suite selftest ok")


if __name__ == "__main__":
    main()
