#!/usr/bin/env python3
"""Regression coverage for consent-gated, capability-only broker discovery."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from broker_capability import (
    CAPABILITY_PROBE_VERSION,
    LONG_BRIDGE_TIMEOUT_SECONDS,
    probe_broker_capabilities,
)
from mars_runtime_config import run_macro_board_from_runtime
from mars_web_capture import capture_mars_direct_web_observations
from macro_preflight import load_field_registry
from runtime_health import build_runtime_health


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "mars-1-0-source-payloads.synthetic.json"
AS_OF = "2026-07-24T00:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def direct_capture():
    payloads = json.loads(FIXTURE.read_text(encoding="utf-8"))
    contract = json.loads(
        (ROOT / "references" / "mars-1-0-observation-source-contracts.json").read_text(
            encoding="utf-8"
        )
    )
    source_urls = {
        field["source_id"]: field["source_url"]
        for field in contract["fields"]
    }
    source_urls[contract["market_session"]["source_id"]] = contract["market_session"]["source_url"]
    source_urls.update(
        {
            source["source_id"]: source["source_url"]
            for source in contract["event_sources"]
        }
    )
    receipts = {
        source_id: {
            "source_url": source_url,
            "opened_at": payloads[source_id]["retrieved_at"],
            "method": "web_search_then_direct_open",
        }
        for source_id, source_url in source_urls.items()
    }
    return capture_mars_direct_web_observations(payloads, receipts, acquired_at=AS_OF)


def main() -> int:
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def longbridge_runner(command, **kwargs):
        calls.append((tuple(command), kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout='{"token":"must-not-persist","connectivity":"ok"}',
            stderr="",
        )

    pending = probe_broker_capabilities(
        read_only_confirmed=False,
        longbridge_runner=longbridge_runner,
        ibkr_probe=lambda: True,
    )
    require(pending["authorization_state"] == "authorization_pending", "consent must be requested first")
    require(pending["capability_probes"] is None, "pending state must not fabricate broker capability")
    require(not calls, "a pending consent state must not invoke Longbridge")

    health = build_runtime_health(Path("/private/nonexistent-mars-runtime"), "2026-07-24", [])
    require(
        health["current_mode"] == "authorization_pending",
        "unprobed broker state must not be labeled dry-run",
    )
    source_notes = {item["id"]: item["note"] for item in health["broker_source_health"]}
    require("not probed" in source_notes["longbridge"], "health must disclose missing capability probe")
    capability_notes = {item["id"]: item["note"] for item in health["source_capability_health"]}
    require(
        "not probed" in capability_notes["longbridge_terminal_cli"],
        "capability health must disclose missing discovery consistently",
    )

    active = probe_broker_capabilities(
        read_only_confirmed=True,
        longbridge_runner=longbridge_runner,
        ibkr_probe=lambda: True,
    )
    require(active["authorization_state"] == "confirmed", "confirmed probe must retain consent state")
    probes = active["capability_probes"]
    require(isinstance(probes, dict), "confirmed probe must return a normalized capability mapping")
    require(
        probes == {
            "longbridge": {"read_only": "available", "probe_version": CAPABILITY_PROBE_VERSION},
            "ibkr": {"read_only": "available", "probe_version": CAPABILITY_PROBE_VERSION},
        },
        "only successful capability-only probes may be available",
    )
    require(
        calls
        == [
            (
                ("longbridge", "check", "--format", "json"),
                {
                    "capture_output": True,
                    "check": False,
                    "text": True,
                    "timeout": LONG_BRIDGE_TIMEOUT_SECONDS,
                },
            )
        ],
        "Longbridge discovery must call only its capability check",
    )
    rendered = json.dumps(active, sort_keys=True)
    require("must-not-persist" not in rendered and "token" not in rendered, "probe output must not retain raw data")

    unavailable = probe_broker_capabilities(
        read_only_confirmed=True,
        longbridge_runner=lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="failure"),
        ibkr_probe=None,
    )
    require(
        unavailable["capability_probes"] == {
            "longbridge": {"read_only": "unavailable", "probe_version": CAPABILITY_PROBE_VERSION},
            "ibkr": {"read_only": "unavailable", "probe_version": CAPABILITY_PROBE_VERSION},
        },
        "failed or task-invisible capabilities must not be treated as authorized",
    )

    with TemporaryDirectory() as temporary:
        setup = run_macro_board_from_runtime(
            Path(temporary) / "mars-runtime", direct_capture(), AS_OF, capability_probes=None
        )
    require(setup.kind == "authorization_required", "first-run Macro must ask before capability discovery")
    require(setup.delivery_packet is None, "authorization prompt must not emit a Board")

    require(load_field_registry()["contract_version"], "fixture seam remains reachable")
    print("mars broker capability selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
