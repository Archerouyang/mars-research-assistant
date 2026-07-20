#!/usr/bin/env python3
"""Shared Runtime State helpers for private Trading Research runtime files."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


DEFAULT_RUNTIME_RELATIVE = Path("Documents") / "dailytrades-runtime"


@dataclass(frozen=True)
class RuntimeSelection:
    """Resolved private runtime path plus the source of that selection."""

    path: Path
    origin: str


def default_runtime_dir(env: Mapping[str, str] | None = None) -> Path:
    """Return the configured private runtime directory."""

    source = os.environ if env is None else env
    configured = source.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / DEFAULT_RUNTIME_RELATIVE


def resolve_runtime_selection(
    explicit_runtime_dir: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> RuntimeSelection:
    """Resolve explicit, environment, and default runtime selection in order."""

    if explicit_runtime_dir is not None:
        return RuntimeSelection(Path(explicit_runtime_dir).expanduser(), "explicit_argument")
    source = os.environ if env is None else env
    if source.get("TRADING_RESEARCH_RUNTIME_DIR"):
        return RuntimeSelection(default_runtime_dir(source), "environment")
    return RuntimeSelection(default_runtime_dir(source), "default")


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
