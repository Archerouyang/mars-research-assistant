#!/usr/bin/env python3
"""Build immutable, offline research artifact packets from one Board snapshot.

This module owns the public artifact-packet seam only. It never reads a live
source, private runtime state, or a host environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import copy
import hashlib
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
INSTRUMENT_BOARD = "instrument_research"
PAYLOAD_VERSION = "1.0"
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
UNSAFE_DIAGNOSTIC_TERMS = ("traceback", "stack trace", "/Users/", "api_key", "password", "token")
REQUIRED_INSTRUMENT_MODULES = ("industry", "fundamentals", "catalysts", "market_instrument")
FORBIDDEN_HTML_TERMS = (
    "<script",
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


class ArtifactPacketError(ValueError):
    """A fail-closed public error code without sensitive input details."""


@dataclass(frozen=True)
class ArtifactPacket:
    """Exact bytes returned by the artifact-packet public interface."""

    canonical_json: bytes
    html: bytes
    manifest: bytes


def build_artifact_packet(
    snapshot: Mapping[str, Any],
    *,
    default_view: str = "Overview",
    presentation_state: str = "ready",
) -> ArtifactPacket:
    """Validate one Instrument snapshot and return its canonical artifact packet."""

    normalized = validate_instrument_snapshot(snapshot)
    views = normalized["payload"]["views"]
    if default_view not in views:
        raise ArtifactPacketError("default_view_invalid")
    if presentation_state not in PRESENTATION_STATES:
        raise ArtifactPacketError("presentation_state_invalid")

    canonical_json = canonical_json_bytes(normalized)
    _require_size(canonical_json, SNAPSHOT_HARD_LIMIT_BYTES, "snapshot_size_exceeded")
    html = render_instrument_research_brief(normalized, default_view, presentation_state)
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
    for key, path in paths.items():
        data = getattr(packet, "canonical_json" if key == "json" else key)
        if path.exists() and path.read_bytes() != data:
            raise ArtifactPacketError("immutable_output_conflict")
    for key, path in paths.items():
        if not path.exists():
            data = getattr(packet, "canonical_json" if key == "json" else key)
            path.write_bytes(data)
    return paths


def validate_instrument_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep-copied valid Instrument snapshot or a safe error code."""

    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    normalized = copy.deepcopy(dict(snapshot))
    if normalized.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactPacketError("schema_version_invalid")
    if normalized.get("board") != INSTRUMENT_BOARD:
        raise ArtifactPacketError("board_invalid")
    if normalized.get("payload_version") != PAYLOAD_VERSION:
        raise ArtifactPacketError("payload_version_invalid")
    if normalized.get("renderer_version") != RENDERER_VERSION:
        raise ArtifactPacketError("renderer_version_invalid")
    if normalized.get("privacy") not in {"public_fixture", "private_runtime"}:
        raise ArtifactPacketError("privacy_invalid")
    if normalized.get("artifact_lifecycle") not in {"transient", "durable"}:
        raise ArtifactPacketError("artifact_lifecycle_invalid")
    if not isinstance(normalized.get("payload"), dict):
        raise ArtifactPacketError("payload_invalid")
    payload = normalized["payload"]
    if payload.get("board") != normalized["board"]:
        raise ArtifactPacketError("board_mismatch")
    if payload.get("payload_version") != normalized["payload_version"]:
        raise ArtifactPacketError("payload_version_mismatch")
    if not _is_nonempty_string(normalized.get("snapshot_id")):
        raise ArtifactPacketError("snapshot_id_invalid")
    _parse_timestamp(normalized.get("decision_cutoff"), "decision_cutoff_invalid")
    _validate_envelope_fields(normalized)
    _require_size(canonical_json_bytes(normalized), SNAPSHOT_HARD_LIMIT_BYTES, "snapshot_size_exceeded")
    _validate_public_privacy(normalized)
    _validate_diagnostics(normalized.get("diagnostics"))
    _validate_sources(normalized)
    _validate_payload(normalized)
    _validate_content_hash(normalized)
    return normalized


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON with stable key order and no presentation whitespace."""

    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ArtifactPacketError("schema_invalid") from exc


def sha256_hex(data: bytes) -> str:
    """Return the stable SHA-256 identity for an exact byte sequence."""

    return hashlib.sha256(data).hexdigest()


def render_instrument_research_brief(
    snapshot: Mapping[str, Any], default_view: str, presentation_state: str
) -> bytes:
    """Render a directly openable semantic Overview without executable code."""

    payload = snapshot["payload"]
    subject = payload["subject"]
    modules = payload["modules"]
    module_rows = "".join(
        "<article class=\"module\">"
        f"<h3>{escape(module['id'].replace('_', ' ').title())}</h3>"
        f"<p><strong>Status:</strong> {escape(module['evidence_state'])}</p>"
        f"<p>{escape(module['summary'])}</p>"
        f"<p><strong>As of:</strong> {escape(module['as_of'])}</p>"
        f"<p><strong>Gap:</strong> {escape(module['gap_reason'] or 'None')}</p>"
        "</article>"
        for module in modules
    )
    source_rows = "".join(
        "<li>"
        f"{escape(source['alias'])} ({escape(source['priority'])}, {escape(source['freshness_status'])}, "
        f"{escape(source['as_of'])})"
        "</li>"
        for source in snapshot["source_registry"]
    )
    views = "".join(
        _render_view_label(view, default_view) for view in payload["views"]
    )
    html = f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{escape(subject['instrument'])} Instrument Research</title>
<style>
:root {{ color-scheme: light; font-family: Arial, sans-serif; line-height: 1.45; }}
body {{ margin: 0; color: #17212b; background: #f6f8fa; }}
main {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
header, section, footer {{ margin-bottom: 20px; }}
.masthead {{ border-bottom: 3px solid #18794e; padding-bottom: 16px; }}
.eyebrow {{ color: #0d5f3b; font-weight: 700; margin: 0; }}
nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }}
nav span {{ border: 1px solid #6d7a86; padding: 4px 8px; }}
nav span[aria-current=\"page\"] {{ background: #d7f3e3; font-weight: 700; }}
.summary {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
.summary p, .module {{ background: #fff; border: 1px solid #c8d0d8; margin: 0; padding: 12px; }}
.modules {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
.rail {{ border-left: 4px solid #d0a000; padding-left: 16px; }}
footer {{ border-top: 1px solid #c8d0d8; padding-top: 12px; font-size: 0.92rem; }}
@media (max-width: 736px) {{ main {{ padding: 16px; }} .summary, .modules {{ grid-template-columns: 1fr; }} .rail {{ border-left: 0; border-top: 4px solid #d0a000; padding-left: 0; padding-top: 12px; }} }}
</style>
</head>
<body>
<main>
<header class=\"masthead\">
<p class=\"eyebrow\">Instrument Research</p>
<h1>{escape(subject['instrument'])} Research brief</h1>
<p>Overview for a synthetic {escape(subject['product_type'])} in {escape(subject['market'])}.</p>
<nav aria-label=\"Research views\">{views}</nav>
</header>
<section aria-labelledby=\"provenance\">
<h2 id=\"provenance\">Provenance</h2>
<p>Snapshot {escape(snapshot['snapshot_id'])}; cutoff {escape(snapshot['decision_cutoff'])}; privacy {escape(snapshot['privacy'])}.</p>
</section>
<section class=\"summary\" aria-label=\"Research summary\">
<p><strong>Current decision</strong><br>{escape(payload['decision'])}</p>
<p><strong>Coverage</strong><br>{snapshot['coverage']['required_complete']} of {snapshot['coverage']['required_total']} required modules complete.</p>
<p><strong>Status</strong><br>Evidence: {escape(snapshot['evidence_state'])}; presentation: {escape(presentation_state)}.</p>
</section>
<section aria-labelledby=\"modules\">
<h2 id=\"modules\">Module status and gaps</h2>
<div class=\"modules\">{module_rows}</div>
</section>
<section class=\"rail\" aria-labelledby=\"evidence-rail\">
<h2 id=\"evidence-rail\">Evidence rail</h2>
<ul>{source_rows}</ul>
</section>
<footer>
<h2>Safety boundary</h2>
<p>Synthetic fixture. Not investment advice. No external requests or state-changing actions occur when this file is opened.</p>
</footer>
</main>
</body>
</html>
"""
    return html.encode("utf-8")


