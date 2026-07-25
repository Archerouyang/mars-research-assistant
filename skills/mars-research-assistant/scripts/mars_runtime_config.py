#!/usr/bin/env python3
"""Private, minimal first-run state for Mars broker-personalized workflows."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from broker_capability import CAPABILITY_PROBE_VERSION


CONFIG_FILE_NAME = "mars-runtime-config.json"
CONFIG_SCHEMA_VERSION = "mars-runtime-config-v1"
SKILL_VERSION = "1.0.0"
SUPPORTED_BROKERS = frozenset({"longbridge", "ibkr"})
CONFIG_KEYS = frozenset(
    {
        "schema_version",
        "default_broker",
        "read_only_confirmed",
        "setup_completed_at",
        "skill_version",
        "field_contract_version",
        "capability_probe_version",
        "last_capability_probe_at",
        "capability_status",
    }
)


class CapabilityRecheckRequired(ValueError):
    """Stored private setup no longer proves its single broker capability."""


def configure_first_run(
    runtime_dir: str | Path,
    *,
    default_broker: str,
    read_only_confirmed: bool,
    capability_probes: Mapping[str, Any],
    as_of: str,
    field_contract_version: str,
) -> dict[str, Any]:
    """Write one non-sensitive, explicit default broker choice.

    Callers provide an already obtained capability-only probe. This module
    deliberately never contacts a broker and therefore cannot read positions,
    account identifiers, credentials, or market data during setup.
    """

    timestamp = _parse_timestamp(as_of, "setup_completed_at")
    _require_field_contract_version(field_contract_version)
    statuses = _normalize_capability_probes(capability_probes)
    if default_broker not in SUPPORTED_BROKERS:
        raise ValueError("one_supported_default_broker_required")
    if statuses[default_broker] != "available":
        raise ValueError("default_broker_not_available")
    if read_only_confirmed is not True:
        raise ValueError("read_only_confirmation_required")

    config_path = _config_path(runtime_dir)
    if config_path.exists():
        raise FileExistsError("private_config_already_exists")
    config = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "default_broker": default_broker,
        "read_only_confirmed": True,
        "setup_completed_at": _format_timestamp(timestamp),
        "skill_version": SKILL_VERSION,
        "field_contract_version": field_contract_version,
        "capability_probe_version": CAPABILITY_PROBE_VERSION,
        "last_capability_probe_at": _format_timestamp(timestamp),
        "capability_status": statuses,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(config, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return copy.deepcopy(config)


def run_macro_board_from_runtime(
    runtime_dir: str | Path,
    web_capture: Any,
    as_of: str,
    *,
    capability_probes: Mapping[str, Any] | None = None,
    broker_market_capture: Any | None = None,
    registry: Mapping[str, Any] | None = None,
):
    """Compatibility entry for a field-contract Macro Board.

    A Mars Macro Board uses eligible normalized broker market/macro fields with
    exact public fallbacks. The private runtime broker choice does not authorize
    account access and cannot authorize a holdings display.
    This function never writes the runtime; persistence remains a separate,
    explicit action after a Board has been delivered.
    """

    del runtime_dir, capability_probes
    from macro_preflight import run_macro_board

    return run_macro_board(
        web_capture,
        as_of,
        broker_market_capture=broker_market_capture,
        registry=registry,
    )


def load_private_config(runtime_dir: str | Path) -> dict[str, Any]:
    """Load a private config for explicit inspection without performing I/O elsewhere."""

    path = _config_path(runtime_dir)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CapabilityRecheckRequired("config_json_invalid") from error
    if not isinstance(value, dict) or set(value) != CONFIG_KEYS:
        raise CapabilityRecheckRequired("config_schema_invalid")
    return copy.deepcopy(value)


def _validate_private_config(
    config_path: Path,
    *,
    capability_probes: Mapping[str, Any],
    field_contract_version: str,
) -> None:
    config = load_private_config(config_path.parent)
    _require_field_contract_version(field_contract_version)
    broker = config.get("default_broker")
    if broker not in SUPPORTED_BROKERS:
        raise CapabilityRecheckRequired("default_broker_invalid")
    if config.get("read_only_confirmed") is not True:
        raise CapabilityRecheckRequired("read_only_confirmation_missing")
    if config.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise CapabilityRecheckRequired("config_schema_changed")
    if config.get("skill_version") != SKILL_VERSION:
        raise CapabilityRecheckRequired("skill_version_changed")
    if config.get("field_contract_version") != field_contract_version:
        raise CapabilityRecheckRequired("field_contract_version_changed")
    if config.get("capability_probe_version") != CAPABILITY_PROBE_VERSION:
        raise CapabilityRecheckRequired("capability_probe_contract_changed")
    for timestamp_key in ("setup_completed_at", "last_capability_probe_at"):
        _parse_timestamp(config.get(timestamp_key), timestamp_key)

    current_statuses = _normalize_capability_probes(capability_probes)
    stored_statuses = config.get("capability_status")
    if stored_statuses != current_statuses:
        raise CapabilityRecheckRequired("broker_capability_changed")
    if current_statuses[broker] != "available":
        raise CapabilityRecheckRequired("default_broker_not_available")


def _config_path(runtime_dir: str | Path) -> Path:
    return Path(runtime_dir).expanduser() / CONFIG_FILE_NAME


def _registry_contract_version(registry: Mapping[str, Any] | None) -> str:
    if registry is None:
        from macro_preflight import load_field_registry

        registry = load_field_registry()
    value = registry.get("contract_version") if isinstance(registry, Mapping) else None
    _require_field_contract_version(value)
    return str(value)


def _require_field_contract_version(value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("field_contract_version_invalid")


def _normalize_capability_probes(probes: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(probes, Mapping) or set(probes) != SUPPORTED_BROKERS:
        raise ValueError("read_only_capability_probe_invalid")
    statuses: dict[str, str] = {}
    for broker in sorted(SUPPORTED_BROKERS):
        probe = probes.get(broker)
        if not isinstance(probe, Mapping) or set(probe) != {"read_only", "probe_version"}:
            raise ValueError("read_only_capability_probe_invalid")
        if probe.get("probe_version") != CAPABILITY_PROBE_VERSION:
            raise ValueError("read_only_capability_probe_invalid")
        state = probe.get("read_only")
        if state not in {"available", "unavailable"}:
            raise ValueError("read_only_capability_probe_invalid")
        statuses[broker] = str(state)
    return statuses


def _available_brokers(probes: Mapping[str, Any]) -> tuple[str, ...]:
    statuses = _normalize_capability_probes(probes)
    return tuple(broker for broker in sorted(statuses) if statuses[broker] == "available")


def _display_broker(value: str) -> str:
    return {"ibkr": "IBKR", "longbridge": "Longbridge"}[value]


def _parse_timestamp(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise CapabilityRecheckRequired(f"{field_name}_invalid")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CapabilityRecheckRequired(f"{field_name}_invalid") from error
    if timestamp.tzinfo is None:
        raise CapabilityRecheckRequired(f"{field_name}_invalid")
    return timestamp.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
