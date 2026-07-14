#!/usr/bin/env python3
"""Self-test display-first visual artifact generation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

from contract_suite import PluginPaths


def run_script(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"script failed: {' '.join(args)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def assert_contains(path: Path, terms: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise AssertionError(f"{path} missing {term!r}")


def main() -> None:
    paths = PluginPaths.from_script(__file__)
    chart_input = paths.fixture_input / "chart-ohlcv-qqq-sample.json"
    macro_input = paths.fixture_input / "macro-regime-mini-panel-2026-06-24.json"

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)

        display_svg = tmp / "qqq-display.svg"
        run_script(
            [
                str(paths.scripts / "chart_artifact.py"),
                str(chart_input),
                "--display-output",
                str(display_svg),
                "--artifact-id",
                "qqq-display-test",
            ]
        )
        if not display_svg.is_file():
            raise AssertionError("chart script should write a display SVG")
        assert_contains(
            display_svg,
            [
                "<svg",
                "QQQ",
                "EMA 20",
                "EMA 50",
                "trigger zone",
                "TP/rebalance",
                "chart callouts",
                "L1",
                "Z1",
                "price reference table",
                "price / range",
                "plan action",
                "last close",
                "trigger zone high / EMA 20",
                "invalidation / review trigger",
            ],
        )
        if (tmp / "artifact-manifest.json").exists():
            raise AssertionError("chart script must not write a manifest by default")

        saved_svg = tmp / "qqq-saved.svg"
        saved_html = tmp / "qqq-saved.html"
        manifest = tmp / "artifact-manifest.json"
        run_script(
            [
                str(paths.scripts / "chart_artifact.py"),
                str(chart_input),
                "--output",
                str(saved_html),
                "--display-output",
                str(saved_svg),
                "--save-manifest",
                "--manifest",
                str(manifest),
                "--artifact-id",
                "qqq-saved-test",
                "--linked-context",
                "setup:QQQ-demo",
                "--data-source",
                "fixture",
                "--data-as-of",
                "2026-06-12",
                "--decision-summary",
                "Fixture chart for chat display",
            ]
        )
        for expected in (saved_svg, saved_html, manifest):
            if not expected.is_file():
                raise AssertionError(f"expected artifact missing: {expected}")
        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        row = manifest_payload["artifacts"][0]
        if manifest_payload.get("schema_version") != 1:
            raise AssertionError("manifest schema version should be 1")
        if row.get("artifact_id") != "qqq-saved-test":
            raise AssertionError("manifest should record artifact id")
        if row.get("type") != "price_action" or row.get("mode") != "saved":
            raise AssertionError("manifest should record price_action saved artifact")
        if not str(row.get("image_path", "")).endswith(".svg"):
            raise AssertionError("manifest should record display SVG path")

        macro_svg = tmp / "macro-display.svg"
        run_script(
            [
                str(paths.scripts / "macro_regime_artifact.py"),
                str(macro_input),
                "--display-output",
                str(macro_svg),
                "--artifact-id",
                "macro-display-test",
            ]
        )
        if not macro_svg.is_file():
            raise AssertionError("macro script should write a display SVG")
        assert_contains(
            macro_svg,
            [
                "<svg",
                "Macro / Regime",
                "strategy posture",
                "threshold",
                "delta",
                "impact path",
                "reference table",
                "indicator",
                "latest",
                "key thresholds",
                "read",
                "10Y",
                "4.48%",
                "4.50% pressure line",
                "VIX",
                "NDX/RUT",
            ],
        )

    print("visual artifact selftest ok")


if __name__ == "__main__":
    main()
