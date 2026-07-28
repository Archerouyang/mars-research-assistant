#!/usr/bin/env python3
"""Create and verify the integrity marker for a managed Mars package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from typing import Any


MARKER_NAME = ".mars-managed.json"
EXCLUDED_PARTS = {".venv", "__pycache__"}


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _tracked_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if (
            not path.is_file()
            or path.name == MARKER_NAME
            or path.suffix == ".pyc"
            or any(part in EXCLUDED_PARTS for part in relative.parts)
        ):
            continue
        files[relative.as_posix()] = _digest(path)
    return files


def _environment_integrity(root: Path) -> dict[str, int | str]:
    environment = root / ".venv"
    if not environment.is_dir():
        raise ValueError("managed package-local .venv is missing")
    digest = sha256()
    entries = 0
    for path in sorted(environment.rglob("*")):
        relative = path.relative_to(environment).as_posix()
        if path.is_symlink():
            kind = b"link"
            payload = os.readlink(path).encode("utf-8")
        elif path.is_file():
            kind = b"file"
            payload = path.read_bytes()
        else:
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(kind)
        digest.update(b"\0")
        digest.update(sha256(payload).digest())
        entries += 1
    return {"sha256": digest.hexdigest(), "entries": entries}


def _read_marker(root: Path) -> dict[str, Any]:
    marker_path = root / MARKER_NAME
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid managed marker: {error}") from error
    if (
        not isinstance(marker, dict)
        or marker.get("managed_install_schema") != 1
        or marker.get("package") != "mars-research-assistant"
        or not isinstance(marker.get("source_integrity"), dict)
        or not isinstance(marker.get("environment_integrity"), dict)
    ):
        raise ValueError("unsupported managed marker")
    return marker


def write_marker(root: Path) -> None:
    lock_path = root / "uv.lock"
    marker = {
        "managed_install_schema": 1,
        "package": "mars-research-assistant",
        "uv_lock_sha256": _digest(lock_path),
        "source_integrity": _tracked_files(root),
        "environment_integrity": _environment_integrity(root),
    }
    marker_path = root / MARKER_NAME
    temporary = marker_path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(marker, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, marker_path)


def verify_marker(root: Path) -> None:
    marker = _read_marker(root)
    expected = marker["source_integrity"]
    actual = _tracked_files(root)
    if actual != expected:
        changed = sorted(
            path
            for path in set(actual) | set(expected)
            if actual.get(path) != expected.get(path)
        )
        preview = ", ".join(changed[:5])
        raise ValueError(f"managed install was customized: {preview}")
    if marker.get("uv_lock_sha256") != _digest(root / "uv.lock"):
        raise ValueError("managed uv.lock does not match its marker")
    if marker["environment_integrity"] != _environment_integrity(root):
        raise ValueError("managed package-local environment was customized")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("write", "verify", "lock-hash"))
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    try:
        if arguments.command == "write":
            write_marker(root)
        elif arguments.command == "verify":
            verify_marker(root)
        else:
            print(_read_marker(root)["uv_lock_sha256"])
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 74
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
