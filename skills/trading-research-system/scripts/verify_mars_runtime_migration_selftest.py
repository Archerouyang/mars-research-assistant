#!/usr/bin/env python3
"""Focused safety checks for the copy-only private runtime migration."""

from __future__ import annotations

from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from mars_runtime_migration import (
    RuntimeMigrationError,
    default_migration_paths,
    inspect_private_runtime_migration,
    migrate_private_runtime,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_error(expected: str, callback) -> None:
    try:
        callback()
    except RuntimeMigrationError as error:
        require(str(error) == expected, f"expected {expected}, got {error}")
    else:
        raise AssertionError(f"expected migration error: {expected}")


def seed_runtime(root: Path) -> Path:
    runtime = root / "legacy-runtime"
    (runtime / "daily" / "2026-07-24").mkdir(parents=True)
    (runtime / "updates").mkdir()
    (runtime / "daily" / "2026-07-24" / "market-plan.md").write_text(
        "private runtime content\n", encoding="utf-8"
    )
    (runtime / "trading-profile.md").write_text("private profile\n", encoding="utf-8")
    return runtime


def main() -> int:
    with TemporaryDirectory(prefix="mars-runtime-migration-") as temporary:
        root = Path(temporary)
        legacy, mars = default_migration_paths(root)
        require(
            legacy == root / "Documents" / "dailytrades-runtime",
            "legacy default path must remain explicit for the migration",
        )
        require(
            mars == root / "Documents" / "mars-research-assistant-runtime",
            "Mars default path must be deterministic",
        )

        source = seed_runtime(root)
        destination = root / "mars-runtime"
        dry_run = inspect_private_runtime_migration(source, destination)
        require(dry_run["applied"] is False, "inspection must remain dry-run")
        require(dry_run["file_count"] == 2, "dry-run must account for every regular file")
        require(not destination.exists(), "dry-run must not create a destination")
        require(dry_run["legacy_runtime_preserved"] is True, "source preservation must be explicit")

        applied = migrate_private_runtime(source, destination, apply=True)
        require(applied["applied"] is True, "explicit apply must report completion")
        require(source.is_dir(), "migration must preserve the legacy source")
        require(
            (destination / "daily" / "2026-07-24" / "market-plan.md").read_text(encoding="utf-8")
            == "private runtime content\n",
            "destination must retain copied runtime bytes",
        )
        require((destination / "updates").is_dir(), "migration must preserve empty runtime directories")
        require(
            inspect_private_runtime_migration(destination, root / "copy-check")["manifest_sha256"]
            == applied["manifest_sha256"],
            "applied runtime must match the validated manifest",
        )
        expect_error(
            "destination_runtime_exists",
            lambda: migrate_private_runtime(source, destination, apply=True),
        )
        require(source.is_dir(), "destination conflict must not alter the source")

        changed_source = seed_runtime(root / "changed")
        changed_destination = root / "changed-destination"
        changed = False

        def mutate_after_copy(origin: Path, copied: Path) -> None:
            nonlocal changed
            shutil.copy2(origin, copied)
            if not changed:
                changed = True
                (changed_source / "trading-profile.md").write_text("changed\n", encoding="utf-8")

        expect_error(
            "source_changed_during_migration",
            lambda: migrate_private_runtime(
                changed_source,
                changed_destination,
                apply=True,
                copy_file=mutate_after_copy,
            ),
        )
        require(not changed_destination.exists(), "validation failure must not publish a destination")
        require(
            not list(root.glob(".changed-destination.migration-*")),
            "validation failure must clean its staging directory",
        )

        failed_source = seed_runtime(root / "failed")
        failed_destination = root / "failed-destination"

        def fail_copy(_: Path, __: Path) -> None:
            raise OSError("simulated copy failure")

        expect_error(
            "runtime_copy_failed",
            lambda: migrate_private_runtime(
                failed_source,
                failed_destination,
                apply=True,
                copy_file=fail_copy,
            ),
        )
        require(not failed_destination.exists(), "copy failure must not publish a destination")
        require(
            not list(root.glob(".failed-destination.migration-*")),
            "copy failure must clean its staging directory",
        )

        unsafe_source = root / "unsafe-runtime"
        unsafe_source.mkdir()
        (unsafe_source / "link").symlink_to(source / "trading-profile.md")
        expect_error(
            "runtime_symlink_not_supported",
            lambda: inspect_private_runtime_migration(unsafe_source, root / "unsafe-destination"),
        )

    print("mars runtime migration selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
