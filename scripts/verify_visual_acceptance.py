#!/usr/bin/env python3
"""Run the #58 visual, privacy, distribution, and host-evidence gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"
SKILL_SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(SKILL_SCRIPTS))

from canonical_gallery import BOARD_SPECS, GalleryError, verify_gallery  # noqa: E402
from visual_acceptance import (  # noqa: E402
    AcceptanceError,
    generate_public_artifact_corpus,
    run_browser_matrix,
    scan_privacy_corpus,
    scan_privacy_paths,
    scan_static_artifact_apis,
    validate_codex_inline_evidence,
    verify_distribution_mirrors,
    verify_degraded_identity,
    verify_gallery_matches_corpus,
    verify_legacy_visual_inventory,
    write_failure_bundle,
)


FIXTURES = SKILL / "assets" / "fixtures" / "input"
STAGED_GALLERY = REPO / "docs" / "staging" / "canonical-gallery-v1"
INVENTORY = REPO / "docs" / "visual-acceptance" / "legacy-visual-inventory.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--failure-dir", type=Path, required=True)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--codex-evidence", type=Path)
    parser.add_argument("--require-codex-evidence", action="store_true")
    parser.add_argument("--structural-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        corpus_report = generate_public_artifact_corpus(FIXTURES, args.output_dir)
        api_report = scan_static_artifact_apis(args.output_dir)
        degraded_report = verify_degraded_identity(args.output_dir)
        generated_privacy = scan_privacy_corpus(args.output_dir)
        source_fixture_privacy = scan_privacy_paths(_source_fixture_paths(), root=REPO)
        gallery_manifest = verify_gallery(STAGED_GALLERY)
        gallery_renderer = verify_gallery_matches_corpus(
            args.output_dir, STAGED_GALLERY, gallery_manifest
        )
        gallery_privacy = scan_privacy_corpus(STAGED_GALLERY)
        documentation_privacy = scan_privacy_paths(_visual_document_paths(), root=REPO)
        wrapper_report = verify_distribution_mirrors(
            SKILL,
            (REPO / "plugins" / "trading-research-system" / "skills" / "trading-research-system",),
        )
        assets_report = verify_distribution_mirrors(
            SKILL / "assets",
            (REPO / "plugins" / "trading-research-system" / "assets",),
        )
        inventory_report = verify_legacy_visual_inventory(REPO, INVENTORY)
        browser_report: dict[str, object] = {"status": "not_run"}
        if not args.structural_only:
            browser_report = run_browser_matrix(
                corpus_dir=args.output_dir,
                browser_path=args.browser,
                failure_dir=args.failure_dir,
            )

        expected_hashes = {
            row["board"]: row["html_sha256"] for row in gallery_manifest["boards"]
        }
        codex_report: dict[str, object] = {"status": "pending_human_review"}
        if args.codex_evidence is not None:
            evidence = json.loads(args.codex_evidence.read_text(encoding="utf-8"))
            codex_report = validate_codex_inline_evidence(evidence, expected_hashes)
        elif args.require_codex_evidence:
            raise AcceptanceError("codex_inline_evidence_required")

        release_status = (
            "pass" if codex_report.get("status") == "pass" else "pending_human_review"
        )
        report = {
            "automated_status": "pass",
            "browser": browser_report,
            "codex_inline": codex_report,
            "corpus": corpus_report,
            "distribution": {"assets": assets_report, "wrapper": wrapper_report},
            "degraded_identity": degraded_report,
            "gallery": {
                "boards": len(gallery_manifest["boards"]),
                "captures": len(gallery_manifest["captures"]),
                "content_hash": gallery_manifest["gallery_content_hash"],
                "renderer": gallery_renderer,
            },
            "privacy": {
                "documentation": documentation_privacy,
                "gallery": gallery_privacy,
                "generated": generated_privacy,
                "source_fixtures": source_fixture_privacy,
            },
            "static_artifact_apis": api_report,
            "unrelated_visuals": inventory_report,
            "release_status": release_status,
            "status": release_status,
        }
        (args.output_dir / "visual-acceptance-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        if not (args.failure_dir / "failure-report.json").is_file():
            write_failure_bundle(
                args.failure_dir,
                report={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "status": "fail",
                },
                dom_offenders=[],
                manifest_diff={"status": "not_available"},
                screenshots={},
            )
        print(f"visual acceptance failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _visual_document_paths() -> tuple[Path, ...]:
    return (
        REPO / "README.md",
        REPO / "README.zh-CN.md",
        REPO / "docs" / "adr" / "0008-canonical-research-artifact-packets.md",
        REPO / "docs" / "visual-acceptance" / "human-review-checklist.md",
        SKILL / "references" / "artifact-packet-contract.md",
        SKILL / "references" / "visual-acceptance-contract.md",
    )


def _source_fixture_paths() -> tuple[Path, ...]:
    return tuple(
        FIXTURES / f"{spec.fixture_prefix}-{state.replace('_', '-')}.json"
        for spec in BOARD_SPECS
        for state in ("complete", "partial", "stale", "source_error")
    )


if __name__ == "__main__":
    main()
