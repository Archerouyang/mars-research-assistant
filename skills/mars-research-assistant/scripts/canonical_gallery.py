#!/usr/bin/env python3
"""Build and verify one staged, exact-byte cross-host research Gallery.

The module consumes only committed synthetic snapshots and caller-provided PNG
captures. It performs no browser, network, broker, runtime, or order action.
"""

from __future__ import annotations

from dataclasses import dataclass
import binascii
import copy
from html import escape
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import tempfile
from typing import Callable, Mapping, Sequence
import zlib

from artifact_packet import (
    ArtifactPacketError,
    HTML_HARD_LIMIT_BYTES,
    MANIFEST_HARD_LIMIT_BYTES,
    SNAPSHOT_HARD_LIMIT_BYTES,
    build_artifact_packet,
    canonical_json_bytes,
    sha256_hex,
    write_artifact_packet,
)


GALLERY_MANIFEST_VERSION = "1.0"
GALLERY_PNG_TARGET_BYTES = 1536 * 1024
GALLERY_PNG_HARD_LIMIT_BYTES = 2560 * 1024
PUBLIC_SNAPSHOT_TARGET_BYTES = 750 * 1024
PUBLIC_HTML_TARGET_BYTES = 2560 * 1024
CAPTURE_HEIGHT = 840
CAPTURE_WIDTHS = (1200, 700)
EVIDENCE_STATES = ("complete", "partial", "source_error", "stale")
PUBLIC_GALLERY_PREFIX = "docs/assets/canonical-gallery"


class GalleryError(ValueError):
    """A stable fail-closed code for Gallery generation and verification."""


@dataclass(frozen=True)
class BoardSpec:
    board_id: str
    slug: str
    fixture_prefix: str
    view_ids: tuple[tuple[str, str], ...]
    approved_views: tuple[str, ...]

    @property
    def views(self) -> tuple[str, ...]:
        return tuple(label for label, _view_id in self.view_ids)

    def view_id(self, label: str) -> str:
        try:
            return dict(self.view_ids)[label]
        except KeyError as exc:
            raise GalleryError("gallery_view_invalid") from exc


@dataclass(frozen=True)
class CaptureSpec:
    board_id: str
    board_slug: str
    view: str
    width: int
    height: int = CAPTURE_HEIGHT

    @property
    def view_slug(self) -> str:
        value = self.view.lower().replace("&", "and")
        return re.sub(r"[^a-z0-9]+", "-", value).strip("-")

    @property
    def relative_path(self) -> str:
        return f"captures/{self.board_slug}/{self.view_slug}-{self.width}x{self.height}.png"


BOARD_SPECS = (
    BoardSpec(
        board_id="instrument_research",
        slug="instrument-research",
        fixture_prefix="instrument-research",
        view_ids=(
            ("Overview", "overview"),
            ("Price & Setup", "price-setup"),
            ("Industry & Peers", "industry-peers"),
            ("Catalysts & Flows", "catalysts-flows"),
        ),
        approved_views=("Overview", "Price & Setup"),
    ),
    BoardSpec(
        board_id="macro_regime",
        slug="macro-regime",
        fixture_prefix="macro-regime",
        view_ids=(
            ("Overview", "overview"),
            ("Rates & Liquidity", "rates-liquidity"),
            ("Inflation & Growth", "inflation-growth"),
            ("Cross-Asset Impact", "cross-asset-impact"),
            ("Event Scenarios", "event-scenarios"),
        ),
        approved_views=("Overview", "Cross-Asset Impact"),
    ),
)
BOARD_BY_ID = {item.board_id: item for item in BOARD_SPECS}
APPROVED_CAPTURES = tuple(
    CaptureSpec(spec.board_id, spec.slug, view, width)
    for spec in BOARD_SPECS
    for view in spec.approved_views
    for width in CAPTURE_WIDTHS
)


Capture = Callable[[CaptureSpec, Path], bytes | tuple[bytes, Mapping[str, int | float | str]]]


