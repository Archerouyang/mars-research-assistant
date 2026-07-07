#!/usr/bin/env python3
"""Verify display-first visual artifact behavior and documentation."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo

SPEC = ContractSpec(
    name="visual artifact",
    success_message="visual artifact contract ok",
    failure_header="visual artifact contract failed:",
    files={
        "visual_helpers": FileContract(
            path=ROOT / "scripts" / "visual_artifacts.py",
            required_terms=[
                "display-first",
                ".scratch/visual-artifacts",
                "VisualArtifactRecord",
                "append_manifest",
                "save_manifest",
                "No live broker reads",
                "No live market data calls",
            ],
        ),
        "price_chart": FileContract(
            path=ROOT / "scripts" / "chart_artifact.py",
            required_terms=[
                "--display-output",
                "--save-manifest",
                "render_svg",
                "trigger zone",
                "invalidation",
                "TP/rebalance",
                "display-first",
            ],
        ),
        "macro_chart": FileContract(
            path=ROOT / "scripts" / "macro_regime_artifact.py",
            required_terms=[
                "macro / regime mini-panel",
                "Source Routing Boundary",
                "Longbridge macrodata",
                "official / reputable confirmation",
                "strategy posture",
                "impact path",
                "threshold",
                "delta",
                "reference table",
                "key thresholds",
                "--display-output",
                "No live broker reads",
            ],
        ),
        "selftest": FileContract(
            path=ROOT / "scripts" / "verify_visual_artifact_selftest.py",
            required_terms=[
                "visual artifact selftest ok",
                "chart_artifact.py",
                "macro_regime_artifact.py",
                "artifact-manifest.json",
            ],
        ),
        "macro_fixture": FileContract(
            path=ROOT / "assets" / "fixtures" / "input" / "macro-regime-mini-panel-2026-06-24.json",
            required_terms=[
                "Macro / Regime Mini-Panel",
                "strategy_posture",
                "thresholds",
                "impact_path",
                "10Y",
                "VIX",
                "NDX/RUT",
                "Source Routing Boundary",
            ],
        ),
        "output_templates": FileContract(
            path=ROOT / "skills" / "trading-research" / "references" / "output-templates.md",
            required_terms=[
                "display-first visual",
                "inline price visual",
                "inline macro visual",
                "optional local save",
                "Do not save visual artifacts by default",
            ],
        ),
        "adr": FileContract(
            path=REPO / "docs" / "adr" / "0002-chart-artifacts-not-dashboard.md",
            required_terms=[
                "display-first",
                "transient",
                "optional durable save",
            ],
        ),
        "development_plan": FileContract(
            path=REPO / "docs" / "DEVELOPMENT_PLAN.md",
            required_terms=[
                "Content & Visualization Artifact System MVP",
                "display-first visual artifacts",
            ],
        ),
        "roadmap": FileContract(
            path=REPO / "docs" / "ROADMAP.md",
            required_terms=[
                "Content & Visualization Artifact System MVP",
                "chat-first visual artifacts",
            ],
        ),
        "project_log": FileContract(
            path=REPO / "docs" / "PROJECT_LOG.md",
            required_terms=[
                "2026-07-07",
                "Content & Visualization Artifact System MVP",
            ],
        ),
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
