#!/usr/bin/env python3
"""Shared validation, serialization, safety, and immutable-write packet core.

This module has no Board-registry or adapter dependency. It never reads a live
source, private runtime state, or host environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping



SCHEMA_VERSION = "1.0"
RENDERER_VERSION = "1.0"
MANIFEST_VERSION = "1.0"
SNAPSHOT_HARD_LIMIT_BYTES = 1536 * 1024
HTML_HARD_LIMIT_BYTES = 4 * 1024 * 1024
MANIFEST_HARD_LIMIT_BYTES = 64 * 1024
PRESENTATION_STATES = frozenset(
    {"ready", "static_fallback", "missing_artifact", "invalid_artifact", "capture_mismatch"}
)
EVIDENCE_STATES = frozenset({"complete", "partial", "stale", "source_error"})
FRESHNESS_POLICIES: Mapping[str, timedelta | None] = {
    "official-current-v1": None,
    "event-calendar-v1": timedelta(hours=24),
    "intraday-market-v1": timedelta(minutes=15),
}
PRIVACY_SENTINELS = (
    "/Users/",
    "BEGIN PRIVATE KEY",
    "api_key",
    "password",
    "account_id",
    "broker_response",
    "private_runtime",
    ".codex",
)
PUBLIC_PRIVACY_COMPACT_SENTINELS = frozenset(
    {
        "accountid",
        "accountnumber",
        "credential",
        "secret",
        "token",
        "apikey",
        "privatekey",
        "rawbrokerresponse",
        "brokerresponse",
        "privateplan",
        "privateposition",
        "userchart",
        "usergeneratedchart",
    }
)
PUBLIC_PRIVATE_PATH_PATTERN = re.compile(r"(?:^|/)(?:users|home|\.ssh|\.codex)(?:/|$)", re.IGNORECASE)
BROKER_ACCOUNT_ID_PATTERN = re.compile(r"\b(?:DU|U)\d{5,}\b", re.IGNORECASE)
UNSAFE_DIAGNOSTIC_TERMS = ("traceback", "stack trace", "/Users/", "api_key", "password", "token")
DIAGNOSTIC_SEVERITIES = frozenset({"info", "warning", "error"})
DIAGNOSTIC_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
SAFE_TEXT_FORBIDDEN_TERMS = UNSAFE_DIAGNOSTIC_TERMS + (
    "raw response",
    "credential",
    "authorization",
    "bearer ",
    "full account",
)
ACCOUNT_ID_PATTERN = re.compile(r"\b(?:\d[ -]?){7,}\d\b")
FORBIDDEN_SNAPSHOT_TERMS = (
    "fetch(",
    "xmlhttprequest",
    "websocket",
    "http://",
    "https://",
    "cdn",
    "telemetry",
    "broker",
    "runtime",
    "order action",
)
FORBIDDEN_HTML_TERMS = (
    'src="http',
    "src='http",
    'src="//',
    "src='//",
    'href="http',
    "href='http",
    "fetch(",
    "xmlhttprequest",
    "websocket",
    "telemetry",
    "order action",
)
SNAPSHOT_V1_FIELDS = frozenset(
    {
        "artifact_lifecycle",
        "board",
        "builder",
        "content_hash",
        "coverage",
        "decision_cutoff",
        "diagnostics",
        "evidence_state",
        "locale",
        "payload",
        "payload_version",
        "privacy",
        "renderer_version",
        "schema_version",
        "snapshot_id",
        "source_registry",
        "state_reasons",
        "timezone",
    }
)
BUILDER_V1_FIELDS = frozenset({"generated_at", "id"})
COVERAGE_V1_FIELDS = frozenset({"required_complete", "required_total"})
MODULE_V1_FIELDS = frozenset(
    {
        "as_of",
        "data",
        "evidence_state",
        "freshness_policy_id",
        "gap_reason",
        "id",
        "requirement",
        "source_refs",
        "summary",
    }
)
SOURCE_V1_FIELDS = frozenset({"alias", "as_of", "freshness_policy_id", "freshness_status", "id", "priority"})


class ArtifactPacketError(ValueError):
    """A fail-closed public error code without sensitive input details."""


@dataclass(frozen=True)
class ArtifactPacket:
    """Exact bytes returned by the artifact-packet public interface."""

    canonical_json: bytes
    html: bytes
    manifest: bytes


ValidatePayload = Callable[[Mapping[str, Any]], None]
RenderBoard = Callable[[Mapping[str, Any], str, str], bytes]


@dataclass(frozen=True)
class BoardAdapter:
    """The consumed contract for one statically registered Board adapter."""

    board_id: str
    payload_version: str
    validate_payload: ValidatePayload
    render: RenderBoard
    allowed_modules: frozenset[str]
    freshness_policies: Mapping[str, timedelta | None]
    allowed_snapshot_action_terms: frozenset[str] = frozenset()


def validate_snapshot(
    snapshot: Mapping[str, Any],
    adapter: BoardAdapter,
) -> dict[str, Any]:
    """Validate the shared envelope, then delegate Board payload policy."""

    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    normalized = copy.deepcopy(dict(snapshot))
    if normalized.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactPacketError("schema_version_invalid")
    if normalized.get("board") != adapter.board_id:
        raise ArtifactPacketError("board_invalid")
    if normalized.get("payload_version") != adapter.payload_version:
        raise ArtifactPacketError("payload_version_invalid")
    if normalized.get("renderer_version") != RENDERER_VERSION:
        raise ArtifactPacketError("renderer_version_invalid")
    if normalized.get("privacy") not in {"public_fixture", "private_runtime"}:
        raise ArtifactPacketError("privacy_invalid")
    if normalized.get("artifact_lifecycle") not in {"transient", "durable"}:
        raise ArtifactPacketError("artifact_lifecycle_invalid")
    _validate_public_privacy(normalized)
    _validate_snapshot_action_safety(
        normalized,
        adapter.allowed_snapshot_action_terms,
    )
    _validate_common_field_sets(normalized)
    payload = normalized.get("payload")
    if not isinstance(payload, dict):
        raise ArtifactPacketError("payload_invalid")
    if payload.get("board") != normalized["board"]:
        raise ArtifactPacketError("board_mismatch")
    if payload.get("payload_version") != normalized["payload_version"]:
        raise ArtifactPacketError("payload_version_mismatch")
    if not _is_nonempty_string(normalized.get("snapshot_id")):
        raise ArtifactPacketError("snapshot_id_invalid")
    _parse_timestamp(normalized.get("decision_cutoff"), "decision_cutoff_invalid")
    _validate_envelope_fields(normalized)
    _require_size(canonical_json_bytes(normalized), SNAPSHOT_HARD_LIMIT_BYTES, "snapshot_size_exceeded")
    _validate_sources(normalized, adapter.freshness_policies)
    _validate_diagnostics(normalized, adapter.allowed_modules)
    adapter.validate_payload(normalized)
    _validate_content_hash(normalized)
    return normalized


def build_artifact_packet(
    snapshot: Mapping[str, Any],
    adapter: BoardAdapter,
    *,
    default_view: str = "Overview",
    presentation_state: str = "ready",
) -> ArtifactPacket:
    """Validate one Board snapshot and return its canonical artifact packet."""

    normalized = validate_snapshot(snapshot, adapter)
    views = normalized["payload"]["views"]
    if default_view not in views:
        raise ArtifactPacketError("default_view_invalid")
    if presentation_state not in PRESENTATION_STATES:
        raise ArtifactPacketError("presentation_state_invalid")

    canonical_json = canonical_json_bytes(normalized)
    _require_size(canonical_json, SNAPSHOT_HARD_LIMIT_BYTES, "snapshot_size_exceeded")
    html = adapter.render(normalized, default_view, presentation_state)
    _validate_html_safety(html)
    _require_size(html, HTML_HARD_LIMIT_BYTES, "html_size_exceeded")
    html_sha256 = sha256_hex(html)
    manifest = canonical_json_bytes(
        {
            "artifact_identity": f"{normalized['snapshot_id']}:{normalized['board']}",
            "artifact_lifecycle": normalized["artifact_lifecycle"],
            "board": normalized["board"],
            "canonical_html": "research-brief.html",
            "canonical_json": "snapshot.canonical.json",
            "canonical_json_sha256": sha256_hex(canonical_json),
            "content_hash": normalized["content_hash"],
            "decision_cutoff": normalized["decision_cutoff"],
            "default_view": default_view,
            "html_sha256": html_sha256,
            "manifest_version": MANIFEST_VERSION,
            "payload_version": normalized["payload_version"],
            "presentation_state": presentation_state,
            "privacy": normalized["privacy"],
            "renderer_version": normalized["renderer_version"],
            "snapshot_id": normalized["snapshot_id"],
            "snapshot_contract_version": normalized["schema_version"],
            "views": views,
        }
    )
    _require_size(manifest, MANIFEST_HARD_LIMIT_BYTES, "manifest_size_exceeded")
    return ArtifactPacket(canonical_json=canonical_json, html=html, manifest=manifest)


def write_artifact_packet(packet: ArtifactPacket, output_dir: Path) -> dict[str, Path]:
    """Write a packet once; pre-existing bytes must exactly match the packet."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output_dir / "snapshot.canonical.json",
        "html": output_dir / "research-brief.html",
        "manifest": output_dir / "artifact.manifest.json",
    }
    existing_names = {path.name for path in output_dir.iterdir()}
    expected_names = {path.name for path in paths.values()}
    if existing_names and existing_names != expected_names:
        raise ArtifactPacketError("immutable_output_conflict")
    if existing_names and any(path.is_symlink() or not path.is_file() for path in paths.values()):
        raise ArtifactPacketError("immutable_output_conflict")
    for key, path in paths.items():
        data = getattr(packet, "canonical_json" if key == "json" else key)
        if path.exists() and path.read_bytes() != data:
            raise ArtifactPacketError("immutable_output_conflict")
    for key, path in paths.items():
        if not path.exists():
            data = getattr(packet, "canonical_json" if key == "json" else key)
            path.write_bytes(data)
    return paths


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON with stable key order and no presentation whitespace."""

    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ArtifactPacketError("schema_invalid") from exc


def sha256_hex(data: bytes) -> str:
    """Return the stable SHA-256 identity for an exact byte sequence."""

    return hashlib.sha256(data).hexdigest()


def _validate_sources(
    snapshot: Mapping[str, Any],
    freshness_policies: Mapping[str, timedelta | None] = FRESHNESS_POLICIES,
) -> None:
    cutoff = _parse_timestamp(snapshot["decision_cutoff"], "decision_cutoff_invalid")
    sources = snapshot.get("source_registry")
    if not isinstance(sources, list) or not sources:
        raise ArtifactPacketError("source_registry_invalid")
    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ArtifactPacketError("source_registry_invalid")
        source_id = source.get("id")
        policy = source.get("freshness_policy_id")
        alias = source.get("alias")
        if (
            not _is_nonempty_string(source_id)
            or not _is_nonempty_string(alias)
            or _contains_unsafe_text(alias)
            or source_id in source_ids
            or policy not in freshness_policies
        ):
            raise ArtifactPacketError("source_registry_invalid")
        source_ids.add(source_id)
        if source.get("priority") not in {"S0", "S1", "S2", "S3", "S4"}:
            raise ArtifactPacketError("source_registry_invalid")
        observed = _parse_timestamp(source.get("as_of"), "source_freshness_invalid")
        if observed > cutoff:
            raise ArtifactPacketError("source_freshness_invalid")
        expected_status = evaluate_freshness(policy, observed, cutoff, freshness_policies)
        if source.get("freshness_status") != expected_status:
            raise ArtifactPacketError("source_freshness_invalid")


def _validate_common_field_sets(snapshot: Mapping[str, Any]) -> None:
    """Reject envelope extension fields until a new contract defines them."""

    _reject_unknown_fields(snapshot, SNAPSHOT_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("builder"), BUILDER_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("coverage"), COVERAGE_V1_FIELDS)
    payload = snapshot.get("payload")
    if isinstance(payload, Mapping):
        modules = payload.get("modules")
        if isinstance(modules, list):
            for module in modules:
                _reject_unknown_fields(module, MODULE_V1_FIELDS)
    sources = snapshot.get("source_registry")
    if isinstance(sources, list):
        for source in sources:
            _reject_unknown_fields(source, SOURCE_V1_FIELDS)


def _validate_envelope_fields(snapshot: Mapping[str, Any]) -> None:
    builder = snapshot.get("builder")
    if not isinstance(builder, dict) or not _is_nonempty_string(builder.get("id")):
        raise ArtifactPacketError("schema_invalid")
    _parse_timestamp(builder.get("generated_at"), "schema_invalid")
    if not _is_nonempty_string(snapshot.get("timezone")) or not _is_nonempty_string(snapshot.get("locale")):
        raise ArtifactPacketError("schema_invalid")
    if snapshot.get("evidence_state") not in EVIDENCE_STATES:
        raise ArtifactPacketError("evidence_state_invalid")
    reasons = snapshot.get("state_reasons")
    if not isinstance(reasons, list) or not all(isinstance(reason, str) for reason in reasons):
        raise ArtifactPacketError("schema_invalid")


def _reject_unknown_fields(value: Any, allowed_fields: frozenset[str]) -> None:
    if isinstance(value, Mapping) and set(value) - allowed_fields:
        raise ArtifactPacketError("schema_invalid")


def evaluate_freshness(
    policy_id: str,
    observed_at: datetime,
    decision_cutoff: datetime,
    freshness_policies: Mapping[str, timedelta | None] = FRESHNESS_POLICIES,
) -> str:
    """Evaluate a versioned source freshness policy at a fixed decision cutoff."""

    limit = freshness_policies.get(policy_id)
    if limit is None:
        return "fresh"
    return "fresh" if decision_cutoff - observed_at <= limit else "stale"


def _validate_content_hash(snapshot: Mapping[str, Any]) -> None:
    content = copy.deepcopy(dict(snapshot))
    expected = content.pop("content_hash", None)
    if not isinstance(expected, str) or len(expected) != 64:
        raise ArtifactPacketError("content_hash_invalid")
    if sha256_hex(canonical_json_bytes(content)) != expected:
        raise ArtifactPacketError("content_hash_mismatch")


def _validate_public_privacy(value: Any) -> None:
    if value.get("privacy") != "public_fixture":
        return
    for text in _iter_snapshot_text(value):
        if _contains_public_privacy_sentinel(text):
            raise ArtifactPacketError("privacy_violation")


def _validate_diagnostics(
    snapshot: Mapping[str, Any],
    allowed_modules: frozenset[str],
) -> None:
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, list):
        raise ArtifactPacketError("diagnostics_invalid")
    known_aliases = {source["alias"] for source in snapshot["source_registry"]}
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            raise ArtifactPacketError("diagnostics_invalid")
        allowed = {"code", "severity", "module", "source_alias", "message", "retryable"}
        if set(diagnostic) - allowed:
            raise ArtifactPacketError("diagnostics_invalid")
        code = diagnostic.get("code")
        severity = diagnostic.get("severity")
        message = diagnostic.get("message")
        retryable = diagnostic.get("retryable")
        if (
            not _is_nonempty_string(code)
            or not isinstance(severity, str)
            or severity not in DIAGNOSTIC_SEVERITIES
            or not isinstance(message, str)
            or len(message) > 200
            or not isinstance(retryable, bool)
        ):
            raise ArtifactPacketError("diagnostics_invalid")
        module = diagnostic.get("module")
        source_alias = diagnostic.get("source_alias")
        if (module is not None and not isinstance(module, str)) or (
            source_alias is not None and not isinstance(source_alias, str)
        ):
            raise ArtifactPacketError("diagnostics_invalid")
        for field in (code, message, module, source_alias):
            if field is not None and _contains_unsafe_text(field):
                raise ArtifactPacketError("diagnostic_unsafe")
        if not DIAGNOSTIC_CODE_PATTERN.fullmatch(code):
            raise ArtifactPacketError("diagnostics_invalid")
        if module is not None and (
            not _is_nonempty_string(module) or module not in allowed_modules
        ):
            raise ArtifactPacketError("diagnostic_reference_invalid")
        if source_alias is not None and (
            not _is_nonempty_string(source_alias) or source_alias not in known_aliases
        ):
            raise ArtifactPacketError("diagnostic_reference_invalid")


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(term.lower() in lowered for term in SAFE_TEXT_FORBIDDEN_TERMS) or bool(
        ACCOUNT_ID_PATTERN.search(value) or BROKER_ACCOUNT_ID_PATTERN.search(value)
    )


def _iter_snapshot_text(value: Any, *, top_level: bool = True):
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            yield str(key)
            if top_level and key == "content_hash":
                continue
            yield from _iter_snapshot_text(nested_value, top_level=False)
    elif isinstance(value, list):
        for nested_value in value:
            yield from _iter_snapshot_text(nested_value, top_level=False)
    elif isinstance(value, str):
        yield value


def _contains_public_privacy_sentinel(value: str) -> bool:
    normalized_path = value.replace("\\", "/")
    compact = re.sub(r"[^a-z0-9]+", "", value.casefold())
    bare_account_id = ACCOUNT_ID_PATTERN.fullmatch(value.strip())
    return (
        any(sentinel.casefold() in value.casefold() for sentinel in PRIVACY_SENTINELS)
        or bool(PUBLIC_PRIVATE_PATH_PATTERN.search(normalized_path))
        or any(sentinel in compact for sentinel in PUBLIC_PRIVACY_COMPACT_SENTINELS)
        or bool(bare_account_id)
        or bool(BROKER_ACCOUNT_ID_PATTERN.search(value))
    )


def _validate_html_safety(html: bytes) -> None:
    lowered = html.decode("utf-8").lower()
    if any(term in lowered for term in FORBIDDEN_HTML_TERMS):
        raise ArtifactPacketError("html_safety_violation")


def _validate_snapshot_action_safety(
    snapshot: Mapping[str, Any],
    allowed_terms: frozenset[str] = frozenset(),
) -> None:
    forbidden_terms = tuple(
        term for term in FORBIDDEN_SNAPSHOT_TERMS if term not in allowed_terms
    )
    for text in _iter_snapshot_text(snapshot.get("payload", {})):
        if any(term in text.casefold() for term in forbidden_terms):
            raise ArtifactPacketError("html_safety_violation")


def _parse_timestamp(value: Any, error_code: str) -> datetime:
    if not _is_nonempty_string(value):
        raise ArtifactPacketError(error_code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArtifactPacketError(error_code) from exc
    if parsed.tzinfo is None:
        raise ArtifactPacketError(error_code)
    return parsed.astimezone(timezone.utc)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_size(data: bytes, limit: int, error_code: str) -> None:
    if len(data) > limit:
        raise ArtifactPacketError(error_code)