def validate_fixture_corpus(fixtures_dir: Path) -> dict[str, object]:
    """Validate the exact three-Board by four-state public fixture matrix."""

    snapshots: list[dict[str, object]] = []
    states_by_board: dict[str, list[str]] = {}
    complete_view_count = 0
    seen_snapshot_ids: set[str] = set()
    for spec in BOARD_SPECS:
        states: list[str] = []
        for state in EVIDENCE_STATES:
            path = fixtures_dir / f"{spec.fixture_prefix}-{state.replace('_', '-')}.json"
            if not path.is_file():
                raise GalleryError("fixture_missing")
            raw = path.read_bytes()
            try:
                snapshot = json.loads(raw)
                packet = build_artifact_packet(snapshot)
            except (json.JSONDecodeError, ArtifactPacketError) as exc:
                raise GalleryError("fixture_invalid") from exc
            if snapshot.get("board") != spec.board_id or snapshot.get("evidence_state") != state:
                raise GalleryError("fixture_state_mismatch")
            if snapshot.get("privacy") != "public_fixture":
                raise GalleryError("fixture_privacy_invalid")
            snapshot_id = snapshot.get("snapshot_id")
            if not isinstance(snapshot_id, str) or snapshot_id in seen_snapshot_ids:
                raise GalleryError("fixture_identity_invalid")
            seen_snapshot_ids.add(snapshot_id)
            views = snapshot.get("payload", {}).get("views")
            if views != list(spec.views):
                raise GalleryError("fixture_views_mismatch")
            _validate_semantic_overview(snapshot, packet.html)
            if state == "complete":
                complete_view_count += len(views)
            snapshot_bytes = len(packet.canonical_json)
            html_bytes = len(packet.html)
            if snapshot_bytes > SNAPSHOT_HARD_LIMIT_BYTES:
                raise GalleryError("snapshot_size_exceeded")
            if html_bytes > HTML_HARD_LIMIT_BYTES:
                raise GalleryError("html_size_exceeded")
            states.append(state)
            snapshots.append(
                {
                    "board": spec.board_id,
                    "evidence_state": state,
                    "fixture": path.name,
                    "fixture_sha256": sha256_hex(raw),
                    "html_bytes": html_bytes,
                    "html_target_met": html_bytes <= PUBLIC_HTML_TARGET_BYTES,
                    "privacy": snapshot["privacy"],
                    "snapshot_bytes": snapshot_bytes,
                    "snapshot_id": snapshot_id,
                    "snapshot_target_met": snapshot_bytes <= PUBLIC_SNAPSHOT_TARGET_BYTES,
                }
            )
        states_by_board[spec.board_id] = states
    return {
        "complete_view_count": complete_view_count,
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "states_by_board": states_by_board,
    }


