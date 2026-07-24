#!/usr/bin/env python3
"""Copy a private DailyTrades runtime into the Mars runtime without data loss.

The migration is deliberately copy-only: the legacy runtime remains untouched
until the user has inspected the Mars runtime and decides how to retire it.
No manifest is persisted, because private runtime file names and contents do
not belong in public plugin assets.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable


LEGACY_RUNTIME_RELATIVE = Path("Documents") / "dailytrades-runtime"
MARS_RUNTIME_RELATIVE = Path("Documents") / "mars-research-assistant-runtime"


class RuntimeMigrationError(ValueError):
    """An explicit private runtime migration could not be completed safely."""


@dataclass(frozen=True)
class RuntimeFile:
    """Private-file metadata used only while validating one migration."""

    relative_path: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class RuntimeManifest:
    """A non-persisted integrity view of a private runtime directory."""

    directories: tuple[str, ...]
    files: tuple[RuntimeFile, ...]

    @property
    def byte_count(self) -> int:
        return sum(item.byte_count for item in self.files)

    @property
    def digest(self) -> str:
        entries = [f"directory\t{directory}" for directory in self.directories]
        entries.extend(
            f"file\t{item.relative_path}\t{item.byte_count}\t{item.sha256}" for item in self.files
        )
        value = "\n".join(entries).encode("utf-8")
        return hashlib.sha256(value).hexdigest()


CopyFile = Callable[[Path, Path], None]


def default_migration_paths(home_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Return the legacy and Mars default runtime roots without touching disk."""

    home = Path.home() if home_dir is None else Path(home_dir).expanduser()
    return home / LEGACY_RUNTIME_RELATIVE, home / MARS_RUNTIME_RELATIVE


def inspect_private_runtime_migration(
    source_runtime_dir: str | Path,
    destination_runtime_dir: str | Path,
) -> dict[str, object]:
    """Validate a migration and return a private-safe, dry-run summary."""

    source = _resolve_path(source_runtime_dir)
    destination = _resolve_path(destination_runtime_dir)
    _validate_paths(source, destination)
    manifest = _build_manifest(source)
    return _summary(source, destination, manifest, applied=False)


def migrate_private_runtime(
    source_runtime_dir: str | Path,
    destination_runtime_dir: str | Path,
    *,
    apply: bool = False,
    copy_file: CopyFile = shutil.copy2,
) -> dict[str, object]:
    """Copy and validate a private runtime, or return the dry-run summary.

    The destination must not already exist. The source is never renamed,
    deleted, or modified by this function. A staging directory is only renamed
    into place after its complete manifest matches the source manifest.
    """

    source = _resolve_path(source_runtime_dir)
    destination = _resolve_path(destination_runtime_dir)
    _validate_paths(source, destination)
    source_manifest = _build_manifest(source)
    if not apply:
        return _summary(source, destination, source_manifest, applied=False)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.migration-", dir=destination.parent)
    )
    try:
        _copy_manifest(source, staging, source_manifest, copy_file)
        copied_manifest = _build_manifest(staging)
        current_source_manifest = _build_manifest(source)
        if copied_manifest != source_manifest or current_source_manifest != source_manifest:
            raise RuntimeMigrationError("source_changed_during_migration")
        if destination.exists() or destination.is_symlink():
            raise RuntimeMigrationError("destination_runtime_exists")
        staging.replace(destination)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return _summary(source, destination, source_manifest, applied=True)


def _resolve_path(value: str | Path) -> Path:
    return Path(value).expanduser().absolute()


def _validate_paths(source: Path, destination: Path) -> None:
    if source == destination:
        raise RuntimeMigrationError("source_and_destination_must_differ")
    if source.is_symlink() or not source.is_dir():
        raise RuntimeMigrationError("source_runtime_missing_or_unsafe")
    if destination.exists() or destination.is_symlink():
        raise RuntimeMigrationError("destination_runtime_exists")


def _build_manifest(root: Path) -> RuntimeManifest:
    manifest_directories: list[str] = []
    files: list[RuntimeFile] = []
    for current_root, child_directories, file_names in os.walk(root, followlinks=False):
        current = Path(current_root)
        relative_directory = current.relative_to(root)
        if relative_directory != Path("."):
            manifest_directories.append(relative_directory.as_posix())
        for directory in child_directories:
            candidate = current / directory
            if candidate.is_symlink():
                raise RuntimeMigrationError("runtime_symlink_not_supported")
        for file_name in file_names:
            candidate = current / file_name
            if candidate.is_symlink() or not candidate.is_file():
                raise RuntimeMigrationError("runtime_symlink_not_supported")
            relative = candidate.relative_to(root).as_posix()
            files.append(
                RuntimeFile(
                    relative_path=relative,
                    byte_count=candidate.stat().st_size,
                    sha256=_sha256_file(candidate),
                )
            )
    return RuntimeManifest(
        directories=tuple(sorted(manifest_directories)),
        files=tuple(sorted(files, key=lambda item: item.relative_path)),
    )


def _copy_manifest(
    source: Path,
    staging: Path,
    manifest: RuntimeManifest,
    copy_file: CopyFile,
) -> None:
    for directory in manifest.directories:
        (staging / directory).mkdir(parents=True, exist_ok=True)
    for item in manifest.files:
        original = source / item.relative_path
        copied = staging / item.relative_path
        copied.parent.mkdir(parents=True, exist_ok=True)
        try:
            copy_file(original, copied)
        except OSError as error:
            raise RuntimeMigrationError("runtime_copy_failed") from error


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _summary(
    source: Path,
    destination: Path,
    manifest: RuntimeManifest,
    *,
    applied: bool,
) -> dict[str, object]:
    return {
        "kind": "private_runtime_migration",
        "applied": applied,
        "source_runtime_dir": str(source),
        "destination_runtime_dir": str(destination),
        "file_count": len(manifest.files),
        "byte_count": manifest.byte_count,
        "manifest_sha256": manifest.digest,
        "legacy_runtime_preserved": True,
    }


def main() -> int:
    legacy, mars = default_migration_paths()
    parser = argparse.ArgumentParser(description="Safely copy a private runtime into the Mars runtime")
    parser.add_argument("--source-runtime-dir", default=str(legacy))
    parser.add_argument("--destination-runtime-dir", default=str(mars))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="copy after validation; omitted means dry-run only",
    )
    args = parser.parse_args()
    result = migrate_private_runtime(
        args.source_runtime_dir,
        args.destination_runtime_dir,
        apply=args.apply,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