def _validate_sources(snapshot: Mapping[str, Any]) -> None:
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
        if (
            not _is_nonempty_string(source_id)
            or not _is_nonempty_string(source.get("alias"))
            or source_id in source_ids
            or policy not in FRESHNESS_POLICIES
        ):
            raise ArtifactPacketError("source_registry_invalid")
        source_ids.add(source_id)
        if source.get("priority") not in {"S0", "S1", "S2", "S3", "S4"}:
            raise ArtifactPacketError("source_registry_invalid")
        observed = _parse_timestamp(source.get("as_of"), "source_freshness_invalid")
        if observed > cutoff:
            raise ArtifactPacketError("source_freshness_invalid")
        expected_status = evaluate_freshness(policy, observed, cutoff)
        if source.get("freshness_status") != expected_status:
            raise ArtifactPacketError("source_freshness_invalid")


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


def _render_view_label(view: str, default_view: str) -> str:
    current = ' aria-current="page"' if view == default_view else ""
    return f"<span{current}>{escape(view)}</span>"


def evaluate_freshness(policy_id: str, observed_at: datetime, decision_cutoff: datetime) -> str:
    """Evaluate a versioned source freshness policy at a fixed decision cutoff."""

    limit = FRESHNESS_POLICIES.get(policy_id)
    if limit is None:
        return "fresh"
    return "fresh" if decision_cutoff - observed_at <= limit else "stale"


