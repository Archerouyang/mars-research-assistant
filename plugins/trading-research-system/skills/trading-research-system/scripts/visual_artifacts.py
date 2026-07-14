#!/usr/bin/env python3
"""Shared helpers for display-first visual artifacts.

The default mode is transient chat display. Durable runtime saving is opt-in and
must be requested by the caller with an explicit manifest path.

No live broker reads. No live market data calls.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any


DEFAULT_ARTIFACT_DIR = ".scratch/visual-artifacts"


@dataclass(frozen=True)
class VisualArtifactRecord:
    """A durable manifest row for an optional saved visual artifact."""

    artifact_id: str
    type: str
    mode: str
    linked_context: str
    data_source: str
    data_as_of: str
    image_path: str
    html_path: str
    decision_summary: str


def slugify(raw: str, fallback: str = "visual-artifact") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip("-").lower()
    return slug or fallback


def default_display_output(
    repo_root: Path,
    artifact_id: str,
    suffix: str = ".svg",
) -> Path:
    """Return an ignored transient path for chat-display output."""

    return repo_root / DEFAULT_ARTIFACT_DIR / f"{slugify(artifact_id)}{suffix}"


def write_text_artifact(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_manifest(manifest_path: Path, record: VisualArtifactRecord) -> None:
    """Append or replace one artifact record in artifact-manifest.json."""

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        payload = {"schema_version": 1, "artifacts": []}

    if not isinstance(payload, dict):
        raise SystemExit("artifact manifest must be a JSON object")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        artifacts = []

    record_dict = asdict(record)
    replaced = False
    for index, existing in enumerate(artifacts):
        if isinstance(existing, dict) and existing.get("artifact_id") == record.artifact_id:
            artifacts[index] = record_dict
            replaced = True
            break

    if not replaced:
        artifacts.append(record_dict)

    payload["schema_version"] = 1
    payload["artifacts"] = artifacts
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def save_manifest(manifest_path: Path, record: VisualArtifactRecord) -> None:
    """Explicit opt-in wrapper for durable artifact manifest writes."""

    append_manifest(manifest_path, record)


def manifest_record_from_args(
    *,
    artifact_id: str,
    artifact_type: str,
    mode: str,
    linked_context: str,
    data_source: str,
    data_as_of: str,
    image_path: Path | None,
    html_path: Path | None,
    decision_summary: str,
) -> VisualArtifactRecord:
    return VisualArtifactRecord(
        artifact_id=artifact_id,
        type=artifact_type,
        mode=mode,
        linked_context=linked_context,
        data_source=data_source,
        data_as_of=data_as_of,
        image_path=str(image_path or ""),
        html_path=str(html_path or ""),
        decision_summary=decision_summary,
    )


def coerce_series_points(raw: Any, *, value_key: str = "value") -> list[dict[str, Any]]:
    """Normalize a dated numeric series for simple SVG renderers."""

    if not isinstance(raw, list):
        return []

    points: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"series point {index} must be an object")
        time = str(item.get("time") or item.get("date") or index)
        value = item.get(value_key)
        if value in (None, ""):
            continue
        try:
            points.append({"time": time, "value": float(value)})
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"series point {index} has invalid value") from exc
    return points