def stage_gallery(
    *,
    fixtures_dir: Path,
    output_dir: Path,
    capture: Capture,
    documentation_sources: Sequence[Path],
) -> Path:
    """Generate a coherent Gallery in a fresh sibling and atomically publish it."""

    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise GalleryError("output_not_fresh")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        corpus_report = validate_fixture_corpus(fixtures_dir)
        board_rows: list[dict[str, object]] = []
        board_record_by_id: dict[str, dict[str, object]] = {}
        for spec in BOARD_SPECS:
            fixture = fixtures_dir / f"{spec.fixture_prefix}-complete.json"
            snapshot = json.loads(fixture.read_text(encoding="utf-8"))
            packet = build_artifact_packet(snapshot)
            packet_dir = temporary / "artifacts" / spec.slug
            write_artifact_packet(packet, packet_dir)
            artifact_manifest = json.loads(packet.manifest)
            html_path = f"artifacts/{spec.slug}/research-brief.html"
            json_path = f"artifacts/{spec.slug}/snapshot.canonical.json"
            manifest_path = f"artifacts/{spec.slug}/artifact.manifest.json"
            html_hash = sha256_hex(packet.html)
            row: dict[str, object] = {
                "artifact_manifest_path": manifest_path,
                "artifact_manifest_sha256": sha256_hex(packet.manifest),
                "board": spec.board_id,
                "canonical_json_path": json_path,
                "canonical_json_sha256": sha256_hex(packet.canonical_json),
                "decision_cutoff": snapshot["decision_cutoff"],
                "evidence_state": snapshot["evidence_state"],
                "html_bytes": len(packet.html),
                "html_path": html_path,
                "html_sha256": html_hash,
                "host_delivery": {
                    "claude_code": {
                        "html_path": html_path,
                        "html_sha256": html_hash,
                        "mode": "local_open",
                    },
                    "codex": {
                        "html_path": html_path,
                        "html_sha256": html_hash,
                        "mode": "exact_byte_copy",
                    },
                    "github": {
                        "html_path": html_path,
                        "html_sha256": html_hash,
                        "mode": "hash_linked_static",
                    },
                },
                "privacy": snapshot["privacy"],
                "snapshot_id": snapshot["snapshot_id"],
                "views": artifact_manifest["views"],
            }
            board_rows.append(row)
            board_record_by_id[spec.board_id] = row

        capture_rows: list[dict[str, object]] = []
        for spec in APPROVED_CAPTURES:
            html_path = temporary / str(board_record_by_id[spec.board_id]["html_path"])
            result = capture(spec, html_path)
            if isinstance(result, tuple):
                png, timing = result
            else:
                png, timing = result, {}
            png = embed_png_identity(png, board=spec.board_id, view=spec.view)
            metadata = inspect_png(png)
            if metadata["width"] != spec.width or metadata["height"] != spec.height:
                raise GalleryError("capture_dimensions_invalid")
            if metadata["identity"].get("mars-research-assistant-synthetic") != "true":
                raise GalleryError("capture_identity_invalid")
            if len(png) > GALLERY_PNG_HARD_LIMIT_BYTES:
                raise GalleryError("capture_size_exceeded")
            path = temporary / spec.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(png)
            board_row = board_record_by_id[spec.board_id]
            capture_rows.append(
                {
                    "board": spec.board_id,
                    "height": spec.height,
                    "html_sha256": board_row["html_sha256"],
                    "non_interactive": True,
                    "path": spec.relative_path,
                    "png_bytes": len(png),
                    "png_sha256": sha256_hex(png),
                    "png_target_met": len(png) <= GALLERY_PNG_TARGET_BYTES,
                    "synthetic": True,
                    "timing": _normalize_timing(timing),
                    "view": spec.view,
                    "width": spec.width,
                }
            )

        proposal_rows = _write_documentation_proposals(
            temporary,
            documentation_sources=documentation_sources,
            captures=capture_rows,
            boards=board_rows,
        )
        manifest: dict[str, object] = {
            "boards": board_rows,
            "budgets": {
                "capture_hard_bytes": GALLERY_PNG_HARD_LIMIT_BYTES,
                "capture_target_bytes": GALLERY_PNG_TARGET_BYTES,
                "html_hard_bytes": HTML_HARD_LIMIT_BYTES,
                "html_target_bytes": PUBLIC_HTML_TARGET_BYTES,
                "manifest_hard_bytes": MANIFEST_HARD_LIMIT_BYTES,
                "snapshot_hard_bytes": SNAPSHOT_HARD_LIMIT_BYTES,
                "snapshot_target_bytes": PUBLIC_SNAPSHOT_TARGET_BYTES,
                "timing_ms": {"capture": 5000, "controls_ready": 2000, "semantic_ready": 1000},
            },
            "captures": capture_rows,
            "corpus": corpus_report,
            "browser_acceptance": _capture_report(capture),
            "documentation_proposals": proposal_rows,
            "gallery_manifest_version": GALLERY_MANIFEST_VERSION,
            "presentation_failures": [
                "missing_artifact",
                "invalid_artifact",
                "capture_mismatch",
            ],
            "public_cutover": "not_performed",
        }
        manifest["gallery_content_hash"] = gallery_content_hash(manifest)
        manifest_bytes = canonical_json_bytes(manifest)
        if len(manifest_bytes) > MANIFEST_HARD_LIMIT_BYTES:
            raise GalleryError("gallery_manifest_size_exceeded")
        (temporary / "gallery.manifest.json").write_bytes(manifest_bytes)
        verify_gallery(temporary)
        os.replace(temporary, output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return output_dir


def verify_reproduced_gallery(
    *,
    output_dir: Path,
    fixtures_dir: Path,
    capture: Capture,
    documentation_sources: Sequence[Path],
) -> None:
    """Regenerate in a fresh directory and reject coordinated capture/hash edits."""

    verify_gallery(output_dir)
    with tempfile.TemporaryDirectory(dir=output_dir.parent) as tmp:
        reproduced = Path(tmp) / "reproduced-gallery"
        stage_gallery(
            fixtures_dir=fixtures_dir,
            output_dir=reproduced,
            capture=capture,
            documentation_sources=documentation_sources,
        )
        original_manifest = verify_gallery(output_dir)
        reproduced_manifest = verify_gallery(reproduced)
        if canonical_json_bytes(_normalized_reproduction_manifest(original_manifest)) != canonical_json_bytes(
            _normalized_reproduction_manifest(reproduced_manifest)
        ):
            raise GalleryError("gallery_reproduction_mismatch")
        paths = [
            *(str(item["path"]) for item in original_manifest["captures"]),
            *(str(item["html_path"]) for item in original_manifest["boards"]),
            *(str(item["canonical_json_path"]) for item in original_manifest["boards"]),
            *(str(item["artifact_manifest_path"]) for item in original_manifest["boards"]),
            *(str(item["path"]) for item in original_manifest["documentation_proposals"]),
        ]
        reproduced_paths = {
            *(str(item["path"]) for item in reproduced_manifest["captures"]),
            *(str(item["html_path"]) for item in reproduced_manifest["boards"]),
            *(str(item["canonical_json_path"]) for item in reproduced_manifest["boards"]),
            *(str(item["artifact_manifest_path"]) for item in reproduced_manifest["boards"]),
            *(str(item["path"]) for item in reproduced_manifest["documentation_proposals"]),
        }
        if set(paths) != reproduced_paths:
            raise GalleryError("gallery_reproduction_mismatch")
        for relative in paths:
            if (output_dir / relative).read_bytes() != (reproduced / relative).read_bytes():
                raise GalleryError("gallery_reproduction_mismatch")


def verify_gallery(output_dir: Path) -> dict[str, object]:
    """Verify every exact byte and identity in an existing staged Gallery."""

    manifest_path = output_dir / "gallery.manifest.json"
    try:
        manifest_bytes = manifest_path.read_bytes()
        if len(manifest_bytes) > MANIFEST_HARD_LIMIT_BYTES:
            raise GalleryError("gallery_manifest_size_exceeded")
        manifest = json.loads(manifest_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GalleryError("gallery_manifest_invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("gallery_manifest_version") != GALLERY_MANIFEST_VERSION:
        raise GalleryError("gallery_manifest_invalid")
    if manifest.get("gallery_content_hash") != gallery_content_hash(manifest):
        raise GalleryError("gallery_content_hash_mismatch")
    if manifest.get("public_cutover") != "not_performed":
        raise GalleryError("public_cutover_invalid")
    expected_budgets = {
        "capture_hard_bytes": GALLERY_PNG_HARD_LIMIT_BYTES,
        "capture_target_bytes": GALLERY_PNG_TARGET_BYTES,
        "html_hard_bytes": HTML_HARD_LIMIT_BYTES,
        "html_target_bytes": PUBLIC_HTML_TARGET_BYTES,
        "manifest_hard_bytes": MANIFEST_HARD_LIMIT_BYTES,
        "snapshot_hard_bytes": SNAPSHOT_HARD_LIMIT_BYTES,
        "snapshot_target_bytes": PUBLIC_SNAPSHOT_TARGET_BYTES,
        "timing_ms": {"capture": 5000, "controls_ready": 2000, "semantic_ready": 1000},
    }
    if manifest.get("budgets") != expected_budgets:
        raise GalleryError("gallery_budgets_invalid")
    if manifest.get("presentation_failures") != [
        "missing_artifact",
        "invalid_artifact",
        "capture_mismatch",
    ]:
        raise GalleryError("presentation_failures_invalid")
    corpus = manifest.get("corpus")
    if (
        not isinstance(corpus, dict)
        or corpus.get("snapshot_count") != 12
        or corpus.get("complete_view_count") != 15
    ):
        raise GalleryError("gallery_corpus_invalid")
    browser_acceptance = manifest.get("browser_acceptance")
    if not isinstance(browser_acceptance, dict) or browser_acceptance.get("mode") not in {
        "browser",
        "hermetic_test",
    }:
        raise GalleryError("browser_acceptance_invalid")
    if browser_acceptance.get("mode") == "browser" and (
        browser_acceptance.get("complete_views_checked") != 15
        or browser_acceptance.get("no_js_overviews_checked") != 3
    ):
        raise GalleryError("browser_acceptance_invalid")

    boards = manifest.get("boards")
    captures = manifest.get("captures")
    if not isinstance(boards, list) or len(boards) != 3:
        raise GalleryError("gallery_boards_invalid")
    if not isinstance(captures, list) or len(captures) != len(APPROVED_CAPTURES):
        raise GalleryError("gallery_captures_invalid")
    board_by_id: dict[str, Mapping[str, object]] = {}
    for board in boards:
        if not isinstance(board, dict) or board.get("board") not in BOARD_BY_ID:
            raise GalleryError("gallery_boards_invalid")
        board_id = str(board["board"])
        board_by_id[board_id] = board
        _verify_file_hash(output_dir, board, "html_path", "html_sha256", "html_hash_mismatch")
        _verify_file_hash(
            output_dir,
            board,
            "canonical_json_path",
            "canonical_json_sha256",
            "canonical_json_hash_mismatch",
        )
        _verify_file_hash(
            output_dir,
            board,
            "artifact_manifest_path",
            "artifact_manifest_sha256",
            "artifact_manifest_hash_mismatch",
        )
        artifact_manifest_path = _safe_path(output_dir, board.get("artifact_manifest_path"))
        try:
            artifact_manifest = json.loads(artifact_manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GalleryError("artifact_manifest_invalid") from exc
        if (
            artifact_manifest.get("board") != board_id
            or artifact_manifest.get("snapshot_id") != board.get("snapshot_id")
            or artifact_manifest.get("html_sha256") != board.get("html_sha256")
            or artifact_manifest.get("canonical_json_sha256")
            != board.get("canonical_json_sha256")
            or artifact_manifest.get("default_view") != "Overview"
            or artifact_manifest.get("presentation_state") != "ready"
            or artifact_manifest.get("privacy") != "public_fixture"
            or artifact_manifest.get("views") != board.get("views")
        ):
            raise GalleryError("artifact_manifest_invalid")
        hosts = board.get("host_delivery")
        if not isinstance(hosts, dict) or set(hosts) != {"codex", "claude_code", "github"}:
            raise GalleryError("host_delivery_invalid")
        for host in hosts.values():
            if (
                not isinstance(host, dict)
                or host.get("html_path") != board.get("html_path")
                or host.get("html_sha256") != board.get("html_sha256")
            ):
                raise GalleryError("host_delivery_mismatch")
        expected_modes = {
            "codex": "exact_byte_copy",
            "claude_code": "local_open",
            "github": "hash_linked_static",
        }
        if any(hosts[name].get("mode") != mode for name, mode in expected_modes.items()):
            raise GalleryError("host_delivery_invalid")

    actual_capture_keys: set[tuple[object, ...]] = set()
    for capture in captures:
        if not isinstance(capture, dict):
            raise GalleryError("gallery_captures_invalid")
        board = board_by_id.get(str(capture.get("board")))
        if board is None or capture.get("html_sha256") != board.get("html_sha256"):
            raise GalleryError("capture_html_mismatch")
        path = _safe_path(output_dir, capture.get("path"))
        try:
            png = path.read_bytes()
        except OSError as exc:
            raise GalleryError("capture_missing") from exc
        if sha256_hex(png) != capture.get("png_sha256"):
            raise GalleryError("capture_hash_mismatch")
        if len(png) != capture.get("png_bytes") or len(png) > GALLERY_PNG_HARD_LIMIT_BYTES:
            raise GalleryError("capture_size_mismatch")
        metadata = inspect_png(png)
        if (
            metadata["width"] != capture.get("width")
            or metadata["height"] != capture.get("height")
            or metadata["identity"].get("mars-research-assistant-board") != capture.get("board")
            or metadata["identity"].get("mars-research-assistant-view") != capture.get("view")
            or metadata["identity"].get("mars-research-assistant-synthetic") != "true"
            or not metadata["nonblank"]
        ):
            raise GalleryError("capture_identity_invalid")
        timing = capture.get("timing")
        if not isinstance(timing, dict) or set(timing) != {
            "browser_startup_ms",
            "capture_ms",
            "controls_ready_ms",
            "semantic_ready_ms",
        }:
            raise GalleryError("capture_timing_invalid")
        for key, hard_limit in (("semantic_ready_ms", 1000), ("controls_ready_ms", 2000), ("capture_ms", 5000)):
            value = timing[key]
            if not isinstance(value, (int, float)) or value < 0 or value > hard_limit:
                raise GalleryError("capture_timing_exceeded")
        actual_capture_keys.add(
            (capture.get("board"), capture.get("view"), capture.get("width"), capture.get("height"))
        )
    expected_capture_keys = {
        (item.board_id, item.view, item.width, item.height) for item in APPROVED_CAPTURES
    }
    if actual_capture_keys != expected_capture_keys:
        raise GalleryError("gallery_captures_invalid")

    proposals = manifest.get("documentation_proposals")
    if not isinstance(proposals, list) or len(proposals) != 3:
        raise GalleryError("documentation_proposal_invalid")
    for proposal in proposals:
        if not isinstance(proposal, dict):
            raise GalleryError("documentation_proposal_invalid")
        _verify_file_hash(output_dir, proposal, "path", "sha256", "documentation_hash_mismatch")
    expected_files = {
        "gallery.manifest.json",
        *(str(board[field]) for board in boards for field in (
            "html_path",
            "canonical_json_path",
            "artifact_manifest_path",
        )),
        *(str(capture["path"]) for capture in captures),
        *(str(proposal["path"]) for proposal in proposals),
    }
    actual_files = {
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        raise GalleryError("gallery_inventory_invalid")
    return manifest


def copy_exact_html(gallery_dir: Path, board_id: str, destination: Path) -> Path:
    """Copy canonical bytes for a host, accepting only empty or identical output."""

    manifest = verify_gallery(gallery_dir)
    board = next((row for row in manifest["boards"] if row["board"] == board_id), None)
    if board is None:
        raise GalleryError("board_invalid")
    source = _safe_path(gallery_dir, board["html_path"])
    data = source.read_bytes()
    if destination.exists() and destination.read_bytes() != data:
        raise GalleryError("host_output_conflict")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(data)
    if sha256_hex(destination.read_bytes()) != board["html_sha256"]:
        raise GalleryError("host_copy_mismatch")
    return destination


def create_test_png(width: int, height: int, *, board: str, view: str) -> bytes:
    """Create a small deterministic nonblank RGB PNG for hermetic contract tests."""

    rows = bytearray()
    colors = ((246, 248, 250), (23, 105, 170), (154, 103, 0), (36, 106, 54))
    for y in range(height):
        rows.append(0)
        block_row = bytearray()
        for block in range((width + 79) // 80):
            color = colors[(block + (y // 60)) % len(colors)]
            block_row.extend(bytes(color) * 80)
        rows.extend(block_row[: width * 3])
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
    png += _png_chunk(b"IEND", b"")
    return embed_png_identity(png, board=board, view=view)


def embed_png_identity(png: bytes, *, board: str, view: str) -> bytes:
    """Add or replace safe identity metadata before the PNG IEND chunk."""

    chunks = _read_png_chunks(png)
    retained = [
        (kind, data)
        for kind, data in chunks
        if kind != b"IEND"
        and not (
            kind == b"tEXt"
            and data.partition(b"\0")[0].endswith((b"-board", b"-view", b"-synthetic"))
        )
    ]
    identity = (
        ("mars-research-assistant-board", board),
        ("mars-research-assistant-view", view),
        ("mars-research-assistant-synthetic", "true"),
    )
    output = bytearray(b"\x89PNG\r\n\x1a\n")
    for kind, data in retained:
        output.extend(_png_chunk(kind, data))
    for key, value in identity:
        output.extend(_png_chunk(b"tEXt", key.encode("latin-1") + b"\0" + value.encode("latin-1")))
    output.extend(_png_chunk(b"IEND", b""))
    return bytes(output)


def inspect_png(png: bytes) -> dict[str, object]:
    """Validate dimensions, identity metadata, and basic nonblank pixel content."""

    chunks = _read_png_chunks(png)
    ihdr = next((data for kind, data in chunks if kind == b"IHDR"), None)
    if ihdr is None or len(ihdr) != 13:
        raise GalleryError("capture_invalid")
    width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", ihdr
    )
    if depth != 8 or color_type not in {2, 6} or compression or filtering or interlace:
        raise GalleryError("capture_invalid")
    identity: dict[str, str] = {}
    compressed = bytearray()
    for kind, data in chunks:
        if kind == b"IDAT":
            compressed.extend(data)
        if kind == b"tEXt" and b"\0" in data:
            key, value = data.split(b"\0", 1)
            if key.startswith(b"mars-research-assistant-"):
                identity[key.decode("latin-1")] = value.decode("latin-1")
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error as exc:
        raise GalleryError("capture_invalid") from exc
    bytes_per_pixel = 3 if color_type == 2 else 4
    stride = width * bytes_per_pixel
    if len(raw) != height * (stride + 1):
        raise GalleryError("capture_invalid")
    previous = bytearray(stride)
    distinct: set[bytes] = set()
    for row_index in range(height):
        start = row_index * (stride + 1)
        filter_type = raw[start]
        source = raw[start + 1 : start + 1 + stride]
        if filter_type == 0:
            reconstructed = bytearray(source)
        else:
            reconstructed = bytearray(stride)
            for index, value in enumerate(source):
                left = reconstructed[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
                above = previous[index]
                upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
                predictor = _png_predictor(filter_type, left, above, upper_left)
                reconstructed[index] = (value + predictor) & 0xFF
        if row_index % max(1, height // 20) == 0:
            for offset in range(0, stride, max(bytes_per_pixel, stride // 40)):
                distinct.add(bytes(reconstructed[offset : offset + 3]))
        previous = reconstructed
    return {
        "height": height,
        "identity": identity,
        "nonblank": len(distinct) >= 3,
        "width": width,
    }


def _validate_semantic_overview(snapshot: Mapping[str, object], html: bytes) -> None:
    text = html.decode("utf-8")
    payload = snapshot.get("payload")
    if not isinstance(payload, dict):
        raise GalleryError("semantic_overview_invalid")
    required_values = (
        escape(str(payload.get("decision", ""))),
        str(snapshot.get("decision_cutoff", "")),
        str(snapshot.get("evidence_state", "")),
    )
    if any(not value or value not in text for value in required_values):
        raise GalleryError("semantic_overview_invalid")
    required_tokens = ("Decision cutoff", "Evidence rail", "Coverage", "gap")
    if any(token.lower() not in text.lower() for token in required_tokens):
        raise GalleryError("semantic_overview_invalid")


def _write_documentation_proposals(
    output: Path,
    *,
    documentation_sources: Sequence[Path],
    captures: Sequence[Mapping[str, object]],
    boards: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if len(documentation_sources) != 2:
        raise GalleryError("documentation_sources_invalid")
    proposals = output / "proposals"
    proposals.mkdir(parents=True, exist_ok=True)
    capture_by_board_view_width = {
        (item["board"], item["view"], item["width"]): item for item in captures
    }
    overview_lines_en = [
        "## Proposed Canonical Research Board Gallery",
        "",
        "Staged only. These synthetic, non-interactive captures are hash-linked to the same canonical HTML used by Codex and Claude Code.",
        "",
    ]
    overview_lines_zh = [
        "## 拟议 Canonical Research Board Gallery",
        "",
        "仅在 staging 中。以下合成、非交互截图与 Codex 和 Claude Code 使用的同一份 canonical HTML 通过哈希关联。",
        "",
    ]
    for board in boards:
        spec = BOARD_BY_ID[str(board["board"])]
        capture = capture_by_board_view_width[(spec.board_id, "Overview", 1200)]
        public_capture = f"{PUBLIC_GALLERY_PREFIX}/{capture['path']}"
        public_html = f"{PUBLIC_GALLERY_PREFIX}/{board['html_path']}"
        hash_prefix = str(capture["png_sha256"])[:12]
        overview_lines_en.extend(
            (
                f"### {spec.slug.replace('-', ' ').title()}",
                f"![Synthetic {spec.slug} Overview; png sha256 {hash_prefix}]({public_capture})",
                f"[Open canonical HTML]({public_html}) · non-interactive screenshot · synthetic fixture",
                "",
            )
        )
        overview_lines_zh.extend(
            (
                f"### {spec.slug.replace('-', ' ').title()}",
                f"![合成 {spec.slug} Overview；PNG SHA-256 {hash_prefix}]({public_capture})",
                f"[打开 canonical HTML]({public_html}) · 非交互截图 · 合成 fixture",
                "",
            )
        )

    source_en = documentation_sources[0].read_text(encoding="utf-8")
    source_zh = documentation_sources[1].read_text(encoding="utf-8")
    content_by_path = {
        "proposals/README.proposed.md": _replace_markdown_section(
            source_en,
            "Synthetic Output Gallery",
            "\n".join(overview_lines_en),
        ),
        "proposals/README.zh-CN.proposed.md": _replace_markdown_section(
            source_zh,
            "合成输出示例",
            "\n".join(overview_lines_zh),
        ),
        "proposals/canonical-research-boards.proposed.md": _detailed_document(captures, boards),
    }
    rows: list[dict[str, object]] = []
    for relative, content in content_by_path.items():
        data = content.encode("utf-8")
        path = output / relative
        path.write_bytes(data)
        rows.append({"path": relative, "sha256": sha256_hex(data)})
    return rows


def _replace_markdown_section(source: str, heading: str, replacement: str) -> str:
    marker = f"## {heading}"
    start = source.find(marker)
    if start < 0:
        raise GalleryError("documentation_gallery_section_missing")
    next_heading = source.find("\n## ", start + len(marker))
    end = len(source) if next_heading < 0 else next_heading + 1
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]


def _detailed_document(
    captures: Sequence[Mapping[str, object]], boards: Sequence[Mapping[str, object]]
) -> str:
    board_hashes = {str(item["board"]): str(item["html_sha256"]) for item in boards}
    lines = [
        "# Proposed canonical research Board Gallery",
        "",
        "> Staging packet only. Public documentation and legacy SVG references are unchanged.",
        "",
        "Each screenshot is synthetic and non-interactive. Codex exact-byte copy, Claude Code local-open, and GitHub static references share the recorded canonical HTML SHA-256.",
        "",
    ]
    for item in captures:
        if item["width"] != 1200:
            continue
        lines.extend(
            (
                f"## {item['board']} · {item['view']}",
                "",
                f"HTML SHA-256: `{board_hashes[str(item['board'])]}`",
                f"PNG SHA-256: `{item['png_sha256']}`",
                "",
                f"![Synthetic {item['board']} {item['view']}]({PUBLIC_GALLERY_PREFIX}/{item['path']})",
                "",
                f"Narrow capture: [{item['width'] if item['width'] == 700 else 700}x840]({PUBLIC_GALLERY_PREFIX}/captures/{BOARD_BY_ID[str(item['board'])].slug}/{CaptureSpec(str(item['board']), BOARD_BY_ID[str(item['board'])].slug, str(item['view']), 700).view_slug}-700x840.png)",
                "",
            )
        )
    return "\n".join(lines)


def _normalize_timing(value: Mapping[str, int | float | str]) -> dict[str, int | float | str]:
    required = {
        "browser_startup_ms",
        "capture_ms",
        "controls_ready_ms",
        "semantic_ready_ms",
    }
    if set(value) != required:
        raise GalleryError("capture_timing_invalid")
    if any(not isinstance(value[key], (int, float)) or value[key] < 0 for key in required):
        raise GalleryError("capture_timing_invalid")
    return dict(value)


def _capture_report(capture: Capture) -> dict[str, object]:
    report = getattr(capture, "report", None)
    if report is None:
        return {"mode": "hermetic_test"}
    value = report()
    if not isinstance(value, dict):
        raise GalleryError("browser_acceptance_invalid")
    return value


def gallery_content_hash(manifest: Mapping[str, object]) -> str:
    """Return the deterministic outer hash for a Gallery manifest."""

    content = copy.deepcopy(dict(manifest))
    content.pop("gallery_content_hash", None)
    return sha256_hex(canonical_json_bytes(content))


def _normalized_reproduction_manifest(manifest: Mapping[str, object]) -> dict[str, object]:
    normalized = copy.deepcopy(dict(manifest))
    normalized.pop("gallery_content_hash", None)
    captures = normalized.get("captures")
    if isinstance(captures, list):
        for capture in captures:
            if isinstance(capture, dict):
                capture.pop("timing", None)
    return normalized


def _verify_file_hash(
    root: Path,
    record: Mapping[str, object],
    path_field: str,
    hash_field: str,
    error_code: str,
) -> None:
    path = _safe_path(root, record.get(path_field))
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise GalleryError(error_code) from exc
    if sha256_hex(data) != record.get(hash_field):
        raise GalleryError(error_code)


def _safe_path(root: Path, relative: object) -> Path:
    if not isinstance(relative, str):
        raise GalleryError("gallery_path_invalid")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise GalleryError("gallery_path_invalid")
    resolved = root.joinpath(*path.parts).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise GalleryError("gallery_path_invalid") from exc
    return resolved


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    checksum = binascii.crc32(kind)
    checksum = binascii.crc32(data, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)


def _read_png_chunks(png: bytes) -> list[tuple[bytes, bytes]]:
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise GalleryError("capture_invalid")
    chunks: list[tuple[bytes, bytes]] = []
    offset = 8
    while offset + 12 <= len(png):
        length = struct.unpack(">I", png[offset : offset + 4])[0]
        end = offset + 12 + length
        if end > len(png):
            raise GalleryError("capture_invalid")
        kind = png[offset + 4 : offset + 8]
        data = png[offset + 8 : offset + 8 + length]
        checksum = struct.unpack(">I", png[offset + 8 + length : end])[0]
        if binascii.crc32(data, binascii.crc32(kind)) & 0xFFFFFFFF != checksum:
            raise GalleryError("capture_invalid")
        chunks.append((kind, data))
        offset = end
        if kind == b"IEND":
            if offset != len(png):
                raise GalleryError("capture_invalid")
            return chunks
    raise GalleryError("capture_invalid")


def _png_predictor(filter_type: int, left: int, above: int, upper_left: int) -> int:
    if filter_type == 0:
        return 0
    if filter_type == 1:
        return left
    if filter_type == 2:
        return above
    if filter_type == 3:
        return (left + above) // 2
    if filter_type == 4:
        estimate = left + above - upper_left
        distances = (abs(estimate - left), abs(estimate - above), abs(estimate - upper_left))
        return (left, above, upper_left)[distances.index(min(distances))]
    raise GalleryError("capture_invalid")
