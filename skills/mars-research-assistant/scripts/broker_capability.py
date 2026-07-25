#!/usr/bin/env python3
"""Capability-only discovery for the supported IBKR provider."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from ibkr_provider import PROVIDER_ID, capability_statuses


CAPABILITY_PROBE_VERSION = "broker-capability-v3"


def probe_broker_capabilities(
    *,
    task_tool_names: Iterable[str] = (),
) -> dict[str, object]:
    """Return IBKR capability state without reading any broker payload."""

    return {
        "capability_state": "checked",
        "capability_probes": {
            PROVIDER_ID: _capability_probe(capability_statuses(task_tool_names)),
        },
    }


def _capability_probe(statuses: dict[str, str]) -> dict[str, str]:
    return {**statuses, "probe_version": CAPABILITY_PROBE_VERSION}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run capability-only broker checks without reading account data."
    )
    parser.add_argument(
        "--task-tool",
        action="append",
        default=[],
        metavar="TOOL_NAME",
        help="Host-supplied task tool name; use only names visible in the current Codex task.",
    )
    parser.add_argument("--format", choices=("json",), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = probe_broker_capabilities(
        task_tool_names=args.task_tool,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
