#!/usr/bin/env python3
"""Black-box smoke for Mars first-run read-only broker configuration."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from mars_runtime_config import (
    CONFIG_FILE_NAME,
    configure_first_run,
    run_macro_board_from_runtime,
)
from mars_web_capture import capture_mars_direct_web_observations
from macro_preflight import load_field_registry


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "mars-1-0-source-payloads.synthetic.json"
AS_OF = "2026-07-23T22:00:00Z"


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
    capabilities = {
        "longbridge": {"read_only": "available", "probe_version": "broker-capability-v1"},
        "ibkr": {"read_only": "unavailable", "probe_version": "broker-capability-v1"},
    }
    with TemporaryDirectory() as temporary:
        runtime = Path(temporary) / "mars-runtime"
        setup = run_macro_board_from_runtime(
            runtime, direct_capture(), AS_OF, capability_probes=capabilities
        )
        require(setup.kind == "setup_required", "missing private setup must stop before Board creation")
        require(setup.delivery_packet is None, "setup guidance must not emit a Board")

        config = configure_first_run(
            runtime,
            default_broker="longbridge",
            read_only_confirmed=True,
            capability_probes=capabilities,
            as_of=AS_OF,
            field_contract_version=load_field_registry()["contract_version"],
        )
        config_path = runtime / CONFIG_FILE_NAME
        require(config_path.is_file(), "first-run setup must write only the private config")
        rendered = config_path.read_text(encoding="utf-8").casefold()
        require(
            not any(term in rendered for term in ("token", "credential", "account", "position", "payload")),
            "private config must not retain secrets, account data, or market payloads",
        )
        require(config["default_broker"] == "longbridge", "one explicit broker must be retained")
        require(config["read_only_confirmed"] is True, "read-only confirmation must be persisted")

        allowed = run_macro_board_from_runtime(
            runtime, direct_capture(), AS_OF, capability_probes=capabilities
        )
        require(allowed.kind == "board", "configured direct-source run must reach the existing Board seam")
        require(allowed.delivery_packet is not None, "configured run must produce a standalone Board packet")

        changed_contract = dict(load_field_registry())
        changed_contract["contract_version"] = "macro-v2"
        recheck = run_macro_board_from_runtime(
            runtime,
            direct_capture(),
            AS_OF,
            capability_probes=capabilities,
            registry=changed_contract,
        )
        require(
            recheck.kind == "capability_recheck_required",
            "a field-contract change must require explicit capability recheck",
        )
        require(recheck.delivery_packet is None, "capability recheck must not emit a Board")

        try:
            configure_first_run(
                Path(temporary) / "invalid",
                default_broker="ibkr",
                read_only_confirmed=True,
                capability_probes=capabilities,
                as_of=AS_OF,
                field_contract_version="macro-v1",
            )
        except ValueError as error:
            require(str(error) == "default_broker_not_available", "unavailable broker must be rejected")
        else:
            raise AssertionError("unavailable broker must not become the default")

    print("mars runtime config selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
