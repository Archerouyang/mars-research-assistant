#!/usr/bin/env python3
"""Create a local daily trading research folder from bundled templates."""

from __future__ import annotations

import argparse
import shutil
from datetime import date
import os
from pathlib import Path

from record_schemas import DAILY_TEMPLATE_TARGETS, template_dir_from_script as schema_template_dir

RESEARCH_NOTES = """# Research Notes

## Information Collection

-

## Information Processing

-

## Trade Ideas

-

## Verification

-
"""


def default_runtime_dir() -> Path:
    configured = os.environ.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Documents" / "dailytrades-runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize runtime daily trading research files.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/dailytrades-runtime",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Daily data root override. Defaults to <runtime-dir>/daily",
    )
    parser.add_argument(
        "--templates",
        default=None,
        help="Template directory; defaults to plugin assets/templates",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def template_dir_from_script() -> Path:
    return schema_template_dir(__file__)


def copy_template(source: Path, target: Path, overwrite: bool) -> str:
    if target.exists() and not overwrite:
        return f"kept existing {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return f"wrote {target}"


def write_text(path: Path, text: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return f"kept existing {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return f"wrote {path}"


def main() -> None:
    args = parse_args()
    root = Path(args.root).expanduser() if args.root else Path(args.runtime_dir).expanduser() / "daily"
    target_dir = root / args.date
    template_dir = Path(args.templates) if args.templates else template_dir_from_script()
    messages: list[str] = []

    for template_name, target_name in DAILY_TEMPLATE_TARGETS.items():
        source = template_dir / template_name
        if not source.is_file():
            raise SystemExit(f"missing template: {source}")
        messages.append(copy_template(source, target_dir / target_name, args.overwrite))

    messages.append(write_text(target_dir / "research-notes.md", RESEARCH_NOTES, args.overwrite))

    print(f"Daily research folder: {target_dir}")
    for message in messages:
        print(f"- {message}")


if __name__ == "__main__":
    main()