def _validate_payload(snapshot: Mapping[str, Any]) -> None:
    payload = snapshot["payload"]
    if not all(_is_nonempty_string(payload.get(key)) for key in ("question", "decision", "posture")):
        raise ArtifactPacketError("payload_invalid")
    subject = payload.get("subject")
    if not isinstance(subject, dict) or not all(
        _is_nonempty_string(subject.get(key))
        for key in ("instrument", "underlying", "product_type", "market", "currency", "analysis_horizon")
    ):
        raise ArtifactPacketError("subject_invalid")
    views = payload.get("views")
    if not isinstance(views, list) or views != ["Overview", "Price & Setup", "Industry & Peers", "Catalysts & Flows"]:
        raise ArtifactPacketError("views_invalid")
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise ArtifactPacketError("modules_invalid")
    by_id = {module.get("id"): module for module in modules if isinstance(module, dict)}
    if (
        len(modules) != len(REQUIRED_INSTRUMENT_MODULES)
        or len(by_id) != len(modules)
        or set(by_id) != set(REQUIRED_INSTRUMENT_MODULES)
    ):
        raise ArtifactPacketError("modules_invalid")
    source_ids = {source["id"] for source in snapshot["source_registry"]}
    required_complete = 0
    for module_id in REQUIRED_INSTRUMENT_MODULES:
        module = by_id[module_id]
        if module.get("requirement") != "required" or module.get("evidence_state") not in EVIDENCE_STATES:
            raise ArtifactPacketError("modules_invalid")
        if not _is_nonempty_string(module.get("summary")) or not isinstance(module.get("gap_reason"), str):
            raise ArtifactPacketError("modules_invalid")
        _parse_timestamp(module.get("as_of"), "modules_invalid")
        refs = module.get("source_refs")
        if (
            not isinstance(refs, list)
            or not refs
            or not all(_is_nonempty_string(reference) for reference in refs)
            or not set(refs).issubset(source_ids)
        ):
            raise ArtifactPacketError("modules_invalid")
        if module.get("freshness_policy_id") not in FRESHNESS_POLICIES:
            raise ArtifactPacketError("modules_invalid")
        if module["evidence_state"] == "complete":
            required_complete += 1
    coverage = snapshot.get("coverage")
    if coverage != {"required_complete": required_complete, "required_total": 4}:
        raise ArtifactPacketError("coverage_mismatch")
    if snapshot.get("evidence_state") != _derive_instrument_evidence_state(by_id):
        raise ArtifactPacketError("evidence_state_mismatch")


def _derive_instrument_evidence_state(modules: Mapping[str, Mapping[str, Any]]) -> str:
    states = {module_id: modules[module_id]["evidence_state"] for module_id in REQUIRED_INSTRUMENT_MODULES}
    if any(state == "stale" for state in states.values()):
        return "stale"
    usable = {module_id for module_id, state in states.items() if state in {"complete", "partial"}}
    if states["industry"] not in {"complete", "partial"} or states["fundamentals"] not in {"complete", "partial"}:
        return "source_error"
    if len(usable) < 3:
        return "source_error"
    if all(state == "complete" for state in states.values()):
        return "complete"
    return "partial"


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
    text = canonical_json_bytes(value).decode("utf-8").lower()
    if any(sentinel.lower() in text for sentinel in PRIVACY_SENTINELS):
        raise ArtifactPacketError("privacy_violation")


def _validate_diagnostics(diagnostics: Any) -> None:
    if not isinstance(diagnostics, list):
        raise ArtifactPacketError("diagnostics_invalid")
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            raise ArtifactPacketError("diagnostics_invalid")
        allowed = {"code", "severity", "module", "source_alias", "message", "retryable"}
        if set(diagnostic) - allowed or not _is_nonempty_string(diagnostic.get("code")):
            raise ArtifactPacketError("diagnostics_invalid")
        message = diagnostic.get("message", "")
        if not isinstance(message, str) or len(message) > 200:
            raise ArtifactPacketError("diagnostic_unsafe")
        lowered = message.lower()
        if any(term.lower() in lowered for term in UNSAFE_DIAGNOSTIC_TERMS):
            raise ArtifactPacketError("diagnostic_unsafe")


def _validate_html_safety(html: bytes) -> None:
    lowered = html.decode("utf-8").lower()
    if any(term in lowered for term in FORBIDDEN_HTML_TERMS):
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
