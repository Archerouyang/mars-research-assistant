#!/usr/bin/env python3
"""Rebuild the README gallery from deterministic synthetic fixtures."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "mars-research-assistant"
SCRIPTS = SKILL / "scripts"
FIXTURES = SKILL / "assets" / "fixtures" / "input"
DEFAULT_OUTPUT = REPO / "docs" / "assets" / "readme"


def run(command: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout)


def find_browser(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    candidates = (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    for name in ("google-chrome", "chromium", "chromium-browser"):
        resolved = shutil.which(name)
        if resolved:
            return Path(resolved)
    return None


def capture(browser: Path, html: Path, png: Path) -> None:
    run(
        [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1200,840",
            "--virtual-time-budget=2500",
            "--run-all-compositor-stages-before-draw",
            f"--screenshot={png}",
            html.resolve().as_uri(),
        ]
    )
    if not png.is_file() or png.stat().st_size <= 1_000:
        raise SystemExit(f"browser screenshot is empty: {png}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--browser-mode",
        choices=("required", "auto", "none"),
        default="required",
        help="Whether a browser screenshot is required for the PA README image",
    )
    parser.add_argument("--browser-path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            str(SCRIPTS / "chart_artifact.py"),
            str(FIXTURES / "chart-ohlcv-qqq-sample.json"),
            "--output",
            str(output / "price-action-panel.html"),
            "--display-output",
            str(output / "price-action-panel-fallback.svg"),
            "--artifact-id",
            "readme-price-action",
        ]
    )
    browser = find_browser(args.browser_path)
    if args.browser_mode == "required" and browser is None:
        raise SystemExit("Chrome/Chromium is required to capture the PA README image")
    if args.browser_mode != "none" and browser is not None:
        capture(
            browser,
            output / "price-action-panel.html",
            output / "price-action-panel.png",
        )

    print(f"README gallery generated: {output}")


if __name__ == "__main__":
    main()
