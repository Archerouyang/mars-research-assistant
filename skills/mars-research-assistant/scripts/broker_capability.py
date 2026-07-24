#!/usr/bin/env python3
"""Consent-gated, capability-only discovery for supported read-only brokers."""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any, Callable, Iterable


CAPABILITY_PROBE_VERSION = "broker-capability-v2"
LONG_BRIDGE_CHECK = ("longbridge", "check", "--format", "json")
LONG_BRIDGE_TIMEOUT_SECONDS = 10
IBKR_TASK_TOOL_PREFIX = "mcp__codex_apps__interactive_brokers__"


def probe_broker_capabilities(
    *,
    read_only_confirmed: bool,
    longbridge_runner: Callable[..., Any] = subprocess.run,
    task_tool_names: Iterable[str] = (),
) -> dict[str, object]:
    """Return normalized capability state without retaining broker responses.

    This is intentionally not an account-data adapter. Longbridge runs only its
    documented connectivity/token check after consent. IBKR has no portable
    credential store; the host supplies only its current task-visible tool names.
    """

    if read_only_confirmed is not True:
        return {
            "authorization_state": "authorization_pending",
            "capability_probes": None,
        }

    return {
        "authorization_state": "confirmed",
        "capability_probes": {
            "longbridge": _capability_probe(_probe_longbridge(longbridge_runner)),
            "ibkr": _capability_probe(_probe_ibkr(task_tool_names)),
        },
    }


def _capability_probe(status: str) -> dict[str, str]:
    return {"read_only": status, "probe_version": CAPABILITY_PROBE_VERSION}


def _probe_longbridge(longbridge_runner: Callable[..., Any]) -> str:
    try:
        completed = longbridge_runner(
            list(LONG_BRIDGE_CHECK),
            capture_output=True,
            check=False,
            text=True,
            timeout=LONG_BRIDGE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    return "available" if getattr(completed, "returncode", 1) == 0 else "unavailable"


def _probe_ibkr(task_tool_names: Iterable[str]) -> str:
    for name in task_tool_names:
        if isinstance(name, str) and name.startswith(IBKR_TASK_TOOL_PREFIX):
            return "available"
    return "unavailable"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run consent-gated, capability-only broker checks without reading account data."
    )
    parser.add_argument(
        "--confirm-read-only",
        action="store_true",
        help="Required before the Longbridge capability check is invoked.",
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
        read_only_confirmed=args.confirm_read_only,
        task_tool_names=args.task_tool,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
