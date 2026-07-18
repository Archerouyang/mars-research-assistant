#!/usr/bin/env python3
"""Contract tests for the canonical visual acceptance release gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from visual_acceptance import (  # noqa: E402
    AcceptanceError,
    build_acceptance_matrix,
    generate_public_artifact_corpus,
    scan_privacy_corpus,
    scan_privacy_paths,
    scan_static_artifact_apis,
    validate_codex_inline_evidence,
    validate_matrix_results,
    verify_distribution_mirrors,
    verify_degraded_identity,
    verify_gallery_matches_corpus,
    verify_legacy_visual_inventory,
    write_failure_bundle,
    run_browser_matrix,
)


class VisualAcceptanceSelftest(unittest.TestCase):
    maxDiff = None

    def test_matrix_has_approved_complete_degraded_dark_and_gallery_counts(self) -> None:
        matrix = build_acceptance_matrix()

        self.assertEqual(len(matrix["complete"]), 60)
        self.assertEqual(len(matrix["degraded"]), 90)
        self.assertEqual(len(matrix["gallery"]), 12)
        self.assertEqual(len(matrix["dark"]), 48)
        self.assertEqual(
            {case["width"] for case in matrix["complete"]},
            {1200, 700, 736, 320},
        )
        self.assertEqual(
            {case["state"] for case in matrix["degraded"]},
            {"partial", "stale", "source_error"},
        )
        self.assertEqual(
            {case["width"] for case in matrix["degraded"]},
            {736, 320},
        )

    def test_privacy_scan_covers_text_json_html_manifest_and_png_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe_files = {
                "snapshot.json": '{"privacy":"public_fixture"}',
                "board.html": "<html><body>synthetic fixture</body></html>",
                "gallery.manifest.json": '{"public_cutover":"not_performed"}',
                "README.md": "Public synthetic visual fixture.",
            }
            for name, content in safe_files.items():
                (root / name).write_text(content, encoding="utf-8")
            (root / "capture.png").write_bytes(
                b"\x89PNG\r\n\x1a\npublic synthetic metadata"
            )

            report = scan_privacy_corpus(root)
            self.assertEqual(report["files_scanned"], 5)
            self.assertEqual(report["findings"], [])

            sentinels = {
                "snapshot.json": '"account_id":"PRIVATE-ACCOUNT-999"',
                "board.html": "/Users/private/trading/runtime",
                "gallery.manifest.json": '"token":"ghp_private_sentinel"',
                "README.md": "broker_raw_response: private sentinel",
                "capture.png": "api_secret=private-sentinel",
            }
            for name, sentinel in sentinels.items():
                path = root / name
                if path.suffix == ".png":
                    path.write_bytes(b"\x89PNG\r\n\x1a\n" + sentinel.encode())
                else:
                    path.write_text(sentinel, encoding="utf-8")
                with self.subTest(name=name):
                    with self.assertRaisesRegex(AcceptanceError, "privacy_scan_failed"):
                        scan_privacy_corpus(root)
                if path.suffix == ".png":
                    path.write_bytes(b"\x89PNG\r\n\x1a\npublic synthetic metadata")
                else:
                    path.write_text(safe_files[name], encoding="utf-8")

    def test_failure_bundle_preserves_required_machine_and_visual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "failure"
            write_failure_bundle(
                root,
                report={"status": "fail", "errors": ["overflow"]},
                dom_offenders=[{"selector": "#critical", "reason": "clipped"}],
                manifest_diff={"missing": ["capture.png"]},
                screenshots={"portfolio-risk-320.png": b"synthetic screenshot"},
            )

            self.assertTrue((root / "failure-report.json").is_file())
            self.assertTrue((root / "dom-offenders.json").is_file())
            self.assertTrue((root / "manifest-diff.json").is_file())
            self.assertEqual(
                (root / "screenshots" / "portfolio-risk-320.png").read_bytes(),
                b"synthetic screenshot",
            )

    def test_browser_launch_failure_preserves_diagnostic_bundle(self) -> None:
        class FailingChromium:
            @staticmethod
            def launch(**_kwargs: object) -> object:
                raise RuntimeError("synthetic browser launch failure")

        class FakePlaywright:
            chromium = FailingChromium()

        class FakeManager:
            def __enter__(self) -> FakePlaywright:
                return FakePlaywright()

            def __exit__(self, *_args: object) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            failure_dir = root / "failure"
            with self.assertRaisesRegex(
                AcceptanceError, "browser_acceptance_infrastructure_failed"
            ):
                run_browser_matrix(
                    corpus_dir=root / "unused-corpus",
                    browser_path=None,
                    failure_dir=failure_dir,
                    playwright_factory=FakeManager,
                )
            report = json.loads(
                (failure_dir / "failure-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "fail")
            self.assertEqual(
                report["failures"][0]["infrastructure"],
                "browser_acceptance_infrastructure_failed",
            )

    def test_source_fixture_privacy_allowlist_rejects_injected_private_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = []
            for index in range(12):
                path = root / f"fixture-{index}.json"
                path.write_text('{"privacy":"public_fixture"}', encoding="utf-8")
                fixtures.append(path)
            self.assertEqual(
                scan_privacy_paths(fixtures, root=root)["files_scanned"],
                12,
            )
            fixtures[-1].write_text(
                '{"account_id":"PRIVATE-ACCOUNT-999"}', encoding="utf-8"
            )
            with self.assertRaisesRegex(AcceptanceError, "privacy_scan_failed"):
                scan_privacy_paths(fixtures, root=root)

    def test_codex_inline_evidence_requires_exact_hashes_and_rejects_wrapper(self) -> None:
        expected = {
            "instrument_research": "1" * 64,
            "macro_regime": "2" * 64,
            "portfolio_risk": "3" * 64,
        }
        records = []
        for board, html_sha256 in expected.items():
            records.append(
                {
                    "board": board,
                    "host": "codex_inline",
                    "browser_wrapper": False,
                    "html_sha256": html_sha256,
                    "default_view": "Overview",
                    "all_views_switched": True,
                    "keyboard_pass": True,
                    "responsive_pass": True,
                    "page_errors": [],
                    "external_requests": [],
                    "reviewer": "human-reviewer",
                    "reviewed_at": "2026-07-18T10:00:00Z",
                }
            )

        report = validate_codex_inline_evidence({"records": records}, expected)
        self.assertEqual(report["boards_checked"], 3)

        records[0]["browser_wrapper"] = True
        with self.assertRaisesRegex(AcceptanceError, "codex_inline_evidence_invalid"):
            validate_codex_inline_evidence({"records": records}, expected)

    def test_legacy_visual_inventory_is_hash_pinned_and_detects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = root / "legacy.svg"
            asset.write_text("<svg></svg>", encoding="utf-8")
            readme = root / "README.md"
            readme.write_text("```mermaid\ngraph TD\n```\n", encoding="utf-8")
            inventory = {
                "files": [
                    {
                        "path": "legacy.svg",
                        "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
                    },
                    {
                        "path": "README.md",
                        "sha256": hashlib.sha256(readme.read_bytes()).hexdigest(),
                    },
                ]
            }
            inventory_path = root / "inventory.json"
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

            report = verify_legacy_visual_inventory(root, inventory_path)
            self.assertEqual(report["files_checked"], 2)

            asset.write_text("<svg><text>changed</text></svg>", encoding="utf-8")
            with self.assertRaisesRegex(AcceptanceError, "legacy_visual_inventory_mismatch"):
                verify_legacy_visual_inventory(root, inventory_path)

    def test_public_corpus_generation_requires_fresh_output_and_emits_twelve_packets(self) -> None:
        fixtures = (
            REPO
            / "skills"
            / "trading-research-system"
            / "assets"
            / "fixtures"
            / "input"
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "public-corpus"
            report = generate_public_artifact_corpus(fixtures, output)

            self.assertEqual(report["packets"], 12)
            self.assertEqual(report["boards"], 3)
            self.assertEqual(report["states"], 4)
            self.assertEqual(len(list(output.rglob("research-brief.html"))), 12)
            self.assertEqual(len(list(output.rglob("snapshot.canonical.json"))), 12)
            self.assertEqual(len(list(output.rglob("artifact.manifest.json"))), 12)

            with self.assertRaisesRegex(AcceptanceError, "output_not_fresh"):
                generate_public_artifact_corpus(fixtures, output)

    def test_static_artifact_api_scan_fails_for_network_runtime_broker_and_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "research-brief.html"
            html.write_text("<html><script>const fixture = 'public';</script></html>", encoding="utf-8")
            self.assertEqual(scan_static_artifact_apis(root)["files_scanned"], 1)

            forbidden = (
                "fetch('/live')",
                "new XMLHttpRequest()",
                "new WebSocket('wss://broker')",
                "runtime_health()",
                "broker.get_positions()",
                "placeOrder({symbol:'TSM'})",
            )
            for expression in forbidden:
                with self.subTest(expression=expression):
                    html.write_text(f"<script>{expression}</script>", encoding="utf-8")
                    with self.assertRaisesRegex(AcceptanceError, "forbidden_artifact_api"):
                        scan_static_artifact_apis(root)

    def test_distribution_mirror_check_is_recursive_and_byte_exact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "canonical"
            mirror_a = root / "mirror-a"
            mirror_b = root / "mirror-b"
            for target in (canonical, mirror_a, mirror_b):
                (target / "references").mkdir(parents=True)
                (target / "references" / "visual.md").write_text("contract\n", encoding="utf-8")

            report = verify_distribution_mirrors(canonical, (mirror_a, mirror_b))
            self.assertEqual(report["mirrors_checked"], 2)

            (mirror_b / "references" / "visual.md").write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(AcceptanceError, "distribution_mirror_mismatch"):
                verify_distribution_mirrors(canonical, (mirror_a, mirror_b))

    def test_matrix_result_validation_requires_every_approved_identity(self) -> None:
        matrix = build_acceptance_matrix()
        results = {
            group: [{**case, "status": "pass"} for case in cases]
            for group, cases in matrix.items()
            if group != "gallery"
        }
        report = validate_matrix_results(results)
        self.assertEqual(report["complete"], 60)
        self.assertEqual(report["degraded"], 90)
        self.assertEqual(report["dark"], 48)

        results["degraded"].pop()
        with self.assertRaisesRegex(AcceptanceError, "browser_matrix_incomplete"):
            validate_matrix_results(results)

    def test_staged_gallery_html_must_match_fresh_complete_corpus_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus"
            gallery = root / "gallery"
            boards = []
            for board, slug in (
                ("instrument_research", "instrument-research"),
                ("macro_regime", "macro-regime"),
                ("portfolio_risk", "portfolio-risk"),
            ):
                current = corpus / slug / "complete" / "research-brief.html"
                staged = gallery / "artifacts" / slug / "research-brief.html"
                current.parent.mkdir(parents=True)
                staged.parent.mkdir(parents=True)
                current.write_bytes(board.encode())
                staged.write_bytes(board.encode())
                boards.append(
                    {
                        "board": board,
                        "html_path": f"artifacts/{slug}/research-brief.html",
                    }
                )

            report = verify_gallery_matches_corpus(corpus, gallery, {"boards": boards})
            self.assertEqual(report["boards_checked"], 3)

            (gallery / boards[0]["html_path"]).write_bytes(b"stale")
            with self.assertRaisesRegex(AcceptanceError, "gallery_renderer_drift"):
                verify_gallery_matches_corpus(corpus, gallery, {"boards": boards})

    def test_degraded_artifacts_cannot_substitute_complete_html(self) -> None:
        fixtures = (
            REPO
            / "skills"
            / "trading-research-system"
            / "assets"
            / "fixtures"
            / "input"
        )
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus"
            generate_public_artifact_corpus(fixtures, corpus)
            report = verify_degraded_identity(corpus)
            self.assertEqual(report["artifacts_checked"], 9)

            complete = corpus / "instrument-research" / "complete" / "research-brief.html"
            stale = corpus / "instrument-research" / "stale" / "research-brief.html"
            stale.write_bytes(complete.read_bytes())
            with self.assertRaisesRegex(AcceptanceError, "stale_fallback_substitution"):
                verify_degraded_identity(corpus)


if __name__ == "__main__":
    unittest.main()
