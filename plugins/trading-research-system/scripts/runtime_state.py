#!/usr/bin/env python3
"""Shared Runtime State helpers for private Trading Research runtime files."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
from typing import Mapping


DEFAULT_RUNTIME_RELATIVE = Path("Documents") / "dailytrades-runtime"


def default_runtime_dir(env: Mapping[str, str] | None = None) -> Path:
    """Return the configured private runtime directory."""

    source = os.environ if env is None else env
    configured = source.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / DEFAULT_RUNTIME_RELATIVE


def template_dir_from_script(script_path: str | Path) -> Path:
    """Return the plugin assets/templates directory for a script path."""

    return Path(script_path).resolve().parents[1] / "assets" / "templates"


def resolve_daily_root(runtime_dir: str | Path, root: str | Path | None = None) -> Path:
    """Return the daily root, honoring an explicit root override."""

    if root is not None:
        return Path(root).expanduser()
    return Path(runtime_dir).expanduser() / "daily"


def resolve_daily_dir(
    runtime_dir: str | Path,
    trading_date: str,
    root: str | Path | None = None,
    daily_dir: str | Path | None = None,
) -> Path:
    """Return the dated daily directory, honoring explicit overrides."""

    if daily_dir is not None:
        return Path(daily_dir).expanduser()
    return resolve_daily_root(runtime_dir, root) / trading_date


@dataclass(frozen=True)
class RuntimeWriter:
    """Apply runtime writes consistently, with dry-run and overwrite policy."""

    dry_run: bool = False
    overwrite: bool = False

    def ensure_dir(self, path: str | Path) -> str:
        target = Path(path).expanduser()
        if self.dry_run:
            return f"would create dir {target}"
        target.mkdir(parents=True, exist_ok=True)
        return f"created dir {target}"

    def copy_template(self, source: str | Path, target: str | Path) -> str:
        source_path = Path(source).expanduser()
        target_path = Path(target).expanduser()
        if not source_path.is_file():
            raise SystemExit(f"missing template: {source_path}")
        if target_path.exists() and not self.overwrite:
            return f"kept existing {target_path}"
        if self.dry_run:
            action = "would overwrite" if target_path.exists() else "would write"
            return f"{action} {target_path}"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
        return f"wrote {target_path}"

    def write_text(self, path: str | Path, text: str) -> str:
        target = Path(path).expanduser()
        if target.exists() and not self.overwrite:
            return f"kept existing {target}"
        if self.dry_run:
            action = "would overwrite" if target.exists() else "would write"
            return f"{action} {target}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return f"wrote {target}"
