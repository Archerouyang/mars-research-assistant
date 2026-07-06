#!/usr/bin/env python3
"""Verify source routing separates broker, market, macrodata, news, and research."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
REFERENCES = ROOT / "skills" / "trading-research" / "references"
TEMPLATES = ROOT / "assets" / "templates"

FILES = {
    "context": REPO / "CONTEXT.md",
    "macro_policy_filter": REFERENCES / "macro-policy-filter.md",
    "output_templates": REFERENCES / "output-templates.md",
    "broker_contract": REFERENCES / "broker-data-contract.md",
    "orchestrator": REFERENCES / "daily-ops-orchestrator.md",
    "weekly_skill": ROOT / "skills" / "weekly-trading-plan" / "SKILL.md",
    "macro_skill": ROOT / "skills" / "macro-equity-research" / "SKILL.md",
    "macro_monitor": TEMPLATES / "automation-macro-industry-research-monitor.md",
    "fixture_expected": ROOT
    / "assets"
    / "fixtures"
    / "expected"
    / "source-routing-longbridge-boundary.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "context": [
        "Source Routing Boundary",
        "Longbridge macrodata",
        "Longbridge broker source",
        "news source",
        "does not make Longbridge the default source for news",
    ],
    "macro_policy_filter": [
        "Source Routing Boundary",
        "Choose sources by claim type",
        "Longbridge `macrodata` is S1 macro/financial data",
        "Longbridge broker or market data is not a news source",
        "Selecting Longbridge for stock data does not make Longbridge the default source for macro, policy, industry, or news analysis",
        "Macro policy facts require S0",
        "Industry news leads require S2 or authorized research",
        "Do not use one connector as the exclusive evidence layer",
    ],
    "output_templates": [
        "Source Routing Boundary",
        "source purpose",
        "official policy facts",
        "market data / macrodata",
        "news leads",
        "research thesis",
        "broker/account facts",
        "Longbridge selection for one purpose does not override the source mix for other purposes",
    ],
    "broker_contract": [
        "Longbridge `macrodata` is a separate macro-data source",
        "Do not make Longbridge market data a first-phase hard dependency",
        "Longbridge broker source does not become the source for macro policy or industry news",
    ],
    "orchestrator": [
        "Source Routing Boundary",
        "source purpose",
        "Do not reuse broker-source selection as news-source selection",
        "Longbridge macrodata can support macro values but cannot replace official or reputable news sources",
    ],
    "weekly_skill": [
        "Source Routing Boundary",
        "Choose sources by claim type",
        "Selecting Longbridge for stock data does not make Longbridge the default source for macro, policy, industry, or news analysis",
    ],
    "macro_skill": [
        "Source Routing Boundary",
        "Choose sources by claim type",
        "Longbridge `macrodata` can be used for macro and financial-condition reads",
        "not as the exclusive source for macro, policy, industry, or news analysis",
    ],
    "macro_monitor": [
        "Source Routing Boundary",
        "public/authorized sources",
        "Longbridge macrodata",
        "official or reputable sources",
        "not use Longbridge as the only source",
    ],
    "fixture_expected": [
        "Source Routing Boundary",
        "Longbridge stock data selected",
        "not sufficient for policy/news",
        "S0 official",
        "S1 macrodata",
        "S2 reputable media",
        "S3 research",
        "allowed source mix",
    ],
    "roadmap": [
        "Source Routing Boundary",
        "Longbridge macrodata",
        "not become the default source for news",
    ],
    "development_plan": [
        "Source Routing Boundary",
        "Longbridge macrodata",
        "not become the default source for news",
    ],
    "project_log": [
        "Source Routing Boundary",
        "Longbridge macrodata",
        "not become the default source for news",
    ],
}

SPEC = ContractSpec(
    name="source routing boundary",
    success_message="source routing contract ok",
    failure_header="source routing contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
