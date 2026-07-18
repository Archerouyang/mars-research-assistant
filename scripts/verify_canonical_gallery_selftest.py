#!/usr/bin/env python3
"""Contract tests for the staged cross-host canonical Gallery packet."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
import zlib


REPO = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO / "skills" / "trading-research-system" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from canonical_gallery import (  # noqa: E402
    APPROVED_CAPTURES,
    BOARD_SPECS,
    GalleryError,
    copy_exact_html,
    create_test_png,
    gallery_content_hash,
    stage_gallery,
    validate_fixture_corpus,
    verify_gallery,
    verify_reproduced_gallery,
)


FIXTURES = REPO / "skills" / "trading-research-system" / "assets" / "fixtures" / "input"


def deterministic_capture(spec, _html):
    return create_test_png(
        spec.width,
        spec.height,
        board=spec.board_id,
        view=spec.view,
    ), {
        "browser_startup_ms": 1,
        "capture_ms": 1,
        "controls_ready_ms": 1,
        "semantic_ready_ms": 1,
    }


def add_png_text_chunk(png: bytes) -> bytes:
    payload = b"review\x00coordinated-tamper"
    chunk_type = b"tEXt"
    chunk = struct.pack(">I", len(payload)) + chunk_type + payload
    chunk += struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
    return png[:-12] + chunk + png[-12:]


class CanonicalGallerySelftest(unittest.TestCase):
    maxDiff = None

    def test_corpus_covers_every_board_state_and_all_fifteen_views(self) -> None:
        report = validate_fixture_corpus(FIXTURES)

        self.assertEqual(report["snapshot_count"], 12)
        self.assertEqual(report["complete_view_count"], 15)
        self.assertEqual(
            report["states_by_board"],
            {
                spec.board_id: ["complete", "partial", "source_error", "stale"]
                for spec in BOARD_SPECS
            },
        )
        self.assertTrue(all(item["privacy"] == "public_fixture" for item in report["snapshots"]))
        self.assertTrue(all(item["snapshot_bytes"] <= 1536 * 1024 for item in report["snapshots"]))
        self.assertTrue(all(item["html_bytes"] <= 4 * 1024 * 1024 for item in report["snapshots"]))

    def test_stage_links_one_html_identity_across_hosts_and_twelve_captures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "canonical-gallery"
            stage_gallery(
                fixtures_dir=FIXTURES,
                output_dir=output,
                capture=deterministic_capture,
                documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
            )

            manifest = verify_gallery(output)
            self.assertEqual(len(manifest["captures"]), 12)
            self.assertEqual(
                {(row["board"], row["view"], row["width"], row["height"]) for row in manifest["captures"]},
                {(item.board_id, item.view, item.width, item.height) for item in APPROVED_CAPTURES},
            )
            for board in manifest["boards"]:
                hosts = board["host_delivery"]
                hashes = {
                    hosts["codex"]["html_sha256"],
                    hosts["claude_code"]["html_sha256"],
                    hosts["github"]["html_sha256"],
                    board["html_sha256"],
                }
                self.assertEqual(len(hashes), 1)
                self.assertEqual(hosts["codex"]["mode"], "exact_byte_copy")
                self.assertEqual(hosts["claude_code"]["mode"], "local_open")
                self.assertEqual(hosts["github"]["mode"], "hash_linked_static")

                copied = Path(tmp) / f"{board['board']}.html"
                copy_exact_html(output, board["board"], copied)
                canonical = output / board["html_path"]
                self.assertEqual(copied.read_bytes(), canonical.read_bytes())

            self.assertTrue((output / "proposals" / "README.proposed.md").is_file())
            self.assertTrue((output / "proposals" / "README.zh-CN.proposed.md").is_file())
            self.assertTrue((output / "proposals" / "canonical-research-boards.proposed.md").is_file())
            self.assertEqual(manifest["public_cutover"], "not_performed")
            proposal = (output / "proposals" / "README.proposed.md").read_text(encoding="utf-8")
            self.assertNotIn("docs/assets/readme/macro-regime-panel.svg", proposal)
            self.assertEqual(proposal.count("## Proposed Canonical Research Board Gallery"), 1)

    def test_stage_is_fresh_and_atomic_and_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "canonical-gallery"
            output.mkdir()
            (output / "foreign.txt").write_text("keep", encoding="utf-8")

            with self.assertRaisesRegex(GalleryError, "output_not_fresh"):
                stage_gallery(
                    fixtures_dir=FIXTURES,
                    output_dir=output,
                    capture=deterministic_capture,
                    documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
                )
            self.assertEqual((output / "foreign.txt").read_text(encoding="utf-8"), "keep")

            shutil.rmtree(output)
            stage_gallery(
                fixtures_dir=FIXTURES,
                output_dir=output,
                capture=deterministic_capture,
                documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
            )
            manifest = json.loads((output / "gallery.manifest.json").read_text(encoding="utf-8"))
            capture_path = output / manifest["captures"][0]["path"]
            capture_path.write_bytes(capture_path.read_bytes() + b"direct replacement")
            with self.assertRaisesRegex(GalleryError, "capture_hash_mismatch"):
                verify_gallery(output)

            capture_path.write_bytes(create_test_png(
                manifest["captures"][0]["width"],
                manifest["captures"][0]["height"],
                board=manifest["captures"][0]["board"],
                view=manifest["captures"][0]["view"],
            ))
            edited = json.loads((output / "gallery.manifest.json").read_text(encoding="utf-8"))
            edited["captures"][0]["png_sha256"] = "0" * 64
            (output / "gallery.manifest.json").write_text(
                json.dumps(edited, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(GalleryError, "gallery_content_hash_mismatch"):
                verify_gallery(output)

            shutil.rmtree(output)
            stage_gallery(
                fixtures_dir=FIXTURES,
                output_dir=output,
                capture=deterministic_capture,
                documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
            )
            coordinated = json.loads((output / "gallery.manifest.json").read_text(encoding="utf-8"))
            row = coordinated["captures"][0]
            capture_path = output / row["path"]
            altered = add_png_text_chunk(capture_path.read_bytes())
            capture_path.write_bytes(altered)
            row["png_sha256"] = hashlib.sha256(altered).hexdigest()
            row["png_bytes"] = len(altered)
            coordinated["gallery_content_hash"] = gallery_content_hash(coordinated)
            (output / "gallery.manifest.json").write_text(
                json.dumps(coordinated, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            verify_gallery(output)
            with self.assertRaisesRegex(GalleryError, "gallery_reproduction_mismatch"):
                verify_reproduced_gallery(
                    output_dir=output,
                    fixtures_dir=FIXTURES,
                    capture=deterministic_capture,
                    documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
                )

            shutil.rmtree(output)
            stage_gallery(
                fixtures_dir=FIXTURES,
                output_dir=output,
                capture=deterministic_capture,
                documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
            )
            corpus_edit = json.loads((output / "gallery.manifest.json").read_text(encoding="utf-8"))
            corpus_edit["corpus"]["snapshots"][0]["fixture_sha256"] = "f" * 64
            corpus_edit["gallery_content_hash"] = gallery_content_hash(corpus_edit)
            (output / "gallery.manifest.json").write_text(
                json.dumps(corpus_edit, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            verify_gallery(output)
            with self.assertRaisesRegex(GalleryError, "gallery_reproduction_mismatch"):
                verify_reproduced_gallery(
                    output_dir=output,
                    fixtures_dir=FIXTURES,
                    capture=deterministic_capture,
                    documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
                )

            extra = output / "unlisted.txt"
            extra.write_text("not in manifest", encoding="utf-8")
            with self.assertRaisesRegex(GalleryError, "gallery_inventory_invalid"):
                verify_gallery(output)
            extra.unlink()
            manifest_path = output / "gallery.manifest.json"
            manifest_path.write_bytes(manifest_path.read_bytes() + b" " * (64 * 1024))
            with self.assertRaisesRegex(GalleryError, "gallery_manifest_size_exceeded"):
                verify_gallery(output)


if __name__ == "__main__":
    unittest.main()
