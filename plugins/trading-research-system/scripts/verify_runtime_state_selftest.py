#!/usr/bin/env python3
"""Self-test Runtime State path resolution and safe writes."""

from __future__ import annotations

from pathlib import Path
import tempfile

from runtime_state import (
    RuntimeWriter,
    default_runtime_dir,
    resolve_daily_dir,
    resolve_runtime_selection,
    template_dir_from_script,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        configured_runtime = tmp / "configured-runtime"

        if default_runtime_dir({"TRADING_RESEARCH_RUNTIME_DIR": str(configured_runtime)}) != configured_runtime:
            raise AssertionError("configured runtime dir should come from env")

        if default_runtime_dir({}) != Path.home() / "Documents" / "dailytrades-runtime":
            raise AssertionError("default runtime dir should use ~/Documents/dailytrades-runtime")

        explicit_selection = resolve_runtime_selection(configured_runtime, {})
        if explicit_selection.path != configured_runtime or explicit_selection.origin != "explicit_argument":
            raise AssertionError("explicit runtime selection should win")
        env_selection = resolve_runtime_selection(None, {"TRADING_RESEARCH_RUNTIME_DIR": str(configured_runtime)})
        if env_selection.path != configured_runtime or env_selection.origin != "environment":
            raise AssertionError("environment runtime selection should be disclosed")
        default_selection = resolve_runtime_selection(None, {})
        if default_selection.origin != "default":
            raise AssertionError("default runtime selection should be disclosed")

        runtime_dir = tmp / "runtime"
        date = "2026-07-06"
        if resolve_daily_dir(runtime_dir, date) != runtime_dir / "daily" / date:
            raise AssertionError("daily dir should default to <runtime>/daily/<date>")

        daily_root = tmp / "custom-daily-root"
        if resolve_daily_dir(runtime_dir, date, root=daily_root) != daily_root / date:
            raise AssertionError("daily root override should be honored")

        explicit_daily_dir = tmp / "explicit-daily"
        if resolve_daily_dir(runtime_dir, date, daily_dir=explicit_daily_dir) != explicit_daily_dir:
            raise AssertionError("explicit daily dir should win over root/runtime")

        expected_templates = Path(__file__).resolve().parents[1] / "assets" / "templates"
        if template_dir_from_script(__file__) != expected_templates:
            raise AssertionError("template dir should resolve to plugin assets/templates")

        source = tmp / "template.txt"
        source.write_text("template\n", encoding="utf-8")
        target = tmp / "nested" / "target.txt"

        dry_writer = RuntimeWriter(dry_run=True, overwrite=False)
        dry_message = dry_writer.copy_template(source, target)
        if "would write" not in dry_message or target.exists():
            raise AssertionError("dry-run copy should report without writing")

        writer = RuntimeWriter(dry_run=False, overwrite=False)
        if "wrote" not in writer.copy_template(source, target):
            raise AssertionError("first copy should write target")
        target.write_text("user-edited\n", encoding="utf-8")
        if "kept existing" not in writer.copy_template(source, target):
            raise AssertionError("existing target should be kept without overwrite")
        if target.read_text(encoding="utf-8") != "user-edited\n":
            raise AssertionError("kept target should preserve user content")

        overwrite_writer = RuntimeWriter(dry_run=False, overwrite=True)
        if "wrote" not in overwrite_writer.write_text(target, "replacement\n"):
            raise AssertionError("overwrite writer should write replacement text")
        if target.read_text(encoding="utf-8") != "replacement\n":
            raise AssertionError("overwrite writer should replace target content")

    print("runtime state selftest ok")


if __name__ == "__main__":
    main()
