#!/usr/bin/env python3
"""Validate DailyTrades portable Skill and optional native wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    contract = Path(__file__).with_name("verify_portable_distribution_contract.py")
    result = subprocess.run(
        [sys.executable, str(contract), "--repo-root", str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, end="", file=sys.stderr)
        return result.returncode

    try:
        marketplace = json.loads(
            (repo / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        plugins = marketplace.get("plugins")
        require(isinstance(plugins, list) and len(plugins) == 1, "Codex marketplace must contain one plugin")
        require(plugins[0].get("name") == "trading-research-system", "Codex marketplace name drift")
        require(
            plugins[0].get("source", {}).get("path") == "./plugins/trading-research-system",
            "Codex marketplace source drift",
        )
        manifest = json.loads(
            (
                repo
                / "plugins"
                / "trading-research-system"
                / ".codex-plugin"
                / "plugin.json"
            ).read_text(encoding="utf-8")
        )
        require(manifest.get("version") == "0.1.1", "published version drift")
        require(manifest.get("license") == "MIT", "published license drift")
        require((repo / "LICENSE").is_file(), "root MIT license missing")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"plugin distribution contract failed: {exc}", file=sys.stderr)
        return 1

    print("Plugin distribution contract ok: trading-research-system 0.1.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
