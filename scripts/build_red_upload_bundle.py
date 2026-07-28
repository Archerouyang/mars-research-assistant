#!/usr/bin/env python3
"""Build a deterministic, filtered RED upload archive and hash manifest."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import stat
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "mars-research-assistant"
PACKAGE_FILE_LIST = ROOT / "package-files.txt"
PERMISSIONS = (
    "public_network_research",
    "managed_uv_install",
    "user_selected_local_artifact_write",
    "explicitly_confirmed_google_drive_write",
)


def _included_files() -> list[Path]:
    relative_paths = [
        line.strip()
        for line in PACKAGE_FILE_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(relative_paths) != len(set(relative_paths)):
        raise ValueError("package file list contains duplicates")
    files: list[Path] = []
    for relative in relative_paths:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"package file is missing or symbolic: {relative}")
        files.append(path)
    return files


def _zip_info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    return info


def build(output: Path) -> Path:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[str, bytes, bool]] = []
    file_hashes: dict[str, str] = {}
    for path in _included_files():
        relative = path.relative_to(ROOT).as_posix()
        name = f"{PREFIX}/{relative}"
        content = path.read_bytes()
        executable = bool(path.stat().st_mode & stat.S_IXUSR)
        entries.append((name, content, executable))
        file_hashes[name] = sha256(content).hexdigest()
    internal_manifest = {
        "red_upload_schema": 1,
        "package": PREFIX,
        "permissions": list(PERMISSIONS),
        "file_sha256": file_hashes,
        "markdown_only_degradation": (
            "Use root SKILL.md for discovery and managed GitHub install guidance; "
            "do not claim scripts or the uv environment are installed."
        ),
    }
    internal_bytes = (
        json.dumps(internal_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    entries.append(
        (f"{PREFIX}/RED_UPLOAD_MANIFEST.json", internal_bytes, False)
    )
    temporary = output.with_suffix(output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w") as archive:
        for name, content, executable in sorted(entries):
            archive.writestr(_zip_info(name, executable), content)
    temporary.replace(output)
    sidecar = {
        **internal_manifest,
        "archive": output.name,
        "archive_sha256": sha256(output.read_bytes()).hexdigest(),
    }
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    manifest = build(arguments.output)
    print(f"built RED upload bundle: {arguments.output.resolve()}")
    print(f"wrote hash manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
